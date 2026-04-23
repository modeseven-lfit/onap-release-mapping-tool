# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Map Docker image names to their source Gerrit project paths.

The mapper resolves an image reference (e.g. ``onap/so/so-cnf-adapter``)
to a Gerrit project path (e.g. ``so/adapters/so-cnf-adapter``).

Candidate collection and ranking
--------------------------------
The resolver does not simply return the first strategy that produces
a match. Instead it collects plausible candidates from several
strategies and then ranks them, preferring verified Gerrit ground
truth over weaker or unverified guesses. A parent-pointing override
is therefore NOT guaranteed to win: if a later stage finds a deeper
verified Gerrit match for the same image leaf, the longest verified
path supersedes the override. This is the crux of the fix for the
``so-cnf-adapter`` class of mis-attribution.

1. **Explicit override candidate** — exact match in the loaded
   mapping table. An override whose target does not exist in
   ``known_projects`` is still retained and, if ultimately chosen,
   flagged as ``OVERRIDE_STALE`` so the audit step can surface it.
2. **Gerrit ground-truth candidates** — find Gerrit projects whose
   final path segment equals the image's leaf segment. Prefer the
   same top-level namespace; fall back cross-namespace only when no
   in-namespace candidate exists. Within the chosen namespace
   bucket, the deepest path wins. This stage intentionally subsumes
   the simpler "direct hit" case: when the image path is itself a
   Gerrit project, that project's leaf is considered alongside any
   deeper siblings sharing the same leaf.
3. **Heuristic fallback candidates** — ``org.onap.<a>.<b>.*``,
   dash-to-slash for known top-level projects, and slash
   pass-through. Heuristic outputs are preferred when they are
   verified against ``known_projects``; an unverified heuristic
   guess only wins when no ground-truth match exists anywhere
   (preserving offline / partial-run behaviour).
4. **``None``** when no candidate matches.

Ranking rules applied to the collected candidates:

* Any verified candidate beats any unverified candidate.
* Among verified candidates, the deepest path (slash count) wins;
  same-depth ties resolve alphabetically for deterministic output.
* Among unverified candidates (offline / partial-run), an explicit
  override beats a heuristic guess because the override represents
  deliberate human judgement.

Every resolution yields both the project path and a
:class:`MappingResult` that records HOW the decision was made, so
downstream code (validators, exporters, audit reports) can explain or
flag each attribution without having to re-run the algorithm.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Any

from .yaml_utils import safe_load_yaml, safe_load_yaml_string

# Known top-level ONAP project prefixes used for dash-to-slash heuristic.
_KNOWN_TOP_LEVEL_PROJECTS: frozenset[str] = frozenset(
    {
        "aai",
        "ccsdk",
        "cps",
        "dcaegen2",
        "dmaap",
        "holmes",
        "modeling",
        "msb",
        "multicloud",
        "oof",
        "policy",
        "portal-ng",
        "sdc",
        "sdnc",
        "so",
        "usecase-ui",
        "vfc",
    }
)

# Precomputed longest-first ordering so _heuristic_dash() doesn't
# re-sort on every call (e.g. prefers "portal-ng" over "portal").
_KNOWN_PREFIXES_LONGEST_FIRST: tuple[str, ...] = tuple(
    sorted(_KNOWN_TOP_LEVEL_PROJECTS, key=len, reverse=True)
)


class MappingReason(str, Enum):
    """How an image was resolved to a Gerrit project.

    Values are strings so they serialise cleanly into JSON / YAML
    manifest output and can be grouped or filtered by consumers.
    """

    OVERRIDE = "override"
    """Explicit entry in the mapping table."""

    OVERRIDE_STALE = "override-stale"
    """Explicit entry resolves to a repo not present in Gerrit."""

    LEAF_MATCH_NAMESPACE = "leaf-match-namespace"
    """Longest-match on leaf segment within the same top-level namespace."""

    LEAF_MATCH_CROSS_NAMESPACE = "leaf-match-cross-namespace"
    """Longest-match on leaf segment across namespaces (in-namespace empty)."""

    HEURISTIC_ORG_ONAP_VERIFIED = "heuristic-org-onap-verified"
    """``org.onap.*`` heuristic guess that exists in Gerrit."""

    HEURISTIC_DASH_VERIFIED = "heuristic-dash-verified"
    """Dash-to-slash heuristic guess that exists in Gerrit."""

    HEURISTIC_SLASH_VERIFIED = "heuristic-slash-verified"
    """Slash-passthrough heuristic guess that exists in Gerrit."""

    HEURISTIC_ORG_ONAP_UNVERIFIED = "heuristic-org-onap-unverified"
    """``org.onap.*`` heuristic guess without Gerrit verification."""

    HEURISTIC_DASH_UNVERIFIED = "heuristic-dash-unverified"
    """Dash-to-slash heuristic guess without Gerrit verification."""

    HEURISTIC_SLASH_UNVERIFIED = "heuristic-slash-unverified"
    """Slash-passthrough heuristic guess without Gerrit verification."""

    UNRESOLVED = "unresolved"
    """No explicit mapping and no heuristic produced a result."""


@dataclass(frozen=True)
class MappingResult:
    """Detailed outcome of a single image-to-project resolution.

    Attributes:
        project: Resolved Gerrit project path, or ``None`` if
            unresolved.
        reason: Classification of how the decision was reached.
        verified: ``True`` when the chosen project was confirmed
            present in the Gerrit known-projects set.
        alternatives: Other plausible candidates considered but not
            chosen. Useful for audit reports when the leaf segment
            matches multiple Gerrit repos.
    """

    project: str | None
    reason: MappingReason
    verified: bool = False
    alternatives: tuple[str, ...] = field(default_factory=tuple)


class ImageMapper:
    """Map Docker image names to their source Gerrit project paths.

    When a set of known Gerrit project paths is supplied via
    ``known_projects``, the mapper applies a longest-match algorithm
    that verifies every candidate against ground truth and prefers
    the deepest, same-namespace match. When ``known_projects`` is
    empty or ``None`` (offline / partial-run scenario) the mapper
    falls back to unverified heuristics, preserving the original
    behaviour so partial-run manifests are still produced.
    """

    def __init__(
        self,
        mapping_file: Path | None = None,
        known_projects: set[str] | frozenset[str] | None = None,
    ) -> None:
        """Initialise the mapper.

        Args:
            mapping_file: Optional path to a YAML file with additional
                or overriding image-to-project mappings.
            known_projects: Optional set of Gerrit project paths used
                as ground truth for verification and longest-match
                resolution. Typically populated from the Gerrit
                collector's project listing. When ``None`` or empty
                the mapper falls back to unverified heuristics.
        """
        self._logger = logging.getLogger(__name__)
        self._mappings: dict[str, str] = {}
        self._load_default_mappings()
        if mapping_file:
            self._load_override_mappings(mapping_file)

        # Normalise known_projects to a frozenset for fast membership
        # checks and immutability. Empty set means "no ground truth".
        self._known_projects: frozenset[str] = frozenset(known_projects or ())

        # Index Gerrit projects by their leaf segment to speed up
        # the longest-match stage (O(1) per image instead of O(N)).
        # Accumulate into mutable lists during construction, then
        # freeze to tuples in a single pass so each lookup returns
        # an immutable value without the O(N^2) cost of repeatedly
        # concatenating tuples on insertion.
        _leaf_index_build: dict[str, list[str]] = {}
        for project in self._known_projects:
            leaf = project.rsplit("/", maxsplit=1)[-1]
            _leaf_index_build.setdefault(leaf, []).append(project)
        self._leaf_index: dict[str, tuple[str, ...]] = {
            leaf: tuple(projects) for leaf, projects in _leaf_index_build.items()
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def known_projects(self) -> frozenset[str]:
        """Return the frozen set of Gerrit project paths used for ground truth."""
        return self._known_projects

    @property
    def has_ground_truth(self) -> bool:
        """``True`` when a non-empty ``known_projects`` set was supplied."""
        return bool(self._known_projects)

    @property
    def mappings(self) -> dict[str, str]:
        """Return a shallow copy of the loaded explicit mappings."""
        return dict(self._mappings)

    def map_image(self, image_name: str) -> str | None:
        """Return the Gerrit project path for *image_name*, or ``None``.

        Convenience wrapper around :meth:`resolve` that returns only
        the project path. Most callers want just the path; code that
        needs to explain the decision should call :meth:`resolve`.

        Args:
            image_name: Docker image name, e.g. ``onap/policy-api``.

        Returns:
            Gerrit project path or ``None``.
        """
        return self.resolve(image_name).project

    def resolve(self, image_name: str) -> MappingResult:
        """Resolve *image_name* to a :class:`MappingResult`.

        See module docstring for the full resolution order. This
        method is deterministic: given the same ``known_projects``
        set and mapping file it always produces the same result for
        a given image.

        Args:
            image_name: Docker image name, e.g.
                ``onap/so/so-cnf-adapter``.

        Returns:
            A :class:`MappingResult` describing the outcome.
        """
        normalised = self._strip_registry(image_name)
        without_prefix = self._strip_onap_prefix(normalised)

        # Compute every candidate we might return, then apply the
        # "longest match always wins" rule as the final arbiter. This
        # ensures a parent-pointing override (e.g. onap/cps-temporal
        # → cps) cannot shadow a deeper real repo (cps/cps-temporal)
        # when ground truth reveals the deeper match. Without ground
        # truth the override still wins because no competing candidate
        # exists.

        override_result = self._resolve_override(image_name, normalised, without_prefix)

        # Stages below are only meaningful for images in the ONAP
        # namespace. Anything else (e.g. a base image) short-circuits
        # to either the override (if one exists) or unresolved.
        is_onap = normalised.startswith("onap/")
        if not is_onap:
            if override_result is not None:
                return override_result
            self._logger.debug("No mapping found for non-onap image: %s", image_name)
            return MappingResult(project=None, reason=MappingReason.UNRESOLVED)

        leaf_result: MappingResult | None = None
        if self.has_ground_truth:
            leaf_result = self._leaf_match(without_prefix)

        # Always collect heuristic candidates for ONAP images and let
        # the ranking step decide between override, leaf-match, and
        # heuristic outputs. A heuristic may resolve to a deeper
        # verified project than a verified leaf match (for example
        # when the dash-heuristic produces ``policy/api`` for
        # ``onap/policy-api`` while leaf-match would otherwise pick a
        # shallower depth-0 repo), and the deepest verified candidate
        # must be allowed to win. Skipping heuristics here would
        # contradict the "collect all candidates, then rank" contract
        # stated in the module docstring.
        heuristic_result: MappingResult | None = self._run_heuristics(without_prefix)

        # Choose the longest verified candidate. An override, leaf
        # match, and heuristic guess may all be present; the one
        # whose resolved project has the greatest depth wins. Ties
        # break on verification status, then alphabetically for
        # determinism.
        best = self._pick_best_candidate(
            override_result,
            leaf_result,
            heuristic_result,
        )
        if best is not None:
            return best

        self._logger.debug("No mapping found for image: %s", image_name)
        return MappingResult(project=None, reason=MappingReason.UNRESOLVED)

    def _resolve_override(
        self,
        image_name: str,
        normalised: str,
        without_prefix: str,
    ) -> MappingResult | None:
        """Look up an explicit override and classify its freshness.

        Args:
            image_name: Original image reference, used only for logging.
            normalised: Image name with registry prefix stripped.
            without_prefix: Image name with ``onap/`` prefix stripped.

        Returns:
            :class:`MappingResult` when an override exists, ``None``
            otherwise.
        """
        override = self._mappings.get(normalised) or self._mappings.get(without_prefix)
        if override is None:
            return None

        verified = self._is_known(override)
        reason = (
            MappingReason.OVERRIDE
            if verified or not self.has_ground_truth
            else MappingReason.OVERRIDE_STALE
        )
        if reason is MappingReason.OVERRIDE_STALE:
            self._logger.warning(
                "Override for %s → %s does not match any known Gerrit project",
                image_name,
                override,
            )
        return MappingResult(
            project=override,
            reason=reason,
            verified=verified,
        )

    @staticmethod
    def _pick_best_candidate(
        *candidates: MappingResult | None,
    ) -> MappingResult | None:
        """Select the best candidate from override / leaf / heuristic stages.

        The decision implements two design principles simultaneously:

        * **Longest verified match wins** — among results that are
          verified against Gerrit ground truth, the deepest path wins.
          This is how a parent-pointing override (e.g. ``cps``) loses
          to a deeper real repo (``cps/cps-temporal``).
        * **User intent matters when nothing is verified** — when no
          candidate can be verified (e.g. ground truth unavailable, or
          heuristics only produced unverified guesses) an explicit
          override beats a heuristic guess, because the override
          represents deliberate human judgement.

        Ranking (higher wins, evaluated in order):

        1. Verified against ground truth (``True`` beats ``False``).
        2. **Only among verified candidates** — path depth (slash
           count); same-depth ties resolve alphabetically.
        3. **Only among unverified candidates** — override beats leaf
           match beats heuristic; within the same reason, deeper
           paths win, and same-depth ties resolve alphabetically.

        Args:
            *candidates: Zero or more candidate results; ``None``
                entries are ignored.

        Returns:
            The chosen result, or ``None`` if every candidate was
            ``None`` or had no project.
        """
        real = [c for c in candidates if c is not None and c.project is not None]
        if not real:
            return None

        # Prefer any verified candidate over any unverified one.
        verified = [c for c in real if c.verified]

        if verified:
            # Among verified candidates, longest match wins. Depth
            # (slash count) is the sole ranking key so that a leaf
            # match at ``so/adapters/so-cnf-adapter`` beats a parent-
            # pointing override at ``so``. Same-depth ties resolve
            # alphabetically for deterministic output — this matches
            # the tiebreak rule used inside ``_pick_longest`` for the
            # leaf-match stage itself, so the two code paths cannot
            # disagree on ordering.
            def verified_depth(result: MappingResult) -> int:
                project = result.project or ""
                return project.count("/")

            max_depth = max(verified_depth(c) for c in verified)
            deepest = [c for c in verified if verified_depth(c) == max_depth]
            return sorted(deepest, key=lambda c: c.project or "")[0]

        # Nothing is verified (either no ground truth available, or
        # every candidate failed verification). In this regime user
        # intent matters more than path shape: an explicit override
        # represents deliberate human judgement and outranks any
        # heuristic guess, even if the heuristic happens to produce a
        # longer path. This preserves offline / partial-run behaviour
        # where overrides are the only authoritative signal available.
        reason_priority: dict[MappingReason, int] = {
            MappingReason.OVERRIDE: 100,
            MappingReason.OVERRIDE_STALE: 90,
            MappingReason.LEAF_MATCH_NAMESPACE: 80,
            MappingReason.LEAF_MATCH_CROSS_NAMESPACE: 70,
            MappingReason.HEURISTIC_ORG_ONAP_VERIFIED: 60,
            MappingReason.HEURISTIC_DASH_VERIFIED: 55,
            MappingReason.HEURISTIC_SLASH_VERIFIED: 50,
            MappingReason.HEURISTIC_ORG_ONAP_UNVERIFIED: 30,
            MappingReason.HEURISTIC_DASH_UNVERIFIED: 25,
            MappingReason.HEURISTIC_SLASH_UNVERIFIED: 20,
            MappingReason.UNRESOLVED: 0,
        }

        def unverified_rank(result: MappingResult) -> tuple[int, int]:
            project = result.project or ""
            return (
                reason_priority.get(result.reason, 0),
                project.count("/"),
            )

        unverified_top_key = max(unverified_rank(c) for c in real)
        unverified_top = [c for c in real if unverified_rank(c) == unverified_top_key]
        return sorted(unverified_top, key=lambda c: c.project or "")[0]

    @staticmethod
    def get_top_level_project(gerrit_project: str) -> str:
        """Extract the top-level project from a Gerrit path.

        Examples:
            ``policy/api`` → ``policy``
            ``so/adapters/so-cnf-adapter`` → ``so``
            ``cps`` → ``cps``

        Args:
            gerrit_project: Gerrit project path.

        Returns:
            Top-level project name.
        """
        return gerrit_project.split("/", maxsplit=1)[0]

    # ------------------------------------------------------------------
    # Private helpers – loading
    # ------------------------------------------------------------------

    def _load_default_mappings(self) -> None:
        """Load the shipped ``image_repo_mapping.yaml`` from package data."""
        try:
            resource = (
                resources.files("onap_release_map")
                .joinpath("data")
                .joinpath("image_repo_mapping.yaml")
            )
            content = resource.read_text(encoding="utf-8")
            data = safe_load_yaml_string(content)
            self._merge_mappings(data)
            self._logger.debug("Loaded %d default image mappings", len(self._mappings))
        except Exception:
            self._logger.warning("Could not load default image mappings", exc_info=True)

    def _load_override_mappings(self, path: Path) -> None:
        """Load and merge user-provided override mappings.

        Args:
            path: Path to a YAML file whose top-level keys are image
                names and values are Gerrit project paths.
        """
        data = safe_load_yaml(path)
        if data:
            count_before = len(self._mappings)
            self._merge_mappings(data)
            added = len(self._mappings) - count_before
            self._logger.debug(
                "Merged %d override mappings from %s (%d new)",
                len(data),
                path,
                added,
            )

    def _merge_mappings(self, data: dict[str, Any]) -> None:
        """Merge a mapping dict into ``self._mappings``.

        The YAML structure is expected to be a flat mapping of image
        name (string) to Gerrit project path (string). Nested
        structures with a ``mappings`` key are also accepted.

        Args:
            data: Parsed YAML data.
        """
        if not isinstance(data, dict):
            return

        # Support a top-level "mappings" key wrapping the actual map.
        mappings: Any = data.get("mappings", data)
        if not isinstance(mappings, dict):
            return

        for key, value in mappings.items():
            if isinstance(key, str) and isinstance(value, str):
                self._mappings[key] = value

    # ------------------------------------------------------------------
    # Private helpers – resolution
    # ------------------------------------------------------------------

    def _is_known(self, project: str) -> bool:
        """Return ``True`` if *project* exists in the known-projects set.

        When no ground truth was supplied this also returns ``False``
        because an empty set contains no projects. Callers that need
        to distinguish "no ground truth was provided" from "project
        not found in ground truth" must consult :attr:`has_ground_truth`
        in addition to this method; the two states cannot be told
        apart from the return value alone.

        Args:
            project: Gerrit project path to check.

        Returns:
            ``True`` when the project exists in ``known_projects``;
            ``False`` both when the project is absent and when no
            ground truth was supplied.
        """
        return project in self._known_projects

    def _leaf_match(self, without_prefix: str) -> MappingResult | None:
        """Find the deepest Gerrit project whose leaf matches the image.

        Preference order:
            1. In-namespace matches (same top-level project as the image).
            2. Cross-namespace matches (only when in-namespace empty).

        Within each bucket, deeper paths win; ties break alphabetically
        for determinism.

        Args:
            without_prefix: Image name without registry or ``onap/``
                prefix, e.g. ``so/so-cnf-adapter``.

        Returns:
            :class:`MappingResult` when a leaf match is found, ``None``
            otherwise.
        """
        leaf = without_prefix.rsplit("/", maxsplit=1)[-1]
        candidates = self._leaf_index.get(leaf, ())
        if not candidates:
            return None

        # Determine the image's declared namespace (top-level project).
        # For an image like "so/so-cnf-adapter" the namespace is "so".
        # For a flat image like "cps-temporal" there is no explicit
        # namespace so all candidates are considered cross-namespace.
        image_namespace = (
            without_prefix.split("/", maxsplit=1)[0] if "/" in without_prefix else None
        )

        in_namespace: list[str] = []
        cross_namespace: list[str] = []
        for project in candidates:
            project_namespace = project.split("/", maxsplit=1)[0]
            if image_namespace is not None and project_namespace == image_namespace:
                in_namespace.append(project)
            else:
                cross_namespace.append(project)

        if in_namespace:
            chosen = self._pick_longest(in_namespace)
            alternatives = tuple(sorted(p for p in in_namespace if p != chosen))
            return MappingResult(
                project=chosen,
                reason=MappingReason.LEAF_MATCH_NAMESPACE,
                verified=True,
                alternatives=alternatives,
            )

        if cross_namespace:
            chosen = self._pick_longest(cross_namespace)
            alternatives = tuple(sorted(p for p in cross_namespace if p != chosen))
            return MappingResult(
                project=chosen,
                reason=MappingReason.LEAF_MATCH_CROSS_NAMESPACE,
                verified=True,
                alternatives=alternatives,
            )

        return None

    @staticmethod
    def _pick_longest(candidates: list[str]) -> str:
        """Pick the deepest path from *candidates*, breaking ties alphabetically.

        Depth is measured by slash count so that ``so/adapters/foo``
        wins over ``so/foo``. Ties (same depth) resolve alphabetically
        for deterministic output.

        Args:
            candidates: Non-empty list of Gerrit project paths.

        Returns:
            The chosen path.
        """
        # First select only the deepest paths by slash count.
        # Then break same-depth ties alphabetically for deterministic
        # output by returning the lexicographically smallest deepest path.
        max_depth = max(p.count("/") for p in candidates)
        deepest = [p for p in candidates if p.count("/") == max_depth]
        return sorted(deepest)[0]

    def _run_heuristics(self, without_prefix: str) -> MappingResult | None:
        """Try heuristic mappings, preferring verified ones.

        When ground truth is available, each heuristic guess is
        checked against ``known_projects``. Verified guesses win
        immediately. An unverified guess is held as a last-resort
        candidate and returned only if no verified guess was found.

        When no ground truth is available, the first heuristic that
        produces any output wins (and is reported as unverified).

        Args:
            without_prefix: Image name without registry or ``onap/``
                prefix.

        Returns:
            :class:`MappingResult` or ``None`` when no heuristic
            matched.
        """
        heuristics: tuple[
            tuple[
                str,
                MappingReason,
                MappingReason,
            ],
            ...,
        ] = (
            (
                "_heuristic_org_onap",
                MappingReason.HEURISTIC_ORG_ONAP_VERIFIED,
                MappingReason.HEURISTIC_ORG_ONAP_UNVERIFIED,
            ),
            (
                "_heuristic_slash",
                MappingReason.HEURISTIC_SLASH_VERIFIED,
                MappingReason.HEURISTIC_SLASH_UNVERIFIED,
            ),
            (
                "_heuristic_dash",
                MappingReason.HEURISTIC_DASH_VERIFIED,
                MappingReason.HEURISTIC_DASH_UNVERIFIED,
            ),
        )

        unverified_fallback: MappingResult | None = None

        for method_name, verified_reason, unverified_reason in heuristics:
            method = getattr(self, method_name)
            guess = method(without_prefix)
            if guess is None:
                continue
            if self._is_known(guess):
                return MappingResult(
                    project=guess,
                    reason=verified_reason,
                    verified=True,
                )
            # Hold the first unverified guess as a last-resort fallback.
            # Subsequent heuristics may still produce a verified match.
            if unverified_fallback is None:
                unverified_fallback = MappingResult(
                    project=guess,
                    reason=unverified_reason,
                    verified=False,
                )

        return unverified_fallback

    # ------------------------------------------------------------------
    # Private helpers – heuristics
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_registry(image_name: str) -> str:
        """Remove a leading Nexus/registry prefix from an image name.

        Args:
            image_name: Raw image reference.

        Returns:
            Image name without registry prefix.
        """
        # Pattern: nexus3.onap.org:10001/onap/foo → onap/foo
        if "/" in image_name:
            parts = image_name.split("/", maxsplit=1)
            # A registry prefix normally contains a dot or colon.
            if "." in parts[0] or ":" in parts[0]:
                return parts[1]
        return image_name

    @staticmethod
    def _strip_onap_prefix(image_name: str) -> str:
        """Remove the leading ``onap/`` prefix if present.

        Args:
            image_name: Image name possibly starting with ``onap/``.

        Returns:
            Image name without the ``onap/`` prefix.
        """
        if image_name.startswith("onap/"):
            return image_name[len("onap/") :]
        return image_name

    @staticmethod
    def _heuristic_org_onap(name: str) -> str | None:
        """Handle ``org.onap.<a>.<b>…`` naming convention.

        Maps ``org.onap.<a>.<b>`` (and deeper) to ``<a>/<b>``.

        Args:
            name: Image name without registry/onap prefix.

        Returns:
            Gerrit project path or ``None``.
        """
        prefix = "org.onap."
        if not name.startswith(prefix):
            return None
        remainder = name[len(prefix) :]
        segments = remainder.split(".")
        if len(segments) >= 2:
            return f"{segments[0]}/{segments[1]}"
        return None

    @staticmethod
    def _heuristic_slash(name: str) -> str | None:
        """Pass through slash-separated image paths.

        ``<project>/<sub>`` → ``<project>/<sub>``

        Args:
            name: Image name without registry/onap prefix.

        Returns:
            Gerrit project path or ``None``.
        """
        if "/" in name:
            return name
        return None

    @staticmethod
    def _heuristic_dash(name: str) -> str | None:
        """Convert dash-separated names using known project prefixes.

        ``<proj>-<sub>`` → ``<proj>/<sub>`` when *proj* is a known
        top-level project.

        Args:
            name: Image name without registry/onap prefix.

        Returns:
            Gerrit project path or ``None``.
        """
        # Try each known prefix, longest-first to prefer portal-ng over portal.
        for prefix in _KNOWN_PREFIXES_LONGEST_FIRST:
            dash_prefix = prefix + "-"
            if name.startswith(dash_prefix):
                remainder = name[len(dash_prefix) :]
                if remainder:
                    return f"{prefix}/{remainder}"
        return None


__all__ = [
    "ImageMapper",
    "MappingReason",
    "MappingResult",
]

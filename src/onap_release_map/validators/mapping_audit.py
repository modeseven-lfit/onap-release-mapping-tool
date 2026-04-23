# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Audit the image → Gerrit project mapping produced during collection.

The :class:`MappingAuditValidator` re-runs the :class:`ImageMapper`
against every Docker image in a built manifest and classifies each
resolution into one of several :class:`ValidationSeverity` levels.
Findings are aggregated into a :class:`ValidationReport` which can be
attached to the manifest output, surfaced in the CLI, or used to gate
CI runs via ``--strict-validation``.

Design goals
------------
* **Read-only**. The validator never mutates manifest contents; it only
  produces findings.
* **Deterministic**. Findings are sorted by severity, then category,
  then image so repeated runs produce identical output.
* **Actionable**. Every finding carries enough context (image, current
  mapping, suggested mapping, reason) that a human can triage without
  re-running the tool.
* **Stable taxonomy**. The :class:`ValidationFinding` shape is part of
  the manifest schema; new categories may be added but existing ones
  must not change meaning.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from onap_release_map.models import (
    ValidationCategory,
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
)
from onap_release_map.parsers.image_mapper import (
    ImageMapper,
    MappingReason,
    MappingResult,
)

if TYPE_CHECKING:
    from onap_release_map.models import ReleaseManifest


class MappingAuditValidator:
    """Audit image-to-project mappings against Gerrit ground truth.

    This validator re-resolves every Docker image in a manifest using
    a fresh :class:`ImageMapper` (seeded with the supplied override
    file and known Gerrit project set) and compares the fresh result
    against the mapping the manifest currently records.

    Typical usage:

        .. code-block:: python

            validator = MappingAuditValidator(
                mapping_file=Path("image_repo_mapping.yaml"),
                known_projects=gerrit_project_set,
            )
            report = validator.validate(manifest)
            if not report.passed:
                for finding in report.findings:
                    print(finding.reason)
    """

    name = "mapping_audit"

    def __init__(
        self,
        mapping_file: Path | None = None,
        known_projects: set[str] | frozenset[str] | None = None,
    ) -> None:
        """Initialise the validator.

        Args:
            mapping_file: Optional path to the override YAML file used
                during collection. When ``None`` only the shipped
                defaults are loaded.
            known_projects: Set of Gerrit project paths to treat as
                ground truth. Should be the same set passed to the
                :class:`OOMCollector` during collection so the audit
                matches the collector's view of reality.
        """
        self._mapper = ImageMapper(
            mapping_file=mapping_file,
            known_projects=known_projects,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, manifest: ReleaseManifest) -> ValidationReport:
        """Audit every Docker image in *manifest* and return a report.

        The validator never mutates the manifest. It constructs a new
        report whose ``passed`` flag is ``True`` when no ``ERROR``
        findings were produced.

        Args:
            manifest: A fully-built release manifest.

        Returns:
            A :class:`ValidationReport` summarising the audit.
        """
        findings: list[ValidationFinding] = []

        if not self._mapper.has_ground_truth:
            # Without Gerrit ground truth every verification-based
            # check is a no-op, so emit a single dedicated AUDIT_SKIPPED
            # finding and skip the per-image walk. This is a distinct
            # signal from UNRESOLVED (which means a specific image could
            # not be mapped even with ground truth present).
            findings.append(
                ValidationFinding(
                    category=ValidationCategory.AUDIT_SKIPPED,
                    severity=ValidationSeverity.INFO,
                    reason=(
                        "Gerrit ground truth unavailable; mapping audit "
                        "skipped. Enable the gerrit collector, or ensure "
                        "it collected at least one project, to get full "
                        "attribution verification."
                    ),
                )
            )
            return self._finalise(findings)

        for image in manifest.docker_images:
            finding = self._audit_image(image.image, image.gerrit_project)
            if finding is not None:
                findings.append(finding)

        return self._finalise(findings)

    # ------------------------------------------------------------------
    # Per-image audit
    # ------------------------------------------------------------------

    def _audit_image(
        self,
        image_name: str,
        current_mapping: str | None,
    ) -> ValidationFinding | None:
        """Compare a manifest image's current mapping to a fresh resolve.

        Args:
            image_name: Docker image reference, e.g.
                ``onap/so/so-cnf-adapter``.
            current_mapping: The manifest's recorded
                ``gerrit_project`` for this image.

        Returns:
            A :class:`ValidationFinding` when something is worth
            flagging, ``None`` when the mapping is clean.
        """
        fresh = self._mapper.resolve(image_name)

        # Still-unresolved images: the manifest already records no
        # mapping AND a fresh resolve still produces none. Surface
        # these as WARNING so reviewers can decide whether an
        # explicit override is needed.
        if fresh.project is None and current_mapping is None:
            return ValidationFinding(
                category=ValidationCategory.UNRESOLVED,
                severity=ValidationSeverity.WARNING,
                image=image_name,
                current_mapping=None,
                reason=(
                    f"Image {image_name!r} could not be mapped to any "
                    "Gerrit project. Consider adding an explicit "
                    "override."
                ),
            )

        # Drift: manifest disagrees with a fresh resolve. Two sub-cases
        # are worth distinguishing for reviewers:
        #
        # 1. STALE_OVERRIDE_WITH_FIX — the manifest's recorded mapping
        #    exactly matches a stale override in the current mapping
        #    table (i.e. an override whose target is NOT a known
        #    Gerrit project), AND the fresh resolve selected a
        #    different verified project. This is the "algorithm
        #    corrected a broken override" case — reviewers should
        #    remove or fix the override so the audit stops flagging
        #    it. The replacement is typically deeper than the stale
        #    override (that's how the longest-match rule bypasses the
        #    override), but the category fires on any verified
        #    replacement regardless of depth so cross-namespace or
        #    same-depth corrections are also surfaced.
        # 2. OVERRIDE_SHADOWED — generic drift. The manifest's value
        #    differs from what a fresh resolve would produce for any
        #    reason other than the above (manual edit, older tool
        #    version, upstream changes between collection and audit).
        if fresh.project != current_mapping:
            if self._is_stale_override_with_fix(
                image_name,
                current_mapping,
                fresh,
            ):
                return ValidationFinding(
                    category=ValidationCategory.STALE_OVERRIDE_WITH_FIX,
                    severity=ValidationSeverity.ERROR,
                    image=image_name,
                    current_mapping=current_mapping,
                    suggested_mapping=fresh.project,
                    reason=(
                        f"Override for {image_name!r} points at "
                        f"{current_mapping!r} which is not a known "
                        "Gerrit project. The mapper selected a "
                        f"verified replacement {fresh.project!r} via "
                        f"{fresh.reason.value}. Update or remove the "
                        "override so the table reflects reality."
                    ),
                    alternatives=list(fresh.alternatives),
                )
            return ValidationFinding(
                category=ValidationCategory.OVERRIDE_SHADOWED,
                severity=ValidationSeverity.WARNING,
                image=image_name,
                current_mapping=current_mapping,
                suggested_mapping=fresh.project,
                reason=(
                    f"Manifest records {current_mapping!r} for "
                    f"{image_name!r} but a fresh resolve produced "
                    f"{fresh.project!r} via "
                    f"{fresh.reason.value}."
                ),
                alternatives=list(fresh.alternatives),
            )

        # Mapping agrees with fresh resolve — classify based on how it
        # was reached. Stale overrides, unverified heuristics, and
        # ambiguous leaves are all worth flagging even when the
        # manifest is internally consistent.
        return self._classify_result(image_name, fresh)

    def _is_stale_override_with_fix(
        self,
        image_name: str,
        current_mapping: str | None,
        fresh: MappingResult,
    ) -> bool:
        """Detect the "stale override silently corrected" drift case.

        Returns ``True`` when all of the following hold:

        * An explicit override exists for *image_name* in the current
          mapping table.
        * That override resolves to the same value the manifest
          currently records (so the manifest was produced while the
          stale override was in effect).
        * The override's target is NOT a known Gerrit project (i.e.
          it is stale).
        * The fresh resolve produced a different, verified project.

        Together these conditions identify the exact scenario the
        :class:`ValidationCategory.STALE_OVERRIDE_WITH_FIX` signal
        exists to describe: a broken override that the mapper
        superseded with a verified replacement, which reviewers
        should still fix at the data source so the audit stops
        flagging the drift.

        The replacement is typically deeper than the stale override
        (that's usually why the longest-match stage bypassed the
        override in the first place), but this predicate does NOT
        enforce a depth comparison: any verified replacement counts,
        including same-depth cross-namespace leaf matches. The goal
        is to surface every stale override the algorithm silently
        corrected, not only the deeper-path subset.

        Args:
            image_name: Image reference under audit.
            current_mapping: Manifest's recorded project path.
            fresh: Result produced by re-running the mapper.

        Returns:
            ``True`` when the drift matches the stale-override-with-fix
            pattern.
        """
        if current_mapping is None or fresh.project is None:
            return False
        if not fresh.verified:
            return False

        # Look up any override the mapper holds for this image. Try
        # both the raw name and the onap/-stripped form to mirror the
        # mapper's own two-key lookup. Cache the mappings dict once
        # because ``ImageMapper.mappings`` returns a shallow copy on
        # every access; reading it twice in the same expression would
        # allocate two full copies per call on a path that can run
        # per-image when drift is widespread.
        mappings = self._mapper.mappings
        stripped = image_name
        if stripped.startswith("onap/"):
            stripped = stripped[len("onap/") :]
        override = mappings.get(image_name) or mappings.get(stripped)
        if override is None or override != current_mapping:
            return False

        # Override is in play and matches what the manifest recorded.
        # Classify as stale-with-fix only when the override itself is
        # not present in Gerrit ground truth.
        return override not in self._mapper.known_projects

    def _classify_result(
        self,
        image_name: str,
        result: MappingResult,
    ) -> ValidationFinding | None:
        """Classify a resolution result into a finding, or clear it.

        Args:
            image_name: Image reference under audit.
            result: The mapping result produced by the fresh resolve.

        Returns:
            A :class:`ValidationFinding` when noteworthy, ``None``
            when the mapping is clean and uninteresting.
        """
        reason = result.reason

        if reason is MappingReason.OVERRIDE_STALE:
            # The override resolves to a repo Gerrit doesn't have.
            # When the longest-match algorithm produced a deeper
            # verified replacement elsewhere in the candidate set,
            # the fresh result's reason would NOT be OVERRIDE_STALE —
            # it would be a LEAF_MATCH_*. So if we see OVERRIDE_STALE
            # here, no better replacement was found automatically.
            return ValidationFinding(
                category=ValidationCategory.STALE_OVERRIDE,
                severity=ValidationSeverity.ERROR,
                image=image_name,
                current_mapping=result.project,
                reason=(
                    f"Override for {image_name!r} points at "
                    f"{result.project!r} which is not a known Gerrit "
                    "project. Review and either correct the override "
                    "or remove it."
                ),
            )

        if reason in (
            MappingReason.HEURISTIC_ORG_ONAP_UNVERIFIED,
            MappingReason.HEURISTIC_DASH_UNVERIFIED,
            MappingReason.HEURISTIC_SLASH_UNVERIFIED,
        ):
            return ValidationFinding(
                category=ValidationCategory.HEURISTIC_UNVERIFIED,
                severity=ValidationSeverity.WARNING,
                image=image_name,
                current_mapping=result.project,
                reason=(
                    f"Image {image_name!r} was mapped to "
                    f"{result.project!r} via the "
                    f"{reason.value} heuristic, but the result does "
                    "not match any known Gerrit project. Add an "
                    "explicit override or investigate."
                ),
                detail={"heuristic": reason.value},
            )

        if reason is MappingReason.LEAF_MATCH_CROSS_NAMESPACE:
            # Cross-namespace leaf matches are worth surfacing even
            # when verified because they indicate the image may
            # belong in a different top-level project than its name
            # suggests. Usually correct, but worth a review.
            return ValidationFinding(
                category=ValidationCategory.CROSS_NAMESPACE_FALLBACK,
                severity=ValidationSeverity.INFO,
                image=image_name,
                current_mapping=result.project,
                reason=(
                    f"Image {image_name!r} was mapped to "
                    f"{result.project!r} by matching its leaf segment "
                    "across top-level namespaces. Confirm this is the "
                    "intended attribution."
                ),
                alternatives=list(result.alternatives),
            )

        if result.alternatives:
            # Multiple repos shared the image's leaf within the
            # winning namespace. The tiebreak (longest path then
            # alphabetical) picked one, but reviewers should know
            # there were siblings.
            return ValidationFinding(
                category=ValidationCategory.AMBIGUOUS_LEAF,
                severity=ValidationSeverity.INFO,
                image=image_name,
                current_mapping=result.project,
                reason=(
                    f"Image {image_name!r} leaf segment matched "
                    f"{len(result.alternatives) + 1} Gerrit projects. "
                    f"Longest-match chose {result.project!r}. "
                    "Confirm this is the intended attribution."
                ),
                alternatives=list(result.alternatives),
            )

        return None

    # ------------------------------------------------------------------
    # Report assembly
    # ------------------------------------------------------------------

    def _finalise(
        self,
        findings: list[ValidationFinding],
    ) -> ValidationReport:
        """Assemble findings into a sorted, counted :class:`ValidationReport`.

        Args:
            findings: Unsorted findings accumulated during the audit.

        Returns:
            The final report.
        """
        severity_order = {
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.INFO: 2,
        }
        findings.sort(
            key=lambda f: (
                severity_order[f.severity],
                f.category.value,
                f.image or "",
            )
        )

        counts: dict[str, int] = {}
        for finding in findings:
            sev_key = f"severity:{finding.severity.value}"
            cat_key = f"category:{finding.category.value}"
            counts[sev_key] = counts.get(sev_key, 0) + 1
            counts[cat_key] = counts.get(cat_key, 0) + 1

        errors = sum(1 for f in findings if f.severity is ValidationSeverity.ERROR)
        warnings = sum(1 for f in findings if f.severity is ValidationSeverity.WARNING)
        infos = sum(1 for f in findings if f.severity is ValidationSeverity.INFO)

        passed = errors == 0

        summary = (
            f"{errors} error(s), {warnings} warning(s), {infos} info"
            if findings
            else "All image mappings verified against Gerrit ground truth"
        )

        return ValidationReport(
            validator=self.name,
            passed=passed,
            summary=summary,
            counts=dict(sorted(counts.items())),
            findings=findings,
        )


__all__ = [
    "MappingAuditValidator",
]

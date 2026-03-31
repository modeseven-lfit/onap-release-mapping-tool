# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Map Docker image names to their source Gerrit project paths."""

from __future__ import annotations

import logging
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


class ImageMapper:
    """Map Docker image names to their source Gerrit project paths."""

    def __init__(self, mapping_file: Path | None = None) -> None:
        """Initialise the mapper with default and optional override mappings.

        Args:
            mapping_file: Optional path to a YAML file with additional or
                overriding image-to-project mappings.
        """
        self._logger = logging.getLogger(__name__)
        self._mappings: dict[str, str] = {}
        self._load_default_mappings()
        if mapping_file:
            self._load_override_mappings(mapping_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_image(self, image_name: str) -> str | None:
        """Return the Gerrit project path for *image_name*, or ``None``.

        Resolution order:
        1. Explicit lookup in loaded mappings.
        2. ``org.onap.<a>.<b>…`` → ``<a>/<b>``.
        3. Slash-separated path: ``onap/<project>/<sub>`` → ``<project>/<sub>``.
        4. Dash-separated with known prefix → ``<proj>/<sub>``.
        5. ``None`` when nothing matches.

        Args:
            image_name: Docker image name, e.g. ``onap/policy-api``.

        Returns:
            Gerrit project path or ``None``.
        """
        # Strip leading registry prefix if present (e.g. nexus3.onap.org:10001/)
        normalised = self._strip_registry(image_name)

        # 1. Explicit mapping
        if normalised in self._mappings:
            return self._mappings[normalised]

        # Also try without the "onap/" prefix
        without_prefix = self._strip_onap_prefix(normalised)
        if without_prefix in self._mappings:
            return self._mappings[without_prefix]

        # Heuristics only apply to images from the onap namespace
        is_onap = normalised.startswith("onap/")

        # 2. org.onap.<a>.<b>.* heuristic
        if is_onap:
            result = self._heuristic_org_onap(without_prefix)
            if result is not None:
                return result

        # 3. Slash-separated path pass-through
        if is_onap:
            result = self._heuristic_slash(without_prefix)
            if result is not None:
                return result

        # 4. Dash-to-slash with known top-level project
        if is_onap:
            result = self._heuristic_dash(without_prefix)
            if result is not None:
                return result

        self._logger.debug("No mapping found for image: %s", image_name)
        return None

    @staticmethod
    def get_top_level_project(gerrit_project: str) -> str:
        """Extract the top-level project from a Gerrit path.

        Examples:
            ``policy/api`` → ``policy``
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
            path: Path to a YAML file whose top-level keys are image names
                and values are Gerrit project paths.
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

        The YAML structure is expected to be a flat mapping of image name
        (string) to Gerrit project path (string).  Nested structures with a
        ``mappings`` key are also accepted.

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
        # Try each known prefix, longest-first to prefer portal-ng over portal
        for prefix in _KNOWN_PREFIXES_LONGEST_FIRST:
            dash_prefix = prefix + "-"
            if name.startswith(dash_prefix):
                remainder = name[len(dash_prefix) :]
                if remainder:
                    return f"{prefix}/{remainder}"
        return None

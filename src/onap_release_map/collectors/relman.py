# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Release management collector — parses relman repos.yaml for maintenance status."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import quote

from onap_release_map.collectors import BaseCollector, CollectorResult, registry
from onap_release_map.models import OnapRepository
from onap_release_map.parsers.yaml_utils import safe_load_yaml


def _parse_bool(value: object) -> bool:
    """Interpret a string or native boolean as Python ``bool``.

    The relman ``repos.yaml`` encodes booleans as quoted YAML strings
    (``'true'`` / ``'false'``), but we also handle native booleans and
    mixed-case variants so the collector is resilient to format drift.

    Args:
        value: A string (``"true"``/``"false"``) or native ``bool``.

    Returns:
        The corresponding Python boolean.  Unrecognised values are
        treated as ``False``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


@registry.register
class RelmanCollector(BaseCollector):
    """Collect repository metadata from the ONAP relman ``repos.yaml``.

    The release-management repository maintains a canonical list of
    every ONAP Gerrit project together with its maintenance and
    read-only status.  This collector converts those entries into
    :class:`~onap_release_map.models.OnapRepository` objects with
    ``confidence="medium"`` because the file is an authoritative
    roster but does not carry image or Helm-chart detail.
    """

    name = "relman"

    _DEFAULT_GERRIT_URL = "https://gerrit.onap.org/r"

    def __init__(
        self,
        repos_yaml_path: Path | None = None,
        gerrit_url: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialise the relman collector.

        Args:
            repos_yaml_path: Filesystem path to the relman
                ``repos.yaml`` file.  Must be supplied before
                :meth:`collect` is called.
            gerrit_url: Base URL of the Gerrit instance used to
                build per-repository links.  Defaults to the
                public ONAP Gerrit.
            **kwargs: Additional keyword arguments (ignored).
        """
        super().__init__()
        self.repos_yaml_path = repos_yaml_path
        self._gerrit_url = (gerrit_url or self._DEFAULT_GERRIT_URL).rstrip("/")

    def collect(self, **kwargs: object) -> CollectorResult:
        """Parse ``repos.yaml`` and return repository objects.

        Raises:
            ValueError: If *repos_yaml_path* was not provided.

        Returns:
            A :class:`CollectorResult` containing one
            :class:`OnapRepository` per entry in the YAML file.
        """
        if self.repos_yaml_path is None:
            raise ValueError("repos_yaml_path is required for RelmanCollector")

        self._logger.info(
            "Loading relman repos.yaml from %s",
            self.repos_yaml_path,
        )

        data = safe_load_yaml(self.repos_yaml_path)
        if not data:
            self._logger.warning("No data parsed from %s", self.repos_yaml_path)
            return CollectorResult()

        repositories: list[OnapRepository] = []

        for top_level_project, entries in data.items():
            if not isinstance(entries, list):
                self._logger.warning(
                    "Expected a list under '%s', got %s; skipping",
                    top_level_project,
                    type(entries).__name__,
                )
                continue

            for entry in entries:
                if not isinstance(entry, dict):
                    self._logger.warning(
                        "Non-dict entry under '%s'; skipping",
                        top_level_project,
                    )
                    continue

                repo = self._build_repository(entry, top_level_project)
                if repo is not None:
                    repositories.append(repo)

        repositories.sort(key=lambda r: r.gerrit_project)

        self._logger.info(
            "Collected %d repositories from relman",
            len(repositories),
        )

        return CollectorResult(repositories=repositories)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_repository(
        self,
        entry: dict[str, object],
        top_level_project: str,
    ) -> OnapRepository | None:
        """Convert a single YAML entry to an ``OnapRepository``.

        Args:
            entry: Dictionary with ``repository``, ``unmaintained``,
                ``read_only``, and ``included_in`` keys.
            top_level_project: The top-level YAML key that groups
                this entry (e.g. ``"policy"``).

        Returns:
            An ``OnapRepository`` instance, or ``None`` when the
            entry lacks a ``repository`` field.
        """
        gerrit_project = entry.get("repository")
        if not gerrit_project or not isinstance(gerrit_project, str):
            self._logger.warning(
                "Entry under '%s' missing 'repository'; skipping",
                top_level_project,
            )
            return None

        unmaintained = _parse_bool(entry.get("unmaintained", False))
        read_only = _parse_bool(entry.get("read_only", False))

        maintained = not unmaintained
        gerrit_state: Literal["ACTIVE", "READ_ONLY"] = (
            "READ_ONLY" if read_only else "ACTIVE"
        )

        # Repos that are both read-only AND unmaintained are legacy
        # build dependencies; everything else is treated as runtime.
        category: Literal[
            "runtime",
            "build-dependency",
            "infrastructure",
            "test",
            "documentation",
            "tooling",
        ]
        if read_only and unmaintained:
            category = "build-dependency"
        else:
            category = "runtime"

        gerrit_url = (
            f"{self._gerrit_url}/admin/repos/{quote(gerrit_project, safe='')}"
        )

        return OnapRepository(
            gerrit_project=gerrit_project,
            top_level_project=top_level_project,
            gerrit_url=gerrit_url,
            confidence="medium",
            confidence_reasons=[
                "Listed in relman repos.yaml",
            ],
            category=category,
            gerrit_state=gerrit_state,
            maintained=maintained,
            discovered_by=["relman"],
        )

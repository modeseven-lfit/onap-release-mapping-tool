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


def _parse_included_in(value: object) -> list[str]:
    """Parse the ``included_in`` field from repos.yaml.

    The field may be a YAML list, a string representation of a list
    (e.g. ``'[]'`` or ``'[\"Montreal\"]'``), or ``None``.

    Args:
        value: Raw value from the YAML entry.

    Returns:
        A list of release name strings (may be empty).
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in ("[]", ""):
            return []
        # Handle string like '["Montreal", "Rabat"]'
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1]
            parts = [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
            return [p for p in parts if p]
        return [stripped]
    return []


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

        # Detect parent projects: a project is a parent if another
        # project exists beneath it as a slash-delimited child path.
        parent_projects: set[str] = set()
        for repo in repositories:
            parts = repo.gerrit_project.split("/")
            for index in range(1, len(parts)):
                parent_projects.add("/".join(parts[:index]))

        for repo in repositories:
            if repo.gerrit_project in parent_projects:
                repo.is_parent_project = True

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
        included_in = _parse_included_in(entry.get("included_in"))

        maintained = not unmaintained
        gerrit_state: Literal["ACTIVE", "READ_ONLY"] = (
            "READ_ONLY" if read_only else "ACTIVE"
        )

        # Determine release inclusion from relman data.
        # READ_ONLY repos are archived and definitively not
        # in the current release.  Active repos with a
        # non-empty included_in list are treated as likely in
        # the release (the field lists release names, but the
        # collector does not yet know the *current* release
        # name, so any inclusion signal is taken as positive).
        # Active repos with an empty included_in list are left
        # undetermined (None); the manifest builder may later
        # set this to True if OOM discovers them.
        in_current_release: bool | None
        if read_only:
            in_current_release = False
        elif included_in:
            in_current_release = True
        else:
            in_current_release = None

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

        gerrit_url = f"{self._gerrit_url}/admin/repos/{quote(gerrit_project, safe='')}"

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
            in_current_release=in_current_release,
            maintained=maintained,
            discovered_by=["relman"],
        )

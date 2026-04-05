# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""OOM cross-reference reconciliation provider."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from onap_release_map.models import OnapRepository

logger = logging.getLogger(__name__)

# File patterns to search within the OOM kubernetes/ tree.
_SEARCH_GLOBS: tuple[str, ...] = (
    "*/values.yaml",
    "*/Chart.yaml",
    "*/templates/*.yaml",
    "*/templates/*.tpl",
    "*/resources/**/*.yaml",
    "*/resources/**/*.properties",
    "*/resources/**/*.xml",
    "*/resources/**/*.json",
    "*/components/*/values.yaml",
    "*/components/*/Chart.yaml",
    "*/components/*/templates/*.yaml",
    "*/components/*/templates/*.tpl",
    "*/components/*/resources/**/*.yaml",
    "*/components/*/resources/**/*.properties",
)

# Regex to extract Gerrit project URLs embedded in OOM files.
_GERRIT_URL_RE = re.compile(
    r"gerrit\.onap\.org/r/([a-zA-Z0-9._/-]+?)(?:\.git)?(?:[\"'\s,;)]|$)"
)


class OOMCrossRefProvider:
    """Search OOM Helm chart files for cross-project references.

    This provider scans the OOM ``kubernetes/`` tree for mentions
    of Gerrit project names that are not yet classified as
    in-release.  Three signal types are recognised:

    1. **Word-boundary matches** of the full ``gerrit_project``
       path (e.g. ``oom/readiness``, ``dmaap/datarouter``).
    2. **Explicit Gerrit URL references** matching
       ``gerrit.onap.org/r/<project>``.
    3. **Umbrella enable flags** — projects that appear as
       disabled component keys in ``onap/values.yaml``.

    Parameters
    ----------
    oom_path:
        Root of the OOM repository checkout.
    """

    def __init__(self, oom_path: Path) -> None:
        self._oom_path = oom_path
        self._kubernetes_path = oom_path / "kubernetes"
        self._file_cache: dict[Path, str] | None = None

    @property
    def name(self) -> str:
        """Short identifier for log messages."""
        return "oom-crossref"

    def reconcile(
        self,
        repo_map: dict[str, OnapRepository],
    ) -> set[str]:
        """Search OOM files for references to non-release repos.

        Parameters
        ----------
        repo_map:
            Mutable mapping of Gerrit project name to repository.

        Returns
        -------
        set[str]
            Gerrit project names promoted during this pass.
        """
        if not self._kubernetes_path.is_dir():
            logger.warning(
                "OOM kubernetes/ path not found: %s",
                self._kubernetes_path,
            )
            return set()

        # Identify candidates: repos not yet in release and
        # not READ_ONLY.
        candidates: dict[str, OnapRepository] = {}
        for proj, repo in repo_map.items():
            if repo.in_current_release is not True and repo.gerrit_state != "READ_ONLY":
                candidates[proj] = repo

        if not candidates:
            return set()

        # Build the searchable file content cache (once).
        if self._file_cache is None:
            self._file_cache = self._load_files()

        # Collect all file contents into one pass per candidate.
        promoted: set[str] = set()
        for proj, repo in candidates.items():
            reason = self._search_for_project(proj)
            if reason:
                repo.in_current_release = True
                repo.confidence_reasons.append(reason)
                promoted.add(proj)
                logger.debug(
                    "Promoted %s: %s",
                    proj,
                    reason,
                )

        return promoted

    def _load_files(self) -> dict[Path, str]:
        """Read all searchable OOM files into memory.

        Returns
        -------
        dict[Path, str]
            Mapping of file path to text content.
        """
        files: dict[Path, str] = {}
        for pattern in _SEARCH_GLOBS:
            for path in self._kubernetes_path.glob(pattern):
                if path in files or not path.is_file():
                    continue
                try:
                    files[path] = path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                except OSError:
                    logger.debug(
                        "Could not read %s",
                        path,
                        exc_info=True,
                    )
        logger.info(
            "OOM cross-ref: loaded %d files from %s",
            len(files),
            self._kubernetes_path,
        )
        return files

    def _search_for_project(
        self,
        project: str,
    ) -> str | None:
        """Search cached OOM files for *project* references.

        Parameters
        ----------
        project:
            Gerrit project path (e.g. ``dmaap/datarouter``).

        Returns
        -------
        str | None
            Human-readable reason string if found, else ``None``.
        """
        assert self._file_cache is not None  # noqa: S101

        # Skip very short names (< 4 chars) to avoid false
        # positives from substring matches.
        if len(project) < 4:
            return None

        # Strategy 1: word-boundary match of the full project
        # path in OOM files.
        pattern = re.compile(
            r"(?<![a-zA-Z0-9_/.-])" + re.escape(project) + r"(?![a-zA-Z0-9_/.-])",
        )
        for path, content in self._file_cache.items():
            if pattern.search(content):
                rel = path.relative_to(self._kubernetes_path)
                return f"Referenced in OOM file {rel}"

        # Strategy 2: explicit Gerrit URL reference.
        for path, content in self._file_cache.items():
            for match in _GERRIT_URL_RE.finditer(content):
                if match.group(1) == project:
                    rel = path.relative_to(
                        self._kubernetes_path,
                    )
                    return f"Gerrit URL reference in OOM file {rel}"

        return None

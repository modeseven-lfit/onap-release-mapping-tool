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
    in-release.  Two signal types are recognised:

    1. **Word-boundary matches** of the full ``gerrit_project``
       path (e.g. ``oom/readiness``, ``dmaap/datarouter``).
    2. **Explicit Gerrit URL references** matching
       ``gerrit.onap.org/r/<project>``.

    Parameters
    ----------
    oom_path:
        Root of the OOM repository checkout.
    """

    def __init__(self, oom_path: Path) -> None:
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

        # Scan files once for all candidates (inverted search).
        found = self._search_all_candidates(candidates)

        promoted: set[str] = set()
        for proj, reason in found.items():
            repo = candidates[proj]
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

    def _search_all_candidates(
        self,
        candidates: dict[str, OnapRepository],
    ) -> dict[str, str]:
        """Scan cached OOM files once for all candidate projects.

        Instead of iterating files per candidate (O(candidates ×
        files)), this method scans every file once and checks all
        remaining candidates against it, removing matches as they
        are found.

        Parameters
        ----------
        candidates:
            Mapping of Gerrit project name to repository for
            repos not yet in release.

        Returns
        -------
        dict[str, str]
            Mapping of promoted project name to human-readable
            reason string.
        """
        assert self._file_cache is not None  # noqa: S101

        found: dict[str, str] = {}

        # Filter to candidates with names long enough to
        # avoid false-positive substring matches.
        eligible = {p for p in candidates if len(p) >= 4}

        # Strategy 1: extract all Gerrit URLs from files in a
        # single pass and match against candidates.
        remaining = set(eligible)
        for path, content in self._file_cache.items():
            if not remaining:
                break
            for match in _GERRIT_URL_RE.finditer(content):
                proj = match.group(1)
                if proj in remaining:
                    rel = path.relative_to(
                        self._kubernetes_path,
                    )
                    found[proj] = f"Gerrit URL reference in OOM file {rel}"
                    remaining.discard(proj)

        # Strategy 2: word-boundary match — pre-compile one
        # pattern per remaining candidate, then scan each file
        # once against all patterns.
        if remaining:
            patterns: dict[str, re.Pattern[str]] = {
                proj: re.compile(
                    r"(?<![a-zA-Z0-9_/.-])" + re.escape(proj) + r"(?![a-zA-Z0-9_/.-])",
                )
                for proj in remaining
            }
            for path, content in self._file_cache.items():
                if not patterns:
                    break
                newly_found: list[str] = []
                for proj, pattern in patterns.items():
                    if pattern.search(content):
                        rel = path.relative_to(
                            self._kubernetes_path,
                        )
                        found[proj] = f"Referenced in OOM file {rel}"
                        newly_found.append(proj)
                for proj in newly_found:
                    del patterns[proj]

        return found

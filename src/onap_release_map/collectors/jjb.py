# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""JJB collector — discovers repositories with CI jobs in ci-management."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

import yaml

from onap_release_map.collectors import BaseCollector, CollectorResult, registry
from onap_release_map.models import OnapRepository


def _jjb_tag_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> object:
    """Construct any JJB custom-tag node as a no-op placeholder.

    Handles scalar nodes (``!include-raw-escape: script.sh``) and
    sequence nodes (``!include-raw-escape:\\n  - a.sh\\n  - b.sh``)
    so the rest of the document can still be parsed for ``project:``
    metadata.

    Args:
        loader: The YAML loader instance.
        node: The tagged YAML node.

    Returns:
        The scalar string or list of strings under the tag.
    """
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return None


class _JJBSafeLoader(yaml.SafeLoader):
    """``SafeLoader`` with no-op constructors for JJB custom tags.

    Jenkins Job Builder YAML files use custom tags such as
    ``!include-raw:``, ``!include-raw-escape:``, and
    ``!include-jinja2:`` to inline shell scripts at parse time.
    Standard ``SafeLoader`` raises ``ConstructorError`` for these
    unknown tags.  This loader treats them as plain values so the
    rest of the document can be parsed for ``project:`` metadata.
    """


# Register no-op constructors for every JJB include variant.
# Both forms (with and without trailing colon) are needed because
# PyYAML's tag resolution treats them differently depending on
# whitespace after the tag.
_JJB_CUSTOM_TAGS = (
    "!include-raw:",
    "!include-raw-escape:",
    "!include-jinja2:",
    "!include-raw",
    "!include-raw-escape",
    "!include-jinja2",
)

for _tag in _JJB_CUSTOM_TAGS:
    _JJBSafeLoader.add_constructor(_tag, _jjb_tag_constructor)


# Regex matching a YAML document-start marker on its own line.
_YAML_DOC_BOUNDARY = re.compile(r"^---[ \t]*$", re.MULTILINE)


def _iter_yaml_documents(
    content: str, path: Path, logger: logging.Logger
) -> Iterator[object]:
    """Yield YAML documents from *content*, skipping failures.

    Uses :class:`_JJBSafeLoader` so JJB custom tags are accepted.
    The raw text is split on ``---`` document boundaries and each
    chunk is parsed with an independent loader so that a parse
    error in one document cannot prevent earlier or later documents
    from being returned.

    Args:
        content: Raw YAML text (may contain multiple documents).
        path: Source file path, used only for log messages.
        logger: Logger for parse-error warnings.

    Yields:
        Parsed YAML documents.
    """
    raw_docs = _YAML_DOC_BOUNDARY.split(content)
    for raw_doc in raw_docs:
        if not raw_doc.strip():
            continue
        try:
            data = yaml.load(raw_doc, Loader=_JJBSafeLoader)  # noqa: S506
        except yaml.YAMLError as exc:
            logger.warning("YAML parse error in %s: %s", path, exc)
            continue
        if data is not None:
            yield data


def _is_template_placeholder(value: str) -> bool:
    """Return ``True`` when *value* contains JJB template braces.

    JJB YAML files use ``{project}``, ``{name}``, and similar
    placeholders that should not be treated as real Gerrit project
    paths.

    Args:
        value: The string to check.

    Returns:
        ``True`` if the string contains ``{`` or ``}``.
    """
    return "{" in value or "}" in value


def _extract_projects_from_document(document: object) -> list[dict[str, str]]:
    """Extract Gerrit project entries from a single YAML document.

    A JJB YAML document is typically a list of dicts.  Each dict may
    have a top-level ``"project"`` key whose value is another dict
    containing the actual ``project`` (Gerrit path) and
    ``project-name`` fields.

    Args:
        document: A parsed YAML document (the result of one
            iteration from ``yaml.safe_load_all``).

    Returns:
        A list of dicts with ``"project"`` and optional
        ``"project_name"`` keys representing real Gerrit paths.
    """
    results: list[dict[str, str]] = []

    if not isinstance(document, list):
        return results

    for item in document:
        if not isinstance(item, dict):
            continue

        project_block = item.get("project")
        if not isinstance(project_block, dict):
            continue

        gerrit_project = project_block.get("project")
        if not isinstance(gerrit_project, str) or not gerrit_project.strip():
            continue

        gerrit_project = gerrit_project.strip()
        if _is_template_placeholder(gerrit_project):
            continue

        entry: dict[str, str] = {"project": gerrit_project}

        project_name = project_block.get("project-name")
        if isinstance(project_name, str) and project_name.strip():
            pn = project_name.strip()
            if not _is_template_placeholder(pn):
                entry["project_name"] = pn

        results.append(entry)

    return results


@registry.register
class JJBCollector(BaseCollector):
    """Collect repository data from JJB definitions in ci-management.

    The ONAP ``ci-management`` repository stores Jenkins Job Builder
    YAML files under its ``jjb/`` directory.  Each file may contain
    one or more YAML documents with ``project:`` blocks that reference
    the Gerrit project path a CI job targets.

    This collector walks every ``*.yaml`` file under the provided
    *jjb_path*, extracts unique Gerrit project paths, and emits
    :class:`~onap_release_map.models.OnapRepository` objects with
    ``has_ci=True`` to indicate that the repository has CI coverage.
    """

    name = "jjb"

    def __init__(
        self,
        jjb_path: Path | None = None,
        gerrit_url: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialise the JJB collector.

        Args:
            jjb_path: Filesystem path to the ``jjb/`` directory
                inside a ci-management checkout.  Must be supplied
                before :meth:`collect` is called.
            gerrit_url: Base URL of the Gerrit instance used to
                construct per-repo links.  Defaults to
                ``https://gerrit.onap.org/r``.
            **kwargs: Additional keyword arguments (ignored).
        """
        super().__init__()
        self.jjb_path = jjb_path
        self._gerrit_url = (gerrit_url or "https://gerrit.onap.org/r").rstrip("/")

    def collect(self, **kwargs: object) -> CollectorResult:
        """Parse JJB YAML files and return repository objects.

        Walks all ``*.yaml`` files recursively under *jjb_path*,
        extracts Gerrit project references, deduplicates them, and
        returns one :class:`OnapRepository` per unique project.

        Raises:
            ValueError: If *jjb_path* was not provided.

        Returns:
            A :class:`CollectorResult` containing one
            :class:`OnapRepository` per unique Gerrit project
            discovered in JJB definitions.
        """
        if self.jjb_path is None:
            raise ValueError("jjb_path is required for JJBCollector")

        self._logger.info("Scanning JJB definitions under %s", self.jjb_path)

        # Map gerrit_project -> first project_name seen (if any)
        seen_projects: dict[str, str | None] = {}
        yaml_files = sorted(self.jjb_path.rglob("*.yaml"))

        if not yaml_files:
            self._logger.warning("No YAML files found under %s", self.jjb_path)
            return CollectorResult()

        self._logger.debug("Found %d YAML files to scan", len(yaml_files))

        for yaml_file in yaml_files:
            entries = self._parse_jjb_file(yaml_file)
            for entry in entries:
                proj = entry["project"]
                if proj not in seen_projects:
                    seen_projects[proj] = entry.get("project_name")

        repositories = self._build_repositories(seen_projects, self._gerrit_url)
        repositories.sort(key=lambda r: r.gerrit_project)

        self._logger.info(
            "Collected %d repositories from JJB definitions",
            len(repositories),
        )

        return CollectorResult(repositories=repositories)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_jjb_file(self, path: Path) -> list[dict[str, str]]:
        """Parse a single JJB YAML file for project references.

        Handles multi-document YAML files via
        :func:`_iter_yaml_documents` with :class:`_JJBSafeLoader`.
        Malformed files are logged and skipped rather than raising
        exceptions.

        Args:
            path: Path to the YAML file to parse.

        Returns:
            A list of dicts with ``"project"`` and optional
            ``"project_name"`` keys.
        """
        results: list[dict[str, str]] = []

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._logger.warning("Cannot read JJB file %s: %s", path, exc)
            return results

        for document in _iter_yaml_documents(content, path, self._logger):
            entries = _extract_projects_from_document(document)
            results.extend(entries)

        return results

    @staticmethod
    def _build_repositories(
        projects: dict[str, str | None],
        gerrit_base_url: str,
    ) -> list[OnapRepository]:
        """Convert deduplicated project entries to repository objects.

        Args:
            projects: Mapping of Gerrit project path to optional
                ``project-name`` value.
            gerrit_base_url: Base URL of the Gerrit instance used
                to construct per-repo admin links.

        Returns:
            A list of :class:`OnapRepository` instances.
        """
        repositories: list[OnapRepository] = []

        # project_name is parsed but not yet used; retained for
        # future enrichment (e.g. display names in manifests).
        for gerrit_project, _project_name in projects.items():
            top_level = gerrit_project.split("/")[0]

            gerrit_url = (
                f"{gerrit_base_url}/admin/repos/{quote(gerrit_project, safe='')}"
            )

            repo = OnapRepository(
                gerrit_project=gerrit_project,
                top_level_project=top_level,
                gerrit_url=gerrit_url,
                confidence="medium",
                confidence_reasons=[
                    "Has CI jobs in ci-management JJB",
                ],
                category="runtime",
                has_ci=True,
                discovered_by=["jjb"],
            )
            repositories.append(repo)

        return repositories

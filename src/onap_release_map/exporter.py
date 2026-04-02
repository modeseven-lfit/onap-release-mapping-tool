# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Output format converters for release manifests."""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import yaml

from onap_release_map.exceptions import ExportError

if TYPE_CHECKING:
    from onap_release_map.models import ReleaseManifest

logger = logging.getLogger(__name__)

__all__ = [
    "EXPORT_FORMATS",
    "export_csv",
    "export_gerrit_list",
    "export_manifest",
    "export_markdown",
    "export_yaml",
]


def export_yaml(manifest: ReleaseManifest) -> str:
    """Export a release manifest as YAML.

    Serialises the manifest via Pydantic's ``model_dump`` and
    renders the result with PyYAML using sorted keys and block
    style for readability.

    Parameters
    ----------
    manifest:
        The release manifest to export.

    Returns
    -------
    str
        YAML-formatted string.
    """
    data = manifest.model_dump(mode="json")
    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=True,
        allow_unicode=True,
    )


def export_csv(manifest: ReleaseManifest, *, mode: str = "repos") -> str:
    """Export a release manifest as CSV.

    Two modes are supported:

    * ``repos`` — one row per Gerrit repository
    * ``images`` — one row per Docker image

    List-valued fields are joined with semicolons so that each row
    remains a single CSV record.

    Parameters
    ----------
    manifest:
        The release manifest to export.
    mode:
        Export mode — ``"repos"`` or ``"images"``.

    Returns
    -------
    str
        CSV-formatted string including the header row.

    Raises
    ------
    ExportError
        If *mode* is not ``"repos"`` or ``"images"``.
    """
    logger.debug("Exporting CSV in %s mode", mode)
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

    if mode == "repos":
        writer.writerow(
            [
                "gerrit_project",
                "top_level_project",
                "category",
                "confidence",
                "gerrit_state",
                "maintained",
                "has_ci",
                "discovered_by",
            ]
        )
        for repo in manifest.repositories:
            writer.writerow(
                [
                    repo.gerrit_project,
                    repo.top_level_project,
                    repo.category,
                    repo.confidence,
                    repo.gerrit_state or "",
                    _bool_str(repo.maintained),
                    _bool_str(repo.has_ci),
                    ";".join(repo.discovered_by),
                ]
            )
    elif mode == "images":
        writer.writerow(
            [
                "image",
                "tag",
                "registry",
                "gerrit_project",
                "nexus_validated",
                "helm_charts",
            ]
        )
        for img in manifest.docker_images:
            writer.writerow(
                [
                    img.image,
                    img.tag,
                    img.registry or "",
                    img.gerrit_project or "",
                    _bool_str(img.nexus_validated),
                    ";".join(img.helm_charts),
                ]
            )
    else:
        msg = f"Unknown CSV mode: {mode!r}. Use 'repos' or 'images'."
        raise ExportError(msg)

    return buf.getvalue()


def export_markdown(manifest: ReleaseManifest) -> str:
    """Export a release manifest as a Markdown report.

    Produces a self-contained Markdown document with a title,
    metadata summary, and tables for repositories, Docker images,
    and Helm components.

    Parameters
    ----------
    manifest:
        The release manifest to export.

    Returns
    -------
    str
        Markdown-formatted string.
    """
    release = manifest.onap_release
    lines: list[str] = [
        f"# ONAP Release Manifest: {release.name}",
        "",
        f"- **Generated:** {manifest.generated_at}",
        f"- **Tool version:** {manifest.tool_version}",
        f"- **Schema version:** {manifest.schema_version}",
        f"- **OOM chart version:** {release.oom_chart_version}",
        "",
        "## Summary",
        "",
        f"- **Total repositories:** {len(manifest.repositories)}",
        f"- **Total Docker images:** {len(manifest.docker_images)}",
        f"- **Total Helm components:** {len(manifest.helm_components)}",
        "",
    ]

    # Repositories table
    lines.append("## Repositories")
    lines.append("")
    lines.append(
        "| Gerrit Project | Category | Confidence | State | Maintained | Has CI |"
    )
    lines.append(
        "| -------------- | -------- | ---------- | ----- | ---------- | ------ |"
    )
    for repo in manifest.repositories:
        state = repo.gerrit_state or ""
        maintained = _bool_display(repo.maintained)
        has_ci = _bool_display(repo.has_ci)
        lines.append(
            f"| {repo.gerrit_project} | {repo.category} "
            f"| {repo.confidence} | {state} "
            f"| {maintained} | {has_ci} |"
        )
    lines.append("")

    # Docker images table
    lines.append("## Docker Images")
    lines.append("")
    lines.append("| Image | Tag | Gerrit Project | Registry | Validated |")
    lines.append("| ----- | --- | -------------- | -------- | --------- |")
    for img in manifest.docker_images:
        project = img.gerrit_project or ""
        reg = img.registry or ""
        validated = _bool_display(img.nexus_validated)
        lines.append(f"| {img.image} | {img.tag} | {project} | {reg} | {validated} |")
    lines.append("")

    # Helm components table
    lines.append("## Helm Components")
    lines.append("")
    lines.append("| Name | Version | Enabled | Condition Key |")
    lines.append("| ---- | ------- | ------- | ------------- |")
    for comp in manifest.helm_components:
        version = comp.version or ""
        enabled = _bool_display(comp.enabled_by_default)
        condition = comp.condition_key or ""
        lines.append(f"| {comp.name} | {version} | {enabled} | {condition} |")
    lines.append("")

    return "\n".join(lines)


def export_gerrit_list(manifest: ReleaseManifest) -> str:
    """Export Gerrit project paths as a plain-text list.

    Produces one Gerrit project path per line, sorted
    alphabetically.  The output is compatible with the
    ``projects.txt`` convention used by ONAP integration
    bootstrap scripts.

    Parameters
    ----------
    manifest:
        The release manifest to export.

    Returns
    -------
    str
        Newline-terminated plain-text string.
    """
    logger.debug("Exporting %d Gerrit projects", len(manifest.repositories))
    projects = sorted(r.gerrit_project for r in manifest.repositories)
    if projects:
        return "\n".join(projects) + "\n"
    return ""


def export_manifest(
    manifest: ReleaseManifest,
    fmt: str,
    *,
    mode: str = "repos",
) -> str:
    """Export a manifest in the requested format.

    This is the main dispatcher that delegates to the format-specific
    export functions.

    Parameters
    ----------
    manifest:
        The release manifest to export.
    fmt:
        Output format name — one of ``yaml``, ``csv``, ``md``,
        or ``gerrit-list``.
    mode:
        Sub-mode for CSV export (``"repos"`` or ``"images"``).

    Returns
    -------
    str
        Formatted output string.

    Raises
    ------
    ExportError
        If *fmt* is not a recognised format name.
    """
    logger.info("Exporting manifest as %s", fmt)
    if fmt == "csv":
        return export_csv(manifest, mode=mode)

    handler = EXPORT_FORMATS.get(fmt)
    if handler is None:
        valid_formats = sorted(set(EXPORT_FORMATS.keys()) | {"csv"})
        valid = ", ".join(valid_formats)
        msg = f"Unknown export format: {fmt!r}. Valid formats: {valid}"
        raise ExportError(msg)

    return handler(manifest)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _bool_str(value: bool | None) -> str:
    """Convert an optional boolean to a CSV-friendly string.

    Returns ``"true"``, ``"false"``, or ``""`` for ``None``.
    """
    if value is None:
        return ""
    return str(value).lower()


def _bool_display(value: bool | None) -> str:
    """Convert an optional boolean to a human-friendly string.

    Returns ``"Yes"``, ``"No"``, or empty string for ``None``.
    """
    if value is None:
        return ""
    return "Yes" if value else "No"


EXPORT_FORMATS: dict[str, Callable[[ReleaseManifest], str]] = {
    "yaml": export_yaml,
    "md": export_markdown,
    "gerrit-list": export_gerrit_list,
}
"""Mapping of format names to their export functions."""

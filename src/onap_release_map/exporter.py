# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Output format converters for release manifests."""

from __future__ import annotations

import csv
import html
import io
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import markdown as md_lib
import yaml

from onap_release_map.exceptions import ExportError

if TYPE_CHECKING:
    from onap_release_map.models import ReleaseManifest

logger = logging.getLogger(__name__)

__all__ = [
    "EXPORT_FORMATS",
    "export_csv",
    "export_gerrit_list",
    "export_html",
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


def export_html(manifest: ReleaseManifest) -> str:
    """Export a release manifest as a styled HTML report.

    Converts the Markdown report produced by :func:`export_markdown`
    into a self-contained HTML document with dark-theme styling that
    matches the project's GitHub Pages index page.

    The generated HTML includes inline CSS (no external dependencies),
    responsive tables with hover effects, and a navigation link back
    to the parent index page.

    All manifest-derived string values are HTML-escaped before
    Markdown generation to prevent cross-site scripting (XSS)
    when the report is hosted on GitHub Pages.

    Parameters
    ----------
    manifest:
        The release manifest to export.

    Returns
    -------
    str
        Complete HTML document as a string.
    """
    safe_manifest = _sanitise_manifest(manifest)
    md_text = export_markdown(safe_manifest)
    body_html = md_lib.markdown(md_text, extensions=["tables"])
    title = f"ONAP Release Manifest: {manifest.onap_release.name}"
    return _html_wrapper(body_html, title)


def _html_wrapper(body_html: str, title: str) -> str:
    """Wrap an HTML fragment in a full dark-themed HTML document.

    Provides the ``<!DOCTYPE html>`` scaffold, inline CSS using the
    same design tokens as the GitHub Pages index, and table-specific
    styling for borders, padding, striped rows, and hover effects.

    Parameters
    ----------
    body_html:
        Inner HTML content to place inside ``<body>``.
    title:
        Text for the ``<title>`` element.

    Returns
    -------
    str
        Complete HTML document as a string.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport"'
        ' content="width=device-width, initial-scale=1">\n'
        f"  <title>{html.escape(title)}</title>\n"
        "  <style>\n"
        "    :root {\n"
        "      --bg: #0d1117; --fg: #c9d1d9;\n"
        "      --card-bg: #161b22;\n"
        "      --border: #30363d;\n"
        "      --accent: #58a6ff;\n"
        "      --green: #3fb950;\n"
        "    }\n"
        "    * { box-sizing: border-box;"
        " margin: 0; padding: 0; }\n"
        "    body {\n"
        "      font-family: -apple-system,"
        " BlinkMacSystemFont, "
        '"Segoe UI",\n'
        "                   Helvetica, Arial,"
        " sans-serif;\n"
        "      background: var(--bg);"
        " color: var(--fg);\n"
        "      max-width: 960px;"
        " margin: 0 auto; padding: 2rem 1rem;\n"
        "    }\n"
        "    a { color: var(--accent);"
        " text-decoration: none; }\n"
        "    a:hover { text-decoration: underline; }\n"
        "    .back-link {\n"
        "      display: inline-block;\n"
        "      margin-bottom: 1.5rem;\n"
        "      font-size: 0.9rem;\n"
        "    }\n"
        "    h1 { color: var(--accent);"
        " margin-bottom: 0.5rem; }\n"
        "    h2 { color: var(--accent);"
        " margin-top: 2rem;"
        " margin-bottom: 0.75rem; }\n"
        "    ul { margin: 0.5rem 0 1rem 1.5rem; }\n"
        "    li { margin-bottom: 0.25rem; }\n"
        "    table {\n"
        "      width: 100%;\n"
        "      border-collapse: collapse;\n"
        "      margin-bottom: 1.5rem;\n"
        "      background: var(--card-bg);\n"
        "      border: 1px solid var(--border);\n"
        "      border-radius: 6px;\n"
        "      overflow: hidden;\n"
        "    }\n"
        "    th, td {\n"
        "      padding: 0.6rem 0.75rem;\n"
        "      text-align: left;\n"
        "      border-bottom:"
        " 1px solid var(--border);\n"
        "    }\n"
        "    th {\n"
        "      background: var(--border);\n"
        "      color: var(--fg);\n"
        "      font-weight: 600;\n"
        "      cursor: default;\n"
        "    }\n"
        "    tr:nth-child(even) td {\n"
        "      background: rgba(99,110,123,0.08);\n"
        "    }\n"
        "    tr:hover td {\n"
        "      background: rgba(88,166,255,0.1);\n"
        "    }\n"
        "    footer {\n"
        "      margin-top: 3rem; color: #8b949e;\n"
        "      font-size: 0.85rem;\n"
        "    }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <a class="back-link"'
        ' href="../">&larr; Back to index</a>\n'
        f"  {body_html}\n"
        "  <footer>\n"
        "    <p>Generated by\n"
        '      <a href="https://github.com/'
        "modeseven-lfit/"
        'onap-release-mapping-tool">\n'
        "        onap-release-mapping-tool\n"
        "      </a>\n"
        "    </p>\n"
        "  </footer>\n"
        "</body>\n"
        "</html>\n"
    )


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


def _sanitise_manifest(manifest: ReleaseManifest) -> ReleaseManifest:
    """Return a deep copy of *manifest* with strings HTML-escaped.

    Escapes HTML special characters (``&``, ``<``, ``>``, ``"``,
    ``'``) **and** Markdown link metacharacters (``[``, ``]``) in
    all user-facing string fields so that the resulting Markdown —
    and therefore the HTML produced from it — is safe against
    cross-site scripting (XSS) and Markdown injection (e.g.
    ``[click](javascript:...)``).

    Parameters
    ----------
    manifest:
        The release manifest to sanitise.

    Returns
    -------
    ReleaseManifest
        A new manifest instance with escaped string values.
    """
    data = manifest.model_dump(mode="json")

    # Escape manifest-level metadata fields
    for key in ("generated_at", "tool_version", "schema_version"):
        if key in data and isinstance(data[key], str):
            data[key] = _esc(data[key])

    # Escape release-level fields
    rel = data.get("onap_release", {})
    for key in ("name", "oom_chart_version"):
        if key in rel and isinstance(rel[key], str):
            rel[key] = _esc(rel[key])

    # Escape repository fields
    for repo in data.get("repositories", []):
        for key in (
            "gerrit_project",
            "top_level_project",
            "category",
            "confidence",
            "gerrit_state",
        ):
            if key in repo and isinstance(repo[key], str):
                repo[key] = _esc(repo[key])
        if "discovered_by" in repo:
            repo["discovered_by"] = [_esc(v) for v in repo["discovered_by"]]

    # Escape Docker image fields
    for img in data.get("docker_images", []):
        for key in ("image", "tag", "registry", "gerrit_project"):
            if key in img and isinstance(img[key], str):
                img[key] = _esc(img[key])
        if "helm_charts" in img:
            img["helm_charts"] = [_esc(v) for v in img["helm_charts"]]

    # Escape Helm component fields
    for comp in data.get("helm_components", []):
        for key in ("name", "version", "condition_key"):
            if key in comp and isinstance(comp[key], str):
                comp[key] = _esc(comp[key])

    from onap_release_map.models import ReleaseManifest as RM

    result: ReleaseManifest = RM.model_validate(data)
    return result


def _esc(value: str) -> str:
    """Escape HTML special chars and Markdown link metacharacters.

    Applies :func:`html.escape` first, then replaces ``[`` and
    ``]`` with their HTML entities so that Markdown link syntax
    such as ``[click](javascript:...)`` is neutralised before
    the value reaches :func:`markdown.markdown`.

    Parameters
    ----------
    value:
        Raw string to escape.

    Returns
    -------
    str
        Escaped string safe for Markdown-to-HTML conversion.
    """
    escaped = html.escape(value)
    return escaped.replace("[", "&#91;").replace("]", "&#93;")


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
    "gerrit-list": export_gerrit_list,
    "html": export_html,
    "md": export_markdown,
    "yaml": export_yaml,
}
"""Mapping of format names to their export functions."""

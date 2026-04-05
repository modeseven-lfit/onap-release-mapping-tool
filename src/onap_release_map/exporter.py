# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Output format converters for release manifests."""

from __future__ import annotations

import csv
import html
import io
import logging
from collections.abc import Callable, Sequence
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
    "filter_repositories",
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
                "in_current_release",
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
                    _bool_str(repo.in_current_release),
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
        state = _state_emoji(repo)
        maintained = _bool_display(repo.maintained)
        has_ci = _bool_display(repo.has_ci)
        lines.append(
            f"| {repo.gerrit_project} | {repo.category} "
            f"| {repo.confidence} | {state} "
            f"| {maintained} | {has_ci} |"
        )
    lines.append("")

    lines.extend(_totals_section(manifest.repositories))

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
    into a single HTML document with dark-theme styling that
    matches the project's GitHub Pages index page.

    The generated HTML includes inline CSS and CDN-hosted
    Simple-DataTables for interactive table features, responsive
    tables with hover effects, and a navigation link back to the
    parent index page.

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

    # Add dt-enabled class to all tables for DataTables init
    body_html = body_html.replace("<table>", '<table class="dt-enabled">')

    # Inject state legend between the Repositories heading and its table
    legend_html = (
        '<div class="state-legend">\n'
        "    <p><strong>State Legend</strong></p>\n"
        "    <p>\u2705 In current ONAP release</p>\n"
        "    <p>\u2611\ufe0f Parent project"
        " (children in release)</p>\n"
        "    <p>\u274c Not in current ONAP release</p>\n"
        "    <p>\u2753 Undetermined</p>\n"
        "    <p>\U0001f4e6 Read-only / archived</p>\n"
        "  </div>\n"
    )
    repos_heading = "<h2>Repositories</h2>"
    idx = body_html.find(repos_heading)
    if idx != -1:
        insert_at = idx + len(repos_heading)
        body_html = body_html[:insert_at] + "\n  " + legend_html + body_html[insert_at:]

    title = f"ONAP Release Manifest: {manifest.onap_release.name}"
    return _html_wrapper(body_html, title)


def _html_wrapper(body_html: str, title: str) -> str:
    """Wrap an HTML fragment in a full dark-themed HTML document.

    Provides the ``<!DOCTYPE html>`` scaffold, inline CSS using the
    same design tokens as the GitHub Pages index, table-specific
    styling for borders, padding, striped rows, and hover effects,
    and Simple-DataTables integration for search and column sorting.

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
        "  <!-- Simple-DataTables CSS -->\n"
        '  <link href="https://cdn.jsdelivr.net/npm/'
        'simple-datatables@9/dist/style.css"'
        ' rel="stylesheet" type="text/css">\n'
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
        "      max-width: 1200px;"
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
        #
        # DataTables dark-theme overrides
        #
        "    /* DataTables wrapper */\n"
        "    .dataTable-wrapper {\n"
        "      margin: 1.5em 0;\n"
        "    }\n"
        "    .dataTable-top {\n"
        "      display: flex;\n"
        "      justify-content: space-between;\n"
        "      align-items: center;\n"
        "      gap: 1rem;\n"
        "      padding: 1rem 0;\n"
        "      margin-bottom: 1rem;\n"
        "      flex-wrap: wrap;\n"
        "    }\n"
        "    .dataTable-search input {\n"
        "      width: 100%;\n"
        "      max-width: 300px;\n"
        "      padding: 0.5rem 0.75rem;\n"
        "      border: 1px solid var(--border);\n"
        "      border-radius: 6px;\n"
        "      font-size: 1rem;\n"
        "      background-color: var(--card-bg);\n"
        "      color: var(--fg);\n"
        "    }\n"
        "    .dataTable-search input:focus {\n"
        "      outline: none;\n"
        "      border-color: var(--accent);\n"
        "      box-shadow:"
        " 0 0 0 3px rgba(88,166,255,0.2);\n"
        "    }\n"
        "    .dataTable-search input::placeholder {\n"
        "      color: #8b949e;\n"
        "    }\n"
        "    /* Sorting indicators */\n"
        "    .dataTable-sorter {\n"
        "      position: relative;\n"
        "      cursor: pointer;\n"
        "      user-select: none;\n"
        "    }\n"
        "    .dataTable-sorter::before,\n"
        "    .dataTable-sorter::after {\n"
        "      content: '';\n"
        "      position: absolute;\n"
        "      right: 0.5rem;\n"
        "      width: 0; height: 0;\n"
        "      border-left: 4px solid transparent;\n"
        "      border-right:"
        " 4px solid transparent;\n"
        "      opacity: 0.3;\n"
        "    }\n"
        "    .dataTable-sorter::before {\n"
        "      bottom: 50%; margin-bottom: 3px;\n"
        "      border-bottom: 4px solid #8b949e;\n"
        "    }\n"
        "    .dataTable-sorter::after {\n"
        "      top: 50%; margin-top: 3px;\n"
        "      border-top: 4px solid #8b949e;\n"
        "    }\n"
        "    .dataTable-sorter:hover::before,\n"
        "    .dataTable-sorter:hover::after {\n"
        "      opacity: 0.6;\n"
        "    }\n"
        "    .dataTable-ascending"
        " .dataTable-sorter::before {\n"
        "      opacity: 1;\n"
        "      border-bottom-color: var(--accent);\n"
        "    }\n"
        "    .dataTable-descending"
        " .dataTable-sorter::after {\n"
        "      opacity: 1;\n"
        "      border-top-color: var(--accent);\n"
        "    }\n"
        "    .dataTable-empty {\n"
        "      padding: 2rem;\n"
        "      text-align: center;\n"
        "      color: #8b949e;\n"
        "      font-style: italic;\n"
        "    }\n"
        "    /* Hide pagination and bottom bar */\n"
        "    .dataTable-bottom {\n"
        "      display: none !important;\n"
        "    }\n"
        "    /* State emoji legend */\n"
        "    .state-legend {\n"
        "      margin: 0.5rem 0 1rem 0;\n"
        "      padding: 1rem;\n"
        "      background: var(--card-bg);\n"
        "      border: 1px solid var(--border);\n"
        "      border-radius: 6px;\n"
        "      font-size: 0.9rem;\n"
        "    }\n"
        "    .state-legend p {\n"
        "      margin: 0.3rem 0;\n"
        "    }\n"
        "    /* Print: hide DataTables controls */\n"
        "    @media print {\n"
        "      .dataTable-top,\n"
        "      .dataTable-bottom {\n"
        "        display: none !important;\n"
        "      }\n"
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
        "  <!-- Simple-DataTables JS -->\n"
        '  <script src="https://cdn.jsdelivr.net/npm/'
        'simple-datatables@9"'
        ' type="text/javascript"></script>\n'
        "  <script>\n"
        "  document.addEventListener('DOMContentLoaded',"
        " function() {\n"
        "    document.querySelectorAll("
        "'table.dt-enabled').forEach("
        "function(table) {\n"
        "      var rows ="
        " table.querySelectorAll('tbody tr');\n"
        "      // Skip tables with fewer than 3 rows;\n"
        "      // search/sort add no value to tiny tables\n"
        "      if (rows.length < 3) return;\n"
        "      try {\n"
        "        new simpleDatatables.DataTable(table, {\n"
        "          searchable: true,\n"
        "          sortable: true,\n"
        "          paging: false,\n"
        "          perPage: 0,\n"
        "          perPageSelect: false,\n"
        "          labels: {\n"
        '            placeholder: "Filter table...",\n'
        '            noRows: "No entries found",\n'
        "            info: "
        '"Showing {start} to {end} of {rows}"\n'
        "          }\n"
        "        });\n"
        "      } catch (e) {\n"
        "        console.error("
        "'Failed to init DataTable:', e);\n"
        "      }\n"
        "    });\n"
        "  });\n"
        "  </script>\n"
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
        ``html``, or ``gerrit-list``.
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


def filter_repositories(
    manifest: ReleaseManifest,
    *,
    filter_repos: Sequence[str] | None = None,
    exclude_readonly: bool = False,
) -> ReleaseManifest:
    """Return a new manifest with repositories filtered.

    Applies the requested filters to the repository list and
    recalculates the summary statistics to match the reduced
    set.

    Parameters
    ----------
    manifest:
        The release manifest to filter.
    filter_repos:
        Gerrit project names to **remove** from the manifest.
        Matching is exact (case-sensitive).  ``None`` or an
        empty sequence means no name-based filtering.
    exclude_readonly:
        When ``True``, drop every repository whose
        ``gerrit_state`` is ``"READ_ONLY"``.

    Returns
    -------
    ReleaseManifest
        A shallow copy of *manifest* with the filtered
        repository list and updated summary counts.
    """
    repos = list(manifest.repositories)

    if filter_repos:
        excluded = set(filter_repos)
        repos = [r for r in repos if r.gerrit_project not in excluded]

    if exclude_readonly:
        repos = [r for r in repos if r.gerrit_state != "READ_ONLY"]

    # Recalculate summary statistics
    by_category: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for repo in repos:
        by_category[repo.category] = by_category.get(repo.category, 0) + 1
        by_confidence[repo.confidence] = by_confidence.get(repo.confidence, 0) + 1

    new_summary = manifest.summary.model_copy(
        update={
            "total_repositories": len(repos),
            "repositories_by_category": by_category,
            "repositories_by_confidence": by_confidence,
        },
    )

    result: ReleaseManifest = manifest.model_copy(
        update={
            "repositories": repos,
            "summary": new_summary,
        },
    )
    return result


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


def _state_emoji(repo: object) -> str:
    """Convert repository state fields to an emoji indicator.

    Uses the ``gerrit_state``, ``in_current_release``, and
    ``is_parent_project`` attributes to produce a visual status:

    * 📦 — ``READ_ONLY`` (archived / read-only)
    * ✅ — ``ACTIVE`` and in the current ONAP release
    * ☑️ — ``ACTIVE`` parent project with children in release
    * ❌ — ``ACTIVE`` but NOT in the current ONAP release
    * ❓ — Undetermined (release scope unknown)

    Parameters
    ----------
    repo:
        An ``OnapRepository`` instance (or any object with the
        relevant attributes).

    Returns
    -------
    str
        An emoji string representing the repository state.
    """
    gerrit_state = getattr(repo, "gerrit_state", None)
    in_release = getattr(repo, "in_current_release", None)
    is_parent = getattr(repo, "is_parent_project", None)

    if gerrit_state == "READ_ONLY":
        return "\U0001f4e6"  # 📦

    if in_release is True:
        if is_parent is True:
            return "\u2611\ufe0f"  # ☑️
        return "\u2705"  # ✅

    if in_release is False:
        return "\u274c"  # ❌

    # Unknown / undetermined
    return "\u2753"  # ❓


_STATE_DESCRIPTIONS: dict[str, str] = {
    "\u2705": "In current ONAP release",
    "\u2611\ufe0f": "Parent project (children in release)",
    "\u274c": "Not in current ONAP release",
    "\u2753": "Undetermined",
    "\U0001f4e6": "Read-only / archived",
}


def _totals_section(repositories: Sequence[object]) -> list[str]:
    """Build a Markdown totals subsection for repository states.

    Counts each repository by its emoji state indicator and
    returns a small summary table with a key describing each
    symbol.  Rows with a zero count are omitted.

    Parameters
    ----------
    repositories:
        Sequence of ``OnapRepository`` instances (or any objects
        accepted by :func:`_state_emoji`).

    Returns
    -------
    list[str]
        Markdown lines forming a ``### Totals`` subsection.
    """
    counts: dict[str, int] = {}
    for repo in repositories:
        emoji = _state_emoji(repo)
        counts[emoji] = counts.get(emoji, 0) + 1

    order = [
        "\u2705",
        "\u2611\ufe0f",
        "\u274c",
        "\u2753",
        "\U0001f4e6",
    ]

    lines: list[str] = [
        "### Totals",
        "",
        "| Total | State | Description |",
        "| ----: | :---: | ----------- |",
    ]
    for emoji in order:
        count = counts.get(emoji, 0)
        if count > 0:
            desc = _STATE_DESCRIPTIONS[emoji]
            lines.append(f"| {count} | {emoji} | {desc} |")
    lines.append("")

    return lines


EXPORT_FORMATS: dict[str, Callable[[ReleaseManifest], str]] = {
    "yaml": export_yaml,
    "md": export_markdown,
    "html": export_html,
    "gerrit-list": export_gerrit_list,
}

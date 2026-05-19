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
                "attribution_reason",
                "attribution_verified",
                "attribution_alternatives",
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
                    img.attribution_reason or "",
                    _bool_str(img.attribution_verified),
                    ";".join(img.attribution_alternatives),
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
    lines.extend(_repositories_summary_block(manifest.repositories))
    lines.extend(_repositories_legend_block())
    lines.extend(_state_legend_block())
    lines.append(
        "| Gerrit Project | Sources | Category | Confidence | State "
        "| Maintained | Has CI |"
    )
    lines.append(
        "| -------------- | ------- | -------- | ---------- | ----- "
        "| ---------- | ------ |"
    )
    for repo in manifest.repositories:
        state = _state_emoji(repo)
        maintained = _bool_display(repo.maintained)
        has_ci = _bool_display(repo.has_ci)
        sources = ", ".join(repo.discovered_by) if repo.discovered_by else "\u2014"
        confidence_cell = _confidence_cell(repo.confidence, repo.confidence_reasons)
        lines.append(
            f"| {repo.gerrit_project} | {sources} | {repo.category} "
            f"| {confidence_cell} | {state} "
            f"| {maintained} | {has_ci} |"
        )
    lines.append("")

    lines.extend(_totals_section(manifest.repositories))

    # Docker images table
    lines.append("## Docker Images")
    lines.append("")
    lines.extend(_docker_images_summary_block(manifest.docker_images))
    lines.extend(_docker_images_legend_block())
    lines.append(
        "| Image | Tag | Gerrit Project | Registry | Validated | Attribution |"
    )
    lines.append(
        "| ----- | --- | -------------- | -------- | --------- | ----------- |"
    )
    for img in manifest.docker_images:
        project = img.gerrit_project or ""
        reg = img.registry or ""
        validated = _bool_display(img.nexus_validated)
        # Attribution cell shows the mapper reason with a verification
        # marker suffix (✓ verified, ✗ unverified, blank when no ground
        # truth was available). Alternatives are appended in parentheses
        # when the longest-match tiebreak had to choose between
        # siblings, so reviewers can spot ambiguous leaves at a glance.
        attribution = img.attribution_reason or ""
        if attribution:
            if img.attribution_verified is True:
                attribution += " ✓"
            elif img.attribution_verified is False:
                attribution += " ✗"
            if img.attribution_alternatives:
                alts = ", ".join(img.attribution_alternatives)
                attribution += f" (alt: {alts})"
        lines.append(
            f"| {img.image} | {img.tag} | {project} | {reg} "
            f"| {validated} | {attribution} |"
        )
    lines.append("")

    # Helm components table
    lines.append("## Helm Components")
    lines.append("")
    lines.extend(_helm_components_summary_block(manifest.helm_components))
    lines.extend(_helm_components_legend_block())
    lines.append("| Name | Version | Enabled by default |")
    lines.append("| ---- | ------- | ------------------ |")
    for comp in manifest.helm_components:
        version = comp.version or ""
        enabled = _helm_enabled_cell(comp.enabled_by_default, comp.condition_key)
        lines.append(f"| {comp.name} | {version} | {enabled} |")
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

    # Add dt-enabled class to all tables for DataTables init,
    # but skip the small Totals summary table which needs no
    # search or sort controls.
    _TOTALS_MARKER = "<h3>Totals</h3>"
    parts = body_html.split(_TOTALS_MARKER, maxsplit=1)
    parts[0] = parts[0].replace("<table>", '<table class="dt-enabled">')
    if len(parts) == 2:
        # Find the first <table> after the Totals heading — leave
        # it plain — then enable DataTables on the rest.
        before_tbl, sep, after_tbl = parts[1].partition("<table>")
        parts[1] = (
            before_tbl
            + sep
            + after_tbl.replace("<table>", '<table class="dt-enabled">')
        )
    body_html = _TOTALS_MARKER.join(parts)

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
        "    .state-legend,\n"
        "    .legend,\n"
        "    .summary {\n"
        "      margin: 0.5rem 0 1rem 0;\n"
        "      padding: 1rem;\n"
        "      background: var(--card-bg);\n"
        "      border: 1px solid var(--border);\n"
        "      border-radius: 6px;\n"
        "      font-size: 0.9rem;\n"
        "    }\n"
        "    .state-legend p,\n"
        "    .legend p,\n"
        "    .summary p {\n"
        "      margin: 0.3rem 0;\n"
        "    }\n"
        "    .legend code,\n"
        "    .summary code {\n"
        "      background: rgba(110,118,129,0.15);\n"
        "      padding: 0.1rem 0.35rem;\n"
        "      border-radius: 3px;\n"
        "      font-size: 0.85em;\n"
        "    }\n"
        "    .summary {\n"
        "      border-left: 3px solid var(--accent);\n"
        "    }\n"
        "    /* Tooltip indicator on the Confidence cell */\n"
        "    td abbr[title] {\n"
        "      text-decoration: underline dotted;\n"
        "      cursor: help;\n"
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
        if "confidence_reasons" in repo:
            repo["confidence_reasons"] = [_esc(v) for v in repo["confidence_reasons"]]

    # Escape Docker image fields
    for img in data.get("docker_images", []):
        for key in (
            "image",
            "tag",
            "registry",
            "gerrit_project",
            "attribution_reason",
        ):
            if key in img and isinstance(img[key], str):
                img[key] = _esc(img[key])
        if "helm_charts" in img:
            img["helm_charts"] = [_esc(v) for v in img["helm_charts"]]
        if "attribution_alternatives" in img:
            img["attribution_alternatives"] = [
                _esc(v) for v in img["attribution_alternatives"]
            ]

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


_UNKNOWN_DISPLAY = "—"
"""Em-dash used to render tri-state ``None`` values in human output.

A visible placeholder makes "value not determined from any data
source" clearly distinct from a definite ``No``.  Without it,
blank cells in the Markdown/HTML reports were easily misread as
"the answer is No" (see PR description / Fiete's feedback).
"""


def _bool_display(value: bool | None) -> str:
    """Convert an optional boolean to a human-friendly string.

    Returns ``"Yes"``, ``"No"``, or :data:`_UNKNOWN_DISPLAY`
    (an em-dash) for ``None``.  The em-dash placeholder makes
    ``None`` visually distinct from a definite ``False`` in the
    Markdown and HTML reports.
    """
    if value is None:
        return _UNKNOWN_DISPLAY
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


_STATE_ORDER: list[str] = [
    "\u2705",
    "\u2611\ufe0f",
    "\u274c",
    "\u2753",
    "\U0001f4e6",
]

_STATE_DESCRIPTIONS: dict[str, str] = {
    "\u2705": "In current ONAP release",
    "\u2611\ufe0f": "Parent project (children in release)",
    "\u274c": "Not in current ONAP release",
    "\u2753": "Undetermined",
    "\U0001f4e6": "Read-only / archived",
}


# ---------------------------------------------------------------
# Legend blocks
# ---------------------------------------------------------------
#
# These helpers emit short explanatory blocks that sit directly
# beneath each table heading in the Markdown export.  Because the
# HTML report is generated by running the Markdown through
# ``markdown.markdown``, the same blocks appear in both outputs
# without any post-conversion injection.
#
# The blocks are wrapped in ``<div class="legend">`` so the CSS in
# :func:`_html_wrapper` can give them the same bordered "card"
# treatment as the existing state-emoji legend.  Markdown passes
# raw HTML block elements through unchanged when they begin at
# column zero with a blank line either side, which is exactly the
# shape these helpers produce.


def _state_legend_block() -> list[str]:
    """Render the State emoji legend as a Markdown HTML block.

    Emits the legend inline in the Markdown stream (rather than
    injecting it post-conversion in :func:`export_html`) so the
    same content reaches every output format that goes through
    :func:`export_markdown`.  The ``state-legend`` class name is
    preserved for backwards compatibility with consumers that
    style or scrape the existing markup.
    """
    lines: list[str] = ['<div class="state-legend">']
    lines.append("  <p><strong>State Legend</strong></p>")
    for emoji in _STATE_ORDER:
        desc = _STATE_DESCRIPTIONS[emoji]
        lines.append(f"  <p>{emoji} {desc}</p>")
    lines.append("</div>")
    lines.append("")
    return lines


def _legend_block(
    title: str,
    rows: Sequence[tuple[str, str]],
) -> list[str]:
    """Render an HTML ``<div class="legend">`` block as Markdown lines.

    The block contains a bold title followed by a series of
    ``<em>label</em> — description`` paragraphs.  Both label and
    description are passed through verbatim, so callers must
    pre-escape any untrusted content (the legend text in this
    module is fully static and safe).

    Parameters
    ----------
    title:
        Title shown in bold at the top of the legend.
    rows:
        Ordered sequence of ``(label, description)`` tuples.

    Returns
    -------
    list[str]
        Markdown lines (including the trailing blank line).
    """
    lines: list[str] = ['<div class="legend">']
    lines.append(f"  <p><strong>{title}</strong></p>")
    for label, description in rows:
        lines.append(f"  <p><em>{label}</em> \u2014 {description}</p>")
    lines.append("</div>")
    lines.append("")
    return lines


def _repositories_legend_block() -> list[str]:
    """Legend describing the Repositories table columns.

    Explains the meaning of every column whose value can be
    ambiguous on inspection, in particular the tri-state
    ``Maintained`` and ``Has CI`` columns whose blank cells were
    being misread as a definite "No".
    """
    rows: list[tuple[str, str]] = [
        (
            "Category",
            (
                "<code>runtime</code> (deployed component), "
                "<code>build-dependency</code> (read-only, archived), "
                "<code>infrastructure</code> (e.g. OOM itself), "
                "<code>test</code>, <code>documentation</code>, "
                "<code>tooling</code>."
            ),
        ),
        (
            "Confidence",
            (
                "<code>high</code> = image referenced in OOM Helm "
                "charts; <code>medium</code> = listed in relman "
                "<code>repos.yaml</code> or has CI jobs in JJB; "
                "<code>low</code> = heuristic discovery only."
            ),
        ),
        (
            "State",
            ("Emoji indicator \u2014 see the State Legend below."),
        ),
        (
            "Maintained",
            (
                "From relman <code>repos.yaml</code> "
                "(<code>unmaintained: true</code> → <strong>No</strong>). "
                "<strong>Yes</strong> = explicitly listed and not flagged "
                "unmaintained; <strong>No</strong> = explicitly flagged "
                "unmaintained; <strong>\u2014</strong> = no entry in "
                "<code>repos.yaml</code> (status unknown from this source)."
            ),
        ),
        (
            "Has CI",
            (
                "From the JJB collector scanning <code>ci-management</code>. "
                "<strong>Yes</strong> = at least one Jenkins job targets "
                "this repository; <strong>\u2014</strong> = no JJB job was "
                "found (the collector does not record a definite "
                "<strong>No</strong>)."
            ),
        ),
    ]
    return _legend_block("How to read this table", rows)


def _docker_images_legend_block() -> list[str]:
    """Legend describing the Docker Images table columns.

    The Attribution column is by far the most opaque: it serialises
    the :class:`MappingReason` enum from the image mapper together
    with a verification marker derived from the Gerrit ground-truth
    set.  This helper unpacks both into plain English.
    """
    rows: list[tuple[str, str]] = [
        (
            "Validated",
            (
                "<strong>Yes</strong> = image:tag confirmed present in "
                "Nexus; <strong>No</strong> = lookup failed; "
                "<strong>\u2014</strong> = no Nexus probe was attempted."
            ),
        ),
        (
            "Attribution",
            (
                "How the image was mapped to a Gerrit project. "
                "See the Attribution key below for the full list of "
                "reason codes and verification markers."
            ),
        ),
    ]
    lines = _legend_block("How to read this table", rows)

    # A second legend block specifically for the Attribution column,
    # which has its own vocabulary of reason codes and markers.
    attribution_rows: list[tuple[str, str]] = [
        (
            "override",
            "Explicit entry in <code>image_repo_mapping.yaml</code>.",
        ),
        (
            "override-stale",
            (
                "Explicit override exists but resolves to a project "
                "not in Gerrit (mapping file is out of date)."
            ),
        ),
        (
            "leaf-match-namespace",
            (
                "Longest-match on the image's leaf segment within the "
                "same top-level namespace (best-quality automatic match)."
            ),
        ),
        (
            "leaf-match-cross-namespace",
            (
                "Same as above but the match crossed namespaces \u2014 "
                "flagged for human review."
            ),
        ),
        (
            "heuristic-*-verified",
            (
                "Pattern-based guess (<code>org.onap.*</code> prefix, "
                "dash\u2192slash, or slash passthrough) that was "
                "confirmed against the Gerrit project list."
            ),
        ),
        (
            "heuristic-*-unverified",
            (
                "Same heuristic, but no Gerrit confirmation \u2014 "
                "lower-confidence result."
            ),
        ),
        (
            "unresolved",
            "Mapper found no candidate; no Gerrit project assigned.",
        ),
        (
            "\u2713 / \u2717 / (blank)",
            (
                "Verification marker: <strong>\u2713</strong> = "
                "confirmed in Gerrit ground truth; "
                "<strong>\u2717</strong> = could not be verified; "
                "blank = no Gerrit ground truth was loaded for this run."
            ),
        ),
        (
            "(alt: …)",
            (
                "Other plausible candidates the longest-match "
                "algorithm considered but did not choose."
            ),
        ),
    ]
    lines.extend(_legend_block("Attribution key", attribution_rows))
    return lines


def _helm_components_legend_block() -> list[str]:
    """Legend describing the Helm Components table.

    The combined ``Enabled by default`` column is the single biggest
    point of confusion because ONAP's umbrella chart uses an
    opt-in pattern: almost every component defaults to disabled,
    so the column reads as predominantly "No".  This block calls
    that pattern out explicitly and explains the parenthesised
    Helm dependency condition key shown alongside each value.
    """
    rows: list[tuple[str, str]] = [
        (
            "Enabled by default",
            (
                "Whether the component is deployed when the umbrella "
                "chart is installed without overrides. "
                "<strong>Yes</strong> / <strong>No</strong> reflect the "
                "<code>&lt;component&gt;.enabled</code> default in the OOM "
                "umbrella <code>values.yaml</code>; <strong>\u2014</strong> "
                "means no <code>enabled</code> key was present "
                "(Helm treats this as unconditional). "
                "<strong>Note:</strong> ONAP's umbrella chart is opt-in "
                "\u2014 most components default to <strong>No</strong>, "
                "and operators select the ones they want at install time."
            ),
        ),
        (
            "(via <code>….enabled</code>)",
            (
                "Helm <em>dependency condition</em> from the umbrella "
                "<code>Chart.yaml</code> \u2014 the values path "
                "operators set to <code>true</code> to include this "
                "subchart in a deployment."
            ),
        ),
    ]
    return _legend_block("How to read this table", rows)


def _helm_enabled_cell(
    enabled_by_default: bool | None,
    condition_key: str | None,
) -> str:
    """Render the folded ``Enabled by default`` cell.

    Combines the umbrella default (Yes / No / em-dash) with the
    Helm dependency condition key, e.g. ``"No (via
    `policy.enabled`)"``.  Falls back to just the value when the
    component has no condition key.

    Parameters
    ----------
    enabled_by_default:
        Tri-state default for the component's umbrella entry.
    condition_key:
        Helm values path that gates inclusion (e.g.
        ``"policy.enabled"``), or ``None``.

    Returns
    -------
    str
        Single Markdown cell value.
    """
    value = _bool_display(enabled_by_default)
    if condition_key:
        return f"{value} (via `{condition_key}`)"
    return value


def _confidence_cell(
    confidence: str,
    confidence_reasons: Sequence[str],
) -> str:
    """Render the Confidence cell with reasons as an HTML tooltip.

    Wraps the confidence level in an ``<abbr title="…">`` element so
    that hovering the cell in the HTML report reveals the reasoning
    the collectors recorded (for example *Listed in relman
    repos.yaml; Has CI jobs in ci-management JJB*).  Markdown
    passes inline HTML through table cells unchanged, so the same
    markup works in both export formats.

    Parameters
    ----------
    confidence:
        Confidence level string (``low`` / ``medium`` / ``high``).
    confidence_reasons:
        Ordered sequence of human-readable rationale strings.

    Returns
    -------
    str
        Markdown cell value.
    """
    if not confidence_reasons:
        return confidence
    # Join reasons with '; ' so the tooltip stays on a single line.
    # The reasons are produced by collectors and may contain HTML
    # metacharacters; the manifest sanitiser HTML-escapes them in
    # the HTML output path, so the title attribute value here is
    # safe to render verbatim in both formats.
    title = "; ".join(confidence_reasons)
    return f'<abbr title="{title}">{confidence}</abbr>'


# ---------------------------------------------------------------
# Summary blocks
# ---------------------------------------------------------------
#
# These helpers compute a small set of counts derived from the
# manifest and emit them as a bullet list directly under each
# section heading.  The intent is to give readers an at-a-glance
# answer to questions like "how many repos have CI jobs?" without
# having to scroll through the full table or interpret the
# tri-state columns.  Counts are particularly useful for framing
# the report data when the underlying tri-state values can be
# blank for structural reasons (the relevant collector didn't
# run, or didn't record a value for that row).


def _repositories_summary_block(
    repositories: Sequence[object],
) -> list[str]:
    """Render a Markdown summary block for the Repositories table.

    Counts coverage by each collector (``discovered_by``) and the
    tri-state Maintained / Has CI columns.  Renders an empty list
    of lines when the manifest contains no repositories.
    """
    if not repositories:
        return []

    total = len(repositories)
    by_source: dict[str, int] = {}
    maintained_yes = maintained_no = maintained_unknown = 0
    has_ci_yes = has_ci_unknown = 0
    readonly = 0
    in_release = 0
    for repo in repositories:
        for src in getattr(repo, "discovered_by", []) or []:
            by_source[src] = by_source.get(src, 0) + 1
        maintained = getattr(repo, "maintained", None)
        if maintained is True:
            maintained_yes += 1
        elif maintained is False:
            maintained_no += 1
        else:
            maintained_unknown += 1
        has_ci = getattr(repo, "has_ci", None)
        if has_ci is True:
            has_ci_yes += 1
        else:
            has_ci_unknown += 1
        if getattr(repo, "gerrit_state", None) == "READ_ONLY":
            readonly += 1
        if getattr(repo, "in_current_release", None) is True:
            in_release += 1

    rows: list[tuple[str, str]] = [
        ("Total repositories", str(total)),
        (
            "In current ONAP release",
            f"{in_release} of {total}",
        ),
        (
            "Read-only / archived",
            f"{readonly} of {total}",
        ),
        (
            "Maintained",
            (
                f"{maintained_yes} Yes, {maintained_no} No, "
                f"{maintained_unknown} \u2014 (not listed in relman)"
            ),
        ),
        (
            "Has CI jobs in JJB",
            (f"{has_ci_yes} Yes, {has_ci_unknown} \u2014 (no JJB entry found)"),
        ),
    ]
    # Sort sources to keep output stable across runs.
    if by_source:
        sources_text = ", ".join(
            f"{name} ({count})" for name, count in sorted(by_source.items())
        )
        rows.append(("Discovered by", sources_text))

    return _summary_block("At a glance", rows)


def _docker_images_summary_block(
    images: Sequence[object],
) -> list[str]:
    """Render a Markdown summary block for the Docker Images table.

    Counts coverage by attribution category and verification status
    so readers can quickly gauge how many images were mapped
    confidently versus heuristically.
    """
    if not images:
        return []

    total = len(images)
    by_category: dict[str, int] = {
        "override": 0,
        "leaf-match": 0,
        "heuristic": 0,
        "unresolved": 0,
        "other": 0,
    }
    verified = unverified = unknown_verify = 0
    nexus_yes = nexus_no = nexus_unknown = 0
    for img in images:
        reason = getattr(img, "attribution_reason", None) or ""
        if reason.startswith("override"):
            by_category["override"] += 1
        elif reason.startswith("leaf-match"):
            by_category["leaf-match"] += 1
        elif reason.startswith("heuristic"):
            by_category["heuristic"] += 1
        elif reason == "unresolved":
            by_category["unresolved"] += 1
        else:
            by_category["other"] += 1
        verify = getattr(img, "attribution_verified", None)
        if verify is True:
            verified += 1
        elif verify is False:
            unverified += 1
        else:
            unknown_verify += 1
        nexus = getattr(img, "nexus_validated", None)
        if nexus is True:
            nexus_yes += 1
        elif nexus is False:
            nexus_no += 1
        else:
            nexus_unknown += 1

    rows: list[tuple[str, str]] = [
        ("Total images", str(total)),
        (
            "By attribution",
            (
                f"{by_category['override']} override, "
                f"{by_category['leaf-match']} leaf-match, "
                f"{by_category['heuristic']} heuristic, "
                f"{by_category['unresolved']} unresolved"
                + (f", {by_category['other']} other" if by_category["other"] else "")
            ),
        ),
        (
            "Verified against Gerrit",
            (
                f"{verified} \u2713, {unverified} \u2717, "
                f"{unknown_verify} \u2014 (no ground truth)"
            ),
        ),
        (
            "Validated in Nexus",
            (f"{nexus_yes} Yes, {nexus_no} No, {nexus_unknown} \u2014 (not probed)"),
        ),
    ]
    return _summary_block("At a glance", rows)


def _helm_components_summary_block(
    components: Sequence[object],
) -> list[str]:
    """Render a Markdown summary block for the Helm Components table."""
    if not components:
        return []

    total = len(components)
    yes = no = unknown = 0
    with_condition = 0
    for comp in components:
        flag = getattr(comp, "enabled_by_default", None)
        if flag is True:
            yes += 1
        elif flag is False:
            no += 1
        else:
            unknown += 1
        if getattr(comp, "condition_key", None):
            with_condition += 1

    rows: list[tuple[str, str]] = [
        ("Total components", str(total)),
        (
            "Enabled by default",
            f"{yes} Yes, {no} No, {unknown} \u2014",
        ),
        (
            "With Helm condition key",
            f"{with_condition} of {total}",
        ),
    ]
    return _summary_block("At a glance", rows)


def _summary_block(
    title: str,
    rows: Sequence[tuple[str, str]],
) -> list[str]:
    """Render an HTML ``<div class="summary">`` block as Markdown lines.

    Shares its structural conventions with :func:`_legend_block`
    but uses a distinct CSS class so the two can be styled
    differently if desired.  Each row is rendered as a single
    paragraph with a bold label and a plain-text count, keeping
    the block compact above each table.
    """
    lines: list[str] = ['<div class="summary">']
    lines.append(f"  <p><strong>{title}</strong></p>")
    for label, value in rows:
        lines.append(f"  <p><strong>{label}:</strong> {value}</p>")
    lines.append("</div>")
    lines.append("")
    return lines


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

    lines: list[str] = [
        "### Totals",
        "",
        "| Total | State | Description |",
        "| ----: | :---: | ----------- |",
    ]
    for emoji in _STATE_ORDER:
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

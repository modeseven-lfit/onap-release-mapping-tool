# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the exporter module."""

from __future__ import annotations

import pytest
import yaml

from onap_release_map.exceptions import ExportError
from onap_release_map.exporter import (
    export_csv,
    export_gerrit_list,
    export_html,
    export_manifest,
    export_markdown,
    export_yaml,
    filter_repositories,
)
from onap_release_map.models import (
    DockerImage,
    HelmComponent,
    ManifestProvenance,
    ManifestSummary,
    OnapRelease,
    OnapRepository,
    ReleaseManifest,
)


def _make_manifest() -> ReleaseManifest:
    """Build a small test manifest with representative data."""
    repos = [
        OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
            category="runtime",
            gerrit_state="ACTIVE",
            maintained=True,
            has_ci=True,
        ),
        OnapRepository(
            gerrit_project="cps",
            top_level_project="cps",
            confidence="medium",
            category="runtime",
        ),
    ]
    images = [
        DockerImage(
            image="onap/policy-api",
            tag="4.2.2",
            gerrit_project="policy/api",
            nexus_validated=True,
        ),
        DockerImage(
            image="onap/cps-and-ncmp",
            tag="3.6.1",
            gerrit_project="cps",
        ),
    ]
    components = [
        HelmComponent(
            name="policy",
            version="18.0.0",
            enabled_by_default=True,
            condition_key="policy.enabled",
        ),
    ]
    return ReleaseManifest(
        schema_version="1.0.0",
        tool_version="0.1.0",
        generated_at="2025-01-01T00:00:00Z",
        onap_release=OnapRelease(
            name="Rabat",
            oom_chart_version="18.0.0",
        ),
        summary=ManifestSummary(
            total_repositories=2,
            total_docker_images=2,
            total_helm_components=1,
        ),
        repositories=repos,
        docker_images=images,
        helm_components=components,
        provenance=ManifestProvenance(),
    )


class TestExportYaml:
    """Tests for export_yaml."""

    def test_yaml_output_valid(self) -> None:
        """Result is valid YAML and contains schema_version."""
        result = export_yaml(_make_manifest())
        data = yaml.safe_load(result)
        assert "schema_version" in data

    def test_yaml_contains_repos(self) -> None:
        """Result contains both repository project names."""
        result = export_yaml(_make_manifest())
        assert "policy/api" in result
        assert "cps" in result


class TestExportCsv:
    """Tests for export_csv."""

    def test_csv_repos_header(self) -> None:
        """First line contains the expected repo column names."""
        result = export_csv(_make_manifest())
        header = result.splitlines()[0]
        assert "gerrit_project" in header
        assert "top_level_project" in header
        assert "category" in header
        assert "confidence" in header

    def test_csv_repos_data(self) -> None:
        """Output contains both repository names."""
        result = export_csv(_make_manifest())
        assert "policy/api" in result
        assert "cps" in result

    def test_csv_images_header(self) -> None:
        """Images mode header contains expected column names."""
        result = export_csv(_make_manifest(), mode="images")
        header = result.splitlines()[0]
        assert "image" in header
        assert "tag" in header
        assert "registry" in header
        assert "gerrit_project" in header

    def test_csv_images_data(self) -> None:
        """Images mode output contains image name and tag."""
        result = export_csv(_make_manifest(), mode="images")
        assert "onap/policy-api" in result
        assert "4.2.2" in result

    def test_csv_invalid_mode(self) -> None:
        """Invalid mode raises ExportError."""
        with pytest.raises(ExportError):
            export_csv(_make_manifest(), mode="invalid")


class TestExportMarkdown:
    """Tests for export_markdown."""

    def test_markdown_title(self) -> None:
        """Output starts with the release title heading."""
        result = export_markdown(_make_manifest())
        assert result.startswith("# ONAP Release Manifest: Rabat")

    def test_markdown_tables(self) -> None:
        """Output contains section headings for all tables."""
        result = export_markdown(_make_manifest())
        assert "## Repositories" in result
        assert "## Docker Images" in result
        assert "## Helm Components" in result

    def test_markdown_repo_data(self) -> None:
        """Output contains policy/api in a table row."""
        result = export_markdown(_make_manifest())
        assert "policy/api" in result


class TestExportHtml:
    """Tests for export_html."""

    def test_html_is_complete_document(self) -> None:
        """Output is a full HTML document with doctype and closing tags."""
        result = export_html(_make_manifest())
        assert result.startswith("<!DOCTYPE html>")
        assert "</html>" in result
        assert "<head>" in result
        assert "</body>" in result

    def test_html_title_contains_release_name(self) -> None:
        """The <title> element includes the release name."""
        result = export_html(_make_manifest())
        assert "<title>ONAP Release Manifest: Rabat</title>" in result

    def test_html_contains_inline_css(self) -> None:
        """The document includes inline CSS with dark-theme variables."""
        result = export_html(_make_manifest())
        assert "<style>" in result
        assert "--bg: #0d1117" in result
        assert "--accent: #58a6ff" in result
        assert "--green: #3fb950" in result

    def test_html_contains_back_link(self) -> None:
        """The document includes a back-to-index navigation link."""
        result = export_html(_make_manifest())
        assert 'href="../"' in result
        assert "Back to index" in result

    def test_html_contains_tables(self) -> None:
        """The rendered HTML contains table elements from Markdown."""
        result = export_html(_make_manifest())
        assert '<table class="dt-enabled">' in result
        assert "<th>" in result
        assert "<td>" in result

    def test_html_contains_repo_data(self) -> None:
        """The HTML includes repository data from the manifest."""
        result = export_html(_make_manifest())
        assert "policy/api" in result
        assert "cps" in result

    def test_html_contains_image_data(self) -> None:
        """The HTML includes Docker image data from the manifest."""
        result = export_html(_make_manifest())
        assert "onap/policy-api" in result
        assert "4.2.2" in result

    def test_html_contains_section_headings(self) -> None:
        """The HTML includes section headings for all tables."""
        result = export_html(_make_manifest())
        assert "Repositories" in result
        assert "Docker Images" in result
        assert "Helm Components" in result

    def test_html_table_hover_styles(self) -> None:
        """The CSS includes hover effects for table rows."""
        result = export_html(_make_manifest())
        assert "tr:hover" in result

    def test_html_table_striped_rows(self) -> None:
        """The CSS includes striped-row styling."""
        result = export_html(_make_manifest())
        assert "tr:nth-child(even)" in result

    def test_html_has_datatables_dependencies(self) -> None:
        """The HTML includes Simple-DataTables CDN resources."""
        result = export_html(_make_manifest())
        assert "simple-datatables@9/dist/style.css" in result
        assert "simple-datatables@9" in result
        assert "simpleDatatables.DataTable" in result
        assert "paging: false" in result

    def test_html_contains_state_emoji(self) -> None:
        """The HTML includes emoji state indicators in table rows."""
        result = export_html(_make_manifest())
        # policy/api has gerrit_state=ACTIVE, in_current_release=None
        # so it should get the ❓ (undetermined) emoji in its table row.
        policy_index = result.index("policy/api")
        row_start = result.rfind("<tr", 0, policy_index)
        row_end = result.find("</tr>", policy_index)
        policy_row = result[row_start : row_end + len("</tr>")]
        assert "\u2753" in policy_row

    def test_html_contains_state_legend(self) -> None:
        """The HTML includes a state legend explaining emoji meanings."""
        result = export_html(_make_manifest())
        assert "State Legend" in result
        assert "State Legend:" not in result
        assert "\U0001f4e6" in result  # 📦
        assert "\u2705" in result  # ✅
        assert "\u274c" in result  # ❌

    def test_html_state_legend_before_repos_table(self) -> None:
        """The state legend appears between the Repositories heading and table."""
        result = export_html(_make_manifest())
        repos_heading_pos = result.index("Repositories</h2>")
        legend_pos = result.index('<div class="state-legend">', repos_heading_pos)
        first_table_after_repos = result.index("<table", legend_pos)
        assert repos_heading_pos < legend_pos < first_table_after_repos

    def test_html_state_legend_order(self) -> None:
        """The state legend lists emojis in the correct order."""
        result = export_html(_make_manifest())
        repos_heading_pos = result.index("Repositories</h2>")
        legend_start = result.index('<div class="state-legend">', repos_heading_pos)
        legend_end = result.index("</div>", legend_start)
        legend = result[legend_start:legend_end]
        pos_check = legend.index("\u2705")
        pos_parent = legend.index("\u2611\ufe0f")
        pos_not = legend.index("\u274c")
        pos_unknown = legend.index("\u2753")
        pos_readonly = legend.index("\U0001f4e6")
        assert pos_check < pos_parent < pos_not < pos_unknown < pos_readonly

    def test_html_datatables_search_enabled(self) -> None:
        """The DataTables init enables search."""
        result = export_html(_make_manifest())
        assert "searchable: true" in result

    def test_html_datatables_sort_enabled(self) -> None:
        """The DataTables init enables column sorting."""
        result = export_html(_make_manifest())
        assert "sortable: true" in result

    def test_html_datatables_pagination_disabled(self) -> None:
        """The DataTables init disables pagination."""
        result = export_html(_make_manifest())
        assert "paging: false" in result

    def test_dispatch_html(self) -> None:
        """Dispatching html via export_manifest returns HTML output."""
        result = export_manifest(_make_manifest(), "html")
        assert "<!DOCTYPE html>" in result
        assert "policy/api" in result


class TestExportGerritList:
    """Tests for export_gerrit_list."""

    def test_gerrit_list_sorted(self) -> None:
        """Lines are sorted alphabetically."""
        result = export_gerrit_list(_make_manifest())
        lines = result.strip().splitlines()
        assert lines == sorted(lines)

    def test_gerrit_list_content(self) -> None:
        """Output contains both project names."""
        result = export_gerrit_list(_make_manifest())
        assert "cps" in result
        assert "policy/api" in result

    def test_gerrit_list_empty(self) -> None:
        """Empty manifest produces an empty string."""
        manifest = ReleaseManifest(
            schema_version="1.0.0",
            tool_version="0.1.0",
            generated_at="2025-01-01T00:00:00Z",
            onap_release=OnapRelease(
                name="Empty",
                oom_chart_version="0.0.0",
            ),
        )
        assert export_gerrit_list(manifest) == ""


class TestExportDispatcher:
    """Tests for export_manifest dispatcher."""

    def test_dispatch_yaml(self) -> None:
        """Dispatching yaml returns YAML output."""
        result = export_manifest(_make_manifest(), "yaml")
        data = yaml.safe_load(result)
        assert "schema_version" in data

    def test_dispatch_gerrit_list(self) -> None:
        """Dispatching gerrit returns gerrit list output."""
        result = export_manifest(_make_manifest(), "gerrit-list")
        assert "policy/api" in result

    def test_dispatch_unknown(self) -> None:
        """Unknown format raises ExportError."""
        with pytest.raises(ExportError):
            export_manifest(_make_manifest(), "invalid")


def _make_xss_manifest() -> ReleaseManifest:
    """Build a manifest with HTML injection payloads."""
    xss = "<script>alert('xss')</script>"
    repos = [
        OnapRepository(
            gerrit_project=f"evil/{xss}",
            top_level_project=xss,
            confidence="high",
            category="runtime",
            gerrit_state="ACTIVE",
            maintained=True,
            has_ci=True,
        ),
    ]
    images = [
        DockerImage(
            image=f"onap/{xss}",
            tag=xss,
            gerrit_project=f"evil/{xss}",
            nexus_validated=True,
        ),
    ]
    components = [
        HelmComponent(
            name=xss,
            version="1.0.0",
            enabled_by_default=True,
            condition_key=xss,
        ),
    ]
    return ReleaseManifest(
        schema_version="1.0.0",
        tool_version="0.1.0",
        generated_at="2025-01-01T00:00:00Z",
        onap_release=OnapRelease(
            name=xss,
            oom_chart_version="0.0.0",
        ),
        summary=ManifestSummary(
            total_repositories=1,
            total_docker_images=1,
            total_helm_components=1,
        ),
        repositories=repos,
        docker_images=images,
        helm_components=components,
        provenance=ManifestProvenance(),
    )


class TestHtmlXssSanitisation:
    """Regression tests for XSS prevention in HTML export."""

    def test_script_tag_escaped_in_release_name(self) -> None:
        """Script tag in release name is escaped in HTML output."""
        result = export_html(_make_xss_manifest())
        # The only <script tags should be the two DataTables entries
        assert result.count("<script") == 2
        assert "&lt;script&gt;" in result

    def test_script_tag_escaped_in_title(self) -> None:
        """Script tag in title element is escaped."""
        result = export_html(_make_xss_manifest())
        assert "<title>" in result
        assert "<script>alert" not in result.split("<title>")[1]

    def test_script_tag_escaped_in_repo_name(self) -> None:
        """Script tag in repository name is escaped in HTML."""
        result = export_html(_make_xss_manifest())
        assert "evil/&lt;script&gt;" in result

    def test_script_tag_escaped_in_image_name(self) -> None:
        """Script tag in Docker image name is escaped in HTML."""
        result = export_html(_make_xss_manifest())
        assert "onap/&lt;script&gt;" in result

    def test_script_tag_escaped_in_helm_name(self) -> None:
        """Script tag in Helm component name is escaped in HTML."""
        result = export_html(_make_xss_manifest())
        body = result.split("Helm Components")[1]
        # Table content must not contain raw script tags;
        # only the DataTables init scripts should appear after
        # the Helm Components heading.
        assert "<script>alert" not in body
        assert "&lt;script&gt;" in body

    def test_ampersand_escaped_in_title(self) -> None:
        """Ampersand in release name is escaped in title element."""
        manifest = _make_manifest()
        data = manifest.model_dump(mode="json")
        data["onap_release"]["name"] = "R&D"
        safe = ReleaseManifest.model_validate(data)
        result = export_html(safe)
        assert "<title>ONAP Release Manifest: R&amp;D</title>" in result

    def test_markdown_link_injection_neutralised(self) -> None:
        """Markdown link syntax in manifest fields is neutralised."""
        manifest = _make_manifest()
        data = manifest.model_dump(mode="json")
        data["repositories"][0]["gerrit_project"] = "[click](javascript:alert(1))"
        safe = ReleaseManifest.model_validate(data)
        result = export_html(safe)
        assert 'href="javascript:' not in result

    def test_metadata_fields_escaped(self) -> None:
        """Metadata fields are escaped in HTML output."""
        manifest = _make_manifest()
        data = manifest.model_dump(mode="json")
        data["tool_version"] = "<img onerror=alert(1)>"
        safe = ReleaseManifest.model_validate(data)
        result = export_html(safe)
        assert "<img onerror=" not in result
        assert "&lt;img onerror=" in result


def _make_stateful_manifest() -> ReleaseManifest:
    """Build a manifest with repos in every possible state."""
    repos = [
        OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
            category="runtime",
            gerrit_state="ACTIVE",
            in_current_release=True,
            is_parent_project=False,
        ),
        OnapRepository(
            gerrit_project="policy",
            top_level_project="policy",
            confidence="medium",
            category="runtime",
            gerrit_state="ACTIVE",
            in_current_release=True,
            is_parent_project=True,
        ),
        OnapRepository(
            gerrit_project="vnfsdk/model",
            top_level_project="vnfsdk",
            confidence="low",
            category="runtime",
            gerrit_state="ACTIVE",
            in_current_release=False,
        ),
        OnapRepository(
            gerrit_project="holmes/rule-management",
            top_level_project="holmes",
            confidence="medium",
            category="runtime",
            gerrit_state="READ_ONLY",
        ),
        OnapRepository(
            gerrit_project="unknown/project",
            top_level_project="unknown",
            confidence="low",
            category="runtime",
            gerrit_state="ACTIVE",
            in_current_release=None,
        ),
        OnapRepository(
            gerrit_project="All-Projects",
            top_level_project="All-Projects",
            confidence="low",
            category="infrastructure",
            gerrit_state="ACTIVE",
            in_current_release=False,
        ),
        OnapRepository(
            gerrit_project="All-Users",
            top_level_project="All-Users",
            confidence="low",
            category="infrastructure",
            gerrit_state="ACTIVE",
            in_current_release=False,
        ),
        OnapRepository(
            gerrit_project=".github",
            top_level_project=".github",
            confidence="low",
            category="infrastructure",
            gerrit_state="ACTIVE",
            in_current_release=False,
        ),
    ]
    return ReleaseManifest(
        schema_version="1.0.0",
        tool_version="0.1.0",
        generated_at="2025-01-01T00:00:00Z",
        onap_release=OnapRelease(
            name="Rabat",
            oom_chart_version="18.0.0",
        ),
        summary=ManifestSummary(
            total_repositories=len(repos),
            total_docker_images=0,
            total_helm_components=0,
        ),
        repositories=repos,
        provenance=ManifestProvenance(),
    )


class TestTotalsSection:
    """Tests for the totals summary section in Markdown output."""

    def test_totals_heading_present(self) -> None:
        """Markdown output contains a Totals subsection heading."""
        result = export_markdown(_make_stateful_manifest())
        assert "### Totals" in result

    def test_totals_table_header(self) -> None:
        """Totals table has the correct header columns."""
        result = export_markdown(_make_stateful_manifest())
        assert "| Total | State | Description |" in result

    def test_totals_contains_in_release(self) -> None:
        """Totals table includes in-release count."""
        result = export_markdown(_make_stateful_manifest())
        assert "| 1 | \u2705 | In current ONAP release |" in result

    def test_totals_contains_parent_project(self) -> None:
        """Totals table includes parent-project count."""
        result = export_markdown(_make_stateful_manifest())
        assert "| 1 | \u2611\ufe0f | Parent project (children in release) |" in result

    def test_totals_contains_not_in_release(self) -> None:
        """Totals table includes not-in-release count."""
        result = export_markdown(_make_stateful_manifest())
        assert "\u274c" in result
        assert "Not in current ONAP release" in result

    def test_totals_contains_readonly(self) -> None:
        """Totals table includes read-only count."""
        result = export_markdown(_make_stateful_manifest())
        assert "\U0001f4e6" in result
        assert "Read-only / archived" in result

    def test_totals_contains_undetermined(self) -> None:
        """Totals table includes undetermined count."""
        result = export_markdown(_make_stateful_manifest())
        assert "\u2753" in result
        assert "Undetermined" in result

    def test_totals_before_docker_images(self) -> None:
        """Totals section appears between Repositories and Docker Images."""
        result = export_markdown(_make_stateful_manifest())
        totals_pos = result.index("### Totals")
        repos_pos = result.index("## Repositories")
        images_pos = result.index("## Docker Images")
        assert repos_pos < totals_pos < images_pos

    def test_totals_omits_zero_counts(self) -> None:
        """Totals table omits rows where the count is zero."""
        manifest = _make_manifest()
        result = export_markdown(manifest)
        # _make_manifest has no READ_ONLY repos so 📦 row is absent
        assert "### Totals" in result
        lines = result.split("\n")
        totals_lines = []
        in_totals = False
        for line in lines:
            if "### Totals" in line:
                in_totals = True
                continue
            if in_totals and line.startswith("##"):
                break
            if (
                in_totals
                and line.startswith("|")
                and "Total" not in line
                and "---" not in line
            ):
                totals_lines.append(line)
        for line in totals_lines:
            # Every data row must have a non-zero count
            parts = [p.strip() for p in line.split("|") if p.strip()]
            assert int(parts[0]) > 0

    def test_totals_in_html_output(self) -> None:
        """HTML export includes the totals heading."""
        result = export_html(_make_stateful_manifest())
        assert "Totals" in result

    def test_totals_table_has_no_datatables(self) -> None:
        """Totals table is plain HTML without the dt-enabled class."""
        result = export_html(_make_stateful_manifest())
        marker = "<h3>Totals</h3>"
        idx = result.index(marker)
        after = result[idx + len(marker) :]
        tbl_start = after.index("<table")
        tbl_end = after.index(">", tbl_start)
        tag = after[tbl_start : tbl_end + 1]
        assert "dt-enabled" not in tag


class TestFilterRepositories:
    """Tests for the filter_repositories function."""

    def test_filter_by_name(self) -> None:
        """Filtering by name removes the matching repository."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(manifest, filter_repos=["All-Projects"])
        names = [r.gerrit_project for r in filtered.repositories]
        assert "All-Projects" not in names
        assert "policy/api" in names

    def test_filter_multiple_names(self) -> None:
        """Filtering by multiple names removes all matches."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=[".github", "All-Projects", "All-Users"],
        )
        names = [r.gerrit_project for r in filtered.repositories]
        assert ".github" not in names
        assert "All-Projects" not in names
        assert "All-Users" not in names
        assert len(filtered.repositories) == 5

    def test_filter_readonly(self) -> None:
        """Excluding read-only removes READ_ONLY repositories."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(manifest, exclude_readonly=True)
        states = [r.gerrit_state for r in filtered.repositories]
        assert "READ_ONLY" not in states
        assert "holmes/rule-management" not in [
            r.gerrit_project for r in filtered.repositories
        ]

    def test_filter_combined(self) -> None:
        """Combining name filter and read-only exclusion."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=["All-Projects", "All-Users", ".github"],
            exclude_readonly=True,
        )
        names = [r.gerrit_project for r in filtered.repositories]
        assert "All-Projects" not in names
        assert "holmes/rule-management" not in names
        # Should keep: policy/api, policy, vnfsdk/model, unknown/project
        assert len(filtered.repositories) == 4

    def test_filter_updates_total(self) -> None:
        """Filtering updates summary.total_repositories."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=["All-Projects"],
        )
        assert filtered.summary.total_repositories == len(filtered.repositories)
        assert filtered.summary.total_repositories == 7

    def test_filter_updates_category_counts(self) -> None:
        """Filtering recalculates repositories_by_category."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=[".github", "All-Projects", "All-Users"],
        )
        total = sum(filtered.summary.repositories_by_category.values())
        assert total == len(filtered.repositories)

    def test_filter_updates_confidence_counts(self) -> None:
        """Filtering recalculates repositories_by_confidence."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=[".github", "All-Projects", "All-Users"],
        )
        total = sum(filtered.summary.repositories_by_confidence.values())
        assert total == len(filtered.repositories)

    def test_filter_none_is_noop(self) -> None:
        """No filters returns equivalent manifest."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(manifest)
        assert len(filtered.repositories) == len(manifest.repositories)

    def test_filter_empty_list_is_noop(self) -> None:
        """Empty filter list returns equivalent manifest."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(manifest, filter_repos=[])
        assert len(filtered.repositories) == len(manifest.repositories)

    def test_filter_preserves_other_fields(self) -> None:
        """Filtering does not alter non-repository manifest fields."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=["All-Projects"],
        )
        assert filtered.onap_release == manifest.onap_release
        assert filtered.tool_version == manifest.tool_version
        assert filtered.docker_images == manifest.docker_images
        assert filtered.helm_components == manifest.helm_components

    def test_filter_readonly_false_keeps_all(self) -> None:
        """Setting exclude_readonly=False keeps READ_ONLY repos."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(manifest, exclude_readonly=False)
        states = [r.gerrit_state for r in filtered.repositories]
        assert "READ_ONLY" in states

    def test_filter_does_not_mutate_original(self) -> None:
        """Filtering returns a new manifest without mutating input."""
        manifest = _make_stateful_manifest()
        original_count = len(manifest.repositories)
        filter_repositories(
            manifest,
            filter_repos=["All-Projects", "All-Users", ".github"],
            exclude_readonly=True,
        )
        assert len(manifest.repositories) == original_count

    def test_filtered_markdown_excludes_repos(self) -> None:
        """Markdown export after filtering omits excluded repos."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            filter_repos=["All-Projects", "All-Users", ".github"],
            exclude_readonly=True,
        )
        result = export_markdown(filtered)
        assert "All-Projects" not in result
        assert "All-Users" not in result
        assert ".github" not in result
        assert "holmes/rule-management" not in result
        assert "policy/api" in result

    def test_filtered_totals_exclude_readonly(self) -> None:
        """Totals section after filtering omits read-only row."""
        manifest = _make_stateful_manifest()
        filtered = filter_repositories(
            manifest,
            exclude_readonly=True,
        )
        result = export_markdown(filtered)
        assert "### Totals" in result
        assert "Read-only / archived" not in result

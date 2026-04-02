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
        assert "<table>" in result
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

    def test_html_no_external_dependencies(self) -> None:
        """The HTML has no external stylesheet or script links."""
        result = export_html(_make_manifest())
        assert '<link rel="stylesheet"' not in result
        assert "<script src=" not in result

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
        assert "<script>" not in result
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
        assert "<script>" not in body

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
        data["repositories"][0]["gerrit_project"] = (
            "[click](javascript:alert(1))"
        )
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

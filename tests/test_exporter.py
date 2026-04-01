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

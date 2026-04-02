# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the differ module."""

from __future__ import annotations

import json

from onap_release_map.differ import (
    diff_manifests,
    format_diff_json,
    format_diff_markdown,
    format_diff_text,
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


def _make_manifest(
    name: str = "TestRelease",
    repos: list[OnapRepository] | None = None,
    images: list[DockerImage] | None = None,
    components: list[HelmComponent] | None = None,
    schema_version: str = "1.0.0",
) -> ReleaseManifest:
    """Build a simple manifest for testing."""
    repos = repos or []
    images = images or []
    components = components or []

    return ReleaseManifest(
        schema_version=schema_version,
        tool_version="0.1.0-test",
        generated_at="2025-01-01T00:00:00Z",
        onap_release=OnapRelease(
            name=name,
            oom_chart_version="18.0.0",
        ),
        summary=ManifestSummary(
            total_repositories=len(repos),
            total_docker_images=len(images),
            total_helm_components=len(components),
        ),
        repositories=repos,
        docker_images=images,
        helm_components=components,
        provenance=ManifestProvenance(),
    )


class TestDiffManifests:
    """Tests for diff_manifests."""

    def test_identical_manifests(self) -> None:
        """Two identical manifests produce an empty diff."""
        repo = OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
        )
        image = DockerImage(image="onap/policy-api", tag="4.2.2")
        component = HelmComponent(name="policy", version="18.0.0")

        a = _make_manifest(
            repos=[repo],
            images=[image],
            components=[component],
        )
        b = _make_manifest(
            repos=[repo],
            images=[image],
            components=[component],
        )

        result = diff_manifests(a, b)

        assert result.repositories.added == []
        assert result.repositories.removed == []
        assert result.repositories.changed == []
        assert result.repositories.unchanged_count == 1

        assert result.docker_images.added == []
        assert result.docker_images.removed == []
        assert result.docker_images.changed == []
        assert result.docker_images.unchanged_count == 1

        assert result.helm_components.added == []
        assert result.helm_components.removed == []
        assert result.helm_components.changed == []
        assert result.helm_components.unchanged_count == 1

        assert result.summary_delta.repositories_delta == 0
        assert result.summary_delta.docker_images_delta == 0
        assert result.summary_delta.helm_components_delta == 0

    def test_repo_added(self) -> None:
        """A repository present only in B appears in added."""
        repo = OnapRepository(
            gerrit_project="cps",
            top_level_project="cps",
            confidence="high",
        )

        a = _make_manifest()
        b = _make_manifest(repos=[repo])

        result = diff_manifests(a, b)

        assert result.repositories.added == ["cps"]
        assert result.repositories.removed == []

    def test_repo_removed(self) -> None:
        """A repository present only in A appears in removed."""
        repo = OnapRepository(
            gerrit_project="aai/resources",
            top_level_project="aai",
            confidence="medium",
        )

        a = _make_manifest(repos=[repo])
        b = _make_manifest()

        result = diff_manifests(a, b)

        assert result.repositories.removed == ["aai/resources"]
        assert result.repositories.added == []

    def test_repo_confidence_changed(self) -> None:
        """A confidence change is recorded as a field change."""
        repo_a = OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="medium",
        )
        repo_b = OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
        )

        a = _make_manifest(repos=[repo_a])
        b = _make_manifest(repos=[repo_b])

        result = diff_manifests(a, b)

        assert len(result.repositories.changed) == 1
        change = result.repositories.changed[0]
        assert change.key == "policy/api"
        assert change.field == "confidence"
        assert change.old_value == "medium"
        assert change.new_value == "high"

    def test_repo_category_changed(self) -> None:
        """A category change is recorded as a field change."""
        repo_a = OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
            category="runtime",
        )
        repo_b = OnapRepository(
            gerrit_project="policy/api",
            top_level_project="policy",
            confidence="high",
            category="build-dependency",
        )

        a = _make_manifest(repos=[repo_a])
        b = _make_manifest(repos=[repo_b])

        result = diff_manifests(a, b)

        assert len(result.repositories.changed) == 1
        change = result.repositories.changed[0]
        assert change.field == "category"
        assert change.old_value == "runtime"
        assert change.new_value == "build-dependency"

    def test_docker_image_tag_changed(self) -> None:
        """A tag change for the same image is a change, not add+remove."""
        img_a = DockerImage(image="onap/policy-api", tag="4.2.1")
        img_b = DockerImage(image="onap/policy-api", tag="4.2.2")

        a = _make_manifest(images=[img_a])
        b = _make_manifest(images=[img_b])

        result = diff_manifests(a, b)

        assert result.docker_images.added == []
        assert result.docker_images.removed == []
        assert len(result.docker_images.changed) == 1

        change = result.docker_images.changed[0]
        assert change.field == "tag"
        assert change.old_value == "4.2.1"
        assert change.new_value == "4.2.2"

    def test_docker_image_added(self) -> None:
        """A new Docker image in B appears in added."""
        img = DockerImage(image="onap/cps-and-ncmp", tag="3.6.1")

        a = _make_manifest()
        b = _make_manifest(images=[img])

        result = diff_manifests(a, b)

        assert result.docker_images.added == ["onap/cps-and-ncmp:3.6.1"]
        assert result.docker_images.removed == []

    def test_docker_image_removed(self) -> None:
        """A Docker image present only in A appears in removed."""
        img = DockerImage(image="onap/aai-resources", tag="1.15.1")

        a = _make_manifest(images=[img])
        b = _make_manifest()

        result = diff_manifests(a, b)

        assert result.docker_images.removed == ["onap/aai-resources:1.15.1"]
        assert result.docker_images.added == []

    def test_helm_component_version_changed(self) -> None:
        """A version change is recorded as a field change."""
        comp_a = HelmComponent(name="policy", version="17.0.0")
        comp_b = HelmComponent(name="policy", version="18.0.0")

        a = _make_manifest(components=[comp_a])
        b = _make_manifest(components=[comp_b])

        result = diff_manifests(a, b)

        assert len(result.helm_components.changed) == 1
        change = result.helm_components.changed[0]
        assert change.key == "policy"
        assert change.field == "version"
        assert change.old_value == "17.0.0"
        assert change.new_value == "18.0.0"

    def test_helm_component_enabled_changed(self) -> None:
        """An enabled_by_default flip is recorded as a field change."""
        comp_a = HelmComponent(
            name="aai",
            version="16.0.0",
            enabled_by_default=True,
        )
        comp_b = HelmComponent(
            name="aai",
            version="16.0.0",
            enabled_by_default=False,
        )

        a = _make_manifest(components=[comp_a])
        b = _make_manifest(components=[comp_b])

        result = diff_manifests(a, b)

        assert len(result.helm_components.changed) == 1
        change = result.helm_components.changed[0]
        assert change.field == "enabled_by_default"
        assert change.old_value == "True"
        assert change.new_value == "False"

    def test_summary_delta(self) -> None:
        """Summary deltas reflect count differences between manifests."""
        a = _make_manifest(
            repos=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="high",
                ),
            ],
            images=[
                DockerImage(image="onap/policy-api", tag="4.2.2"),
            ],
        )
        b = _make_manifest(
            repos=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="high",
                ),
                OnapRepository(
                    gerrit_project="cps",
                    top_level_project="cps",
                    confidence="high",
                ),
                OnapRepository(
                    gerrit_project="aai/resources",
                    top_level_project="aai",
                    confidence="medium",
                ),
            ],
            images=[
                DockerImage(image="onap/policy-api", tag="4.2.2"),
                DockerImage(image="onap/cps-and-ncmp", tag="3.6.1"),
            ],
            components=[
                HelmComponent(name="policy"),
            ],
        )

        result = diff_manifests(a, b)

        assert result.summary_delta.repositories_delta == 2
        assert result.summary_delta.docker_images_delta == 1
        assert result.summary_delta.helm_components_delta == 1

    def test_schema_version_mismatch(self) -> None:
        """Different schema versions are recorded without raising."""
        a = _make_manifest(schema_version="1.0.0")
        b = _make_manifest(schema_version="2.0.0")

        result = diff_manifests(a, b)

        assert result.baseline_schema_version == "1.0.0"
        assert result.comparison_schema_version == "2.0.0"

    def test_empty_manifests(self) -> None:
        """Two empty manifests produce a fully empty diff."""
        a = _make_manifest()
        b = _make_manifest()

        result = diff_manifests(a, b)

        assert result.repositories.added == []
        assert result.repositories.removed == []
        assert result.repositories.changed == []
        assert result.repositories.unchanged_count == 0

        assert result.docker_images.added == []
        assert result.docker_images.removed == []
        assert result.docker_images.changed == []
        assert result.docker_images.unchanged_count == 0

        assert result.helm_components.added == []
        assert result.helm_components.removed == []
        assert result.helm_components.changed == []
        assert result.helm_components.unchanged_count == 0

        assert result.summary_delta.repositories_delta == 0
        assert result.summary_delta.docker_images_delta == 0
        assert result.summary_delta.helm_components_delta == 0


class TestDiffFormatters:
    """Tests for diff output formatters."""

    def test_format_text_output(self) -> None:
        """format_diff_text returns a string with key elements."""
        repo = OnapRepository(
            gerrit_project="cps",
            top_level_project="cps",
            confidence="high",
        )
        a = _make_manifest(name="ReleaseA")
        b = _make_manifest(name="ReleaseB", repos=[repo])

        result = diff_manifests(a, b)
        text = format_diff_text(result)

        assert isinstance(text, str)
        assert "ReleaseA" in text
        assert "ReleaseB" in text
        assert "cps" in text
        assert "Repositories" in text

    def test_format_json_output(self) -> None:
        """format_diff_json returns valid, parseable JSON."""
        a = _make_manifest(name="Alpha")
        b = _make_manifest(name="Beta")

        result = diff_manifests(a, b)
        json_str = format_diff_json(result)

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["baseline_release"] == "Alpha"
        assert parsed["comparison_release"] == "Beta"

    def test_format_markdown_output(self) -> None:
        """format_diff_markdown returns Markdown with heading."""
        a = _make_manifest(name="Old")
        b = _make_manifest(name="New")

        result = diff_manifests(a, b)
        md = format_diff_markdown(result)

        assert isinstance(md, str)
        assert "# Manifest Diff" in md

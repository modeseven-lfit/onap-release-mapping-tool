# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the manifest builder."""

from __future__ import annotations

from onap_release_map.collectors import CollectorResult
from onap_release_map.manifest import ManifestBuilder
from onap_release_map.models import (
    DockerImage,
    HelmComponent,
    OnapRelease,
    OnapRepository,
)


class TestManifestBuilder:
    """Tests for ManifestBuilder."""

    def test_build_empty_manifest(self) -> None:
        """Test building a manifest with no collector results."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )
        manifest = builder.build()

        assert manifest.schema_version == "1.0.0"
        assert manifest.tool_version == "0.1.0"
        assert manifest.onap_release.name == "Test"
        assert manifest.summary.total_repositories == 0

    def test_build_with_results(self) -> None:
        """Test building a manifest with collector results."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Rabat",
                oom_chart_version="18.0.0",
            ),
        )

        result = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="high",
                    discovered_by=["oom"],
                ),
            ],
            docker_images=[
                DockerImage(
                    image="onap/policy-api",
                    tag="4.2.2",
                ),
            ],
            helm_components=[
                HelmComponent(name="policy"),
            ],
        )
        builder.add_result(result)
        manifest = builder.build()

        assert manifest.summary.total_repositories == 1
        assert manifest.summary.total_docker_images == 1
        assert manifest.summary.total_helm_components == 1

    def test_to_json_deterministic(self) -> None:
        """Test that JSON output is deterministic."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
            deterministic=True,
        )
        m1 = builder.build()
        m2 = builder.build()
        json1 = ManifestBuilder.to_json(m1)
        json2 = ManifestBuilder.to_json(m2)
        assert json1 == json2

    def test_dedup_repositories(self) -> None:
        """Test that duplicate repositories are merged."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        r1 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="medium",
                    discovered_by=["oom"],
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="high",
                    discovered_by=["gerrit"],
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        assert manifest.summary.total_repositories == 1
        repo = manifest.repositories[0]
        assert repo.confidence == "high"
        assert "oom" in repo.discovered_by
        assert "gerrit" in repo.discovered_by

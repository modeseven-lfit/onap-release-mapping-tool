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

        assert manifest.schema_version == "1.1.0"
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

    def test_merge_enriches_gerrit_state(self) -> None:
        """Test that merging fills gerrit_state from another collector."""
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
                    confidence="high",
                    discovered_by=["oom"],
                    gerrit_state=None,
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="medium",
                    discovered_by=["gerrit"],
                    gerrit_state="ACTIVE",
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.gerrit_state == "ACTIVE"
        assert repo.confidence == "high"
        assert "oom" in repo.discovered_by
        assert "gerrit" in repo.discovered_by

    def test_merge_enriches_maintained(self) -> None:
        """Test that merging fills maintained from another collector."""
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
                    gerrit_project="aai/resources",
                    top_level_project="aai",
                    confidence="high",
                    discovered_by=["oom"],
                    maintained=None,
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="aai/resources",
                    top_level_project="aai",
                    confidence="medium",
                    discovered_by=["relman"],
                    maintained=True,
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.maintained is True

    def test_merge_enriches_has_ci(self) -> None:
        """Test that merging fills has_ci from another collector."""
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
                    gerrit_project="cps",
                    top_level_project="cps",
                    confidence="high",
                    discovered_by=["oom"],
                    has_ci=None,
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="cps",
                    top_level_project="cps",
                    confidence="medium",
                    discovered_by=["jjb"],
                    has_ci=True,
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.has_ci is True

    def test_merge_confidence_reasons(self) -> None:
        """Test that confidence_reasons are merged from collectors."""
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
                    confidence="high",
                    discovered_by=["oom"],
                    confidence_reasons=[
                        "Docker image referenced in OOM",
                    ],
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="medium",
                    discovered_by=["gerrit"],
                    confidence_reasons=[
                        "Discovered via Gerrit REST API",
                    ],
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert "Docker image referenced in OOM" in repo.confidence_reasons
        assert "Discovered via Gerrit REST API" in repo.confidence_reasons

    def test_collectors_used_in_summary(self) -> None:
        """Test that collectors_used in summary reflects executions."""
        from onap_release_map.models import CollectorExecution

        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        r1 = CollectorResult(
            repositories=[],
            execution=CollectorExecution(
                name="oom",
                duration_seconds=1.0,
                items_collected=10,
                errors=[],
            ),
        )
        r2 = CollectorResult(
            repositories=[],
            execution=CollectorExecution(
                name="relman",
                duration_seconds=0.5,
                items_collected=50,
                errors=[],
            ),
        )
        builder.add_result(r1)
        builder.add_result(r2)
        manifest = builder.build()

        assert manifest.summary.collectors_used == ["oom", "relman"]

    def test_merge_three_collectors(self) -> None:
        """Test merging data from three different collectors."""
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
                    confidence="high",
                    discovered_by=["oom"],
                    docker_images=["onap/policy-api"],
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="medium",
                    discovered_by=["relman"],
                    maintained=True,
                    gerrit_state="ACTIVE",
                ),
            ],
        )
        r3 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="policy/api",
                    top_level_project="policy",
                    confidence="medium",
                    discovered_by=["jjb"],
                    has_ci=True,
                ),
            ],
        )
        builder.add_result(r1)
        builder.add_result(r2)
        builder.add_result(r3)
        manifest = builder.build()

        assert manifest.summary.total_repositories == 1
        repo = manifest.repositories[0]
        assert repo.confidence == "high"
        assert repo.gerrit_state == "ACTIVE"
        assert repo.maintained is True
        assert repo.has_ci is True
        assert "oom" in repo.discovered_by
        assert "relman" in repo.discovered_by
        assert "jjb" in repo.discovered_by
        assert "onap/policy-api" in repo.docker_images

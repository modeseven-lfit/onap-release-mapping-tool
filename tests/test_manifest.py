# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the manifest builder."""

from __future__ import annotations

from onap_release_map.collectors import CollectorResult
from onap_release_map.manifest import CrossRefProvider, ManifestBuilder
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

    def test_active_gerrit_repo_resolved_to_not_in_release(self) -> None:
        """ACTIVE repo with known gerrit_state but no release signal resolves to False."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        result = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="vnfsdk/model",
                    top_level_project="vnfsdk",
                    confidence="medium",
                    discovered_by=["gerrit"],
                    gerrit_state="ACTIVE",
                    in_current_release=None,
                ),
            ],
        )
        builder.add_result(result)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.in_current_release is False

    def test_oom_repo_without_gerrit_state_in_release(self) -> None:
        """OOM-discovered repo without gerrit_state is in the release."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        result = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="mystery/project",
                    top_level_project="mystery",
                    confidence="low",
                    discovered_by=["oom"],
                    gerrit_state=None,
                    in_current_release=None,
                ),
            ],
        )
        builder.add_result(result)
        manifest = builder.build()

        repo = manifest.repositories[0]
        # OOM post-processing sets this to True
        # because "oom" is in discovered_by
        assert repo.in_current_release is True

    def test_unknown_gerrit_state_stays_undetermined(self) -> None:
        """Repo with no gerrit_state remains undetermined."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        result = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="mystery/project",
                    top_level_project="mystery",
                    confidence="low",
                    discovered_by=["relman"],
                    gerrit_state=None,
                    in_current_release=None,
                ),
            ],
        )
        builder.add_result(result)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.in_current_release is None

    def test_oom_repo_not_resolved_to_false(self) -> None:
        """OOM-discovered repo stays in release even with ACTIVE gerrit_state."""
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
        assert repo.in_current_release is True

    def test_gerrit_only_repos_resolved_to_false(self) -> None:
        """Multiple Gerrit-only ACTIVE repos all resolve to not-in-release."""
        builder = ManifestBuilder(
            tool_version="0.1.0",
            onap_release=OnapRelease(
                name="Test",
                oom_chart_version="1.0.0",
            ),
        )

        result = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="vnfsdk/model",
                    top_level_project="vnfsdk",
                    confidence="medium",
                    discovered_by=["gerrit"],
                    gerrit_state="ACTIVE",
                ),
                OnapRepository(
                    gerrit_project="music/core",
                    top_level_project="music",
                    confidence="medium",
                    discovered_by=["gerrit"],
                    gerrit_state="ACTIVE",
                ),
            ],
        )
        builder.add_result(result)
        manifest = builder.build()

        for repo in manifest.repositories:
            assert repo.in_current_release is False

    def test_relman_included_repo_not_overwritten(self) -> None:
        """Repo marked in-release by relman stays True after resolution."""
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
                    gerrit_project="sdc/sdc-fe",
                    top_level_project="sdc",
                    confidence="medium",
                    discovered_by=["relman"],
                    gerrit_state="ACTIVE",
                    in_current_release=True,
                ),
            ],
        )
        r2 = CollectorResult(
            repositories=[
                OnapRepository(
                    gerrit_project="sdc/sdc-fe",
                    top_level_project="sdc",
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
        assert repo.in_current_release is True


class _StubProvider:
    """Simple cross-reference provider for testing."""

    def __init__(
        self,
        name: str,
        targets: dict[str, str],
    ) -> None:
        self._name = name
        self._targets = targets
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def reconcile(
        self,
        repo_map: dict[str, OnapRepository],
    ) -> set[str]:
        self.call_count += 1
        promoted: set[str] = set()
        for project, reason in self._targets.items():
            repo = repo_map.get(project)
            if repo and repo.in_current_release is not True:
                repo.in_current_release = True
                repo.confidence_reasons.append(reason)
                promoted.add(project)
        return promoted


class _ChainedProvider:
    """Provider that only promotes Y when X is already in-release."""

    def __init__(
        self,
        name: str,
        prerequisite: str,
        target: str,
        reason: str,
    ) -> None:
        self._name = name
        self._prerequisite = prerequisite
        self._target = target
        self._reason = reason

    @property
    def name(self) -> str:
        return self._name

    def reconcile(
        self,
        repo_map: dict[str, OnapRepository],
    ) -> set[str]:
        prereq = repo_map.get(self._prerequisite)
        target = repo_map.get(self._target)
        if (
            prereq
            and prereq.in_current_release is True
            and target
            and target.in_current_release is not True
        ):
            target.in_current_release = True
            target.confidence_reasons.append(self._reason)
            return {self._target}
        return set()


def _make_builder_with_repos(
    *repos: OnapRepository,
) -> ManifestBuilder:
    """Create a builder pre-loaded with repos."""
    builder = ManifestBuilder(
        tool_version="0.1.0",
        onap_release=OnapRelease(
            name="Test",
            oom_chart_version="1.0.0",
        ),
    )
    builder.add_result(CollectorResult(repositories=list(repos)))
    return builder


class TestReconciliation:
    """Tests for the cross-reference reconciliation loop."""

    def test_no_providers_is_noop(self) -> None:
        """Build without providers does not alter repo state."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="vnfsdk/model",
                top_level_project="vnfsdk",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
        )
        manifest = builder.build()
        repo = manifest.repositories[0]
        assert repo.in_current_release is False

    def test_provider_promotes_repo(self) -> None:
        """A registered provider can promote a repo to in-release."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="integration",
                top_level_project="integration",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
        )
        provider = _StubProvider(
            "test",
            {"integration": "Referenced by OOM"},
        )
        builder.add_crossref_provider(provider)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.in_current_release is True
        assert "Referenced by OOM" in repo.confidence_reasons

    def test_provider_called_until_convergence(self) -> None:
        """Provider is called again after promoting, then stops."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="integration",
                top_level_project="integration",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
        )
        provider = _StubProvider(
            "test",
            {"integration": "Promoted"},
        )
        builder.add_crossref_provider(provider)
        builder.build()

        # Pass 1 promotes, pass 2 finds nothing → converge
        assert provider.call_count == 2

    def test_recursive_promotion_across_passes(self) -> None:
        """Chained providers promote repos across passes."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="policy/api",
                top_level_project="policy",
                confidence="high",
                discovered_by=["oom"],
                gerrit_state="ACTIVE",
            ),
            OnapRepository(
                gerrit_project="integration",
                top_level_project="integration",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
            OnapRepository(
                gerrit_project="demo",
                top_level_project="demo",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
        )
        # Provider A: promotes integration (unconditionally)
        prov_a = _StubProvider(
            "provA",
            {"integration": "Image in repositoryGenerator"},
        )
        # Provider B: promotes demo only if integration is in-release
        prov_b = _ChainedProvider(
            "provB",
            prerequisite="integration",
            target="demo",
            reason="Referenced by integration",
        )
        builder.add_crossref_provider(prov_a)
        builder.add_crossref_provider(prov_b)
        manifest = builder.build()

        names_in = {
            r.gerrit_project
            for r in manifest.repositories
            if r.in_current_release is True
        }
        assert "integration" in names_in
        assert "demo" in names_in

    def test_parent_re_promoted_after_crossref(self) -> None:
        """Parent projects are re-promoted after cross-ref discovery."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="dmaap",
                top_level_project="dmaap",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
                is_parent_project=True,
            ),
            OnapRepository(
                gerrit_project="dmaap/datarouter",
                top_level_project="dmaap",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="ACTIVE",
            ),
        )
        # Provider promotes the child
        provider = _StubProvider(
            "test",
            {"dmaap/datarouter": "Image in repositoryGenerator"},
        )
        builder.add_crossref_provider(provider)
        manifest = builder.build()

        child = next(
            r for r in manifest.repositories if r.gerrit_project == "dmaap/datarouter"
        )
        parent = next(r for r in manifest.repositories if r.gerrit_project == "dmaap")
        assert child.in_current_release is True
        assert parent.in_current_release is True

    def test_readonly_not_promoted(self) -> None:
        """READ_ONLY repos are not promoted by providers."""
        builder = _make_builder_with_repos(
            OnapRepository(
                gerrit_project="old/archived",
                top_level_project="old",
                confidence="medium",
                discovered_by=["gerrit"],
                gerrit_state="READ_ONLY",
                in_current_release=False,
            ),
        )
        provider = _StubProvider(
            "test",
            {"old/archived": "Should not promote"},
        )
        builder.add_crossref_provider(provider)
        manifest = builder.build()

        repo = manifest.repositories[0]
        assert repo.in_current_release is False

    def test_stub_satisfies_protocol(self) -> None:
        """_StubProvider satisfies the CrossRefProvider protocol."""
        provider = _StubProvider("x", {})
        assert isinstance(provider, CrossRefProvider)

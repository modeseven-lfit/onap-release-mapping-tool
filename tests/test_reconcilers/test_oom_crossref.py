# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the OOM cross-reference reconciliation provider."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from onap_release_map.manifest import CrossRefProvider
from onap_release_map.models import OnapRepository
from onap_release_map.reconcilers.oom_crossref import OOMCrossRefProvider


@pytest.fixture()
def oom_crossref_path(tmp_path: Path) -> Path:
    """Create a minimal OOM tree with cross-references."""
    k8s = tmp_path / "kubernetes"

    # aai component referencing aai/test-config
    aai_dir = k8s / "aai" / "components" / "aai-sparky-be"
    aai_dir.mkdir(parents=True)
    (aai_dir / "values.yaml").write_text(
        "  gerritProject: http://gerrit.onap.org/r/aai/test-config\n",
        encoding="utf-8",
    )

    # so component referencing so/docker-config
    so_dir = k8s / "so" / "components" / "so-mariadb"
    so_dir.mkdir(parents=True)
    (so_dir / "values.yaml").write_text(
        "  gerritProject: http://gerrit.onap.org/r/so/docker-config.git\n",
        encoding="utf-8",
    )

    # onap/values.yaml with disabled components
    onap_dir = k8s / "onap"
    onap_dir.mkdir(parents=True)
    (onap_dir / "values.yaml").write_text(
        "holmes:\n  enabled: false\ndmaap:\n  enabled: false\n",
        encoding="utf-8",
    )

    # policy template referencing integration
    policy_tpl = k8s / "policy" / "templates"
    policy_tpl.mkdir(parents=True)
    (policy_tpl / "configmap.yaml").write_text(
        "data:\n  ref: integration/csit\n",
        encoding="utf-8",
    )

    return tmp_path


def _make_repo(
    project: str,
    *,
    in_release: bool | None = None,
    state: Literal["ACTIVE", "READ_ONLY"] = "ACTIVE",
    parent: bool | None = None,
) -> OnapRepository:
    """Create a minimal OnapRepository for testing."""
    return OnapRepository(
        gerrit_project=project,
        top_level_project=project.split("/")[0],
        confidence="medium",
        discovered_by=["gerrit"],
        gerrit_state=state,
        in_current_release=in_release,
        is_parent_project=parent,
    )


class TestOOMCrossRefProvider:
    """Tests for OOMCrossRefProvider."""

    def test_satisfies_protocol(self, tmp_path: Path) -> None:
        """Provider satisfies the CrossRefProvider protocol."""
        provider = OOMCrossRefProvider(tmp_path)
        assert isinstance(provider, CrossRefProvider)

    def test_name(self, tmp_path: Path) -> None:
        """Provider reports its name."""
        provider = OOMCrossRefProvider(tmp_path)
        assert provider.name == "oom-crossref"

    def test_gerrit_url_reference(self, oom_crossref_path: Path) -> None:
        """Provider finds explicit Gerrit URL cross-references."""
        repo_map = {
            "aai/test-config": _make_repo("aai/test-config"),
            "so/docker-config": _make_repo("so/docker-config"),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)

        assert "aai/test-config" in promoted
        assert "so/docker-config" in promoted
        assert repo_map["aai/test-config"].in_current_release is True
        assert repo_map["so/docker-config"].in_current_release is True

    def test_word_boundary_match(self, oom_crossref_path: Path) -> None:
        """Provider finds word-boundary matches in OOM files."""
        repo_map = {
            "integration/csit": _make_repo("integration/csit"),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)

        assert "integration/csit" in promoted

    def test_skips_already_in_release(self, oom_crossref_path: Path) -> None:
        """Provider does not re-promote repos already in release."""
        repo_map = {
            "aai/test-config": _make_repo("aai/test-config", in_release=True),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)

        assert len(promoted) == 0

    def test_skips_readonly(self, oom_crossref_path: Path) -> None:
        """Provider does not promote READ_ONLY repos."""
        repo_map = {
            "aai/test-config": _make_repo("aai/test-config", state="READ_ONLY"),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)

        assert len(promoted) == 0

    def test_skips_short_names(self, oom_crossref_path: Path) -> None:
        """Provider skips very short project names to avoid noise."""
        repo_map = {
            "cli": _make_repo("cli"),
            "doc": _make_repo("doc"),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)

        assert len(promoted) == 0

    def test_missing_oom_path(self, tmp_path: Path) -> None:
        """Provider returns empty set when OOM path is missing."""
        provider = OOMCrossRefProvider(tmp_path / "nonexistent")
        repo_map = {
            "demo": _make_repo("demo"),
        }
        promoted = provider.reconcile(repo_map)
        assert len(promoted) == 0

    def test_confidence_reason_added(self, oom_crossref_path: Path) -> None:
        """Promoted repos get a confidence reason."""
        repo_map = {
            "aai/test-config": _make_repo("aai/test-config"),
        }
        provider = OOMCrossRefProvider(oom_crossref_path)
        provider.reconcile(repo_map)

        reasons = repo_map["aai/test-config"].confidence_reasons
        assert any("OOM" in r for r in reasons)

    def test_empty_candidates(self, oom_crossref_path: Path) -> None:
        """No candidates produces no promotions."""
        repo_map: dict[str, OnapRepository] = {}
        provider = OOMCrossRefProvider(oom_crossref_path)
        promoted = provider.reconcile(repo_map)
        assert promoted == set()

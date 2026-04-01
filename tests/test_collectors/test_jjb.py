# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the JJB collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from onap_release_map.collectors import registry
from onap_release_map.collectors.jjb import JJBCollector


class TestJJBCollector:
    """Tests for JJBCollector."""

    def test_jjb_collect_basic(self, tmp_path: Path) -> None:
        """Test basic collection from JJB YAML files."""
        policy_dir = tmp_path / "policy"
        policy_dir.mkdir()
        (policy_dir / "policy-api.yaml").write_text(
            "---\n"
            "- project:\n"
            "    name: policy-api-java-17\n"
            '    project-name: "policy-api"\n'
            "    jobs:\n"
            '      - "{project-name}-verify"\n'
            '    project: "policy/api"\n'
            "    stream:\n"
            '      - "master":\n'
            '          branch: "master"\n',
            encoding="utf-8",
        )

        aai_dir = tmp_path / "aai"
        aai_dir.mkdir()
        (aai_dir / "aai-babel.yaml").write_text(
            "---\n"
            "- project:\n"
            "    name: aai-babel\n"
            '    project-name: "aai-babel"\n'
            "    jobs:\n"
            "      - gerrit-maven-verify\n"
            '    project: "aai/babel"\n',
            encoding="utf-8",
        )

        collector = JJBCollector(jjb_path=tmp_path)
        result = collector.collect()

        assert len(result.repositories) == 2

        projects = {r.gerrit_project for r in result.repositories}
        assert projects == {"aai/babel", "policy/api"}

        for repo in result.repositories:
            assert repo.has_ci is True
            assert repo.discovered_by == ["jjb"]

    def test_jjb_template_exclusion(self, tmp_path: Path) -> None:
        """Test that template placeholders are excluded."""
        (tmp_path / "templated.yaml").write_text(
            '---\n- project:\n    name: some-project\n    project: "{name}"\n',
            encoding="utf-8",
        )

        collector = JJBCollector(jjb_path=tmp_path)
        result = collector.collect()

        assert len(result.repositories) == 0

    def test_jjb_deduplication(self, tmp_path: Path) -> None:
        """Test that duplicate project references are deduplicated."""
        (tmp_path / "file1.yaml").write_text(
            '---\n- project:\n    name: policy-api-verify\n    project: "policy/api"\n',
            encoding="utf-8",
        )
        (tmp_path / "file2.yaml").write_text(
            '---\n- project:\n    name: policy-api-merge\n    project: "policy/api"\n',
            encoding="utf-8",
        )

        collector = JJBCollector(jjb_path=tmp_path)
        result = collector.collect()

        assert len(result.repositories) == 1
        assert result.repositories[0].gerrit_project == "policy/api"

    def test_jjb_missing_path(self) -> None:
        """Test that collect raises ValueError without jjb_path."""
        collector = JJBCollector()
        with pytest.raises(ValueError, match="jjb_path"):
            collector.collect()

    def test_jjb_malformed_yaml(self, tmp_path: Path) -> None:
        """Test that malformed YAML is handled gracefully."""
        (tmp_path / "bad.yaml").write_text(
            "{{{\nnot: valid: yaml: [unbalanced\n",
            encoding="utf-8",
        )

        collector = JJBCollector(jjb_path=tmp_path)
        result = collector.collect()

        assert len(result.repositories) == 0

    def test_jjb_custom_gerrit_url(self, tmp_path: Path) -> None:
        """Test that a custom gerrit_url is used in repository links."""
        (tmp_path / "example.yaml").write_text(
            '---\n- project:\n    name: sdnc-oam\n    project: "sdnc/oam"\n',
            encoding="utf-8",
        )

        custom_url = "https://gerrit.custom.org/r"
        collector = JJBCollector(jjb_path=tmp_path, gerrit_url=custom_url)
        result = collector.collect()

        assert len(result.repositories) == 1
        repo = result.repositories[0]
        assert repo.gerrit_url.startswith(custom_url)
        assert "gerrit.onap.org" not in repo.gerrit_url

    def test_jjb_default_gerrit_url(self, tmp_path: Path) -> None:
        """Test that the default ONAP Gerrit URL is used when none given."""
        (tmp_path / "example.yaml").write_text(
            '---\n- project:\n    name: sdnc-oam\n    project: "sdnc/oam"\n',
            encoding="utf-8",
        )

        collector = JJBCollector(jjb_path=tmp_path)
        result = collector.collect()

        assert len(result.repositories) == 1
        assert "gerrit.onap.org" in result.repositories[0].gerrit_url

    def test_jjb_registration(self) -> None:
        """Test that JJBCollector is registered in the collector registry."""
        collector_cls = registry.get("jjb")
        assert collector_cls is JJBCollector

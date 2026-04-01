# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the relman collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from onap_release_map.collectors import registry
from onap_release_map.collectors.relman import RelmanCollector, _parse_bool


class TestRelmanCollector:
    """Tests for RelmanCollector."""

    def test_relman_collect_basic(self, tmp_path: Path) -> None:
        """Test basic collection from a sample repos.yaml."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "policy:\n"
            "  - repository: 'policy/api'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n"
            "  - repository: 'policy/docker'\n"
            "    unmaintained: 'true'\n"
            "    read_only: 'true'\n"
            "    included_in: '[]'\n"
            "aai:\n"
            "  - repository: 'aai/resources'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )

        collector = RelmanCollector(repos_yaml_path=repos_yaml)
        result = collector.collect()

        assert len(result.repositories) == 3

        by_project = {r.gerrit_project: r for r in result.repositories}

        # policy/api — maintained, active, runtime
        api = by_project["policy/api"]
        assert api.maintained is True
        assert api.gerrit_state == "ACTIVE"
        assert api.category == "runtime"
        assert api.discovered_by == ["relman"]
        assert api.confidence == "medium"
        assert api.confidence_reasons == ["Listed in relman repos.yaml"]

        # policy/docker — unmaintained AND read-only → build-dependency
        docker = by_project["policy/docker"]
        assert docker.maintained is False
        assert docker.gerrit_state == "READ_ONLY"
        assert docker.category == "build-dependency"
        assert docker.discovered_by == ["relman"]
        assert docker.confidence == "medium"
        assert docker.confidence_reasons == ["Listed in relman repos.yaml"]

        # aai/resources — maintained, active, runtime
        aai = by_project["aai/resources"]
        assert aai.maintained is True
        assert aai.gerrit_state == "ACTIVE"
        assert aai.category == "runtime"
        assert aai.discovered_by == ["relman"]
        assert aai.confidence == "medium"
        assert aai.confidence_reasons == ["Listed in relman repos.yaml"]

    def test_relman_string_booleans(self) -> None:
        """Test _parse_bool handles various boolean representations."""
        assert _parse_bool("true") is True
        assert _parse_bool("false") is False
        assert _parse_bool(True) is True
        assert _parse_bool(False) is False
        assert _parse_bool("True") is True
        assert _parse_bool("FALSE") is False
        assert _parse_bool(" true ") is True
        assert _parse_bool(None) is False

    def test_relman_missing_path(self) -> None:
        """Test that collect raises ValueError without repos_yaml_path."""
        collector = RelmanCollector()
        with pytest.raises(ValueError, match="repos_yaml_path"):
            collector.collect()

    def test_relman_empty_file(self, tmp_path: Path) -> None:
        """Test that an empty YAML file returns an empty result."""
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("", encoding="utf-8")

        collector = RelmanCollector(repos_yaml_path=empty_yaml)
        result = collector.collect()

        assert len(result.repositories) == 0

    def test_relman_registration(self) -> None:
        """Test that RelmanCollector is registered in the global registry."""
        cls = registry.get("relman")
        assert cls is RelmanCollector

    def test_relman_custom_gerrit_url(self, tmp_path: Path) -> None:
        """Test that a custom gerrit_url is used in repository links."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "policy:\n"
            "  - repository: 'policy/api'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )

        collector = RelmanCollector(
            repos_yaml_path=repos_yaml,
            gerrit_url="https://custom-gerrit.example.com/r",
        )
        result = collector.collect()

        assert len(result.repositories) == 1
        repo = result.repositories[0]
        assert repo.gerrit_url is not None
        assert repo.gerrit_url.startswith(
            "https://custom-gerrit.example.com/r/admin/repos/"
        )

    def test_relman_default_gerrit_url(self, tmp_path: Path) -> None:
        """Test that the default Gerrit URL is used when none is provided."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "aai:\n"
            "  - repository: 'aai/resources'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )

        collector = RelmanCollector(repos_yaml_path=repos_yaml)
        result = collector.collect()

        assert len(result.repositories) == 1
        repo = result.repositories[0]
        assert repo.gerrit_url is not None
        assert repo.gerrit_url.startswith("https://gerrit.onap.org/r/admin/repos/")

    def test_relman_timed_collect(self, tmp_path: Path) -> None:
        """Test timed_collect populates execution metadata."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "sdnc:\n"
            "  - repository: 'sdnc/oam'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )

        collector = RelmanCollector(repos_yaml_path=repos_yaml)
        result = collector.timed_collect()

        assert result.execution is not None
        assert result.execution.name == "relman"
        assert result.execution.duration_seconds >= 0
        assert result.execution.items_collected == 1
        assert result.execution.errors == []

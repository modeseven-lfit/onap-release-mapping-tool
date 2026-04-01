# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the OOM collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from onap_release_map.collectors import registry
from onap_release_map.collectors.oom import OOMCollector


class TestOOMCollector:
    """Tests for OOMCollector."""

    def test_collector_is_registered(self) -> None:
        """Test that OOMCollector is in the registry."""
        assert "oom" in registry.list_names()

    def test_collect_requires_oom_path(self) -> None:
        """Test that collect raises without oom_path."""
        collector = OOMCollector()
        with pytest.raises(ValueError, match="oom_path"):
            collector.collect()

    def test_collect_with_sample_oom(self, sample_oom_path: Path) -> None:
        """Test collection with sample OOM data."""
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.collect()

        assert len(result.repositories) > 0
        assert len(result.docker_images) > 0
        assert len(result.helm_components) > 0

        # Check we found expected repos
        project_names = [r.gerrit_project for r in result.repositories]
        assert "oom" in project_names

    def test_timed_collect(self, sample_oom_path: Path) -> None:
        """Test timed_collect produces execution metadata."""
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.timed_collect()

        assert result.execution is not None
        assert result.execution.name == "oom"
        assert result.execution.duration_seconds >= 0
        assert result.execution.items_collected > 0

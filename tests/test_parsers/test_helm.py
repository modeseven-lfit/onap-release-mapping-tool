# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the Helm chart parser."""

from __future__ import annotations

from pathlib import Path

from onap_release_map.parsers.helm import HelmChartParser


class TestHelmChartParser:
    """Tests for HelmChartParser."""

    def test_parse_umbrella_chart(self, sample_oom_path: Path) -> None:
        """Test parsing a sample OOM umbrella chart."""
        parser = HelmChartParser(sample_oom_path)
        components, images, _ = parser.parse_umbrella_chart()

        assert len(components) >= 3
        component_names = [c["name"] for c in components]
        assert "policy" in component_names
        assert "aai" in component_names
        assert "cps" in component_names

    def test_extract_images(self, sample_oom_path: Path) -> None:
        """Test that Docker images are extracted from values.yaml."""
        parser = HelmChartParser(sample_oom_path)
        _, images, _ = parser.parse_umbrella_chart()

        image_names = [img["image"] for img in images]
        assert "onap/policy-api" in image_names
        assert "onap/policy-pap" in image_names
        assert "onap/aai-resources" in image_names

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """Test parser with a nonexistent OOM path."""
        parser = HelmChartParser(tmp_path / "nonexistent")
        components, images, _ = parser.parse_umbrella_chart()
        assert components == []
        assert images == []

    def test_parse_repository_generator(self, sample_oom_path: Path) -> None:
        """Test parsing repositoryGenerator for infrastructure images."""
        parser = HelmChartParser(sample_oom_path)
        images = parser.parse_repository_generator()

        image_names = [img["image"] for img in images]
        assert "onap/oom/readiness" in image_names
        assert "onap/integration-java11" in image_names
        # Non-ONAP images must be excluded
        assert all(
            isinstance(img["image"], str) and img["image"].startswith("onap/")
            for img in images
        )
        # Registry should be applied from global.repository
        for img in images:
            assert img["registry"] == "nexus3.onap.org:10001"
        # chart_name attribution
        for img in images:
            assert img["chart_name"] == "repositoryGenerator"

    def test_repository_generator_missing(self, tmp_path: Path) -> None:
        """Parser returns empty list when repositoryGenerator is absent."""
        parser = HelmChartParser(tmp_path / "nonexistent")
        images = parser.parse_repository_generator()
        assert images == []

    def test_excludes_argo_dir(self, sample_oom_path: Path) -> None:
        """Test that argo directory is excluded from walking."""
        # Place argo under a component's components/ path where it would be walked
        argo_dir = sample_oom_path / "kubernetes" / "policy" / "components" / "argo"
        argo_dir.mkdir(parents=True)
        (argo_dir / "Chart.yaml").write_text(
            "apiVersion: v2\nname: argo\nversion: 1.0.0\n",
            encoding="utf-8",
        )
        (argo_dir / "values.yaml").write_text(
            "image: onap/argo-fake:1.0.0\n",
            encoding="utf-8",
        )

        parser = HelmChartParser(sample_oom_path)
        _, images, _ = parser.parse_umbrella_chart()
        image_names = [img["image"] for img in images]
        assert "onap/argo-fake" not in image_names

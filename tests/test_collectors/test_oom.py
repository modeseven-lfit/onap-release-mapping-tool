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

    def test_collect_includes_repository_generator(self, sample_oom_path: Path) -> None:
        """Test that repositoryGenerator images are included."""
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.collect()

        # Infrastructure images from repositoryGenerator must appear
        image_names = [img.image for img in result.docker_images]
        assert "onap/oom/readiness" in image_names
        assert "onap/integration-java11" in image_names

        # Non-ONAP images (busybox) must be excluded
        assert "busybox" not in image_names

        # The repositoryGenerator chart attribution must propagate
        readiness = next(
            img for img in result.docker_images if img.image == "onap/oom/readiness"
        )
        assert "repositoryGenerator" in readiness.helm_charts

    def test_timed_collect(self, sample_oom_path: Path) -> None:
        """Test timed_collect produces execution metadata."""
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.timed_collect()

        assert result.execution is not None
        assert result.execution.name == "oom"
        assert result.execution.duration_seconds >= 0
        assert result.execution.items_collected > 0

    def test_attribution_fields_populated(self, sample_oom_path: Path) -> None:
        """Every collected image carries a non-empty attribution reason.

        The OOM collector now calls :meth:`ImageMapper.resolve` instead
        of the thin :meth:`map_image` wrapper and persists the full
        :class:`MappingResult` onto each :class:`DockerImage` record.
        Every image therefore gains a populated ``attribution_reason``
        string (the serialised ``MappingReason`` value), regardless of
        whether the mapping succeeded. This is the observability
        contract described in the class docstring and promised by the
        validator's audit paths.
        """
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.collect()

        # The sample OOM fixture should produce at least one image.
        assert result.docker_images, "expected at least one image"

        for img in result.docker_images:
            # Every image must carry a reason string. Empty/None is
            # never correct after resolve(): the mapper always sets
            # reason, even on the unresolved path.
            assert img.attribution_reason, (
                f"image {img.image!r} has empty attribution_reason"
            )
            # attribution_alternatives defaults to an empty list, so
            # the type must always be a list rather than None.
            assert isinstance(img.attribution_alternatives, list)

    def test_attribution_without_ground_truth_marked_none(
        self,
        sample_oom_path: Path,
    ) -> None:
        """Without known_projects, verified is None rather than False.

        The collector distinguishes "verification not attempted" from
        "verification failed" by passing ``None`` for
        ``attribution_verified`` when no ground truth was supplied.
        This matches the semantics of ``ImageMapper.has_ground_truth``
        and keeps the audit validator's ``AUDIT_SKIPPED`` branch
        distinguishable from genuine verification failures.
        """
        collector = OOMCollector(oom_path=sample_oom_path)
        result = collector.collect()

        for img in result.docker_images:
            assert img.attribution_verified is None, (
                f"image {img.image!r} should have verified=None without "
                f"ground truth, got {img.attribution_verified!r}"
            )

    def test_attribution_with_ground_truth_marked_bool(
        self,
        sample_oom_path: Path,
    ) -> None:
        """With known_projects, verified becomes a real bool per image.

        When the collector receives a non-empty ``known_projects``
        set, every image gains a concrete ``True``/``False`` flag on
        ``attribution_verified`` reflecting whether its resolved
        project was found in ground truth. ``None`` becomes invalid
        in this regime — that would indicate the wiring forgot to
        thread the flag through.
        """
        # Seed ground truth with a project that matches the shipped
        # override for onap/integration-java11 so at least one image
        # in the fixture resolves cleanly against known_projects.
        ground_truth = {"integration/docker/onap-java11", "oom/readiness"}
        collector = OOMCollector(
            oom_path=sample_oom_path,
            known_projects=ground_truth,
        )
        result = collector.collect()

        for img in result.docker_images:
            assert isinstance(img.attribution_verified, bool), (
                f"image {img.image!r} should have a bool verified flag "
                f"with ground truth supplied, got {img.attribution_verified!r}"
            )

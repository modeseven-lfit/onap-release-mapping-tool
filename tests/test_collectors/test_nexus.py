# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the Nexus collector."""

from __future__ import annotations

import httpx
import respx

from onap_release_map.collectors import CollectorResult, registry
from onap_release_map.collectors.nexus import NexusCollector
from onap_release_map.models import DockerImage

NEXUS_URL = "https://nexus3.onap.org"


class TestNexusCollector:
    """Tests for NexusCollector."""

    def test_nexus_registration(self) -> None:
        """NexusCollector is discoverable through the collector registry."""
        assert "nexus" in registry.list_names()
        assert registry.get("nexus") is NexusCollector

    def test_collect_empty_images(self) -> None:
        """No images provided yields an empty CollectorResult."""
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=[],
            concurrent_workers=1,
        )
        result = collector.collect()

        assert isinstance(result, CollectorResult)
        assert len(result.docker_images) == 0

    @respx.mock
    def test_collect_validates_found(self) -> None:
        """Image tag present in Nexus sets nexus_validated=True."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            return_value=httpx.Response(200),
        )

        images = [DockerImage(image="onap/policy-api", tag="4.2.2")]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.collect()

        assert len(result.docker_images) == 1
        assert result.docker_images[0].nexus_validated is True
        assert result.docker_images[0].image == "onap/policy-api"
        assert result.docker_images[0].tag == "4.2.2"

    @respx.mock
    def test_collect_validates_not_found(self) -> None:
        """Missing manifest in Nexus sets nexus_validated=False."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            return_value=httpx.Response(404),
        )

        images = [DockerImage(image="onap/policy-api", tag="4.2.2")]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.collect()

        assert len(result.docker_images) == 1
        assert result.docker_images[0].nexus_validated is False

    @respx.mock
    def test_collect_handles_http_error(self) -> None:
        """HTTP 500 sets nexus_validated=False without raising."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            return_value=httpx.Response(500),
        )

        images = [DockerImage(image="onap/policy-api", tag="4.2.2")]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.collect()

        assert len(result.docker_images) == 1
        assert result.docker_images[0].nexus_validated is False

    @respx.mock
    def test_collect_handles_network_error(self) -> None:
        """Network error sets nexus_validated=False without raising."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            side_effect=httpx.ConnectError("Connection refused"),
        )

        images = [DockerImage(image="onap/policy-api", tag="4.2.2")]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.collect()

        assert len(result.docker_images) == 1
        assert result.docker_images[0].nexus_validated is False

    @respx.mock
    def test_timed_collect(self) -> None:
        """timed_collect populates execution metadata."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            return_value=httpx.Response(200),
        )

        images = [DockerImage(image="onap/policy-api", tag="4.2.2")]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.timed_collect()

        assert result.execution is not None
        assert result.execution.name == "nexus"
        assert result.execution.duration_seconds >= 0
        assert len(result.docker_images) == 1
        assert result.docker_images[0].nexus_validated is True

    @respx.mock
    def test_collect_multiple_images(self) -> None:
        """Multiple images get correct per-image validation status."""
        respx.head(f"{NEXUS_URL}/v2/onap/policy-api/manifests/4.2.2").mock(
            return_value=httpx.Response(200),
        )
        respx.head(f"{NEXUS_URL}/v2/onap/sdc-be/manifests/2.0.0").mock(
            return_value=httpx.Response(404),
        )

        images = [
            DockerImage(image="onap/policy-api", tag="4.2.2"),
            DockerImage(image="onap/sdc-be", tag="2.0.0"),
        ]
        collector = NexusCollector(
            nexus_url=NEXUS_URL,
            docker_images=images,
            concurrent_workers=1,
        )
        result = collector.collect()

        assert len(result.docker_images) == 2

        by_image = {img.image: img for img in result.docker_images}
        assert by_image["onap/policy-api"].nexus_validated is True
        assert by_image["onap/sdc-be"].nexus_validated is False

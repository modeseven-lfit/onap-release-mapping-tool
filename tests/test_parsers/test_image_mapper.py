# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the image mapper."""

from __future__ import annotations

from onap_release_map.parsers.image_mapper import ImageMapper


class TestImageMapper:
    """Tests for ImageMapper."""

    def test_explicit_mapping(self) -> None:
        """Test explicit mapping lookup."""
        mapper = ImageMapper()
        assert mapper.map_image("onap/policy-api") == "policy/api"
        assert mapper.map_image("onap/ccsdk-blueprintsprocessor") == "ccsdk/cds"

    def test_org_onap_heuristic(self) -> None:
        """Test org.onap.* heuristic mapping."""
        mapper = ImageMapper()
        # Use an image NOT in the explicit mapping table so the
        # org.onap.* heuristic code path is actually exercised.
        result = mapper.map_image("onap/org.onap.fake.project.submod")
        assert result == "fake/project"

    def test_slash_passthrough(self) -> None:
        """Test slash-based image names map directly."""
        mapper = ImageMapper()
        # Use an image NOT in the explicit mapping table so the
        # slash-passthrough heuristic code path is actually exercised.
        result = mapper.map_image("onap/fake-project/submodule")
        assert result == "fake-project/submodule"

    def test_get_top_level_project(self) -> None:
        """Test top-level project extraction."""
        mapper = ImageMapper()
        assert mapper.get_top_level_project("policy/api") == "policy"
        assert mapper.get_top_level_project("cps") == "cps"
        assert mapper.get_top_level_project("so/adapters/foo") == "so"

    def test_unmapped_image_returns_none(self) -> None:
        """Test that unmapped images return None."""
        mapper = ImageMapper()
        result = mapper.map_image("unknown/random-image")
        assert result is None

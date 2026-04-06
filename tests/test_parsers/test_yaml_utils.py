# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for safe YAML loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from onap_release_map.parsers.yaml_utils import safe_load_yaml, safe_load_yaml_string

DUPLICATE_ANCHOR_YAML = (
    "first: &myAnchor value1\n"
    "middle: something\n"
    "second: &myAnchor value2\n"
    "ref: *myAnchor\n"
)


class TestSafeLoadYamlString:
    """Tests for the safe_load_yaml_string helper."""

    def test_valid_yaml(self) -> None:
        """Parse a simple dict and verify keys and values match."""
        content = "name: onap\nversion: 1\n"
        result = safe_load_yaml_string(content)
        assert result["name"] == "onap"
        assert result["version"] == 1

    def test_empty_string(self) -> None:
        """An empty string should return an empty dict."""
        result = safe_load_yaml_string("")
        assert result == {}

    def test_invalid_yaml(self) -> None:
        """Broken YAML should return an empty dict."""
        result = safe_load_yaml_string(":\n  - :\n  :")
        assert result == {}

    def test_non_dict_yaml(self) -> None:
        """YAML that parses to a list should return an empty dict."""
        result = safe_load_yaml_string("- item1\n- item2\n")
        assert result == {}

    def test_duplicate_anchor_succeeds(self) -> None:
        """Duplicate YAML anchors must parse without error.

        PyYAML resolves duplicate anchors by letting the last
        definition win for subsequent alias references.
        """
        result = safe_load_yaml_string(DUPLICATE_ANCHOR_YAML)
        assert result != {}, "Duplicate-anchor YAML must not return {}"
        assert result["first"] == "value1"
        assert result["middle"] == "something"
        assert result["second"] == "value2"
        assert result["ref"] == "value2"

    def test_duplicate_anchor_no_error_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No 'YAML parse error' warning for duplicate anchors."""
        with caplog.at_level(logging.WARNING):
            safe_load_yaml_string(DUPLICATE_ANCHOR_YAML)
        assert "YAML parse error" not in caplog.text


class TestSafeLoadYaml:
    """Tests for the safe_load_yaml file-based helper."""

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Load a simple YAML file and verify the parsed content."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\n", encoding="utf-8")
        result = safe_load_yaml(yaml_file)
        assert result == {"key": "value"}

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """A nonexistent file should return an empty dict."""
        result = safe_load_yaml(tmp_path / "missing.yaml")
        assert result == {}

    def test_warning_includes_file_path(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning message must mention the problematic file path."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(":\n  - :\n  :", encoding="utf-8")
        with caplog.at_level(logging.WARNING):
            safe_load_yaml(bad_file)
        assert str(bad_file) in caplog.text

    def test_duplicate_anchor_in_file(self, tmp_path: Path) -> None:
        """Duplicate anchors in a file must parse correctly."""
        yaml_file = tmp_path / "anchors.yaml"
        yaml_file.write_text(DUPLICATE_ANCHOR_YAML, encoding="utf-8")
        result = safe_load_yaml(yaml_file)
        assert result != {}, "Duplicate-anchor YAML file must not return {}"
        assert result["first"] == "value1"
        assert result["middle"] == "something"
        assert result["second"] == "value2"
        assert result["ref"] == "value2"

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from onap_release_map.cli import app

runner = CliRunner()


class TestVersion:
    """Test version-related commands."""

    def test_version_command(self) -> None:
        """Test the version subcommand."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "onap-release-map" in result.output

    def test_version_flag(self) -> None:
        """Test the --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "onap-release-map" in result.output


class TestSchema:
    """Test schema subcommand."""

    def test_schema_output(self) -> None:
        """Test that schema subcommand outputs valid JSON."""
        import json

        result = runner.invoke(app, ["schema"])
        assert result.exit_code == 0
        schema = json.loads(result.output)
        assert schema["title"] == "ONAP Release Manifest"
        assert "$schema" in schema


class TestDiscover:
    """Test discover subcommand."""

    def test_discover_missing_oom_path(self) -> None:
        """Test that discover fails without --oom-path."""
        result = runner.invoke(app, ["discover"])
        assert result.exit_code != 0

    def test_discover_nonexistent_path(self) -> None:
        """Test that discover fails with a nonexistent path."""
        result = runner.invoke(app, ["discover", "--oom-path", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_discover_with_sample_oom(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test discover with a sample OOM structure."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "discover",
                "--oom-path",
                str(sample_oom_path),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert (output_dir / "manifest.json").exists()

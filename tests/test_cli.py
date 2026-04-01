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

    def test_discover_unknown_collector(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that discover rejects an unknown collector name."""
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "unknown",
                "--oom-path",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "unknown collector" in result.output

    def test_discover_relman_missing_path(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that relman collector requires --repos-yaml."""
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom,relman",
                "--oom-path",
                str(sample_oom_path),
            ],
        )
        assert result.exit_code != 0
        assert "--repos-yaml is required" in result.output

    def test_discover_jjb_missing_path(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that jjb collector requires --jjb-path."""
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom,jjb",
                "--oom-path",
                str(sample_oom_path),
            ],
        )
        assert result.exit_code != 0
        assert "--jjb-path is required" in result.output

    def test_discover_with_relman(self, sample_oom_path: Path, tmp_path: Path) -> None:
        """Test discover with oom and relman collectors."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "policy:\n"
            "  - repository: 'policy/api'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom,relman",
                "--oom-path",
                str(sample_oom_path),
                "--repos-yaml",
                str(repos_yaml),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert (output_dir / "manifest.json").exists()

    def test_discover_with_jjb(self, sample_oom_path: Path, tmp_path: Path) -> None:
        """Test discover with oom and jjb collectors."""
        jjb_dir = tmp_path / "jjb"
        jjb_dir.mkdir()
        jjb_file = jjb_dir / "policy-api.yaml"
        jjb_file.write_text(
            "---\n"
            "- project:\n"
            "    name: policy-api\n"
            '    project-name: "policy-api"\n'
            '    project: "policy/api"\n',
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom,jjb",
                "--oom-path",
                str(sample_oom_path),
                "--jjb-path",
                str(jjb_dir),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert (output_dir / "manifest.json").exists()

    def test_discover_collectors_display(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that enabled collectors are displayed in output."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom",
                "--oom-path",
                str(sample_oom_path),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Collectors: oom" in result.output

    def test_discover_empty_collectors(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that an empty --collectors value is rejected."""
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "",
                "--oom-path",
                str(sample_oom_path),
            ],
        )
        assert result.exit_code != 0
        assert "no collectors specified" in result.output

    def test_discover_oom_missing_path(self, tmp_path: Path) -> None:
        """Test that oom collector requires --oom-path."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text(
            "policy:\n"
            "  - repository: 'policy/api'\n"
            "    unmaintained: 'false'\n"
            "    read_only: 'false'\n"
            "    included_in: '[]'\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "relman",
                "--repos-yaml",
                str(repos_yaml),
            ],
        )
        assert result.exit_code == 0
        assert "Collectors: relman" in result.output

    def test_discover_duplicate_collectors(
        self, sample_oom_path: Path, tmp_path: Path
    ) -> None:
        """Test that duplicate collector names are deduplicated."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "discover",
                "--collectors",
                "oom,oom",
                "--oom-path",
                str(sample_oom_path),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        # Deduplicated list should show "oom" only once
        assert "Collectors: oom" in result.output

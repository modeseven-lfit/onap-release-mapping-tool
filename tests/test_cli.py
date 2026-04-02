# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""CLI smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from onap_release_map.cli import app

runner = CliRunner()


def _write_manifest(path: Path, name: str = "TestRelease") -> None:
    """Write a minimal valid manifest JSON file."""
    manifest = {
        "schema_version": "1.0.0",
        "tool_version": "0.1.0",
        "generated_at": "2025-01-01T00:00:00Z",
        "onap_release": {
            "name": name,
            "oom_chart_version": "18.0.0",
        },
        "summary": {
            "total_repositories": 1,
            "total_docker_images": 1,
            "total_helm_components": 1,
            "repositories_by_category": {"runtime": 1},
            "repositories_by_confidence": {"high": 1},
            "collectors_used": ["oom"],
        },
        "repositories": [
            {
                "gerrit_project": "policy/api",
                "top_level_project": "policy",
                "confidence": "high",
                "category": "runtime",
                "discovered_by": ["oom"],
            }
        ],
        "docker_images": [
            {
                "image": "onap/policy-api",
                "tag": "4.2.2",
            }
        ],
        "helm_components": [
            {
                "name": "policy",
                "version": "18.0.0",
                "enabled_by_default": True,
            }
        ],
        "provenance": {
            "data_sources": [],
            "collectors_executed": [],
        },
    }
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


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

    def test_discover_relman_without_oom_path(self, tmp_path: Path) -> None:
        """Test that relman collector runs without --oom-path."""
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
                "relman",
                "--repos-yaml",
                str(repos_yaml),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Collectors: relman" in result.output
        assert (output_dir / "manifest.json").exists()

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


class TestDiff:
    """Test diff subcommand."""

    def test_diff_two_manifests(self, tmp_path: Path) -> None:
        """Test diff between two manifests with different releases."""
        manifest_a = tmp_path / "a.json"
        manifest_b = tmp_path / "b.json"
        _write_manifest(manifest_a, "ReleaseA")
        _write_manifest(manifest_b, "ReleaseB")
        result = runner.invoke(app, ["diff", str(manifest_a), str(manifest_b)])
        assert result.exit_code == 0
        assert "ReleaseA" in result.output
        assert "ReleaseB" in result.output

    def test_diff_json_format(self, tmp_path: Path) -> None:
        """Test diff with JSON output format."""
        manifest_a = tmp_path / "a.json"
        manifest_b = tmp_path / "b.json"
        _write_manifest(manifest_a)
        _write_manifest(manifest_b)
        result = runner.invoke(
            app,
            ["diff", str(manifest_a), str(manifest_b), "--output-format", "json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "baseline_release" in data

    def test_diff_markdown_format(self, tmp_path: Path) -> None:
        """Test diff with Markdown output format."""
        manifest_a = tmp_path / "a.json"
        manifest_b = tmp_path / "b.json"
        _write_manifest(manifest_a)
        _write_manifest(manifest_b)
        result = runner.invoke(
            app,
            ["diff", str(manifest_a), str(manifest_b), "--output-format", "md"],
        )
        assert result.exit_code == 0
        assert "# Manifest Diff" in result.output

    def test_diff_to_file(self, tmp_path: Path) -> None:
        """Test diff with --output flag writes to file."""
        manifest_a = tmp_path / "a.json"
        manifest_b = tmp_path / "b.json"
        output_file = tmp_path / "diff.txt"
        _write_manifest(manifest_a)
        _write_manifest(manifest_b)
        result = runner.invoke(
            app,
            [
                "diff",
                str(manifest_a),
                str(manifest_b),
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_diff_invalid_format(self, tmp_path: Path) -> None:
        """Test diff rejects invalid output format."""
        manifest_a = tmp_path / "a.json"
        manifest_b = tmp_path / "b.json"
        _write_manifest(manifest_a)
        _write_manifest(manifest_b)
        result = runner.invoke(
            app,
            [
                "diff",
                str(manifest_a),
                str(manifest_b),
                "--output-format",
                "invalid",
            ],
        )
        assert result.exit_code != 0

    def test_diff_nonexistent_file(self) -> None:
        """Test diff with nonexistent manifest file."""
        result = runner.invoke(
            app, ["diff", "/nonexistent/a.json", "/nonexistent/b.json"]
        )
        assert result.exit_code != 0


class TestExport:
    """Test export subcommand."""

    def test_export_yaml(self, tmp_path: Path) -> None:
        """Test export to YAML format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(app, ["export", str(manifest_file), "--format", "yaml"])
        assert result.exit_code == 0
        assert "schema_version" in result.output

    def test_export_csv_repos(self, tmp_path: Path) -> None:
        """Test export to CSV repos format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(app, ["export", str(manifest_file), "--format", "csv"])
        assert result.exit_code == 0
        assert "gerrit_project" in result.output

    def test_export_csv_images(self, tmp_path: Path) -> None:
        """Test export to CSV images format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(
            app,
            ["export", str(manifest_file), "--format", "csv", "--images-only"],
        )
        assert result.exit_code == 0
        assert "image" in result.output

    def test_export_markdown(self, tmp_path: Path) -> None:
        """Test export to Markdown format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(app, ["export", str(manifest_file), "--format", "md"])
        assert result.exit_code == 0
        assert "# ONAP Release Manifest" in result.output

    def test_export_gerrit_list(self, tmp_path: Path) -> None:
        """Test export to gerrit-list format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(
            app, ["export", str(manifest_file), "--format", "gerrit-list"]
        )
        assert result.exit_code == 0
        assert "policy/api" in result.output

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test export with --output flag writes to file."""
        manifest_file = tmp_path / "manifest.json"
        output_file = tmp_path / "output.yaml"
        _write_manifest(manifest_file)
        result = runner.invoke(
            app,
            [
                "export",
                str(manifest_file),
                "--format",
                "yaml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_invalid_format(self, tmp_path: Path) -> None:
        """Test export rejects invalid format."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(
            app, ["export", str(manifest_file), "--format", "invalid"]
        )
        assert result.exit_code != 0

    def test_export_nonexistent_file(self) -> None:
        """Test export with nonexistent manifest file."""
        result = runner.invoke(app, ["export", "/nonexistent/manifest.json"])
        assert result.exit_code != 0


class TestVerify:
    """Test verify subcommand."""

    def test_verify_no_check(self, tmp_path: Path) -> None:
        """Test verify with --no-check-images exits cleanly."""
        manifest_file = tmp_path / "manifest.json"
        _write_manifest(manifest_file)
        result = runner.invoke(
            app,
            ["verify", str(manifest_file), "--no-check-images"],
        )
        assert result.exit_code == 0

    def test_verify_nonexistent_file(self) -> None:
        """Test verify with nonexistent manifest file."""
        result = runner.invoke(app, ["verify", "/nonexistent/manifest.json"])
        assert result.exit_code != 0

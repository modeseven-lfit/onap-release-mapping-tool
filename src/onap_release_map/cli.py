# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""CLI interface for onap-release-map."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from onap_release_map import __version__
from onap_release_map.collectors import registry
from onap_release_map.collectors.oom import OOMCollector  # noqa: F401 - registers
from onap_release_map.config import load_config
from onap_release_map.manifest import ManifestBuilder
from onap_release_map.models import DataSource, OnapRelease

if TYPE_CHECKING:
    from onap_release_map.models import ReleaseManifest

app = typer.Typer(
    name="onap-release-map",
    help="ONAP release component mapping tool.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)


def _setup_logging(verbosity: int) -> None:
    """Configure logging based on verbosity level."""
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=err_console, rich_tracebacks=True)],
    )


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"onap-release-map {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """ONAP release component mapping tool."""


@app.command()
def discover(
    oom_path: Annotated[
        Path,
        typer.Option(
            "--oom-path",
            help="Path to local OOM repository clone.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ],
    mapping_file: Annotated[
        Path | None,
        typer.Option(
            "--mapping-file",
            help="Custom image-to-repo mapping YAML override.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="Path to YAML configuration file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            help="Output directory for manifest files.",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path("./output"),
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="Output formats: json, yaml, all.",
        ),
    ] = "json",
    release_name: Annotated[
        str,
        typer.Option(
            "--release-name",
            help="ONAP release code name.",
        ),
    ] = "Rabat",
    deterministic: Annotated[
        bool,
        typer.Option(
            "--deterministic/--no-deterministic",
            help="Produce deterministic output.",
        ),
    ] = True,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (up to -vvv).",
        ),
    ] = 0,
) -> None:
    """Parse OOM charts and generate the release manifest."""
    _setup_logging(verbose)
    _config = load_config(config_file)  # loaded; CLI flags override

    # Validate output format early
    _valid_formats = {"json", "yaml", "all"}
    if output_format not in _valid_formats:
        err_console.print(
            f"[red]Error:[/] unsupported format "
            f"[bold]{output_format}[/]. "
            f"Choose from: {', '.join(sorted(_valid_formats))}"
        )
        raise typer.Exit(code=1)

    console.print(
        f"[bold blue]onap-release-map[/] v{__version__}",
    )
    console.print(
        f"Analyzing OOM charts at: [green]{oom_path}[/]",
    )

    # Detect OOM chart version from Chart.yaml
    chart_version = _detect_chart_version(oom_path)

    onap_release = OnapRelease(
        name=release_name,
        oom_chart_version=chart_version or "unknown",
        oom_branch=_detect_git_branch(oom_path),
        oom_commit=_detect_git_commit(oom_path),
    )

    builder = ManifestBuilder(
        tool_version=__version__,
        onap_release=onap_release,
        deterministic=deterministic,
    )

    # Run OOM collector
    oom_collector = registry.create(
        "oom",
        oom_path=oom_path,
        mapping_file=mapping_file,
    )
    if oom_collector is None:
        err_console.print("[red]Error:[/] OOM collector not available")
        raise typer.Exit(code=1)

    with console.status("[bold green]Parsing OOM Helm charts..."):
        result = oom_collector.timed_collect()

    # Fail fast if the collector reported execution errors
    if result.execution and result.execution.errors:
        err_console.print(
            "[red]Error:[/] OOM collection failed with the "
            "following error(s):"
        )
        for err in result.execution.errors:
            err_console.print(f"  - {err}")
        raise typer.Exit(code=1)

    builder.add_result(result)
    builder.add_data_source(
        DataSource(
            name="oom",
            type="git",
            url=str(oom_path),
            commit=onap_release.oom_commit,
        )
    )

    manifest = builder.build()

    # Display summary
    _print_summary(manifest)

    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format in ("json", "all"):
        json_path = output_dir / "manifest.json"
        json_path.write_text(
            ManifestBuilder.to_json(manifest) + "\n",
            encoding="utf-8",
        )
        console.print(f"  JSON: [green]{json_path}[/]")

    if output_format in ("yaml", "all"):
        try:
            import yaml

            yaml_path = output_dir / "manifest.yaml"
            data = manifest.model_dump(mode="json")
            yaml_path.write_text(
                yaml.dump(
                    data,
                    default_flow_style=False,
                    sort_keys=True,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            console.print(f"  YAML: [green]{yaml_path}[/]")
        except ImportError:
            err_console.print("[yellow]Warning:[/] PyYAML needed for YAML output")

    console.print("\n[bold green]Done![/]")


@app.command()
def schema() -> None:
    """Print the JSON Schema for the manifest format."""
    from importlib import resources

    schema_path = (
        resources.files("onap_release_map")
        .joinpath("schemas")
        .joinpath("manifest-v1.schema.json")
    )
    schema_text = schema_path.read_text(encoding="utf-8")
    print(schema_text, end="")


@app.command()
def version() -> None:
    """Print version information."""
    console.print(f"onap-release-map {__version__}")
    console.print(f"Python {sys.version}")


def _print_summary(manifest: ReleaseManifest) -> None:
    """Print a Rich summary table of the manifest."""
    console.print()
    console.print(
        f"[bold]Release:[/] {manifest.onap_release.name} "
        f"(OOM chart v{manifest.onap_release.oom_chart_version})"
    )
    console.print()

    table = Table(title="Manifest Summary", show_lines=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Repositories", str(manifest.summary.total_repositories))
    table.add_row("Docker Images", str(manifest.summary.total_docker_images))
    table.add_row("Helm Components", str(manifest.summary.total_helm_components))

    for cat, count in sorted(manifest.summary.repositories_by_category.items()):
        table.add_row(f"  Category: {cat}", str(count))

    for conf, count in sorted(manifest.summary.repositories_by_confidence.items()):
        table.add_row(f"  Confidence: {conf}", str(count))

    console.print(table)
    console.print()
    console.print("[bold]Output files:[/]")


def _detect_chart_version(oom_path: Path) -> str | None:
    """Detect OOM umbrella chart version from Chart.yaml."""
    chart_path = oom_path / "kubernetes" / "onap" / "Chart.yaml"
    if not chart_path.exists():
        return None
    try:
        import yaml

        with open(chart_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("version") if isinstance(data, dict) else None
    except Exception:
        return None


def _detect_git_branch(repo_path: Path) -> str | None:
    """Detect current git branch of a repository."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _detect_git_commit(repo_path: Path) -> str | None:
    """Detect current git commit SHA of a repository."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

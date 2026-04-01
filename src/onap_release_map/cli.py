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
from onap_release_map.collectors.gerrit import GerritCollector  # noqa: F401
from onap_release_map.collectors.jjb import JJBCollector  # noqa: F401
from onap_release_map.collectors.oom import OOMCollector  # noqa: F401
from onap_release_map.collectors.relman import RelmanCollector  # noqa: F401
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
        Path | None,
        typer.Option(
            "--oom-path",
            help="Path to local OOM repository clone.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
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
    collectors_opt: Annotated[
        str,
        typer.Option(
            "--collectors",
            help=(
                "Comma-separated list of collectors to run. "
                "Available: oom,relman,jjb,gerrit. "
                "Default: oom."
            ),
        ),
    ] = "oom",
    repos_yaml: Annotated[
        Path | None,
        typer.Option(
            "--repos-yaml",
            help="Path to relman repos.yaml file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    jjb_path: Annotated[
        Path | None,
        typer.Option(
            "--jjb-path",
            help="Path to ci-management jjb/ directory.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
    gerrit_url: Annotated[
        str | None,
        typer.Option(
            "--gerrit-url",
            help="Gerrit REST API base URL.",
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
    config = load_config(config_file)

    # Validate output format early
    _valid_formats = {"json", "yaml", "all"}
    if output_format not in _valid_formats:
        err_console.print(
            f"[red]Error:[/] unsupported format "
            f"[bold]{output_format}[/]. "
            f"Choose from: {', '.join(sorted(_valid_formats))}"
        )
        raise typer.Exit(code=1)

    # Parse collector list — deduplicate preserving first-seen order
    raw_collectors = [c.strip() for c in collectors_opt.split(",") if c.strip()]
    seen: set[str] = set()
    enabled: list[str] = []
    for name in raw_collectors:
        if name not in seen:
            enabled.append(name)
            seen.add(name)

    if not enabled:
        err_console.print(
            "[red]Error:[/] no collectors specified. "
            "Use --collectors with a comma-separated list of collectors."
        )
        raise typer.Exit(code=1)

    available = registry.list_names()
    for name in enabled:
        if name not in available:
            err_console.print(
                f"[red]Error:[/] unknown collector "
                f"[bold]{name}[/]. "
                f"Available: {', '.join(available)}"
            )
            raise typer.Exit(code=1)

    # Validate that required paths are provided for enabled collectors
    if "oom" in enabled and oom_path is None:
        err_console.print(
            "[red]Error:[/] --oom-path is required when the oom collector is enabled"
        )
        raise typer.Exit(code=1)
    if "relman" in enabled and repos_yaml is None:
        err_console.print(
            "[red]Error:[/] --repos-yaml is required "
            "when the relman collector is enabled"
        )
        raise typer.Exit(code=1)
    if "jjb" in enabled and jjb_path is None:
        err_console.print(
            "[red]Error:[/] --jjb-path is required when the jjb collector is enabled"
        )
        raise typer.Exit(code=1)

    console.print(
        f"[bold blue]onap-release-map[/] v{__version__}",
    )
    if oom_path is not None:
        console.print(
            f"Analyzing OOM charts at: [green]{oom_path}[/]",
        )
    console.print(
        f"Collectors: [cyan]{', '.join(enabled)}[/]",
    )

    # Detect OOM chart version from Chart.yaml
    chart_version = _detect_chart_version(oom_path) if oom_path else None

    onap_release = OnapRelease(
        name=release_name,
        oom_chart_version=chart_version or "unknown",
        oom_branch=_detect_git_branch(oom_path) if oom_path else None,
        oom_commit=_detect_git_commit(oom_path) if oom_path else None,
    )

    builder = ManifestBuilder(
        tool_version=__version__,
        onap_release=onap_release,
        deterministic=deterministic,
    )

    # ----------------------------------------------------------
    # Run each enabled collector
    # ----------------------------------------------------------
    _gerrit_raw = config.get("gerrit", {})
    gerrit_cfg = _gerrit_raw if isinstance(_gerrit_raw, dict) else {}

    collector_configs: dict[str, dict[str, object]] = {
        "oom": {
            "oom_path": oom_path,
            "mapping_file": mapping_file,
        },
        "relman": {
            "repos_yaml_path": repos_yaml,
            "gerrit_url": gerrit_url or gerrit_cfg.get("url"),
        },
        "jjb": {
            "jjb_path": jjb_path,
            "gerrit_url": gerrit_url or gerrit_cfg.get("url"),
        },
        "gerrit": {
            "gerrit_url": gerrit_url or gerrit_cfg.get("url"),
            "timeout": gerrit_cfg.get("timeout", 30),
            "max_retries": gerrit_cfg.get("max_retries", 3),
        },
    }

    for collector_name in enabled:
        kwargs = collector_configs.get(collector_name, {})
        collector = registry.create(collector_name, **kwargs)
        if collector is None:
            err_console.print(
                f"[red]Error:[/] {collector_name} collector not available"
            )
            raise typer.Exit(code=1)

        status_msg = _collector_status_message(collector_name)
        with console.status(f"[bold green]{status_msg}"):
            result = collector.timed_collect()

        # Report errors but only abort for the primary collector
        if result.execution and result.execution.errors:
            for err in result.execution.errors:
                err_console.print(f"  [yellow]Warning ({collector_name}):[/] {err}")
            if collector_name == "oom":
                err_console.print("[red]Error:[/] OOM collection failed")
                raise typer.Exit(code=1)
            err_console.print(f"  [yellow]Continuing without {collector_name} data[/]")
        else:
            _items = 0
            if result.execution:
                _items = result.execution.items_collected
            console.print(f"  [green]{collector_name}:[/] {_items} items collected")

        builder.add_result(result)

        # Record data source provenance
        source = _make_data_source(
            collector_name,
            oom_path=oom_path,
            oom_commit=onap_release.oom_commit,
            repos_yaml=repos_yaml,
            jjb_path=jjb_path,
            gerrit_url=gerrit_url or gerrit_cfg.get("url"),
        )
        if source:
            builder.add_data_source(source)

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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _collector_status_message(name: str) -> str:
    """Return a human-readable status message for a collector."""
    messages = {
        "oom": "Parsing OOM Helm charts...",
        "relman": "Loading relman repository data...",
        "jjb": "Scanning JJB CI definitions...",
        "gerrit": "Querying Gerrit REST API...",
    }
    return messages.get(name, f"Running {name} collector...")


def _make_data_source(
    collector_name: str,
    *,
    oom_path: Path | None = None,
    oom_commit: str | None = None,
    repos_yaml: Path | None = None,
    jjb_path: Path | None = None,
    gerrit_url: object = None,
) -> DataSource | None:
    """Build a provenance DataSource for a collector."""
    if collector_name == "oom" and oom_path:
        return DataSource(
            name="oom",
            type="git",
            url=str(oom_path),
            commit=oom_commit,
        )
    if collector_name == "relman" and repos_yaml:
        return DataSource(
            name="relman",
            type="file",
            url=str(repos_yaml),
        )
    if collector_name == "jjb" and jjb_path:
        return DataSource(
            name="jjb",
            type="file",
            url=str(jjb_path),
        )
    if collector_name == "gerrit":
        url = str(gerrit_url) if gerrit_url else "https://gerrit.onap.org/r"
        return DataSource(
            name="gerrit",
            type="api",
            url=url,
        )
    return None


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

    table.add_row(
        "Repositories",
        str(manifest.summary.total_repositories),
    )
    table.add_row(
        "Docker Images",
        str(manifest.summary.total_docker_images),
    )
    table.add_row(
        "Helm Components",
        str(manifest.summary.total_helm_components),
    )

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

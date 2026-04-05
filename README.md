<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# ONAP Release Mapping Tool

[![Build](https://github.com/modeseven-lfit/onap-release-mapping-tool/actions/workflows/build-test.yaml/badge.svg)](https://github.com/modeseven-lfit/onap-release-mapping-tool/actions/workflows/build-test.yaml)
[![PyPI](https://img.shields.io/pypi/v/onap-release-map)](https://pypi.org/project/onap-release-map/)
[![Python](https://img.shields.io/pypi/pyversions/onap-release-map)](https://pypi.org/project/onap-release-map/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

ONAP release component mapping tool — generates definitive manifests of
Gerrit projects and Docker images comprising an ONAP release.

## Results / GitHub Pages

[https://modeseven-lfit.github.io/onap-release-mapping-tool/](https://modeseven-lfit.github.io/onap-release-mapping-tool/)

## Overview

`onap-release-map` follows an **OOM-first** strategy: it starts from the
OOM Helm umbrella chart, recursively resolves every sub-chart and Docker
image reference, then maps those images back to their source Gerrit
repositories. Further collectors enrich the manifest with data from
the ONAP release management repository, JJB CI definitions, and the
Gerrit REST API.

The tool produces a **versioned, self-describing JSON artifact** that
captures the complete state of the analysis, including:

- Every Gerrit repository participating in the release
- Every Docker image and tag referenced by OOM Helm charts
- Image-to-repository mappings with provenance metadata
- Release management status for each project
- CI/CD pipeline correlation from JJB definitions
- Data source provenance and execution statistics

## Features

- **OOM Helm chart parsing** — recursively walks the OOM umbrella chart
  to extract all Docker image references and sub-chart dependencies
- **Gerrit project discovery** — maps Docker images back to their source
  Gerrit repositories via configurable mapping rules and API queries
- **JJB CI correlation** — scans Jenkins Job Builder definitions to link
  repositories with their CI pipeline configurations
- **Release management status** — ingests the relman `repos.yaml` to
  track per-project release participation and lifecycle state
- **Nexus Docker registry validation** — verifies that every image:tag
  pair in the manifest actually exists in the ONAP Nexus3 registry
- **Manifest diffing** — compares two manifests to identify added,
  removed, and changed repositories or images across releases
- **Repository filtering** — excludes infrastructure repos (e.g.
  `All-Projects`, `All-Users`, `.github`) and read-only/archived
  projects from reports by default, with full CLI override support
- **Multi-format export** — converts manifests to YAML, CSV, Markdown,
  or a flat Gerrit repository list
- **JSON Schema validation** — every manifest conforms to a versioned
  JSON Schema, enabling downstream tooling to verify artifacts
- **GitHub Action** — composite action for CI/CD integration that clones
  OOM, runs discovery, and uploads the manifest as a build artifact

## Installation

Install from PyPI:

```/dev/null/shell.sh#L1
pip install onap-release-map
```

Install from source using [uv](https://docs.astral.sh/uv/):

```/dev/null/shell.sh#L1-3
git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
cd onap-release-mapping-tool
uv sync
```

Development setup with all extras:

```/dev/null/shell.sh#L1
uv sync --group dev
```

## Quick Start

```/dev/null/shell.sh#L1-5
# Clone the OOM repository
git clone --depth 1 https://gerrit.onap.org/r/oom

# Generate the release manifest
onap-release-map discover --oom-path ./oom
```

The tool writes the manifest to `./output/manifest.json` by default.

## Commands

### discover

The primary command. Parses OOM Helm charts and runs selected collectors
to build the release manifest.

```/dev/null/shell.sh#L1-2
# Basic discovery with OOM charts
onap-release-map discover --oom-path ./oom
```

```/dev/null/shell.sh#L1-6
# Full discovery with all collectors
onap-release-map discover \
  --oom-path ./oom \
  --collectors oom,gerrit,relman,jjb \
  --repos-yaml ./releases/repos.yaml \
  --jjb-path ./ci-management/jjb
```

```/dev/null/shell.sh#L1-5
# Custom output location and format
onap-release-map discover \
  --oom-path ./oom \
  --output-dir ./results \
  --output-format all
```

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable MD060 -->

| Option                                       | Default      | Description                                                           |
| -------------------------------------------- | ------------ | --------------------------------------------------------------------- |
| `--oom-path PATH`                            | *(required)* | Path to a local OOM repository clone                                  |
| `--collectors LIST`                          | `oom`        | Comma-separated collectors: `oom`, `gerrit`, `relman`, `jjb`          |
| `--release-name NAME`                        | `Rabat`      | ONAP release code name                                                |
| `--output-dir DIR`                           | `./output`   | Output directory for manifest files                                   |
| `--output-format FMT`                        | `json`       | Output format: `json`, `yaml`, `all`                                  |
| `--repos-yaml PATH`                          | —            | Path to relman `repos.yaml` (required for `relman` collector)         |
| `--jjb-path PATH`                            | —            | Path to `ci-management/jjb/` directory (required for `jjb` collector) |
| `--gerrit-url URL`                           | config       | Gerrit REST API base URL                                              |
| `--filter-repos LIST`                        | config       | Comma-separated Gerrit project names to exclude from reports          |
| `--exclude-readonly / --no-exclude-readonly` | `true`       | Exclude read-only/archived Gerrit projects from reports               |
| `--mapping-file PATH`                        | —            | Custom image-to-repo mapping YAML override                            |
| `--config PATH`                              | —            | Path to YAML configuration file                                       |
| `--deterministic`                            | `true`       | Produce deterministic output (sorted keys, stable ordering)           |
| `-v / -vv / -vvv`                            | —            | Increase verbosity                                                    |

<!-- markdownlint-enable MD060 -->
<!-- markdownlint-enable MD013 -->

### diff

Compare two manifests and report differences. Useful for tracking
changes between releases or between successive builds.

```/dev/null/shell.sh#L1-2
# Text diff to stdout
onap-release-map diff manifest-old.json manifest-new.json
```

```/dev/null/shell.sh#L1-5
# Markdown diff written to file
onap-release-map diff \
  manifest-old.json manifest-new.json \
  --output-format md \
  --output changes.md
```

<!-- markdownlint-disable MD013 -->

| Option                | Default      | Description                            |
| --------------------- | ------------ | -------------------------------------- |
| `MANIFEST_A`          | *(required)* | Path to the baseline manifest (JSON)   |
| `MANIFEST_B`          | *(required)* | Path to the comparison manifest (JSON) |
| `--output-format FMT` | `text`       | Output format: `text`, `json`, `md`    |
| `--output PATH`       | —            | Write diff to file instead of stdout   |
| `--ignore-timestamps` | `false`      | Ignore `generated_at` when comparing   |

<!-- markdownlint-enable MD013 -->

### export

Convert a JSON manifest to other formats for consumption by downstream
tools and reports.

```/dev/null/shell.sh#L1-2
# Export to YAML
onap-release-map export manifest.json --format yaml --output manifest.yaml
```

```/dev/null/shell.sh#L1-2
# Export a flat list of Gerrit repository names
onap-release-map export manifest.json --format gerrit-list
```

```/dev/null/shell.sh#L1-2
# Export Docker images as CSV (use --images flag)
onap-release-map export manifest.json --format csv --output images.csv
```

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable MD060 -->

| Option                                       | Default      | Description                                               |
| -------------------------------------------- | ------------ | --------------------------------------------------------- |
| `MANIFEST_PATH`                              | *(required)* | Path to manifest JSON file                                |
| `--format FMT`                               | `yaml`       | Output format: `yaml`, `csv`, `md`, `html`, `gerrit-list` |
| `--output PATH`                              | —            | Write to file instead of stdout                           |
| `--repos-only` / `--images-only`             | `false`      | Limit CSV scope to repos or images (mutually exclusive)   |
| `--filter-repos LIST`                        | —            | Comma-separated Gerrit project names to exclude           |
| `--exclude-readonly / --no-exclude-readonly` | `true`       | Exclude read-only/archived Gerrit projects                |

<!-- markdownlint-enable MD060 -->
<!-- markdownlint-enable MD013 -->

### verify

Check that every Docker image:tag pair in a manifest exists in the
ONAP Nexus3 Docker registry. Returns a non-zero exit code if any images
are missing.

```/dev/null/shell.sh#L1-2
# Verify all images against the default Nexus registry
onap-release-map verify manifest.json
```

```/dev/null/shell.sh#L1-5
# Use a custom registry with more workers
onap-release-map verify manifest.json \
  --nexus-url https://nexus3.example.org \
  --workers 8
```

<!-- markdownlint-disable MD013 -->

| Option                               | Default                         | Description                                   |
| ------------------------------------ | ------------------------------- | --------------------------------------------- |
| `MANIFEST_PATH`                      | *(required)*                    | Path to manifest JSON file                    |
| `--nexus-url URL`                    | `https://nexus3.onap.org:10001` | Nexus3 registry URL                           |
| `--check-images / --no-check-images` | `true`                          | Verify Docker image:tag existence             |
| `--workers N`                        | `4`                             | Number of concurrent validation threads       |
| `--update / --no-update`             | `true`                          | Write validation results back to the manifest |

<!-- markdownlint-enable MD013 -->

### schema

Print the JSON Schema that all manifests conform to. Useful for
integrating with validation tools or generating documentation.

```/dev/null/shell.sh#L1-2
# Print schema to stdout
onap-release-map schema
```

```/dev/null/shell.sh#L1-2
# Save schema to a file
onap-release-map schema > manifest-v1.schema.json
```

### version

Print version information for the tool and the Python runtime.

```/dev/null/shell.sh#L1
onap-release-map version
```

## Configuration

The tool ships with a default configuration at
`configuration/default.yaml`. You can override it with the `--config`
flag on the `discover` command.

Key configuration sections:

```/dev/null/example.yaml#L1-32
# ONAP Gerrit server
gerrit:
  url: "https://gerrit.onap.org/r"
  timeout: 30
  max_retries: 3

# OOM repository defaults
oom:
  default_branch: "master"
  exclude_dirs:
    - "argo"
    - "archive"

# Repository filtering — repos excluded from reports
filter_repos:
  - ".github"
  - "All-Projects"
  - "All-Users"
  # JJB CI job definitions for the ONAP Jenkins instance, not runtime
  # release content
  - "ci-management"

# Exclude read-only/archived Gerrit projects from reports
exclude_readonly: true

# Nexus registry for validation
nexus:
  url: "https://nexus3.onap.org"
  timeout: 10
  max_retries: 3
  concurrent_workers: 4
```

The `filter_repos` list and `exclude_readonly` flag control which
repositories appear in exported reports. Infrastructure repositories
(`.github`, `All-Projects`, `All-Users`) and CI-only repositories
(`ci-management`, which contains JJB CI job definitions for the ONAP
Jenkins instance) do not appear by default, nor do read-only/archived
Gerrit projects. Override either setting via CLI flags
(`--filter-repos`, `--no-exclude-readonly`) or a custom config file.

## GitHub Action

The tool is available as a composite GitHub Action for CI/CD pipelines.
It automatically clones OOM (or uses a pre-cloned checkout), runs
discovery, and uploads the manifest as an artifact.

```/dev/null/workflow.yaml#L1-21
name: Generate ONAP Release Manifest
on:
  workflow_dispatch:

jobs:
  manifest:
    runs-on: ubuntu-latest
    steps:
      - name: Generate manifest
        uses: modeseven-lfit/onap-release-mapping-tool@main
        id: release-map
        with:
          oom-branch: "master"
          release-name: "Rabat"
          collectors: "oom,gerrit"
          output-format: "all"

      - name: Show results
        run: |
          echo "Repositories: ${{ steps.release-map.outputs.total-repositories }}"
          echo "Images: ${{ steps.release-map.outputs.total-images }}"
```

<!-- markdownlint-disable MD013 -->

| Input              | Default                     | Description                                             |
| ------------------ | --------------------------- | ------------------------------------------------------- |
| `oom-path`         | *(empty — triggers clone)*  | Path to pre-cloned OOM repo                             |
| `oom-branch`       | `master`                    | OOM branch to analyze                                   |
| `gerrit-url`       | `https://gerrit.onap.org/r` | Gerrit base URL                                         |
| `collectors`       | `oom,gerrit`                | Comma-separated collector list                          |
| `output-dir`       | `$RUNNER_TEMP`              | Output directory                                        |
| `output-format`    | `json`                      | Output format: `json`, `yaml`, `all`                    |
| `release-name`     | `Rabat`                     | ONAP release code name                                  |
| `mapping-file`     | —                           | Custom image-to-repo mapping YAML override              |
| `filter-repos`     | —                           | Comma-separated Gerrit projects to exclude              |
| `exclude-readonly` | `true`                      | Exclude read-only/archived Gerrit projects              |
| `python-version`   | `3.12`                      | Python version to use                                   |
| `version`          | `latest`                    | Tool version (e.g. `0.1.0` or `latest`)                 |

| Output               | Description                              |
| -------------------- | ---------------------------------------- |
| `manifest-path`      | Path to the generated JSON manifest      |
| `manifest-version`   | Schema version of the generated manifest |
| `total-repositories` | Number of repositories found             |
| `total-images`       | Number of Docker images found            |
| `onap-release`       | ONAP release name                        |

<!-- markdownlint-enable MD013 -->

## Output Formats

<!-- markdownlint-disable MD013 -->

| Format      | Command                         | Description                                                            |
| ----------- | ------------------------------- | ---------------------------------------------------------------------- |
| JSON        | `discover --output-format json` | Primary manifest format with full metadata and schema validation       |
| YAML        | `discover --output-format yaml` | Human-readable counterpart of the JSON manifest                        |
| CSV         | `export --format csv`           | Tabular data suitable for spreadsheets (filterable by repos or images) |
| Markdown    | `export --format md`            | Formatted tables for embedding in reports or wikis                     |
| HTML        | `export --format html`          | Dark-themed interactive report with search, sort, and emoji indicators |
| Gerrit list | `export --format gerrit-list`   | Flat newline-delimited list of Gerrit project names                    |

<!-- markdownlint-enable MD013 -->

## HTML Report Features

The HTML export (`export --format html`) produces a single dark-themed
HTML report hosted on
[GitHub Pages](https://modeseven-lfit.github.io/onap-release-mapping-tool/).
CDN-hosted [Simple-DataTables](https://github.com/fiduswriter/Simple-DataTables)
assets supply interactive table behaviour and styling, so the report
requires network access for full functionality.

### Interactive Tables

Report tables include search/filter and column sorting powered by
[Simple-DataTables](https://github.com/fiduswriter/Simple-DataTables):

- **Search/filter** — a search box above each table for real-time
  filtering
- **Column sorting** — click any column header to sort
  ascending/descending

Tables with fewer than three rows skip interactivity, as search and
sort add no value to small tables.

### State Indicators

<!-- markdownlint-disable MD013 -->

The Repositories table uses emoji in the **State** column to convey
release scope at a glance:

<!-- markdownlint-disable MD060 -->

| Emoji | Meaning                                                    |
| ----- | ---------------------------------------------------------- |
| 📦    | `READ_ONLY` — archived project                              |
| ✅    | `ACTIVE` — project content is in the current ONAP release  |
| ☑️    | `ACTIVE` — parent project with children in current release |
| ❌    | `ACTIVE` — project is NOT in the current ONAP release      |
| ❓    | Undetermined — tool could not resolve release scope        |

<!-- markdownlint-enable MD060 -->

<!-- markdownlint-enable MD013 -->

### Totals Summary

The Markdown and HTML reports include a **Totals** subsection directly
below the Repositories table. This table provides a numerical count of
repositories in each state category alongside the emoji key:

<!-- markdownlint-disable MD013 -->

| Total | State | Description                            |
| ----: | :---: | -------------------------------------- |
|    90 | ✅    | In current ONAP release                |
|    11 | ☑️    | Parent project (children in release)   |
|     5 | ❌    | Not in current ONAP release            |
|     3 | ❓    | Undetermined                           |
|    20 | 📦    | Read-only / archived                   |

<!-- markdownlint-enable MD013 -->

The table omits rows with a zero count automatically. When repository
filtering is active (e.g. `--exclude-readonly`), the totals reflect the
filtered set.

The tool resolves state by cross-referencing four data sources:

1. **OOM discovery** — repos found in OOM Helm charts are definitively
   in the release (✅)
2. **Relman `included_in`** — the release management `repos.yaml`
   tracks which releases each project participates in
3. **READ_ONLY status** — archived projects are definitively not in
   the release (📦)
4. **Parent project detection** — Gerrit parent projects whose children
   ship in the release receive the parent indicator (☑️)

## Development

Install development dependencies:

```/dev/null/shell.sh#L1
uv sync --group dev
```

Run the test suite:

```/dev/null/shell.sh#L1
uv run pytest tests/
```

Run linting and formatting checks:

```/dev/null/shell.sh#L1-2
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Run type checking:

```/dev/null/shell.sh#L1
uv run mypy src/
```

This repository uses [pre-commit](https://pre-commit.com/) hooks to
enforce code quality on every commit. Install them with:

```/dev/null/shell.sh#L1
pre-commit install
```

The hooks run gitlint, ruff, mypy, reuse (SPDX license compliance),
yamllint, actionlint, and interrogate (docstring coverage).

## Documentation

Full documentation is available on
[Read the Docs](https://onap-release-mapping-tool.readthedocs.io/).

## License

This project uses the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
See the [LICENSE](LICENSE) file for details.

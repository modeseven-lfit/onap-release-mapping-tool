<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- SPDX-FileCopyrightText: 2026 The Linux Foundation -->

# ONAP Release Mapping Tool — Development Plan

## 1. Executive Summary

This document describes the technical design, architecture, and implementation
plan for `onap-release-map`, a Python CLI tool and GitHub Action that produces
a definitive, machine-readable manifest of every Gerrit project and Docker
image that comprises a given ONAP release.

The tool follows an **OOM-first** strategy: it starts from the OOM Helm
umbrella chart (`oom/kubernetes/onap/Chart.yaml`), recursively resolves every
sub-chart and Docker image reference, then maps those images back to their
source Gerrit repositories. The architecture is **modular and extensible** so
that additional data sources (Gerrit REST API, `relman/repos.yaml`,
ci-management JJB definitions, integration manifests) can be blended in over
time to improve accuracy and coverage.

Every invocation produces a **versioned, self-describing JSON artifact** that
captures the complete state of the analysis. Artifacts are stored in a
companion repository
([`onap-release-mapping-artifacts`][artifacts-repo]) for
longitudinal comparison across tool versions, ONAP releases, and calendar
dates.

### Repositories

<!-- markdownlint-disable MD013 -->

| Repository                                                        | Purpose                                          |
| ----------------------------------------------------------------- | ------------------------------------------------ |
| [`modeseven-lfit/onap-release-mapping-tool`][tool-repo]           | CLI tool, GitHub Action wrapper, CI/CD workflows |
| [`modeseven-lfit/onap-release-mapping-artifacts`][artifacts-repo] | Date-stamped artifact archive, GitHub Pages site |

<!-- markdownlint-enable MD013 -->

[tool-repo]: https://github.com/modeseven-lfit/onap-release-mapping-tool
[artifacts-repo]: https://github.com/modeseven-lfit/onap-release-mapping-artifacts

---

## 2. Goals and Requirements

### 2.1 Functional Requirements

<!-- markdownlint-disable MD013 -->

| ID    | Requirement                                                                                              |
| ----- | -------------------------------------------------------------------------------------------------------- |
| FR-01 | Parse the OOM umbrella Helm chart and all sub-charts recursively                                         |
| FR-02 | Extract every `onap/*` Docker image reference with its pinned tag                                        |
| FR-03 | Map Docker image names to Gerrit project paths                                                           |
| FR-04 | Query the Gerrit REST API for project state and metadata                                                 |
| FR-05 | Cross-reference with `relman/repos.yaml` for maintenance status                                          |
| FR-06 | Cross-reference with ci-management JJB for active CI status                                              |
| FR-07 | Produce a unified release manifest in JSON (primary) and additional output formats (YAML, CSV, Markdown) |
| FR-08 | Support diffing two manifests to show added/removed/changed repos and images                             |
| FR-09 | Validate that referenced Docker images exist in the Nexus registry                                       |
| FR-10 | Run as a CLI tool locally and as a GitHub Action in CI                                                   |
| FR-11 | Store every run's artifacts in the companion artifacts repository                                        |
| FR-12 | Generate a GitHub Pages site from the latest and historical artifacts                                    |

<!-- markdownlint-enable MD013 -->

### 2.2 Non-Functional Requirements

<!-- markdownlint-disable MD013 -->

| ID    | Requirement                                                               |
| ----- | ------------------------------------------------------------------------- |
| NF-01 | Idempotent and repeatable: same inputs produce byte-identical JSON        |
| NF-02 | Extensible schema with a version field for forward compatibility          |
| NF-03 | Modular source-plugin architecture for adding new data sources            |
| NF-04 | No authentication required for basic operation (Gerrit REST is anonymous) |
| NF-05 | Python ≥3.10, modern PEP standards, publishable to PyPI                   |
| NF-06 | Comprehensive pre-commit hooks, type checking, and test coverage          |
| NF-07 | Deterministic JSON output (sorted keys, stable ordering) for diffability  |

<!-- markdownlint-enable MD013 -->

---

## 3. Architecture Overview

### 3.1 High-Level Data Flow

```text
                          ┌────────────────────────────┐
                          │   OOM Git Repository       │
                          │   (local clone or remote)   │
                          └────────────┬───────────────┘
                                       │ Parse Helm charts
                                       ▼
┌──────────────────┐   ┌───────────────────────────────┐   ┌───────────────────┐
│ Gerrit REST API  │──▶│                               │◀──│ relman/repos.yaml │
│ /r/projects/     │   │      onap-release-map         │   │ (maintenance      │
└──────────────────┘   │      CLI Tool                 │   │  status)          │
                       │                               │   └───────────────────┘
┌──────────────────┐   │  ┌─────────┐  ┌───────────┐  │   ┌───────────────────┐
│ ci-management    │──▶│  │Collector│  │ Manifest  │  │◀──│ Nexus3 Registry   │
│ JJB definitions  │   │  │ Plugins │─▶│ Builder   │  │   │ (image validation)│
└──────────────────┘   │  └─────────┘  └─────┬─────┘  │   └───────────────────┘
                       │                     │         │
                       └─────────────────────┼─────────┘
                                             │
                              ┌───────────────┼──────────────┐
                              ▼               ▼              ▼
                        ┌──────────┐   ┌──────────┐   ┌──────────┐
                        │   JSON   │   │   YAML   │   │ Markdown │
                        │ manifest │   │ manifest │   │  report  │
                        └──────────┘   └──────────┘   └──────────┘
```

### 3.2 Plugin/Collector Architecture

Each data source is a **collector** that implements a common interface. The
manifest builder aggregates results from all enabled collectors, merging and
deduplicating entries. This makes it straightforward to add new data sources
without modifying existing code.

```text
┌─────────────────────────────────────────────────────────┐
│                    CollectorRegistry                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ OOMCollector  │  │GerritCollect.│  │RelmanCollect.│  │
│  │ (primary)     │  │ (enrichment) │  │ (enrichment) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │          │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  │
│  │JJBCollector  │  │NexusCollect. │  │IntegCollect. │  │
│  │ (enrichment) │  │ (validation) │  │ (enrichment) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Collector priority/confidence tiers:**

<!-- markdownlint-disable MD013 -->

| Tier           | Collector              | Confidence | What It Provides                                            |
| -------------- | ---------------------- | ---------- | ----------------------------------------------------------- |
| 1 (Primary)    | `OOMCollector`         | High       | Helm chart dependencies, Docker images, chart→image mapping |
| 2 (Enrichment) | `GerritCollector`      | Medium     | Project state (ACTIVE/READ_ONLY), descriptions, branches    |
| 2 (Enrichment) | `RelmanCollector`      | Medium     | Maintenance status, read-only flags from `repos.yaml`       |
| 2 (Enrichment) | `JJBCollector`         | Medium     | Active CI status, job types, Gerrit project paths           |
| 2 (Enrichment) | `IntegrationCollector` | Medium     | Version manifest data, release CSV refs                     |
| 3 (Validation) | `NexusCollector`       | N/A        | Validates image:tag existence in Nexus3 registry            |

<!-- markdownlint-enable MD013 -->

### 3.3 Design Principles

1. **OOM is the source of truth for "what's in the release"** — the Helm
   charts define the deployment; everything else enriches or validates.

2. **Every collector is optional** — the tool produces useful output with
   only the OOM collector. Additional collectors refine the picture.

3. **Deterministic output** — given identical inputs, the JSON output is
   byte-for-byte identical. Keys are sorted, lists are sorted by a stable
   key, timestamps use a fixed format.

4. **Schema-versioned artifacts** — every output file carries a
   `schema_version` field. Consumers can detect and handle schema changes.

5. **Provenance tracking** — every output records which collectors ran,
   what data sources were consulted, and the tool version that produced it.

---

## 4. Data Sources — Detailed Analysis

### 4.1 OOM Helm Charts (Primary)

**Location:** `oom/kubernetes/` in the OOM Gerrit repository.

**What to parse:**

<!-- markdownlint-disable MD013 -->

| File                                     | Data Extracted                                                            |
| ---------------------------------------- | ------------------------------------------------------------------------- |
| `onap/Chart.yaml`                        | Top-level dependencies (component names, version constraints, conditions) |
| `<component>/Chart.yaml`                 | Sub-chart dependencies (nested components, shared infrastructure charts)  |
| `<component>/values.yaml`                | Docker image references (`image:` keys with `onap/*` prefixes)            |
| `<component>/components/*/Chart.yaml`    | Deeply nested sub-chart dependencies                                      |
| `<component>/components/*/values.yaml`   | Deeply nested Docker image references                                     |
| `common/repositoryGenerator/values.yaml` | Global image definitions, registry endpoints, image→repo mapping          |

<!-- markdownlint-enable MD013 -->

**Parsing rules:**

- Recursively walk `kubernetes/` starting from `onap/Chart.yaml`.
- **Exclude** the `argo/` directory entirely (not authoritative).
- **Exclude** the `archive/` directory (deprecated charts).
- For each `values.yaml`, extract all values matching `onap/*:*` (the same
  regex used by the existing `generate-docker-manifest.sh`).
- Also extract image references from `image:` map entries where `imageName`
  and `tag` are separate fields.
- Track the chart→image relationship (which chart deploys which images).

**Docker image → Gerrit project mapping:**

This is the most challenging part. The mapping follows conventions but has
exceptions. The tool should maintain a **mapping table** (shipped as a YAML
data file within the package) that can be overridden by users. The default
table is seeded from the 94 images identified in our audit.

Heuristic rules (applied in order):

1. **Direct match:** `onap/<project>` → Gerrit `<project>`
   (e.g. `onap/cps-and-ncmp` → `cps`)
2. **Slash-to-slash:** `onap/<a>/<b>` → Gerrit `<a>/<b>`
   (e.g. `onap/policy-api` → `policy/api` via dash→slash)
3. **Java-style prefixes:** `onap/org.onap.<a>.<b>.<c>` → Gerrit `<a>/<b>`
   (e.g. `onap/org.onap.dcaegen2.collectors.ves.vescollector` →
   `dcaegen2/collectors/ves`)
4. **Explicit override:** lookup in the shipped mapping table
   (e.g. `onap/ccsdk-blueprintsprocessor` → `ccsdk/cds`)

### 4.2 Gerrit REST API

**Endpoint:** `https://gerrit.onap.org/r/projects/`

**Authentication:** None required (anonymous read access).

**Key queries:**

<!-- markdownlint-disable MD013 -->

| Query                                       | Purpose                                  |
| ------------------------------------------- | ---------------------------------------- |
| `GET /projects/?type=ALL&d&state=ACTIVE`    | All active projects with descriptions    |
| `GET /projects/?type=ALL&d&state=READ_ONLY` | All archived/read-only projects          |
| `GET /projects/{name}/branches/`            | Branch list for release branch detection |

<!-- markdownlint-enable MD013 -->

**Magic prefix:** All Gerrit REST responses start with `)]}'` which must be
stripped before JSON parsing.

**Rate limiting:** The ONAP Gerrit is not heavily rate-limited for anonymous
reads, but the client should implement polite backoff (1-second delay between
paginated requests).

### 4.3 `relman/repos.yaml`

**Location:** `relman/repos/repos.yaml` in the `relman` Gerrit repository.

**Format:** YAML dictionary keyed by top-level project name, each containing
a list of repository entries with fields:

- `repository` — Gerrit project path (e.g. `policy/api`)
- `unmaintained` — `'true'` or `'false'` (string, not boolean)
- `read_only` — `'true'` or `'false'` (string, not boolean)
- `included_in` — Release list (currently unused: all `'[]'`)

**Note:** The `included_in` field is always empty today. A future goal of
this tool is to produce data that _could_ populate this field.

**Statistics:** 372 repositories across 47 top-level projects; 297 maintained,
75 unmaintained; 173 read-only.

### 4.4 CI-Management JJB Definitions

**Location:** `ci-management/jjb/` in the `ci-management` Gerrit repository.

**Format:** YAML files defining Jenkins jobs via JJB. The key field is
`project:` which contains the Gerrit repository path.

**Statistics:** 134 unique Gerrit projects with active CI jobs across 21
top-level project areas.

**Parsing approach:** Grep for `project:` fields in YAML files, excluding
template placeholders (`{project}`, `{name}`). Map the extracted paths to
the unified project list.

### 4.5 Integration Version Manifest

**Location:** `integration/version-manifest/src/main/` in the `integration`
Gerrit repository.

**Key files:**

- `resources/docker-manifest.csv` — `image,tag` CSV (generated from OOM)
- `scripts/generate-docker-manifest.sh` — canonical image extraction script
- `integration/docs/files/csv/release-integration-ref.csv` — pinned
  commit SHAs per repo for the release

### 4.6 Nexus3 Docker Registry

**Endpoint:** `https://nexus3.onap.org/`

**Purpose:** Validate that Docker images referenced in OOM actually exist
in the release registry.

**API:** Docker Registry V2 API (`/v2/<name>/tags/list`).

---

## 5. Schema Design

### 5.1 Manifest Schema (v1.0.0)

The manifest is the primary output artifact. It uses a versioned JSON schema
designed for extensibility — new fields can be added without breaking
consumers that check `schema_version`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ONAP Release Manifest",
  "description": "Machine-readable manifest of all components in an ONAP release",
  "type": "object",
  "required": [
    "schema_version",
    "tool_version",
    "generated_at",
    "onap_release",
    "repositories",
    "docker_images",
    "helm_components",
    "provenance"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "description": "Semantic version of the manifest schema",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "examples": ["1.0.0"]
    },
    "tool_version": {
      "type": "string",
      "description": "Version of onap-release-map that generated this manifest"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp of generation"
    },
    "onap_release": {
      "type": "object",
      "required": ["name", "oom_chart_version"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Release code name (e.g. Rabat)"
        },
        "oom_chart_version": {
          "type": "string",
          "description": "OOM umbrella chart version (e.g. 18.0.0)"
        },
        "oom_branch": {
          "type": "string",
          "description": "Git branch of the OOM repo that was analyzed"
        },
        "oom_commit": {
          "type": "string",
          "description": "Git commit SHA of the OOM repo"
        }
      }
    },
    "summary": {
      "type": "object",
      "description": "Aggregate statistics",
      "properties": {
        "total_repositories": { "type": "integer" },
        "total_docker_images": { "type": "integer" },
        "total_helm_components": { "type": "integer" },
        "repositories_by_category": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "repositories_by_confidence": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "collectors_used": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "repositories": {
      "type": "array",
      "description": "All Gerrit repositories in the release",
      "items": { "$ref": "#/definitions/Repository" }
    },
    "docker_images": {
      "type": "array",
      "description": "All Docker images deployed in the release",
      "items": { "$ref": "#/definitions/DockerImage" }
    },
    "helm_components": {
      "type": "array",
      "description": "All top-level Helm chart components",
      "items": { "$ref": "#/definitions/HelmComponent" }
    },
    "provenance": {
      "type": "object",
      "description": "Metadata about how this manifest was generated",
      "properties": {
        "data_sources": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "type": { "type": "string" },
              "url": { "type": "string" },
              "commit": { "type": "string" },
              "fetched_at": { "type": "string", "format": "date-time" }
            }
          }
        },
        "collectors_executed": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "duration_seconds": { "type": "number" },
              "items_collected": { "type": "integer" },
              "errors": { "type": "array", "items": { "type": "string" } }
            }
          }
        }
      }
    }
  },
  "definitions": {
    "Repository": {
      "type": "object",
      "required": ["gerrit_project", "top_level_project", "confidence"],
      "properties": {
        "gerrit_project": {
          "type": "string",
          "description": "Full Gerrit project path (e.g. policy/api)"
        },
        "top_level_project": {
          "type": "string",
          "description": "Top-level project area (e.g. policy)"
        },
        "gerrit_url": {
          "type": "string",
          "format": "uri"
        },
        "confidence": {
          "type": "string",
          "enum": ["high", "medium", "low"],
          "description": "Confidence that this repo is in the release"
        },
        "confidence_reasons": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Human-readable explanation of confidence score"
        },
        "category": {
          "type": "string",
          "enum": [
            "runtime",
            "build-dependency",
            "infrastructure",
            "test",
            "documentation",
            "tooling"
          ]
        },
        "gerrit_state": {
          "type": "string",
          "enum": ["ACTIVE", "READ_ONLY"],
          "description": "From Gerrit REST API"
        },
        "maintained": {
          "type": "boolean",
          "description": "From relman/repos.yaml"
        },
        "has_ci": {
          "type": "boolean",
          "description": "From ci-management JJB"
        },
        "docker_images": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Docker images built from this repo"
        },
        "helm_charts": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Helm charts that deploy images from this repo"
        },
        "discovered_by": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Which collectors found this repository"
        }
      }
    },
    "DockerImage": {
      "type": "object",
      "required": ["image", "tag"],
      "properties": {
        "image": {
          "type": "string",
          "description": "Full image name (e.g. onap/policy-api)"
        },
        "tag": {
          "type": "string",
          "description": "Pinned image tag (e.g. 4.2.2)"
        },
        "registry": {
          "type": "string",
          "description": "Docker registry (e.g. nexus3.onap.org:10001)"
        },
        "gerrit_project": {
          "type": "string",
          "description": "Source Gerrit project (best-effort mapping)"
        },
        "helm_charts": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Helm charts that reference this image"
        },
        "nexus_validated": {
          "type": "boolean",
          "description": "Whether the image:tag was verified in Nexus"
        }
      }
    },
    "HelmComponent": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Chart name in the umbrella (e.g. policy)"
        },
        "version": {
          "type": "string",
          "description": "Chart version constraint"
        },
        "enabled_by_default": {
          "type": "boolean"
        },
        "condition_key": {
          "type": "string",
          "description": "Helm values key that enables this component"
        },
        "sub_charts": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Names of nested sub-charts"
        },
        "docker_images": {
          "type": "array",
          "items": { "type": "string" },
          "description": "All Docker images deployed by this component"
        },
        "gerrit_projects": {
          "type": "array",
          "items": { "type": "string" },
          "description": "All Gerrit projects contributing to this component"
        }
      }
    }
  }
}
```

### 5.2 Schema Evolution Strategy

- **Minor versions** (1.1.0, 1.2.0): add new optional fields. Consumers
  that ignore unknown fields are unaffected.
- **Major versions** (2.0.0): change required fields or restructure.
  The tool should be able to read and diff manifests from older schema
  versions via a compatibility layer.
- The JSON Schema definition is shipped inside the Python package at
  `src/onap_release_map/schemas/manifest-v1.schema.json` and is
  importable at runtime for self-validation.

---

## 6. CLI Tool Design

### 6.1 Package Identity

| Field           | Value                      |
| --------------- | -------------------------- |
| **PyPI name**   | `onap-release-map`         |
| **Import name** | `onap_release_map`         |
| **CLI command** | `onap-release-map`         |
| **Entry point** | `onap_release_map.cli:app` |

### 6.2 Subcommands

```text
onap-release-map [OPTIONS] COMMAND [ARGS]

Commands:
  discover    Parse OOM charts and generate the release manifest
  diff        Compare two manifests and report differences
  verify      Check Docker image existence in the Nexus registry
  export      Convert a manifest to CSV, YAML, or Markdown
  schema      Print the JSON Schema for the manifest format
  version     Print version information
```

#### `discover` (Primary Command)

```text
onap-release-map discover [OPTIONS]

Options:
  --oom-path PATH           Path to local OOM repo clone
  --oom-branch TEXT         OOM branch to analyze (if cloning from remote)
  --oom-remote URL          OOM Git remote URL (clones to temp dir)
  --gerrit-url URL          Gerrit base URL [default: https://gerrit.onap.org/r]
  --relman-path PATH        Path to local relman repo clone
  --ci-mgmt-path PATH       Path to local ci-management repo clone
  --collectors TEXT          Comma-separated list of collectors to enable
                             [default: oom,gerrit,relman,jjb]
  --mapping-file PATH       Custom image→repo mapping YAML override
  --output-dir PATH         Output directory [default: ./output]
  --output-format TEXT       Output formats: json,yaml,csv,md,all
                             [default: json]
  --deterministic / --no-deterministic
                             Produce deterministic output [default: True]
  --verbose / -v             Increase verbosity (up to -vvv)
```

#### `diff`

```text
onap-release-map diff [OPTIONS] MANIFEST_A MANIFEST_B

Arguments:
  MANIFEST_A    Path or URL to the baseline manifest (JSON)
  MANIFEST_B    Path or URL to the comparison manifest (JSON)

Options:
  --output-format TEXT    Output format: text, json, md [default: text]
  --output PATH           Write diff to file instead of stdout
  --ignore-timestamps     Ignore generated_at when comparing
```

**Diff output includes:**

- Repositories added / removed / changed (category, confidence, state)
- Docker images added / removed / version changed
- Helm components added / removed / enabled-state changed
- Summary statistics delta

#### `verify`

```text
onap-release-map verify [OPTIONS] MANIFEST

Arguments:
  MANIFEST    Path to manifest JSON file

Options:
  --nexus-url URL         Nexus3 registry URL
                           [default: https://nexus3.onap.org]
  --check-images          Verify Docker image:tag existence
  --check-gerrit          Verify Gerrit projects are accessible
  --workers INT            Concurrent validation threads [default: 4]
```

#### `export`

```text
onap-release-map export [OPTIONS] MANIFEST

Arguments:
  MANIFEST    Path to manifest JSON file

Options:
  --format TEXT    Output format: yaml, csv, md, gerrit-list
  --output PATH    Write to file instead of stdout
  --repos-only     Export only the repository list (no images/charts)
  --images-only    Export only the Docker image list
```

The `gerrit-list` format outputs a plain-text list of Gerrit project paths,
one per line, compatible with the `projects.txt` convention used by
`integration/bootstrap/` scripts.

### 6.3 Source Layout

```text
onap-release-mapping-tool/
├── .editorconfig
├── .github/
│   ├── actionlint.yaml
│   ├── dependabot.yml
│   ├── release-drafter.yml
│   ├── scripts/
│   │   ├── copy-artifacts.sh          # Push artifacts to companion repo
│   │   └── generate-index.sh          # Generate GitHub Pages index.html
│   └── workflows/
│       ├── autolabeler.yaml           # (from template)
│       ├── build-test.yaml            # PR: build → test → audit → SBOM
│       ├── build-test-release.yaml    # Tag: build → test → PyPI → release
│       ├── mapping-production.yaml    # Scheduled/manual: run tool → publish
│       ├── release-drafter.yaml       # (from template)
│       ├── semantic-pull-request.yaml # (from template)
│       ├── sha-pinned-actions.yaml    # (from template)
│       └── tag-push.yaml              # (from template)
├── .gitignore
├── .gitlint
├── .pre-commit-config.yaml
├── .yamllint
├── LICENSE
├── LICENSES/
│   └── Apache-2.0.txt
├── README.md
├── REUSE.toml
├── action.yaml                        # GitHub Action composite wrapper
├── configuration/
│   └── default.yaml                   # Default tool configuration
├── pyproject.toml
├── src/
│   └── onap_release_map/
│       ├── __init__.py
│       ├── __main__.py                # python -m onap_release_map
│       ├── _version.py                # Auto-generated by hatch-vcs
│       ├── py.typed                   # PEP 561 marker
│       ├── cli.py                     # Typer CLI definition
│       ├── config.py                  # Configuration loading/merging
│       ├── exceptions.py              # Custom exception hierarchy
│       ├── manifest.py                # ManifestBuilder: aggregation + output
│       ├── differ.py                  # Manifest diff logic
│       ├── exporter.py                # Output format converters
│       ├── collectors/
│       │   ├── __init__.py            # CollectorRegistry, BaseCollector ABC
│       │   ├── oom.py                 # OOMCollector (Helm chart parser)
│       │   ├── gerrit.py              # GerritCollector (REST API client)
│       │   ├── relman.py              # RelmanCollector (repos.yaml parser)
│       │   ├── jjb.py                 # JJBCollector (ci-management parser)
│       │   ├── integration.py         # IntegrationCollector (version manifest)
│       │   └── nexus.py               # NexusCollector (image validation)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── repository.py          # OnapRepository dataclass
│       │   ├── docker_image.py        # DockerImage dataclass
│       │   ├── helm_component.py      # HelmComponent dataclass
│       │   └── manifest.py            # ReleaseManifest dataclass
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── helm.py                # Helm Chart.yaml / values.yaml parser
│       │   ├── image_mapper.py        # Docker image → Gerrit project mapper
│       │   └── yaml_utils.py          # Safe YAML loading utilities
│       ├── schemas/
│       │   └── manifest-v1.schema.json
│       └── data/
│           └── image_repo_mapping.yaml  # Default image→repo mapping table
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                      # Sample Chart.yaml, values.yaml, etc.
│   ├── test_cli.py
│   ├── test_collectors/
│   │   ├── test_oom.py
│   │   ├── test_gerrit.py
│   │   ├── test_relman.py
│   │   └── test_jjb.py
│   ├── test_differ.py
│   ├── test_exporter.py
│   ├── test_manifest.py
│   └── test_parsers/
│       ├── test_helm.py
│       └── test_image_mapper.py
└── docs/
    ├── conf.py
    └── index.rst
```

### 6.4 Key Dependencies

| Package      | Purpose                                      | Min Version |
| ------------ | -------------------------------------------- | ----------- |
| `typer`      | CLI framework                                | ≥0.21.0     |
| `rich`       | Terminal formatting, tables, progress bars   | ≥14.0.0     |
| `pydantic`   | Data validation and serialization for models | ≥2.10.0     |
| `httpx`      | HTTP client for Gerrit/Nexus REST APIs       | ≥0.28.0     |
| `pyyaml`     | YAML parsing for Helm charts and config      | ≥6.0.0      |
| `jsonschema` | Runtime manifest validation                  | ≥4.23.0     |

**Dev dependencies:**

| Package                | Purpose                    |
| ---------------------- | -------------------------- |
| `pytest`               | Testing framework          |
| `pytest-cov`           | Coverage reporting         |
| `responses` or `respx` | HTTP mocking for API tests |
| `ruff`                 | Linting and formatting     |
| `mypy`                 | Type checking              |
| `basedpyright`         | Additional type checking   |

### 6.5 Build System

Following the `dependamerge` template:

- **Build backend:** Hatchling + hatch-vcs
- **Version source:** VCS (git tags)
- **`_version.py`:** Auto-generated by `hatch-vcs` build hook
- **Wheel packages:** `src/onap_release_map`
- **Python support:** ≥3.10

---

## 7. GitHub Action Interface

### 7.1 `action.yaml` (Composite Action)

The `action.yaml` wraps the CLI tool for use in GitHub Actions workflows. It
installs the tool via `uv` and runs the `discover` subcommand.

**Inputs:**

<!-- markdownlint-disable MD013 -->

| Input            | Required | Default                         | Description                    |
| ---------------- | -------- | ------------------------------- | ------------------------------ |
| `oom-path`       | No       | (clones from Gerrit)            | Path to pre-cloned OOM repo    |
| `oom-branch`     | No       | `master`                        | OOM branch to analyze          |
| `gerrit-url`     | No       | `https://gerrit.onap.org/r`     | Gerrit base URL                |
| `collectors`     | No       | `oom,gerrit`                    | Comma-separated collector list |
| `output-dir`     | No       | `$RUNNER_TEMP/onap-release-map` | Output directory               |
| `output-format`  | No       | `json`                          | Output formats                 |
| `python-version` | No       | `3.12`                          | Python version to use          |

<!-- markdownlint-enable MD013 -->

**Outputs:**

| Output               | Description                              |
| -------------------- | ---------------------------------------- |
| `manifest-path`      | Path to the generated JSON manifest      |
| `manifest-version`   | Schema version of the generated manifest |
| `total-repositories` | Number of repositories found             |
| `total-images`       | Number of Docker images found            |
| `onap-release`       | ONAP release name (e.g. Rabat)           |

**Steps (composite):**

1. Install Python via `actions/setup-python`
2. Install `uv` via `astral-sh/setup-uv`
3. Install the tool: `uv tool install .` (or from PyPI if `version` input
   is provided)
4. Clone OOM if `oom-path` is not provided
5. Run `onap-release-map discover` with the configured options
6. Set outputs from the manifest JSON
7. Upload the output directory as a workflow artifact

---

## 8. Workflow Design

### 8.1 `build-test.yaml` — PR CI Pipeline

**Trigger:** Pull requests and `workflow_dispatch`.

**Job DAG:**

```text
repository-metadata ──┐
                      ├──▶ python-tests (matrix) ──▶ ✓
python-build ─────────┤
                      ├──▶ python-audit (matrix) ──▶ ✓
                      │
                      └──▶ sbom ──▶ ✓
```

**Pattern:** Identical to `dependamerge` — uses `lfreleng-actions/*`
reusable actions for build, test, audit, and SBOM generation with Grype
vulnerability scanning. All actions SHA-pinned. Hardened runners. Minimal
permissions.

### 8.2 `build-test-release.yaml` — Tag/Release Pipeline

**Trigger:** Tag pushes (`**`).

**Job DAG:**

```text
tag-validate ─▶ python-build ─▶ python-tests ─▶ test-pypi ─▶ pypi
                    │                                            │
                    ├──▶ python-audit                            ▼
                    │                               attach-artefacts
                    └──▶ sbom                              │
                                                           ▼
                                                   promote-release
```

**Pattern:** Identical to `dependamerge` — tag validation, signed builds
with attestations, two-stage PyPI publishing (TestPyPI → production),
artifact attachment to draft release, then promotion to published.

### 8.3 `mapping-production.yaml` — Release Mapping Workflow

**Trigger:** `workflow_dispatch` only (manual). A scheduled cron can be
added later once the tool is stable.

**Inputs (workflow_dispatch):**

<!-- markdownlint-disable MD013 -->

| Input            | Required | Default                 | Description              |
| ---------------- | -------- | ----------------------- | ------------------------ |
| `oom_branch`     | No       | `master`                | OOM branch to analyze    |
| `collectors`     | No       | `oom,gerrit,relman,jjb` | Collectors to enable     |
| `skip_pages`     | No       | `false`                 | Skip GitHub Pages update |
| `skip_artifacts` | No       | `false`                 | Skip artifact transfer   |
| `debug`          | No       | `false`                 | Enable debug output      |

<!-- markdownlint-enable MD013 -->

**Job DAG:**

```text
analyze ──▶ publish-pages ──▶ copy-to-artifacts-repo ──▶ summary
```

#### Job 1: `analyze`

1. Check out `onap-release-mapping-tool` repository
2. Install Python + uv, sync dependencies
3. Clone OOM from Gerrit (sparse checkout of `kubernetes/` only)
4. Optionally clone `relman`, `ci-management`, `integration` repos
5. Run `onap-release-map discover` with all configured collectors
6. Create `metadata.json` with run provenance
7. Upload artifacts:
   - `manifest` — the JSON/YAML/CSV/Markdown manifest files
   - `metadata` — `metadata.json` with provenance

#### Job 2: `publish-pages`

1. Check out `gh-pages` branch of the **tool** repository
2. Download `manifest` artifact from the `analyze` job
3. Copy manifest files into a date-stamped directory
   (`YYYY-MM-DD/`) and also into `latest/`
4. Run `generate-index.sh` to create/update `index.html`
5. Commit and push to `gh-pages`

#### Job 3: `copy-to-artifacts-repo`

1. Download all artifacts from the `analyze` job
2. Run `copy-artifacts.sh` which:
   - Clones `modeseven-lfit/onap-release-mapping-artifacts` using the
     fine-grained `ARTIFACTS_REPO_TOKEN` secret
   - Creates `data/artifacts/YYYY-MM-DD/` directory
   - Copies manifest and metadata files
   - Generates a `README.md` for the date folder
   - Commits and pushes to `main`

#### Job 4: `summary`

1. Always runs (even if prior jobs fail)
2. Generates `$GITHUB_STEP_SUMMARY` with key statistics
3. Reports any failures

### 8.4 Secrets and Variables

**Repository secrets** (on the tool repo):

<!-- markdownlint-disable MD013 -->

| Secret                 | Purpose                                                                |
| ---------------------- | ---------------------------------------------------------------------- |
| `ARTIFACTS_REPO_TOKEN` | Fine-grained PAT with write access to `onap-release-mapping-artifacts` |

<!-- markdownlint-enable MD013 -->

**Repository variables** (on the tool repo):

| Variable     | Value                       | Purpose            |
| ------------ | --------------------------- | ------------------ |
| `GERRIT_URL` | `https://gerrit.onap.org/r` | Gerrit base URL    |
| `OOM_BRANCH` | `master`                    | Default OOM branch |

---

## 9. Artifacts Repository Design

### 9.1 Repository: `onap-release-mapping-artifacts`

This is a **passive data store** — it contains no workflows of its own. All
content is pushed by the tool repository's `mapping-production.yaml` workflow.

### 9.2 Directory Structure

```text
onap-release-mapping-artifacts/
├── .editorconfig
├── .gitignore
├── .gitlint
├── .pre-commit-config.yaml          # repos: [] (disabled)
├── .yamllint
├── LICENSE
├── LICENSES/
│   └── Apache-2.0.txt
├── README.md
├── REUSE.toml                       # Blanket annotation for data/**
└── data/
    └── artifacts/
        ├── 2026-07-15/
        │   ├── README.md            # Auto-generated run summary
        │   ├── manifest.json        # Release manifest (primary artifact)
        │   ├── manifest.yaml        # YAML format
        │   ├── manifest.csv         # CSV format (repos only)
        │   ├── manifest.md          # Markdown report
        │   ├── metadata.json        # Run provenance
        │   └── diff-from-previous.json  # Diff from last run (if available)
        ├── 2026-07-16/
        │   └── ...
        └── latest -> 2026-07-16     # Symlink to most recent
```

### 9.3 GitHub Pages

GitHub Pages should be enabled on the artifacts repo, serving from the `main`
branch `/` path. A simple `index.html` at the root provides navigation to
historical manifests.

Alternatively (and preferably), the tool repo's `gh-pages` branch hosts the
rendered reports, while the artifacts repo stores the raw data for archival
and machine consumption.

### 9.4 Size Management

Unlike the project-reporting-tool (which produces multi-MB raw JSON per
project per day), the release manifest is expected to be relatively compact
(~100-200 KB per run). At daily runs this would be ~50-70 MB/year, which is
manageable without pruning. If size becomes an issue, old artifacts can be
compressed or moved to tagged releases.

---

## 10. Docker Image → Gerrit Repo Mapping Table

This is a critical data file shipped with the tool. It encodes the known
mapping between Docker image names and their source Gerrit projects.
The mapping is loaded at runtime and can be overridden via `--mapping-file`.

### 10.1 Format

```yaml
# image_repo_mapping.yaml
# Maps Docker image names (without registry prefix) to Gerrit project paths.
# Only exceptions and non-obvious mappings need entries here.
# The tool applies heuristic rules first; this table overrides heuristics.

mappings:
  # AAI
  onap/babel: aai/babel
  onap/aai-graphadmin: aai/graphadmin
  onap/aai-haproxy: aai/aai-common
  onap/aai-resources: aai/resources
  onap/aai-schema-service: aai/schema-service
  onap/aai-traversal: aai/traversal
  onap/model-loader: aai/model-loader
  onap/sparky-be: aai/sparky-be

  # CCSDK / CDS
  onap/ccsdk-blueprintsprocessor: ccsdk/cds
  onap/ccsdk-commandexecutor: ccsdk/cds
  onap/ccsdk-py-executor: ccsdk/cds
  onap/ccsdk-sdclistener: ccsdk/cds
  onap/ccsdk-cds-ui-server: ccsdk/cds
  onap/ccsdk-dgbuilder-image: ccsdk/distribution
  onap/ccsdk-apps-ms-neng: ccsdk/apps
  onap/ccsdk-oran-a1policymanagementservice: ccsdk/oran

  # CPS
  onap/cps-and-ncmp: cps
  onap/cps-temporal: cps
  onap/ncmp-dmi-plugin: cps/ncmp-dmi-plugin

  # DCAEGEN2
  onap/org.onap.dcaegen2.collectors.hv-ves.hv-collector-main: dcaegen2/collectors/hv-ves
  onap/org.onap.dcaegen2.collectors.ves.vescollector: dcaegen2/collectors/ves
  onap/org.onap.dcaegen2.deployments.dcae-services-policy-sync: dcaegen2/deployments
  onap/org.onap.dcaegen2.deployments.healthcheck-container: dcaegen2/deployments
  onap/org.onap.dcaegen2.platform.ves-openapi-manager: dcaegen2/platform/ves-openapi-manager
  onap/org.onap.dcaegen2.services.datalakeadminui: dcaegen2/services
  onap/org.onap.dcaegen2.services.datalake.exposure.service: dcaegen2/services
  onap/org.onap.dcaegen2.services.datalakefeeder: dcaegen2/services
  onap/org.onap.dcaegen2.services.prh.prh-app-server: dcaegen2/services/prh

  # DMaaP
  onap/dmaap/datarouter-prov-client: dmaap/datarouter

  # Integration
  onap/integration-java11: integration/docker/onap-java11

  # Multicloud
  onap/multicloud/framework: multicloud/framework
  onap/multicloud/framework-artifactbroker: multicloud/framework
  onap/multicloud/k8s: multicloud/k8s
  onap/multicloud/openstack-fcaps: multicloud/openstack

  # OOM
  onap/oom/readiness: oom/readiness
  onap/org.onap.oom.platform.cert-service.oom-certservice-api: oom/platform/cert-service
  onap/org.onap.oom.platform.cert-service.oom-certservice-k8s-external-provider: oom/platform/cert-service
  onap/org.onap.oom.platform.cert-service.oom-certservice-post-processor: oom/platform/cert-service

  # Policy
  onap/policy-apex-pdp: policy/apex-pdp
  onap/policy-api: policy/api
  onap/policy-pap: policy/pap
  onap/policy-xacml-pdp: policy/xacml-pdp
  onap/policy-pdpd-cl: policy/drools-pdp
  onap/policy-opa-pdp: policy/opa-pdp
  onap/policy-distribution: policy/distribution
  onap/policy-db-migrator: policy/docker
  onap/policy-clamp-ac-k8s-ppnt: policy/clamp
  onap/policy-clamp-ac-http-ppnt: policy/clamp
  onap/policy-clamp-ac-a1pms-ppnt: policy/clamp
  onap/policy-clamp-ac-kserve-ppnt: policy/clamp
  onap/policy-clamp-ac-pf-ppnt: policy/clamp
  onap/policy-clamp-runtime-acm: policy/clamp

  # Portal-NG
  onap/portal-ng/bff: portal-ng/bff
  onap/portal-ng/history: portal-ng/history
  onap/portal-ng/preferences: portal-ng/preferences
  onap/portal-ng/ui: portal-ng/ui

  # SDC
  onap/sdc-backend-all-plugins: sdc
  onap/sdc-backend-init: sdc
  onap/sdc-cassandra: sdc
  onap/sdc-cassandra-init: sdc
  onap/sdc-frontend: sdc
  onap/sdc-onboard-backend: sdc
  onap/sdc-onboard-cassandra-init: sdc
  onap/sdc-workflow-backend: sdc/sdc-workflow-designer
  onap/sdc-workflow-frontend: sdc/sdc-workflow-designer
  onap/sdc-workflow-init: sdc/sdc-workflow-designer
  onap/sdc-helm-validator: sdc/sdc-helm-validator

  # SDNC
  onap/sdnc-image: sdnc/oam
  onap/sdnc-ansible-server-image: sdnc/oam
  onap/sdnc-web-image: sdnc/oam
  onap/sdnc-ueb-listener-image: sdnc/oam

  # SO
  onap/so/api-handler-infra: so
  onap/so/bpmn-infra: so
  onap/so/catalog-db-adapter: so
  onap/so/openstack-adapter: so
  onap/so/request-db-adapter: so
  onap/so/sdc-controller: so
  onap/so/sdnc-adapter: so
  onap/so/so-admin-cockpit: so/so-admin-cockpit
  onap/so/so-cnf-adapter: so
  onap/so/so-cnfm-as-lcm: so
  onap/so/so-etsi-nfvo-ns-lcm: so
  onap/so/so-etsi-sol003-adapter: so/adapters/so-etsi-sol003-adapter
  onap/so/so-etsi-sol005-adapter: so/adapters/so-etsi-sol005-adapter
  onap/so/so-nssmf-adapter: so/adapters/so-nssmf-adapter
  onap/so/so-oof-adapter: so/adapters/so-oof-adapter
  onap/so/ve-vnfm-adapter: so

  # Music
  onap/music/prom: music/prom

  # Testsuite
  onap/testsuite: testsuite

  # Usecase-UI
  onap/usecase-ui: usecase-ui
  onap/usecase-ui-server: usecase-ui/server
  onap/usecase-ui-nlp: usecase-ui/nlp
  onap/usecase-ui-intent-analysis: usecase-ui/intent-analysis
  onap/usecase-ui-llm-adaptation: usecase-ui/llm-adaptation

# Build-only dependencies (not producing Docker images but required for build)
# These are discovered by the JJB collector, not the OOM collector.
build_dependencies:
  - oparent
  - ccsdk/parent
  - ccsdk/sli
  - ccsdk/features
  - policy/parent
  - policy/common
  - policy/models
  - policy/drools-applications
  - so/libs
  - aai/aai-common
  - aai/rest-client
  - sdc/sdc-be-common
  - sdc/sdc-distribution-client
  - sdc/sdc-tosca
  - sdnc/northbound

# Infrastructure repositories (required for CI/CD and project governance)
infrastructure:
  - ci-management
  - integration
  - integration/csit
  - integration/xtesting
  - demo
  - doc
  - relman
  - oom
  - vnfrqts/requirements
```

---

## 11. Implementation Phases

### Phase 1: Project Scaffolding and OOM Collector

**Goal:** Produce a working CLI tool that parses OOM charts and outputs a
manifest with Docker images and their mapped Gerrit projects.

**Tasks:**

1. **Scaffold the project:**
   - Create `pyproject.toml` (Hatchling + hatch-vcs, Typer + Rich deps)
   - Create `REUSE.toml` with SPDX annotation rules
   - Create `src/onap_release_map/` package with `__init__.py`, `py.typed`,
     `__main__.py`, `cli.py`
   - Update `.pre-commit-config.yaml` ruff scopes for new source paths
   - Update `README.md` with project description
   - Create `action.yaml` composite action skeleton

2. **Implement core models** (`models/`):
   - `OnapRepository`, `DockerImage`, `HelmComponent`, `ReleaseManifest`
     as Pydantic models with JSON serialization
   - Ship `manifest-v1.schema.json` in `schemas/`

3. **Implement the Helm chart parser** (`parsers/helm.py`):
   - Parse `Chart.yaml` for dependencies (name, version, condition)
   - Parse `values.yaml` for Docker image references
   - Recursive walking of sub-chart directories
   - Exclusion of `argo/` and `archive/` directories

4. **Implement the image mapper** (`parsers/image_mapper.py`):
   - Load `data/image_repo_mapping.yaml`
   - Apply heuristic rules for unmapped images
   - Support user-supplied override files

5. **Implement the OOM collector** (`collectors/oom.py`):
   - Orchestrates helm parser + image mapper
   - Produces a list of `OnapRepository`, `DockerImage`, `HelmComponent`

6. **Implement the manifest builder** (`manifest.py`):
   - Aggregates collector results
   - Deduplicates and merges entries
   - Produces deterministic JSON output with provenance metadata

7. **Implement the CLI** (`cli.py`):
   - `discover` subcommand with `--oom-path` option
   - `schema` subcommand
   - `version` subcommand
   - Rich console output with progress indicators

8. **Write tests:**
   - Fixture files: sample `Chart.yaml` and `values.yaml` files
   - Unit tests for helm parser, image mapper, OOM collector
   - Integration test for the full `discover` pipeline
   - CLI smoke tests via `typer.testing.CliRunner`

9. **Set up CI workflows:**
   - `build-test.yaml` — PR pipeline (build → test → audit → SBOM)

**Deliverable:** `onap-release-map discover --oom-path ./oom` produces a
valid JSON manifest with ~94 Docker images and ~50-60 Gerrit projects.

### Phase 2: Enrichment Collectors

**Goal:** Add the Gerrit, relman, and JJB collectors to enrich the manifest
with project state, maintenance status, and CI coverage.

**Tasks:**

1. **Implement Gerrit REST client** (`collectors/gerrit.py`):
   - HTTP client with magic-prefix stripping
   - Query `/projects/?type=ALL&d&state=ACTIVE`
   - Query `/projects/?type=ALL&d&state=READ_ONLY`
   - Polite rate limiting (1s between requests)
   - Map results to `gerrit_state` on existing `OnapRepository` entries
   - Add newly discovered repos at medium confidence

2. **Implement relman collector** (`collectors/relman.py`):
   - Parse `repos.yaml` (handle string booleans: `'true'`/`'false'`)
   - Map `unmaintained` and `read_only` fields to `OnapRepository`
   - Add build-dependency repos at medium confidence

3. **Implement JJB collector** (`collectors/jjb.py`):
   - Grep for `project:` fields in YAML files under `jjb/`
   - Exclude template placeholders
   - Map to `has_ci` on `OnapRepository` entries

4. **Implement the collector registry** (`collectors/__init__.py`):
   - `BaseCollector` abstract class with `collect()` method
   - `CollectorRegistry` for discovery and ordering
   - `--collectors` CLI option for enabling/disabling

5. **Extend the manifest builder:**
   - Merge logic for multi-collector results
   - Confidence scoring based on collector agreement
   - `discovered_by` and `confidence_reasons` population

6. **Write tests** for each collector with mocked API responses.

**Deliverable:** Running with all four collectors produces a manifest with
~90-110 Gerrit projects, each annotated with confidence, state, maintenance
status, and CI coverage.

### Phase 3: Diff, Export, and Validation

**Goal:** Add the `diff`, `export`, and `verify` subcommands.

**Tasks:**

1. **Implement `differ.py`:**
   - Load two manifests, compare by `gerrit_project` and `image` keys
   - Produce added/removed/changed lists for repos, images, and charts
   - Support text, JSON, and Markdown output formats
   - Handle schema version differences gracefully

2. **Implement `exporter.py`:**
   - YAML output via `pyyaml`
   - CSV output (repos-only and images-only modes)
   - Markdown report with tables (using Rich or Jinja2)
   - `gerrit-list` plain-text format

3. **Implement Nexus collector/validator** (`collectors/nexus.py`):
   - Docker Registry V2 API: `GET /v2/<name>/tags/list`
   - Concurrent validation with configurable worker count
   - Populate `nexus_validated` field on `DockerImage` entries

4. **Wire up CLI subcommands:** `diff`, `export`, `verify`.

5. **Write tests** for diff logic (particularly edge cases around
   schema version differences), export formats, and Nexus validation.

**Deliverable:** Full CLI functionality. Users can generate manifests, diff
them, export to multiple formats, and verify against Nexus.

### Phase 4: GitHub Action and CI Workflows

**Goal:** Complete the GitHub Action wrapper and production workflow.

**Tasks:**

1. **Implement `action.yaml`:**
   - Composite action with all inputs/outputs defined
   - Installs uv, Python, the tool
   - Clones OOM from Gerrit (sparse checkout)
   - Runs `discover`, sets outputs from the manifest

2. **Implement `mapping-production.yaml`:**
   - `analyze` job: runs the action, uploads artifacts
   - `publish-pages` job: updates `gh-pages` on the tool repo
   - `copy-to-artifacts-repo` job: pushes to
     `onap-release-mapping-artifacts` via `copy-artifacts.sh`
   - `summary` job: generates workflow summary

3. **Implement `generate-index.sh`:**
   - Create a styled `index.html` for GitHub Pages
   - Card-based navigation to date-stamped manifests
   - Links to JSON, Markdown, and diff views

4. **Implement `copy-artifacts.sh`:**
   - Clone artifacts repo with `ARTIFACTS_REPO_TOKEN`
   - Create date-stamped directory, copy files, generate README
   - Commit and push

5. **Bootstrap the artifacts repository:**
   - Add `README.md`, `LICENSE`, `REUSE.toml`, `.pre-commit-config.yaml`
     (with `repos: []`), `.gitlint`, `.editorconfig`, `.yamllint`
   - Enable GitHub Pages on `main` branch

6. **Implement `build-test-release.yaml`:**
   - Tag-triggered release pipeline
   - TestPyPI → production PyPI publishing
   - Artifact attachment and release promotion

7. **Configure secrets and variables** on the tool repository.

**Deliverable:** End-to-end automated pipeline. Manual `workflow_dispatch`
triggers analysis, publishes results to GitHub Pages, and archives artifacts.

### Phase 5: Polish and Hardening

**Goal:** Production readiness, documentation, and PyPI publication.

**Tasks:**

1. **Documentation:**
   - Comprehensive `README.md` with usage examples
   - Sphinx docs for ReadTheDocs
   - Inline docstrings (100% coverage via `interrogate`)

2. **Robustness:**
   - Error handling for network failures, malformed YAML, missing files
   - Graceful degradation when optional collectors fail
   - Retry logic for Gerrit/Nexus API calls

3. **Performance:**
   - Concurrent Docker image validation
   - Caching of Gerrit API responses within a single run
   - Sparse git checkout for large repos (only `kubernetes/` from OOM)

4. **Release management:**
   - Tag `v0.1.0` to trigger first PyPI publish
   - Create GitHub release with changelog

5. **Feedback loop:**
   - Propose a patch to `relman/repos.yaml` to populate the `included_in`
     field using data from this tool's manifests

---

## 12. Configuration File Format

The tool supports a YAML configuration file for default settings, loaded
from `configuration/default.yaml` and overridable via `--config`.

```yaml
# configuration/default.yaml
---
# ONAP Gerrit server
gerrit:
  url: "https://gerrit.onap.org/r"
  timeout: 30
  max_retries: 3

# OOM repository
oom:
  default_branch: "master"
  remote_url: "https://gerrit.onap.org/r/oom"
  exclude_dirs:
    - "argo"
    - "archive"

# Collectors to enable by default
collectors:
  - oom
  - gerrit
  - relman
  - jjb

# Output settings
output:
  formats:
    - json
  deterministic: true
  pretty_print: true
  indent: 2

# Nexus registry for validation
nexus:
  url: "https://nexus3.onap.org"
  timeout: 10
  concurrent_workers: 4

# Logging
logging:
  level: "INFO"
  format: "rich"
```

---

## 13. Testing Strategy

### 13.1 Test Pyramid

<!-- markdownlint-disable MD013 -->

| Level           | Scope                        | Tools                     | Target                                               |
| --------------- | ---------------------------- | ------------------------- | ---------------------------------------------------- |
| **Unit**        | Individual functions/classes | pytest, fixtures          | Parsers, mappers, models, collectors (mocked APIs)   |
| **Integration** | Multi-component flows        | pytest, respx/responses   | Full discover pipeline with fixture data             |
| **CLI**         | Command-line interface       | `typer.testing.CliRunner` | All subcommands with various option combinations     |
| **Schema**      | Output validation            | jsonschema                | Generated manifests validate against the JSON Schema |

<!-- markdownlint-enable MD013 -->

### 13.2 Fixture Strategy

The `tests/fixtures/` directory should contain sample ONAP data files:

- `oom/` — minimal Helm chart tree with representative `Chart.yaml` and
  `values.yaml` files (extracted from the real OOM repo)
- `relman/repos.yaml` — subset of the real `repos.yaml`
- `jjb/` — representative JJB YAML files
- `gerrit_responses/` — JSON fixtures for Gerrit API responses
- `manifests/` — sample manifest JSON files for diff testing

### 13.3 Coverage Target

- Initial target: **70%** line coverage
- Aspirational target: **85%** line coverage
- Critical paths (parsers, mappers, manifest builder): **90%+**

---

## 14. Release Strategy

### 14.1 Versioning

Semantic versioning via git tags. The version is derived from tags by
`hatch-vcs` — no manual version bumps needed.

- `v0.1.0` — Phase 1 complete (OOM collector only)
- `v0.2.0` — Phase 2 complete (all enrichment collectors)
- `v0.3.0` — Phase 3 complete (diff, export, verify)
- `v0.4.0` — Phase 4 complete (GitHub Action, CI workflows)
- `v1.0.0` — Phase 5 complete (production-ready)

### 14.2 PyPI Publication

- **TestPyPI:** Automatic on every tag push (via `build-test-release.yaml`)
- **Production PyPI:** Automatic after TestPyPI succeeds
- **Trusted publishing:** OIDC-based, no long-lived API tokens
- **Sigstore signing:** All release artifacts are signed
- **Attestations:** Build provenance attestations attached to releases

### 14.3 GitHub Releases

- Draft releases created automatically by `release-drafter`
- Promoted to published by `tag-push.yaml` after tag validation
- Build artifacts (wheel, sdist) attached to each release

---

## 15. Open Questions and Future Work

### 15.1 Open Questions

1. **Should the tool clone OOM at runtime or require a pre-existing clone?**
   Both are supported; the default for CI should be runtime cloning (via
   sparse checkout for speed), while local development uses a pre-existing
   clone.

2. **Should we attempt to resolve transitive build dependencies?**
   Maven POM analysis (`oparent`, `ccsdk/parent`, etc.) would significantly
   expand coverage but adds complexity. This is deferred to a future phase.

3. **How should we handle the `included_in` field in `relman/repos.yaml`?**
   The tool could generate a patch file that populates this field based on
   its analysis, which could then be submitted as a Gerrit change.

4. **Should the tool support analyzing specific ONAP release branches?**
   Yes — the `--oom-branch` option should accept branch names like
   `newdelhi`, `montreal`, etc. The Gerrit API can also filter by branch.

### 15.2 Future Enhancements

- **Maven POM analysis** for build-dependency discovery
- **Dockerfile analysis** for verifying image→repo mappings
- **GitHub mirror integration** for repos that have GitHub mirrors
- **Slack/email notifications** when the manifest changes significantly
- **Web dashboard** on GitHub Pages with interactive charts and search
- **Integration with ONAP release process** — automated validation gate
- **Multi-release comparison** — side-by-side view of N releases
- **Project health scoring** — combine activity, CI, maintenance status

---

## 16. Reference: Current ONAP Rabat Release Components

Based on the audit performed during the research phase, here is the
expected output for the current **Rabat** release (OOM chart v18.0.0):

### 16.1 Top-Level Helm Components (23)

| Component            | Version | Default Enabled |
| -------------------- | ------- | --------------- |
| `a1policymanagement` | ~13.x-0 | No              |
| `aai`                | ~16.x-0 | No              |
| `authentication`     | ~15.x-0 | No              |
| `cassandra`          | ~16.x-0 | No              |
| `cds`                | ~16.x-0 | No              |
| `common`             | ~13.x-0 | Yes (always)    |
| `cps`                | ~13.x-0 | No              |
| `dcaegen2-services`  | ~16.x-0 | No              |
| `mariadb-galera`     | ~16.x-0 | No              |
| `multicloud`         | ~15.x-0 | No              |
| `platform`           | ~13.x-0 | No              |
| `policy`             | ~17.x-0 | No              |
| `portal-ng`          | ~14.x-0 | No              |
| `postgres`           | ~13.x-0 | No              |
| `repository-wrapper` | ~13.x-0 | Yes             |
| `robot`              | ~13.x-0 | No              |
| `roles-wrapper`      | ~13.x-0 | Yes             |
| `sdc`                | ~13.x-0 | No              |
| `sdnc`               | ~16.x-0 | No              |
| `so`                 | ~16.x-0 | No              |
| `strimzi`            | ~16.x-0 | No              |
| `uui`                | ~16.x-0 | No              |

### 16.2 Docker Images (94 ONAP-specific)

See the `data/image_repo_mapping.yaml` section above for the complete list
of 94 `onap/*` Docker images and their mapped Gerrit projects.

### 16.3 Estimated Repository Count by Category

<!-- markdownlint-disable MD013 -->

| Category                                      | Count       | Source           |
| --------------------------------------------- | ----------- | ---------------- |
| Runtime (produce Docker images)               | ~50-60      | OOM collector    |
| Build dependencies (parent POMs, shared libs) | ~15-20      | JJB collector    |
| Infrastructure (OOM, CI, integration)         | ~10-15      | Known list       |
| Test/demo                                     | ~10-15      | Integration CSVs |
| Documentation                                 | ~3-5        | Known list       |
| **Total estimated**                           | **~90-110** |                  |

<!-- markdownlint-enable MD013 -->

---

## 17. Glossary

<!-- markdownlint-disable MD013 -->

| Term           | Definition                                                         |
| -------------- | ------------------------------------------------------------------ |
| **OOM**        | ONAP Operations Manager — Helm-based K8s deployment system         |
| **JJB**        | Jenkins Job Builder — YAML-driven Jenkins job definitions          |
| **Gerrit**     | Code review and Git hosting platform used by ONAP                  |
| **Relman**     | Release Management project in ONAP Gerrit                          |
| **Nexus3**     | Sonatype Nexus3 artifact repository hosting Docker images          |
| **Collector**  | A plugin module that gathers data from a specific source           |
| **Manifest**   | The JSON output artifact describing a release's components         |
| **Confidence** | How certain we are that a repo is in the release (high/medium/low) |
| **Rabat**      | Current ONAP release code name (chart version 18.0.0)              |

<!-- markdownlint-enable MD013 -->

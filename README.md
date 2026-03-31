<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# onap-release-map

ONAP release component mapping tool — generates definitive manifests of
Gerrit projects and Docker images comprising an ONAP release.

## Overview

`onap-release-map` follows an **OOM-first** strategy: it starts from the
OOM Helm umbrella chart, recursively resolves every sub-chart and Docker
image reference, then maps those images back to their source Gerrit
repositories.

The tool produces a **versioned, self-describing JSON artifact** that
captures the complete state of the analysis.

## Installation

```shell
pip install onap-release-map
```

Or install from source:

```shell
git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
cd onap-release-mapping-tool
pip install -e ".[dev]"
```

## Quick Start

```shell
# Clone the OOM repository
git clone https://gerrit.onap.org/r/oom

# Generate the release manifest
onap-release-map discover --oom-path ./oom
```

## Commands

<!-- markdownlint-disable MD013 -->

| Command    | Description                                        |
| ---------- | -------------------------------------------------- |
| `discover` | Parse OOM charts and generate the release manifest |
| `diff`     | Compare two manifests and report differences       |
| `validate` | Validate Docker images exist in the Nexus registry |
| `export`   | Convert a manifest to CSV, YAML, or Markdown       |
| `schema`   | Print the JSON Schema for the manifest format      |
| `version`  | Print version information                          |

<!-- markdownlint-enable MD013 -->

## Development

```shell
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check src/ tests/
```

## License

[Apache-2.0](LICENSE)
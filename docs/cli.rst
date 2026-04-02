.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

=============
CLI Reference
=============

The ``onap-release-map`` command-line interface uses
`Typer <https://typer.tiangolo.com/>`_ and provides subcommands for
generating, comparing, exporting, and validating ONAP release manifests.

.. typer:: onap_release_map.cli:app
   :prog: onap-release-map
   :show-nested:

Command Overview
================

.. list-table::
   :header-rows: 1
   :widths: 15 55

   * - Command
     - Description
   * - ``discover``
     - Parse OOM Helm charts and generate the release manifest
   * - ``diff``
     - Compare two manifests and report differences
   * - ``export``
     - Convert a manifest to CSV, YAML, Markdown, or Gerrit list
   * - ``verify``
     - Check Docker image existence in the Nexus registry
   * - ``schema``
     - Print the JSON Schema for the manifest format
   * - ``version``
     - Print version information

discover
--------

The ``discover`` command is the primary entry point. It parses OOM Helm
charts, resolves Docker image references, and maps images back to their
source Gerrit repositories.

.. code-block:: shell

   # Basic usage with a local OOM clone
   onap-release-map discover --oom-path ./oom

   # Specify release name and output directory
   onap-release-map discover \
       --oom-path ./oom \
       --release-name Rabat \
       --output-dir ./output

   # Run two collectors together
   onap-release-map discover \
       --oom-path ./oom \
       --collectors oom,gerrit

   # Use a custom configuration file
   onap-release-map discover \
       --oom-path ./oom \
       --config configuration/default.yaml

diff
----

The ``diff`` command compares two existing manifests and produces a
structured report of changes between them.

.. code-block:: shell

   # Text diff (default)
   onap-release-map diff manifest-a.json manifest-b.json

   # Markdown diff written to file
   onap-release-map diff manifest-a.json manifest-b.json \
       --output-format md --output diff-report.md

   # JSON diff ignoring timestamp differences
   onap-release-map diff manifest-a.json manifest-b.json \
       --output-format json --ignore-timestamps

export
------

The ``export`` command converts a JSON manifest into alternative
output formats.

.. code-block:: shell

   # Export as YAML
   onap-release-map export manifest.json --format yaml

   # Export as CSV
   onap-release-map export manifest.json --format csv

   # Export as Markdown report
   onap-release-map export manifest.json --format md --output report.md

   # Export Gerrit project list
   onap-release-map export manifest.json --format gerrit-list

verify
------

The ``verify`` command checks that Docker images referenced in a
manifest actually exist in the ONAP Nexus registry.

.. code-block:: shell

   # Verify all images against default Nexus URL
   onap-release-map verify manifest.json

   # Specify a custom Nexus URL and worker count
   onap-release-map verify manifest.json \
       --nexus-url https://nexus3.onap.org \
       --workers 8

schema
------

The ``schema`` command prints the JSON Schema that describes the
manifest format.

.. code-block:: shell

   onap-release-map schema

version
-------

The ``version`` command prints the tool version and Python version.

.. code-block:: shell

   onap-release-map version

Global Options
==============

``--version`` / ``-V``
   Show the tool version and exit.

``--help``
   Show help text and exit. Works on any subcommand as well.

Exit Codes
==========

.. list-table::
   :header-rows: 1
   :widths: 10 60

   * - Code
     - Meaning
   * - ``0``
     - Success
   * - ``1``
     - Runtime error (missing files, invalid input, network failure)
   * - ``2``
     - CLI usage error (invalid arguments or options)
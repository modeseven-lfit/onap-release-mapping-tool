.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

=====
Usage
=====

This guide demonstrates common workflows with ``onap-release-map``.

Generating a Release Manifest
=============================

The ``discover`` command is the primary entry point.  It parses the OOM
Helm umbrella chart, resolves every sub-chart and Docker image reference,
then maps images back to their source Gerrit repositories.

Basic Discovery
---------------

Clone the OOM repository and point the tool at it:

.. code-block:: console

   $ git clone --depth 1 https://gerrit.onap.org/r/oom
   $ onap-release-map discover --oom-path ./oom

By default the tool writes the manifest to ``./output/manifest.json``.

Specifying a Release Name
-------------------------

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --release-name Rabat

Choosing an Output Directory
-----------------------------

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --output-dir ./output

Output Format Options
---------------------

Request JSON and YAML manifests simultaneously:

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --output-format all

Combining Collectors
--------------------

Combine the OOM collector with the Gerrit collector for richer metadata:

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --collectors oom,gerrit

Available collectors: ``oom``, ``gerrit``, ``relman``, ``jjb``.

Custom Image-to-Repo Mapping
-----------------------------

Override the built-in image-to-repository mapping with a custom YAML
file:

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --mapping-file ./my-mappings.yaml

Verbose Output
--------------

Increase verbosity for debugging.  Use ``-v`` for info-level logging or
``-vv`` for debug-level:

.. code-block:: console

   $ onap-release-map discover --oom-path ./oom -vv

Diffing Manifests
=================

The ``diff`` command compares two manifests and reports additions,
removals, and changes across repositories, Docker images, and Helm
components.

Plain Text Diff
---------------

.. code-block:: console

   $ onap-release-map diff old-manifest.json new-manifest.json

JSON Diff
---------

.. code-block:: console

   $ onap-release-map diff \
       old-manifest.json new-manifest.json \
       --output-format json

Markdown Diff
-------------

.. code-block:: console

   $ onap-release-map diff \
       old-manifest.json new-manifest.json \
       --output-format md \
       --output diff-report.md

Ignoring Timestamps
-------------------

Ignore the ``generated_at`` field when comparing manifests that the tool
generated at different times but that should otherwise be identical:

.. code-block:: console

   $ onap-release-map diff \
       old-manifest.json new-manifest.json \
       --ignore-timestamps

Exporting Formats
=================

The ``export`` command converts a JSON manifest into alternative output
formats.

YAML Export
-----------

.. code-block:: console

   $ onap-release-map export manifest.json --format yaml

CSV Export
----------

Export the repository list as CSV:

.. code-block:: console

   $ onap-release-map export manifest.json --format csv

Markdown Report
---------------

.. code-block:: console

   $ onap-release-map export manifest.json \
       --format md --output report.md

Gerrit Project List
-------------------

Produce a plain-text list of Gerrit project paths, one per line.  This
format is compatible with the ``projects.txt`` convention used by ONAP
integration scripts:

.. code-block:: console

   $ onap-release-map export manifest.json --format gerrit-list

Writing to a File
-----------------

All export commands accept ``--output`` to write to a file instead of
stdout:

.. code-block:: console

   $ onap-release-map export manifest.json \
       --format yaml --output manifest.yaml

Verifying Docker Images
=======================

The ``verify`` command checks whether Docker images listed in a manifest
actually exist in the Nexus registry.

Basic Verification
------------------

.. code-block:: console

   $ onap-release-map verify manifest.json

Custom Nexus URL
----------------

.. code-block:: console

   $ onap-release-map verify manifest.json \
       --nexus-url https://nexus3.onap.org

Adjusting Concurrency
---------------------

Control the number of concurrent validation workers:

.. code-block:: console

   $ onap-release-map verify manifest.json --workers 8

Using Configuration Files
=========================

Instead of passing every option on the command line you can use a YAML
configuration file.

.. code-block:: console

   $ onap-release-map discover \
       --oom-path ./oom \
       --config ./configuration/default.yaml

See :doc:`configuration` for the full reference.

Using as a GitHub Action
========================

The repository ships a composite GitHub Action that automates manifest
generation in CI/CD pipelines.

Minimal Workflow
----------------

.. code-block:: yaml

   name: Generate ONAP manifest
   on:
     workflow_dispatch:

   jobs:
     manifest:
       runs-on: ubuntu-latest
       timeout-minutes: 30
       steps:
         - name: Checkout action
           uses: actions/checkout@v4
           with:
             repository: modeseven-lfit/onap-release-mapping-tool

         - name: Generate manifest
           id: manifest
           uses: ./
           with:
             release-name: Rabat

         - name: Show results
           run: |
             echo "Repositories: ${{ steps.manifest.outputs.total-repositories }}"
             echo "Images: ${{ steps.manifest.outputs.total-images }}"

Action Inputs
-------------

.. list-table::
   :header-rows: 1
   :widths: 20 50 10 20

   * - Input
     - Description
     - Required
     - Default
   * - ``oom-path``
     - Path to a pre-cloned OOM repository
     - No
     - *(clones from Gerrit)*
   * - ``oom-branch``
     - OOM branch to analyse
     - No
     - ``master``
   * - ``gerrit-url``
     - Gerrit base URL
     - No
     - ``https://gerrit.onap.org/r``
   * - ``collectors``
     - Comma-separated collector list
     - No
     - ``oom,gerrit``
   * - ``output-dir``
     - Output directory
     - No
     - ``$RUNNER_TEMP``
   * - ``output-format``
     - Output formats (``json``, ``yaml``, ``all``)
     - No
     - ``json``
   * - ``release-name``
     - ONAP release code name
     - No
     - ``Rabat``
   * - ``mapping-file``
     - Custom image-to-repo mapping YAML
     - No
     - *(none)*
   * - ``python-version``
     - Python version to use
     - No
     - ``3.12``

Action Outputs
--------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Output
     - Description
   * - ``manifest-path``
     - Path to the generated JSON manifest
   * - ``manifest-version``
     - Schema version of the generated manifest
   * - ``total-repositories``
     - Number of repositories found
   * - ``total-images``
     - Number of Docker images found
   * - ``onap-release``
     - ONAP release name

The action also uploads the output directory as a build artifact named
``onap-release-manifest`` with a 90-day retention period.
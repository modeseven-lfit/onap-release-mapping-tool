.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

===========================
ONAP Release Mapping Tool
===========================

**onap-release-map** generates definitive manifests of Gerrit projects and
Docker images comprising an ONAP release.  It follows an **OOM-first**
strategy: starting from the OOM Helm umbrella chart, it recursively resolves
every sub-chart and Docker image reference, then maps those images back to
their source Gerrit repositories.

The tool produces a **versioned, self-describing JSON artifact** that captures
the complete state of the analysis.

Features
--------

- Discover ONAP components from OOM Helm charts
- Map Docker images to their source Gerrit repositories
- Diff two release manifests to track changes between releases
- Export manifests to CSV, YAML, Markdown, or Gerrit project lists
- Verify Docker image existence against the Nexus registry
- Run as a CLI tool or as a GitHub Action

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   cli
   configuration
   api/index
   contributing
   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

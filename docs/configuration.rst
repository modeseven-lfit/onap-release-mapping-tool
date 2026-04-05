.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

Configuration
=============

``onap-release-map`` supports configuration through YAML files and
command-line options. Command-line options take precedence over
configuration file values, which in turn take precedence over built-in
defaults.

Configuration File
------------------

Pass a configuration file to the ``discover`` command with the
``--config`` option:

.. code-block:: shell

   onap-release-map discover --config myconfig.yaml --oom-path ./oom

The tool ships with a default configuration embedded in the package. A
reference copy is available in the repository at
``configuration/default.yaml``.

Default Configuration
---------------------

.. code-block:: yaml

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

   # Repository filtering — repos excluded from reports
   filter_repos:
     - ".github"
     - "All-Projects"
     - "All-Users"
     # JJB CI job definitions for the ONAP Jenkins instance
     - "ci-management"

   # Exclude read-only/archived Gerrit projects
   exclude_readonly: true

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
     max_retries: 3
     concurrent_workers: 4

   # Logging
   logging:
     level: "INFO"
     format: "rich"

Configuration Keys
------------------

Gerrit Settings
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``gerrit.url``
     - ``https://gerrit.onap.org/r``
     - Base URL of the ONAP Gerrit server.
   * - ``gerrit.timeout``
     - ``30``
     - HTTP request timeout in seconds for Gerrit API calls.
   * - ``gerrit.max_retries``
     - ``3``
     - Max number of retry attempts for failed Gerrit requests.

OOM Settings
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``oom.default_branch``
     - ``master``
     - Default Git branch to use when cloning or analysing OOM.
   * - ``oom.remote_url``
     - ``https://gerrit.onap.org/r/oom``
     - Remote URL used to clone the OOM repository when the user
       does not supply a local path.
   * - ``oom.exclude_dirs``
     - ``["argo", "archive"]``
     - List of top-level directories inside the OOM ``kubernetes/``
       tree to skip during chart discovery.

Collectors
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``collectors``
     - ``["oom"]``
     - List of collector names to run. Available collectors:
       ``oom``, ``gerrit``, ``relman``, ``jjb``.

Filtering Settings
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``filter_repos``
     - ``[".github", "All-Projects", "All-Users", "ci-management"]``
     - List of Gerrit project names to exclude from exported
       reports. Infrastructure repositories and projects that do
       not contain runtime release content (such as
       ``ci-management``, which holds JJB CI job definitions for
       the ONAP Jenkins instance) are excluded by default.
       Override via the ``--filter-repos`` CLI flag or a custom
       config file.
   * - ``exclude_readonly``
     - ``true``
     - When enabled, repositories in ``READ_ONLY`` state are
       removed from exported reports. Override with
       ``--no-exclude-readonly``.

Output Settings
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``output.formats``
     - ``["json"]``
     - List of output formats to generate. Supported values:
       ``json``, ``yaml``.
   * - ``output.deterministic``
     - ``true``
     - When enabled, the tool truncates timestamps to whole seconds
       and sorts output for reproducible builds.
   * - ``output.pretty_print``
     - ``true``
     - Pretty-print JSON output with indentation.
   * - ``output.indent``
     - ``2``
     - Number of spaces for JSON indentation.

Nexus Settings
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``nexus.url``
     - ``https://nexus3.onap.org``
     - Base URL of the Nexus 3 Docker registry used for image
       verification.
   * - ``nexus.timeout``
     - ``10``
     - HTTP request timeout in seconds for Nexus API calls.
   * - ``nexus.max_retries``
     - ``3``
     - Max number of attempts per image validation request.
       Retries occur on network errors and HTTP 500+ responses,
       with a 1-second delay between attempts.
   * - ``nexus.concurrent_workers``
     - ``4``
     - Number of concurrent threads used when verifying Docker
       images against the registry.

Logging Settings
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``logging.level``
     - ``INFO``
     - Default log level. Overridden by the ``-v`` / ``-vv``
       command-line flags.
   * - ``logging.format``
     - ``rich``
     - Log output format. The tool supports ``rich`` as the sole
       format.

Example Configurations
----------------------

Minimal Configuration
~~~~~~~~~~~~~~~~~~~~~

A minimal configuration that changes the release branch:

.. code-block:: yaml

   oom:
     default_branch: "oslo"

Multi-Collector Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable extra collectors and increase Gerrit timeout for slow
connections:

.. code-block:: yaml

   gerrit:
     url: "https://gerrit.onap.org/r"
     timeout: 60
     max_retries: 5

   collectors:
     - oom
     - gerrit
     - relman

   output:
     formats:
       - json
       - yaml
     deterministic: true

CI/CD Configuration
~~~~~~~~~~~~~~~~~~~

A configuration suitable for automated pipelines with all outputs
enabled and higher concurrency:

.. code-block:: yaml

   collectors:
     - oom
     - gerrit

   output:
     formats:
       - json
       - yaml
     deterministic: true
     pretty_print: true

   nexus:
     concurrent_workers: 8
     timeout: 15

   logging:
     level: "WARNING"

Configuration Merging
---------------------

When the user supplies a configuration file, its values are
**deep-merged** with the built-in defaults. This means you need to
specify the keys you want to override — all other values keep their
defaults.

For example, if your configuration file contains:

.. code-block:: yaml

   gerrit:
     timeout: 60

The resulting effective configuration will still include
``gerrit.url``, ``gerrit.max_retries``, and all other default values.
The tool overrides ``gerrit.timeout`` to ``60`` and nothing else.

List values (such as ``collectors``, ``filter_repos``, and
``oom.exclude_dirs``) are **replaced** entirely rather than merged.
If you specify ``collectors: [oom, gerrit]`` in your file, it replaces
the default ``[oom]`` rather than appending to it.
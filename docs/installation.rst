.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

============
Installation
============

Requirements
------------

- Python 3.10 or later
- Git (for source installation and OOM repository cloning)

From PyPI
---------

Install the latest release from PyPI:

.. code-block:: shell

   pip install onap-release-map

From Source
-----------

Clone the repository and install with ``uv``:

.. code-block:: shell

   git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
   cd onap-release-mapping-tool
   uv sync

Or install with ``pip``:

.. code-block:: shell

   git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
   cd onap-release-mapping-tool
   pip install .

Development Installation
------------------------

For development, install with the ``dev`` extras to include testing and
linting dependencies:

.. code-block:: shell

   git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
   cd onap-release-mapping-tool
   uv sync --group dev

Or using ``pip``:

.. code-block:: shell

   pip install -e ".[dev]"

This installs:

- **pytest** — test framework
- **pytest-mock** — mocking utilities
- **pytest-cov** — coverage reporting
- **respx** — HTTP request mocking for httpx
- **mypy** — static type checking
- **types-PyYAML** — type stubs for PyYAML

Verifying the Installation
--------------------------

After installation, verify the tool is available:

.. code-block:: shell

   onap-release-map version

You should see the tool version and Python version printed to the
console.

Runtime Dependencies
--------------------

The tool pulls in the following packages automatically:

- **typer** — CLI framework
- **rich** — terminal formatting and progress display
- **pydantic** — data validation and settings management
- **httpx** — async-capable HTTP client
- **pyyaml** — YAML parsing
- **jsonschema** — JSON Schema validation
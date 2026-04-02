.. SPDX-FileCopyrightText: 2025 The Linux Foundation
.. SPDX-License-Identifier: Apache-2.0

Contributing
============

Thank you for your interest in contributing to **onap-release-map**! This
guide covers the development workflow, coding standards, and submission
process.

Development Setup
-----------------

1. Clone the repository:

   .. code-block:: shell

      git clone https://github.com/modeseven-lfit/onap-release-mapping-tool.git
      cd onap-release-mapping-tool

2. Install `uv <https://docs.astral.sh/uv/>`_ (if not already available):

   .. code-block:: shell

      curl -LsSf https://astral.sh/uv/install.sh | sh

3. Create a virtual environment and install all dependencies:

   .. code-block:: shell

      uv sync --all-extras

4. Install the pre-commit hooks:

   .. code-block:: shell

      uv run pre-commit install

Running Tests
-------------

The test suite uses **pytest** with coverage reporting:

.. code-block:: shell

   # Run the full test suite
   uv run pytest tests/

   # Run tests with short output, stop on first failure
   uv run pytest tests/ -x -q

   # Run a specific test file
   uv run pytest tests/test_exporter.py

   # Run tests matching a keyword
   uv run pytest tests/ -k "test_diff"

Coverage reports are generated in ``htmlcov/`` by default.

Code Style
----------

This project uses `Ruff <https://docs.astral.sh/ruff/>`_ for both linting
and formatting. The configuration lives in ``pyproject.toml``.

.. code-block:: shell

   # Check for lint errors
   uv run ruff check src/ tests/

   # Auto-fix lint errors where possible
   uv run ruff check --fix src/ tests/

   # Format code
   uv run ruff format src/ tests/

Type checking is performed by **mypy** and **basedpyright**:

.. code-block:: shell

   uv run mypy src/
   uv run basedpyright src/

Docstring Coverage
^^^^^^^^^^^^^^^^^^

All public modules, classes, and functions must have docstrings. The project
uses **Google-style** docstrings:

.. code-block:: python

   def export_manifest(manifest: ReleaseManifest, fmt: str) -> str:
       """Export a manifest in the requested format.

       Args:
           manifest: The release manifest to export.
           fmt: Output format name (yaml, csv, md, gerrit-list).

       Returns:
           Formatted output string.

       Raises:
           ExportError: If the format is not recognised.
       """

Commit Message Format
---------------------

This project follows `Conventional Commits`_ with **capitalised type
prefixes** and the `seven rules of a great Git commit message`_.

.. _Conventional Commits: https://www.conventionalcommits.org/
.. _seven rules of a great Git commit message: https://chris.beams.io/posts/git-commit/

Format
^^^^^^

.. code-block:: text

   Type(scope): Short imperative description

   Body explaining what and why. Wrap at 72 characters.

   Co-authored-by: Name <email>
   Signed-off-by: Your Name <your-email@example.com>

Allowed Types
^^^^^^^^^^^^^

``Fix``, ``Feat``, ``Chore``, ``Docs``, ``Style``, ``Refactor``,
``Perf``, ``Test``, ``Revert``, ``CI``, ``Build``

Rules
^^^^^

- Subject line must be **50 characters or fewer**.
- Subject must start with a **capitalised** Conventional Commit type.
- Subject must use the **imperative mood** ("Add feature", not "Added
  feature").
- Subject must **not** end with a period.
- Body lines must wrap at **72 characters** (URLs are exempt).
- Always sign off with ``-s`` for the Developer Certificate of Origin.

Example:

.. code-block:: shell

   git commit -s -m "Feat(export): Add CSV image-mode export

   Adds a new 'images' mode to the CSV exporter so users can
   export Docker image inventories alongside repository lists.

   Co-authored-by: Claude <noreply@anthropic.com>"

Pre-commit Hooks
----------------

The repository uses `pre-commit <https://pre-commit.com/>`_ to enforce
quality gates before every commit. Hooks include:

- **gitlint** — commit message format validation
- **reuse** — SPDX license header compliance
- **ruff** — Python linting and formatting
- **mypy** — Python type checking
- **yamllint** — YAML linting
- **actionlint** — GitHub Actions workflow validation
- **codespell** — spell checking
- **basedpyright** — advanced type checking
- **markdownlint** — Markdown linting

If a commit fails due to a pre-commit hook:

1. Fix the issues reported by the hook.
2. Stage the fixes with ``git add``.
3. Run the commit command again.

.. warning::

   **Never** use ``git commit --no-verify`` to bypass hooks, and
   **never** use ``git reset`` after a failed commit attempt.

License Headers (SPDX)
-----------------------

All new source files **must** include SPDX license headers. For Python
files:

.. code-block:: python

   # SPDX-FileCopyrightText: 2025 The Linux Foundation
   # SPDX-License-Identifier: Apache-2.0

For reStructuredText files:

.. code-block:: rst

   .. SPDX-FileCopyrightText: 2025 The Linux Foundation
   .. SPDX-License-Identifier: Apache-2.0

Some file types (test fixtures, lock files, documentation assets) are
covered by ``REUSE.toml`` and do not require inline headers. Check
``REUSE.toml`` for the full list of glob patterns.

You can verify compliance locally:

.. code-block:: shell

   uv run reuse lint

Pull Request Process
--------------------

1. Create a feature branch from ``main``.
2. Make your changes in atomic commits (one logical change per commit).
3. Ensure all tests pass and pre-commit hooks are satisfied.
4. Push your branch and open a pull request.
5. Respond to review feedback and update your branch as needed.

Each commit in the pull request should be independently valid — avoid
"fixup" or "WIP" commits in the final history.
# SPDX-FileCopyrightText: 2025 The Linux Foundation
# SPDX-License-Identifier: Apache-2.0

"""Sphinx configuration for onap-release-map documentation."""

import os
import sys

# Make the src/ layout importable for autodoc in local builds.
# On Read the Docs the package is installed via pip (see .readthedocs.yml),
# so this fallback only matters when running sphinx-build locally without
# installing the package first.
sys.path.insert(0, os.path.abspath(os.path.join("..", "src")))

# -- Project information -----------------------------------------------------

project = "onap-release-map"
copyright = "2025, The Linux Foundation"  # noqa: A001
author = "The Linux Foundation"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.typer",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "ONAP-RELEASE-TOOL-PLAN.md",
    "Release tool prompts.txt",
]

# Support both reStructuredText and Markdown sources
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}

# -- Extension configuration -------------------------------------------------

# Intersphinx: link to external project documentation
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "httpx": ("https://www.python-httpx.org/", None),
}

# Napoleon: support Google-style docstrings
napoleon_google_docstrings = True
napoleon_numpy_docstrings = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc configuration
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"

# Use importlib for modern autodoc module loading
autodoc_class_signature = "separated"

# sphinx-autodoc-typehints
always_document_param_types = True
typehints_defaults = "comma"

# MyST parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 3

# Suppress warnings for cross-reference ambiguity and duplicate object
# descriptions.  These arise because Pydantic models are re-exported
# from ``onap_release_map.models.__init__`` and also documented in
# their canonical submodule locations, and because Pydantic Field()
# descriptors are emitted by both autodoc and sphinx-autodoc-typehints.
suppress_warnings = [
    "ref.python",
    "py.duplicate",
    "toc.not_included",
]

# Deduplicate Pydantic model attribute entries across package re-exports
# and submodule definitions by allowing overwrites in the object inventory.
toc_object_entries_show_parents = "hide"

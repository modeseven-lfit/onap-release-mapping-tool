# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""ONAP release component mapping tool."""

try:
    from ._version import __version__
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    try:
        from importlib.metadata import version as _get_version

        __version__ = _get_version("onap-release-map")
    except Exception:
        __version__ = "0.0.0"

__all__ = ["__version__"]

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Configuration loading and merging for onap-release-map."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from onap_release_map.parsers.yaml_utils import safe_load_yaml

logger = logging.getLogger(__name__)

__all__ = [
    "DEFAULTS",
    "load_config",
]

# Default configuration values
DEFAULTS: dict[str, Any] = {
    "gerrit": {
        "url": "https://gerrit.onap.org/r",
        "timeout": 30,
        "max_retries": 3,
    },
    "oom": {
        "default_branch": "master",
        "remote_url": "https://gerrit.onap.org/r/oom",
        "exclude_dirs": ["argo", "archive"],
    },
    "collectors": ["oom"],
    "output": {
        "formats": ["json"],
        "deterministic": True,
        "pretty_print": True,
        "indent": 2,
    },
    "nexus": {
        "url": "https://nexus3.onap.org",
        "timeout": 10,
        "concurrent_workers": 4,
    },
    "logging": {
        "level": "INFO",
        "format": "rich",
    },
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and merge configuration.

    Loads the default configuration, then overlays values from the
    user-specified config file if provided.

    Args:
        config_path: Optional path to a YAML configuration file.

    Returns:
        Merged configuration dictionary.
    """
    config = _deep_copy_dict(DEFAULTS)

    if config_path is not None:
        if config_path.exists():
            user_config = safe_load_yaml(config_path)
            config = _deep_merge(config, user_config)
            logger.info("Loaded configuration from %s", config_path)
        else:
            logger.warning("Config file not found: %s", config_path)

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base, returning a new dict."""
    result = _deep_copy_dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _deep_copy_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Deep copy a dict of simple types."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            result[key] = list(value)
        else:
            result[key] = value
    return result

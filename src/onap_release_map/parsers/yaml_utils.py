# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Safe YAML loading utilities."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def safe_load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file safely.

    Args:
        path: Path to the YAML file to load.

    Returns:
        Parsed YAML content as a dictionary. Returns an empty dict
        on read errors or parse failures.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Cannot read YAML file %s: %s", path, exc)
        return {}
    return safe_load_yaml_string(content)


def safe_load_yaml_string(content: str) -> dict[str, Any]:
    """Load YAML from a string.

    Args:
        content: YAML content as a string.

    Returns:
        Parsed YAML content as a dictionary. Returns an empty dict
        when the content is empty or cannot be parsed.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        logger.warning("YAML parse error: %s", exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return data

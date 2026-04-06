# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Safe YAML loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class _PermissiveSafeLoader(yaml.SafeLoader):
    """yaml.SafeLoader variant that silently accepts duplicate anchors.

    PyYAML >= 6.0 raises ``ComposerError`` when it encounters an anchor
    name that was already defined in the same document.  Real-world ONAP
    YAML files sometimes reuse anchor names, so this loader tolerates
    duplicates by letting the last definition win for subsequent alias
    references.
    """

    def compose_node(self, parent: Any, index: Any) -> Any:
        """Compose a YAML node, allowing duplicate anchor names."""
        if self.check_event(yaml.AliasEvent):
            event = self.get_event()
            anchor = event.anchor
            if anchor not in self.anchors:
                raise yaml.composer.ComposerError(
                    None,
                    None,
                    f"found undefined alias {anchor!r}",
                    event.start_mark,
                )
            return self.anchors[anchor]

        event = self.peek_event()
        anchor = event.anchor

        # Remove a previously seen anchor so the parent class does not
        # raise ComposerError for the duplicate.  The downstream
        # compose_*_node call will re-register the anchor, making the
        # last definition win.
        if anchor is not None and anchor in self.anchors:
            del self.anchors[anchor]

        return super().compose_node(parent, index)


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
    return safe_load_yaml_string(content, source=str(path))


def safe_load_yaml_string(
    content: str,
    source: str = "<string>",
) -> dict[str, Any]:
    """Load YAML from a string.

    Args:
        content: YAML content as a string.
        source:  Optional label included in warning messages to
                 identify where the content originated (e.g. a file
                 path).  Defaults to ``"<string>"``.

    Returns:
        Parsed YAML content as a dictionary. Returns an empty dict
        when the content is empty or cannot be parsed.
    """
    try:
        data = yaml.load(content, Loader=_PermissiveSafeLoader)  # noqa: S506
    except yaml.YAMLError as exc:
        logger.warning("YAML parse error in %s: %s", source, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return data

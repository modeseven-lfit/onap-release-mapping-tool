# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Custom exception hierarchy for onap-release-map."""

__all__ = [
    "CollectorError",
    "ConfigurationError",
    "ExportError",
    "MappingError",
    "OnapReleaseMapError",
    "ParserError",
    "SchemaError",
]


class OnapReleaseMapError(Exception):
    """Base exception for all onap-release-map errors."""


class ConfigurationError(OnapReleaseMapError):
    """Invalid or missing configuration."""


class CollectorError(OnapReleaseMapError):
    """Error during data collection."""


class ParserError(OnapReleaseMapError):
    """Error parsing data files (Helm charts, YAML, etc.)."""


class MappingError(OnapReleaseMapError):
    """Error in image-to-repository mapping."""


class SchemaError(OnapReleaseMapError):
    """Error validating manifest against schema."""


class ExportError(OnapReleaseMapError):
    """Error exporting manifest to output format."""

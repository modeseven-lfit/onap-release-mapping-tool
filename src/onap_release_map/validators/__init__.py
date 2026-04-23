# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Post-collection validators for manifest data quality.

Validators run after all collectors have completed and the manifest
has been built. They examine the final manifest for data-quality
issues (stale overrides, unverified heuristic fallbacks, orphan
mappings, ambiguous leaf matches, etc.) and produce a structured
report that is embedded in the manifest output.

Unlike collectors, validators are read-only with respect to the
manifest content — they may append findings to a dedicated report
section but must not mutate repositories, images, or components.

The report data models (:class:`ValidationFinding`,
:class:`ValidationReport`, and the supporting enums) live under
``onap_release_map.models.validation`` so the manifest schema can
reference them without creating a circular import between the
``models`` and ``validators`` packages. They are re-exported here
for convenience so callers that only interact with validators do
not have to reach into ``models``.
"""

from onap_release_map.models.validation import (
    ValidationCategory,
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
)

from .mapping_audit import MappingAuditValidator

__all__ = [
    "MappingAuditValidator",
    "ValidationCategory",
    "ValidationFinding",
    "ValidationReport",
    "ValidationSeverity",
]

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Pydantic models for post-collection validation reports.

These models describe the shape of validator output that is embedded
in the release manifest under the ``validation`` field. Keeping the
schema definitions in the ``models`` package (rather than alongside
validator logic) avoids circular imports between ``models`` and
``validators``, and matches the existing convention that all manifest
schema lives under ``models``.

The data types here are deliberately validator-agnostic: any future
validator that wants to contribute findings to the manifest can reuse
:class:`ValidationFinding` and :class:`ValidationReport` without
needing to modify the manifest schema.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity classification for a single validation finding.

    Values are strings so they serialise cleanly into JSON / YAML
    manifest output and can be grouped or filtered by consumers.
    """

    ERROR = "error"
    """Definitively wrong: blocks CI when ``--strict-validation`` is on."""

    WARNING = "warning"
    """Likely wrong or ambiguous: surfaces for human review."""

    INFO = "info"
    """Informational only: recorded for audit but not acted upon."""


class ValidationCategory(str, Enum):
    """Classification of a mapping audit finding.

    Categories are orthogonal to severity — the same category can
    produce different severities depending on context. New categories
    may be added over time but existing ones must not change meaning,
    as they are part of the manifest schema.
    """

    STALE_OVERRIDE = "stale_override"
    """Explicit override resolves to a repo not present in Gerrit."""

    STALE_OVERRIDE_WITH_FIX = "stale_override_with_fix"
    """Stale override that the mapper superseded with a verified replacement.

    Fires when the manifest records the stale override's target
    verbatim but a fresh resolve produces a different, verified
    project. The replacement is typically deeper than the override
    (that is how longest-match bypasses the override in the first
    place) but depth is not enforced: any verified replacement counts,
    including same-depth cross-namespace leaf matches. Distinct from
    :attr:`STALE_OVERRIDE`, which fires when no replacement was found
    and the stale value still stands.
    """

    OVERRIDE_SHADOWED = "override_shadowed"
    """Manifest mapping differs from the repo selected by a fresh resolve.

    Surfaced when the value recorded in the manifest under audit does
    not match the project that :class:`ImageMapper.resolve` would
    produce today. Causes include drift between collection and audit
    time, manual edits to a manifest, or an earlier tool version that
    chose a different candidate.
    """

    HEURISTIC_UNVERIFIED = "heuristic_unverified"
    """Mapping resolved via heuristic whose output is not in Gerrit."""

    AMBIGUOUS_LEAF = "ambiguous_leaf"
    """Multiple Gerrit repos share the image leaf; one was chosen."""

    CROSS_NAMESPACE_FALLBACK = "cross_namespace_fallback"
    """Leaf match had to cross top-level namespaces to find a repo."""

    UNRESOLVED = "unresolved"
    """Image could not be mapped to any Gerrit project."""

    AUDIT_SKIPPED = "audit_skipped"
    """Validator could not audit because prerequisites were missing.

    Emitted, for example, when Gerrit ground truth is unavailable
    (the ``gerrit`` collector was disabled) and the mapping audit
    cannot verify any resolution. Distinct from :attr:`UNRESOLVED`,
    which signals that a specific image could not be mapped despite
    ground truth being present.
    """


class ValidationFinding(BaseModel):
    """A single audit finding produced by a validator.

    Each finding records what was observed, what the validator would
    suggest instead (when applicable), and enough provenance for a
    reviewer to reproduce the decision without re-running the tool.
    """

    category: ValidationCategory
    """Classification of the finding."""

    severity: ValidationSeverity
    """How serious the finding is."""

    image: str | None = None
    """Docker image reference the finding concerns, if applicable."""

    current_mapping: str | None = None
    """Gerrit project path the manifest currently records."""

    suggested_mapping: str | None = None
    """Alternative mapping the validator recommends, when known."""

    reason: str
    """Human-readable explanation of the finding."""

    alternatives: list[str] = Field(default_factory=list)
    """Other plausible candidates considered during resolution."""

    detail: dict[str, str] = Field(default_factory=dict)
    """Optional free-form detail fields for category-specific context."""


class ValidationReport(BaseModel):
    """Aggregated output of a validator run.

    Attributes:
        validator: Identifier of the validator that produced the
            report (e.g. ``"mapping_audit"``).
        passed: ``True`` when the report contains no ``ERROR``-level
            findings.
        summary: Human-readable one-line summary suitable for CLI
            output.
        counts: Per-severity and per-category counts for quick
            stats without iterating ``findings``.
        findings: Ordered list of findings (errors first, then
            warnings, then info; within each severity group sorted
            by category then image).
    """

    validator: str
    """Identifier of the validator that produced the report."""

    passed: bool
    """``True`` when the report contains no ERROR-level findings."""

    summary: str
    """Human-readable one-line summary suitable for CLI output."""

    counts: dict[str, int] = Field(default_factory=dict)
    """Per-severity and per-category counts keyed as ``severity:NAME``
    and ``category:NAME`` for quick stats without iterating findings."""

    findings: list[ValidationFinding] = Field(default_factory=list)
    """Ordered list of findings: errors first, then warnings, then
    info; within each severity level sorted by category then image
    for deterministic output."""


__all__ = [
    "ValidationCategory",
    "ValidationFinding",
    "ValidationReport",
    "ValidationSeverity",
]

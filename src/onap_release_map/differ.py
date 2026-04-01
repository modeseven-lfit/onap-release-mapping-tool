# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Manifest diff logic — compare two release manifests."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from onap_release_map.models import (
    DockerImage,
    HelmComponent,
    OnapRepository,
    ReleaseManifest,
)

logger = logging.getLogger(__name__)

__all__ = [
    "DiffResult",
    "FieldChange",
    "SectionDiff",
    "SummaryDelta",
    "diff_manifests",
    "format_diff_json",
    "format_diff_markdown",
    "format_diff_text",
]


class FieldChange(BaseModel):
    """A single field-level change between two manifest entries.

    Captures the identifier of the item that changed, which field
    differs, and the old and new values for that field.
    """

    key: str
    """Identifier of the changed item (gerrit_project / image:tag / chart name)."""

    field: str
    """Name of the field that changed."""

    old_value: str | None = None
    """Value in the baseline manifest, or ``None`` if absent."""

    new_value: str | None = None
    """Value in the comparison manifest, or ``None`` if absent."""


class SectionDiff(BaseModel):
    """Diff results for one manifest section (repos, images, or charts).

    Lists keys that were added, removed, or changed between the
    baseline and comparison manifests, together with a count of
    entries that remained identical.
    """

    added: list[str] = Field(default_factory=list)
    """Keys present only in the comparison manifest."""

    removed: list[str] = Field(default_factory=list)
    """Keys present only in the baseline manifest."""

    changed: list[FieldChange] = Field(default_factory=list)
    """Field-level changes for keys present in both manifests."""

    unchanged_count: int = 0
    """Number of entries that are identical in both manifests."""


class SummaryDelta(BaseModel):
    """Numeric deltas between the summary statistics of two manifests.

    Each delta is computed as ``comparison_value - baseline_value``,
    so positive numbers indicate growth and negative numbers indicate
    shrinkage.
    """

    repositories_delta: int = 0
    """Change in total repository count (B.total − A.total)."""

    docker_images_delta: int = 0
    """Change in total Docker image count."""

    helm_components_delta: int = 0
    """Change in total Helm component count."""


class DiffResult(BaseModel):
    """Complete diff between two release manifests.

    Contains per-section diffs for repositories, Docker images, and
    Helm components, plus high-level summary deltas and the release
    names being compared.
    """

    baseline_release: str
    """Release name from the baseline manifest."""

    comparison_release: str
    """Release name from the comparison manifest."""

    baseline_schema_version: str
    """Schema version of the baseline manifest."""

    comparison_schema_version: str
    """Schema version of the comparison manifest."""

    repositories: SectionDiff = Field(default_factory=SectionDiff)
    """Diff for the repositories section."""

    docker_images: SectionDiff = Field(default_factory=SectionDiff)
    """Diff for the Docker images section."""

    helm_components: SectionDiff = Field(default_factory=SectionDiff)
    """Diff for the Helm components section."""

    summary_delta: SummaryDelta = Field(default_factory=SummaryDelta)
    """Numeric deltas between the two manifest summaries."""

    metadata_changes: list[FieldChange] = Field(default_factory=list)
    """Field-level changes in top-level manifest metadata."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _str_val(value: Any) -> str | None:
    """Coerce a value to its string representation for diffing.

    Returns ``None`` when the input is ``None``, otherwise the
    ``str()`` representation.
    """
    if value is None:
        return None
    return str(value)


def _diff_repos(
    a_list: list[OnapRepository],
    b_list: list[OnapRepository],
) -> SectionDiff:
    """Compare two lists of repositories keyed by ``gerrit_project``.

    Detects additions, removals, and field-level changes for the
    ``confidence``, ``category``, ``gerrit_state``, ``maintained``,
    and ``has_ci`` fields.
    """
    a_map = {r.gerrit_project: r for r in a_list}
    b_map = {r.gerrit_project: r for r in b_list}

    a_keys = set(a_map)
    b_keys = set(b_map)

    added = sorted(b_keys - a_keys)
    removed = sorted(a_keys - b_keys)
    common = sorted(a_keys & b_keys)

    changed: list[FieldChange] = []
    unchanged_count = 0

    tracked_fields = (
        "confidence",
        "category",
        "gerrit_state",
        "maintained",
        "has_ci",
    )

    for key in common:
        a_repo = a_map[key]
        b_repo = b_map[key]
        key_changed = False
        for fld in tracked_fields:
            old = getattr(a_repo, fld)
            new = getattr(b_repo, fld)
            if old != new:
                changed.append(
                    FieldChange(
                        key=key,
                        field=fld,
                        old_value=_str_val(old),
                        new_value=_str_val(new),
                    )
                )
                key_changed = True
        if not key_changed:
            unchanged_count += 1

    return SectionDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged_count=unchanged_count,
    )


def _diff_docker_images(
    a_list: list[DockerImage],
    b_list: list[DockerImage],
) -> SectionDiff:
    """Compare two lists of Docker images grouped by image name.

    Images are first grouped by their ``image`` name into lists so
    that manifests containing multiple tags for the same image (e.g.
    ``onap/policy-api:4.2.0`` **and** ``onap/policy-api:4.2.2``)
    are handled correctly instead of silently dropping duplicates.

    The comparison strategy depends on how many tags each side has:

    * **Image name in only one manifest** — every ``image:tag``
      combination is reported as added or removed.
    * **Single tag on each side** — a tag change is reported as a
      ``FieldChange`` with ``field="tag"`` (preserving the original
      behaviour).  ``gerrit_project`` and ``nexus_validated`` are
      also compared.
    * **Multiple tags on either side** — tags are compared as sets.
      Tags only in B are added, tags only in A are removed, and
      tags present in both are compared field-by-field for
      ``gerrit_project`` and ``nexus_validated``.
    """
    # Group images by name, preserving all tags.
    a_map: dict[str, list[DockerImage]] = {}
    for img in a_list:
        a_map.setdefault(img.image, []).append(img)

    b_map: dict[str, list[DockerImage]] = {}
    for img in b_list:
        b_map.setdefault(img.image, []).append(img)

    a_keys = set(a_map)
    b_keys = set(b_map)

    added: list[str] = []
    removed: list[str] = []
    changed: list[FieldChange] = []
    unchanged_count = 0

    # Image names only in B → all their image:tag keys are added.
    for name in sorted(b_keys - a_keys):
        for img in b_map[name]:
            added.append(f"{img.image}:{img.tag}")

    # Image names only in A → all their image:tag keys are removed.
    for name in sorted(a_keys - b_keys):
        for img in a_map[name]:
            removed.append(f"{img.image}:{img.tag}")

    # Image names present in both manifests.
    for name in sorted(a_keys & b_keys):
        a_imgs = a_map[name]
        b_imgs = b_map[name]

        # Single-tag fast path: treat tag change as a FieldChange.
        if len(a_imgs) == 1 and len(b_imgs) == 1:
            a_img = a_imgs[0]
            b_img = b_imgs[0]
            baseline_key = f"{name}:{a_img.tag}"
            key_changed = False

            if a_img.tag != b_img.tag:
                changed.append(
                    FieldChange(
                        key=baseline_key,
                        field="tag",
                        old_value=a_img.tag,
                        new_value=b_img.tag,
                    )
                )
                key_changed = True

            if a_img.gerrit_project != b_img.gerrit_project:
                changed.append(
                    FieldChange(
                        key=baseline_key,
                        field="gerrit_project",
                        old_value=_str_val(a_img.gerrit_project),
                        new_value=_str_val(b_img.gerrit_project),
                    )
                )
                key_changed = True

            if a_img.nexus_validated != b_img.nexus_validated:
                changed.append(
                    FieldChange(
                        key=baseline_key,
                        field="nexus_validated",
                        old_value=_str_val(a_img.nexus_validated),
                        new_value=_str_val(b_img.nexus_validated),
                    )
                )
                key_changed = True

            if not key_changed:
                unchanged_count += 1
            continue

        # Multi-tag path: compare by tag sets.
        a_by_tag = {img.tag: img for img in a_imgs}
        b_by_tag = {img.tag: img for img in b_imgs}

        a_tags = set(a_by_tag)
        b_tags = set(b_by_tag)

        for tag in sorted(b_tags - a_tags):
            added.append(f"{name}:{tag}")

        for tag in sorted(a_tags - b_tags):
            removed.append(f"{name}:{tag}")

        for tag in sorted(a_tags & b_tags):
            a_img = a_by_tag[tag]
            b_img = b_by_tag[tag]
            tag_changed = False

            if a_img.gerrit_project != b_img.gerrit_project:
                changed.append(
                    FieldChange(
                        key=f"{name}:{tag}",
                        field="gerrit_project",
                        old_value=_str_val(a_img.gerrit_project),
                        new_value=_str_val(b_img.gerrit_project),
                    )
                )
                tag_changed = True

            if a_img.nexus_validated != b_img.nexus_validated:
                changed.append(
                    FieldChange(
                        key=f"{name}:{tag}",
                        field="nexus_validated",
                        old_value=_str_val(a_img.nexus_validated),
                        new_value=_str_val(b_img.nexus_validated),
                    )
                )
                tag_changed = True

            if not tag_changed:
                unchanged_count += 1

    return SectionDiff(
        added=sorted(added),
        removed=sorted(removed),
        changed=changed,
        unchanged_count=unchanged_count,
    )


def _diff_helm_components(
    a_list: list[HelmComponent],
    b_list: list[HelmComponent],
) -> SectionDiff:
    """Compare two lists of Helm components keyed by ``name``.

    Tracks changes in ``version`` and ``enabled_by_default``.
    """
    a_map = {c.name: c for c in a_list}
    b_map = {c.name: c for c in b_list}

    a_keys = set(a_map)
    b_keys = set(b_map)

    added = sorted(b_keys - a_keys)
    removed = sorted(a_keys - b_keys)
    common = sorted(a_keys & b_keys)

    changed: list[FieldChange] = []
    unchanged_count = 0

    tracked_fields = ("version", "enabled_by_default")

    for key in common:
        a_comp = a_map[key]
        b_comp = b_map[key]
        key_changed = False
        for fld in tracked_fields:
            old = getattr(a_comp, fld)
            new = getattr(b_comp, fld)
            if old != new:
                changed.append(
                    FieldChange(
                        key=key,
                        field=fld,
                        old_value=_str_val(old),
                        new_value=_str_val(new),
                    )
                )
                key_changed = True
        if not key_changed:
            unchanged_count += 1

    return SectionDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged_count=unchanged_count,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def diff_manifests(
    a: ReleaseManifest,
    b: ReleaseManifest,
    *,
    ignore_timestamps: bool = False,
) -> DiffResult:
    """Compare two release manifests and return a structured diff.

    Parameters
    ----------
    a:
        The baseline (older) manifest.
    b:
        The comparison (newer) manifest.
    ignore_timestamps:
        When ``True``, the ``generated_at`` field is excluded from
        comparison.  Schema version differences are always recorded
        but never cause a failure.

    Returns
    -------
    DiffResult
        Structured diff covering repositories, Docker images, Helm
        components, and summary statistics.
    """
    if a.schema_version != b.schema_version:
        logger.warning(
            "Schema versions differ: %s vs %s",
            a.schema_version,
            b.schema_version,
        )

    if ignore_timestamps:
        logger.debug("Ignoring generated_at timestamps in comparison")

    repo_diff = _diff_repos(a.repositories, b.repositories)
    image_diff = _diff_docker_images(a.docker_images, b.docker_images)
    helm_diff = _diff_helm_components(a.helm_components, b.helm_components)

    summary_delta = SummaryDelta(
        repositories_delta=len(b.repositories) - len(a.repositories),
        docker_images_delta=len(b.docker_images) - len(a.docker_images),
        helm_components_delta=len(b.helm_components) - len(a.helm_components),
    )

    metadata_changes: list[FieldChange] = []

    if not ignore_timestamps and a.generated_at != b.generated_at:
        metadata_changes.append(
            FieldChange(
                key="manifest",
                field="generated_at",
                old_value=a.generated_at,
                new_value=b.generated_at,
            )
        )

    if a.tool_version != b.tool_version:
        metadata_changes.append(
            FieldChange(
                key="manifest",
                field="tool_version",
                old_value=a.tool_version,
                new_value=b.tool_version,
            )
        )

    return DiffResult(
        baseline_release=a.onap_release.name,
        comparison_release=b.onap_release.name,
        baseline_schema_version=a.schema_version,
        comparison_schema_version=b.schema_version,
        repositories=repo_diff,
        docker_images=image_diff,
        helm_components=helm_diff,
        summary_delta=summary_delta,
        metadata_changes=metadata_changes,
    )


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def _format_section_text(label: str, section: SectionDiff) -> str:
    """Render a single section diff as plain text lines.

    Parameters
    ----------
    label:
        Human-readable section heading.
    section:
        The ``SectionDiff`` to render.

    Returns
    -------
    str
        Multiline plain text representation.
    """
    lines: list[str] = [f"  {label}:"]

    if section.added:
        lines.append(f"    Added ({len(section.added)}):")
        for key in section.added:
            lines.append(f"      + {key}")

    if section.removed:
        lines.append(f"    Removed ({len(section.removed)}):")
        for key in section.removed:
            lines.append(f"      - {key}")

    if section.changed:
        lines.append(f"    Changed ({len(section.changed)}):")
        for chg in section.changed:
            old = chg.old_value if chg.old_value is not None else "—"
            new = chg.new_value if chg.new_value is not None else "—"
            lines.append(
                f"      ~ {chg.key} [{chg.field}]: {old} -> {new}"
            )

    lines.append(f"    Unchanged: {section.unchanged_count}")
    return "\n".join(lines)


def format_diff_text(diff: DiffResult) -> str:
    """Format a diff result as human-readable plain text.

    Parameters
    ----------
    diff:
        The ``DiffResult`` to render.

    Returns
    -------
    str
        Multiline plain text suitable for terminal display.
    """
    lines: list[str] = [
        f"Manifest Diff: {diff.baseline_release} -> {diff.comparison_release}",
        f"Schema versions: {diff.baseline_schema_version} -> "
        f"{diff.comparison_schema_version}",
        "",
    ]

    if diff.metadata_changes:
        lines.append("  Metadata Changes:")
        for chg in diff.metadata_changes:
            lines.append(f"    ~ {chg.field}: {chg.old_value} -> {chg.new_value}")
        lines.append("")

    lines.append(_format_section_text("Repositories", diff.repositories))
    lines.append("")
    lines.append(_format_section_text("Docker Images", diff.docker_images))
    lines.append("")
    lines.append(_format_section_text("Helm Components", diff.helm_components))
    lines.append("")

    delta = diff.summary_delta
    lines.append("  Summary Delta:")
    lines.append(f"    Repositories: {delta.repositories_delta:+d}")
    lines.append(f"    Docker Images: {delta.docker_images_delta:+d}")
    lines.append(f"    Helm Components: {delta.helm_components_delta:+d}")

    return "\n".join(lines)


def format_diff_json(diff: DiffResult) -> str:
    """Format a diff result as deterministic JSON.

    Parameters
    ----------
    diff:
        The ``DiffResult`` to render.

    Returns
    -------
    str
        JSON string with sorted keys and two-space indentation.
    """
    return json.dumps(
        diff.model_dump(mode="json"),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )


def _md_section_table(label: str, section: SectionDiff) -> str:
    """Render a single section diff as a Markdown table.

    Parameters
    ----------
    label:
        Heading text for the section.
    section:
        The ``SectionDiff`` to render.

    Returns
    -------
    str
        Markdown fragment with heading and table(s).
    """
    lines: list[str] = [f"### {label}", ""]

    has_content = section.added or section.removed or section.changed

    if not has_content:
        lines.append(f"No changes ({section.unchanged_count} unchanged entries).")
        lines.append("")
        return "\n".join(lines)

    if section.added:
        lines.append(f"**Added** ({len(section.added)}):")
        lines.append("")
        lines.append("| Key |")
        lines.append("| --- |")
        for key in section.added:
            lines.append(f"| {key} |")
        lines.append("")

    if section.removed:
        lines.append(f"**Removed** ({len(section.removed)}):")
        lines.append("")
        lines.append("| Key |")
        lines.append("| --- |")
        for key in section.removed:
            lines.append(f"| {key} |")
        lines.append("")

    if section.changed:
        lines.append(f"**Changed** ({len(section.changed)}):")
        lines.append("")
        lines.append("| Key | Field | Old | New |")
        lines.append("| --- | ----- | --- | --- |")
        for chg in section.changed:
            old = chg.old_value if chg.old_value is not None else "—"
            new = chg.new_value if chg.new_value is not None else "—"
            lines.append(f"| {chg.key} | {chg.field} | {old} | {new} |")
        lines.append("")

    lines.append(f"*Unchanged: {section.unchanged_count}*")
    lines.append("")
    return "\n".join(lines)


def format_diff_markdown(diff: DiffResult) -> str:
    """Format a diff result as Markdown with tables.

    Parameters
    ----------
    diff:
        The ``DiffResult`` to render.

    Returns
    -------
    str
        Markdown document suitable for inclusion in reports or
        pull request descriptions.
    """
    lines: list[str] = [
        f"# Manifest Diff: {diff.baseline_release} → {diff.comparison_release}",
        "",
        f"**Schema versions:** {diff.baseline_schema_version} → "
        f"{diff.comparison_schema_version}",
        "",
    ]

    if diff.metadata_changes:
        lines.append("### Metadata Changes")
        lines.append("")
        lines.append("| Field | Old | New |")
        lines.append("| ----- | --- | --- |")
        for chg in diff.metadata_changes:
            old = chg.old_value if chg.old_value is not None else "—"
            new = chg.new_value if chg.new_value is not None else "—"
            lines.append(f"| {chg.field} | {old} | {new} |")
        lines.append("")

    lines.append(_md_section_table("Repositories", diff.repositories))
    lines.append(_md_section_table("Docker Images", diff.docker_images))
    lines.append(_md_section_table("Helm Components", diff.helm_components))

    delta = diff.summary_delta
    lines.append("### Summary Delta")
    lines.append("")
    lines.append("| Metric | Delta |")
    lines.append("| ------ | ----- |")
    lines.append(f"| Repositories | {delta.repositories_delta:+d} |")
    lines.append(f"| Docker Images | {delta.docker_images_delta:+d} |")
    lines.append(f"| Helm Components | {delta.helm_components_delta:+d} |")
    lines.append("")

    return "\n".join(lines)

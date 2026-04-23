# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Pydantic models for release manifest structure and provenance."""

from pydantic import BaseModel, Field

from .docker_image import DockerImage
from .helm_component import HelmComponent
from .repository import OnapRepository
from .validation import ValidationReport

#: Current manifest schema version. Bump this constant (and add a
#: new bullet to the :class:`ReleaseManifest` version history) when
#: the shape of the serialised manifest changes. Every producer and
#: consumer inside the project derives the version from this single
#: source of truth rather than duplicating a literal string.
#:
#: Version history:
#:     * ``1.0.0`` — initial release.
#:     * ``1.1.0`` — added manifest provenance.
#:     * ``1.2.0`` — added optional ``validation`` section reporting
#:       the outcome of post-collection data-quality validators.
MANIFEST_SCHEMA_VERSION: str = "1.2.0"


class DataSource(BaseModel):
    """A data source consulted during manifest generation.

    Tracks where raw data was fetched from so that results
    can be reproduced or audited later.
    """

    name: str
    """Human-readable name of the data source."""

    type: str
    """Kind of source, e.g. ``"git"``, ``"api"``, or ``"file"``."""

    url: str | None = None
    """URL used to fetch the data, if applicable."""

    commit: str | None = None
    """Git commit SHA captured at fetch time, if applicable."""

    fetched_at: str | None = None
    """ISO 8601 timestamp of when the data was retrieved."""


class CollectorExecution(BaseModel):
    """Execution record for a single collector run.

    Captures timing, item counts, and any errors so the manifest
    consumer can assess data quality.
    """

    name: str
    """Collector identifier, e.g. ``"oom_helm"`` or ``"gerrit_projects"``."""

    duration_seconds: float = 0.0
    """Wall-clock time the collector took to run."""

    items_collected: int = 0
    """Number of items the collector produced."""

    errors: list[str] = Field(default_factory=list)
    """Error messages encountered during collection."""


class ManifestProvenance(BaseModel):
    """Provenance metadata for the entire manifest.

    Groups the data sources and collector runs that contributed
    to this manifest so consumers can evaluate completeness.
    """

    data_sources: list[DataSource] = Field(default_factory=list)
    """Data sources consulted during generation."""

    collectors_executed: list[CollectorExecution] = Field(default_factory=list)
    """Collector runs that contributed data."""


class OnapRelease(BaseModel):
    """Identity of the ONAP release being mapped.

    Pins the release to a specific OOM chart version and,
    optionally, to the exact branch and commit used.
    """

    name: str
    """Release code-name, e.g. ``"Rabat"``."""

    oom_chart_version: str
    """Top-level OOM Helm chart version, e.g. ``"18.0.0"``."""

    oom_branch: str | None = None
    """OOM repository branch, e.g. ``"montreal"``."""

    oom_commit: str | None = None
    """Exact OOM commit SHA used for analysis."""


class ManifestSummary(BaseModel):
    """High-level statistics summarising the manifest contents.

    Provides quick counts so consumers do not need to iterate
    the full lists to get an overview.
    """

    total_repositories: int = 0
    """Number of Gerrit repositories in the manifest."""

    total_docker_images: int = 0
    """Number of Docker images in the manifest."""

    total_helm_components: int = 0
    """Number of Helm components in the manifest."""

    repositories_by_category: dict[str, int] = Field(default_factory=dict)
    """Repository counts grouped by category."""

    repositories_by_confidence: dict[str, int] = Field(default_factory=dict)
    """Repository counts grouped by confidence level."""

    collectors_used: list[str] = Field(default_factory=list)
    """Names of collectors that contributed data."""


class ReleaseManifest(BaseModel):
    """Top-level manifest describing an ONAP release.

    This is the root object serialised to JSON.  It contains
    every repository, Docker image, and Helm component
    discovered for the release, together with provenance and
    summary statistics.
    """

    schema_version: str = MANIFEST_SCHEMA_VERSION
    """Manifest schema version for forward compatibility.

    Defaults to :data:`MANIFEST_SCHEMA_VERSION`, which is the single
    source of truth for the current schema revision. Consumers that
    need to detect or compare versions should read this field from a
    loaded manifest rather than hard-coding a literal string.
    """

    tool_version: str
    """Version of ``onap-release-map`` that produced this manifest."""

    generated_at: str
    """ISO 8601 timestamp of when the manifest was generated."""

    onap_release: OnapRelease
    """Identity of the ONAP release being described."""

    summary: ManifestSummary = Field(default_factory=ManifestSummary)
    """Aggregate statistics for the manifest contents."""

    repositories: list[OnapRepository] = Field(default_factory=list)
    """Gerrit repositories belonging to this release."""

    docker_images: list[DockerImage] = Field(default_factory=list)
    """Docker images pinned to this release."""

    helm_components: list[HelmComponent] = Field(default_factory=list)
    """Helm components in the OOM umbrella chart."""

    provenance: ManifestProvenance = Field(default_factory=ManifestProvenance)
    """Data-source and collector provenance information."""

    validation: ValidationReport | None = None
    """Optional post-collection validation report.

    When present, summarises the findings of validators (e.g. the
    mapping audit) that examined the manifest after collection. When
    no validators ran, this field serialises as ``null`` in the JSON
    output produced by the current exporters rather than being
    omitted, preserving a stable top-level shape for consumers that
    predate schema version 1.2.0.
    """


__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "CollectorExecution",
    "DataSource",
    "ManifestProvenance",
    "ManifestSummary",
    "OnapRelease",
    "ReleaseManifest",
]

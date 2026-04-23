# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Pydantic model for Docker container image metadata."""

from pydantic import BaseModel, Field

__all__ = ["DockerImage"]


class DockerImage(BaseModel):
    """A Docker container image referenced by an ONAP release.

    Represents a single Docker image pinned to a specific tag, as discovered
    from Helm chart values, Nexus registries, or other data sources.  Each
    image may optionally be linked back to the Gerrit project that builds it
    and the Helm charts that deploy it.

    Attribution observability
    -------------------------
    Alongside the resolved ``gerrit_project``, each image can carry the
    provenance of that decision: which strategy the image mapper used,
    whether the chosen project was verified against live Gerrit ground
    truth, and any alternative candidates the longest-match stage
    considered before settling on the winner. Downstream consumers
    (validators, exporters, audit reports) can use these fields to
    explain or flag an attribution without re-running the mapper.
    """

    image: str
    """Full image name, e.g. ``onap/policy-api``."""

    tag: str
    """Pinned image tag for this release, e.g. ``4.2.2``."""

    registry: str | None = None
    """Docker registry hosting the image, e.g. ``nexus3.onap.org:10001``."""

    gerrit_project: str | None = None
    """Source Gerrit project that builds this image (best-effort mapping)."""

    helm_charts: list[str] = Field(default_factory=list)
    """Helm charts that reference this image."""

    nexus_validated: bool | None = None
    """Whether the image:tag combination was verified to exist in Nexus."""

    attribution_reason: str | None = None
    """Serialised :class:`MappingReason` describing how the mapping was reached.

    Values match the string form of the enum (for example ``override``,
    ``leaf-match-namespace``, ``heuristic-dash-verified``,
    ``override-stale``, ``unresolved``). ``None`` when the image record
    predates attribution observability or was produced by a collector
    that does not use :class:`ImageMapper`.
    """

    attribution_verified: bool | None = None
    """Tri-state verification flag for ``gerrit_project``.

    ``True`` when the resolved project was confirmed present in the
    Gerrit ground-truth set at resolution time.

    ``False`` in two sub-cases that consumers should distinguish by
    also reading ``gerrit_project`` and ``attribution_reason``:

    * ``gerrit_project`` is a non-null path the mapper could not
      verify against ground truth (for example an unverified
      heuristic fallback or a stale override). The attribution is
      suspect but a candidate still exists.
    * ``gerrit_project`` is ``None`` because no candidate matched
      (``attribution_reason`` is ``unresolved``). ``False`` here
      records "no verified result exists" rather than "a result
      was verified and rejected" — semantically closer to "not
      applicable" than to "rejected".

    ``None`` only when no ground truth was available at resolution
    time, so verification was impossible to determine either way.

    Consumers must read this field together with ``gerrit_project``
    and ``attribution_reason`` rather than treating ``False`` as a
    single signal.
    """

    attribution_alternatives: list[str] = Field(default_factory=list)
    """Other plausible project paths considered but not chosen.

    Populated when multiple Gerrit repositories share the image's leaf
    segment and the longest-match tiebreak had to select one. Useful
    for ``ambiguous_leaf`` findings in the validator report and for
    humans auditing why a particular attribution won. Empty when the
    mapper had a single candidate or did not run.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image": "onap/policy-api",
                    "tag": "4.2.2",
                    "registry": "nexus3.onap.org:10001",
                    "gerrit_project": "policy/api",
                    "helm_charts": ["policy"],
                    "nexus_validated": True,
                    "attribution_reason": "override",
                    "attribution_verified": True,
                    "attribution_alternatives": [],
                }
            ]
        }
    }

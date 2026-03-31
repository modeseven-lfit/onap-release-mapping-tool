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
                }
            ]
        }
    }

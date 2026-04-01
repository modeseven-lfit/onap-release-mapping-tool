# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Pydantic model for ONAP Gerrit repository metadata."""

from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["OnapRepository"]


class OnapRepository(BaseModel):
    """An ONAP Gerrit repository and its relationship to a release.

    Captures the full Gerrit project path, its top-level project area,
    confidence in the mapping, category classification, and cross-references
    to Docker images and Helm charts that originate from this repository.
    """

    gerrit_project: str
    """Full Gerrit project path, e.g. ``"policy/api"``."""

    top_level_project: str
    """Top-level ONAP project area, e.g. ``"policy"``."""

    gerrit_url: str | None = None
    """Full URL to the project in Gerrit."""

    confidence: Literal["high", "medium", "low"]
    """Confidence level of the mapping to this release."""

    confidence_reasons: list[str] = Field(default_factory=list)
    """Human-readable reasons explaining the confidence score."""

    category: Literal[
        "runtime",
        "build-dependency",
        "infrastructure",
        "test",
        "documentation",
        "tooling",
    ] = "runtime"
    """Functional category of the repository within the release."""

    gerrit_state: Literal["ACTIVE", "READ_ONLY"] | None = None
    """Current state of the project in Gerrit, if known."""

    maintained: bool | None = None
    """Whether the repository is actively maintained."""

    has_ci: bool | None = None
    """Whether the repository has CI jobs configured."""

    docker_images: list[str] = Field(default_factory=list)
    """Docker images built from this repository."""

    helm_charts: list[str] = Field(default_factory=list)
    """Helm charts that deploy images originating from this repository."""

    discovered_by: list[str] = Field(default_factory=list)
    """Names of the collectors that discovered this repository."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gerrit_project": "policy/api",
                    "top_level_project": "policy",
                    "gerrit_url": "https://gerrit.onap.org/r/admin/repos/policy/api",
                    "confidence": "high",
                    "confidence_reasons": [
                        "Image name matches Gerrit project path",
                        "Found in OOM Helm chart values",
                    ],
                    "category": "runtime",
                    "gerrit_state": "ACTIVE",
                    "maintained": True,
                    "has_ci": True,
                    "docker_images": ["onap/policy-api"],
                    "helm_charts": ["policy"],
                    "discovered_by": [
                        "oom_chart_collector",
                        "gerrit_project_collector",
                    ],
                }
            ]
        }
    }

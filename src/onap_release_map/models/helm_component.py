# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Pydantic model for an OOM Helm chart component."""

from pydantic import BaseModel, Field


class HelmComponent(BaseModel):
    """A Helm chart component within the OOM umbrella chart.

    Represents a top-level or nested Helm chart that deploys one or more
    Docker images as part of an ONAP release.  The umbrella chart
    (``oom/kubernetes/onap``) depends on these components, each of which
    can be individually enabled or disabled via Helm values keys.

    Attributes:
        name: Chart name as it appears in the umbrella chart
            (e.g. ``"policy"``).
        version: Semver version constraint declared in the umbrella's
            ``Chart.yaml`` requirements / dependencies list.
        enabled_by_default: Whether the component is enabled when the
            umbrella chart is installed with default values.
        condition_key: The Helm values key that controls whether this
            component is deployed (e.g. ``"policy.enabled"``).
        sub_charts: Names of nested sub-charts contained within this
            component chart.
        docker_images: Full image names (without registry prefix)
            deployed by this component and its sub-charts.
        gerrit_projects: Gerrit project paths whose source code
            contributes to this component's images or configuration.
    """

    name: str
    version: str | None = None
    enabled_by_default: bool | None = None
    condition_key: str | None = None
    sub_charts: list[str] = Field(default_factory=list)
    docker_images: list[str] = Field(default_factory=list)
    gerrit_projects: list[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "policy",
                    "version": "18.0.0",
                    "enabled_by_default": True,
                    "condition_key": "policy.enabled",
                    "sub_charts": [
                        "policy-api",
                        "policy-pap",
                        "policy-apex-pdp",
                    ],
                    "docker_images": [
                        "onap/policy-api",
                        "onap/policy-pap",
                        "onap/policy-apex-pdp",
                    ],
                    "gerrit_projects": [
                        "policy/api",
                        "policy/pap",
                        "policy/apex-pdp",
                    ],
                }
            ]
        }
    }


__all__ = ["HelmComponent"]

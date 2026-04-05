# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Shared test fixtures for onap-release-map tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def sample_oom_path(tmp_path: Path) -> Path:
    """Create a minimal OOM repo structure for testing.

    Creates a fake OOM directory with a Chart.yaml and values.yaml
    containing sample Docker image references.
    """
    kubernetes = tmp_path / "kubernetes"
    onap_dir = kubernetes / "onap"
    onap_dir.mkdir(parents=True)

    # Umbrella Chart.yaml
    chart_yaml = onap_dir / "Chart.yaml"
    chart_yaml.write_text(
        "apiVersion: v2\n"
        "name: onap\n"
        "version: 18.0.0\n"
        "description: ONAP umbrella Helm chart\n"
        "dependencies:\n"
        "  - name: policy\n"
        "    version: ~17.x-0\n"
        "    repository: 'file://components/policy'\n"
        "    condition: policy.enabled\n"
        "  - name: aai\n"
        "    version: ~16.x-0\n"
        "    repository: 'file://components/aai'\n"
        "    condition: aai.enabled\n"
        "  - name: cps\n"
        "    version: ~13.x-0\n"
        "    repository: 'file://components/cps'\n"
        "    condition: cps.enabled\n",
        encoding="utf-8",
    )

    # Policy component
    policy_dir = kubernetes / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "Chart.yaml").write_text(
        "apiVersion: v2\n"
        "name: policy\n"
        "version: 17.0.0\n"
        "dependencies:\n"
        "  - name: policy-api\n"
        "    version: ~17.x-0\n"
        "    repository: 'file://components/policy-api'\n",
        encoding="utf-8",
    )
    (policy_dir / "values.yaml").write_text(
        "global:\n"
        "  image:\n"
        "    registry: nexus3.onap.org:10001\n"
        "policy-api:\n"
        "  image: onap/policy-api:4.2.2\n"
        "policy-pap:\n"
        "  image: onap/policy-pap:4.2.2\n",
        encoding="utf-8",
    )

    # AAI component
    aai_dir = kubernetes / "aai"
    aai_dir.mkdir(parents=True)
    (aai_dir / "Chart.yaml").write_text(
        "apiVersion: v2\nname: aai\nversion: 16.0.0\n",
        encoding="utf-8",
    )
    (aai_dir / "values.yaml").write_text(
        "aai-resources:\n"
        "  image: onap/aai-resources:1.15.1\n"
        "aai-traversal:\n"
        "  image: onap/aai-traversal:1.15.1\n",
        encoding="utf-8",
    )

    # CPS component
    cps_dir = kubernetes / "cps"
    cps_dir.mkdir(parents=True)
    (cps_dir / "Chart.yaml").write_text(
        "apiVersion: v2\nname: cps\nversion: 13.0.0\n",
        encoding="utf-8",
    )
    (cps_dir / "values.yaml").write_text(
        "cps:\n  image: onap/cps-and-ncmp:3.6.1\n",
        encoding="utf-8",
    )

    # repositoryGenerator (infrastructure images)
    repo_gen_dir = kubernetes / "common" / "repositoryGenerator"
    repo_gen_dir.mkdir(parents=True)
    (repo_gen_dir / "values.yaml").write_text(
        "global:\n"
        "  repository: nexus3.onap.org:10001\n"
        "  readinessImage: onap/oom/readiness:7.0.1\n"
        "  jreImage: onap/integration-java11:10.0.0\n"
        "  busyboxImage: busybox:1.37.0\n",
        encoding="utf-8",
    )

    return tmp_path

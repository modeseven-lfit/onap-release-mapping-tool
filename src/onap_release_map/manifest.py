# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Manifest builder - aggregates collector results into a release manifest."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone

from onap_release_map.collectors import CollectorResult
from onap_release_map.models import (
    DataSource,
    DockerImage,
    HelmComponent,
    ManifestProvenance,
    ManifestSummary,
    OnapRelease,
    OnapRepository,
    ReleaseManifest,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ManifestBuilder",
]


class ManifestBuilder:
    """Build a release manifest from collector results."""

    def __init__(
        self,
        tool_version: str,
        onap_release: OnapRelease,
        deterministic: bool = True,
    ) -> None:
        self.tool_version = tool_version
        self.onap_release = onap_release
        self.deterministic = deterministic
        self._timestamp = datetime.now(tz=timezone.utc)
        self._results: list[CollectorResult] = []
        self._data_sources: list[DataSource] = []

    def add_result(self, result: CollectorResult) -> None:
        """Add a collector result to the manifest."""
        self._results.append(result)

    def add_data_source(self, source: DataSource) -> None:
        """Record a data source used during collection."""
        self._data_sources.append(source)

    def build(self) -> ReleaseManifest:
        """Build the final release manifest from all collected data."""
        repositories = self._merge_repositories()
        docker_images = self._merge_docker_images()
        helm_components = self._merge_helm_components()

        # Build summary
        category_counts: Counter[str] = Counter()
        confidence_counts: Counter[str] = Counter()
        for repo in repositories:
            category_counts[repo.category] += 1
            confidence_counts[repo.confidence] += 1

        collectors_used = []
        executions = []
        for result in self._results:
            if result.execution:
                collectors_used.append(result.execution.name)
                executions.append(result.execution)

        summary = ManifestSummary(
            total_repositories=len(repositories),
            total_docker_images=len(docker_images),
            total_helm_components=len(helm_components),
            repositories_by_category=dict(sorted(category_counts.items())),
            repositories_by_confidence=dict(sorted(confidence_counts.items())),
            collectors_used=sorted(set(collectors_used)),
        )

        provenance = ManifestProvenance(
            data_sources=self._data_sources,
            collectors_executed=executions,
        )

        if self.deterministic:
            generated_at = self._timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            generated_at = self._timestamp.isoformat()

        return ReleaseManifest(
            schema_version="1.1.0",
            tool_version=self.tool_version,
            generated_at=generated_at,
            onap_release=self.onap_release,
            summary=summary,
            repositories=repositories,
            docker_images=docker_images,
            helm_components=helm_components,
            provenance=provenance,
        )

    def _merge_repositories(self) -> list[OnapRepository]:
        """Merge repos from all collectors, deduplicating by project."""
        repo_map: dict[str, OnapRepository] = {}
        for result in self._results:
            for repo in result.repositories:
                if repo.gerrit_project in repo_map:
                    existing = repo_map[repo.gerrit_project]
                    # Merge discovered_by
                    for d in repo.discovered_by:
                        if d not in existing.discovered_by:
                            existing.discovered_by.append(d)
                    # Merge docker_images
                    for img in repo.docker_images:
                        if img not in existing.docker_images:
                            existing.docker_images.append(img)
                    # Merge helm_charts
                    for chart in repo.helm_charts:
                        if chart not in existing.helm_charts:
                            existing.helm_charts.append(chart)
                    # Merge confidence_reasons
                    for reason in repo.confidence_reasons:
                        if reason not in existing.confidence_reasons:
                            existing.confidence_reasons.append(reason)
                    # Take highest confidence
                    conf_order = {
                        "high": 3,
                        "medium": 2,
                        "low": 1,
                    }
                    if conf_order.get(repo.confidence, 0) > conf_order.get(
                        existing.confidence, 0
                    ):
                        existing.confidence = repo.confidence
                    # Fill in missing fields
                    if existing.gerrit_state is None:
                        existing.gerrit_state = repo.gerrit_state
                    elif repo.gerrit_state == "READ_ONLY":
                        existing.gerrit_state = "READ_ONLY"
                    # READ_ONLY is definitively not in the
                    # current release regardless of how the
                    # state was set (first fill or override).
                    if existing.gerrit_state == "READ_ONLY":
                        existing.in_current_release = False
                    if existing.maintained is None:
                        existing.maintained = repo.maintained
                    if existing.has_ci is None:
                        existing.has_ci = repo.has_ci
                    # Merge in_current_release: True wins over
                    # None/False since any positive signal is
                    # authoritative, except READ_ONLY is
                    # definitively not in the current release.
                    if (
                        repo.in_current_release is True
                        and existing.gerrit_state != "READ_ONLY"
                    ):
                        existing.in_current_release = True
                    elif (
                        existing.in_current_release is None
                        and repo.in_current_release is not None
                    ):
                        existing.in_current_release = repo.in_current_release
                    # Merge is_parent_project: True wins
                    if repo.is_parent_project is True:
                        existing.is_parent_project = True
                    elif (
                        existing.is_parent_project is None
                        and repo.is_parent_project is not None
                    ):
                        existing.is_parent_project = repo.is_parent_project
                else:
                    repo_map[repo.gerrit_project] = repo

        # Post-processing: OOM-discovered repos are in the current
        # release unless they were already definitively excluded.
        for repo in repo_map.values():
            if (
                "oom" in repo.discovered_by
                and repo.gerrit_state != "READ_ONLY"
                and repo.in_current_release is not False
            ):
                repo.in_current_release = True

        # Parent projects whose children are in the release
        # are themselves considered in the release.
        # Precompute parent paths for repos in the release to
        # avoid an O(n^2) scan.
        release_parents: set[str] = set()
        for name, repo in repo_map.items():
            if repo.in_current_release is True:
                parts = name.split("/")
                for i in range(1, len(parts)):
                    release_parents.add("/".join(parts[:i]))
        for repo in repo_map.values():
            if (
                repo.is_parent_project
                and repo.gerrit_project in release_parents
                and repo.gerrit_state != "READ_ONLY"
                and repo.in_current_release is not False
            ):
                repo.in_current_release = True

        return sorted(repo_map.values(), key=lambda r: r.gerrit_project)

    def _merge_docker_images(self) -> list[DockerImage]:
        """Merge Docker images from all collectors."""
        image_map: dict[str, DockerImage] = {}
        for result in self._results:
            for img in result.docker_images:
                key = f"{img.image}:{img.tag}"
                if key not in image_map:
                    image_map[key] = img
                else:
                    existing = image_map[key]
                    for chart in img.helm_charts:
                        if chart not in existing.helm_charts:
                            existing.helm_charts.append(chart)
                    if existing.gerrit_project is None:
                        existing.gerrit_project = img.gerrit_project
        return sorted(image_map.values(), key=lambda i: (i.image, i.tag))

    def _merge_helm_components(self) -> list[HelmComponent]:
        """Merge Helm components from all collectors."""
        comp_map: dict[str, HelmComponent] = {}
        for result in self._results:
            for comp in result.helm_components:
                if comp.name not in comp_map:
                    comp_map[comp.name] = comp
        return sorted(comp_map.values(), key=lambda c: c.name)

    @staticmethod
    def to_json(
        manifest: ReleaseManifest,
        pretty: bool = True,
        indent: int = 2,
    ) -> str:
        """Serialize manifest to deterministic JSON string."""
        data = manifest.model_dump(mode="json")
        return json.dumps(
            data,
            sort_keys=True,
            indent=indent if pretty else None,
            ensure_ascii=False,
        )

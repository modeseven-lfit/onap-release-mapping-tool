# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""OOM Helm chart collector - primary data source for ONAP release mapping."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote

from onap_release_map.collectors import BaseCollector, CollectorResult, registry
from onap_release_map.models import DockerImage, HelmComponent, OnapRepository
from onap_release_map.parsers.helm import HelmChartParser
from onap_release_map.parsers.image_mapper import ImageMapper


@registry.register
class OOMCollector(BaseCollector):
    """Collect release data from OOM Helm charts.

    This is the primary collector. It parses the OOM umbrella chart,
    extracts Docker image references, and maps them to Gerrit projects.
    """

    name = "oom"

    def __init__(
        self,
        oom_path: Path | None = None,
        mapping_file: Path | None = None,
        gerrit_url: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialise the OOM collector.

        Args:
            oom_path: Path to the OOM repository checkout.
            mapping_file: Optional path to a YAML file with additional
                or overriding image-to-project mappings.
            gerrit_url: Base URL of the Gerrit instance.  Defaults to
                ``https://gerrit.onap.org/r``.
            **kwargs: Passed through to :class:`BaseCollector`.
        """
        super().__init__()
        self.oom_path = oom_path
        self.mapping_file = mapping_file
        self._gerrit_url = (gerrit_url or "https://gerrit.onap.org/r").rstrip("/")

    def collect(self, **kwargs: object) -> CollectorResult:
        """Parse OOM charts and produce repositories, images, and components."""
        if self.oom_path is None:
            raise ValueError("oom_path is required for OOMCollector")

        parser = HelmChartParser(self.oom_path)
        mapper = ImageMapper(self.mapping_file)

        helm_components_raw, docker_images_raw, _ = parser.parse_umbrella_chart()

        # Build Docker image models
        seen_images: dict[str, DockerImage] = {}
        for img_data in docker_images_raw:
            image_key = f"{img_data['image']}:{img_data.get('tag', 'latest')}"
            chart_name = img_data.get("chart_name", "")

            if image_key in seen_images:
                # Merge chart metadata and enrich missing fields
                existing = seen_images[image_key]
                if chart_name and chart_name not in existing.helm_charts:
                    existing.helm_charts.append(chart_name)
                # Backfill registry if the original entry was missing it
                new_registry = img_data.get("registry")
                if new_registry and not existing.registry:
                    existing.registry = new_registry
                continue

            gerrit_project = mapper.map_image(img_data["image"])
            img = DockerImage(
                image=img_data["image"],
                tag=img_data.get("tag", "latest"),
                registry=img_data.get("registry"),
                gerrit_project=gerrit_project,
                helm_charts=[chart_name] if chart_name else [],
            )
            seen_images[image_key] = img

        docker_images = list(seen_images.values())

        # Build Helm component models
        helm_components: list[HelmComponent] = []
        # Index sub-charts by top-level component.
        comp_sub_charts: dict[str, list[str]] = {}
        # Index images and projects per chart name (both top-level
        # and nested, e.g. "policy" and "policy/policy-api") so
        # every HelmComponent gets its own associations.
        chart_images: dict[str, list[str]] = {}
        for comp_data in helm_components_raw:
            parent = comp_data.get("component", "")
            sub = comp_data.get("sub_component", "")
            if parent and sub:
                comp_sub_charts.setdefault(parent, [])
                if sub not in comp_sub_charts[parent]:
                    comp_sub_charts[parent].append(sub)
        for img_data in docker_images_raw:
            chart_name = img_data.get("chart_name", "")
            if not chart_name:
                continue
            # Associate image with exact chart_name (e.g.
            # "policy/policy-api") and the top-level component.
            top_comp = chart_name.split("/")[0]
            for key in dict.fromkeys([chart_name, top_comp]):
                chart_images.setdefault(key, [])
                if img_data["image"] not in chart_images[key]:
                    chart_images[key].append(img_data["image"])

        # Derive gerrit_projects per chart key from image mappings
        chart_gerrit: dict[str, list[str]] = {}
        for chart_key, images in chart_images.items():
            projects: list[str] = []
            for img_name in images:
                proj = mapper.map_image(img_name)
                if proj and proj not in projects:
                    projects.append(proj)
            if projects:
                chart_gerrit[chart_key] = projects

        for comp_data in helm_components_raw:
            comp_name = comp_data["name"]
            # Build a lookup key that matches the chart_images index:
            # nested sub-charts use "parent/sub", top-level use name.
            parent = comp_data.get("component", "")
            sub = comp_data.get("sub_component", "")
            if parent and sub:
                lookup_key = f"{parent}/{sub}"
            else:
                lookup_key = comp_name
            helm_components.append(
                HelmComponent(
                    name=comp_name,
                    version=comp_data.get("umbrella_version")
                    or comp_data.get("version"),
                    enabled_by_default=comp_data.get("enabled_by_default"),
                    condition_key=comp_data.get("condition"),
                    sub_charts=comp_sub_charts.get(comp_name, []),
                    docker_images=chart_images.get(lookup_key, []),
                    gerrit_projects=chart_gerrit.get(lookup_key, []),
                )
            )

        # Build Repository models from mapped images
        repo_map: dict[str, OnapRepository] = {}
        for img in docker_images:
            if img.gerrit_project is None:
                continue
            proj = img.gerrit_project
            if proj not in repo_map:
                top_level = mapper.get_top_level_project(proj)
                repo_map[proj] = OnapRepository(
                    gerrit_project=proj,
                    top_level_project=top_level,
                    gerrit_url=f"{self._gerrit_url}/admin/repos/{quote(proj, safe='')}",
                    confidence="high",
                    confidence_reasons=["Docker image referenced in OOM Helm charts"],
                    category="runtime",
                    discovered_by=["oom"],
                )
            if img.image not in repo_map[proj].docker_images:
                repo_map[proj].docker_images.append(img.image)
            for chart in img.helm_charts:
                if chart not in repo_map[proj].helm_charts:
                    repo_map[proj].helm_charts.append(chart)

        # Also add OOM itself as infrastructure
        repo_map.setdefault(
            "oom",
            OnapRepository(
                gerrit_project="oom",
                top_level_project="oom",
                gerrit_url=f"{self._gerrit_url}/admin/repos/oom",
                confidence="high",
                confidence_reasons=["OOM is the deployment repository"],
                category="infrastructure",
                discovered_by=["oom"],
            ),
        )

        repositories = sorted(repo_map.values(), key=lambda r: r.gerrit_project)

        return CollectorResult(
            repositories=list(repositories),
            docker_images=sorted(docker_images, key=lambda d: (d.image, d.tag)),
            helm_components=sorted(helm_components, key=lambda h: h.name),
        )

    @staticmethod
    def _get_git_commit(repo_path: Path) -> str | None:
        """Get the current git commit SHA of a repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

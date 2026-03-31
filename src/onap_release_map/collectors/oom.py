# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""OOM Helm chart collector - primary data source for ONAP release mapping."""

from __future__ import annotations

import subprocess
from pathlib import Path

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
        **kwargs: object,
    ) -> None:
        super().__init__()
        self.oom_path = oom_path
        self.mapping_file = mapping_file

    def collect(self, **kwargs: object) -> CollectorResult:
        """Parse OOM charts and produce repositories, images, and components."""
        if self.oom_path is None:
            raise ValueError("oom_path is required for OOMCollector")

        parser = HelmChartParser(self.oom_path)
        mapper = ImageMapper(self.mapping_file)

        helm_components_raw, docker_images_raw, _ = parser.parse_umbrella_chart()

        # Build Docker image models
        docker_images: list[DockerImage] = []
        seen_images: set[str] = set()
        for img_data in docker_images_raw:
            image_key = f"{img_data['image']}:{img_data.get('tag', 'latest')}"
            if image_key in seen_images:
                continue
            seen_images.add(image_key)

            gerrit_project = mapper.map_image(img_data["image"])
            docker_images.append(
                DockerImage(
                    image=img_data["image"],
                    tag=img_data.get("tag", "latest"),
                    registry=img_data.get("registry"),
                    gerrit_project=gerrit_project,
                    helm_charts=img_data.get("helm_charts", []),
                )
            )

        # Build Helm component models
        helm_components: list[HelmComponent] = []
        for comp_data in helm_components_raw:
            helm_components.append(
                HelmComponent(
                    name=comp_data["name"],
                    version=comp_data.get("version"),
                    enabled_by_default=comp_data.get("enabled_by_default", False),
                    condition_key=comp_data.get("condition"),
                    sub_charts=comp_data.get("sub_charts", []),
                    docker_images=comp_data.get("docker_images", []),
                    gerrit_projects=comp_data.get("gerrit_projects", []),
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
                    gerrit_url=(f"https://gerrit.onap.org/r/admin/repos/{proj}"),
                    confidence="high",
                    confidence_reasons=["Docker image referenced in OOM Helm charts"],
                    category="runtime",
                    discovered_by=["oom"],
                )
            repo_map[proj].docker_images.append(img.image)
            for chart in img.helm_charts:
                if chart not in repo_map[proj].helm_charts:
                    repo_map[proj].helm_charts.append(chart)

        # Also add OOM itself as infrastructure
        self._get_git_commit(self.oom_path)
        repo_map.setdefault(
            "oom",
            OnapRepository(
                gerrit_project="oom",
                top_level_project="oom",
                gerrit_url=("https://gerrit.onap.org/r/admin/repos/oom"),
                confidence="high",
                confidence_reasons=["OOM is the deployment repository"],
                category="infrastructure",
                discovered_by=["oom"],
            ),
        )

        repositories = sorted(repo_map.values(), key=lambda r: r.gerrit_project)

        return CollectorResult(
            repositories=list(repositories),
            docker_images=sorted(docker_images, key=lambda d: d.image),
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

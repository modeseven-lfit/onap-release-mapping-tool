# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Parser for OOM Helm charts to extract dependencies and Docker images."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from .yaml_utils import safe_load_yaml

# Regex matching fully-qualified or short ONAP Docker image references.
# Examples:
#   nexus3.onap.org:10001/onap/policy-api:3.1.3
#   onap/sdnc-image:2.6.1
_IMAGE_RE = re.compile(r"^(?:nexus3\.onap\.org:\d+/)?(onap/[a-zA-Z0-9._/-]+):(.+)$")


class HelmChartParser:
    """Parse OOM Helm charts to extract dependencies and Docker images."""

    EXCLUDE_DIRS: set[str] = {"argo", "archive"}

    def __init__(self, oom_path: Path) -> None:
        self.oom_path = oom_path
        self.kubernetes_path = oom_path / "kubernetes"
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse_umbrella_chart(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse the OOM umbrella chart and all sub-charts.

        Returns:
            Tuple of (helm_components, docker_images, chart_image_mapping)
            where each is a list of dicts with extracted data.
        """
        umbrella_chart_path = self.kubernetes_path / "onap" / "Chart.yaml"
        if not umbrella_chart_path.is_file():
            self._logger.error("Umbrella Chart.yaml not found: %s", umbrella_chart_path)
            return [], [], []

        umbrella = self._parse_chart_yaml(umbrella_chart_path)
        dependencies: list[dict[str, Any]] = umbrella.get("dependencies", [])

        helm_components: list[dict[str, Any]] = []
        docker_images: list[dict[str, Any]] = []
        chart_image_mapping: list[dict[str, Any]] = []

        for dep in dependencies:
            dep_name = dep.get("name", "")
            if not dep_name:
                continue

            component_path = self.kubernetes_path / dep_name
            if not component_path.is_dir():
                self._logger.debug("Component directory missing: %s", component_path)
                continue

            components, images = self._walk_component(dep_name, component_path)
            helm_components.extend(components)
            docker_images.extend(images)

            if images:
                chart_image_mapping.append(
                    {
                        "chart": dep_name,
                        "version": dep.get("version", ""),
                        "images": [img["image"] for img in images],
                    }
                )

        self._logger.info(
            "Parsed %d components, %d images from umbrella chart",
            len(helm_components),
            len(docker_images),
        )
        return helm_components, docker_images, chart_image_mapping

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_chart_yaml(self, chart_path: Path) -> dict[str, Any]:
        """Parse a single Chart.yaml and return its contents.

        Args:
            chart_path: Path to the Chart.yaml file.

        Returns:
            Dict with chart metadata (name, version, dependencies …).
        """
        data = safe_load_yaml(chart_path)
        return {
            "name": data.get("name", ""),
            "version": data.get("version", ""),
            "appVersion": data.get("appVersion", ""),
            "description": data.get("description", ""),
            "dependencies": data.get("dependencies", []),
        }

    def _parse_values_yaml(
        self, values_path: Path, chart_name: str = ""
    ) -> list[dict[str, str]]:
        """Parse a values.yaml to find Docker image references.

        Args:
            values_path: Path to the values.yaml file.
            chart_name: Helm chart name to attach to each image.

        Returns:
            List of dicts with keys: image, tag, registry, chart_name.
        """
        if not values_path.is_file():
            return []

        data = safe_load_yaml(values_path)
        return self._extract_images_from_values(data, chart_name)

    def _walk_component(
        self, component_name: str, component_path: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        """Walk a component directory to find sub-charts and images.

        Looks for Chart.yaml in the component root and in each
        ``components/*/`` sub-directory.  Directories whose names are
        in :pyattr:`EXCLUDE_DIRS` are silently skipped.

        Args:
            component_name: Top-level component name.
            component_path: Filesystem path to the component.

        Returns:
            Tuple of (helm_components, docker_images).
        """
        helm_components: list[dict[str, Any]] = []
        docker_images: list[dict[str, str]] = []

        # Root chart -------------------------------------------------
        root_chart = component_path / "Chart.yaml"
        if root_chart.is_file():
            chart_info = self._parse_chart_yaml(root_chart)
            chart_info["component"] = component_name
            helm_components.append(chart_info)

        # Values at component root -----------------------------------
        root_values = component_path / "values.yaml"
        docker_images.extend(self._parse_values_yaml(root_values, component_name))

        # Walk ``components/`` sub-directories -----------------------
        components_dir = component_path / "components"
        if components_dir.is_dir():
            for sub_dir in sorted(components_dir.iterdir()):
                if not sub_dir.is_dir():
                    continue
                if sub_dir.name in self.EXCLUDE_DIRS:
                    self._logger.debug("Skipping excluded directory: %s", sub_dir.name)
                    continue

                sub_chart = sub_dir / "Chart.yaml"
                if sub_chart.is_file():
                    info = self._parse_chart_yaml(sub_chart)
                    info["component"] = component_name
                    info["sub_component"] = sub_dir.name
                    helm_components.append(info)

                sub_values = sub_dir / "values.yaml"
                sub_name = f"{component_name}/{sub_dir.name}"
                docker_images.extend(self._parse_values_yaml(sub_values, sub_name))

                # Recurse one more level for deeply nested charts
                nested_components = sub_dir / "components"
                if nested_components.is_dir():
                    nested_comps, nested_imgs = self._walk_nested_components(
                        component_name,
                        sub_dir.name,
                        nested_components,
                    )
                    helm_components.extend(nested_comps)
                    docker_images.extend(nested_imgs)

        return helm_components, docker_images

    def _walk_nested_components(
        self,
        component_name: str,
        sub_component: str,
        nested_dir: Path,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        """Walk a nested ``components/`` directory one level deep.

        Args:
            component_name: Top-level component name.
            sub_component: Immediate parent sub-component name.
            nested_dir: Path to the nested ``components/`` directory.

        Returns:
            Tuple of (helm_components, docker_images).
        """
        helm_components: list[dict[str, Any]] = []
        docker_images: list[dict[str, str]] = []

        for entry in sorted(nested_dir.iterdir()):
            if not entry.is_dir() or entry.name in self.EXCLUDE_DIRS:
                continue

            chart_file = entry / "Chart.yaml"
            if chart_file.is_file():
                info = self._parse_chart_yaml(chart_file)
                info["component"] = component_name
                info["sub_component"] = f"{sub_component}/{entry.name}"
                helm_components.append(info)

            values_file = entry / "values.yaml"
            chart_label = f"{component_name}/{sub_component}/{entry.name}"
            docker_images.extend(self._parse_values_yaml(values_file, chart_label))

        return helm_components, docker_images

    def _extract_images_from_values(
        self, data: dict[str, Any], chart_name: str
    ) -> list[dict[str, str]]:
        """Recursively extract Docker image references from values.

        Recognised patterns:

        1. A key named ``image`` whose *string* value matches the
           ONAP image regex.
        2. A *dict* value containing ``imageName`` (with ``onap/``
           prefix) and optionally a ``tag`` key.
        3. The ``global.image`` pattern with ``repository`` and
           ``tag`` sub-keys.

        Args:
            data: Parsed YAML values dict.
            chart_name: Chart name to associate with each image.

        Returns:
            List of dicts with keys: image, tag, registry, chart_name.
        """
        results: list[dict[str, str]] = []
        self._recurse_values(data, chart_name, results)
        return results

    def _recurse_values(
        self,
        node: Any,
        chart_name: str,
        results: list[dict[str, str]],
    ) -> None:
        """Recursively walk *node* collecting image references.

        Args:
            node: Current YAML node (dict, list, or scalar).
            chart_name: Chart name for attribution.
            results: Accumulator list (mutated in place).
        """
        if isinstance(node, dict):
            self._inspect_dict(node, chart_name, results)
        elif isinstance(node, list):
            for item in node:
                self._recurse_values(item, chart_name, results)

    def _inspect_dict(
        self,
        mapping: dict[str, Any],
        chart_name: str,
        results: list[dict[str, str]],
    ) -> None:
        """Inspect a single mapping node for image references.

        Args:
            mapping: Dict node from the parsed YAML.
            chart_name: Chart name for attribution.
            results: Accumulator list (mutated in place).
        """
        # Pattern 1 – plain ``image: <ref>`` string
        image_val = mapping.get("image")
        if isinstance(image_val, str):
            match = _IMAGE_RE.match(image_val)
            if match:
                results.append(
                    self._build_image_record(
                        match.group(1),
                        match.group(2),
                        image_val,
                        chart_name,
                    )
                )

        # Pattern 2 – ``imageName`` / ``tag`` dict
        image_name = mapping.get("imageName")
        if isinstance(image_name, str) and "onap/" in image_name:
            tag = str(mapping.get("tag", "latest"))
            full_ref = f"{image_name}:{tag}"
            match = _IMAGE_RE.match(full_ref)
            if match:
                results.append(
                    self._build_image_record(
                        match.group(1),
                        match.group(2),
                        full_ref,
                        chart_name,
                    )
                )

        # Pattern 3 – ``repository`` + ``tag`` inside an image block
        repo = mapping.get("repository")
        if isinstance(repo, str) and "onap/" in repo:
            tag = str(mapping.get("tag", "latest"))
            full_ref = f"{repo}:{tag}"
            match = _IMAGE_RE.match(full_ref)
            if match:
                results.append(
                    self._build_image_record(
                        match.group(1),
                        match.group(2),
                        full_ref,
                        chart_name,
                    )
                )

        # Recurse into child values
        for value in mapping.values():
            self._recurse_values(value, chart_name, results)

    @staticmethod
    def _build_image_record(
        image: str, tag: str, raw_ref: str, chart_name: str
    ) -> dict[str, str]:
        """Build a normalised image-record dict.

        Args:
            image: Image name without registry prefix (e.g.
                ``onap/policy-api``).
            tag: Image tag / version string.
            raw_ref: Original reference string from values.yaml.
            chart_name: Helm chart that references this image.

        Returns:
            Dict with keys image, tag, registry, chart_name.
        """
        registry = ""
        if raw_ref.startswith("nexus3.onap.org"):
            registry = raw_ref.split("/")[0]
        return {
            "image": image,
            "tag": tag,
            "registry": registry,
            "chart_name": chart_name,
        }

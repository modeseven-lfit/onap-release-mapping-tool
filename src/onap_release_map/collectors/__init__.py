# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Collector framework for gathering ONAP release data from various sources."""

from __future__ import annotations

import abc
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from onap_release_map.models import (
        CollectorExecution,
        DockerImage,
        HelmComponent,
        OnapRepository,
    )


@dataclass
class CollectorResult:
    """Results from a single collector run."""

    repositories: list[OnapRepository] = field(default_factory=list)
    docker_images: list[DockerImage] = field(default_factory=list)
    helm_components: list[HelmComponent] = field(default_factory=list)
    execution: CollectorExecution | None = None


class BaseCollector(abc.ABC):
    """Abstract base class for all data collectors."""

    name: str = "base"

    def __init__(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.{self.name}")

    @abc.abstractmethod
    def collect(self, **kwargs: object) -> CollectorResult:
        """Run the collector and return results."""
        ...

    def timed_collect(self, **kwargs: object) -> CollectorResult:
        """Run collect() with timing and error handling."""
        from onap_release_map.models import CollectorExecution

        start = time.monotonic()
        errors: list[str] = []
        try:
            result = self.collect(**kwargs)
        except Exception as exc:
            self._logger.error("Collector %s failed: %s", self.name, exc)
            errors.append(str(exc))
            result = CollectorResult()

        duration = time.monotonic() - start
        items = (
            len(result.repositories)
            + len(result.docker_images)
            + len(result.helm_components)
        )
        result.execution = CollectorExecution(
            name=self.name,
            duration_seconds=round(duration, 3),
            items_collected=items,
            errors=errors,
        )
        return result


class CollectorRegistry:
    """Registry of available collectors."""

    def __init__(self) -> None:
        self._collectors: dict[str, type[BaseCollector]] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, collector_cls: type[BaseCollector]) -> type[BaseCollector]:
        """Register a collector class. Can be used as a decorator."""
        self._collectors[collector_cls.name] = collector_cls
        return collector_cls

    def get(self, name: str) -> type[BaseCollector] | None:
        """Get a collector class by name."""
        return self._collectors.get(name)

    def list_names(self) -> list[str]:
        """List all registered collector names."""
        return sorted(self._collectors.keys())

    def create(self, name: str, **kwargs: object) -> BaseCollector | None:
        """Create a collector instance by name."""
        cls = self._collectors.get(name)
        if cls is None:
            self._logger.warning("Unknown collector: %s", name)
            return None
        return cls(**kwargs)


# Global registry
registry = CollectorRegistry()

__all__ = [
    "BaseCollector",
    "CollectorRegistry",
    "CollectorResult",
    "registry",
]

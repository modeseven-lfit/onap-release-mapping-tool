# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Nexus3 Docker registry collector - validates image existence."""

from __future__ import annotations

import concurrent.futures

import httpx

from onap_release_map.collectors import BaseCollector, CollectorResult, registry
from onap_release_map.models import DockerImage

__all__ = ["NexusCollector"]


@registry.register
class NexusCollector(BaseCollector):
    """Validate Docker image existence against a Nexus3 registry.

    Uses the Docker Registry HTTP API V2 to check whether each
    image:tag combination from a previously-built manifest actually
    exists in the configured Nexus instance.  Results are written
    back to the ``nexus_validated`` field of each
    :class:`DockerImage`.
    """

    name = "nexus"

    def __init__(
        self,
        *,
        nexus_url: str = "https://nexus3.onap.org",
        timeout: int = 10,
        concurrent_workers: int = 4,
        docker_images: list[DockerImage] | None = None,
        **kwargs: object,
    ) -> None:
        """Initialise the Nexus collector.

        Args:
            nexus_url: Base URL of the Nexus3 instance hosting the
                Docker registry V2 API.
            timeout: HTTP request timeout in seconds.
            concurrent_workers: Maximum number of threads used for
                concurrent image validation.
            docker_images: List of :class:`DockerImage` objects to
                validate.  Typically produced by an earlier collector
                such as :class:`OOMCollector`.
            **kwargs: Additional keyword arguments accepted for forward
                compatibility. Currently ignored and not passed to
                :class:`BaseCollector`.
        """
        super().__init__()
        if timeout <= 0:
            msg = f"timeout must be positive, got {timeout}"
            raise ValueError(msg)
        if concurrent_workers < 1:
            msg = f"concurrent_workers must be at least 1, got {concurrent_workers}"
            raise ValueError(msg)
        self._nexus_url = nexus_url.rstrip("/")
        self._timeout = timeout
        self._concurrent_workers = concurrent_workers
        self._docker_images = docker_images or []

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def collect(self, **kwargs: object) -> CollectorResult:
        """Validate every Docker image against the Nexus registry.

        For each :class:`DockerImage` provided at construction time,
        a ``HEAD`` request is issued to the Docker Registry V2
        manifest endpoint (``/v2/<name>/manifests/<tag>``).  If the
        manifest exists the ``nexus_validated`` field is set to
        ``True``; otherwise it is set to ``False``.

        Returns:
            A :class:`CollectorResult` whose ``docker_images`` list
            contains copies of the input images with
            ``nexus_validated`` populated.
        """
        if not self._docker_images:
            self._logger.info("No Docker images to validate; returning empty result")
            return CollectorResult()

        self._logger.info(
            "Validating %d Docker images against %s (workers=%d)",
            len(self._docker_images),
            self._nexus_url,
            self._concurrent_workers,
        )

        validated: list[DockerImage] = []

        with httpx.Client(timeout=self._timeout) as client:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self._concurrent_workers,
            ) as executor:
                futures = {
                    executor.submit(self._validate_image, client, img): img
                    for img in self._docker_images
                }
                for future in concurrent.futures.as_completed(futures):
                    original = futures[future]
                    try:
                        validated.append(future.result())
                    except Exception:
                        self._logger.exception(
                            "Unexpected error validating %s:%s",
                            original.image,
                            original.tag,
                        )
                        validated.append(
                            original.model_copy(
                                update={"nexus_validated": False},
                            )
                        )

        validated.sort(key=lambda d: (d.image, d.tag))

        passed = sum(1 for d in validated if d.nexus_validated)
        self._logger.info(
            "Nexus validation complete: %d/%d images verified",
            passed,
            len(validated),
        )

        return CollectorResult(docker_images=validated)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _validate_image(
        self,
        client: httpx.Client,
        image: DockerImage,
    ) -> DockerImage:
        """Check whether a single image:tag exists in the registry.

        Issues a ``HEAD`` request to the Docker Registry V2 manifests
        endpoint for the specific tag, avoiding the overhead of
        fetching the full tag list.

        Args:
            client: An :class:`httpx.Client` to use for the request.
            image: The :class:`DockerImage` to validate.

        Returns:
            A copy of *image* with ``nexus_validated`` set to
            ``True`` when the tag exists, or ``False`` otherwise.
        """
        url = f"{self._nexus_url}/v2/{image.image}/manifests/{image.tag}"
        self._logger.debug("Checking %s:%s -> %s", image.image, image.tag, url)

        try:
            response = client.head(
                url,
                headers={
                    "Accept": (
                        "application/vnd.docker.distribution.manifest.v2+json, "
                        "application/vnd.oci.image.manifest.v1+json, "
                        "application/vnd.docker.distribution.manifest.list.v2+json, "
                        "application/vnd.oci.image.index.v1+json"
                    ),
                },
            )
            found = response.status_code == 200

            if found:
                self._logger.debug(
                    "Tag %s found for %s",
                    image.tag,
                    image.image,
                )
            elif response.status_code == 404:
                self._logger.info(
                    "Tag %s NOT found for %s (HTTP %d)",
                    image.tag,
                    image.image,
                    response.status_code,
                )
            else:
                self._logger.warning(
                    "Unexpected HTTP %d when checking %s:%s",
                    response.status_code,
                    image.image,
                    image.tag,
                )

            result: DockerImage = image.model_copy(
                update={"nexus_validated": found},
            )
            return result

        except httpx.HTTPError as exc:
            self._logger.warning(
                "HTTP error validating %s:%s: %s",
                image.image,
                image.tag,
                exc,
            )
            result = image.model_copy(update={"nexus_validated": False})
            return result

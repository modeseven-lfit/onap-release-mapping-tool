# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Gerrit REST API collector - discovers ONAP projects via Gerrit."""

from __future__ import annotations

import json
import time
from typing import Any, Literal
from urllib.parse import quote

import httpx

from onap_release_map.collectors import BaseCollector, CollectorResult, registry
from onap_release_map.models import OnapRepository

# Gerrit prefixes all JSON responses with this magic string to
# prevent cross-site scripting.  It must be stripped before parsing.
_GERRIT_MAGIC_PREFIX = ")]}'\n"


@registry.register
class GerritCollector(BaseCollector):
    """Collect ONAP repository metadata from the Gerrit REST API.

    Queries the ``/projects/`` endpoint for both ``ACTIVE`` and
    ``READ_ONLY`` projects and produces an :class:`OnapRepository` for
    each one.  No authentication is required; the ONAP Gerrit instance
    supports anonymous read access.
    """

    name = "gerrit"

    def __init__(
        self,
        gerrit_url: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: object,
    ) -> None:
        """Initialise the Gerrit collector.

        Args:
            gerrit_url: Base URL of the Gerrit instance.  Defaults to
                ``https://gerrit.onap.org/r``.
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum number of retry attempts per request.
            **kwargs: Passed through to :class:`BaseCollector`.
        """
        super().__init__()
        self._gerrit_url = (gerrit_url or "https://gerrit.onap.org/r").rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def collect(self, **kwargs: object) -> CollectorResult:
        """Query Gerrit for all ONAP projects and return the results.

        Two queries are made: one for ``ACTIVE`` projects and one for
        ``READ_ONLY`` (archived) projects.  Each discovered project is
        converted into an :class:`OnapRepository`.

        Raises:
            RuntimeError: If all fetch attempts failed and no
                repositories were collected.

        Returns:
            A :class:`CollectorResult` containing the discovered
            repositories.
        """
        repositories: dict[str, OnapRepository] = {}
        fetch_errors: list[str] = []

        with httpx.Client(timeout=self._timeout) as client:
            for state in ("ACTIVE", "READ_ONLY"):
                self._logger.info("Querying Gerrit for %s projects", state)
                try:
                    projects = self._fetch_projects(client, state)
                except RuntimeError as exc:
                    msg = f"Failed to fetch {state} projects: {exc}"
                    self._logger.warning(msg)
                    fetch_errors.append(msg)
                    continue
                self._logger.info(
                    "Discovered %d %s projects from Gerrit",
                    len(projects),
                    state,
                )
                for project_name in projects:
                    repo = self._make_repository(
                        project_name,
                        state,
                    )
                    repositories[project_name] = repo

        if not repositories and fetch_errors:
            raise RuntimeError(
                "Gerrit collection failed: " + "; ".join(fetch_errors)
            )

        sorted_repos = sorted(repositories.values(), key=lambda r: r.gerrit_project)
        self._logger.info(
            "Gerrit collector produced %d repositories in total",
            len(sorted_repos),
        )
        return CollectorResult(repositories=sorted_repos)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _fetch_projects(
        self,
        client: httpx.Client,
        state: str,
    ) -> dict[str, dict[str, Any]]:
        """Fetch all projects in the given *state* from Gerrit.

        Handles pagination transparently: Gerrit returns at most 500
        entries per page.  When the response contains a ``_more_projects``
        marker the next page is requested after a polite 1-second delay.

        Args:
            state: Gerrit project state filter (``ACTIVE`` or
                ``READ_ONLY``).

        Returns:
            A mapping of project name to project metadata dict.
        """
        all_projects: dict[str, dict[str, Any]] = {}
        start = 0

        while True:
            url = (
                f"{self._gerrit_url}/projects/?type=ALL&d&state={state}&S={start}&n=500"
            )
            data = self._get_json(client, url)
            if not data:
                break

            # Gerrit may signal pagination via a top-level
            # *_more_projects* key.  Remove it so it is not
            # treated as a project or counted in the offset.
            has_more = False
            if "_more_projects" in data:
                has_more = bool(data.pop("_more_projects"))

            all_projects.update(data)

            # Also check per-project markers (the more common
            # Gerrit response style).
            if not has_more:
                has_more = any(
                    isinstance(v, dict) and v.get("_more_projects")
                    for v in data.values()
                )

            if has_more:
                start += len(data)
                self._logger.debug("Pagination: fetching next page (offset %d)", start)
                time.sleep(1)
            else:
                break

        return all_projects

    def _get_json(self, client: httpx.Client, url: str) -> dict[str, Any]:
        """Perform a GET request and return parsed JSON.

        Strips the Gerrit magic prefix from the response body and
        retries on transient errors up to ``max_retries`` times.

        Args:
            url: Fully-qualified URL to fetch.

        Returns:
            Parsed JSON as a dictionary, or an empty dict on failure.
        """
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                self._logger.debug(
                    "GET %s (attempt %d/%d)", url, attempt, self._max_retries
                )
                response = client.get(url)
                response.raise_for_status()

                body = response.text
                if body.startswith(_GERRIT_MAGIC_PREFIX):
                    body = body[len(_GERRIT_MAGIC_PREFIX) :]

                result: dict[str, Any] = json.loads(body)
                return result

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                self._logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries:
                    time.sleep(1)
            except (json.JSONDecodeError, ValueError) as exc:
                self._logger.error("Failed to parse Gerrit response: %s", exc)
                return {}

        msg = (
            f"All {self._max_retries} attempts to fetch "
            f"{url} failed: {last_exc}"
        )
        self._logger.error(msg)
        raise RuntimeError(msg)

    def _make_repository(
        self,
        project_name: str,
        state: Literal["ACTIVE", "READ_ONLY"],
    ) -> OnapRepository:
        """Convert a Gerrit project entry into an OnapRepository.

        Args:
            project_name: Full Gerrit project path (e.g. ``policy/api``).
            state: The Gerrit state used in the query (``ACTIVE`` or
                ``READ_ONLY``).

        Returns:
            A populated :class:`OnapRepository` instance.
        """
        top_level = project_name.split("/")[0]
        encoded_name = quote(project_name, safe="")
        gerrit_url = f"{self._gerrit_url}/admin/repos/{encoded_name}"

        return OnapRepository(
            gerrit_project=project_name,
            top_level_project=top_level,
            gerrit_url=gerrit_url,
            confidence="medium",
            confidence_reasons=["Discovered via Gerrit REST API"],
            category="runtime",
            gerrit_state=state,
            discovered_by=["gerrit"],
        )

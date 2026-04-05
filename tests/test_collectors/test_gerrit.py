# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the Gerrit REST API collector."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from onap_release_map.collectors.gerrit import GerritCollector

GERRIT_URL = "https://gerrit.example.com/r"
MAGIC_PREFIX = ")]}'\n"


def _gerrit_response(payload: str, status_code: int = 200) -> httpx.Response:
    """Build an ``httpx.Response`` with the Gerrit magic prefix."""
    return httpx.Response(status_code, text=f"{MAGIC_PREFIX}{payload}")


def _active_url(offset: int = 0) -> str:
    """Return the ACTIVE projects endpoint URL for the given offset."""
    return f"{GERRIT_URL}/projects/?type=ALL&d&state=ACTIVE&S={offset}&n=500"


def _readonly_url(offset: int = 0) -> str:
    """Return the READ_ONLY projects endpoint URL for the given offset."""
    return f"{GERRIT_URL}/projects/?type=ALL&d&state=READ_ONLY&S={offset}&n=500"


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_collect_basic(_mock_sleep: object) -> None:
    """Collect ACTIVE and READ_ONLY projects from mocked Gerrit."""
    active_body = (
        '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}, '
        '"aai/resources": {"id": "aai%2Fresources", "state": "ACTIVE"}}'
    )
    readonly_body = '{"aaf/authz": {"id": "aaf%2Fauthz", "state": "READ_ONLY"}}'

    respx.get(_active_url()).mock(
        return_value=_gerrit_response(active_body),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response(readonly_body),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)
    result = collector.collect()

    repos_by_name = {r.gerrit_project: r for r in result.repositories}

    assert len(result.repositories) == 3
    assert repos_by_name["policy/api"].gerrit_state == "ACTIVE"
    assert repos_by_name["aai/resources"].gerrit_state == "ACTIVE"
    assert repos_by_name["aaf/authz"].gerrit_state == "READ_ONLY"

    for repo in result.repositories:
        assert repo.confidence == "medium"
        assert repo.discovered_by == ["gerrit"]


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_magic_prefix_stripping(_mock_sleep: object) -> None:
    """Verify the Gerrit magic prefix is stripped before JSON parsing."""
    body_json = '{"demo/project": {"id": "demo%2Fproject", "state": "ACTIVE"}}'
    raw_body = f"{MAGIC_PREFIX}{body_json}"

    respx.get(_active_url()).mock(
        return_value=httpx.Response(200, text=raw_body),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)
    result = collector.collect()

    assert len(result.repositories) == 1
    assert result.repositories[0].gerrit_project == "demo/project"


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_retry_on_error(_mock_sleep: object) -> None:
    """Collector retries after a transient 500 and succeeds."""
    active_body = '{"sdc/sdc-be": {"id": "sdc%2Fsdc-be", "state": "ACTIVE"}}'

    # First attempt fails, second succeeds.
    respx.get(_active_url()).mock(
        side_effect=[
            httpx.Response(500, text="Internal Server Error"),
            _gerrit_response(active_body),
        ],
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=3)
    result = collector.collect()

    repos_by_name = {r.gerrit_project: r for r in result.repositories}
    assert "sdc/sdc-be" in repos_by_name


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_all_retries_fail(_mock_sleep: object) -> None:
    """Collector raises RuntimeError when all retries are exhausted."""
    respx.get(_active_url()).mock(
        return_value=httpx.Response(500, text="fail"),
    )
    respx.get(_readonly_url()).mock(
        return_value=httpx.Response(500, text="fail"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=2)

    with pytest.raises(RuntimeError, match="Gerrit collection failed"):
        collector.collect()


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_all_retries_fail_timed(_mock_sleep: object) -> None:
    """timed_collect surfaces fetch failures in execution.errors."""
    respx.get(_active_url()).mock(
        return_value=httpx.Response(500, text="fail"),
    )
    respx.get(_readonly_url()).mock(
        return_value=httpx.Response(500, text="fail"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=2)
    result = collector.timed_collect()

    assert result.repositories == []
    assert result.execution is not None
    assert len(result.execution.errors) > 0
    assert "Gerrit collection failed" in result.execution.errors[0]


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_pagination(_mock_sleep: object) -> None:
    """Collector follows ``_more_projects`` pagination marker."""
    page1_body = (
        '{"so/so": {"id": "so%2Fso", "state": "ACTIVE", "_more_projects": true}}'
    )
    page2_body = '{"so/libs": {"id": "so%2Flibs", "state": "ACTIVE"}}'

    respx.get(_active_url(offset=0)).mock(
        return_value=_gerrit_response(page1_body),
    )
    respx.get(_active_url(offset=1)).mock(
        return_value=_gerrit_response(page2_body),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)
    result = collector.collect()

    names = {r.gerrit_project for r in result.repositories}
    assert "so/so" in names
    assert "so/libs" in names
    assert len(result.repositories) == 2


def test_gerrit_registration() -> None:
    """GerritCollector is discoverable through the collector registry."""
    from onap_release_map.collectors import registry

    cls = registry.get("gerrit")
    assert cls is not None
    assert cls is GerritCollector


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_cache_hit(_mock_sleep: object) -> None:
    """Second identical request is served from cache; only one HTTP call."""
    active_body = '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}}'

    route_active = respx.get(_active_url()).mock(
        return_value=_gerrit_response(active_body),
    )
    route_readonly = respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)

    result1 = collector.collect()
    assert len(result1.repositories) == 1

    # Record call counts after first collect.
    active_calls_after_first = route_active.call_count
    readonly_calls_after_first = route_readonly.call_count

    result2 = collector.collect()
    assert len(result2.repositories) == 1

    # Second collect must not issue any new HTTP requests (cache hit).
    assert route_active.call_count == active_calls_after_first
    assert route_readonly.call_count == readonly_calls_after_first


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_clear_cache(_mock_sleep: object) -> None:
    """After clear_cache(), the same request triggers a fresh HTTP call."""
    active_body = '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}}'

    route_active = respx.get(_active_url()).mock(
        return_value=_gerrit_response(active_body),
    )
    route_readonly = respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)

    result1 = collector.collect()
    assert len(result1.repositories) == 1

    active_calls_after_first = route_active.call_count
    readonly_calls_after_first = route_readonly.call_count

    collector.clear_cache()

    result2 = collector.collect()
    assert len(result2.repositories) == 1

    # After clearing the cache, fresh HTTP requests must be issued.
    assert route_active.call_count == active_calls_after_first + 1
    assert route_readonly.call_count == readonly_calls_after_first + 1


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_cache_safe_with_pagination(_mock_sleep: object) -> None:
    """Cached responses with _more_projects are not corrupted by mutation.

    _fetch_projects() pops the _more_projects key from the response
    dict.  The cache must return a defensive copy so that the stored
    value remains intact for later calls.
    """
    # First page has a pagination marker; second page does not.
    page1_body = (
        '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}, '
        '"_more_projects": true}'
    )
    page2_body = '{"aai/aai-common": {"id": "aai%2Faai-common", "state": "ACTIVE"}}'

    active_url_page1 = f"{GERRIT_URL}/projects/?type=ALL&d&state=ACTIVE&S=0&n=500"
    active_url_page2 = f"{GERRIT_URL}/projects/?type=ALL&d&state=ACTIVE&S=1&n=500"

    respx.get(active_url_page1).mock(
        return_value=_gerrit_response(page1_body),
    )
    respx.get(active_url_page2).mock(
        return_value=_gerrit_response(page2_body),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)

    result1 = collector.collect()
    names1 = {r.gerrit_project for r in result1.repositories}
    assert "policy/api" in names1
    assert "aai/aai-common" in names1

    # Second collect uses the cache.  If the cached page-1 dict was
    # mutated (pop removed _more_projects), the collector would stop
    # after page 1 and miss aai/aai-common.
    result2 = collector.collect()
    names2 = {r.gerrit_project for r in result2.repositories}
    assert "policy/api" in names2
    assert "aai/aai-common" in names2
    assert names1 == names2


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_gerrit_top_level_project(_mock_sleep: object) -> None:
    """``top_level_project`` is the first path component of the name."""
    active_body = (
        '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}, '
        '"cps": {"id": "cps", "state": "ACTIVE"}}'
    )

    respx.get(_active_url()).mock(
        return_value=_gerrit_response(active_body),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)
    result = collector.collect()

    repos_by_name = {r.gerrit_project: r for r in result.repositories}
    assert repos_by_name["policy/api"].top_level_project == "policy"
    assert repos_by_name["cps"].top_level_project == "cps"


# -----------------------------------------------------------------
# State-based filtering tests
# -----------------------------------------------------------------


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_states_active_only(_mock_sleep: object) -> None:
    """When states=["ACTIVE"], only ACTIVE projects are queried."""
    active_body = '{"policy/api": {"id": "policy%2Fapi", "state": "ACTIVE"}}'

    respx.get(_active_url()).mock(
        return_value=_gerrit_response(active_body),
    )
    # READ_ONLY endpoint must NOT be called.
    route_readonly = respx.get(_readonly_url()).mock(
        return_value=_gerrit_response("{}"),
    )

    collector = GerritCollector(
        gerrit_url=GERRIT_URL,
        max_retries=1,
        states=["ACTIVE"],
    )
    result = collector.collect()

    assert len(result.repositories) == 1
    assert result.repositories[0].gerrit_project == "policy/api"
    assert result.repositories[0].gerrit_state == "ACTIVE"
    assert route_readonly.call_count == 0


@respx.mock
@patch("onap_release_map.collectors.gerrit.time.sleep")
def test_states_readonly_only(_mock_sleep: object) -> None:
    """When states=["READ_ONLY"], only READ_ONLY projects are queried."""
    readonly_body = '{"aaf/authz": {"id": "aaf%2Fauthz", "state": "READ_ONLY"}}'

    route_active = respx.get(_active_url()).mock(
        return_value=_gerrit_response("{}"),
    )
    respx.get(_readonly_url()).mock(
        return_value=_gerrit_response(readonly_body),
    )

    collector = GerritCollector(
        gerrit_url=GERRIT_URL,
        max_retries=1,
        states=["READ_ONLY"],
    )
    result = collector.collect()

    assert len(result.repositories) == 1
    assert result.repositories[0].gerrit_project == "aaf/authz"
    assert result.repositories[0].gerrit_state == "READ_ONLY"
    assert route_active.call_count == 0


def test_states_invalid_value() -> None:
    """Passing an unrecognised state raises ValueError."""
    with pytest.raises(ValueError, match="Invalid Gerrit state"):
        GerritCollector(
            gerrit_url=GERRIT_URL,
            states=["ACTIVE", "BOGUS"],  # type: ignore[list-item]
        )


def test_states_bare_string_rejected() -> None:
    """Passing a bare string instead of a list raises TypeError."""
    with pytest.raises(TypeError, match="must be a list of strings"):
        GerritCollector(
            gerrit_url=GERRIT_URL,
            states="ACTIVE",  # type: ignore[arg-type]
        )


def test_states_default_backward_compat() -> None:
    """When states is None the default includes both states."""
    collector = GerritCollector(gerrit_url=GERRIT_URL, max_retries=1)
    assert set(collector.states) == {"ACTIVE", "READ_ONLY"}


def test_states_property() -> None:
    """The states property reflects the configured filter."""
    collector = GerritCollector(
        gerrit_url=GERRIT_URL,
        max_retries=1,
        states=["ACTIVE"],
    )
    assert collector.states == ("ACTIVE",)

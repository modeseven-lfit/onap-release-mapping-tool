# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the image mapper."""

from __future__ import annotations

from onap_release_map.parsers.image_mapper import (
    ImageMapper,
    MappingReason,
    MappingResult,
)


class TestImageMapper:
    """Tests for :class:`ImageMapper` legacy behaviour."""

    def test_explicit_mapping(self) -> None:
        """Test explicit mapping lookup."""
        mapper = ImageMapper()
        assert mapper.map_image("onap/policy-api") == "policy/api"
        assert mapper.map_image("onap/ccsdk-blueprintsprocessor") == "ccsdk/cds"

    def test_org_onap_heuristic(self) -> None:
        """Test org.onap.* heuristic mapping."""
        mapper = ImageMapper()
        # Use an image NOT in the explicit mapping table so the
        # org.onap.* heuristic code path is actually exercised.
        result = mapper.map_image("onap/org.onap.fake.project.submod")
        assert result == "fake/project"

    def test_slash_passthrough(self) -> None:
        """Test slash-based image names map directly."""
        mapper = ImageMapper()
        # Use an image NOT in the explicit mapping table so the
        # slash-passthrough heuristic code path is actually exercised.
        result = mapper.map_image("onap/fake-project/submodule")
        assert result == "fake-project/submodule"

    def test_get_top_level_project(self) -> None:
        """Test top-level project extraction."""
        mapper = ImageMapper()
        assert mapper.get_top_level_project("policy/api") == "policy"
        assert mapper.get_top_level_project("cps") == "cps"
        assert mapper.get_top_level_project("so/adapters/foo") == "so"

    def test_unmapped_image_returns_none(self) -> None:
        """Test that unmapped images return None."""
        mapper = ImageMapper()
        result = mapper.map_image("unknown/random-image")
        assert result is None


class TestLongestMatchAttribution:
    """Tests for the longest-match algorithm using known_projects."""

    # Representative slice of the real ONAP Gerrit project list.
    # Includes the nested paths that previously broke attribution
    # (so/adapters/*, cps/cps-temporal, so/so-etsi-nfvo) so these
    # tests act as regression checks for the reported bugs.
    ONAP_PROJECTS = frozenset(
        {
            "aai",
            "aai/aai-common",
            "aai/babel",
            "aai/graphadmin",
            "aai/model-loader",
            "aai/resources",
            "aai/schema-service",
            "aai/sparky-be",
            "aai/traversal",
            "ccsdk/apps",
            "ccsdk/cds",
            "ccsdk/distribution",
            "ccsdk/oran",
            "cps",
            "cps/cps-temporal",
            "cps/ncmp-dmi-plugin",
            "dcaegen2/collectors/hv-ves",
            "dcaegen2/collectors/ves",
            "dcaegen2/deployments",
            "dcaegen2/platform/ves-openapi-manager",
            "dcaegen2/services",
            "dcaegen2/services/prh",
            "integration/docker/onap-java11",
            "multicloud/framework",
            "multicloud/k8s",
            "multicloud/openstack",
            "oom",
            "oom/platform/cert-service",
            "oom/readiness",
            "policy/api",
            "policy/apex-pdp",
            "policy/clamp",
            "policy/distribution",
            "policy/docker",
            "policy/drools-pdp",
            "policy/opa-pdp",
            "policy/pap",
            "policy/xacml-pdp",
            "portal-ng/bff",
            "portal-ng/history",
            "portal-ng/preferences",
            "portal-ng/ui",
            "sdc",
            "sdc/sdc-helm-validator",
            "sdc/sdc-workflow-designer",
            "sdnc/oam",
            "so",
            "so/adapters/so-cnf-adapter",
            "so/adapters/so-etsi-sol003-adapter",
            "so/adapters/so-etsi-sol005-adapter",
            "so/adapters/so-nssmf-adapter",
            "so/adapters/so-oof-adapter",
            "so/so-admin-cockpit",
            "so/so-etsi-nfvo",
            "testsuite",
            "usecase-ui",
            "usecase-ui/intent-analysis",
            "usecase-ui/llm-adaptation",
            "usecase-ui/nlp",
            "usecase-ui/server",
        }
    )

    def test_has_ground_truth_flag(self) -> None:
        """``has_ground_truth`` reflects whether a set was supplied."""
        assert ImageMapper().has_ground_truth is False
        assert ImageMapper(known_projects=set()).has_ground_truth is False
        assert ImageMapper(known_projects=self.ONAP_PROJECTS).has_ground_truth is True

    def test_known_projects_normalised_to_frozenset(self) -> None:
        """``known_projects`` is exposed as an immutable frozenset."""
        mapper = ImageMapper(known_projects={"a/b", "c/d"})
        assert isinstance(mapper.known_projects, frozenset)
        assert mapper.known_projects == frozenset({"a/b", "c/d"})

    def test_image_path_equals_known_project_resolves_via_leaf_match(self) -> None:
        """When the image path equals a Gerrit path, leaf-match still wins.

        The former "direct hit" stage was removed because it could
        short-circuit a deeper longest-match candidate. Now stage 2
        (leaf-match) considers the image's own path alongside any
        deeper siblings sharing the same leaf segment. When there is
        only one candidate with that leaf, the result is equivalent
        to a direct hit.
        """
        # We construct a minimal ground truth that deliberately has
        # no overlap with the shipped overrides so stage 1 is skipped.
        mapper = ImageMapper(known_projects={"fake-proj/component"})
        result = mapper.resolve("onap/fake-proj/component")
        assert result.project == "fake-proj/component"
        assert result.reason is MappingReason.LEAF_MATCH_NAMESPACE
        assert result.verified is True

    def test_leaf_match_prefers_in_namespace_over_cross_namespace(self) -> None:
        """In-namespace leaf match wins even when a cross match exists."""
        ground_truth = {
            "so/adapters/widget",
            "aai/widget",
        }
        mapper = ImageMapper(known_projects=ground_truth)
        result = mapper.resolve("onap/so/widget")
        assert result.project == "so/adapters/widget"
        assert result.reason is MappingReason.LEAF_MATCH_NAMESPACE

    def test_leaf_match_falls_back_to_cross_namespace(self) -> None:
        """When nothing in-namespace matches, cross-namespace is tried."""
        ground_truth = {"other/widget"}
        mapper = ImageMapper(known_projects=ground_truth)
        result = mapper.resolve("onap/so/widget")
        assert result.project == "other/widget"
        assert result.reason is MappingReason.LEAF_MATCH_CROSS_NAMESPACE

    def test_leaf_match_picks_deepest_within_namespace(self) -> None:
        """Longest path wins over shorter paths within a namespace."""
        ground_truth = {
            "so/widget",
            "so/adapters/widget",
            "so/adapters/deep/widget",
        }
        mapper = ImageMapper(known_projects=ground_truth)
        result = mapper.resolve("onap/so/widget")
        assert result.project == "so/adapters/deep/widget"
        # The two other candidates are reported as alternatives so
        # validators and exporters can surface the choice.
        assert "so/widget" in result.alternatives
        assert "so/adapters/widget" in result.alternatives

    def test_leaf_match_deterministic_alphabetical_tiebreak(self) -> None:
        """Equal-depth candidates resolve alphabetically."""
        ground_truth = {
            "so/alpha/widget",
            "so/beta/widget",
        }
        mapper = ImageMapper(known_projects=ground_truth)
        result = mapper.resolve("onap/so/widget")
        assert result.project == "so/alpha/widget"
        assert result.alternatives == ("so/beta/widget",)

    def test_so_cnf_adapter_regression(self) -> None:
        """Regression: onap/so/so-cnf-adapter must not attribute to parent `so`.

        This is the exact scenario reported by the ONAP developer that
        motivated the rewrite. The correct Gerrit project is a deeper
        sibling of so-etsi-sol003-adapter et al.
        """
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        result = mapper.resolve("onap/so/so-cnf-adapter")
        assert result.project == "so/adapters/so-cnf-adapter"
        assert result.reason is MappingReason.LEAF_MATCH_NAMESPACE
        assert result.verified is True

    def test_cps_temporal_regression(self) -> None:
        """Regression: onap/cps-temporal must attribute to cps/cps-temporal.

        This previously landed on the parent `cps` repo because the
        shipped override table points at the parent. With ground truth
        from Gerrit, the leaf-match stage discovers the deeper real
        repo ``cps/cps-temporal`` and — per the "longest verified
        match always wins" rule — supersedes the parent-pointing
        override. The override itself is still reported as stale by
        the audit validator (covered by separate tests in PR 2).
        """
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        result = mapper.resolve("onap/cps-temporal")
        assert result.project == "cps/cps-temporal"
        # The image ``cps-temporal`` has no slash after the ``onap/``
        # prefix is stripped, so it has no declared namespace; every
        # leaf match is classified as cross-namespace. The project
        # path is still correct — this reason tag simply records that
        # the algorithm had to search across namespaces to find it.
        assert result.reason is MappingReason.LEAF_MATCH_CROSS_NAMESPACE
        assert result.verified is True

        # Without ground truth, the override wins unchallenged because
        # no competing candidate exists. This preserves offline and
        # partial-run behaviour where the override table is the only
        # authoritative signal available.
        offline = ImageMapper()
        offline_result = offline.resolve("onap/cps-temporal")
        assert offline_result.project == "cps"
        assert offline_result.reason is MappingReason.OVERRIDE
        assert offline_result.verified is False

    def test_so_etsi_nfvo_requires_override(self) -> None:
        """so-etsi-nfvo-ns-lcm has no leaf match; needs an explicit override.

        The image leaf ``so-etsi-nfvo-ns-lcm`` does not equal the Gerrit
        basename ``so-etsi-nfvo`` so stage 3 cannot recover it. This
        test documents that behaviour — the audit validator will flag
        the override as stale when/if it gets corrected to point at the
        real repo.
        """
        ground_truth = self.ONAP_PROJECTS | {"so"}
        mapper = ImageMapper(known_projects=ground_truth)
        # Shipped override maps to parent `so` (confidence preserved).
        result = mapper.resolve("onap/so/so-etsi-nfvo-ns-lcm")
        assert result.project == "so"
        assert result.reason is MappingReason.OVERRIDE
        assert result.verified is True

    def test_existing_so_adapters_still_resolve(self) -> None:
        """Existing correct SO adapter overrides remain correct."""
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        for adapter in (
            "so-etsi-sol003-adapter",
            "so-etsi-sol005-adapter",
            "so-nssmf-adapter",
            "so-oof-adapter",
        ):
            image = f"onap/so/{adapter}"
            result = mapper.resolve(image)
            assert result.project == f"so/adapters/{adapter}"
            assert result.verified is True

    def test_parent_attribution_preserved_when_no_sub_repo(self) -> None:
        """Images built from monorepos still attribute to the parent."""
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        # These SO images are built out of the top-level `so` monorepo
        # because no dedicated Gerrit subrepo exists.
        for img in (
            "onap/so/api-handler-infra",
            "onap/so/bpmn-infra",
            "onap/so/catalog-db-adapter",
            "onap/so/request-db-adapter",
            "onap/so/sdnc-adapter",
        ):
            result = mapper.resolve(img)
            assert result.project == "so"
            assert result.reason is MappingReason.OVERRIDE

    def test_stale_override_flagged(self) -> None:
        """Override resolving to a non-existent repo is flagged as stale."""
        # Ground truth does not include "made/up/repo".
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        mapper._mappings["onap/synthetic-image"] = "made/up/repo"  # noqa: SLF001
        result = mapper.resolve("onap/synthetic-image")
        assert result.project == "made/up/repo"
        assert result.reason is MappingReason.OVERRIDE_STALE
        assert result.verified is False

    def test_override_not_flagged_stale_without_ground_truth(self) -> None:
        """Without ground truth, overrides cannot be verified — never stale."""
        mapper = ImageMapper()  # no known_projects
        mapper._mappings["onap/synthetic-image"] = "made/up/repo"  # noqa: SLF001
        result = mapper.resolve("onap/synthetic-image")
        assert result.project == "made/up/repo"
        assert result.reason is MappingReason.OVERRIDE
        assert result.verified is False

    def test_heuristic_verified_when_result_in_ground_truth(self) -> None:
        """Heuristic output that matches a known project is reported as verified."""
        ground_truth = {"policy/fresh-repo"}
        mapper = ImageMapper(known_projects=ground_truth)
        # Use an image that is NOT in the shipped override table and
        # whose dash-heuristic guess matches the ground truth.
        result = mapper.resolve("onap/policy-fresh-repo")
        assert result.project == "policy/fresh-repo"
        assert result.reason is MappingReason.HEURISTIC_DASH_VERIFIED
        assert result.verified is True

    def test_heuristic_supersedes_shallower_verified_leaf_match(self) -> None:
        """Deepest verified wins even when a verified leaf match exists.

        Regression for the "always collect, then rank" contract. A
        verified leaf match at depth 0 (e.g. a top-level ``policy-api``
        repo) must not prevent the dash heuristic from contributing a
        deeper verified candidate (``policy/api``). The deepest
        verified candidate wins regardless of which stage produced it.

        Previously ``resolve()`` short-circuited heuristics whenever
        any leaf match was found, which meant a shallow verified leaf
        match could silently shadow a deeper verified heuristic guess.
        """
        ground_truth = {
            # Depth 0: what a naive leaf-match would find for the
            # image ``onap/policy-api`` (which has no slash after the
            # onap/ prefix, so leaf segment is ``policy-api``).
            "policy-api",
            # Depth 1: what the dash heuristic produces for the same
            # image. This is the deeper candidate and must win.
            "policy/api",
        }
        mapper = ImageMapper(known_projects=ground_truth)
        # Remove the shipped override for onap/policy-api so we
        # exercise the leaf-match vs heuristic arbitration directly.
        mapper._mappings.pop("onap/policy-api", None)  # noqa: SLF001

        result = mapper.resolve("onap/policy-api")
        assert result.project == "policy/api"
        assert result.verified is True
        # The winner was produced by the dash heuristic, so its reason
        # should reflect that — not the leaf-match stage.
        assert result.reason is MappingReason.HEURISTIC_DASH_VERIFIED

    def test_heuristic_unverified_reported_as_fallback(self) -> None:
        """Unverified heuristic output is labelled clearly for audit."""
        ground_truth = {"policy/something-else"}
        mapper = ImageMapper(known_projects=ground_truth)
        # Image leaf does not match the ground truth, so the dash
        # heuristic still produces a guess but it's not verified.
        result = mapper.resolve("onap/policy-ghost-repo")
        # Leaf "ghost-repo" has no match, so stage 3 returns None.
        # Stage 4 runs heuristics; dash-heuristic produces
        # "policy/ghost-repo" which is not in the ground truth.
        assert result.project == "policy/ghost-repo"
        assert result.reason is MappingReason.HEURISTIC_DASH_UNVERIFIED
        assert result.verified is False

    def test_non_onap_image_returns_unresolved(self) -> None:
        """Images outside the onap/ namespace skip heuristics."""
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        result = mapper.resolve("library/postgres")
        assert result.project is None
        assert result.reason is MappingReason.UNRESOLVED

    def test_registry_prefix_is_stripped(self) -> None:
        """Nexus / registry prefixes do not confuse the mapper."""
        mapper = ImageMapper(known_projects=self.ONAP_PROJECTS)
        result = mapper.resolve("nexus3.onap.org:10001/onap/so/so-cnf-adapter")
        assert result.project == "so/adapters/so-cnf-adapter"


class TestMappingResult:
    """Tests for the :class:`MappingResult` dataclass itself."""

    def test_default_alternatives_empty(self) -> None:
        """Default alternatives is an empty tuple."""
        result = MappingResult(
            project="foo/bar",
            reason=MappingReason.LEAF_MATCH_NAMESPACE,
            verified=True,
        )
        assert result.alternatives == ()

    def test_frozen_dataclass(self) -> None:
        """MappingResult is immutable to prevent accidental mutation."""
        result = MappingResult(project="x", reason=MappingReason.LEAF_MATCH_NAMESPACE)
        import dataclasses

        assert dataclasses.is_dataclass(result)
        # Frozen dataclasses raise FrozenInstanceError on assignment.
        try:
            result.project = "y"  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            pass
        else:
            msg = "MappingResult should be frozen"
            raise AssertionError(msg)

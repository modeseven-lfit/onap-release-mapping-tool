# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Tests for the mapping audit validator."""

from __future__ import annotations

from onap_release_map.models import (
    MANIFEST_SCHEMA_VERSION,
    DockerImage,
    ManifestSummary,
    OnapRelease,
    ReleaseManifest,
    ValidationCategory,
    ValidationSeverity,
)
from onap_release_map.validators import MappingAuditValidator

# Representative slice of the real ONAP Gerrit project list.
ONAP_PROJECTS = frozenset(
    {
        "aai/resources",
        "aai/schema-service",
        "ccsdk/cds",
        "ccsdk/oran",
        "cps",
        "cps/ncmp-dmi-plugin",
        "oom",
        "oom/platform/cert-service",
        "policy/api",
        "policy/apex-pdp",
        "sdc",
        "sdc/sdc-helm-validator",
        "sdc/sdc-workflow-designer",
        "sdnc/oam",
        "so",
        "so/adapters/so-cnf-adapter",
        "so/adapters/so-etsi-sol003-adapter",
        "so/adapters/so-nssmf-adapter",
        "so/so-admin-cockpit",
        "so/so-etsi-nfvo",
        "testsuite",
    }
)


def _make_manifest(images: list[DockerImage]) -> ReleaseManifest:
    """Build a minimal :class:`ReleaseManifest` wrapping *images*.

    ``schema_version`` is sourced from :data:`MANIFEST_SCHEMA_VERSION`
    so validator tests stay in lockstep with the single source of
    truth and do not need editing on every schema-version bump.
    Passing the constant explicitly (rather than relying on the model
    default) keeps the import from being flagged as unused and makes
    the dependency on the canonical version obvious to readers.
    """
    return ReleaseManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        tool_version="0.0.0-test",
        generated_at="2026-01-01T00:00:00Z",
        onap_release=OnapRelease(
            name="Test",
            oom_chart_version="0.0.0",
        ),
        summary=ManifestSummary(),
        docker_images=images,
    )


class TestMappingAuditValidator:
    """Tests for :class:`MappingAuditValidator`."""

    def test_clean_manifest_passes(self) -> None:
        """A manifest whose mappings all verify produces no findings."""
        images = [
            DockerImage(
                image="onap/so/so-cnf-adapter",
                tag="1.0.0",
                gerrit_project="so/adapters/so-cnf-adapter",
            ),
            DockerImage(
                image="onap/policy-api",
                tag="1.0.0",
                gerrit_project="policy/api",
            ),
        ]
        manifest = _make_manifest(images)

        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        report = validator.validate(manifest)

        assert report.validator == "mapping_audit"
        assert report.passed is True
        assert report.findings == []
        assert report.counts == {}

    def test_drift_classified_as_override_shadowed(self) -> None:
        """Manifest values disagreeing with a fresh resolve classify correctly.

        The manifest's recorded mapping (``so``) differs from what
        the fresh mapper produces (``so/adapters/so-cnf-adapter``),
        and no stale override is in play, so the drift must classify
        as ``OVERRIDE_SHADOWED`` (WARNING) rather than the stricter
        ``STALE_OVERRIDE_WITH_FIX`` (ERROR).
        """
        images = [
            DockerImage(
                image="onap/so/so-cnf-adapter",
                tag="1.0.0",
                # Manifest records the old (wrong) attribution to the
                # parent monorepo. The fresh resolve will disagree
                # because the leaf-match stage finds the real repo.
                gerrit_project="so",
            ),
        ]
        manifest = _make_manifest(images)

        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        report = validator.validate(manifest)

        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.OVERRIDE_SHADOWED
        assert finding.severity is ValidationSeverity.WARNING
        assert finding.image == "onap/so/so-cnf-adapter"
        assert finding.current_mapping == "so"
        assert finding.suggested_mapping == "so/adapters/so-cnf-adapter"

    def test_findings_sorted_by_severity_then_category_then_image(self) -> None:
        """Multi-finding reports respect the documented sort invariant.

        The validator promises that findings emerge in a deterministic
        order: ERROR before WARNING before INFO, and within each
        severity by category name then image reference. This test
        constructs a manifest that exercises all three severity levels
        with multiple images per level, then asserts that the returned
        order matches the documented rule exactly.
        """
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        # Two stale overrides to produce two ERROR findings that
        # differ on their image reference so the within-severity
        # image-alphabetical sort can be observed.
        validator._mapper._mappings["onap/zeta-synthetic"] = (  # noqa: SLF001
            "made/up/zeta"
        )
        validator._mapper._mappings["onap/alpha-synthetic"] = (  # noqa: SLF001
            "made/up/alpha"
        )
        images = [
            # Unresolved image at WARNING severity. Listed first so
            # the input ordering cannot accidentally produce the
            # expected output ordering.
            DockerImage(
                image="library/postgres",
                tag="14",
                gerrit_project=None,
            ),
            # Two STALE_OVERRIDE errors inserted in reverse alpha so
            # the sort actually has to do work.
            DockerImage(
                image="onap/zeta-synthetic",
                tag="1.0.0",
                gerrit_project="made/up/zeta",
            ),
            DockerImage(
                image="onap/alpha-synthetic",
                tag="1.0.0",
                gerrit_project="made/up/alpha",
            ),
            # Heuristic-unverified WARNING. Lands in the middle
            # severity bucket alongside the UNRESOLVED finding above.
            DockerImage(
                image="onap/policy-ghost-repo",
                tag="1.0.0",
                gerrit_project="policy/ghost-repo",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        # Project the report into (severity, category, image) tuples
        # so the test asserts on the sort keys directly rather than
        # whatever else the findings happen to carry.
        observed = [
            (f.severity.value, f.category.value, f.image) for f in report.findings
        ]

        # Expected order:
        # 1. Both ERROR / stale_override findings, alphabetical on
        #    image (alpha- before zeta-).
        # 2. The WARNING heuristic_unverified finding — category
        #    "heuristic_unverified" sorts alphabetically before
        #    "unresolved".
        # 3. The WARNING unresolved finding.
        assert observed == [
            ("error", "stale_override", "onap/alpha-synthetic"),
            ("error", "stale_override", "onap/zeta-synthetic"),
            ("warning", "heuristic_unverified", "onap/policy-ghost-repo"),
            ("warning", "unresolved", "library/postgres"),
        ]

    def test_stale_override_is_flagged_as_error(self) -> None:
        """Override pointing at a non-existent repo produces an ERROR."""
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        # Inject a bogus override directly into the validator's mapper
        # so we exercise the OVERRIDE_STALE code path without needing
        # to ship a fixture mapping file.
        validator._mapper._mappings["onap/synthetic"] = (  # noqa: SLF001
            "made/up/repo"
        )

        images = [
            DockerImage(
                image="onap/synthetic",
                tag="1.0.0",
                gerrit_project="made/up/repo",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.passed is False
        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.STALE_OVERRIDE
        assert finding.severity is ValidationSeverity.ERROR
        assert finding.current_mapping == "made/up/repo"

    def test_stale_override_with_fix_is_error(self) -> None:
        """Stale override silently corrected by longest-match is an ERROR.

        This is the exact drift pattern the
        :attr:`ValidationCategory.STALE_OVERRIDE_WITH_FIX` signal
        exists to describe. A reviewer-visible override points at a
        repo that does not exist in Gerrit (``made/up/parent``), but
        the manifest was produced while the override was in effect
        and the longest-match algorithm then discovered a deeper
        verified repo (``real/parent/widget``) that shares the image
        leaf. The manifest ends up with the pre-fix override value,
        which the audit should loudly flag so the data source can be
        corrected.
        """
        ground_truth = frozenset({"real/parent/widget"})
        validator = MappingAuditValidator(known_projects=ground_truth)
        # Inject a stale override that the mapper holds in state but
        # that was in effect when the manifest was produced.
        validator._mapper._mappings["onap/thing/widget"] = (  # noqa: SLF001
            "made/up/parent"
        )

        images = [
            DockerImage(
                image="onap/thing/widget",
                tag="1.0.0",
                # Pre-fix manifest value matches the stale override.
                gerrit_project="made/up/parent",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.passed is False
        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.STALE_OVERRIDE_WITH_FIX
        assert finding.severity is ValidationSeverity.ERROR
        assert finding.current_mapping == "made/up/parent"
        assert finding.suggested_mapping == "real/parent/widget"

    def test_drift_without_stale_override_is_override_shadowed(self) -> None:
        """Generic manifest/resolve drift stays classified as WARNING.

        When the manifest's recorded mapping disagrees with a fresh
        resolve but NO stale override matches the recorded value, the
        finding is plain :attr:`ValidationCategory.OVERRIDE_SHADOWED`
        at WARNING severity. This covers drift from manual edits,
        older tool versions, or upstream changes between collection
        and audit — cases that do NOT warrant the ERROR severity
        given to ``STALE_OVERRIDE_WITH_FIX``.
        """
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        # The manifest records an unrelated path (not from any
        # override). The fresh resolve produces the correct
        # attribution. No stale override is in play.
        images = [
            DockerImage(
                image="onap/so/so-cnf-adapter",
                tag="1.0.0",
                # Arbitrary manually-edited value that does not
                # correspond to any override in the mapping table.
                gerrit_project="sdc",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.OVERRIDE_SHADOWED
        assert finding.severity is ValidationSeverity.WARNING

    def test_heuristic_unverified_is_warning(self) -> None:
        """Heuristic guesses that don't verify are WARNINGs, not ERRORs."""
        # Ground truth intentionally excludes `policy/ghost-repo` so
        # the dash heuristic produces an unverified guess.
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        images = [
            DockerImage(
                image="onap/policy-ghost-repo",
                tag="1.0.0",
                gerrit_project="policy/ghost-repo",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        # Passed is True because no ERROR was produced, only WARNING.
        assert report.passed is True
        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.HEURISTIC_UNVERIFIED
        assert finding.severity is ValidationSeverity.WARNING
        assert finding.current_mapping == "policy/ghost-repo"
        assert finding.detail.get("heuristic", "").startswith("heuristic-")

    def test_cross_namespace_leaf_match_is_info(self) -> None:
        """Cross-namespace leaf matches surface as INFO for review."""
        # Ground truth has only one repo with the `widget` leaf, and
        # it is in a different top-level namespace from the image.
        ground_truth = frozenset({"other/widget"})
        validator = MappingAuditValidator(known_projects=ground_truth)
        images = [
            DockerImage(
                image="onap/so/widget",
                tag="1.0.0",
                gerrit_project="other/widget",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.passed is True
        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.CROSS_NAMESPACE_FALLBACK
        assert finding.severity is ValidationSeverity.INFO

    def test_ambiguous_leaf_is_info_with_alternatives(self) -> None:
        """When multiple repos share a leaf, alternatives are recorded."""
        ground_truth = frozenset(
            {
                "so/adapters/widget",
                "so/so-widget",
                "so/extra/widget",
            }
        )
        validator = MappingAuditValidator(known_projects=ground_truth)
        # Longest-match will pick one of the two deepest candidates
        # (so/adapters/widget or so/extra/widget). Whichever wins the
        # alphabetical tiebreak, the other should appear in alternatives.
        images = [
            DockerImage(
                image="onap/so/widget",
                tag="1.0.0",
                gerrit_project="so/adapters/widget",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        # We expect at least an AMBIGUOUS_LEAF finding.
        categories = [f.category for f in report.findings]
        assert ValidationCategory.AMBIGUOUS_LEAF in categories
        ambiguous = next(
            f
            for f in report.findings
            if f.category is ValidationCategory.AMBIGUOUS_LEAF
        )
        assert ambiguous.severity is ValidationSeverity.INFO
        assert ambiguous.alternatives  # non-empty

    def test_unresolved_image_is_warning(self) -> None:
        """Images that resolve to None are flagged for review."""
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        images = [
            DockerImage(
                image="library/postgres",
                tag="14",
                gerrit_project=None,
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.passed is True
        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.category is ValidationCategory.UNRESOLVED
        assert finding.severity is ValidationSeverity.WARNING

    def test_without_ground_truth_audit_is_skipped(self) -> None:
        """With no known_projects, the validator emits a single INFO."""
        validator = MappingAuditValidator()
        images = [
            DockerImage(
                image="onap/so/so-cnf-adapter",
                tag="1.0.0",
                gerrit_project="so",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.passed is True
        assert len(report.findings) == 1
        assert report.findings[0].severity is ValidationSeverity.INFO
        assert report.findings[0].category is ValidationCategory.AUDIT_SKIPPED
        assert "ground truth" in report.findings[0].reason.lower()

    def test_counts_aggregated_by_severity_and_category(self) -> None:
        """Counts dict groups findings by both severity and category."""
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        validator._mapper._mappings["onap/synthetic-a"] = (  # noqa: SLF001
            "made/up/a"
        )
        validator._mapper._mappings["onap/synthetic-b"] = (  # noqa: SLF001
            "made/up/b"
        )
        images = [
            DockerImage(
                image="onap/synthetic-a",
                tag="1.0.0",
                gerrit_project="made/up/a",
            ),
            DockerImage(
                image="onap/synthetic-b",
                tag="1.0.0",
                gerrit_project="made/up/b",
            ),
            DockerImage(
                image="onap/policy-ghost-repo",
                tag="1.0.0",
                gerrit_project="policy/ghost-repo",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        assert report.counts.get("severity:error") == 2
        assert report.counts.get("severity:warning") == 1
        assert report.counts.get("category:stale_override") == 2
        assert report.counts.get("category:heuristic_unverified") == 1
        assert report.passed is False

    def test_errors_sort_before_warnings_before_info(self) -> None:
        """Findings ordering: errors first, then warnings, then info."""
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        validator._mapper._mappings["onap/synthetic"] = (  # noqa: SLF001
            "made/up/repo"
        )
        images = [
            DockerImage(
                image="onap/policy-ghost-repo",
                tag="1.0.0",
                gerrit_project="policy/ghost-repo",
            ),
            DockerImage(
                image="library/postgres",
                tag="14",
                gerrit_project=None,
            ),
            DockerImage(
                image="onap/synthetic",
                tag="1.0.0",
                gerrit_project="made/up/repo",
            ),
        ]
        manifest = _make_manifest(images)
        report = validator.validate(manifest)

        severities = [f.severity for f in report.findings]
        # The first finding must be the ERROR; the last must be INFO
        # or a WARNING if no INFO-level findings were produced.
        assert severities[0] is ValidationSeverity.ERROR
        # Severities must be non-decreasing in the ordering defined
        # by the validator (ERROR < WARNING < INFO).
        severity_rank = {
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.INFO: 2,
        }
        ranks = [severity_rank[s] for s in severities]
        assert ranks == sorted(ranks)

    def test_validator_does_not_mutate_manifest(self) -> None:
        """Validators must be read-only with respect to manifest contents."""
        images = [
            DockerImage(
                image="onap/so/so-cnf-adapter",
                tag="1.0.0",
                gerrit_project="so",
            ),
        ]
        manifest = _make_manifest(images)
        original_mapping = manifest.docker_images[0].gerrit_project

        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        validator.validate(manifest)

        # The validator produced a suggestion but must not have
        # changed the manifest content itself.
        assert manifest.docker_images[0].gerrit_project == original_mapping

    def test_summary_reflects_pass_state(self) -> None:
        """Summary text matches whether findings were produced."""
        clean_manifest = _make_manifest(
            [
                DockerImage(
                    image="onap/policy-api",
                    tag="1.0.0",
                    gerrit_project="policy/api",
                ),
            ]
        )
        validator = MappingAuditValidator(known_projects=ONAP_PROJECTS)
        clean_report = validator.validate(clean_manifest)
        assert "verified" in clean_report.summary.lower()

        validator._mapper._mappings["onap/synthetic"] = (  # noqa: SLF001
            "made/up/repo"
        )
        noisy_manifest = _make_manifest(
            [
                DockerImage(
                    image="onap/synthetic",
                    tag="1.0.0",
                    gerrit_project="made/up/repo",
                ),
            ]
        )
        noisy_report = validator.validate(noisy_manifest)
        assert "error" in noisy_report.summary.lower()

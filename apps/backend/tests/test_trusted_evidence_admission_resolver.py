"""Trusted evidence-admission authority is derived from locked server state."""

from __future__ import annotations

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    PlanBindingRecord,
    PlanGraphRecord,
    PlanSuiteBindingRecord,
    RunRecord,
    SuiteBindingRecord,
    SuiteExecutionRecord,
    SystemScopeRecord,
    TargetBindingRecord,
    TrustPolicyBindingRecord,
)
from src.application.ports.evidence_admission import (
    EvidenceAdmissionAuthorityRecord,
    EvidenceAdmissionScope,
)
from src.application.services.evaluation_workbench_service import (
    _envelope_suite_binding,
    _envelope_target_binding,
    _envelope_trust_binding,
    _requested_plan_domain,
    _suite_domain,
    _target_domain,
    _trust_domain,
)
from src.application.services.trusted_evidence_admission_resolver import (
    TrustedEvidenceAdmissionResolver,
)
from src.domain.assurance.evaluation_v2 import (
    build_execution_envelope_v2,
    canonical_sha256,
    plan_content_projection,
)

NOW = datetime(2026, 8, 8, 8, 0, tzinfo=timezone.utc)
NONCE = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii").rstrip("=")


class FakeRepository:
    def __init__(self, authority: EvidenceAdmissionAuthorityRecord | None) -> None:
        self.authority = authority
        self.database_now = NOW
        self.references_exist = True
        self.load_calls: list[tuple[EvidenceAdmissionScope, str, str]] = []
        self.reference_calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def read_fresh_utc_now(self) -> datetime:
        return self.database_now

    def load_admission_authority_for_update(
        self,
        *,
        scope: EvidenceAdmissionScope,
        issuer_key: str,
        signer_key_id: str,
    ) -> EvidenceAdmissionAuthorityRecord | None:
        self.load_calls.append((scope, issuer_key, signer_key_id))
        return self.authority

    def restriction_references_exist(
        self,
        *,
        scope: EvidenceAdmissionScope,
        suite_version_ids: tuple[str, ...],
        target_version_ids: tuple[str, ...],
    ) -> bool:
        del scope
        self.reference_calls.append((suite_version_ids, target_version_ids))
        return self.references_exist


def _suite() -> SuiteBindingRecord:
    configuration_schema = {
        "type": "object",
        "properties": {"threshold": {"type": "number", "minimum": 0, "maximum": 1}},
        "required": ["threshold"],
        "additionalProperties": False,
    }
    configuration_defaults = {"threshold": 0.5}
    budgets = {"maxCases": 200}
    manifest = {
        "suiteRef": "fairmind/agent-safety@1.0.0",
        "ownerScope": "org-a",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "runnerImageDigest": None,
        "adapter": {"name": "inspect", "version": "0.3.0"},
        "configurationSchema": configuration_schema,
        "configurationDefaults": configuration_defaults,
        "requiredInputRoles": ["scenario_set"],
        "budgets": budgets,
        "resultContractVersion": "1.0.0",
    }
    return SuiteBindingRecord(
        id="suite-version-a",
        owner_organization_id="org-a",
        owner_scope="org-a",
        namespace="fairmind",
        name="agent-safety",
        version="1.0.0",
        suite_ref="fairmind/agent-safety@1.0.0",
        manifest=FrozenJsonObject.from_mapping(manifest),
        manifest_digest=canonical_sha256(manifest),
        target_kinds=("agent",),
        subject_kinds=("agent",),
        lifecycle_phases=("pre_deploy",),
        execution_depths=("deep",),
        delivery_modes=("external_provider",),
        worker_type="external_provider",
        runner_image_digest=None,
        adapter_name="inspect",
        adapter_version="0.3.0",
        configuration_schema=FrozenJsonObject.from_mapping(configuration_schema),
        configuration_defaults=FrozenJsonObject.from_mapping(configuration_defaults),
        required_input_roles=("scenario_set",),
        budgets=FrozenJsonObject.from_mapping(budgets),
        result_contract_version="1.0.0",
        status="active",
        created_by="catalog-admin",
        created_at=NOW.isoformat(),
    )


def _graph_and_run() -> tuple[PlanGraphRecord, RunRecord]:
    target_manifest = {
        "schemaVersion": "2.0.0",
        "inputs": {"scenario_set": {"kind": "content_digest", "sha256": "f" * 64}},
    }
    target = TargetBindingRecord(
        id="target-version-a",
        organization_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        target_key="agent-prod",
        target_kind="agent",
        version="1.0.0",
        system_version="2026.08",
        subject_kind="agent",
        subject_id="agent-prod",
        subject_version="sha-a",
        subject_digest="b" * 64,
        deployment_id="deployment-a",
        connector_binding_id=None,
        manifest=FrozenJsonObject.from_mapping(target_manifest),
        manifest_digest=canonical_sha256(target_manifest),
        status="active",
        supersedes_id=None,
        created_by="catalog-admin",
        created_at=NOW.isoformat(),
    )
    trust = TrustPolicyBindingRecord(
        id="trust-a",
        organization_id="org-a",
        version="1.0.0",
        policy=FrozenJsonObject.from_mapping({}),
        policy_hash=canonical_sha256({}),
        status="active",
    )
    selection = PlanSuiteBindingRecord(
        suite=_suite(),
        ordinal=0,
        configuration=FrozenJsonObject.from_mapping({"threshold": 0.5}),
        configuration_hash=canonical_sha256({"threshold": 0.5}),
    )
    plan = PlanBindingRecord(
        id="plan-a",
        organization_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        name="Agent release assurance",
        contract_version="2.0.0",
        target_version_id=target.id,
        target_kind="agent",
        lifecycle_phases=("pre_deploy",),
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy_version_id=trust.id,
        plan_content_hash="0" * 64,
        status="active",
        created_by="planner",
        updated_by="activator",
        created_at=NOW.isoformat(),
        updated_at=NOW.isoformat(),
    )
    graph = PlanGraphRecord(
        scope=SystemScopeRecord("org-a", "workspace-a", "system-a"),
        plan=plan,
        target=target,
        trust_policy=trust,
        suites=(selection,),
    )
    projection = plan_content_projection(
        org_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        target=_target_domain(target),
        plan=_requested_plan_domain(graph),
        trust_policy=_trust_domain(trust),
        suites=[_suite_domain(selection)],
    )
    plan = replace(plan, plan_content_hash=canonical_sha256(projection))
    graph = replace(graph, plan=plan)
    execution = SuiteExecutionRecord(
        id="suite-execution-a",
        suite_version_id=selection.suite.id,
        owner_scope="org-a",
        ordinal=0,
        technical_status="awaiting_evidence",
        evidence_result_status="pending",
        admission_status="pending",
        review_status="pending",
        freshness_status="current",
        evidence_run_id=None,
        passport_revision_id=None,
        linked_by=None,
        linked_at=None,
        result_summary=None,
        limitations=None,
        failure_code=None,
        failure_message=None,
        started_at=None,
        completed_at=None,
        created_at=NOW.isoformat(),
        updated_at=NOW.isoformat(),
    )
    envelope, _, envelope_hash = build_execution_envelope_v2(
        envelope_id="envelope-a",
        run_id="run-a",
        org_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        plan_id="plan-a",
        plan_content_hash=plan.plan_content_hash,
        target=_envelope_target_binding(target),
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy=_envelope_trust_binding(trust),
        nonce=NONCE,
        requester_id="requester-a",
        requested_at=NOW.isoformat(),
        suites=[
            _envelope_suite_binding(
                selection,
                execution_id=execution.id,
                target=target,
            )
        ],
    )
    run = RunRecord(
        id="run-a",
        organization_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        plan_id="plan-a",
        contract_version="2.0.0",
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        technical_status="awaiting_evidence",
        evidence_outcome="pending",
        overall_verdict="insufficient",
        layer_verdicts_schema_version="1.0.0",
        layer_verdicts=FrozenJsonObject.from_mapping(
            {
                "suites": {execution.id: "insufficient"},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
        suite_executions=(execution,),
        envelope_id="envelope-a",
        envelope_nonce=NONCE,
        envelope=FrozenJsonObject.from_mapping(envelope),
        envelope_hash=envelope_hash,
        verdict_version=0,
        requested_by="requester-a",
        started_at=None,
        completed_at=None,
        failure_code=None,
        failure_message=None,
        created_at=NOW.isoformat(),
        updated_at=NOW.isoformat(),
    )
    return graph, run


def _authority(**changes: object) -> EvidenceAdmissionAuthorityRecord:
    graph, run = _graph_and_run()
    values: dict[str, object] = {
        "scope": EvidenceAdmissionScope("org-a", "system-a", "run-a", "suite-execution-a"),
        "plan_graph": graph,
        "run": run,
        "issuer_internal_id": "issuer-row-a",
        "issuer_key": "issuer-protocol-a",
        "issuer_type": "external_provider",
        "issuer_status": "active",
        "source_restrictions": (),
        "suite_restrictions": (),
        "target_restrictions": (),
        "maximum_evidence_age_seconds": 3600,
        "unsigned_import_policy": "reject",
        "signing_key_internal_id": "signing-row-a",
        "signer_key_id": "key-protocol-a",
        "signer_algorithm": "Ed25519",
        "public_jwk": FrozenJsonObject.from_mapping(
            {"kty": "OKP", "crv": "Ed25519", "x": "A" * 43}
        ),
        "key_valid_from": NOW - timedelta(days=1),
        "key_valid_until": NOW + timedelta(days=1),
        "key_revoked_at": None,
    }
    values.update(changes)
    return EvidenceAdmissionAuthorityRecord(**values)


@pytest.mark.parametrize("parent_projection", ["pending", "raw_terminal"])
def test_terminal_but_unlinked_authority_accepts_only_narrow_parent_projections(
    parent_projection: str,
) -> None:
    authority = _authority()
    graph = authority.plan_graph
    first_selection = graph.suites[0]
    second_manifest = first_selection.suite.manifest.to_dict()
    second_manifest["suiteRef"] = "fairmind/agent-robustness@1.0.0"
    second_suite = replace(
        first_selection.suite,
        id="suite-version-b",
        name="agent-robustness",
        suite_ref="fairmind/agent-robustness@1.0.0",
        manifest=FrozenJsonObject.from_mapping(second_manifest),
        manifest_digest=canonical_sha256(second_manifest),
    )
    second_selection = replace(
        first_selection,
        suite=second_suite,
        ordinal=1,
    )
    graph = replace(graph, suites=(first_selection, second_selection))
    projection = plan_content_projection(
        org_id=graph.scope.organization_id,
        workspace_id=graph.scope.workspace_id,
        system_id=graph.scope.system_id,
        target=_target_domain(graph.target),
        plan=_requested_plan_domain(graph),
        trust_policy=_trust_domain(graph.trust_policy),
        suites=[_suite_domain(selection) for selection in graph.suites],
    )
    graph = replace(
        graph,
        plan=replace(graph.plan, plan_content_hash=canonical_sha256(projection)),
    )
    first_execution = replace(
        authority.run.suite_executions[0],
        technical_status="succeeded",
        evidence_result_status="failed",
        started_at=NOW.isoformat(),
        completed_at=NOW.isoformat(),
    )
    second_execution = replace(
        first_execution,
        id="suite-execution-b",
        suite_version_id=second_suite.id,
        ordinal=1,
        technical_status="failed",
        evidence_result_status="error",
        started_at=None,
    )
    envelope, _, envelope_hash = build_execution_envelope_v2(
        envelope_id=authority.run.envelope_id,
        run_id=authority.run.id,
        org_id=authority.run.organization_id,
        workspace_id=authority.run.workspace_id,
        system_id=authority.run.system_id,
        plan_id=authority.run.plan_id,
        plan_content_hash=graph.plan.plan_content_hash,
        target=_envelope_target_binding(graph.target),
        trigger=authority.run.trigger,
        lifecycle_phase=authority.run.lifecycle_phase,
        execution_depth=graph.plan.execution_depth,
        enforcement_mode=graph.plan.enforcement_mode,
        delivery_mode=graph.plan.delivery_mode,
        trust_policy=_envelope_trust_binding(graph.trust_policy),
        nonce=authority.run.envelope_nonce,
        requester_id=authority.run.requested_by,
        requested_at=authority.run.created_at,
        suites=[
            _envelope_suite_binding(
                selection,
                execution_id=execution.id,
                target=graph.target,
            )
            for selection, execution in zip(
                graph.suites,
                (first_execution, second_execution),
                strict=True,
            )
        ],
    )
    run_changes: dict[str, object] = {
        "suite_executions": (first_execution, second_execution),
        "envelope": FrozenJsonObject.from_mapping(envelope),
        "envelope_hash": envelope_hash,
        "layer_verdicts": FrozenJsonObject.from_mapping(
            {
                "suites": {
                    first_execution.id: "insufficient",
                    second_execution.id: "insufficient",
                },
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
    }
    if parent_projection == "raw_terminal":
        run_changes.update(
            technical_status="failed",
            evidence_outcome="failed",
            started_at=NOW.isoformat(),
            completed_at=NOW.isoformat(),
        )
    authority = replace(
        authority,
        plan_graph=graph,
        run=replace(authority.run, **run_changes),
    )

    context = TrustedEvidenceAdmissionResolver(FakeRepository(authority)).resolve(
        scope=authority.scope,
        issuer_key=authority.issuer_key,
        signer_key_id=authority.signer_key_id,
    )

    assert context.authority.run.suite_executions[0].evidence_run_id is None
    assert context.authority.run.technical_status == (
        "awaiting_evidence" if parent_projection == "pending" else "failed"
    )


def test_resolver_returns_protocol_identities_and_database_clock() -> None:
    authority = _authority(
        source_restrictions=("external_provider",),
        suite_restrictions=("suite-version-a",),
        target_restrictions=("target-version-a",),
    )
    repository = FakeRepository(authority)

    context = TrustedEvidenceAdmissionResolver(repository).resolve(
        scope=authority.scope,
        issuer_key="issuer-protocol-a",
        signer_key_id="key-protocol-a",
    )

    assert context.database_now == NOW
    assert context.trusted_key.issuer_id == "issuer-protocol-a"
    assert context.trusted_key.key_id == "key-protocol-a"
    assert context.trusted_key.issuer_id != authority.issuer_internal_id
    assert context.trusted_key.key_id != authority.signing_key_internal_id
    assert context.expected_binding.workspace_id == "workspace-a"
    assert repository.reference_calls == [(("suite-version-a",), ("target-version-a",))]
    assert len(context.authority_hash) == 64


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"issuer_status": "revoked"}, "evidence_issuer_untrusted"),
        ({"issuer_type": "fairmind_worker"}, "evidence_issuer_untrusted"),
        ({"maximum_evidence_age_seconds": 0}, "trust_policy_invalid"),
        ({"unsigned_import_policy": "allow"}, "trust_policy_invalid"),
        ({"source_restrictions": ("fairmind_worker",)}, "evidence_issuer_restricted"),
        (
            {"source_restrictions": ("external_provider", "bogus")},
            "evidence_issuer_restriction_invalid",
        ),
        (
            {"source_restrictions": ("external_provider", "external_provider")},
            "evidence_issuer_restriction_invalid",
        ),
        (
            {"source_restrictions": ("external_provider", "")},
            "evidence_issuer_restriction_invalid",
        ),
        ({"suite_restrictions": ("suite-version-other",)}, "evidence_issuer_restricted"),
        ({"target_restrictions": ("target-version-other",)}, "evidence_issuer_restricted"),
        ({"signer_algorithm": "HS256"}, "evidence_signing_key_untrusted"),
        ({"key_revoked_at": NOW}, "evidence_signing_key_untrusted"),
    ],
)
def test_resolver_rejects_untrusted_or_restricted_authority(
    change: dict[str, object],
    code: str,
) -> None:
    authority = _authority(**change)
    with pytest.raises(EvaluationWorkbenchError) as caught:
        TrustedEvidenceAdmissionResolver(FakeRepository(authority)).resolve(
            scope=authority.scope,
            issuer_key=authority.issuer_key,
            signer_key_id=authority.signer_key_id,
        )
    assert caught.value.code == code


def test_resolver_rejects_unknown_restriction_references() -> None:
    authority = _authority(suite_restrictions=("suite-version-a",))
    repository = FakeRepository(authority)
    repository.references_exist = False

    with pytest.raises(EvaluationWorkbenchError) as caught:
        TrustedEvidenceAdmissionResolver(repository).resolve(
            scope=authority.scope,
            issuer_key=authority.issuer_key,
            signer_key_id=authority.signer_key_id,
        )

    assert caught.value.code == "evidence_issuer_restriction_invalid"


def test_resolver_fails_closed_when_the_locked_authority_is_missing() -> None:
    scope = EvidenceAdmissionScope("org-a", "system-a", "run-a", "suite-execution-a")
    with pytest.raises(EvaluationWorkbenchError) as caught:
        TrustedEvidenceAdmissionResolver(FakeRepository(None)).resolve(
            scope=scope,
            issuer_key="issuer-protocol-a",
            signer_key_id="key-protocol-a",
        )
    assert caught.value.code == "evidence_admission_authority_not_found"

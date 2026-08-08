"""Verified Passport V2 admission is one exact, trusted mutation."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationResult,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_admission import (
    EvidenceAdmissionScope,
    ExpectedServerBinding,
    TrustedEvidenceAdmissionContext,
    TrustedSigningKey,
    VerifiedPassportV2Record,
)
from src.application.services.evidence_authenticity_service import (
    AuthenticityCandidate,
    EvidenceAuthenticityError,
)
from src.application.services.evaluator_registry import (
    EvaluatorRegistration,
    StaticEvaluatorRegistry,
)
from src.application.services.verified_evidence_admission_service import (
    VerifiedEvidenceAdmissionService,
)
from src.domain.assurance.evaluation_v2 import (
    build_execution_envelope_v2,
    canonical_sha256,
)
from src.domain.assurance.evidence_passport_v2 import (
    evidence_passport_v2_content_hash,
    expected_execution_binding_v2,
)

UTC = timezone.utc
REQUESTED_AT = datetime(2026, 8, 8, 8, 0, tzinfo=UTC)
CAPTURED_AT = REQUESTED_AT + timedelta(minutes=2)
SIGNED_AT = REQUESTED_AT + timedelta(minutes=3)
FIRST_DATABASE_NOW = REQUESTED_AT + timedelta(minutes=4)
VERIFIED_AT = REQUESTED_AT + timedelta(minutes=5)
MUTATION_CLOCK_THAT_MUST_NOT_WIN = datetime(2030, 1, 1, tzinfo=UTC)
NONCE = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii").rstrip("=")
PUBLIC_X = base64.urlsafe_b64encode(bytes(reversed(range(32)))).decode("ascii").rstrip("=")
SCOPE = EvidenceAdmissionScope("org-a", "system-a", "run-a", "suite-execution-a")


def _envelope_and_binding() -> tuple[dict[str, object], dict[str, object], str]:
    envelope, _, envelope_hash = build_execution_envelope_v2(
        envelope_id="envelope-a",
        run_id=SCOPE.run_id,
        org_id=SCOPE.organization_id,
        workspace_id="workspace-a",
        system_id=SCOPE.system_id,
        plan_id="plan-a",
        plan_content_hash="a" * 64,
        target={
            "id": "target-version-a",
            "targetKey": "agent-prod",
            "targetKind": "agent",
            "version": "1.0.0",
            "systemVersion": "2026.08",
            "subjectKind": "agent",
            "subjectId": "agent-prod",
            "subjectVersion": "sha-a",
            "subjectDigest": "b" * 64,
            "deploymentId": "deployment-a",
            "connectorBindingId": None,
            "manifestDigest": "c" * 64,
        },
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy={
            "id": "trust-a",
            "version": "1.0.0",
            "policyHash": "d" * 64,
        },
        nonce=NONCE,
        requester_id="requester-a",
        requested_at=REQUESTED_AT.isoformat(),
        suites=[
            {
                "suiteExecutionId": SCOPE.suite_execution_id,
                "suiteVersionId": "suite-version-a",
                "suiteRef": "fairmind/agent-safety@1.0.0",
                "ownerScope": "org-a",
                "manifestDigest": "e" * 64,
                "workerType": "external_provider",
                "runnerImageDigest": None,
                "adapterName": "inspect",
                "adapterVersion": "0.3.0",
                "resultContractVersion": "1.0.0",
                "configuration": {"threshold": 0.5},
                "configurationHash": canonical_sha256({"threshold": 0.5}),
                "inputRoles": ["scenario_set"],
                "budgets": {"maxCases": 200},
                "inputs": {
                    "scenario_set": {
                        "kind": "content_digest",
                        "sha256": "f" * 64,
                    }
                },
            }
        ],
    )
    return (
        envelope,
        expected_execution_binding_v2(envelope, SCOPE.suite_execution_id),
        envelope_hash,
    )


def _passport_bytes(
    *,
    technical_status: str = "succeeded",
    evidence_result_status: str = "failed",
    evaluator_changes: dict[str, object] | None = None,
    captured_at: datetime = CAPTURED_AT,
    signed_at: datetime = SIGNED_AT,
    expires_at: datetime = REQUESTED_AT + timedelta(days=3),
) -> bytes:
    _, binding, _ = _envelope_and_binding()
    evaluator: dict[str, object] = {
        "issuerId": "issuer-protocol-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "resultContractVersion": "1.0.0",
    }
    evaluator.update(evaluator_changes or {})
    passport: dict[str, object] = {
        "schemaVersion": "2.0.0",
        "passportId": "passport-a",
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": SCOPE.organization_id,
        "workspaceId": "workspace-a",
        "systemId": SCOPE.system_id,
        "executionBinding": binding,
        "evaluator": evaluator,
        "result": {
            "technicalStatus": technical_status,
            "evidenceResultStatus": evidence_result_status,
            "summary": {"caseCount": 200, "attackSuccessRate": 0.17},
        },
        "artifacts": [
            {
                "artifactId": "artifact-a",
                "role": "report",
                "sha256": "1" * 64,
                "mediaType": "application/json",
                "sizeBytes": 4096,
            }
        ],
        "limitations": ["The evaluator excludes unsupported provider features."],
        "capturedAt": captured_at.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "signature": {
            "algorithm": "Ed25519",
            "issuerId": "issuer-protocol-a",
            "keyId": "key-protocol-a",
            "signedAt": signed_at.isoformat(),
            "value": "A" * 86,
        },
    }
    passport["contentHash"] = evidence_passport_v2_content_hash(passport)
    return json.dumps(passport, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _execution(
    *,
    execution_id: str = SCOPE.suite_execution_id,
    ordinal: int = 0,
    suite_version_id: str = "suite-version-a",
    technical_status: str = "awaiting_evidence",
    evidence_result_status: str = "pending",
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> SuiteExecutionRecord:
    return SuiteExecutionRecord(
        id=execution_id,
        suite_version_id=suite_version_id,
        owner_scope="org-a",
        ordinal=ordinal,
        technical_status=technical_status,
        evidence_result_status=evidence_result_status,
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
        started_at=None if started_at is None else started_at.isoformat(),
        completed_at=None if completed_at is None else completed_at.isoformat(),
        created_at=REQUESTED_AT.isoformat(),
        updated_at=(REQUESTED_AT + timedelta(minutes=1)).isoformat(),
    )


def _authority(
    *,
    executions: tuple[SuiteExecutionRecord, ...] | None = None,
    run_technical_status: str = "awaiting_evidence",
    run_evidence_outcome: str = "pending",
    run_started_at: datetime | None = None,
    run_completed_at: datetime | None = None,
    overall_verdict: str = "insufficient",
    verdict_version: int = 0,
    maximum_age_seconds: int = 600,
    key_valid_until: datetime = REQUESTED_AT + timedelta(days=1),
) -> SimpleNamespace:
    envelope, _, envelope_hash = _envelope_and_binding()
    current_executions = executions or (_execution(),)
    suites = tuple(
        SimpleNamespace(
            ordinal=execution.ordinal,
            suite=SimpleNamespace(
                id=execution.suite_version_id,
                adapter_name="inspect",
                adapter_version="0.3.0",
                result_contract_version="1.0.0",
            ),
        )
        for execution in current_executions
    )
    run = SimpleNamespace(
        id=SCOPE.run_id,
        organization_id=SCOPE.organization_id,
        workspace_id="workspace-a",
        system_id=SCOPE.system_id,
        technical_status=run_technical_status,
        evidence_outcome=run_evidence_outcome,
        overall_verdict=overall_verdict,
        verdict_version=verdict_version,
        envelope=FrozenJsonObject.from_mapping(envelope),
        envelope_hash=envelope_hash,
        suite_executions=current_executions,
        started_at=None if run_started_at is None else run_started_at.isoformat(),
        completed_at=None if run_completed_at is None else run_completed_at.isoformat(),
        created_at=REQUESTED_AT.isoformat(),
        updated_at=(REQUESTED_AT + timedelta(minutes=1)).isoformat(),
    )
    return SimpleNamespace(
        scope=SCOPE,
        plan_graph=SimpleNamespace(
            plan=SimpleNamespace(delivery_mode="external_provider"),
            suites=suites,
        ),
        run=run,
        issuer_key="issuer-protocol-a",
        issuer_type="external_provider",
        maximum_evidence_age_seconds=maximum_age_seconds,
        key_valid_until=key_valid_until,
    )


def _context(
    authority: SimpleNamespace,
    *,
    database_now: datetime,
    authority_hash: str = "9" * 64,
) -> TrustedEvidenceAdmissionContext:
    _, binding, _ = _envelope_and_binding()
    return TrustedEvidenceAdmissionContext(
        authority=authority,  # type: ignore[arg-type]
        expected_binding=ExpectedServerBinding(
            organization_id=SCOPE.organization_id,
            workspace_id="workspace-a",
            system_id=SCOPE.system_id,
            execution_binding=binding,
        ),
        trusted_key=TrustedSigningKey(
            issuer_id="issuer-protocol-a",
            key_id="key-protocol-a",
            algorithm="Ed25519",
            public_jwk={"kty": "OKP", "crv": "Ed25519", "x": PUBLIC_X},
            valid_from=REQUESTED_AT - timedelta(days=1),
            valid_until=authority.key_valid_until,
            revoked_at=None,
        ),
        authority_hash=authority_hash,
        database_now=database_now,
    )


class FakeResolver:
    def __init__(self, contexts: list[TrustedEvidenceAdmissionContext]) -> None:
        self.contexts = contexts
        self.calls: list[tuple[EvidenceAdmissionScope, str, str]] = []

    def resolve(self, *, scope, issuer_key, signer_key_id):
        self.calls.append((scope, issuer_key, signer_key_id))
        return self.contexts.pop(0)


class FakeAuthenticityService:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls: list[tuple[object, object, object, datetime]] = []

    def assess(self, passport, expected, trusted_key, now):
        self.calls.append((passport, expected, trusted_key, now))
        if self.failure is not None:
            raise self.failure
        result = passport["result"]
        assert isinstance(result, dict)
        signature = passport["signature"]
        assert isinstance(signature, dict)
        evaluator = passport["evaluator"]
        assert isinstance(evaluator, dict)
        return AuthenticityCandidate(
            content_hash=passport["contentHash"],
            passport_snapshot_hash="2" * 64,
            signature_input_hash="3" * 64,
            execution_binding_hash=canonical_sha256(passport["executionBinding"]),
            evaluator_projection_hash=canonical_sha256(evaluator),
            public_key_fingerprint="5" * 64,
            verifier_contract="fairmind/evidence-passport-v2/verified-admission",
            verifier_version="2.0.0",
            issuer_id=signature["issuerId"],
            key_id=signature["keyId"],
            captured_at=datetime.fromisoformat(passport["capturedAt"]),
            signed_at=datetime.fromisoformat(signature["signedAt"]),
            expires_at=datetime.fromisoformat(passport["expiresAt"]),
            normalized_result=result,
        )


class FakeRepository:
    def __init__(self) -> None:
        self.persisted = []
        self.events: list[str] = []

    def persist_verified_passport_v2(self, command):
        self.events.append("persist")
        self.persisted.append(command)
        return VerifiedPassportV2Record(
            organization_id=command.scope.organization_id,
            workspace_id=command.authority.run.workspace_id,
            system_id=command.scope.system_id,
            run_id=command.scope.run_id,
            suite_execution_id=command.scope.suite_execution_id,
            evidence_run_id=command.evidence_run_id,
            passport_revision_id=command.passport_revision_id,
            verification_receipt_id=command.verification_receipt_id,
            admission_id=command.admission_id,
            nonce_claim_id=command.nonce_claim_id,
            suite_evidence_link_id=command.suite_evidence_link_id,
            envelope_hash=command.authority.run.envelope_hash,
            passport_content_hash=command.passport_content_hash,
            technical_status=command.technical_status,
            evidence_result_status=command.evidence_result_status,
            admission_status="verified",
            review_status="pending",
            freshness_status="current",
            run_technical_status=command.run_technical_status,
            run_evidence_outcome=command.run_evidence_outcome,
            overall_verdict=command.authority.run.overall_verdict,
            verdict_version=command.authority.run.verdict_version,
            effective_expires_at=command.effective_expires_at,
            verified_at=command.verified_at,
        )

    def force_evidence_admission_constraints(self) -> None:
        self.events.append("constraints")


class FakeUnitOfWork:
    def __init__(self, repository: FakeRepository) -> None:
        self.repository = repository
        self.command = None
        self.callback_entered = False
        self.outcome = None
        self.rejections: list[EvaluationWorkbenchError] = []

    def mutate(self, command, callback):
        self.command = command
        self.callback_entered = True
        try:
            self.outcome = callback(MUTATION_CLOCK_THAT_MUST_NOT_WIN)
        except EvaluationWorkbenchError as error:
            self.rejections.append(error)
            raise
        return MutationResult.create(
            body=self.outcome.body.to_dict(),
            status=self.outcome.status,
        )


class SequentialUuidFactory:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self):
        self.value += 1
        return UUID(int=self.value)


def _configured_service(
    *,
    authority: SimpleNamespace | None = None,
    second_authority: SimpleNamespace | None = None,
    first_now: datetime = FIRST_DATABASE_NOW,
    verified_at: datetime = VERIFIED_AT,
    first_hash: str = "9" * 64,
    second_hash: str = "9" * 64,
    authenticity_failure: Exception | None = None,
    evaluator_registry: StaticEvaluatorRegistry | None = None,
):
    initial = authority or _authority()
    verified = second_authority or initial
    repository = FakeRepository()
    unit_of_work = FakeUnitOfWork(repository)
    authenticity = FakeAuthenticityService(authenticity_failure)
    resolver = FakeResolver(
        [
            _context(initial, database_now=first_now, authority_hash=first_hash),
            _context(verified, database_now=verified_at, authority_hash=second_hash),
        ]
    )
    service = VerifiedEvidenceAdmissionService(
        unit_of_work,
        authenticity,  # type: ignore[arg-type]
        evaluator_registry=evaluator_registry
        or StaticEvaluatorRegistry(
            catalog_version="2026.08.1",
            registrations=(
                EvaluatorRegistration(
                    evaluator_id="evaluator-a",
                    adapter_name="inspect",
                    adapter_version="0.3.0",
                    result_contract_version="1.0.0",
                    source_types=frozenset({"external_provider"}),
                ),
            ),
        ),
        uuid_factory=SequentialUuidFactory(),
    )
    service._resolver = resolver
    return service, unit_of_work, repository, authenticity, resolver


def test_verified_admission_persists_exact_graph_with_fresh_database_time() -> None:
    service, unit_of_work, repository, authenticity, resolver = _configured_service()
    raw = _passport_bytes()

    result = service.admit_verified_passport_v2(
        scope=SCOPE,
        actor_id="reviewer-a",
        idempotency_key="admit-key-a",
        raw_passport=raw,
    )

    assert result.status == 201
    assert set(result.body) == {
        "admissionId",
        "evidenceRunId",
        "passportRevisionId",
        "verificationReceiptId",
        "nonceClaimId",
        "suiteEvidenceLinkId",
        "runId",
        "suiteExecutionId",
        "envelopeHash",
        "passportContentHash",
        "technicalStatus",
        "evidenceResultStatus",
        "admissionStatus",
        "reviewStatus",
        "freshnessStatus",
        "runTechnicalStatus",
        "runEvidenceOutcome",
        "overallVerdict",
        "verdictVersion",
        "effectiveExpiresAt",
        "verifiedAt",
    }
    assert len(resolver.calls) == 2
    assert authenticity.calls[0][3] == FIRST_DATABASE_NOW
    assert repository.events == ["persist", "constraints"]
    command = repository.persisted[0]
    graph_ids = {
        command.evidence_run_id,
        command.passport_revision_id,
        command.verification_receipt_id,
        command.admission_id,
        command.nonce_claim_id,
        command.suite_evidence_link_id,
    }
    assert len(graph_ids) == 6
    assert all(str(UUID(value)) == value for value in graph_ids)
    assert command.evidence_id is None
    assert command.previous_revision_hash is None
    assert command.verified_at == VERIFIED_AT
    assert command.evidence_created_at == VERIFIED_AT
    assert command.revision_created_at == VERIFIED_AT
    assert command.effective_expires_at == CAPTURED_AT + timedelta(seconds=600)
    assert command.run_technical_status == "succeeded"
    assert command.run_evidence_outcome == "failed"
    assert command.suite_started_at == VERIFIED_AT
    assert command.suite_completed_at == VERIFIED_AT
    assert command.run_started_at == VERIFIED_AT
    assert command.run_completed_at == VERIFIED_AT
    assert command.evaluator_projection.to_dict() == {
        "issuerId": "issuer-protocol-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "resultContractVersion": "1.0.0",
    }
    expected_request_hash = canonical_sha256(
        {
            "method": "POST",
            "operation": "evaluation-v2.evidence.verified-admit",
            "scope": {
                "organizationId": SCOPE.organization_id,
                "systemId": SCOPE.system_id,
                "runId": SCOPE.run_id,
                "suiteExecutionId": SCOPE.suite_execution_id,
            },
            "body": {
                "contractVersion": "2.0.0",
                "rawPassport": {
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "byteLength": len(raw),
                },
            },
        }
    )
    assert unit_of_work.command.request_hash == expected_request_hash
    assert unit_of_work.outcome.audit_details.to_dict() == {
        "schemaVersion": "evaluation-v2.verified-evidence-admission/v1",
        "runId": SCOPE.run_id,
        "suiteExecutionId": SCOPE.suite_execution_id,
        "admissionId": command.admission_id,
        "evidenceRunId": command.evidence_run_id,
        "passportRevisionId": command.passport_revision_id,
        "verificationReceiptId": command.verification_receipt_id,
        "nonceClaimId": command.nonce_claim_id,
        "suiteEvidenceLinkId": command.suite_evidence_link_id,
        "envelopeHash": command.authority.run.envelope_hash,
        "passportContentHash": command.passport_content_hash,
        "technicalStatus": "succeeded",
        "evidenceResultStatus": "failed",
        "admissionStatus": "verified",
        "reviewStatus": "pending",
        "freshnessStatus": "current",
        "runTechnicalStatus": "succeeded",
        "runEvidenceOutcome": "failed",
        "evaluatorRegistryHash": "e816008e154dd1c5509c2158ca1e0ff0f40a8f75c209a22f2d473fc375e5c617",
        "evaluatorRegistrationHash": "eba56d312a0fe0e4ce7e6af6bc4b20b4660f75da7d4accc343772ea9298d62c3",
    }


def test_signed_evaluator_must_be_registered_by_server_catalog() -> None:
    service, unit_of_work, repository, _, _ = _configured_service(
        evaluator_registry=StaticEvaluatorRegistry(
            catalog_version="2026.08.1",
            registrations=(
                EvaluatorRegistration(
                    evaluator_id="different-evaluator",
                    adapter_name="inspect",
                    adapter_version="0.3.0",
                    result_contract_version="1.0.0",
                    source_types=frozenset({"external_provider"}),
                ),
            ),
        )
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key="unregistered-evaluator-a",
            raw_passport=_passport_bytes(),
        )

    assert caught.value.code == "evidence_evaluator_unregistered"
    assert repository.persisted == []
    assert unit_of_work.rejections == [caught.value]


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    (
        ("sourceType", "fairmind_worker", "evidence_passport_invalid"),
        ("adapterName", "promptfoo", "evidence_evaluator_binding_mismatch"),
        ("adapterVersion", "0.4.0", "evidence_evaluator_binding_mismatch"),
        ("resultContractVersion", "2.0.0", "evidence_evaluator_binding_mismatch"),
    ),
)
def test_signed_evaluator_must_exactly_match_locked_delivery_and_suite(
    field: str,
    value: str,
    expected_code: str,
) -> None:
    service, unit_of_work, repository, _, _ = _configured_service()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key=f"mismatch-{field}",
            raw_passport=_passport_bytes(evaluator_changes={field: value}),
        )

    assert caught.value.code == expected_code
    assert caught.value.status_code in {409, 422}
    assert repository.persisted == []
    assert unit_of_work.rejections == [caught.value]


def test_authority_must_remain_identical_across_authenticity_verification() -> None:
    service, _, repository, _, _ = _configured_service(second_hash="8" * 64)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key="authority-race-a",
            raw_passport=_passport_bytes(),
        )

    assert caught.value.code == "evidence_admission_authority_changed"
    assert repository.persisted == []


@pytest.mark.parametrize(
    ("raw", "failure", "expected_code"),
    (
        (b'{"not":"a passport"}', None, "evidence_passport_invalid"),
        (
            None,
            EvidenceAuthenticityError("signature verification failed"),
            "evidence_authenticity_failed",
        ),
        (
            None,
            EvidenceAuthenticityError("private verifier crash detail"),
            "evidence_authenticity_failed",
        ),
    ),
)
def test_parse_and_authenticity_rejections_are_bounded_inside_the_mutation(
    raw: bytes | None,
    failure: Exception | None,
    expected_code: str,
) -> None:
    service, unit_of_work, repository, _, resolver = _configured_service(
        authenticity_failure=failure
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key=f"reject-{expected_code}",
            raw_passport=raw or _passport_bytes(),
        )

    assert caught.value.code == expected_code
    assert caught.value.status_code == 422
    assert "private" not in caught.value.message
    assert unit_of_work.callback_entered is True
    assert unit_of_work.rejections == [caught.value]
    assert repository.persisted == []
    if raw is not None:
        assert resolver.calls == []


@pytest.mark.parametrize(
    ("captured_at", "signed_at", "verified_at", "expected_code"),
    (
        (
            REQUESTED_AT - timedelta(seconds=1),
            SIGNED_AT,
            VERIFIED_AT,
            "evidence_chronology_invalid",
        ),
        (
            CAPTURED_AT,
            SIGNED_AT,
            CAPTURED_AT + timedelta(seconds=600),
            "evidence_expired",
        ),
    ),
)
def test_database_chronology_and_strict_effective_expiry_are_enforced(
    captured_at: datetime,
    signed_at: datetime,
    verified_at: datetime,
    expected_code: str,
) -> None:
    service, _, repository, _, _ = _configured_service(verified_at=verified_at)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key=f"chronology-{expected_code}",
            raw_passport=_passport_bytes(
                captured_at=captured_at,
                signed_at=signed_at,
            ),
        )

    assert caught.value.code == expected_code
    assert repository.persisted == []


def test_succeeded_cannot_skip_from_queued_state() -> None:
    authority = _authority(executions=(_execution(technical_status="queued"),))
    service, _, repository, _, _ = _configured_service(authority=authority)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.admit_verified_passport_v2(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key="skip-running-a",
            raw_passport=_passport_bytes(),
        )

    assert caught.value.code == "suite_execution_transition_invalid"
    assert repository.persisted == []


def test_terminal_parent_accepts_exact_terminal_but_unlinked_sibling() -> None:
    completed = REQUESTED_AT + timedelta(seconds=30)
    current = _execution(
        technical_status="succeeded",
        evidence_result_status="failed",
        started_at=REQUESTED_AT + timedelta(seconds=10),
        completed_at=completed,
    )
    sibling = _execution(
        execution_id="suite-execution-b",
        ordinal=1,
        suite_version_id="suite-version-b",
        technical_status="failed",
        evidence_result_status="error",
        completed_at=completed,
    )
    authority = _authority(
        executions=(current, sibling),
        run_technical_status="failed",
        run_evidence_outcome="failed",
        run_started_at=REQUESTED_AT + timedelta(seconds=10),
        run_completed_at=completed,
    )
    service, _, repository, _, _ = _configured_service(authority=authority)

    service.admit_verified_passport_v2(
        scope=SCOPE,
        actor_id="reviewer-a",
        idempotency_key="terminal-unlinked-a",
        raw_passport=_passport_bytes(),
    )

    command = repository.persisted[0]
    assert command.run_technical_status == "failed"
    assert command.run_evidence_outcome == "failed"
    assert command.run_completed_at == completed
    assert command.suite_started_at == REQUESTED_AT + timedelta(seconds=10)
    assert command.suite_completed_at == completed


def test_cancelled_suite_can_admit_pending_without_false_failure() -> None:
    service, _, repository, _, _ = _configured_service()

    service.admit_verified_passport_v2(
        scope=SCOPE,
        actor_id="reviewer-a",
        idempotency_key="cancelled-pending-a",
        raw_passport=_passport_bytes(
            technical_status="cancelled",
            evidence_result_status="pending",
        ),
    )

    command = repository.persisted[0]
    assert (command.technical_status, command.evidence_result_status) == (
        "cancelled",
        "pending",
    )
    assert (command.run_technical_status, command.run_evidence_outcome) == (
        "cancelled",
        "pending",
    )


def test_version_zero_review_verdict_is_preserved_as_governance_not_evidence() -> None:
    authority = _authority(overall_verdict="review")
    service, _, repository, _, _ = _configured_service(authority=authority)

    result = service.admit_verified_passport_v2(
        scope=SCOPE,
        actor_id="reviewer-a",
        idempotency_key="review-verdict-a",
        raw_passport=_passport_bytes(),
    )

    assert result.body["overallVerdict"] == "review"
    assert result.body["verdictVersion"] == 0
    assert repository.persisted[0].evidence_result_status == "failed"

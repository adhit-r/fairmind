"""End-to-end Evidence Passport ingestion, persistence, and revision tests."""

from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
import uuid

import pytest
import rfc8785
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from database.connection import Base, get_db
from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidence,
    GovernanceEvidenceArtifact,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)
from database.models import (
    Organization,
    OrganizationAuditLog,
    OrganizationMember,
    User,
)
from migrations.governance_assurance_migration import sql_for
from src.application.ports.evidence_ingestion import EvidenceRunConflict
from src.application.ports.evidence_ingestion import EvidenceRevisionConflict
from src.application.services.governance_assurance_service import GovernanceAssuranceService
from src.domain.assurance.evidence_passport import EvidencePassport, with_server_hashes
from src.infrastructure.db.repositories.evidence_ingestion_repository import (
    SqlAlchemyEvidenceIngestionStore,
)

REPO_ROOT = Path(__file__).parents[3]
ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
USER_A = str(uuid.uuid4())
USER_B = str(uuid.uuid4())
HASH = "a" * 64


def _rows(session, model, *, order_by=None):
    table = model.__table__
    statement = select(table)
    if order_by is not None:
        statement = statement.order_by(order_by)
    return session.execute(statement).mappings().all()


def _count(session, model) -> int:
    return len(_rows(session, model))


def _audit_rows(session, action: str):
    audits = OrganizationAuditLog.__table__
    return session.execute(select(audits).where(audits.c.action == action)).mappings().all()


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email="evidence@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


@pytest.fixture
def assurance_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    active_user = {"value": _token(USER_A)}

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    async def override_user():
        return active_user["value"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        with TestClient(app) as client:
            yield client, session_factory, active_user
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed_org(session, org_id: str, user_id: str, role: str = "admin") -> None:
    user_uuid = uuid.UUID(user_id)
    session.execute(
        User.__table__.insert().values(
            id=user_uuid,
            email=f"{user_id}@example.test",
            username=user_id,
        )
    )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(org_id),
            name=org_id,
            slug=org_id,
            owner_id=user_uuid,
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=user_uuid,
            role=role,
            status="active",
        )
    )


def _seed_system_and_control(
    session,
    *,
    org_id: str = ORG_A,
    workspace_id: str = "workspace-001",
    system_id: str = "system-001",
    suffix: str = "001",
) -> tuple[str, str]:
    session.execute(
        GovernanceWorkspace.__table__.insert().values(
            id=workspace_id,
            org_id=org_id,
            name=f"Workspace {suffix}",
        )
    )
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id=system_id,
            workspace_id=workspace_id,
            org_id=org_id,
            name=f"System {suffix}",
        )
    )
    version_id = f"version-{suffix}"
    control_id = f"control-{suffix}"
    assignment_id = f"assignment-{suffix}"
    assessment_id = f"assessment-{suffix}"
    session.execute(
        GovernanceFrameworkVersion.__table__.insert().values(
            id=version_id,
            framework_key="generic",
            name="Generic",
            version_label="1",
            source_hash=HASH,
        )
    )
    session.execute(
        GovernanceControlDefinition.__table__.insert().values(
            id=control_id,
            framework_version_id=version_id,
            external_id="CTRL-1",
            title="Control",
            statement="Statement",
            frequency="Every 3 months",
            active=True,
        )
    )
    session.execute(
        GovernanceFrameworkAssignment.__table__.insert().values(
            id=assignment_id,
            org_id=org_id,
            system_id=system_id,
            framework_version_id=version_id,
        )
    )
    session.execute(
        GovernanceControlAssessment.__table__.insert().values(
            id=assessment_id,
            org_id=org_id,
            system_id=system_id,
            framework_assignment_id=assignment_id,
            control_definition_id=control_id,
        )
    )
    session.commit()
    return system_id, assessment_id


def _passport(
    *,
    org_id: str = ORG_A,
    workspace_id: str = "workspace-001",
    system_id: str = "system-001",
    run_id: str = "run-001",
    passport_id: str = "passport-001",
    assessment_id: str = "assessment-001",
    result_status: str = "passed",
    capability_state: str = "validated",
    limitations: list[str] | None = None,
) -> dict:
    payload = {
        "schemaVersion": "1.0.0",
        "passportId": passport_id,
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": org_id,
        "workspaceId": workspace_id,
        "aiSystem": {
            "systemId": system_id,
            "name": "System 001 supplied name",
            "kind": "model",
            "version": "2026.07",
            "identityHash": "1" * 64,
            "ownerId": "owner-001",
        },
        "evaluation": {
            "sourceType": "fairmind_evaluation",
            "sourceIdentifier": "fairmind-bias-suite",
            "runId": run_id,
            "capabilityState": capability_state,
            "assuranceSource": "fairmind_internal",
            "evaluator": {
                "name": "FairMind evaluator",
                "version": "2.0.0",
                "adapterName": "passport-adapter",
                "adapterVersion": "1.0.0",
                "runnerVersion": "3.0.0",
            },
            "suite": {"name": "Bias suite", "version": "2026.07", "trigger": "release_gate"},
            "subject": {
                "kind": "model",
                "subjectId": "subject-001",
                "name": "System 001",
                "version": "2026.07",
                "digest": "2" * 64,
            },
            "scope": {
                "intendedUse": "Bounded synthetic evaluation.",
                "inputFingerprint": "3" * 64,
                "datasetName": "Synthetic data",
                "datasetVersion": "1",
                "datasetHash": "4" * 64,
                "sampleCount": 100,
                "protectedGroups": ["age"],
                "locales": ["en-IN"],
                "exclusions": ["Production data."],
            },
            "configurationHash": "5" * 64,
            "thresholds": [
                {
                    "metric": "parity",
                    "operator": "lte",
                    "value": 0.1,
                    "rationale": "Preregistered threshold.",
                }
            ],
            "result": {
                "status": result_status,
                "summary": f"Bounded {result_status} result.",
                "metrics": [{"name": "parity", "value": 0.05, "thresholdMet": True}],
                "startedAt": "2026-07-18T00:00:00Z",
                "endedAt": "2026-07-18T00:05:00Z",
            },
            "runContentHash": "0" * 64,
            "capturedAt": "2026-07-18T00:05:00Z",
            "limitations": limitations if limitations is not None else ["Synthetic test set only."],
        },
        "artifacts": [
            {
                "artifactId": "artifact-report",
                "role": "report",
                "uri": f"s3://evidence/{run_id}/report.json",
                "sha256": "6" * 64,
                "mediaType": "application/json",
                "sizeBytes": 1024,
                "containsSensitiveData": False,
            },
            {
                "artifactId": "artifact-log",
                "role": "log",
                "uri": f"s3://evidence/{run_id}/diagnostic.log",
                "sha256": "7" * 64,
                "mediaType": "text/plain",
                "sizeBytes": 512,
                "containsSensitiveData": False,
            },
        ],
        "frameworkMappings": [
            {
                "mappingId": "mapping-001",
                "framework": {
                    "key": "generic",
                    "versionLabel": "1",
                    "sourceHash": HASH,
                },
                "control": {"externalId": "CTRL-1", "assessmentId": assessment_id},
                "state": "candidate",
                "relation": "supports",
                "rationale": "Explicit evaluator mapping for review.",
                "suggestedBy": {"actorType": "adapter", "actorId": "adapter-001"},
                "createdAt": "2026-07-18T00:05:00Z",
            }
        ],
        "review": {"status": "pending", "reviewVersion": 0},
        "findings": [],
        "remediation": [],
        "freshness": {
            "status": "current",
            "policy": "Re-evaluate on material change.",
            "assessedAt": "2026-07-18T00:05:00Z",
            "staleReasons": [],
            "invalidationKeys": ["system_version", "dataset_hash"],
        },
        "lineage": {"predecessorPassportIds": [], "retestOfPassportIds": []},
        "createdAt": "2026-07-18T00:05:00Z",
        "canonicalContentHash": "0" * 64,
    }
    return with_server_hashes(EvidencePassport.model_validate(payload)).model_dump(
        by_alias=True,
        mode="json",
        exclude_none=True,
    )


def _independently_hash_passport(payload: dict) -> dict:
    result = deepcopy(payload)
    run_projection = {
        "schemaVersion": result["schemaVersion"],
        "aiSystem": deepcopy(result["aiSystem"]),
        "evaluation": {
            key: deepcopy(value)
            for key, value in result["evaluation"].items()
            if key != "runContentHash"
        },
        "artifacts": deepcopy(result["artifacts"]),
    }
    result["evaluation"]["runContentHash"] = hashlib.sha256(
        rfc8785.dumps(run_projection)
    ).hexdigest()
    snapshot = {
        key: deepcopy(value)
        for key, value in result.items()
        if key not in {"canonicalContentHash", "signatures"}
    }
    result["canonicalContentHash"] = hashlib.sha256(rfc8785.dumps(snapshot)).hexdigest()
    return result


def _post(
    client: TestClient, passport: dict, *, path_org: str = ORG_A, path_system: str = "system-001"
):
    return client.post(
        f"/api/v1/ai-governance/organizations/{path_org}/systems/{path_system}/evidence-runs",
        json=passport,
    )


@pytest.mark.parametrize(
    "raw_fragment",
    [
        '"organizationId":"%s","organizationId":"%s"' % (ORG_A, ORG_A),
        '"aiSystem":{"systemId":"system-001","systemId":"system-001"}',
    ],
)
def test_duplicate_json_names_are_rejected_at_root_and_nested_levels(
    assurance_client, raw_fragment: str
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    if raw_fragment.startswith('"organizationId"'):
        raw = "{" + raw_fragment + "}"
    else:
        raw = "{" + raw_fragment + "}"

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/system-001/evidence-runs",
        content=raw.encode(),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422, response.text
    assert "duplicate" in response.text.lower()
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


@pytest.mark.parametrize("unsafe_integer", [2**53, -(2**53)])
def test_ijson_unsafe_integer_request_is_rejected_as_422(
    assurance_client, unsafe_integer: int
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    passport = _passport()
    passport["evaluation"]["thresholds"][0]["value"] = unsafe_integer

    response = _post(client, passport)

    assert response.status_code == 422, response.text
    assert "I-JSON" in response.text or "integer" in response.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


def test_ijson_lone_surrogate_request_is_rejected_as_422(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    passport = _passport()
    passport["evaluation"]["result"]["summary"] = "\ud800"
    raw = json.dumps(passport, ensure_ascii=True).encode("ascii")

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/system-001/evidence-runs",
        content=raw,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422, response.text
    assert "surrogate" in response.text.lower()
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


def _seed_default(session_factory) -> tuple[str, str]:
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    identifiers = _seed_system_and_control(session)
    session.close()
    return identifiers


def test_new_passport_writes_run_ordered_artifacts_revision_candidates_and_audit(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    system_id, assessment_id = _seed_default(session_factory)

    response = _post(client, _passport())

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["disposition"] == "created"
    assert body["runId"] == "run-001"
    assert body["passportId"] == "passport-001"
    assert body["latestRevision"] == 1
    assert body["runContentHash"] == _passport()["evaluation"]["runContentHash"]
    assert body["latestCanonicalContentHash"] == _passport()["canonicalContentHash"]
    assert body["result"] == "passed"
    assert body["capabilityState"] == "validated"
    assert [artifact["artifactId"] for artifact in body["artifacts"]] == [
        "artifact-report",
        "artifact-log",
    ]
    assert body["candidateMappings"][0]["controlAssessmentId"] == assessment_id
    assert body["candidateMappings"][0]["state"] == "candidate"

    session = session_factory()
    assert _rows(session, GovernanceEvidenceRun)
    artifacts = _rows(
        session,
        GovernanceEvidenceArtifact,
        order_by=GovernanceEvidenceArtifact.__table__.c.ordinal,
    )
    assert [(item["artifact_id"], item["ordinal"]) for item in artifacts] == [
        ("artifact-report", 0),
        ("artifact-log", 1),
    ]
    revisions = _rows(session, GovernanceEvidencePassportRevision)
    assert len(revisions) == 1
    assert revisions[0]["passport_revision"] == 1
    assert (
        json.loads(revisions[0]["snapshot_json"])["canonicalContentHash"]
        == body["latestCanonicalContentHash"]
    )
    mappings = _rows(session, GovernanceControlEvidence)
    assert len(mappings) == 1 and mappings[0]["state"] == "candidate"
    assert mappings[0]["source_mapping_id"] == "mapping-001"
    audits = _audit_rows(session, "evidence_passport.ingested")
    assert len(audits) == 1
    session.close()


def test_absent_optional_protocol_fields_remain_absent_in_stored_snapshot(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    passport = _passport()
    passport["evaluation"]["scope"].pop("protectedGroups")
    passport["evaluation"]["scope"].pop("locales")
    passport["evaluation"]["thirdPartyAssessor"] = {
        "identity": "Independent Assurance Co.",
        "independenceAssertion": True,
    }
    passport = _independently_hash_passport(passport)

    response = _post(client, passport)

    assert response.status_code == 201, response.text
    session = session_factory()
    snapshot = json.loads(_rows(session, GovernanceEvidencePassportRevision)[0]["snapshot_json"])
    assert "protectedGroups" not in snapshot["evaluation"]["scope"]
    assert "locales" not in snapshot["evaluation"]["scope"]
    assert "qualifications" not in snapshot["evaluation"]["thirdPartyAssessor"]
    assert snapshot["evaluation"]["runContentHash"] == passport["evaluation"]["runContentHash"]
    assert snapshot["canonicalContentHash"] == passport["canonicalContentHash"]
    session.close()


def test_identical_replay_returns_200_without_duplicate_rows_or_success_audit(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    passport = _passport()

    created = _post(client, passport)
    replayed = _post(client, json.loads(json.dumps(passport, sort_keys=True)))

    assert created.status_code == 201
    assert replayed.status_code == 200, replayed.text
    assert replayed.json()["disposition"] == "replayed"
    assert replayed.json()["id"] == created.json()["id"]
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 1
    assert _count(session, GovernanceEvidenceArtifact) == 2
    assert _count(session, GovernanceEvidencePassportRevision) == 1
    assert _count(session, GovernanceControlEvidence) == 1
    assert len(_audit_rows(session, "evidence_passport.ingested")) == 1
    session.close()


def test_changed_content_under_same_identity_returns_durably_audited_409(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    original = _passport()
    assert _post(client, original).status_code == 201
    changed = deepcopy(original)
    changed["evaluation"]["result"]["metrics"][0]["value"] = 0.2
    changed = with_server_hashes(EvidencePassport.model_validate(changed)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )

    conflict = _post(client, changed)

    assert conflict.status_code == 409, conflict.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 1
    audits = _audit_rows(session, "evidence_passport.conflict")
    assert len(audits) == 1
    assert set(audits[0]["changes"]) == {
        "sourceType",
        "sourceIdentifier",
        "runId",
        "existingRunContentHash",
        "incomingRunContentHash",
        "existingCanonicalContentHash",
        "incomingCanonicalContentHash",
    }
    assert "passport" not in json.dumps(audits[0]["changes"]).lower()
    session.close()


def test_conflict_audit_failure_returns_500_instead_of_unaudited_409(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    original = _passport()
    assert _post(client, original).status_code == 201
    session = session_factory()
    session.execute(
        text(
            "CREATE TRIGGER fail_conflict_audit BEFORE INSERT ON org_audit_logs "
            "FOR EACH ROW WHEN NEW.action = 'evidence_passport.conflict' "
            "BEGIN SELECT RAISE(ABORT, 'forced conflict audit failure'); END"
        )
    )
    session.commit()
    session.close()
    changed = deepcopy(original)
    changed["evaluation"]["result"]["metrics"][0]["value"] = 0.2
    changed = with_server_hashes(EvidencePassport.model_validate(changed)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )

    response = _post(client, changed)

    assert response.status_code == 500, response.text
    session = session_factory()
    assert _audit_rows(session, "evidence_passport.conflict") == []
    assert _count(session, GovernanceEvidenceRun) == 1
    session.close()


def test_unique_key_race_reclassifies_replay_and_conflict(
    assurance_client,
    monkeypatch,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    original = _passport()
    assert _post(client, original).status_code == 201

    def race_store(payload: dict) -> SqlAlchemyEvidenceIngestionStore:
        session = session_factory()
        store = SqlAlchemyEvidenceIngestionStore(session)
        real_find = store._find_run
        calls = {"count": 0}

        def miss_then_find(passport):
            calls["count"] += 1
            return None if calls["count"] == 1 else real_find(passport)

        monkeypatch.setattr(store, "_find_run", miss_then_find)
        return store

    replay_store = race_store(original)
    replay = replay_store.ingest(EvidencePassport.model_validate(original), USER_A)
    assert replay.disposition.value == "replayed"
    replay_store.db.close()

    changed = deepcopy(original)
    changed["evaluation"]["result"]["metrics"][0]["value"] = 0.3
    changed = with_server_hashes(EvidencePassport.model_validate(changed)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )
    conflict_store = race_store(changed)
    with pytest.raises(EvidenceRunConflict):
        conflict_store.ingest(EvidencePassport.model_validate(changed), USER_A)
    conflict_store.db.close()

    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 1
    assert len(_audit_rows(session, "evidence_passport.conflict")) == 1
    session.close()


@pytest.mark.parametrize(
    "mismatch", ["organization", "workspace", "path_system", "passport_system"]
)
def test_organization_workspace_path_and_passport_system_scope_fail_closed(
    assurance_client,
    mismatch: str,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    session = session_factory()
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id="system-002",
            workspace_id="workspace-001",
            org_id=ORG_A,
            name="System 002",
        )
    )
    session.commit()
    session.close()
    passport = _passport()
    path_org, path_system = ORG_A, "system-001"
    if mismatch == "organization":
        passport["organizationId"] = ORG_B
    elif mismatch == "workspace":
        passport["workspaceId"] = "workspace-other"
    elif mismatch == "path_system":
        path_system = "system-002"
    else:
        passport["aiSystem"]["systemId"] = "system-002"
    passport = with_server_hashes(EvidencePassport.model_validate(passport)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )

    response = _post(client, passport, path_org=path_org, path_system=path_system)

    assert response.status_code == 422, response.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


@pytest.mark.parametrize(
    ("status", "capability"),
    [
        ("passed_with_limitations", "validated"),
        ("failed", "validated"),
        ("error", "validated"),
        ("unavailable", "unavailable"),
        ("insufficient_data", "insufficient_data"),
    ],
)
def test_nonpassing_runs_are_stored_with_limitations_but_not_readiness_evidence(
    assurance_client,
    status: str,
    capability: str,
) -> None:
    client, session_factory, _ = assurance_client
    _, assessment_id = _seed_default(session_factory)
    passport = _passport(
        result_status=status,
        capability_state=capability,
        limitations=[f"Explicit {status} limitation."],
    )
    if status in {"error", "unavailable"}:
        passport["evaluation"]["result"]["metrics"] = []
        passport = with_server_hashes(EvidencePassport.model_validate(passport)).model_dump(
            by_alias=True, mode="json", exclude_none=True
        )

    response = _post(client, passport)
    assert response.status_code == 201, response.text
    mapping = response.json()["candidateMappings"][0]
    reviewed = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review",
        json={
            "state": "accepted",
            "rationale": "Review records the evidence but does not convert its outcome.",
            "reviewVersion": 0,
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    session = session_factory()
    stored = _rows(session, GovernanceEvidenceRun)[0]
    assert stored["result"] == status
    assert json.loads(stored["limitations_json"]) == [f"Explicit {status} limitation."]
    readiness = GovernanceAssuranceService(session).readiness(ORG_A, "assignment-001")
    assert readiness and readiness["missingEvidence"] == 1
    assert (
        session.execute(
            select(GovernanceControlAssessment.__table__.c.status).where(
                GovernanceControlAssessment.__table__.c.id == assessment_id
            )
        ).scalar_one()
        == "not_started"
    )
    session.close()


@pytest.mark.parametrize("bad_reference", ["source_hash", "control", "assessment", "cross_system"])
def test_unresolved_or_cross_system_candidate_rejects_entire_write(
    assurance_client,
    bad_reference: str,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    session = session_factory()
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id="system-002",
            workspace_id="workspace-001",
            org_id=ORG_A,
            name="System 002",
        )
    )
    session.execute(
        GovernanceFrameworkAssignment.__table__.insert().values(
            id="assignment-cross-system",
            org_id=ORG_A,
            system_id="system-002",
            framework_version_id="version-001",
        )
    )
    session.execute(
        GovernanceControlAssessment.__table__.insert().values(
            id="assessment-cross-system",
            org_id=ORG_A,
            system_id="system-002",
            framework_assignment_id="assignment-cross-system",
            control_definition_id="control-001",
        )
    )
    session.commit()
    session.close()
    passport = _passport()
    mapping = passport["frameworkMappings"][0]
    if bad_reference == "source_hash":
        mapping["framework"]["sourceHash"] = "b" * 64
    elif bad_reference == "control":
        mapping["control"]["externalId"] = "MISSING-1"
    elif bad_reference == "assessment":
        mapping["control"]["assessmentId"] = "missing-assessment"
    else:
        mapping["control"]["assessmentId"] = "assessment-cross-system"
    passport = with_server_hashes(EvidencePassport.model_validate(passport)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )

    response = _post(client, passport)

    assert response.status_code == 422, response.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    assert _count(session, GovernanceEvidenceArtifact) == 0
    assert _count(session, GovernanceEvidencePassportRevision) == 0
    session.close()


def test_candidate_control_must_belong_to_the_assigned_framework_version(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    session = session_factory()
    session.execute(
        GovernanceFrameworkVersion.__table__.insert().values(
            id="version-foreign",
            framework_key="foreign",
            name="Foreign",
            version_label="9",
            source_hash="b" * 64,
        )
    )
    session.execute(
        GovernanceControlDefinition.__table__.insert().values(
            id="control-foreign",
            framework_version_id="version-foreign",
            external_id="CTRL-1",
            title="Foreign control",
            statement="Not part of the assigned version",
            frequency="Annual",
            active=True,
        )
    )
    session.execute(
        GovernanceControlAssessment.__table__.update()
        .where(GovernanceControlAssessment.__table__.c.id == "assessment-001")
        .values(control_definition_id="control-foreign")
    )
    session.commit()
    session.close()

    response = _post(client, _passport())

    assert response.status_code == 422, response.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


def test_duplicate_mapping_ids_resolving_to_one_assessment_are_rejected_as_422(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    passport = _passport()
    duplicate_target = deepcopy(passport["frameworkMappings"][0])
    duplicate_target["mappingId"] = "mapping-002"
    passport["frameworkMappings"].append(duplicate_target)
    passport = with_server_hashes(EvidencePassport.model_validate(passport)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )

    response = _post(client, passport)

    assert response.status_code == 422, response.text
    assert "duplicate" in response.text.lower() or "assessment" in response.text.lower()
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    session.close()


@pytest.mark.parametrize(
    ("stage", "table"),
    [
        ("artifact", "governance_evidence_artifacts"),
        ("revision", "governance_evidence_passport_revisions"),
        ("mapping", "governance_control_evidence"),
        ("audit", "org_audit_logs"),
    ],
)
def test_forced_subwrite_failure_rolls_back_entire_new_run(
    assurance_client,
    stage: str,
    table: str,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    session = session_factory()
    session.execute(
        text(
            f"CREATE TRIGGER fail_{stage} BEFORE INSERT ON {table} "
            f"BEGIN SELECT RAISE(ABORT, 'forced {stage} failure'); END"
        )
    )
    session.commit()
    session.close()

    response = _post(client, _passport())

    assert response.status_code == 500, response.text
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 0
    assert _count(session, GovernanceEvidenceArtifact) == 0
    assert _count(session, GovernanceEvidencePassportRevision) == 0
    assert _count(session, GovernanceControlEvidence) == 0
    session.close()


def test_mapping_review_atomically_appends_hash_linked_snapshot_and_stale_review_writes_nothing(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    created = _post(client, _passport())
    mapping = created.json()["candidateMappings"][0]

    accepted = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review",
        json={
            "state": "accepted",
            "rationale": "Human reviewed the bounded source.",
            "reviewVersion": 0,
        },
    )
    stale = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review",
        json={"state": "rejected", "rationale": "Stale", "reviewVersion": 0},
    )

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["disposition"] == "revision_created"
    assert accepted.json()["passportRevision"] == 2
    assert stale.status_code == 409
    session = session_factory()
    revisions = _rows(
        session,
        GovernanceEvidencePassportRevision,
        order_by=GovernanceEvidencePassportRevision.__table__.c.passport_revision,
    )
    assert len(revisions) == 2
    assert revisions[1]["previous_revision_hash"] == revisions[0]["canonical_content_hash"]
    snapshot = json.loads(revisions[1]["snapshot_json"])
    reviewed_mapping = snapshot["frameworkMappings"][0]
    assert reviewed_mapping["state"] == "accepted"
    assert reviewed_mapping["review"]["reviewVersion"] == 1
    stored_mapping = _rows(session, GovernanceControlEvidence)[0]
    assert stored_mapping["state"] == "accepted"
    assert stored_mapping["review_version"] == 1
    assert stored_mapping["passport_revision_id"] == revisions[1]["id"]
    session.close()


def _concurrent_review_database(tmp_path: Path, *, two_mappings: bool):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'revision-race.db'}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    _seed_org(session, ORG_A, USER_A)
    _seed_system_and_control(session)
    passport = _passport()
    if two_mappings:
        session.execute(
            GovernanceControlDefinition.__table__.insert().values(
                id="control-002",
                framework_version_id="version-001",
                external_id="CTRL-2",
                title="Control two",
                statement="Second independently reviewable control",
                frequency="Annual",
                active=True,
            )
        )
        session.execute(
            GovernanceControlAssessment.__table__.insert().values(
                id="assessment-002",
                org_id=ORG_A,
                system_id="system-001",
                framework_assignment_id="assignment-001",
                control_definition_id="control-002",
            )
        )
        second = deepcopy(passport["frameworkMappings"][0])
        second["mappingId"] = "mapping-002"
        second["control"] = {"externalId": "CTRL-2", "assessmentId": "assessment-002"}
        passport["frameworkMappings"].append(second)
        passport = with_server_hashes(EvidencePassport.model_validate(passport)).model_dump(
            by_alias=True, mode="json", exclude_none=True
        )
    created = SqlAlchemyEvidenceIngestionStore(session).ingest(
        EvidencePassport.model_validate(passport), USER_A
    )
    mapping_ids = [mapping["id"] for mapping in created.candidate_mappings]
    session.close()
    return engine, factory, mapping_ids


def _race_reviews(factory, mapping_ids: list[str]):
    barrier = threading.Barrier(len(mapping_ids))

    def review(mapping_id: str):
        session = factory()
        try:
            barrier.wait(timeout=5)
            return SqlAlchemyEvidenceIngestionStore(session).review_mapping(
                ORG_A,
                mapping_id,
                "accepted",
                USER_A,
                "Concurrent bounded review",
                0,
            )
        except Exception as error:  # returned for exact race classification assertions
            return error
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=len(mapping_ids)) as executor:
        return list(executor.map(review, mapping_ids))


def test_two_sessions_racing_same_mapping_yield_one_revision_and_one_stale_conflict(
    tmp_path: Path,
) -> None:
    engine, factory, mapping_ids = _concurrent_review_database(tmp_path, two_mappings=False)

    outcomes = _race_reviews(factory, [mapping_ids[0], mapping_ids[0]])

    assert sum(isinstance(outcome, EvidenceRevisionConflict) for outcome in outcomes) == 1
    success = [outcome for outcome in outcomes if isinstance(outcome, dict)]
    assert len(success) == 1 and success[0]["disposition"] == "revision_created"
    session = factory()
    revisions = _rows(
        session,
        GovernanceEvidencePassportRevision,
        order_by=GovernanceEvidencePassportRevision.__table__.c.passport_revision,
    )
    assert [revision["passport_revision"] for revision in revisions] == [1, 2]
    session.close()
    engine.dispose()


def test_two_sessions_racing_different_mappings_allocate_unique_run_wide_revisions(
    tmp_path: Path,
) -> None:
    engine, factory, mapping_ids = _concurrent_review_database(tmp_path, two_mappings=True)

    outcomes = _race_reviews(factory, mapping_ids)

    assert all(isinstance(outcome, dict) for outcome in outcomes), outcomes
    assert {outcome["passportRevision"] for outcome in outcomes} == {2, 3}
    session = factory()
    revisions = _rows(
        session,
        GovernanceEvidencePassportRevision,
        order_by=GovernanceEvidencePassportRevision.__table__.c.passport_revision,
    )
    assert [revision["passport_revision"] for revision in revisions] == [1, 2, 3]
    assert revisions[1]["previous_revision_hash"] == revisions[0]["canonical_content_hash"]
    assert revisions[2]["previous_revision_hash"] == revisions[1]["canonical_content_hash"]
    session.close()
    engine.dispose()


def test_original_public_revision_replays_after_server_review_without_new_writes(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    original = _passport()
    created = _post(client, original)
    assert created.status_code == 201, created.text
    mapping = created.json()["candidateMappings"][0]
    reviewed = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review",
        json={"state": "accepted", "rationale": "Reviewed", "reviewVersion": 0},
    )
    assert reviewed.status_code == 200, reviewed.text

    replayed = _post(client, deepcopy(original))

    assert replayed.status_code == 200, replayed.text
    assert replayed.json()["disposition"] == "replayed"
    assert replayed.json()["latestRevision"] == 2
    session = session_factory()
    assert _count(session, GovernanceEvidenceRun) == 1
    assert _count(session, GovernanceEvidencePassportRevision) == 2
    assert _count(session, GovernanceControlEvidence) == 1
    assert len(_audit_rows(session, "evidence_passport.ingested")) == 1
    assert _audit_rows(session, "evidence_passport.conflict") == []
    session.close()


def test_forced_revision_failure_rolls_back_mapping_review(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    _seed_default(session_factory)
    mapping = _post(client, _passport()).json()["candidateMappings"][0]
    session = session_factory()
    session.execute(
        text(
            "CREATE TRIGGER fail_review_revision BEFORE INSERT ON "
            "governance_evidence_passport_revisions FOR EACH ROW "
            "BEGIN SELECT RAISE(ABORT, 'forced revision failure'); END"
        )
    )
    session.commit()
    session.close()

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review",
        json={"state": "accepted", "rationale": "Atomic review", "reviewVersion": 0},
    )

    assert response.status_code == 500
    session = session_factory()
    stored_mapping = _rows(session, GovernanceControlEvidence)[0]
    assert stored_mapping["state"] == "candidate"
    assert stored_mapping["review_version"] == 0
    assert _count(session, GovernanceEvidencePassportRevision) == 1
    session.close()


def test_get_evidence_runs_exposes_passport_provenance_without_raw_outputs(
    assurance_client,
) -> None:
    client, session_factory, _ = assurance_client
    system_id, _ = _seed_default(session_factory)
    assert _post(client, _passport()).status_code == 201

    response = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs"
    )

    assert response.status_code == 200
    item = response.json()[0]
    assert "disposition" not in item
    assert item["passportId"] == "passport-001"
    assert item["latestRevision"] == 1
    assert item["runContentHash"]
    assert item["latestCanonicalContentHash"]
    assert item["capabilityState"] == "validated"
    assert item["result"] == "passed"
    assert item["contentHash"] == item["runContentHash"]
    assert item["sourceType"] == "fairmind_evaluation"
    assert item["sourceIdentifier"] == "fairmind-bias-suite"
    assert item["capturedAt"] == "2026-07-18T00:05:00Z"
    assert item["suiteName"] == "Bias suite"
    assert item["suiteVersion"] == "2026.07"
    assert item["subjectVersion"] == "2026.07"
    assert item["runnerVersion"] == "3.0.0"
    assert item["assuranceSource"] == "fairmind_internal"
    assert item["limitations"] == ["Synthetic test set only."]
    assert [value["ordinal"] for value in item["artifacts"]] == [0, 1]
    assert "snapshot" not in item and "summary" not in item


def test_orm_create_all_enforces_s12_required_scope_digests_and_revision_links(
    assurance_client,
) -> None:
    _, session_factory, _ = assurance_client
    _seed_default(session_factory)
    session = session_factory()
    session.execute(text("PRAGMA foreign_keys = ON"))
    assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    runs = GovernanceEvidenceRun.__table__
    valid_run = {
        "id": "orm-run-1",
        "org_id": ORG_A,
        "system_id": "system-001",
        "workspace_id": "workspace-001",
        "passport_id": "passport-orm",
        "schema_version": "1.0.0",
        "capability_state": "validated",
        "assurance_source": "fairmind_internal",
        "source_type": "fairmind_evaluation",
        "source_identifier": "orm-suite",
        "run_id": "orm-run-1",
        "content_hash": "a" * 64,
        "result": "passed",
        "provenance_json": "{}",
        "artifact_refs_json": "[]",
        "limitations_json": "[]",
        "created_at": "now",
    }

    for mutation in (
        {"workspace_id": None},
        {"workspace_id": "missing-workspace"},
        {"passport_id": None},
        {"schema_version": None},
        {"capability_state": None},
        {"assurance_source": None},
        {"content_hash": "A" * 64},
        {"content_hash": "a" * 63},
    ):
        invalid = {**valid_run, **mutation, "id": f"bad-{len(mutation)}-{mutation!s}"}
        invalid["run_id"] = invalid["id"]
        with pytest.raises(IntegrityError):
            session.execute(runs.insert().values(**invalid))
            session.commit()
        session.rollback()

    session.execute(runs.insert().values(**valid_run))
    session.commit()
    artifacts = GovernanceEvidenceArtifact.__table__
    artifact = {
        "id": "orm-artifact-1",
        "org_id": ORG_A,
        "system_id": "system-001",
        "evidence_run_id": "orm-run-1",
        "artifact_id": "artifact-orm",
        "ordinal": 0,
        "role": "report",
        "uri": "s3://evidence/orm",
        "sha256": "B" * 64,
        "media_type": "application/json",
        "contains_sensitive_data": 0,
        "created_at": "now",
    }
    with pytest.raises(IntegrityError):
        session.execute(artifacts.insert().values(**artifact))
        session.commit()
    session.rollback()

    revisions = GovernanceEvidencePassportRevision.__table__
    revision = {
        "id": "orm-revision-1",
        "org_id": ORG_A,
        "system_id": "system-001",
        "evidence_run_id": "orm-run-1",
        "passport_id": "passport-orm",
        "passport_revision": 1,
        "previous_revision_hash": "b" * 64,
        "canonical_content_hash": "C" * 64,
        "snapshot_json": "{}",
        "created_by": USER_A,
        "created_at": "now",
    }
    with pytest.raises(IntegrityError):
        session.execute(revisions.insert().values(**revision))
        session.commit()
    session.rollback()
    revision.update(
        previous_revision_hash=None,
        canonical_content_hash="c" * 64,
        passport_revision=2,
        id="orm-revision-2",
    )
    with pytest.raises(IntegrityError):
        session.execute(revisions.insert().values(**revision))
        session.commit()
    session.rollback()
    session.execute(text("PRAGMA foreign_keys = OFF"))
    session.close()


def test_migration_011_creates_normalized_tenant_scoped_append_only_schema() -> None:
    migrations = REPO_ROOT / "apps/backend/migrations"
    assert not (migrations / "009_governance_assurance.sql").exists()
    assert (migrations / "011_governance_assurance.sql").exists()
    ordered = sorted(path.name for path in migrations.glob("[0-9][0-9][0-9]_*.sql"))
    assert ordered.index("010_environmental_governance.sql") < ordered.index(
        "011_governance_assurance.sql"
    )

    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE governance_workspaces (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE governance_ai_systems (
            id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
            name TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE governance_evidence (
            id TEXT PRIMARY KEY, system_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL, content_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        """)
    connection.executescript(sql_for("sqlite"))
    for table_name in (
        "governance_evidence_runs",
        "governance_evidence_artifacts",
        "governance_evidence_passport_revisions",
        "governance_control_evidence",
    ):
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        ).fetchall()
    }
    assert {
        "governance_evidence_runs_immutable_update",
        "governance_evidence_runs_immutable_delete",
        "governance_evidence_artifacts_immutable_update",
        "governance_evidence_artifacts_immutable_delete",
        "governance_evidence_passport_revisions_immutable_update",
        "governance_evidence_passport_revisions_immutable_delete",
    } <= triggers

    connection.execute(
        "INSERT INTO governance_workspaces (id, org_id, name, created_at, updated_at) "
        "VALUES ('workspace-1', 'org-1', 'Workspace', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, created_at, updated_at) "
        "VALUES ('system-1', 'workspace-1', 'org-1', 'System', 'now', 'now')"
    )
    run_insert = (
        "INSERT INTO governance_evidence_runs "
        "(id, org_id, system_id, workspace_id, passport_id, schema_version, "
        "capability_state, assurance_source, source_type, source_identifier, run_id, "
        "content_hash, result, created_at) VALUES (?, 'org-1', 'system-1', "
        "'workspace-1', 'passport-1', '1.0.0', 'validated', 'fairmind_internal', "
        "'fairmind_evaluation', 'suite-1', ?, ?, 'passed', 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(run_insert, ("run-short", "run-short", "a" * 63))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(run_insert, ("run-upper", "run-upper", "A" * 64))
    connection.execute(run_insert, ("run-1", "run-1", "a" * 64))

    artifact_insert = (
        "INSERT INTO governance_evidence_artifacts "
        "(id, org_id, system_id, evidence_run_id, artifact_id, ordinal, role, uri, "
        "sha256, media_type, contains_sensitive_data, created_at) VALUES "
        "(?, 'org-1', 'system-1', 'run-1', ?, ?, 'report', 's3://evidence/report', "
        "?, 'application/json', 0, 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(artifact_insert, ("artifact-upper", "bad", 0, "B" * 64))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            artifact_insert.replace("'org-1'", "'org-other'", 1),
            ("artifact-cross-tenant", "cross-tenant", 0, "b" * 64),
        )
    connection.execute(artifact_insert, ("artifact-1", "report", 0, "b" * 64))

    revision_insert = (
        "INSERT INTO governance_evidence_passport_revisions "
        "(id, org_id, system_id, evidence_run_id, passport_id, passport_revision, "
        "previous_revision_hash, canonical_content_hash, snapshot_json, created_at) "
        "VALUES (?, 'org-1', 'system-1', 'run-1', 'passport-1', 1, NULL, ?, '{}', 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(revision_insert, ("revision-upper", "C" * 64))
    connection.execute(revision_insert, ("revision-1", "c" * 64))

    for table_name, row_id in (
        ("governance_evidence_runs", "run-1"),
        ("governance_evidence_artifacts", "artifact-1"),
        ("governance_evidence_passport_revisions", "revision-1"),
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                f"UPDATE {table_name} SET created_at = 'later' WHERE id = ?", (row_id,)
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
    connection.close()

    postgresql_sql = sql_for("postgresql")
    adapter_source = (
        REPO_ROOT / "apps/backend/migrations/governance_assurance_migration.py"
    ).read_text(encoding="utf-8")
    assert "011_governance_assurance.sql" in adapter_source
    assert "import re" not in adapter_source and "re.sub" not in adapter_source
    sqlite_fixture = migrations / "fixtures/011_governance_assurance.sqlite.sql"
    assert sqlite_fixture.exists()
    assert sqlite_fixture not in migrations.glob("*.sql")
    assert not (migrations / "011_governance_assurance.sqlite.sql").exists()
    assert "governance_evidence_artifacts" in postgresql_sql
    assert "governance_evidence_passport_revisions" in postgresql_sql
    assert "CHECK (content_hash ~ '^[0-9a-f]{64}$')" in postgresql_sql
    assert "FOREIGN KEY (evidence_run_id, system_id, org_id)" in postgresql_sql
    assert "FOREIGN KEY (passport_revision_id, evidence_id, system_id, org_id)" in postgresql_sql
    assert "CREATE TRIGGER governance_evidence_passport_revisions_no_mutation" in postgresql_sql


def test_old_009_postgresql_installation_has_explicit_ledgered_s12_upgrade_path() -> None:
    migrations = REPO_ROOT / "apps/backend/migrations"
    upgrade = migrations / "upgrade_paths/009_to_011_evidence_passport.sql"
    instructions = migrations / "upgrade_paths/README.md"
    assert upgrade.exists() and instructions.exists()
    assert upgrade not in migrations.glob("*.sql")
    sql = upgrade.read_text(encoding="utf-8")
    assert "BEGIN;" in sql and sql.rstrip().endswith("COMMIT;")
    assert "pg_advisory_xact_lock" in sql
    assert "fairmind_operator_migration_ledger" in sql
    assert "009-to-011-evidence-passport-v1" in sql
    assert "SELECT 1 FROM pg_constraint" in sql
    assert "to_regclass('governance_evidence_runs') IS NULL" in sql
    assert "old 009 governance assurance schema is not installed" in sql
    assert "conrelid = 'governance_evidence_runs'::regclass" in sql
    assert "conrelid = 'governance_control_evidence'::regclass" in sql
    assert "CREATE TABLE IF NOT EXISTS governance_evidence_artifacts" in sql
    assert "CREATE TABLE IF NOT EXISTS governance_evidence_passport_revisions" in sql
    assert "ADD CONSTRAINT uq_governance_evidence_run" not in sql
    assert "ADD CONSTRAINT fk_governance_evidence_source_run" not in sql
    assert "scripts/migrate.py" in instructions.read_text(encoding="utf-8")

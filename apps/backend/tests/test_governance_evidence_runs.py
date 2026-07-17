from datetime import datetime, timedelta, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.routes.governance_assurance import EvidenceRunEnvelope
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from database.connection import Base, get_db
from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidence,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)
from database.models import Organization, OrganizationMember, User
from src.application.services.governance_assurance_service import GovernanceAssuranceService, _is_stale
from migrations.governance_assurance_migration import sql_for


ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
USER_A = str(uuid.uuid4())
USER_B = str(uuid.uuid4())


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
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
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


def _seed_org(session, org_id: str, user_id: str) -> None:
    user_uuid = uuid.UUID(user_id)
    session.execute(User.__table__.insert().values(id=user_uuid, email=f"{user_id}@example.test", username=user_id))
    session.execute(Organization.__table__.insert().values(id=uuid.UUID(org_id), name=org_id, slug=org_id, owner_id=user_uuid))
    session.execute(OrganizationMember.__table__.insert().values(id=uuid.uuid4(), org_id=uuid.UUID(org_id), user_id=user_uuid, role="admin", status="active"))


def _seed_system_and_control(session) -> tuple[str, str]:
    session.execute(GovernanceWorkspace.__table__.insert().values(id="workspace-a", org_id=ORG_A, name="Workspace A"))
    session.execute(GovernanceAISystem.__table__.insert().values(id="system-a", workspace_id="workspace-a", org_id=ORG_A, name="System A"))
    session.execute(GovernanceFrameworkVersion.__table__.insert().values(id="version-a", framework_key="generic", name="Generic", version_label="1", source_hash="source"))
    session.execute(GovernanceControlDefinition.__table__.insert().values(id="control-a", framework_version_id="version-a", external_id="CTRL-1", title="Control", statement="Statement", frequency="Every 3 months", active=True))
    session.execute(GovernanceFrameworkAssignment.__table__.insert().values(id="assignment-a", org_id=ORG_A, system_id="system-a", framework_version_id="version-a"))
    session.execute(GovernanceControlAssessment.__table__.insert().values(id="assessment-a", org_id=ORG_A, system_id="system-a", framework_assignment_id="assignment-a", control_definition_id="control-a"))
    session.commit()
    return "system-a", "assessment-a"


def _seed_second_system(session) -> str:
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id="system-b", workspace_id="workspace-a", org_id=ORG_A, name="System B"
        )
    )
    session.commit()
    return "system-b"


def _envelope(**overrides) -> dict:
    envelope = {
        "sourceType": "evaluation",
        "sourceIdentifier": "fairmind-bias-suite",
        "runId": "run-1",
        "result": "failed",
        "capturedAt": "2026-07-17T00:00:00Z",
        "summary": {"score": 0.2, "passed": False},
        "limitations": ["Synthetic test-set only"],
        "artifactReferences": [{"uri": "s3://customer/evaluations/run-1.json", "sha256": "a" * 64}],
        "controlExternalIds": ["CTRL-1"],
    }
    envelope.update(overrides)
    return envelope


def test_ingestion_canonicalizes_hashes_is_idempotent_and_keeps_failed_run(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    first = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope())
    second = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(summary={"passed": False, "score": 0.2}))

    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    assert first.json()["runId"] == second.json()["runId"]
    assert first.json()["contentHash"] == second.json()["contentHash"]
    assert first.json()["result"] == "failed"
    session = session_factory()
    assert session.execute(select(GovernanceEvidenceRun.__table__.c.result)).scalar_one() == "failed"
    assert session.execute(select(GovernanceEvidence.__table__.c.content_json)).scalar_one() == '{"passed":false,"score":0.2}'
    session.close()


def test_evidence_run_response_exposes_stored_provenance_without_raw_outputs(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(
            suiteName="Bias and subgroup parity",
            suiteVersion="2026.07",
            subjectVersion="2.4.1",
            runnerVersion="fairmind-runner 1.8.0",
            assuranceSource="fairmind_internal",
        ),
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["suiteName"] == "Bias and subgroup parity"
    assert payload["suiteVersion"] == "2026.07"
    assert payload["subjectVersion"] == "2.4.1"
    assert payload["runnerVersion"] == "fairmind-runner 1.8.0"
    assert payload["assuranceSource"] == "fairmind_internal"
    assert payload["limitations"] == ["Synthetic test-set only"]
    assert "summary" not in payload

def test_source_run_cannot_be_reingested_with_different_content(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    first = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope())
    mutation = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(summary={"passed": False, "score": 0.3}))

    assert first.status_code == 201, first.text
    assert mutation.status_code == 409
    session = session_factory()
    run = session.execute(select(GovernanceEvidenceRun.__table__)).mappings().one()
    with pytest.raises(IntegrityError):
        session.execute(
            insert(GovernanceEvidenceRun.__table__).values(
                id="same-source-run", org_id=ORG_A, system_id=system_id,
                source_type=run["source_type"], source_identifier=run["source_identifier"],
                run_id=run["run_id"], content_hash="different-hash",
            )
        )
        session.commit()
    session.rollback()
    session.close()


def test_same_envelope_on_another_system_creates_a_distinct_run_and_artifact(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    second_system_id = _seed_second_system(session)
    session.close()

    first = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope())
    second = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{second_system_id}/evidence-runs", json=_envelope())

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    session = session_factory()
    assert len(session.execute(select(GovernanceEvidenceRun.__table__.c.id)).all()) == 2
    assert len(session.execute(select(GovernanceEvidence.__table__.c.id)).all()) == 2
    session.close()


def test_ingestion_creates_only_explicit_candidates_and_review_history(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, assessment_id = _seed_system_and_control(session)
    session.close()

    ingested = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope())
    assert ingested.status_code == 201, ingested.text
    mapping = ingested.json()["candidateMappings"][0]
    assert mapping["controlAssessmentId"] == assessment_id
    assert mapping["state"] == "candidate"
    accepted = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review", json={"state": "accepted", "rationale": "Reviewed test evidence.", "reviewVersion": 0})
    stale = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review", json={"state": "rejected", "rationale": "Stale reviewer.", "reviewVersion": 0})
    rejected = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/evidence-mappings/{mapping['id']}/review", json={"state": "rejected", "rationale": "Coverage was too narrow.", "reviewVersion": accepted.json()["reviewVersion"]})

    assert accepted.status_code == rejected.status_code == 200
    assert stale.status_code == 409
    assert rejected.json()["state"] == "rejected"
    assert [entry["state"] for entry in rejected.json()["reviewHistory"]] == ["accepted", "rejected"]
    assert all(entry["reviewedBy"] == USER_A and entry["reviewedAt"] for entry in rejected.json()["reviewHistory"])
    session = session_factory()
    assert session.execute(
        select(GovernanceControlAssessment.__table__.c.status).where(
            GovernanceControlAssessment.__table__.c.id == assessment_id
        )
    ).scalar_one() == "not_started"
    session.close()


def test_unmatched_explicit_control_ids_preserve_the_run_without_candidates(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    ingested = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(runId="run-unmatched", controlExternalIds=["MISSING-1"]),
    )

    assert ingested.status_code == 201, ingested.text
    assert ingested.json()["candidateMappings"] == []
    session = session_factory()
    assert session.execute(select(GovernanceEvidenceRun.__table__.c.id)).scalar_one()
    session.close()


def test_evidence_mapping_and_run_are_hidden_across_organizations(assurance_client) -> None:
    client, session_factory, active_user = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    _seed_org(session, ORG_B, USER_B)
    system_id, _ = _seed_system_and_control(session)
    session.close()
    ingested = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope()).json()
    active_user["value"] = _token(USER_B)

    listed = client.get(f"/api/v1/ai-governance/organizations/{ORG_B}/systems/{system_id}/evidence-runs")
    mapped = client.post(f"/api/v1/ai-governance/organizations/{ORG_B}/evidence/{ingested['evidenceId']}/control-mappings", json={"controlAssessmentId": "assessment-a"})
    reviewed = client.post(f"/api/v1/ai-governance/organizations/{ORG_B}/evidence-mappings/{ingested['candidateMappings'][0]['id']}/review", json={"state": "accepted", "reviewVersion": 0})

    assert listed.status_code == mapped.status_code == reviewed.status_code == 404


def test_third_party_assertion_requires_assessor_identity_and_independence(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    rejected = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(assuranceSource="third_party"))
    accepted = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(assuranceSource="third_party", thirdPartyAssessor={"identity": "Assurance Co.", "independenceAssertion": True}))
    malformed_source = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(runId="run-third-party", assuranceSource="third-party"))
    unknown_source = client.post(f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs", json=_envelope(runId="run-unknown-source", assuranceSource="external"))

    assert rejected.status_code == 422
    assert accepted.status_code == 201, accepted.text
    assert malformed_source.status_code == unknown_source.status_code == 422


@pytest.mark.parametrize("sensitive_key", ["raw output", "raw.output", "CHAIN of Thought", "CoMpLeTiOn!!"])
def test_raw_outputs_are_rejected_recursively_with_punctuation_normalization(
    assurance_client, sensitive_key: str
) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(summary={"metric": 0.2, "findings": [{sensitive_key: "do not store"}]}),
    )

    assert response.status_code == 422


def test_raw_outputs_are_rejected_recursively_and_workbook_frequencies_are_parsed(assurance_client) -> None:
    with pytest.raises(Exception):
        EvidenceRunEnvelope(**_envelope(rawOutput={"prompt": "do not store"}))

    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()
    nested = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(summary={"metric": 0.2, "findings": [{"chainOfThought": "do not store"}]}),
    )
    assert nested.status_code == 422

    captured = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    assert _is_stale(captured, "Every 3 months")
    assert not _is_stale(captured, "Every 6 months")
    assert not _is_stale(captured, "Every 12 months")


@pytest.mark.parametrize(
    "artifact_references",
    [
        [{"uri": "x" * 2049, "sha256": "a" * 64}],
        [{"uri": "reference", "sha256": "not-a-digest"}],
        [{"uri": "reference", "sha256": "a" * 64}] * 51,
    ],
    ids=["oversized-uri", "invalid-digest", "too-many-references"],
)
def test_artifact_references_have_strict_shape_and_count_limits(assurance_client, artifact_references: list[dict[str, str]]) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(artifactReferences=artifact_references),
    )

    assert response.status_code == 422


def test_artifact_references_have_an_aggregate_size_limit(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, _ = _seed_system_and_control(session)
    session.close()
    references = [{"uri": "s3://" + "a" * 1800, "sha256": "a" * 64}] * 50

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/evidence-runs",
        json=_envelope(artifactReferences=references),
    )

    assert response.status_code == 422


def test_readiness_uses_captured_time_and_evidence_source_run_is_a_foreign_key(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    system_id, assessment_id = _seed_system_and_control(session)
    now = datetime.now(timezone.utc)
    session.execute(
        GovernanceEvidenceRun.__table__.insert().values(
            id="captured-old", org_id=ORG_A, system_id=system_id, source_type="evaluation",
            source_identifier="suite", run_id="captured-old", content_hash="captured-old",
            captured_at=(now - timedelta(days=100)).isoformat(), created_at=now.isoformat(),
        )
    )
    session.execute(
        GovernanceEvidence.__table__.insert().values(
            id="artifact-old", org_id=ORG_A, system_id=system_id, source_run_id="captured-old",
            evidence_type="evaluation_run", content_json="{}",
        )
    )
    session.execute(
        GovernanceControlEvidence.__table__.insert().values(
            id="mapping-old", org_id=ORG_A, system_id=system_id, evidence_id="captured-old",
            artifact_evidence_id="artifact-old", control_assessment_id=assessment_id, state="accepted",
        )
    )
    session.commit()
    readiness = GovernanceAssuranceService(session).readiness(ORG_A, "assignment-a")
    session.close()

    assert readiness and readiness["staleEvidence"] == 1
    assert any(foreign_key.target_fullname == "governance_evidence_runs.id" for foreign_key in GovernanceEvidence.__table__.c.source_run_id.foreign_keys)
    assert "FOREIGN KEY (source_run_id)" in sql_for("postgresql")
    assert "governance_evidence_source_run_insert" in sql_for("sqlite")

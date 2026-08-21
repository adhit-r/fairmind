"""Native PostgreSQL contract for unverified imported evidence."""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.ports.evidence_review import EvidenceReviewScope
from src.application.ports.governance_decision import GovernanceDecisionScope
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.application.services.imported_evidence_service import ImportedEvidenceService
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.domain.assurance.evaluation_v2 import canonical_sha256
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.test_imported_evidence_delivery_integrity_013i import (
    _seed_postgresql_run,
    postgresql_013i_engine,
)


def _payload(captured_at: str, *, content_hash: str = "a" * 64) -> dict[str, object]:
    return {
        "reportId": "report-native-e2e",
        "reportContentHash": content_hash,
        "capturedAt": captured_at,
        "claimedTechnicalStatus": "succeeded",
        "claimedEvidenceResultStatus": "passed",
        "claimedResultSummary": {"caseCount": 4},
        "artifactRefs": [
            {
                "artifactId": "report-json",
                "role": "report",
                "sha256": "b" * 64,
                "mediaType": "application/json",
                "sizeBytes": 4096,
            }
        ],
        "limitations": [],
    }


def _identities() -> tuple[tuple[str, ...], object]:
    values = tuple(str(uuid.uuid4()) for _ in range(6))
    iterator = iter(values)
    return values, lambda: next(iterator)


def test_native_import_is_atomic_idempotent_and_never_decision_authority(
    postgresql_013i_engine: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = postgresql_013i_engine
    graph = _seed_postgresql_run(engine, delivery_mode="imported_report")
    scope = EvidenceAdmissionScope(
        graph["org_id"], graph["system_id"], graph["run_id"], graph["execution_id"]
    )
    ids, uuid_factory = _identities()
    session = Session(engine, expire_on_commit=False)
    try:
        captured_at = str(
            session.scalar(text("SELECT fairmind_canonical_clock_utc_013f()"))
        )
        payload = _payload(captured_at)
        service = ImportedEvidenceService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
            uuid_factory=uuid_factory,
        )
        created = service.import_unverified_report(
            scope=scope,
            actor_id=graph["actor_id"],
            idempotency_key=f"import-{graph['token']}",
            payload=payload,
        )
        replay = service.import_unverified_report(
            scope=scope,
            actor_id=graph["actor_id"],
            idempotency_key=f"import-{graph['token']}",
            payload=payload,
        )

        assert replay.replayed is True
        assert replay.body == created.body
        assert created.body["resultAuthority"] == "claimed"
        assert created.body["humanReviewOnly"] is True
        assert created.body["decisionEvidenceEligible"] is False

        evidence = session.execute(
            text("SELECT * FROM governance_evidence_runs WHERE id=:id"),
            {"id": ids[0]},
        ).mappings().one()
        revision = session.execute(
            text("SELECT * FROM governance_evidence_passport_revisions WHERE id=:id"),
            {"id": ids[1]},
        ).mappings().one()
        admission = session.execute(
            text("SELECT * FROM governance_evidence_admissions WHERE id=:id"),
            {"id": ids[3]},
        ).mappings().one()
        suite = session.execute(
            text(
                "SELECT * FROM governance_evaluation_run_suite_executions "
                "WHERE id=:id"
            ),
            {"id": graph["execution_id"]},
        ).mappings().one()
        snapshot = json.loads(revision["snapshot_json"])
        report = snapshot["report"]

        assert evidence["run_id"] == graph["execution_id"]
        assert evidence["content_hash"] == report["contentHash"] == "a" * 64
        assert evidence["result"] == report["claimedEvidenceResultStatus"] == "passed"
        assert evidence["captured_at"] == report["capturedAt"]
        assert evidence["expires_at"] == report["effectiveExpiresAt"]
        assert json.loads(evidence["artifact_refs_json"]) == report["artifactRefs"]
        assert json.loads(evidence["limitations_json"]) == report["limitations"]
        assert revision["canonical_content_hash"] == canonical_sha256(snapshot)
        assert admission["admission_status"] == "unverified"
        assert admission["issuer_id"] is None
        assert admission["signing_key_id"] is None
        assert admission["signer_key_id"] is None
        assert admission["signed_at"] is None
        assert admission["captured_at"] == report["capturedAt"]
        assert admission["effective_expires_at"] == report["effectiveExpiresAt"]
        assert suite["evidence_run_id"] == ids[0]
        assert suite["passport_revision_id"] == ids[1]
        assert json.loads(suite["result_summary_json"]) == report["claimedResultSummary"]
        assert json.loads(suite["limitations_json"]) == report["limitations"]
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evidence_verification_receipts "
                "WHERE admission_id=:id"
            ),
            {"id": ids[3]},
        ) == 0
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evidence_nonce_claims "
                "WHERE admission_id=:id"
            ),
            {"id": ids[3]},
        ) == 1
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_suite_evidence_links "
                "WHERE admission_id=:id"
            ),
            {"id": ids[3]},
        ) == 1
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_idempotency_records "
                "WHERE org_id=:org_id AND operation="
                "'evaluation-v2.evidence.unverified-import' AND status='completed'"
            ),
            {"org_id": graph["org_id"]},
        ) == 1
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND action="
                "'evaluation_v2.evidence.unverified_imported' AND outcome='success'"
            ),
            {"org_id": graph["org_id"]},
        ) == 1

        with pytest.raises(EvaluationWorkbenchError) as conflict:
            service.import_unverified_report(
                scope=scope,
                actor_id=graph["actor_id"],
                idempotency_key=f"import-{graph['token']}",
                payload={**payload, "reportContentHash": "c" * 64},
            )
        assert conflict.value.code == "idempotency_conflict"
        assert session.scalar(
            text("SELECT count(*) FROM governance_evidence_runs WHERE id=:id"),
            {"id": ids[0]},
        ) == 1

        review = VerifiedEvidenceReviewService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        )
        with pytest.raises(EvaluationWorkbenchError) as denied_review:
            review.review_verified_evidence(
                scope=EvidenceReviewScope(
                    graph["org_id"],
                    graph["workspace_id"],
                    graph["system_id"],
                    graph["run_id"],
                    graph["execution_id"],
                    ids[3],
                    ids[1],
                ),
                actor_id=graph["actor_id"],
                idempotency_key=f"review-{graph['token']}",
                decision="accepted",
                rationale="Should remain unavailable for unverified material.",
                expected_review_version=0,
            )
        assert denied_review.value.code == "binding_integrity_error"

        decision = GovernanceDecisionService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        )
        with pytest.raises(EvaluationWorkbenchError) as denied_decision:
            decision.decide(
                scope=GovernanceDecisionScope(
                    graph["org_id"],
                    graph["workspace_id"],
                    graph["system_id"],
                    graph["run_id"],
                ),
                actor_id=graph["actor_id"],
                idempotency_key=f"decision-{graph['token']}",
                expected_verdict_version=0,
                overall_verdict="insufficient",
                layer_verdicts={
                    "suites": {graph["execution_id"]: "insufficient"},
                    "modalities": {},
                    "components": {},
                    "riskDimensions": {},
                },
                rationale="Unverified imports cannot authorize a decision.",
            )
        assert denied_decision.value.code == "governance_decision_evidence_not_ready"
    finally:
        session.close()

    rollback_graph = _seed_postgresql_run(engine, delivery_mode="imported_report")
    rollback_scope = EvidenceAdmissionScope(
        rollback_graph["org_id"],
        rollback_graph["system_id"],
        rollback_graph["run_id"],
        rollback_graph["execution_id"],
    )
    rollback_ids, rollback_factory = _identities()
    original_persist = SqlAlchemyEvaluationWorkbenchRepository.persist_unverified_imported_evidence

    def fail_after_graph_write(self, command):
        original_persist(self, command)
        raise RuntimeError("force transaction rollback")

    monkeypatch.setattr(
        SqlAlchemyEvaluationWorkbenchRepository,
        "persist_unverified_imported_evidence",
        fail_after_graph_write,
    )
    rollback_session = Session(engine, expire_on_commit=False)
    try:
        captured_at = str(
            rollback_session.scalar(text("SELECT fairmind_canonical_clock_utc_013f()"))
        )
        rollback_service = ImportedEvidenceService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(rollback_session),
            uuid_factory=rollback_factory,
        )
        with pytest.raises(EvaluationWorkbenchError) as failed:
            rollback_service.import_unverified_report(
                scope=rollback_scope,
                actor_id=rollback_graph["actor_id"],
                idempotency_key=f"rollback-{rollback_graph['token']}",
                payload=_payload(captured_at),
            )
        assert failed.value.code == "evaluation_persistence_failed"
        assert rollback_session.scalar(
            text("SELECT count(*) FROM governance_evidence_runs WHERE id=:id"),
            {"id": rollback_ids[0]},
        ) == 0
        assert rollback_session.scalar(
            text(
                "SELECT count(*) FROM governance_idempotency_records "
                "WHERE org_id=:org_id AND operation="
                "'evaluation-v2.evidence.unverified-import'"
            ),
            {"org_id": rollback_graph["org_id"]},
        ) == 0
        assert rollback_session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND action="
                "'evaluation_v2.evidence.unverified_imported'"
            ),
            {"org_id": rollback_graph["org_id"]},
        ) == 0
    finally:
        rollback_session.close()

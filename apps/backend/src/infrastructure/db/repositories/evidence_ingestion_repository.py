"""SQLAlchemy persistence adapter for canonical Evidence Passport ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import threading
import uuid
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidenceArtifact,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
)
from database.models import OrganizationAuditLog
from src.application.ports.evidence_ingestion import (
    EvidenceAuditWriteError,
    EvidenceMappingReferenceError,
    EvidencePersistenceError,
    EvidenceRevisionConflict,
    EvidenceRunConflict,
    IngestionDisposition,
    IngestionResult,
    ScopedSystem,
)
from src.domain.assurance.evidence_passport import (
    EvidencePassport,
    calculate_canonical_content_hash,
    with_server_hashes,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _uuid_or_none(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


_REVISION_LOCKS_GUARD = threading.Lock()
_REVISION_LOCKS: dict[str, threading.Lock] = {}


def _revision_lock(run_id: str) -> threading.Lock:
    """Serialize SQLite/in-process reviews; PostgreSQL also takes a row lock."""
    with _REVISION_LOCKS_GUARD:
        return _REVISION_LOCKS.setdefault(run_id, threading.Lock())


class SqlAlchemyEvidenceIngestionStore:
    """Own transaction, idempotency-race, mapping-resolution, and audit behavior."""

    def __init__(self, session: object) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session

    def scoped_system(self, org_id: str, system_id: str) -> ScopedSystem | None:
        systems = GovernanceAISystem.__table__
        row = (
            self.db.execute(
                select(systems.c.org_id, systems.c.workspace_id, systems.c.id).where(
                    systems.c.org_id == org_id,
                    systems.c.id == system_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if not row:
            return None
        return ScopedSystem(
            org_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["id"],
        )

    def ingest(self, passport: object, actor_id: str) -> IngestionResult:
        if not isinstance(passport, EvidencePassport):
            raise TypeError("normalized EvidencePassport required")
        existing = self._find_run(passport)
        if existing:
            return self._classify_existing(existing, passport, actor_id)
        resolved = self._resolve_candidates(passport)
        try:
            run_id = self._insert_new(passport, actor_id, resolved)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self._find_run(passport)
            if existing:
                return self._classify_existing(existing, passport, actor_id)
            raise EvidencePersistenceError("Evidence Passport transaction failed")
        except (EvidenceMappingReferenceError, EvidenceRunConflict, EvidenceAuditWriteError):
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise EvidencePersistenceError("Evidence Passport transaction failed") from error
        return self._result(run_id, IngestionDisposition.CREATED)

    def list_runs(self, org_id: str, system_id: str) -> list[IngestionResult] | None:
        if self.scoped_system(org_id, system_id) is None:
            return None
        runs = GovernanceEvidenceRun.__table__
        run_ids = self.db.execute(
            select(runs.c.id)
            .where(
                runs.c.org_id == org_id,
                runs.c.system_id == system_id,
            )
            .order_by(runs.c.created_at.desc())
        ).scalars()
        return [self._result(run_id, None) for run_id in run_ids]

    def review_mapping(
        self,
        org_id: str,
        mapping_id: str,
        state: str,
        actor_id: str,
        rationale: str | None,
        review_version: int,
    ) -> dict[str, Any] | None:
        mappings = GovernanceControlEvidence.__table__
        row = (
            self.db.execute(
                select(mappings).where(mappings.c.id == mapping_id, mappings.c.org_id == org_id)
            )
            .mappings()
            .one_or_none()
        )
        if not row:
            return None
        if not row["source_mapping_id"] or not row["passport_revision_id"]:
            return self._review_mapping_unserialized(
                org_id, mapping_id, state, actor_id, rationale, review_version
            )

        # End any read transaction opened by membership/lookup before waiting.
        # Once inside the process lock, PostgreSQL's FOR UPDATE provides the
        # cross-worker run-wide serialization boundary; SQLite uses this lock
        # and a fresh transaction so it cannot retain a stale revision view.
        run_id = row["evidence_id"]
        self.db.rollback()
        lock = _revision_lock(run_id)
        with lock:
            runs = GovernanceEvidenceRun.__table__
            self.db.execute(
                select(runs.c.id)
                .where(runs.c.id == run_id, runs.c.org_id == org_id)
                .with_for_update()
            ).scalar_one()
            return self._review_mapping_unserialized(
                org_id, mapping_id, state, actor_id, rationale, review_version
            )

    def _review_mapping_unserialized(
        self,
        org_id: str,
        mapping_id: str,
        state: str,
        actor_id: str,
        rationale: str | None,
        review_version: int,
    ) -> dict[str, Any] | None:
        mappings = GovernanceControlEvidence.__table__
        row = (
            self.db.execute(
                select(mappings).where(mappings.c.id == mapping_id, mappings.c.org_id == org_id)
            )
            .mappings()
            .one_or_none()
        )
        if not row:
            return None
        if state not in {"accepted", "rejected"}:
            raise ValueError("Review state must be accepted or rejected")
        if row["review_version"] != review_version:
            raise EvidenceRevisionConflict("Evidence mapping was reviewed by another user")
        if not row["source_mapping_id"] or not row["passport_revision_id"]:
            return self._review_legacy_mapping(row, state, actor_id, rationale, review_version)

        revisions = GovernanceEvidencePassportRevision.__table__
        latest = (
            self.db.execute(
                select(revisions)
                .where(
                    revisions.c.evidence_run_id == row["evidence_id"],
                    revisions.c.org_id == org_id,
                )
                .order_by(revisions.c.passport_revision.desc())
            )
            .mappings()
            .first()
        )
        if latest is None:
            raise EvidenceRevisionConflict("Passport revision chain is missing")
        snapshot = json.loads(latest["snapshot_json"])
        reviewed_at = _now()
        matched = False
        for mapping in snapshot["frameworkMappings"]:
            if mapping["mappingId"] != row["source_mapping_id"]:
                continue
            mapping["state"] = state
            mapping["review"] = {
                "decision": state,
                "reviewer": {"actorType": "user", "actorId": actor_id},
                "reviewedAt": reviewed_at,
                "rationale": rationale or "Reviewed without additional rationale.",
                "reviewVersion": review_version + 1,
            }
            matched = True
            break
        if not matched:
            raise EvidenceRevisionConflict("Source mapping is absent from latest passport snapshot")
        snapshot["passportRevision"] = latest["passport_revision"] + 1
        snapshot["previousRevisionHash"] = latest["canonical_content_hash"]
        normalized = with_server_hashes(EvidencePassport.model_validate(snapshot))
        protocol = normalized.model_dump(
            by_alias=True, mode="json", exclude_none=True, exclude_unset=True
        )
        revision_id = str(uuid.uuid4())
        history = json.loads(row["review_history_json"] or "[]")
        history.append(
            {
                "state": state,
                "rationale": rationale,
                "reviewedBy": actor_id,
                "reviewedAt": reviewed_at,
            }
        )
        try:
            self.db.execute(
                insert(revisions).values(
                    id=revision_id,
                    org_id=row["org_id"],
                    system_id=row["system_id"],
                    evidence_run_id=row["evidence_id"],
                    passport_id=latest["passport_id"],
                    passport_revision=latest["passport_revision"] + 1,
                    previous_revision_hash=latest["canonical_content_hash"],
                    canonical_content_hash=protocol["canonicalContentHash"],
                    snapshot_json=_json(protocol),
                    created_by=actor_id,
                    created_at=reviewed_at,
                )
            )
            updated = self.db.execute(
                update(mappings)
                .where(
                    mappings.c.id == mapping_id,
                    mappings.c.org_id == org_id,
                    mappings.c.review_version == review_version,
                )
                .values(
                    state=state,
                    mapping_rationale=rationale,
                    reviewed_by=actor_id,
                    reviewed_at=reviewed_at,
                    review_history_json=_json(history),
                    review_version=review_version + 1,
                    passport_revision_id=revision_id,
                    updated_at=reviewed_at,
                )
            )
            if updated.rowcount != 1:
                raise EvidenceRevisionConflict("Evidence mapping was reviewed by another user")
            self._insert_audit(
                org_id=org_id,
                actor_id=actor_id,
                action="evidence_passport.revision_created",
                resource_id=row["evidence_id"],
                status="success",
                changes={
                    "passportId": latest["passport_id"],
                    "passportRevision": latest["passport_revision"] + 1,
                    "canonicalContentHash": protocol["canonicalContentHash"],
                    "mappingId": row["source_mapping_id"],
                },
            )
            self.db.commit()
        except EvidenceRevisionConflict:
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise EvidencePersistenceError("passport revision transaction failed") from error
        result = self._mapping(mapping_id)
        result["disposition"] = IngestionDisposition.REVISION_CREATED.value
        result["passportRevision"] = latest["passport_revision"] + 1
        result["canonicalContentHash"] = protocol["canonicalContentHash"]
        return result

    def _review_legacy_mapping(
        self,
        row: dict[str, Any],
        state: str,
        actor_id: str,
        rationale: str | None,
        review_version: int,
    ) -> dict[str, Any]:
        reviewed_at = _now()
        history = json.loads(row["review_history_json"] or "[]")
        history.append(
            {
                "state": state,
                "rationale": rationale,
                "reviewedBy": actor_id,
                "reviewedAt": reviewed_at,
            }
        )
        mappings = GovernanceControlEvidence.__table__
        updated = self.db.execute(
            update(mappings)
            .where(
                mappings.c.id == row["id"],
                mappings.c.org_id == row["org_id"],
                mappings.c.review_version == review_version,
            )
            .values(
                state=state,
                mapping_rationale=rationale,
                reviewed_by=actor_id,
                reviewed_at=reviewed_at,
                review_history_json=_json(history),
                review_version=review_version + 1,
                updated_at=reviewed_at,
            )
        )
        if updated.rowcount != 1:
            self.db.rollback()
            raise EvidenceRevisionConflict("Evidence mapping was reviewed by another user")
        self.db.commit()
        return self._mapping(row["id"])

    def _find_run(self, passport: EvidencePassport) -> dict[str, Any] | None:
        runs = GovernanceEvidenceRun.__table__
        return (
            self.db.execute(
                select(runs).where(
                    runs.c.org_id == passport.organization_id,
                    runs.c.system_id == passport.ai_system.system_id,
                    runs.c.source_type == passport.evaluation.source_type.value,
                    runs.c.source_identifier == passport.evaluation.source_identifier,
                    runs.c.run_id == passport.evaluation.run_id,
                )
            )
            .mappings()
            .one_or_none()
        )

    def _classify_existing(
        self,
        existing: dict[str, Any],
        passport: EvidencePassport,
        actor_id: str,
    ) -> IngestionResult:
        revisions = GovernanceEvidencePassportRevision.__table__
        revision_one = (
            self.db.execute(
                select(revisions).where(
                    revisions.c.evidence_run_id == existing["id"],
                    revisions.c.passport_revision == 1,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            revision_one
            and existing["content_hash"] == passport.evaluation.run_content_hash
            and revision_one["canonical_content_hash"] == passport.canonical_content_hash
        ):
            return self._result(existing["id"], IngestionDisposition.REPLAYED)
        changes = {
            "sourceType": passport.evaluation.source_type.value,
            "sourceIdentifier": passport.evaluation.source_identifier,
            "runId": passport.evaluation.run_id,
            "existingRunContentHash": existing["content_hash"],
            "incomingRunContentHash": passport.evaluation.run_content_hash,
            "existingCanonicalContentHash": (
                revision_one["canonical_content_hash"] if revision_one else None
            ),
            "incomingCanonicalContentHash": passport.canonical_content_hash,
        }
        try:
            self._insert_audit(
                org_id=passport.organization_id,
                actor_id=actor_id,
                action="evidence_passport.conflict",
                resource_id=existing["id"],
                status="failure",
                changes=changes,
            )
            self.db.commit()
        except Exception as error:
            self.db.rollback()
            raise EvidenceAuditWriteError(
                "required conflict audit could not be persisted"
            ) from error
        raise EvidenceRunConflict("Evidence run identity conflicts with immutable content")

    def _resolve_candidates(self, passport: EvidencePassport) -> list[tuple[object, str]]:
        assessments = GovernanceControlAssessment.__table__
        assignments = GovernanceFrameworkAssignment.__table__
        versions = GovernanceFrameworkVersion.__table__
        controls = GovernanceControlDefinition.__table__
        resolved: list[tuple[object, str]] = []
        for mapping in passport.framework_mappings:
            assessment_id = self.db.execute(
                select(assessments.c.id)
                .join(assignments, assignments.c.id == assessments.c.framework_assignment_id)
                .join(versions, versions.c.id == assignments.c.framework_version_id)
                .join(controls, controls.c.id == assessments.c.control_definition_id)
                .where(
                    assessments.c.id == mapping.control.assessment_id,
                    assessments.c.org_id == passport.organization_id,
                    assessments.c.system_id == passport.ai_system.system_id,
                    assignments.c.org_id == passport.organization_id,
                    assignments.c.system_id == passport.ai_system.system_id,
                    versions.c.framework_key == mapping.framework.key,
                    versions.c.version_label == mapping.framework.version_label,
                    versions.c.source_hash == mapping.framework.source_hash,
                    controls.c.framework_version_id == versions.c.id,
                    controls.c.external_id == mapping.control.external_id,
                )
            ).scalar_one_or_none()
            if assessment_id is None:
                self.db.rollback()
                raise EvidenceMappingReferenceError(
                    f"candidate mapping {mapping.mapping_id} does not resolve in scoped framework assignment"
                )
            if any(
                existing_assessment_id == assessment_id for _, existing_assessment_id in resolved
            ):
                self.db.rollback()
                raise EvidenceMappingReferenceError(
                    "duplicate candidate mappings resolve to the same control assessment"
                )
            resolved.append((mapping, assessment_id))
        return resolved

    def _insert_new(
        self,
        passport: EvidencePassport,
        actor_id: str,
        resolved: list[tuple[object, str]],
    ) -> str:
        now = _now()
        run_pk = str(uuid.uuid4())
        revision_pk = str(uuid.uuid4())
        protocol = passport.model_dump(
            by_alias=True, mode="json", exclude_none=True, exclude_unset=True
        )
        runs = GovernanceEvidenceRun.__table__
        artifacts = GovernanceEvidenceArtifact.__table__
        revisions = GovernanceEvidencePassportRevision.__table__
        evidence_mappings = GovernanceControlEvidence.__table__
        self.db.execute(
            insert(runs).values(
                id=run_pk,
                org_id=passport.organization_id,
                system_id=passport.ai_system.system_id,
                workspace_id=passport.workspace_id,
                passport_id=passport.passport_id,
                schema_version=passport.schema_version,
                capability_state=passport.evaluation.capability_state.value,
                assurance_source=passport.evaluation.assurance_source.value,
                source_type=passport.evaluation.source_type.value,
                source_identifier=passport.evaluation.source_identifier,
                run_id=passport.evaluation.run_id,
                content_hash=passport.evaluation.run_content_hash,
                result=passport.evaluation.result.status.value,
                provenance_json=_json(
                    {
                        "schemaVersion": protocol["schemaVersion"],
                        "aiSystem": protocol["aiSystem"],
                        "evaluation": {
                            key: value
                            for key, value in protocol["evaluation"].items()
                            if key != "runContentHash"
                        },
                        "artifacts": protocol["artifacts"],
                    }
                ),
                artifact_refs_json=_json(protocol["artifacts"]),
                limitations_json=_json(list(passport.evaluation.limitations)),
                captured_at=passport.evaluation.captured_at,
                expires_at=passport.evaluation.expires_at,
                evidence_id=None,
                created_at=now,
            )
        )
        if passport.artifacts:
            self.db.execute(
                insert(artifacts),
                [
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": passport.organization_id,
                        "system_id": passport.ai_system.system_id,
                        "evidence_run_id": run_pk,
                        "artifact_id": artifact.artifact_id,
                        "ordinal": ordinal,
                        "role": artifact.role.value,
                        "uri": artifact.uri,
                        "sha256": artifact.sha256,
                        "media_type": artifact.media_type,
                        "size_bytes": artifact.size_bytes,
                        "contains_sensitive_data": int(artifact.contains_sensitive_data),
                        "retention_policy": artifact.retention_policy,
                        "redaction_note": artifact.redaction_note,
                        "created_at": now,
                    }
                    for ordinal, artifact in enumerate(passport.artifacts)
                ],
            )
        self.db.execute(
            insert(revisions).values(
                id=revision_pk,
                org_id=passport.organization_id,
                system_id=passport.ai_system.system_id,
                evidence_run_id=run_pk,
                passport_id=passport.passport_id,
                passport_revision=1,
                previous_revision_hash=None,
                canonical_content_hash=passport.canonical_content_hash,
                snapshot_json=_json(protocol),
                created_by=actor_id,
                created_at=now,
            )
        )
        if resolved:
            self.db.execute(
                insert(evidence_mappings),
                [
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": passport.organization_id,
                        "system_id": passport.ai_system.system_id,
                        "evidence_id": run_pk,
                        "artifact_evidence_id": None,
                        "passport_revision_id": revision_pk,
                        "source_mapping_id": mapping.mapping_id,
                        "control_assessment_id": assessment_id,
                        "state": "candidate",
                        "relation": mapping.relation.value,
                        "suggested_by_json": _json(
                            mapping.suggested_by.model_dump(
                                by_alias=True, mode="json", exclude_none=True
                            )
                        ),
                        "mapping_rationale": mapping.rationale,
                        "review_history_json": "[]",
                        "review_version": 0,
                        "created_at": now,
                        "updated_at": now,
                    }
                    for mapping, assessment_id in resolved
                ],
            )
        self._insert_audit(
            org_id=passport.organization_id,
            actor_id=actor_id,
            action="evidence_passport.ingested",
            resource_id=run_pk,
            status="success",
            changes={
                "passportId": passport.passport_id,
                "passportRevision": 1,
                "runId": passport.evaluation.run_id,
                "runContentHash": passport.evaluation.run_content_hash,
                "canonicalContentHash": passport.canonical_content_hash,
            },
        )
        return run_pk

    def _insert_audit(
        self,
        *,
        org_id: str,
        actor_id: str,
        action: str,
        resource_id: str,
        status: str,
        changes: dict[str, Any],
    ) -> None:
        self.db.execute(
            insert(OrganizationAuditLog.__table__).values(
                id=uuid.uuid4(),
                org_id=uuid.UUID(org_id),
                user_id=_uuid_or_none(actor_id),
                action=action,
                resource_type="evidence_run",
                resource_id=uuid.UUID(resource_id),
                changes=changes,
                status=status,
            )
        )

    def _mapping(self, mapping_id: str) -> dict[str, Any]:
        mappings = GovernanceControlEvidence.__table__
        row = self.db.execute(select(mappings).where(mappings.c.id == mapping_id)).mappings().one()
        return {
            "id": row["id"],
            "evidenceId": row["artifact_evidence_id"],
            "controlAssessmentId": row["control_assessment_id"],
            "sourceMappingId": row["source_mapping_id"],
            "state": row["state"],
            "relation": row["relation"],
            "rationale": row["mapping_rationale"],
            "reviewVersion": row["review_version"],
            "reviewHistory": json.loads(row["review_history_json"] or "[]"),
        }

    def _result(self, run_id: str, disposition: IngestionDisposition | None) -> IngestionResult:
        runs = GovernanceEvidenceRun.__table__
        revisions = GovernanceEvidencePassportRevision.__table__
        evidence_artifacts = GovernanceEvidenceArtifact.__table__
        evidence_mappings = GovernanceControlEvidence.__table__
        run = self.db.execute(select(runs).where(runs.c.id == run_id)).mappings().one()
        provenance = json.loads(run["provenance_json"] or "{}")
        evaluation = provenance.get("evaluation", {})
        suite = evaluation.get("suite", {})
        subject = evaluation.get("subject", {})
        evaluator = evaluation.get("evaluator", {})
        latest = (
            self.db.execute(
                select(revisions)
                .where(revisions.c.evidence_run_id == run_id)
                .order_by(revisions.c.passport_revision.desc())
            )
            .mappings()
            .first()
        )
        if latest is None:
            raise RuntimeError("evidence run has no passport revision")
        artifacts = (
            self.db.execute(
                select(evidence_artifacts)
                .where(evidence_artifacts.c.evidence_run_id == run_id)
                .order_by(evidence_artifacts.c.ordinal)
            )
            .mappings()
            .all()
        )
        mappings = (
            self.db.execute(
                select(evidence_mappings.c.id).where(evidence_mappings.c.evidence_id == run_id)
            )
            .scalars()
            .all()
        )
        return IngestionResult(
            disposition=disposition,
            id=run["id"],
            evidence_id=run["evidence_id"],
            run_id=run["run_id"],
            run_content_hash=run["content_hash"],
            passport_id=run["passport_id"],
            latest_revision=latest["passport_revision"],
            latest_canonical_content_hash=latest["canonical_content_hash"],
            result=run["result"],
            capability_state=run["capability_state"],
            limitations=tuple(json.loads(run["limitations_json"] or "[]")),
            artifacts=tuple(
                {
                    "artifactId": artifact["artifact_id"],
                    "ordinal": artifact["ordinal"],
                    "role": artifact["role"],
                    "uri": artifact["uri"],
                    "sha256": artifact["sha256"],
                    "mediaType": artifact["media_type"],
                    "sizeBytes": artifact["size_bytes"],
                    "containsSensitiveData": bool(artifact["contains_sensitive_data"]),
                    "retentionPolicy": artifact["retention_policy"],
                    "redactionNote": artifact["redaction_note"],
                }
                for artifact in artifacts
            ),
            candidate_mappings=tuple(self._mapping(mapping_id) for mapping_id in mappings),
            source_type=run["source_type"],
            source_identifier=run["source_identifier"],
            captured_at=run["captured_at"],
            suite_name=suite.get("name"),
            suite_version=suite.get("version"),
            subject_version=subject.get("version"),
            runner_version=evaluator.get("runnerVersion"),
            assurance_source=run["assurance_source"],
        )

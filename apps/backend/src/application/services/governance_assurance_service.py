"""Organization-scoped framework assignment operations."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from database.models import OrganizationMember, OrganizationRole


MUTATION_PERMISSION = "model:write"
_CONTROL_STATUSES = {"not_started", "partial", "ready_for_review", "accepted", "rejected"}
_APPLICABILITY = {"applicable", "not_applicable", "pending"}
_MAPPING_STATES = {"candidate", "accepted", "rejected"}
_ASSURANCE_SOURCES = {"fairmind_internal", "company_integration", "manual", "third_party"}
_SENSITIVE_OUTPUT_KEYS = {"rawoutput", "rawoutputs", "prompt", "prompts", "completion", "completions", "reasoning", "chainofthought"}
MAX_SUMMARY_BYTES = 64 * 1024
MAX_ARTIFACT_REFERENCES_BYTES = 64 * 1024
# Deliberately empty until a deployment declares stable evaluation tags.  This
# avoids inferring controls from free-form result text.
EVALUATION_TAG_CONTROL_IDS: dict[str, tuple[str, ...]] = {}


class EvidenceRunConflictError(ValueError):
    """Raised when an immutable source-run identity changes content."""


class EvidenceMappingConflictError(ValueError):
    """Raised when a reviewer submits a stale mapping version."""


@dataclass(frozen=True)
class OrgMembership:
    org_id: str
    user_id: str
    role: str
    permissions: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _reject_raw_outputs(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized_key in _SENSITIVE_OUTPUT_KEYS:
                raise ValueError("Raw outputs and reasoning traces are not accepted")
            _reject_raw_outputs(child)
    elif isinstance(value, list):
        for child in value:
            _reject_raw_outputs(child)


class GovernanceAssuranceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def membership(self, org_id: str, user_id: str) -> OrgMembership | None:
        org_uuid, user_uuid = _uuid(org_id), _uuid(user_id)
        if not org_uuid or not user_uuid:
            return None
        member = self.db.execute(
            select(OrganizationMember.__table__.c.role).where(
                OrganizationMember.__table__.c.org_id == org_uuid,
                OrganizationMember.__table__.c.user_id == user_uuid,
                OrganizationMember.__table__.c.status == "active",
            )
        ).scalar_one_or_none()
        if not member:
            return None
        permissions = self.db.execute(
            select(OrganizationRole.__table__.c.permissions).where(
                OrganizationRole.__table__.c.org_id == org_uuid,
                OrganizationRole.__table__.c.name == member,
            )
        ).scalar_one_or_none()
        return OrgMembership(org_id, user_id, member, tuple(permissions or ()))

    @staticmethod
    def may_mutate(membership: OrgMembership) -> bool:
        return membership.role in {"owner", "admin"} or MUTATION_PERMISSION in membership.permissions

    @staticmethod
    def may_import(membership: OrgMembership) -> bool:
        return membership.role in {"owner", "admin"}

    def list_frameworks(self) -> list[dict]:
        versions = GovernanceFrameworkVersion.__table__
        rows = self.db.execute(
            select(versions.c.framework_key, versions.c.name)
            .distinct()
            .order_by(versions.c.framework_key)
        ).mappings()
        return [dict(row) for row in rows]

    def list_versions(self, framework_key: str) -> list[dict]:
        versions = GovernanceFrameworkVersion.__table__
        rows = self.db.execute(
            select(
                versions.c.id,
                versions.c.framework_key,
                versions.c.name,
                versions.c.version_label,
                versions.c.source_hash,
                versions.c.status,
            )
            .where(versions.c.framework_key == framework_key)
            .order_by(versions.c.imported_at.desc())
        ).mappings()
        return [dict(row) for row in rows]

    def list_controls(self, version_id: str) -> list[dict] | None:
        versions, controls = GovernanceFrameworkVersion.__table__, GovernanceControlDefinition.__table__
        if not self.db.execute(select(versions.c.id).where(versions.c.id == version_id)).scalar_one_or_none():
            return None
        rows = self.db.execute(
            select(
                controls.c.id,
                controls.c.external_id,
                controls.c.title,
                controls.c.statement,
                controls.c.parent_requirement_id,
                controls.c.active,
            )
            .where(controls.c.framework_version_id == version_id)
            .order_by(controls.c.external_id)
        ).mappings()
        return [dict(row) for row in rows]

    def create_workspace(self, org_id: str, name: str, owner: str | None = None) -> dict:
        workspace_id, now = str(uuid.uuid4()), _now()
        self.db.execute(
            insert(GovernanceWorkspace.__table__).values(
                id=workspace_id, org_id=org_id, name=name, owner=owner, created_at=now, updated_at=now
            )
        )
        self.db.commit()
        return {"id": workspace_id, "orgId": org_id, "name": name, "owner": owner}

    def create_system(self, org_id: str, workspace_id: str, name: str, owner: str | None = None) -> dict | None:
        workspace = self.db.execute(
            select(GovernanceWorkspace.__table__.c.id).where(
                GovernanceWorkspace.__table__.c.id == workspace_id,
                GovernanceWorkspace.__table__.c.org_id == org_id,
            )
        ).scalar_one_or_none()
        if not workspace:
            return None
        system_id, now = str(uuid.uuid4()), _now()
        self.db.execute(
            insert(GovernanceAISystem.__table__).values(
                id=system_id,
                workspace_id=workspace_id,
                org_id=org_id,
                name=name,
                owner=owner,
                created_at=now,
                updated_at=now,
            )
        )
        self.db.commit()
        return {"id": system_id, "workspaceId": workspace_id, "orgId": org_id, "name": name, "owner": owner}

    def assign_framework(self, org_id: str, system_id: str, version_id: str) -> tuple[dict | None, bool]:
        systems, versions, assignments, controls, assessments = (
            GovernanceAISystem.__table__,
            GovernanceFrameworkVersion.__table__,
            GovernanceFrameworkAssignment.__table__,
            GovernanceControlDefinition.__table__,
            GovernanceControlAssessment.__table__,
        )
        if not self.db.execute(
            select(systems.c.id).where(systems.c.id == system_id, systems.c.org_id == org_id)
        ).scalar_one_or_none():
            return None, False
        if not self.db.execute(select(versions.c.id).where(versions.c.id == version_id)).scalar_one_or_none():
            return None, False
        existing = self.db.execute(
            select(assignments.c.id).where(
                assignments.c.org_id == org_id,
                assignments.c.system_id == system_id,
                assignments.c.framework_version_id == version_id,
            )
        ).scalar_one_or_none()
        if existing:
            return self._assignment(existing), False
        assignment_id, now = str(uuid.uuid4()), _now()
        try:
            self.db.execute(
                insert(assignments).values(
                    id=assignment_id,
                    org_id=org_id,
                    system_id=system_id,
                    framework_version_id=version_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            active_controls = self.db.execute(
                select(controls.c.id).where(
                    controls.c.framework_version_id == version_id, controls.c.active == 1
                )
            ).scalars()
            assessment_values = [
                {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "system_id": system_id,
                    "framework_assignment_id": assignment_id,
                    "control_definition_id": control_id,
                    "created_at": now,
                    "updated_at": now,
                }
                for control_id in active_controls
            ]
            if assessment_values:
                self.db.execute(insert(assessments), assessment_values)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self.db.execute(
                select(assignments.c.id).where(
                    assignments.c.org_id == org_id,
                    assignments.c.system_id == system_id,
                    assignments.c.framework_version_id == version_id,
                )
            ).scalar_one_or_none()
            return (self._assignment(existing), False) if existing else (None, False)
        except Exception:
            self.db.rollback()
            raise
        return self._assignment(assignment_id), True

    def _assignment(self, assignment_id: str) -> dict:
        assignments = GovernanceFrameworkAssignment.__table__
        row = self.db.execute(select(assignments).where(assignments.c.id == assignment_id)).mappings().one()
        return {
            "id": row["id"],
            "orgId": row["org_id"],
            "systemId": row["system_id"],
            "frameworkVersionId": row["framework_version_id"],
        }

    def list_assignments(self, org_id: str, system_id: str) -> list[dict] | None:
        systems, assignments = GovernanceAISystem.__table__, GovernanceFrameworkAssignment.__table__
        if not self.db.execute(
            select(systems.c.id).where(systems.c.id == system_id, systems.c.org_id == org_id)
        ).scalar_one_or_none():
            return None
        ids = self.db.execute(
            select(assignments.c.id).where(assignments.c.org_id == org_id, assignments.c.system_id == system_id)
        ).scalars()
        return [self._assignment(item) for item in ids]

    def assignment_controls(self, org_id: str, assignment_id: str) -> list[dict] | None:
        assignments, assessments, controls, mappings, runs, evidence = (
            GovernanceFrameworkAssignment.__table__,
            GovernanceControlAssessment.__table__,
            GovernanceControlDefinition.__table__,
            GovernanceControlEvidence.__table__,
            GovernanceEvidenceRun.__table__,
            GovernanceEvidence.__table__,
        )
        if not self.db.execute(
            select(assignments.c.id).where(assignments.c.id == assignment_id, assignments.c.org_id == org_id)
        ).scalar_one_or_none():
            return None
        rows = self.db.execute(
            select(
                assessments.c.id,
                assessments.c.applicability,
                assessments.c.status,
                assessments.c.owner,
                controls.c.external_id,
                controls.c.title,
                controls.c.statement,
                controls.c.obligation,
                controls.c.application,
                controls.c.parent_requirement_id,
                controls.c.parent_requirement_title,
                controls.c.frequency,
            )
            .join(controls, controls.c.id == assessments.c.control_definition_id)
            .where(assessments.c.framework_assignment_id == assignment_id, assessments.c.org_id == org_id)
            .order_by(controls.c.external_id)
        ).mappings().all()

        assessment_ids = [row["id"] for row in rows]
        evidence_by_assessment: dict[str, list[dict]] = {}
        if assessment_ids:
            evidence_rows = self.db.execute(
                select(
                    mappings.c.id,
                    mappings.c.control_assessment_id,
                    mappings.c.state,
                    mappings.c.mapping_rationale,
                    mappings.c.reviewed_at,
                    mappings.c.created_at.label("mapping_created_at"),
                    mappings.c.updated_at.label("mapping_updated_at"),
                    runs.c.source_type,
                    runs.c.source_identifier,
                    runs.c.captured_at.label("run_captured_at"),
                    runs.c.created_at.label("run_created_at"),
                    evidence.c.title.label("artifact_title"),
                    evidence.c.captured_at.label("artifact_captured_at"),
                )
                .select_from(
                    mappings.join(runs, runs.c.id == mappings.c.evidence_id).outerjoin(
                        evidence, evidence.c.id == mappings.c.artifact_evidence_id
                    )
                )
                .where(
                    mappings.c.org_id == org_id,
                    mappings.c.control_assessment_id.in_(assessment_ids),
                )
            ).mappings().all()
            for evidence_row in evidence_rows:
                evidence_by_assessment.setdefault(evidence_row["control_assessment_id"], []).append(
                    dict(evidence_row)
                )

        result = []
        for row in rows:
            linked_evidence = evidence_by_assessment.get(row["id"], [])
            linked_evidence.sort(
                key=lambda item: str(
                    item["artifact_captured_at"]
                    or item["run_captured_at"]
                    or item["run_created_at"]
                    or item["mapping_updated_at"]
                    or item["mapping_created_at"]
                    or ""
                ),
                reverse=True,
            )
            accepted = [item for item in linked_evidence if item["state"] == "accepted"]
            latest = linked_evidence[0] if linked_evidence else None
            latest_accepted = accepted[0] if accepted else None

            def captured_at(item: dict | None) -> str | None:
                if not item:
                    return None
                return item["artifact_captured_at"] or item["run_captured_at"] or item["run_created_at"]

            latest_accepted_at = captured_at(latest_accepted)
            freshness = "missing" if not accepted else (
                "stale" if _is_stale(latest_accepted_at or "", row["frequency"]) else "current"
            )
            rationale = next(
                (item["mapping_rationale"] for item in linked_evidence if item["mapping_rationale"]),
                None,
            )
            result.append(
                {
                    "id": row["id"],
                    "externalId": row["external_id"],
                    "title": row["title"],
                    "statement": row["statement"],
                    "obligation": row["obligation"].lower() if row["obligation"] else None,
                    "application": row["application"].lower() if row["application"] else None,
                    "parentRequirementId": row["parent_requirement_id"] or None,
                    "parentRequirementTitle": row["parent_requirement_title"] or None,
                    "applicability": row["applicability"],
                    "status": row["status"],
                    "owner": row["owner"],
                    "acceptedEvidenceCount": len(accepted),
                    "latestEvaluation": (
                        latest["artifact_title"] or latest["source_identifier"]
                    ) if latest else None,
                    "latestEvaluationSource": latest["source_identifier"] if latest else None,
                    "latestEvaluationAt": captured_at(latest),
                    "freshness": freshness,
                    # Findings are not linked to control assessments in the current schema.
                    "openFindings": None,
                    "mappingRationale": rationale,
                    "evidenceTrace": [
                        {
                            "id": item["id"],
                            "label": item["artifact_title"] or item["source_identifier"],
                            "kind": item["source_type"],
                            "source": item["source_identifier"],
                            "state": item["state"],
                            "capturedAt": captured_at(item),
                        }
                        for item in linked_evidence
                    ],
                }
            )
        return result

    def update_assessment(self, org_id: str, assessment_id: str, values: dict[str, str | None]) -> dict | None:
        assessments = GovernanceControlAssessment.__table__
        row = self.db.execute(
            select(assessments).where(assessments.c.id == assessment_id, assessments.c.org_id == org_id)
        ).mappings().one_or_none()
        if not row:
            return None
        updates = {key: values[key] for key in ("status", "applicability") if values.get(key) is not None}
        if "owner" in values:
            updates["owner"] = values["owner"]
        if not updates:
            return dict(row)
        if "status" in updates and updates["status"] not in _CONTROL_STATUSES:
            raise ValueError("Unsupported control assessment status")
        if "applicability" in updates and updates["applicability"] not in _APPLICABILITY:
            raise ValueError("Unsupported applicability")
        updates["updated_at"] = _now()
        self.db.execute(update(assessments).where(assessments.c.id == assessment_id).values(**updates))
        self.db.commit()
        return dict(self.db.execute(select(assessments).where(assessments.c.id == assessment_id)).mappings().one())

    def ingest_evidence_run(self, org_id: str, system_id: str, envelope: dict, actor_id: str) -> tuple[dict | None, bool]:
        systems, runs, evidence, mappings = (
            GovernanceAISystem.__table__,
            GovernanceEvidenceRun.__table__,
            GovernanceEvidence.__table__,
            GovernanceControlEvidence.__table__,
        )
        if not self.db.execute(
            select(systems.c.id).where(systems.c.id == system_id, systems.c.org_id == org_id)
        ).scalar_one_or_none():
            return None, False
        _reject_raw_outputs(envelope)
        summary_json = _canonical_json(envelope.get("summary", {}))
        if len(summary_json.encode("utf-8")) > MAX_SUMMARY_BYTES:
            raise ValueError("Evidence summary exceeds the size limit")
        artifact_refs_json = _canonical_json(envelope.get("artifact_references", []))
        if len(artifact_refs_json.encode("utf-8")) > MAX_ARTIFACT_REFERENCES_BYTES:
            raise ValueError("Artifact references exceed the size limit")
        if envelope.get("assurance_source") not in _ASSURANCE_SOURCES:
            raise ValueError("Unsupported assurance source")
        if envelope.get("assurance_source") == "third_party":
            assessor = envelope.get("third_party_assessor") or {}
            if not assessor.get("identity") or assessor.get("independence_assertion") is not True:
                raise ValueError("Third-party evidence requires assessor identity and independence")
        canonical = _canonical_json(envelope)
        content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        key = (
            org_id,
            envelope["source_type"],
            envelope["source_identifier"],
            envelope["run_id"],
            content_hash,
        )
        source_run = self.db.execute(
            select(runs.c.id, runs.c.content_hash).where(
                runs.c.org_id == key[0], runs.c.source_type == key[1],
                runs.c.system_id == system_id, runs.c.source_identifier == key[2], runs.c.run_id == key[3],
            )
        ).mappings().one_or_none()
        if source_run and source_run["content_hash"] != content_hash:
            raise EvidenceRunConflictError("Evidence run content is immutable")
        if source_run:
            return self._evidence_run(source_run["id"]), False
        now, run_id, evidence_id = _now(), str(uuid.uuid4()), str(uuid.uuid4())
        try:
            self.db.execute(
                insert(runs).values(
                    id=run_id, org_id=org_id, system_id=system_id,
                    source_type=envelope["source_type"], source_identifier=envelope["source_identifier"],
                    run_id=envelope["run_id"], content_hash=content_hash, result=envelope.get("result", "unknown"),
                    provenance_json=canonical, artifact_refs_json=artifact_refs_json,
                    limitations_json=_canonical_json(envelope.get("limitations", [])),
                    captured_at=envelope.get("captured_at"), expires_at=envelope.get("expires_at"),
                    evidence_id=evidence_id, created_at=now,
                )
            )
            self.db.execute(
                insert(evidence).values(
                    id=evidence_id, org_id=org_id, system_id=system_id, source_run_id=run_id,
                    evidence_type="evaluation_run", title=f"{envelope['source_identifier']} {envelope['run_id']}",
                    source=envelope["source_type"], content_json=summary_json,
                    status=envelope.get("result", "unknown"), uploaded_by=actor_id,
                    metadata_json=_canonical_json({"contentHash": content_hash, "artifactReferences": envelope.get("artifact_references", [])}),
                    captured_at=envelope.get("captured_at"), created_at=now,
                )
            )
            control_ids = set(envelope.get("control_external_ids", []))
            for tag in envelope.get("evaluation_tags", []):
                control_ids.update(EVALUATION_TAG_CONTROL_IDS.get(tag, ()))
            if control_ids:
                assessments, controls = GovernanceControlAssessment.__table__, GovernanceControlDefinition.__table__
                candidates = list(self.db.execute(
                    select(assessments.c.id).join(controls, controls.c.id == assessments.c.control_definition_id).where(
                        assessments.c.org_id == org_id, assessments.c.system_id == system_id,
                        controls.c.external_id.in_(control_ids),
                    )
                ).scalars())
                mapping_values = [
                    {
                        "id": str(uuid.uuid4()), "org_id": org_id, "system_id": system_id,
                        "evidence_id": run_id, "artifact_evidence_id": evidence_id,
                        "control_assessment_id": assessment_id, "state": "candidate",
                        "mapping_rationale": "Explicit evaluation control identifier.",
                        "created_at": now, "updated_at": now,
                    }
                    for assessment_id in candidates
                ]
                if mapping_values:
                    self.db.execute(insert(mappings), mapping_values)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            source_run = self.db.execute(
                select(runs.c.id, runs.c.content_hash).where(
                    runs.c.org_id == key[0], runs.c.source_type == key[1],
                    runs.c.system_id == system_id, runs.c.source_identifier == key[2], runs.c.run_id == key[3],
                )
            ).mappings().one_or_none()
            if source_run:
                if source_run["content_hash"] == content_hash:
                    return self._evidence_run(source_run["id"]), False
                raise EvidenceRunConflictError("Evidence run content is immutable")
            raise
        return self._evidence_run(run_id), True

    def list_evidence_runs(self, org_id: str, system_id: str) -> list[dict] | None:
        systems, runs = GovernanceAISystem.__table__, GovernanceEvidenceRun.__table__
        if not self.db.execute(select(systems.c.id).where(systems.c.id == system_id, systems.c.org_id == org_id)).scalar_one_or_none():
            return None
        return [self._evidence_run(run_id) for run_id in self.db.execute(
            select(runs.c.id).where(runs.c.org_id == org_id, runs.c.system_id == system_id).order_by(runs.c.created_at.desc())
        ).scalars()]

    def create_evidence_mapping(self, org_id: str, evidence_id: str, assessment_id: str, rationale: str | None) -> tuple[dict | None, bool]:
        evidence, runs, assessments, mappings = (
            GovernanceEvidence.__table__, GovernanceEvidenceRun.__table__, GovernanceControlAssessment.__table__, GovernanceControlEvidence.__table__)
        artifact = self.db.execute(select(evidence).where(evidence.c.id == evidence_id, evidence.c.org_id == org_id)).mappings().one_or_none()
        assessment = self.db.execute(select(assessments).where(assessments.c.id == assessment_id, assessments.c.org_id == org_id)).mappings().one_or_none()
        if not artifact or not assessment or artifact["system_id"] != assessment["system_id"] or not artifact["source_run_id"]:
            return None, False
        run = self.db.execute(select(runs.c.id).where(runs.c.id == artifact["source_run_id"], runs.c.org_id == org_id)).scalar_one_or_none()
        if not run:
            return None, False
        existing = self.db.execute(select(mappings.c.id).where(mappings.c.evidence_id == run, mappings.c.control_assessment_id == assessment_id)).scalar_one_or_none()
        if existing:
            return self._mapping(existing), False
        mapping_id, now = str(uuid.uuid4()), _now()
        self.db.execute(insert(mappings).values(id=mapping_id, org_id=org_id, system_id=artifact["system_id"], evidence_id=run, artifact_evidence_id=evidence_id, control_assessment_id=assessment_id, state="candidate", mapping_rationale=rationale, created_at=now, updated_at=now))
        self.db.commit()
        return self._mapping(mapping_id), True

    def review_evidence_mapping(self, org_id: str, mapping_id: str, state: str, actor_id: str, rationale: str | None, review_version: int) -> dict | None:
        from src.application.ports.evidence_ingestion import EvidenceRevisionConflict
        from src.application.services.evidence_ingestion_service import review_evidence_mapping_revision

        try:
            return review_evidence_mapping_revision(
                self.db,
                org_id=org_id,
                mapping_id=mapping_id,
                state=state,
                actor_id=actor_id,
                rationale=rationale,
                review_version=review_version,
            )
        except EvidenceRevisionConflict as error:
            raise EvidenceMappingConflictError(str(error)) from error

    def _evidence_run(self, run_id: str) -> dict:
        runs, mappings = GovernanceEvidenceRun.__table__, GovernanceControlEvidence.__table__
        row = self.db.execute(select(runs).where(runs.c.id == run_id)).mappings().one()
        provenance = json.loads(row["provenance_json"] or "{}")
        limitations = json.loads(row["limitations_json"] or "[]")
        return {
            "id": row["id"], "runId": row["run_id"], "evidenceId": row["evidence_id"],
            "contentHash": row["content_hash"], "result": row["result"], "sourceType": row["source_type"],
            "sourceIdentifier": row["source_identifier"], "capturedAt": row["captured_at"],
            "suiteName": provenance.get("suite_name"), "suiteVersion": provenance.get("suite_version"),
            "subjectVersion": provenance.get("subject_version"), "runnerVersion": provenance.get("runner_version"),
            "assuranceSource": provenance.get("assurance_source"), "limitations": limitations,
            "candidateMappings": [self._mapping(mapping_id) for mapping_id in self.db.execute(select(mappings.c.id).where(mappings.c.evidence_id == run_id)).scalars()],
        }

    def _mapping(self, mapping_id: str) -> dict:
        row = self.db.execute(select(GovernanceControlEvidence.__table__).where(GovernanceControlEvidence.__table__.c.id == mapping_id)).mappings().one()
        return {
            "id": row["id"], "evidenceId": row["artifact_evidence_id"], "controlAssessmentId": row["control_assessment_id"],
            "state": row["state"], "rationale": row["mapping_rationale"],
            "reviewVersion": row["review_version"],
            "reviewHistory": json.loads(row["review_history_json"] or "[]"),
        }

    def readiness(self, org_id: str, assignment_id: str) -> dict | None:
        assignments, assessments = GovernanceFrameworkAssignment.__table__, GovernanceControlAssessment.__table__
        if not self.db.execute(
            select(assignments.c.id).where(assignments.c.id == assignment_id, assignments.c.org_id == org_id)
        ).scalar_one_or_none():
            return None
        controls, mappings, evidence_runs = (
            GovernanceControlDefinition.__table__,
            GovernanceControlEvidence.__table__,
            GovernanceEvidenceRun.__table__,
        )
        rows = self.db.execute(
            select(
                assessments.c.id,
                assessments.c.applicability,
                assessments.c.status,
                controls.c.frequency,
            )
            .join(controls, controls.c.id == assessments.c.control_definition_id)
            .where(
                assessments.c.framework_assignment_id == assignment_id, assessments.c.org_id == org_id
            )
        ).mappings()
        evidence_by_assessment: dict[str, list[str]] = {}
        for row in self.db.execute(
            select(mappings.c.control_assessment_id, evidence_runs.c.captured_at, evidence_runs.c.created_at)
            .join(evidence_runs, evidence_runs.c.id == mappings.c.evidence_id)
            .where(
                mappings.c.org_id == org_id,
                mappings.c.state == "accepted",
                evidence_runs.c.result == "passed",
            )
        ).mappings():
            evidence_by_assessment.setdefault(row["control_assessment_id"], []).append(row["captured_at"] or row["created_at"])
        counts = {
            "applicable": 0,
            "accepted": 0,
            "readyForReview": 0,
            "partial": 0,
            "notStarted": 0,
            "notApplicable": 0,
            "blockingFindings": 0,
            "missingEvidence": 0,
            "staleEvidence": 0,
        }
        for row in rows:
            if row["applicability"] == "not_applicable":
                counts["notApplicable"] += 1
                continue
            if row["applicability"] != "applicable":
                continue
            counts["applicable"] += 1
            status = row["status"]
            if status == "accepted":
                counts["accepted"] += 1
            elif status == "ready_for_review":
                counts["readyForReview"] += 1
            elif status == "partial":
                counts["partial"] += 1
            elif status == "not_started":
                counts["notStarted"] += 1
            elif status == "rejected":
                counts["blockingFindings"] += 1
            evidence_times = evidence_by_assessment.get(row["id"], [])
            if not evidence_times:
                counts["missingEvidence"] += 1
            elif all(_is_stale(timestamp, row["frequency"]) for timestamp in evidence_times):
                counts["staleEvidence"] += 1
        return counts


def _is_stale(created_at: str, frequency: str) -> bool:
    try:
        captured = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=timezone.utc)
    frequency_days = {
        "weekly": 8,
        "monthly": 31,
        "quarterly": 92,
        "annual": 366,
    }
    normalized = (frequency or "").lower()
    interval = re.search(r"every\s+(\d+)\s+months?", normalized)
    if interval:
        months = int(interval.group(1))
        threshold = {3: 92, 6: 183, 12: 366}.get(months, months * 31)
    else:
        threshold = next((days for label, days in frequency_days.items() if label in normalized), 366)
    return datetime.now(timezone.utc) - captured.astimezone(timezone.utc) > timedelta(days=threshold)

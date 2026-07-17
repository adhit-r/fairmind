"""Organization-scoped framework assignment operations."""

from __future__ import annotations

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
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)
from database.models import OrganizationMember, OrganizationRole


MUTATION_PERMISSION = "model:write"
_CONTROL_STATUSES = {"not_started", "partial", "ready_for_review", "accepted", "rejected"}
_APPLICABILITY = {"applicable", "not_applicable", "pending"}


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
        assignments, assessments, controls = (
            GovernanceFrameworkAssignment.__table__,
            GovernanceControlAssessment.__table__,
            GovernanceControlDefinition.__table__,
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
            )
            .join(controls, controls.c.id == assessments.c.control_definition_id)
            .where(assessments.c.framework_assignment_id == assignment_id, assessments.c.org_id == org_id)
            .order_by(controls.c.external_id)
        ).mappings()
        return [
            {
                "id": row["id"],
                "externalId": row["external_id"],
                "title": row["title"],
                "statement": row["statement"],
                "applicability": row["applicability"],
                "status": row["status"],
                "owner": row["owner"],
            }
            for row in rows
        ]

    def update_assessment(self, org_id: str, assessment_id: str, values: dict[str, str | None]) -> dict | None:
        assessments = GovernanceControlAssessment.__table__
        row = self.db.execute(
            select(assessments).where(assessments.c.id == assessment_id, assessments.c.org_id == org_id)
        ).mappings().one_or_none()
        if not row:
            return None
        updates = {key: value for key, value in values.items() if value is not None}
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
            select(mappings.c.control_assessment_id, evidence_runs.c.created_at)
            .join(evidence_runs, evidence_runs.c.id == mappings.c.evidence_id)
            .where(
                mappings.c.org_id == org_id,
                mappings.c.state == "accepted",
            )
        ).mappings():
            evidence_by_assessment.setdefault(row["control_assessment_id"], []).append(row["created_at"])
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
    threshold = next((days for label, days in frequency_days.items() if label in (frequency or "").lower()), 366)
    return datetime.now(timezone.utc) - captured.astimezone(timezone.utc) > timedelta(days=threshold)

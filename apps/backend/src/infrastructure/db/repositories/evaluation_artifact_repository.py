"""PostgreSQL persistence for evaluation input artifacts (013m table, 013n guards)."""

from __future__ import annotations

import uuid
from typing import Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.ports.evaluation_artifacts import (
    ArtifactRecord,
    artifact_storage_key,
)
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    EvaluationAuditAppend,
    append_evaluation_audit_event,
)


_COLUMNS = (
    "id, org_id, sha256, media_type, size_bytes, state, scan_policy, "
    "created_at, available_at, rejected_at, rejection_reason"
)


def _record(row) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=row["id"],
        organization_id=row["org_id"],
        sha256=row["sha256"],
        media_type=row["media_type"],
        size_bytes=int(row["size_bytes"]),
        state=row["state"],
        scan_policy=row["scan_policy"],
        created_at=row["created_at"],
        available_at=row["available_at"],
        rejected_at=row["rejected_at"],
        rejection_reason=row["rejection_reason"],
    )


class SqlAlchemyEvaluationArtifactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _one(self, sql: str, params: Mapping[str, object]) -> ArtifactRecord | None:
        row = self._session.execute(text(sql), params).mappings().one_or_none()
        return None if row is None else _record(row)

    def find(self, *, organization_id: str, sha256: str) -> ArtifactRecord | None:
        return self._one(
            f"SELECT {_COLUMNS} FROM governance_evaluation_artifacts "
            "WHERE org_id = :org_id AND sha256 = :sha256",
            {"org_id": organization_id, "sha256": sha256},
        )

    def find_by_id(self, *, organization_id: str, artifact_id: str) -> ArtifactRecord | None:
        return self._one(
            f"SELECT {_COLUMNS} FROM governance_evaluation_artifacts "
            "WHERE org_id = :org_id AND id = :id",
            {"org_id": organization_id, "id": artifact_id},
        )

    def insert_quarantined(
        self,
        *,
        organization_id: str,
        sha256: str,
        media_type: str,
        size_bytes: int,
        scan_policy: str,
    ) -> ArtifactRecord | None:
        return self._one(
            "INSERT INTO governance_evaluation_artifacts "
            "(id, org_id, sha256, media_type, size_bytes, storage_key, state, "
            "scan_policy, created_at) VALUES (:id, :org_id, :sha256, :media_type, "
            ":size_bytes, :storage_key, 'quarantined', :scan_policy, "
            "fairmind_canonical_clock_utc_013f()) "
            f"ON CONFLICT DO NOTHING RETURNING {_COLUMNS}",
            {
                "id": str(uuid.uuid4()),
                "org_id": organization_id,
                "sha256": sha256,
                "media_type": media_type,
                "size_bytes": size_bytes,
                "storage_key": artifact_storage_key(sha256),
                "scan_policy": scan_policy,
            },
        )

    def lock_quarantined(self, *, organization_id: str, artifact_id: str) -> ArtifactRecord | None:
        return self._one(
            f"SELECT {_COLUMNS} FROM governance_evaluation_artifacts "
            "WHERE org_id = :org_id AND id = :id AND state = 'quarantined' FOR UPDATE",
            {"org_id": organization_id, "id": artifact_id},
        )

    def mark_available(self, *, organization_id: str, artifact_id: str) -> ArtifactRecord:
        record = self._one(
            "UPDATE governance_evaluation_artifacts SET state = 'available', "
            "available_at = fairmind_canonical_clock_utc_013f() "
            "WHERE org_id = :org_id AND id = :id AND state = 'quarantined' "
            f"RETURNING {_COLUMNS}",
            {"org_id": organization_id, "id": artifact_id},
        )
        if record is None:
            raise RuntimeError("locked quarantined artifact disappeared")
        return record

    def mark_rejected(self, *, organization_id: str, artifact_id: str, reason: str) -> ArtifactRecord:
        record = self._one(
            "UPDATE governance_evaluation_artifacts SET state = 'rejected', "
            "rejected_at = fairmind_canonical_clock_utc_013f(), rejection_reason = :reason "
            "WHERE org_id = :org_id AND id = :id AND state = 'quarantined' "
            f"RETURNING {_COLUMNS}",
            {"org_id": organization_id, "id": artifact_id, "reason": reason},
        )
        if record is None:
            raise RuntimeError("locked quarantined artifact disappeared")
        return record

    def audit(
        self,
        *,
        organization_id: str,
        actor_id: str,
        action: str,
        outcome: str,
        resource_type: str,
        resource_id: str,
        details: Mapping[str, object],
    ) -> None:
        created_at = self._session.execute(
            text("SELECT fairmind_canonical_clock_utc_013f()")
        ).scalar_one()
        append_evaluation_audit_event(
            self._session,
            event=EvaluationAuditAppend(
                organization_id=organization_id,
                actor_id=actor_id,
                action=action,
                outcome=outcome,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                created_at=created_at,
            ),
        )

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


__all__ = ["SqlAlchemyEvaluationArtifactRepository"]

"""Tenant-scoped immutable trust-policy persistence operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from database.governance_models import GovernanceEvidenceTrustPolicyVersion
from src.application.ports.trust_administration import TrustPolicyVersionRecord
from src.domain.assurance.evaluation_v2 import canonical_json


class TrustPolicyRepositoryOperations:
    def find_policy_by_version(
        self, *, organization_id: str, version: str, lock: bool
    ) -> TrustPolicyVersionRecord | None:
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        statement = select(table).where(
            table.c.org_id == organization_id, table.c.version == version
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._policy_from_row(row)

    def get_policy(
        self, *, organization_id: str, policy_id: str, lock: bool
    ) -> TrustPolicyVersionRecord | None:
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        statement = select(table).where(
            table.c.org_id == organization_id, table.c.id == policy_id
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._policy_from_row(row)

    def list_policies(
        self, *, organization_id: str, limit: int, offset: int
    ) -> list[TrustPolicyVersionRecord]:
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        rows = (
            self.db.execute(
                select(table)
                .where(table.c.org_id == organization_id)
                .order_by(table.c.created_at, table.c.id)
                .limit(limit)
                .offset(offset)
            )
            .mappings()
            .all()
        )
        return [self._policy_from_row(row) for row in rows]

    def insert_policy(
        self, record: TrustPolicyVersionRecord
    ) -> TrustPolicyVersionRecord:
        self._require_postgresql()
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        try:
            self.db.execute(
                insert(table).values(
                    id=record.id,
                    org_id=record.organization_id,
                    version=record.version,
                    policy_json=canonical_json(record.policy.to_dict()),
                    policy_hash=record.policy_hash,
                    maximum_evidence_age_seconds=record.maximum_evidence_age_seconds,
                    unsigned_import_policy=record.unsigned_import_policy,
                    status="draft",
                    created_by=record.created_by,
                    policy_schema_version="1.0.0",
                    supersedes_id=record.supersedes_id,
                    activated_by=None,
                    activated_at=None,
                    retired_by=None,
                    retired_at=None,
                    retirement_reason=None,
                    created_at=self._timestamp(record.created_at),
                )
            )
        except IntegrityError as error:
            raise self._error(
                "trust_policy_exists", "The trust policy version already exists."
            ) from error
        persisted = self.get_policy(
            organization_id=record.organization_id, policy_id=record.id, lock=False
        )
        if persisted is None:
            raise self._error(
                "trust_policy_integrity_conflict",
                "The trust policy could not be read after persistence.",
            )
        return persisted

    def activate_policy(
        self,
        *,
        record: TrustPolicyVersionRecord,
        actor_id: str,
        rationale: str | None,
        now: datetime,
        expected_status: str,
        expected_current_policy_id: str | None,
        expected_current_policy_hash: str | None,
    ) -> tuple[TrustPolicyVersionRecord, TrustPolicyVersionRecord | None] | None:
        self._require_postgresql()
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        predecessor: TrustPolicyVersionRecord | None = None
        if expected_current_policy_id is not None:
            if record.supersedes_id != expected_current_policy_id:
                return None
            predecessor = self.get_policy(
                organization_id=record.organization_id,
                policy_id=expected_current_policy_id,
                lock=True,
            )
            if (
                predecessor is None
                or predecessor.status not in {"active", "retired"}
                or predecessor.activated_at is None
                or predecessor.policy_hash != expected_current_policy_hash
            ):
                return None
            if predecessor.status == "active":
                if rationale is None:
                    return None
                result = self.db.execute(
                    update(table)
                    .where(
                        table.c.id == expected_current_policy_id,
                        table.c.org_id == record.organization_id,
                        table.c.status == "active",
                        table.c.policy_hash == expected_current_policy_hash,
                    )
                    .values(
                        status="retired",
                        retired_by=actor_id,
                        retired_at=self._timestamp(now),
                        retirement_reason=rationale,
                    )
                )
                if result.rowcount != 1:
                    return None
                predecessor = self.get_policy(
                    organization_id=record.organization_id,
                    policy_id=expected_current_policy_id,
                    lock=True,
                )
                if predecessor is None or predecessor.status != "retired":
                    return None
            else:
                if rationale is not None:
                    return None
                later = self.db.execute(
                    select(table.c.id).where(
                        table.c.org_id == record.organization_id,
                        table.c.activated_at.is_not(None),
                        table.c.activated_at > self._timestamp(predecessor.activated_at),
                    )
                ).first()
                if later is not None:
                    return None
        else:
            if record.supersedes_id is not None:
                return None
            active = self.db.execute(
                select(table.c.id).where(
                    table.c.org_id == record.organization_id,
                    table.c.status == "active",
                )
            ).one_or_none()
            activated_history = self.db.execute(
                select(table.c.id).where(
                    table.c.org_id == record.organization_id,
                    table.c.activated_at.is_not(None),
                )
            ).first()
            if active is not None or activated_history is not None:
                return None
        activated_result = self.db.execute(
            update(table)
            .where(
                table.c.id == record.id,
                table.c.org_id == record.organization_id,
                table.c.status == expected_status,
                table.c.supersedes_id.is_(None)
                if expected_current_policy_id is None
                else table.c.supersedes_id == expected_current_policy_id,
            )
            .values(
                status="active",
                activated_by=actor_id,
                activated_at=self._timestamp(now),
            )
        )
        if activated_result.rowcount != 1:
            raise self._error(
                "trust_policy_activation_conflict",
                "The trust policy changed before activation.",
            )
        activated = self.get_policy(
            organization_id=record.organization_id, policy_id=record.id, lock=False
        )
        if activated is None:
            raise self._error(
                "trust_policy_integrity_conflict",
                "The activated policy could not be read after persistence.",
            )
        return activated, predecessor

    def retire_policy(
        self,
        *,
        record: TrustPolicyVersionRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
        expected_status: str,
    ) -> TrustPolicyVersionRecord | None:
        self._require_postgresql()
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        result = self.db.execute(
            update(table)
            .where(
                table.c.id == record.id,
                table.c.org_id == record.organization_id,
                table.c.status == expected_status,
            )
            .values(
                status="retired",
                retired_by=actor_id,
                retired_at=self._timestamp(now),
                retirement_reason=rationale,
            )
        )
        if result.rowcount != 1:
            return None
        return self.get_policy(
            organization_id=record.organization_id, policy_id=record.id, lock=False
        )

"""Tenant-scoped evidence-issuer persistence operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from database.governance_models import GovernanceEvidenceIssuer
from src.application.ports.trust_administration import EvidenceIssuerRecord
from src.domain.assurance.evaluation_v2 import canonical_json


class TrustIssuerRepositoryOperations:
    def find_issuer_by_key(
        self, *, organization_id: str, issuer_key: str, lock: bool
    ) -> EvidenceIssuerRecord | None:
        table = GovernanceEvidenceIssuer.__table__
        statement = select(table).where(
            table.c.org_id == organization_id, table.c.issuer_key == issuer_key
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._issuer_from_row(row)

    def get_issuer(
        self, *, organization_id: str, issuer_id: str, lock: bool
    ) -> EvidenceIssuerRecord | None:
        table = GovernanceEvidenceIssuer.__table__
        statement = select(table).where(
            table.c.org_id == organization_id, table.c.id == issuer_id
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._issuer_from_row(row)

    def list_issuers(
        self, *, organization_id: str, limit: int, offset: int
    ) -> list[EvidenceIssuerRecord]:
        table = GovernanceEvidenceIssuer.__table__
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
        return [self._issuer_from_row(row) for row in rows]

    def insert_issuer(self, record: EvidenceIssuerRecord) -> EvidenceIssuerRecord:
        self._require_postgresql()
        table = GovernanceEvidenceIssuer.__table__
        try:
            self.db.execute(
                insert(table).values(
                    id=record.id,
                    org_id=record.organization_id,
                    issuer_key=record.issuer_key,
                    name=record.name,
                    issuer_type=record.issuer_type,
                    source_restrictions_json=canonical_json(list(record.source_restrictions)),
                    suite_restrictions_json=canonical_json(
                        list(record.suite_version_restrictions)
                    ),
                    target_restrictions_json=canonical_json(
                        list(record.target_version_restrictions)
                    ),
                    status="active",
                    created_by=record.created_by,
                    created_at=self._timestamp(record.created_at),
                    updated_at=self._timestamp(record.updated_at),
                    revoked_by=None,
                    revoked_at=None,
                    revocation_reason=None,
                )
            )
        except IntegrityError as error:
            raise self._error(
                "trust_issuer_exists", "The evidence issuer already exists."
            ) from error
        persisted = self.get_issuer(
            organization_id=record.organization_id, issuer_id=record.id, lock=False
        )
        if persisted is None:
            raise self._error(
                "trust_issuer_integrity_conflict",
                "The evidence issuer could not be read after persistence.",
            )
        return persisted

    def revoke_issuer(
        self,
        *,
        record: EvidenceIssuerRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
        expected_status: str,
    ) -> EvidenceIssuerRecord | None:
        self._require_postgresql()
        table = GovernanceEvidenceIssuer.__table__
        result = self.db.execute(
            update(table)
            .where(
                table.c.id == record.id,
                table.c.org_id == record.organization_id,
                table.c.status == expected_status,
            )
            .values(
                status="revoked",
                revoked_by=actor_id,
                revoked_at=self._timestamp(now),
                revocation_reason=rationale,
                updated_at=self._timestamp(now),
            )
        )
        if result.rowcount != 1:
            return None
        return self.get_issuer(
            organization_id=record.organization_id, issuer_id=record.id, lock=False
        )

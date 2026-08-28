"""Tenant-scoped public signing-key persistence operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from database.governance_models import GovernanceEvidenceSigningKey
from src.application.ports.trust_administration import EvidenceSigningKeyRecord
from src.domain.assurance.evaluation_v2 import canonical_json


class TrustSigningKeyRepositoryOperations:
    def find_signing_key_by_public_identity(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        key_id: str,
        lock: bool,
    ) -> EvidenceSigningKeyRecord | None:
        table = GovernanceEvidenceSigningKey.__table__
        statement = select(table).where(
            table.c.org_id == organization_id,
            table.c.issuer_id == issuer_id,
            table.c.key_id == key_id,
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._key_from_row(row)

    def find_signing_key_by_fingerprint(
        self, *, fingerprint: str, lock: bool
    ) -> EvidenceSigningKeyRecord | None:
        table = GovernanceEvidenceSigningKey.__table__
        statement = select(table).where(table.c.public_key_fingerprint == fingerprint)
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._key_from_row(row)

    def get_signing_key(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        signing_key_id: str,
        lock: bool,
    ) -> EvidenceSigningKeyRecord | None:
        table = GovernanceEvidenceSigningKey.__table__
        statement = select(table).where(
            table.c.org_id == organization_id,
            table.c.issuer_id == issuer_id,
            table.c.id == signing_key_id,
        )
        row = self.db.execute(self._locked(statement, lock)).mappings().one_or_none()
        return None if row is None else self._key_from_row(row)

    def list_signing_keys(
        self, *, organization_id: str, issuer_id: str, limit: int, offset: int
    ) -> list[EvidenceSigningKeyRecord]:
        table = GovernanceEvidenceSigningKey.__table__
        rows = (
            self.db.execute(
                select(table)
                .where(
                    table.c.org_id == organization_id, table.c.issuer_id == issuer_id
                )
                .order_by(table.c.created_at, table.c.id)
                .limit(limit)
                .offset(offset)
            )
            .mappings()
            .all()
        )
        return [self._key_from_row(row) for row in rows]

    def insert_signing_key(
        self, record: EvidenceSigningKeyRecord
    ) -> EvidenceSigningKeyRecord:
        self._require_postgresql()
        table = GovernanceEvidenceSigningKey.__table__
        try:
            self.db.execute(
                insert(table).values(
                    id=record.id,
                    org_id=record.organization_id,
                    issuer_id=record.issuer_id,
                    key_id=record.key_id,
                    algorithm="Ed25519",
                    public_jwk_json=canonical_json(record.public_jwk.to_dict()),
                    public_key_fingerprint=record.public_key_fingerprint,
                    valid_from=self._timestamp(record.valid_from),
                    valid_until=self._timestamp(record.valid_until),
                    revoked_at=None,
                    revocation_reason=None,
                    revoked_by=None,
                    created_by=record.created_by,
                    created_at=self._timestamp(record.created_at),
                )
            )
        except IntegrityError as error:
            raise self._error(
                "trust_signing_key_exists",
                "The public signing key is already registered.",
            ) from error
        persisted = self.get_signing_key(
            organization_id=record.organization_id,
            issuer_id=record.issuer_id,
            signing_key_id=record.id,
            lock=False,
        )
        if persisted is None:
            raise self._error(
                "trust_signing_key_integrity_conflict",
                "The signing key could not be read after persistence.",
            )
        return persisted

    def revoke_signing_key(
        self,
        *,
        record: EvidenceSigningKeyRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
    ) -> EvidenceSigningKeyRecord | None:
        self._require_postgresql()
        table = GovernanceEvidenceSigningKey.__table__
        result = self.db.execute(
            update(table)
            .where(
                table.c.id == record.id,
                table.c.org_id == record.organization_id,
                table.c.issuer_id == record.issuer_id,
                table.c.revoked_at.is_(None),
                table.c.revoked_by.is_(None),
                table.c.revocation_reason.is_(None),
            )
            .values(
                revoked_by=actor_id,
                revoked_at=self._timestamp(now),
                revocation_reason=rationale,
            )
        )
        if result.rowcount != 1:
            return None
        return self.get_signing_key(
            organization_id=record.organization_id,
            issuer_id=record.issuer_id,
            signing_key_id=record.id,
            lock=False,
        )

"""Framework-free ports for the content-addressed evaluation input artifact store."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Protocol


_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class ArtifactStoreError(Exception):
    """Stable, non-disclosing object-store failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def artifact_storage_key(digest: str) -> str:
    """The one storage key for a digest, shared by the store and any broker.

    013n binds ``governance_evaluation_artifacts.storage_key`` to this value.
    """

    if not isinstance(digest, str) or _SHA256_HEX.fullmatch(digest) is None:
        raise ArtifactStoreError("invalid_digest")
    return f"sha256/{digest}"


class ArtifactStore(Protocol):
    """Write-once, content-addressed bytes. No delete and no list by design."""

    def put_if_absent(self, digest: str, data: bytes, content_type: str) -> bool:
        """Store ``data`` under ``digest``; False when the object already exists."""
        ...

    def get_verified(self, digest: str) -> bytes:
        """Return the stored bytes only when their SHA-256 equals ``digest``.

        Raises ``ArtifactStoreError`` with ``stored_object_missing``,
        ``stored_digest_mismatch`` or ``stored_size_mismatch``.
        """
        ...


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    organization_id: str
    sha256: str
    media_type: str
    size_bytes: int
    state: str
    scan_policy: str
    created_at: str
    available_at: str | None
    rejected_at: str | None
    rejection_reason: str | None


class EvaluationArtifactRepository(Protocol):
    """Row persistence and audit for artifacts, inside one database session."""

    def find(self, *, organization_id: str, sha256: str) -> ArtifactRecord | None: ...

    def find_by_id(
        self, *, organization_id: str, artifact_id: str
    ) -> ArtifactRecord | None: ...

    def insert_quarantined(
        self,
        *,
        organization_id: str,
        sha256: str,
        media_type: str,
        size_bytes: int,
        scan_policy: str,
    ) -> ArtifactRecord | None:
        """Insert one quarantined row; None when the org already has that digest."""
        ...

    def lock_quarantined(
        self, *, organization_id: str, artifact_id: str
    ) -> ArtifactRecord | None: ...

    def mark_available(self, *, organization_id: str, artifact_id: str) -> ArtifactRecord: ...

    def mark_rejected(
        self, *, organization_id: str, artifact_id: str, reason: str
    ) -> ArtifactRecord: ...

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
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


__all__ = [
    "ArtifactRecord",
    "ArtifactStore",
    "ArtifactStoreError",
    "EvaluationArtifactRepository",
    "artifact_storage_key",
]

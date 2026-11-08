"""Scan, store and promote evaluation input artifacts.

Order of operations for one upload:

1. scan the bytes; a hit records an audited rejection and writes nothing;
2. write the object once under its digest (the store refuses overwrites);
3. insert a quarantined row (one per organization and digest);
4. promote: re-read the stored object, re-verify its digest and size, re-scan
   it, then mark the row available, or rejected with a fixed reason code.

A replay of the same bytes returns the existing row and finishes a promotion
that an earlier request left quarantined.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass

from src.application.ports.evaluation_artifacts import (
    ArtifactRecord,
    ArtifactStore,
    ArtifactStoreError,
    EvaluationArtifactRepository,
)
from src.application.services.eval_engines.detectors import SECRETS


SCAN_POLICY = "fairmind-input-scan-v1"
ALLOWED_MEDIA_TYPES = frozenset({"text/csv", "application/json"})
STORED_OBJECT_REJECTIONS = frozenset(
    {"stored_object_missing", "stored_digest_mismatch", "stored_size_mismatch"}
)

# fairmind-input-scan-v1. A bounded pattern set: the shared secret detectors
# from eval_engines.detectors, plus PEM private keys of any algorithm, JSON
# credential members, and chain-of-thought markers. It is deliberately
# conservative: a match rejects the whole input, and the uploader removes it.
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")
_JSON_CREDENTIAL = re.compile(
    r'(?i)"(?:password|passwd|secret|client[_-]?secret|api[_-]?key|'
    r'access[_-]?token|refresh[_-]?token|private[_-]?key)"\s*:\s*"[^"]{8,}"'
)
_CHAIN_OF_THOUGHT = re.compile(
    r"(?i)<\s*/?\s*(?:think|thinking|reasoning|scratchpad)\s*>"
    r"|\bchain[\s_-]*of[\s_-]*thought\b"
    r"|\breasoning[_-](?:content|trace)s?\b"
)


def scan_input(data: bytes) -> str | None:
    """Return a fixed rejection code for unsafe input, or None when it is clean."""

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "undecodable_content"
    if "\x00" in text:
        return "undecodable_content"
    if _PRIVATE_KEY.search(text):
        return "private_key_detected"
    if _JSON_CREDENTIAL.search(text) or any(
        pattern.search(text) for _name, pattern, _valid in SECRETS
    ):
        return "credential_detected"
    if _CHAIN_OF_THOUGHT.search(text):
        return "chain_of_thought_detected"
    return None


class ArtifactUploadError(Exception):
    """Stable failure the HTTP boundary maps to a status code."""

    def __init__(self, code: str, reason_code: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class ArtifactUploadResult:
    record: ArtifactRecord
    created: bool


class EvaluationArtifactService:
    def __init__(
        self,
        repository: EvaluationArtifactRepository,
        store: ArtifactStore,
        *,
        max_bytes: int,
    ) -> None:
        self._repository = repository
        self._store = store
        self._max_bytes = max_bytes

    def upload(
        self,
        *,
        organization_id: str,
        actor_id: str,
        media_type: str,
        data: bytes,
    ) -> ArtifactUploadResult:
        if media_type not in ALLOWED_MEDIA_TYPES:
            raise ArtifactUploadError("unsupported_media_type")
        if not data:
            raise ArtifactUploadError("artifact_empty")
        if len(data) > self._max_bytes:
            raise ArtifactUploadError("artifact_too_large")
        digest = hashlib.sha256(data).hexdigest()

        existing = self._repository.find(organization_id=organization_id, sha256=digest)
        if existing is not None:
            return ArtifactUploadResult(self._finish(existing, actor_id), created=False)

        reason = scan_input(data)
        if reason is not None:
            # No digest in the audit: for a short input it would confirm a guessed secret.
            self._repository.audit(
                organization_id=organization_id,
                actor_id=actor_id,
                action="evaluation_artifact.upload_rejected",
                outcome="rejected",
                resource_type="evaluation_artifact_upload",
                resource_id=str(uuid.uuid4()),
                details={
                    "schemaVersion": 1,
                    "scanPolicy": SCAN_POLICY,
                    "reasonCode": reason,
                    "mediaType": media_type,
                    "sizeBytes": len(data),
                },
            )
            self._repository.commit()
            raise ArtifactUploadError("artifact_rejected", reason)

        try:
            self._store.put_if_absent(digest, data, media_type)
        except ArtifactStoreError:
            raise ArtifactUploadError("artifact_store_unavailable") from None

        inserted = self._repository.insert_quarantined(
            organization_id=organization_id,
            sha256=digest,
            media_type=media_type,
            size_bytes=len(data),
            scan_policy=SCAN_POLICY,
        )
        if inserted is None:
            # A concurrent upload of the same digest won; its row is now committed.
            self._repository.rollback()
            winner = self._repository.find(organization_id=organization_id, sha256=digest)
            if winner is None:
                raise ArtifactUploadError("artifact_store_unavailable")
            return ArtifactUploadResult(self._finish(winner, actor_id), created=False)
        self._repository.audit(
            organization_id=organization_id,
            actor_id=actor_id,
            action="evaluation_artifact.uploaded",
            outcome="success",
            resource_type="evaluation_artifact",
            resource_id=inserted.artifact_id,
            details={
                "schemaVersion": 1,
                "scanPolicy": SCAN_POLICY,
                "sha256": digest,
                "mediaType": media_type,
                "sizeBytes": len(data),
            },
        )
        self._repository.commit()
        return ArtifactUploadResult(self._finish(inserted, actor_id), created=True)

    def _finish(self, record: ArtifactRecord, actor_id: str) -> ArtifactRecord:
        if record.state != "quarantined":
            return record
        return self.promote(
            organization_id=record.organization_id,
            artifact_id=record.artifact_id,
            actor_id=actor_id,
        )

    def promote(self, *, organization_id: str, artifact_id: str, actor_id: str) -> ArtifactRecord:
        """Quarantined -> available only after the stored bytes re-verify."""

        locked = self._repository.lock_quarantined(
            organization_id=organization_id, artifact_id=artifact_id
        )
        if locked is None:
            # Another request promoted or rejected it first.
            self._repository.rollback()
            current = self._repository.find_by_id(
                organization_id=organization_id, artifact_id=artifact_id
            )
            if current is None:
                raise ArtifactUploadError("artifact_not_found")
            return current
        reason: str | None
        try:
            stored = self._store.get_verified(locked.sha256)
        except ArtifactStoreError as error:
            if error.code not in STORED_OBJECT_REJECTIONS:
                self._repository.rollback()
                raise ArtifactUploadError("artifact_store_unavailable") from None
            reason = error.code
        else:
            reason = (
                "stored_size_mismatch"
                if len(stored) != locked.size_bytes
                else scan_input(stored)
            )

        if reason is None:
            promoted = self._repository.mark_available(
                organization_id=organization_id, artifact_id=artifact_id
            )
            action, outcome, details = "evaluation_artifact.promoted", "success", {}
        else:
            promoted = self._repository.mark_rejected(
                organization_id=organization_id, artifact_id=artifact_id, reason=reason
            )
            action, outcome = "evaluation_artifact.promotion_rejected", "rejected"
            details = {"reasonCode": reason}
        self._repository.audit(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            outcome=outcome,
            resource_type="evaluation_artifact",
            resource_id=artifact_id,
            details={"schemaVersion": 1, "sha256": locked.sha256, **details},
        )
        self._repository.commit()
        return promoted


__all__ = [
    "ALLOWED_MEDIA_TYPES",
    "ArtifactUploadError",
    "ArtifactUploadResult",
    "EvaluationArtifactService",
    "SCAN_POLICY",
    "scan_input",
]

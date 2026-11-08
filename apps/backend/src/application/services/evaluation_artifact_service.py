"""Scan, store and promote evaluation input artifacts.

Order of operations for one upload:

1. scan the bytes; a hit records an audited rejection and writes nothing;
2. write the object once under its digest (the store refuses overwrites);
3. insert a quarantined row (one per organization and digest);
4. promote: re-read the stored object, re-verify its digest and size, re-scan
   it, then mark the row available, or rejected with a fixed reason code.

A replay of the same bytes returns the existing row and finishes a promotion
that an earlier request left quarantined, re-writing the object first.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
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
# A missing object is a store-side fault, not a verdict on the bytes: the row
# stays quarantined (503) and a replay re-writes the object, then promotes.
STORED_OBJECT_REJECTIONS = frozenset({"stored_digest_mismatch", "stored_size_mismatch"})

# fairmind-input-scan-v1. A bounded pattern set: the shared secret detectors
# from eval_engines.detectors, plus PEM private keys of any algorithm and
# chain-of-thought markers, run on the raw text and again on every decoded JSON
# key and string or CSV cell (so escapes and quoting cannot hide a match). A
# JSON member or CSV column whose name holds a credential word (password,
# secret, token, credential, api key, private key; compound names such as
# aws_secret_access_key or apiKey included) with a non-empty string value is a
# credential. Unparseable JSON or CSV is undecodable. It is deliberately
# conservative: a match rejects the whole input, and the uploader removes it.
# Not covered: secrets nested in a further encoding (base64, JSON inside a CSV
# cell) that match none of the patterns.
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")
_CHAIN_OF_THOUGHT = re.compile(
    r"(?i)<\s*/?\s*(?:think|thinking|reasoning|scratchpad)\s*>"
    r"|\bchain[\s_-]*of[\s_-]*thought\b"
    r"|\breasoning[_-](?:content|trace)s?\b"
)
_NAME_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+")
_CREDENTIAL_WORDS = frozenset(
    {
        "password", "passwords", "passwd", "passphrase", "secret", "secrets",
        "token", "credential", "credentials", "apikey", "privatekey",
    }
)
_CREDENTIAL_PAIRS = frozenset({("api", "key"), ("private", "key")})


def _is_credential_name(name: str) -> bool:
    words = [word.lower() for word in _NAME_WORD.findall(name)]
    return any(word in _CREDENTIAL_WORDS for word in words) or any(
        pair in _CREDENTIAL_PAIRS for pair in zip(words, words[1:])
    )


def _pattern_reason(text: str) -> str | None:
    if _PRIVATE_KEY.search(text):
        return "private_key_detected"
    if any(pattern.search(text) for _name, pattern, _valid in SECRETS):
        return "credential_detected"
    if _CHAIN_OF_THOUGHT.search(text):
        return "chain_of_thought_detected"
    return None


class _JsonObject(list):
    """Every (key, value) pair of one JSON object, duplicates included."""


def _json_fields(text: str) -> tuple[list[str], bool]:
    strings: list[str] = []
    credential = False
    stack: list[object] = [json.loads(text, object_pairs_hook=_JsonObject)]
    while stack:
        node = stack.pop()
        if isinstance(node, _JsonObject):
            for key, value in node:
                strings.append(key)
                if isinstance(value, str) and value.strip() and _is_credential_name(key):
                    credential = True
                stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, str):
            strings.append(node)
    return strings, credential


def _csv_fields(text: str) -> tuple[list[str], bool]:
    rows = csv.reader(io.StringIO(text, newline=""))
    header = next(rows, [])
    flagged = [index for index, name in enumerate(header) if _is_credential_name(name)]
    strings = list(header)
    credential = False
    for row in rows:
        strings.extend(row)
        if not credential and any(index < len(row) and row[index].strip() for index in flagged):
            credential = True
    return strings, credential


def scan_input(data: bytes, media_type: str) -> str | None:
    """Return a fixed rejection code for unsafe input, or None when it is clean."""

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "undecodable_content"
    if "\x00" in text:
        return "undecodable_content"
    reason = _pattern_reason(text)
    if reason is not None:
        return reason
    try:
        if media_type == "application/json":
            strings, credential = _json_fields(text)
        elif media_type == "text/csv":
            strings, credential = _csv_fields(text)
        else:
            return "undecodable_content"
    except (ValueError, RecursionError, csv.Error):
        return "undecodable_content"
    reason = _pattern_reason("\n".join(strings))
    if reason is not None:
        return reason
    return "credential_detected" if credential else None


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
            if (
                existing.state == "quarantined"
                and scan_input(data, existing.media_type) is None
            ):
                # Same digest, same bytes: re-write an object an earlier request
                # never landed (a no-op when it exists), then promote.
                self._put(digest, data, existing.media_type)
            return ArtifactUploadResult(self._finish(existing, actor_id), created=False)

        reason = scan_input(data, media_type)
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

        self._put(digest, data, media_type)

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

    def _put(self, digest: str, data: bytes, media_type: str) -> None:
        try:
            self._store.put_if_absent(digest, data, media_type)
        except ArtifactStoreError:
            raise ArtifactUploadError("artifact_store_unavailable") from None

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
                else scan_input(stored, locked.media_type)
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

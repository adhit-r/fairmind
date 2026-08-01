"""Side-effect-free authenticity assessment for parsed Evidence Passport V2 data."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import re
from types import MappingProxyType

from src.application.ports.evidence_admission import (
    EvidenceSignatureVerifier,
    ExpectedServerBinding,
    TrustedSigningKey,
)
from src.domain.assurance.evidence_passport_v2 import (
    EvidencePassportV2ValidationError,
    evidence_passport_v2_content_hash,
    evidence_passport_v2_signature_bytes,
    normalize_evidence_passport_v2,
)
from src.domain.assurance.evaluation_v2 import canonical_sha256


class EvidenceAuthenticityError(ValueError):
    """Stable, non-admission authenticity failure safe for caller handling."""


_TRUSTED_SOURCE_TYPES = frozenset({"fairmind_worker", "external_provider"})
_PUBLIC_JWK_KEYS = frozenset({"kty", "crv", "x"})
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]{43}$")
VERIFIER_CONTRACT = "fairmind/evidence-passport-v2/verified-admission"
VERIFIER_VERSION = "2.0.0"
_EVALUATOR_PROJECTION_KEYS = (
    "issuerId",
    "evaluatorId",
    "sourceType",
    "adapterName",
    "adapterVersion",
    "resultContractVersion",
)


def _validate_issuer_restrictions(
    *,
    source_type: str,
    suite_version_id: str,
    target_version_id: str,
    source_restrictions: tuple[str, ...],
    suite_restrictions: tuple[str, ...],
    target_restrictions: tuple[str, ...],
    known_suite_ids: frozenset[str],
    known_target_ids: frozenset[str],
) -> None:
    """Apply the Task 12 closed issuer-restriction semantics.

    Empty canonical arrays are unrestricted. Non-empty arrays are exact
    allow-lists, and every value must belong to the closed server catalog.
    """
    if source_type not in _TRUSTED_SOURCE_TYPES:
        raise EvidenceAuthenticityError("issuer source restriction is invalid")
    for values in (source_restrictions, suite_restrictions, target_restrictions):
        if len(values) != len(set(values)) or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise EvidenceAuthenticityError("issuer restriction is malformed")
    if source_restrictions and (
        any(value not in _TRUSTED_SOURCE_TYPES for value in source_restrictions)
        or source_type not in source_restrictions
    ):
        raise EvidenceAuthenticityError("issuer source is restricted")
    if suite_restrictions and (
        any(value not in known_suite_ids for value in suite_restrictions)
        or suite_version_id not in suite_restrictions
    ):
        raise EvidenceAuthenticityError("issuer suite is restricted")
    if target_restrictions and (
        any(value not in known_target_ids for value in target_restrictions)
        or target_version_id not in target_restrictions
    ):
        raise EvidenceAuthenticityError("issuer target is restricted")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise EvidenceAuthenticityError("timestamp must include a timezone")
    return value.astimezone(timezone.utc)


def _parse_timestamp(value: object, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise EvidenceAuthenticityError(f"{label} timestamp is missing")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise EvidenceAuthenticityError(f"{label} timestamp is invalid") from error
    return _as_utc(parsed)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise EvidenceAuthenticityError(f"{label} is missing")
    return value


def _text(mapping: Mapping[str, object], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise EvidenceAuthenticityError(f"{label} {key} is missing")
    return value


def _deep_freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _plain_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    if isinstance(value, list):
        return [_plain_value(item) for item in value]
    return value


def _canonical_ed25519_public_jwk(
    public_jwk: Mapping[str, object],
) -> dict[str, str]:
    """Return the exact three-member public JWK fingerprint domain.

    The fingerprint algorithm is SHA-256 lower-hex over the RFC 8785
    canonical JSON of ``{crv, kty, x}`` for one canonical Ed25519 public key.
    """
    if (
        frozenset(public_jwk) != _PUBLIC_JWK_KEYS
        or public_jwk.get("kty") != "OKP"
        or public_jwk.get("crv") != "Ed25519"
    ):
        raise EvidenceAuthenticityError("trusted public JWK is invalid")
    public_x = public_jwk.get("x")
    if not isinstance(public_x, str) or _BASE64URL.fullmatch(public_x) is None:
        raise EvidenceAuthenticityError("trusted public JWK is invalid")
    try:
        decoded = base64.b64decode(f"{public_x}=", altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        raise EvidenceAuthenticityError("trusted public JWK is invalid") from None
    if (
        len(decoded) != 32
        or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != public_x
    ):
        raise EvidenceAuthenticityError("trusted public JWK is invalid")
    return {"crv": "Ed25519", "kty": "OKP", "x": public_x}


@dataclass(frozen=True)
class AuthenticityCandidate:
    """Authenticity facts only; an outer admission workflow makes decisions."""

    content_hash: str
    signature_input_hash: str
    execution_binding_hash: str
    evaluator_projection_hash: str
    public_key_fingerprint: str
    verifier_contract: str
    verifier_version: str
    issuer_id: str
    key_id: str
    captured_at: datetime
    signed_at: datetime
    expires_at: datetime
    normalized_result: Mapping[str, object]

    def __post_init__(self) -> None:
        frozen = _deep_freeze(self.normalized_result)
        if not isinstance(frozen, Mapping):
            raise TypeError("normalized_result must be a mapping")
        object.__setattr__(self, "normalized_result", frozen)


class EvidenceAuthenticityService:
    """Verify a parsed passport using trusted, server-derived caller context.

    This service does not resolve the expected binding or signing key itself,
    and it does not store evidence or decide admission. Callers must obtain both
    context objects through trusted orchestration, never from submitted data.
    """

    def __init__(self, verifier: EvidenceSignatureVerifier) -> None:
        self._verifier = verifier

    def assess(
        self,
        passport: Mapping[str, object],
        expected: ExpectedServerBinding,
        trusted_key: TrustedSigningKey,
        now: datetime,
    ) -> AuthenticityCandidate:
        try:
            normalized = normalize_evidence_passport_v2(passport)
        except EvidencePassportV2ValidationError as error:
            raise EvidenceAuthenticityError("passport validation failed") from error
        now_utc = _as_utc(now)

        content_hash = _text(normalized, "contentHash", label="content hash")
        expected_hash = evidence_passport_v2_content_hash(normalized)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise EvidenceAuthenticityError("content hash does not match")

        self._verify_binding(normalized, expected)
        evaluator = _mapping(normalized.get("evaluator"), label="evaluator")
        signature = _mapping(normalized.get("signature"), label="signature")
        _mapping(normalized.get("result"), label="result")

        issuer_id = _text(signature, "issuerId", label="signature")
        key_id = _text(signature, "keyId", label="signature")
        algorithm = _text(signature, "algorithm", label="signature")
        signature_value = _text(signature, "value", label="signature")
        if issuer_id != _text(evaluator, "issuerId", label="evaluator"):
            raise EvidenceAuthenticityError("issuer does not match evaluator")
        if issuer_id != trusted_key.issuer_id:
            raise EvidenceAuthenticityError("issuer is not trusted")
        if key_id != trusted_key.key_id:
            raise EvidenceAuthenticityError("key is not trusted")
        if algorithm != trusted_key.algorithm:
            raise EvidenceAuthenticityError("key algorithm does not match signature")
        canonical_public_jwk = _canonical_ed25519_public_jwk(trusted_key.public_jwk)

        captured_at = _parse_timestamp(normalized.get("capturedAt"), label="captured")
        signed_at = _parse_timestamp(signature.get("signedAt"), label="signed")
        expires_at = _parse_timestamp(normalized.get("expiresAt"), label="expiry")
        if not captured_at <= signed_at <= expires_at:
            raise EvidenceAuthenticityError("timestamp order is invalid")
        if signed_at > now_utc or expires_at <= now_utc:
            raise EvidenceAuthenticityError("timestamp window is invalid")
        self._verify_key_window(trusted_key, signed_at, now_utc)

        signing_input = evidence_passport_v2_signature_bytes(normalized)
        try:
            verified = self._verifier(
                signing_input=signing_input,
                signature_b64url=signature_value,
                public_jwk=trusted_key.public_jwk,
            )
        except Exception as error:
            raise EvidenceAuthenticityError("signature verification failed") from error
        if verified is not True:
            raise EvidenceAuthenticityError("signature verification failed")

        normalized_result = _mapping(normalized.get("result"), label="result")
        evaluator_projection = {
            key: _text(evaluator, key, label="evaluator")
            for key in _EVALUATOR_PROJECTION_KEYS
        }

        return AuthenticityCandidate(
            content_hash=content_hash,
            signature_input_hash=hashlib.sha256(signing_input).hexdigest(),
            execution_binding_hash=canonical_sha256(_plain_value(expected.execution_binding)),
            evaluator_projection_hash=canonical_sha256(evaluator_projection),
            public_key_fingerprint=canonical_sha256(canonical_public_jwk),
            verifier_contract=VERIFIER_CONTRACT,
            verifier_version=VERIFIER_VERSION,
            issuer_id=issuer_id,
            key_id=key_id,
            captured_at=captured_at,
            signed_at=signed_at,
            expires_at=expires_at,
            normalized_result=normalized_result,
        )

    @staticmethod
    def _verify_binding(
        passport: Mapping[str, object], expected: ExpectedServerBinding
    ) -> None:
        if passport.get("organizationId") != expected.organization_id:
            raise EvidenceAuthenticityError("tenant organization does not match")
        if passport.get("workspaceId") != expected.workspace_id:
            raise EvidenceAuthenticityError("tenant workspace does not match")
        if passport.get("systemId") != expected.system_id:
            raise EvidenceAuthenticityError("tenant system does not match")
        binding = _mapping(passport.get("executionBinding"), label="execution binding")
        if binding != expected.execution_binding:
            raise EvidenceAuthenticityError("execution binding does not match")

    @staticmethod
    def _verify_key_window(
        key: TrustedSigningKey, signed_at: datetime, now: datetime
    ) -> None:
        valid_from = _as_utc(key.valid_from)
        valid_until = _as_utc(key.valid_until)
        revoked_at = _as_utc(key.revoked_at) if key.revoked_at is not None else None
        if now < valid_from or now > valid_until:
            raise EvidenceAuthenticityError("key is outside its validity window")
        if signed_at < valid_from or signed_at > valid_until:
            raise EvidenceAuthenticityError("key was invalid when signed")
        if revoked_at is not None and revoked_at <= now:
            raise EvidenceAuthenticityError("key is revoked")

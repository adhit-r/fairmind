"""Ed25519 verification adapter for evidence supplied by trusted issuers."""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class EvidenceVerificationError(ValueError):
    """Raised when evidence signature material cannot be verified safely."""


_PUBLIC_JWK_KEYS = frozenset({"kty", "crv", "x"})
_BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _decode_canonical_base64url(
    value: object,
    *,
    decoded_length: int,
    error_message: str,
) -> bytes:
    encoded_length = (decoded_length * 8 + 5) // 6
    if (
        not isinstance(value, str)
        or len(value) != encoded_length
        or _BASE64URL_PATTERN.fullmatch(value) is None
    ):
        raise EvidenceVerificationError(error_message)

    padding = "=" * (-len(value) % 4)
    try:
        decoded = base64.b64decode(
            f"{value}{padding}",
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError):
        raise EvidenceVerificationError(error_message) from None

    canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if len(decoded) != decoded_length or canonical != value:
        raise EvidenceVerificationError(error_message)
    return decoded


def _public_key_bytes(public_jwk: object) -> bytes:
    if not isinstance(public_jwk, Mapping):
        raise EvidenceVerificationError("invalid Ed25519 public JWK")
    try:
        exact_shape = frozenset(public_jwk) == _PUBLIC_JWK_KEYS
        expected_type = public_jwk.get("kty") == "OKP"
        expected_curve = public_jwk.get("crv") == "Ed25519"
        public_x = public_jwk.get("x")
    except Exception:
        raise EvidenceVerificationError("invalid Ed25519 public JWK") from None
    if not exact_shape or not expected_type or not expected_curve:
        raise EvidenceVerificationError("invalid Ed25519 public JWK")
    return _decode_canonical_base64url(
        public_x,
        decoded_length=32,
        error_message="invalid Ed25519 public JWK",
    )


class Ed25519EvidenceVerifier:
    """Verify an evidence signing input against server-selected public JWK context."""

    def __call__(
        self,
        *,
        signing_input: bytes,
        signature_b64url: str,
        public_jwk: Mapping[str, object],
    ) -> bool:
        if not isinstance(signing_input, bytes):
            raise EvidenceVerificationError("invalid evidence signing input")
        public_key_bytes = _public_key_bytes(public_jwk)
        signature = _decode_canonical_base64url(
            signature_b64url,
            decoded_length=64,
            error_message="invalid evidence signature encoding",
        )
        try:
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
                signature,
                signing_input,
            )
        except InvalidSignature:
            raise EvidenceVerificationError(
                "evidence signature verification failed"
            ) from None
        return True

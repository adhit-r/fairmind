"""Pure Ed25519 key contract shared by trust persistence and admission."""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping


class EvidenceAuthenticityError(ValueError):
    """Stable, non-admission authenticity failure safe for caller handling."""


_PUBLIC_JWK_KEYS = frozenset({"kty", "crv", "x"})
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]{43}$")


def canonical_ed25519_public_jwk(
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


__all__ = ["EvidenceAuthenticityError", "canonical_ed25519_public_jwk"]

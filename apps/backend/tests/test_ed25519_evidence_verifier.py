import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from src.infrastructure.security import (
    Ed25519EvidenceVerifier,
    EvidenceVerificationError,
)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _noncanonical_b64url(raw: bytes) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    encoded = _b64url(raw)
    last_value = alphabet.index(encoded[-1])
    return f"{encoded[:-1]}{alphabet[last_value + 1]}"


def _verifier() -> Ed25519EvidenceVerifier:
    return Ed25519EvidenceVerifier()


def _generated_material() -> tuple[bytes, bytes, dict[str, str]]:
    private_key = Ed25519PrivateKey.generate()
    signing_input = b"fairmind-evidence-envelope-v2"
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        signing_input,
        private_key.sign(signing_input),
        {"kty": "OKP", "crv": "Ed25519", "x": _b64url(public_key)},
    )


def _assert_verification_rejected(
    *, signing_input: bytes, signature: bytes, public_jwk: dict[str, str]
) -> None:
    with pytest.raises(
        EvidenceVerificationError,
        match=r"^evidence signature verification failed$",
    ) as exc_info:
        _verifier()(
            signing_input=signing_input,
            signature_b64url=_b64url(signature),
            public_jwk=public_jwk,
        )
    assert exc_info.value.__cause__ is None


def _assert_public_jwk_rejected(public_jwk: object) -> None:
    signing_input, signature, _ = _generated_material()
    with pytest.raises(
        EvidenceVerificationError,
        match=r"^invalid Ed25519 public JWK$",
    ) as exc_info:
        _verifier()(
            signing_input=signing_input,
            signature_b64url=_b64url(signature),
            public_jwk=public_jwk,
        )
    assert exc_info.value.__cause__ is None


def _assert_signature_encoding_rejected(signature_b64url: object) -> None:
    signing_input, _, public_jwk = _generated_material()
    with pytest.raises(
        EvidenceVerificationError,
        match=r"^invalid evidence signature encoding$",
    ) as exc_info:
        _verifier()(
            signing_input=signing_input,
            signature_b64url=signature_b64url,
            public_jwk=public_jwk,
        )
    assert exc_info.value.__cause__ is None


def test_verifies_rfc_8032_empty_message_vector() -> None:
    public_key = bytes.fromhex(
        "d75a980182b10ab7d54bfed3c964073a"
        "0ee172f3daa62325af021a68f707511a"
    )
    signature = bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a"
        "84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46b"
        "d25bf5f0595bbe24655141438e7a100b"
    )

    assert (
        _verifier()(
            signing_input=b"",
            signature_b64url=_b64url(signature),
            public_jwk={"kty": "OKP", "crv": "Ed25519", "x": _b64url(public_key)},
        )
        is True
    )


def test_verifies_signature_generated_by_cryptography() -> None:
    signing_input, signature, public_jwk = _generated_material()

    assert (
        _verifier()(
            signing_input=signing_input,
            signature_b64url=_b64url(signature),
            public_jwk=public_jwk,
        )
        is True
    )


def test_rejects_one_bit_signing_input_mutation() -> None:
    signing_input, signature, public_jwk = _generated_material()
    mutated_input = bytes([signing_input[0] ^ 1]) + signing_input[1:]

    _assert_verification_rejected(
        signing_input=mutated_input,
        signature=signature,
        public_jwk=public_jwk,
    )


def test_rejects_one_bit_signature_mutation() -> None:
    signing_input, signature, public_jwk = _generated_material()
    mutated_signature = bytes([signature[0] ^ 1]) + signature[1:]

    _assert_verification_rejected(
        signing_input=signing_input,
        signature=mutated_signature,
        public_jwk=public_jwk,
    )


def test_rejects_signature_from_a_different_public_key() -> None:
    signing_input, signature, _ = _generated_material()
    _, _, different_public_jwk = _generated_material()

    _assert_verification_rejected(
        signing_input=signing_input,
        signature=signature,
        public_jwk=different_public_jwk,
    )


def test_rejects_one_bit_public_key_mutation() -> None:
    signing_input, signature, public_jwk = _generated_material()
    public_key = bytearray(
        base64.urlsafe_b64decode(f"{public_jwk['x']}=".encode("ascii"))
    )
    public_key[0] ^= 1
    mutated_public_jwk = {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": _b64url(bytes(public_key)),
    }

    _assert_verification_rejected(
        signing_input=signing_input,
        signature=signature,
        public_jwk=mutated_public_jwk,
    )


@pytest.mark.parametrize(
    "jwk_mutation",
    [
        pytest.param({"kty": "EC"}, id="wrong-kty"),
        pytest.param({"crv": "X25519"}, id="wrong-curve"),
        pytest.param({"alg": "RS256"}, id="wrong-algorithm"),
        pytest.param({"alg": "EdDSA"}, id="algorithm-is-not-part-of-closed-shape"),
        pytest.param({"d": _b64url(b"private" * 5)}, id="private-key-material"),
        pytest.param({"pem": "-----BEGIN PUBLIC KEY-----"}, id="pem-material"),
        pytest.param({"kid": "passport-selected-key"}, id="extra-key-id"),
    ],
)
def test_rejects_non_exact_or_private_jwk_fields(
    jwk_mutation: dict[str, str],
) -> None:
    _, _, public_jwk = _generated_material()
    public_jwk.update(jwk_mutation)

    _assert_public_jwk_rejected(public_jwk)


@pytest.mark.parametrize(
    "public_jwk",
    [
        pytest.param({}, id="missing-fields"),
        pytest.param({"jwk": {"kty": "OKP"}}, id="embedded-jwk"),
        pytest.param("-----BEGIN PUBLIC KEY-----", id="bare-pem"),
        pytest.param(["OKP", "Ed25519"], id="non-mapping"),
    ],
)
def test_rejects_non_jwk_context_shapes(public_jwk: object) -> None:
    _assert_public_jwk_rejected(public_jwk)


@pytest.mark.parametrize(
    "invalid_x",
    [
        pytest.param("!" * 43, id="malformed-alphabet"),
        pytest.param(_b64url(b"x" * 32) + "=", id="padded"),
        pytest.param(_b64url(b"x" * 31), id="short-key"),
        pytest.param(_b64url(b"x" * 33), id="long-key"),
        pytest.param(_noncanonical_b64url(b"x" * 32), id="noncanonical-pad-bits"),
        pytest.param(b"not-text", id="non-text"),
    ],
)
def test_rejects_invalid_public_key_base64url(invalid_x: object) -> None:
    _assert_public_jwk_rejected(
        {"kty": "OKP", "crv": "Ed25519", "x": invalid_x}
    )


@pytest.mark.parametrize(
    "invalid_signature",
    [
        pytest.param("!" * 86, id="malformed-alphabet"),
        pytest.param(_b64url(b"s" * 64) + "=", id="padded"),
        pytest.param(_b64url(b"s" * 63), id="short-signature"),
        pytest.param(_b64url(b"s" * 65), id="long-signature"),
        pytest.param(
            _noncanonical_b64url(b"s" * 64),
            id="noncanonical-pad-bits",
        ),
        pytest.param(b"not-text", id="non-text"),
    ],
)
def test_rejects_invalid_signature_base64url(invalid_signature: object) -> None:
    _assert_signature_encoding_rejected(invalid_signature)


@pytest.mark.parametrize(
    "invalid_signing_input",
    [
        pytest.param("not-bytes", id="text"),
        pytest.param(bytearray(b"mutable"), id="mutable-bytearray"),
        pytest.param(memoryview(b"borrowed"), id="memoryview"),
    ],
)
def test_rejects_non_bytes_signing_input(invalid_signing_input: object) -> None:
    _, signature, public_jwk = _generated_material()
    with pytest.raises(
        EvidenceVerificationError,
        match=r"^invalid evidence signing input$",
    ) as exc_info:
        _verifier()(
            signing_input=invalid_signing_input,
            signature_b64url=_b64url(signature),
            public_jwk=public_jwk,
        )
    assert exc_info.value.__cause__ is None

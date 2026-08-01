"""Framework-free inputs for candidate evidence authenticity assessment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Protocol, runtime_checkable


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    frozen = _freeze(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("expected a mapping")
    return frozen


@dataclass(frozen=True)
class ExpectedServerBinding:
    """Trusted orchestration output; never construct this from submitted evidence."""

    organization_id: str
    workspace_id: str
    system_id: str
    execution_binding: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_binding", _freeze_mapping(self.execution_binding))


@dataclass(frozen=True)
class TrustedSigningKey:
    """Trusted lookup output selected under the bound immutable trust policy."""

    issuer_id: str
    key_id: str
    algorithm: str
    public_jwk: Mapping[str, object]
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "public_jwk", _freeze_mapping(self.public_jwk))


@runtime_checkable
class EvidenceSignatureVerifier(Protocol):
    """Crypto adapter; it performs no trust lookup or persistence."""

    def __call__(
        self,
        *,
        signing_input: bytes,
        signature_b64url: str,
        public_jwk: Mapping[str, object],
    ) -> bool: ...

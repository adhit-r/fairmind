"""Server-owned evaluator registrations for Evidence Passport V2 admission.

The registry is deliberately separate from submitted Passport data.  A signed
``evaluatorId`` is only eligible when the server has an active registration
whose adapter, source, and result contract exactly match the locked suite.
This first implementation is an immutable in-process catalog; persistence and
registration ceremonies remain a later, separately reviewed boundary.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Protocol

from src.domain.assurance.evaluation_v2 import canonical_sha256

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_ALLOWED_SOURCES = frozenset({"fairmind_worker", "external_provider"})
_ALLOWED_STATUSES = frozenset({"active", "deprecated", "revoked"})


class EvaluatorRegistryError(ValueError):
    """A server-owned evaluator registration cannot authorize a binding."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class EvaluatorRegistry(Protocol):
    """Application port for a server-owned evaluator catalog."""

    catalog_hash: str

    def validate_binding(
        self,
        *,
        evaluator_id: str,
        source_type: str,
        adapter_name: str,
        adapter_version: str,
        result_contract_version: str,
    ) -> EvaluatorRegistration: ...


def _require_identifier(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise EvaluatorRegistryError(
            "evaluator_registration_invalid",
            f"The evaluator {label} is invalid.",
        )
    return value


@dataclass(frozen=True, slots=True)
class EvaluatorRegistration:
    """One immutable server-owned evaluator identity and compatibility tuple."""

    evaluator_id: str
    adapter_name: str
    adapter_version: str
    result_contract_version: str
    source_types: frozenset[str]
    status: str = "active"

    def __post_init__(self) -> None:
        for value, label in (
            (self.evaluator_id, "id"),
            (self.adapter_name, "adapter name"),
            (self.adapter_version, "adapter version"),
            (self.result_contract_version, "result contract version"),
        ):
            _require_identifier(value, label=label)
        if self.status not in _ALLOWED_STATUSES:
            raise EvaluatorRegistryError(
                "evaluator_registration_invalid",
                "The evaluator status is invalid.",
            )
        if not isinstance(self.source_types, frozenset) or not self.source_types:
            raise EvaluatorRegistryError(
                "evaluator_registration_invalid",
                "An evaluator must allow at least one delivery source.",
            )
        if not self.source_types.issubset(_ALLOWED_SOURCES):
            raise EvaluatorRegistryError(
                "evaluator_registration_invalid",
                "The evaluator source allowlist is invalid.",
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluatorId": self.evaluator_id,
            "adapterName": self.adapter_name,
            "adapterVersion": self.adapter_version,
            "resultContractVersion": self.result_contract_version,
            "sourceTypes": sorted(self.source_types),
            "status": self.status,
        }


class StaticEvaluatorRegistry:
    """An immutable server-owned catalog used before persistent registration."""

    def __init__(
        self,
        *,
        catalog_version: str,
        registrations: Iterable[EvaluatorRegistration],
    ) -> None:
        self.catalog_version = _require_identifier(catalog_version, label="catalog version")
        by_id: dict[str, EvaluatorRegistration] = {}
        for registration in registrations:
            if not isinstance(registration, EvaluatorRegistration):
                raise EvaluatorRegistryError(
                    "evaluator_registration_invalid",
                    "The evaluator catalog contains an invalid registration.",
                )
            if registration.evaluator_id in by_id:
                raise EvaluatorRegistryError(
                    "evaluator_registration_duplicate",
                    f"The evaluator catalog contains a duplicate registration for {registration.evaluator_id}.",
                )
            by_id[registration.evaluator_id] = registration
        self._registrations = MappingProxyType(by_id)
        self.catalog_hash = canonical_sha256(
            {
                "catalogVersion": self.catalog_version,
                "registrations": [
                    registration.to_dict()
                    for registration in sorted(by_id.values(), key=lambda item: item.evaluator_id)
                ],
            }
        )

    def resolve(self, evaluator_id: str) -> EvaluatorRegistration | None:
        """Return a catalog row without treating it as authorized."""

        return self._registrations.get(evaluator_id)

    def validate_binding(
        self,
        *,
        evaluator_id: str,
        source_type: str,
        adapter_name: str,
        adapter_version: str,
        result_contract_version: str,
    ) -> EvaluatorRegistration:
        """Fail closed unless the exact signed/locked compatibility tuple is catalogued."""

        evaluator_id = _require_identifier(evaluator_id, label="id")
        registration = self.resolve(evaluator_id)
        if registration is None:
            raise EvaluatorRegistryError(
                "evaluator_unregistered",
                "The evaluator is not registered by FairMind.",
            )
        if registration.status != "active":
            raise EvaluatorRegistryError(
                "evaluator_inactive",
                "The evaluator registration is not active.",
            )
        if source_type not in registration.source_types:
            raise EvaluatorRegistryError(
                "evaluator_source_not_allowed",
                "The evaluator is not authorized for this delivery source.",
            )
        if (
            adapter_name != registration.adapter_name
            or adapter_version != registration.adapter_version
            or result_contract_version != registration.result_contract_version
        ):
            raise EvaluatorRegistryError(
                "evaluator_binding_mismatch",
                "The evaluator binding does not match its server registration.",
            )
        return registration


__all__ = [
    "EvaluatorRegistration",
    "EvaluatorRegistry",
    "EvaluatorRegistryError",
    "StaticEvaluatorRegistry",
]

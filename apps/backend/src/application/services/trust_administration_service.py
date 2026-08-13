"""Stable facade for organization-scoped trust administration."""

from src.application.services.trust_administration_shared import (
    DEFAULT_TRUST_LIST_LIMIT,
    MAX_TRUST_LIST_LIMIT,
    MAX_TRUST_LIST_OFFSET,
    POLICY_SCHEMA_VERSION,
    SEMVER_PATTERN,
    TrustAdministrationError,
    TrustAdministrationShared,
)
from src.application.services.trust_issuer_operations import TrustIssuerOperations
from src.application.services.trust_policy_operations import TrustPolicyOperations
from src.application.services.trust_signing_key_operations import TrustSigningKeyOperations


class TrustAdministrationService(
    TrustIssuerOperations,
    TrustSigningKeyOperations,
    TrustPolicyOperations,
    TrustAdministrationShared,
):
    """Expose one service contract while keeping resource logic cohesive."""


__all__ = [
    "DEFAULT_TRUST_LIST_LIMIT",
    "MAX_TRUST_LIST_LIMIT",
    "MAX_TRUST_LIST_OFFSET",
    "POLICY_SCHEMA_VERSION",
    "SEMVER_PATTERN",
    "TrustAdministrationError",
    "TrustAdministrationService",
]

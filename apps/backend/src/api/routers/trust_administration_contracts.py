"""Strict transport contracts for trust administration."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.routes.evaluation_workbench import StrictModel
from src.application.services.trust_administration_service import (
    MAX_TRUST_LIST_LIMIT,
    MAX_TRUST_LIST_OFFSET,
    SEMVER_PATTERN,
)


IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"
UTC_TIMESTAMP_PATTERN = (
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?\+00:00$"
)


class EvidenceIssuerCreate(StrictModel):
    issuer_key: str = Field(alias="issuerKey", min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN)
    name: str = Field(min_length=1, max_length=256)
    issuer_type: Literal["fairmind_worker", "external_provider"] = Field(alias="issuerType")
    source_restrictions: list[str] = Field(alias="sourceRestrictions", max_length=100)
    suite_version_restrictions: list[str] = Field(alias="suiteVersionRestrictions", max_length=100)
    target_version_restrictions: list[str] = Field(alias="targetVersionRestrictions", max_length=100)


class PublicEd25519Jwk(StrictModel):
    crv: Literal["Ed25519"]
    kty: Literal["OKP"]
    x: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]{43}$")


class TrustPolicyDocument(StrictModel):
    maximum_evidence_age_seconds: int = Field(alias="maximumEvidenceAgeSeconds", ge=1)
    schema_version: Literal["1.0.0"] = Field(alias="schemaVersion")
    unsigned_import_policy: Literal["reject", "manual_review"] = Field(
        alias="unsignedImportPolicy"
    )


class EvidenceSigningKeyCreate(StrictModel):
    key_id: str = Field(alias="keyId", min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN)
    public_jwk: PublicEd25519Jwk = Field(alias="publicJwk")
    valid_from: str = Field(alias="validFrom", pattern=UTC_TIMESTAMP_PATTERN)
    valid_until: str = Field(alias="validUntil", pattern=UTC_TIMESTAMP_PATTERN)


class TrustPolicyCreate(StrictModel):
    version: str = Field(min_length=5, max_length=32, pattern=SEMVER_PATTERN)
    maximum_evidence_age_seconds: int = Field(
        alias="maximumEvidenceAgeSeconds", ge=1, le=2_147_483_647
    )
    unsigned_import_policy: Literal["reject", "manual_review"] = Field(
        alias="unsignedImportPolicy"
    )
    supersedes_id: str | None = Field(
        default=None,
        alias="supersedesId",
        min_length=1,
        max_length=128,
        pattern=IDENTIFIER_PATTERN,
    )


class RationaleRequest(StrictModel):
    rationale: str = Field(min_length=1, max_length=2_000)


class TrustPolicyActivationRequest(StrictModel):
    expected_current_policy_id: str | None = Field(
        default=None,
        alias="expectedCurrentPolicyId",
        min_length=1,
        max_length=128,
        pattern=IDENTIFIER_PATTERN,
    )
    expected_current_policy_hash: str | None = Field(
        default=None, alias="expectedCurrentPolicyHash", pattern=r"^[0-9a-f]{64}$"
    )
    rationale: str | None = Field(default=None, min_length=1, max_length=2_000)


class EvidenceIssuerResponse(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    issuer_key: str = Field(alias="issuerKey")
    name: str
    issuer_type: Literal["fairmind_worker", "external_provider"] = Field(alias="issuerType")
    source_restrictions: list[str] = Field(alias="sourceRestrictions")
    suite_version_restrictions: list[str] = Field(alias="suiteVersionRestrictions")
    target_version_restrictions: list[str] = Field(alias="targetVersionRestrictions")
    status: Literal["active", "revoked"]
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    revoked_by: str | None = Field(alias="revokedBy")
    revoked_at: str | None = Field(alias="revokedAt")
    revocation_reason: str | None = Field(alias="revocationReason")


class EvidenceSigningKeyResponse(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    issuer_id: str = Field(alias="issuerId")
    key_id: str = Field(alias="keyId")
    algorithm: Literal["Ed25519"]
    public_jwk: PublicEd25519Jwk = Field(alias="publicJwk")
    public_key_fingerprint: str = Field(alias="publicKeyFingerprint", pattern=r"^[0-9a-f]{64}$")
    valid_from: str = Field(alias="validFrom")
    valid_until: str = Field(alias="validUntil")
    revoked_by: str | None = Field(alias="revokedBy")
    revoked_at: str | None = Field(alias="revokedAt")
    revocation_reason: str | None = Field(alias="revocationReason")
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")


class TrustPolicyResponse(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    version: str = Field(pattern=SEMVER_PATTERN)
    policy_schema_version: Literal["1.0.0"] = Field(alias="policySchemaVersion")
    policy: TrustPolicyDocument
    policy_hash: str = Field(alias="policyHash", pattern=r"^[0-9a-f]{64}$")
    maximum_evidence_age_seconds: int = Field(alias="maximumEvidenceAgeSeconds")
    unsigned_import_policy: Literal["reject", "manual_review"] = Field(alias="unsignedImportPolicy")
    status: Literal["draft", "active", "retired"]
    supersedes_id: str | None = Field(alias="supersedesId")
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")
    activated_by: str | None = Field(alias="activatedBy")
    activated_at: str | None = Field(alias="activatedAt")
    retired_by: str | None = Field(alias="retiredBy")
    retired_at: str | None = Field(alias="retiredAt")
    retirement_reason: str | None = Field(alias="retirementReason")


class EvidenceIssuerPage(StrictModel):
    items: list[EvidenceIssuerResponse]
    limit: int = Field(ge=1, le=MAX_TRUST_LIST_LIMIT)
    offset: int = Field(ge=0, le=MAX_TRUST_LIST_OFFSET)
    has_more: bool = Field(alias="hasMore")


class EvidenceSigningKeyPage(StrictModel):
    items: list[EvidenceSigningKeyResponse]
    limit: int = Field(ge=1, le=MAX_TRUST_LIST_LIMIT)
    offset: int = Field(ge=0, le=MAX_TRUST_LIST_OFFSET)
    has_more: bool = Field(alias="hasMore")


class TrustPolicyPage(StrictModel):
    items: list[TrustPolicyResponse]
    limit: int = Field(ge=1, le=MAX_TRUST_LIST_LIMIT)
    offset: int = Field(ge=0, le=MAX_TRUST_LIST_OFFSET)
    has_more: bool = Field(alias="hasMore")

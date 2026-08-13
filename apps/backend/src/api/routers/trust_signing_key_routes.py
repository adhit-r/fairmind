"""Public Ed25519 signing-key trust-administration endpoints."""

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from api.routes.evaluation_workbench import _payload, _request_body_schema, _respond
from src.api.routers.governance_assurance import organization_membership
from src.api.routers.trust_administration_contracts import (
    IDENTIFIER_PATTERN,
    EvidenceSigningKeyCreate,
    EvidenceSigningKeyPage,
    EvidenceSigningKeyResponse,
    RationaleRequest,
)
from src.api.routers.trust_administration_http import (
    authorize,
    get_trust_administration_service,
    missing,
    raise_application,
    require_trust_administration_enabled,
)
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.trust_administration_service import (
    DEFAULT_TRUST_LIST_LIMIT,
    MAX_TRUST_LIST_LIMIT,
    MAX_TRUST_LIST_OFFSET,
    TrustAdministrationService,
)


signing_key_router = APIRouter(
    dependencies=[Depends(require_trust_administration_enabled)]
)


@signing_key_router.post(
    "/issuers/{issuer_id}/keys",
    status_code=201,
    response_model=EvidenceSigningKeyResponse,
    openapi_extra=_request_body_schema(EvidenceSigningKeyCreate),
)
async def create_signing_key(
    org_id: str,
    request: Request,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, EvidenceSigningKeyCreate)
    try:
        return _respond(
            service.create_signing_key(
                organization_id=membership.org_id,
                issuer_id=issuer_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                payload=payload,
            ),
            EvidenceSigningKeyResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@signing_key_router.get(
    "/issuers/{issuer_id}/keys", response_model=EvidenceSigningKeyPage
)
def list_signing_keys(
    org_id: str,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    limit: int = Query(DEFAULT_TRUST_LIST_LIMIT, ge=1, le=MAX_TRUST_LIST_LIMIT),
    offset: int = Query(0, ge=0, le=MAX_TRUST_LIST_OFFSET),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        return service.list_signing_keys(
            organization_id=membership.org_id,
            issuer_id=issuer_id,
            limit=limit,
            offset=offset,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@signing_key_router.get(
    "/issuers/{issuer_id}/keys/{signing_key_id}",
    response_model=EvidenceSigningKeyResponse,
)
def get_signing_key(
    org_id: str,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    signing_key_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        record = service.get_signing_key(
            organization_id=membership.org_id,
            issuer_id=issuer_id,
            signing_key_id=signing_key_id,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)
    if record is None:
        missing(
            "trust_signing_key_not_found",
            "The signing key was not found for this issuer and organization.",
        )
    return record


@signing_key_router.post(
    "/issuers/{issuer_id}/keys/{signing_key_id}/revoke",
    response_model=EvidenceSigningKeyResponse,
    openapi_extra=_request_body_schema(RationaleRequest),
)
async def revoke_signing_key(
    org_id: str,
    request: Request,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    signing_key_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, RationaleRequest)
    try:
        return _respond(
            service.revoke_signing_key(
                organization_id=membership.org_id,
                issuer_id=issuer_id,
                signing_key_id=signing_key_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            ),
            EvidenceSigningKeyResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


__all__ = ["signing_key_router"]

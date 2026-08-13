"""Evidence-issuer trust-administration endpoints."""

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from api.routes.evaluation_workbench import _payload, _request_body_schema, _respond
from src.api.routers.governance_assurance import organization_membership
from src.api.routers.trust_administration_contracts import (
    IDENTIFIER_PATTERN,
    EvidenceIssuerCreate,
    EvidenceIssuerPage,
    EvidenceIssuerResponse,
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


issuer_router = APIRouter(dependencies=[Depends(require_trust_administration_enabled)])


@issuer_router.post(
    "/issuers",
    status_code=201,
    response_model=EvidenceIssuerResponse,
    openapi_extra=_request_body_schema(EvidenceIssuerCreate),
)
async def create_issuer(
    org_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, EvidenceIssuerCreate)
    try:
        return _respond(
            service.create_issuer(
                organization_id=membership.org_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                payload=payload,
            ),
            EvidenceIssuerResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@issuer_router.get("/issuers", response_model=EvidenceIssuerPage)
def list_issuers(
    org_id: str,
    limit: int = Query(DEFAULT_TRUST_LIST_LIMIT, ge=1, le=MAX_TRUST_LIST_LIMIT),
    offset: int = Query(0, ge=0, le=MAX_TRUST_LIST_OFFSET),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        return service.list_issuers(
            organization_id=membership.org_id, limit=limit, offset=offset
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@issuer_router.get("/issuers/{issuer_id}", response_model=EvidenceIssuerResponse)
def get_issuer(
    org_id: str,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        record = service.get_issuer(
            organization_id=membership.org_id, issuer_id=issuer_id
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)
    if record is None:
        missing(
            "trust_issuer_not_found",
            "The evidence issuer was not found in this organization.",
        )
    return record


@issuer_router.post(
    "/issuers/{issuer_id}/revoke",
    response_model=EvidenceIssuerResponse,
    openapi_extra=_request_body_schema(RationaleRequest),
)
async def revoke_issuer(
    org_id: str,
    request: Request,
    issuer_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, RationaleRequest)
    try:
        return _respond(
            service.revoke_issuer(
                organization_id=membership.org_id,
                issuer_id=issuer_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            ),
            EvidenceIssuerResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


__all__ = ["issuer_router"]

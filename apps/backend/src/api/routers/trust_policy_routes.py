"""Immutable trust-policy administration endpoints."""

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from api.routes.evaluation_workbench import _payload, _request_body_schema, _respond
from src.api.routers.governance_assurance import organization_membership
from src.api.routers.trust_administration_contracts import (
    IDENTIFIER_PATTERN,
    RationaleRequest,
    TrustPolicyActivationRequest,
    TrustPolicyCreate,
    TrustPolicyPage,
    TrustPolicyResponse,
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


policy_router = APIRouter(dependencies=[Depends(require_trust_administration_enabled)])


@policy_router.post(
    "/policies",
    status_code=201,
    response_model=TrustPolicyResponse,
    openapi_extra=_request_body_schema(TrustPolicyCreate),
)
async def create_policy(
    org_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, TrustPolicyCreate)
    normalized_payload = {**payload, "supersedesId": payload.get("supersedesId")}
    try:
        return _respond(
            service.create_policy(
                organization_id=membership.org_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                payload=normalized_payload,
            ),
            TrustPolicyResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@policy_router.get("/policies", response_model=TrustPolicyPage)
def list_policies(
    org_id: str,
    limit: int = Query(DEFAULT_TRUST_LIST_LIMIT, ge=1, le=MAX_TRUST_LIST_LIMIT),
    offset: int = Query(0, ge=0, le=MAX_TRUST_LIST_OFFSET),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        return service.list_policies(
            organization_id=membership.org_id, limit=limit, offset=offset
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@policy_router.get("/policies/{policy_id}", response_model=TrustPolicyResponse)
def get_policy(
    org_id: str,
    policy_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> dict[str, object]:
    authorize(membership, org_id)
    try:
        record = service.get_policy(
            organization_id=membership.org_id, policy_id=policy_id
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)
    if record is None:
        missing(
            "trust_policy_not_found",
            "The trust policy was not found in this organization.",
        )
    return record


@policy_router.post(
    "/policies/{policy_id}/activate",
    response_model=TrustPolicyResponse,
    openapi_extra=_request_body_schema(TrustPolicyActivationRequest),
)
async def activate_policy(
    org_id: str,
    request: Request,
    policy_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, TrustPolicyActivationRequest)
    try:
        return _respond(
            service.activate_policy(
                organization_id=membership.org_id,
                policy_id=policy_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                expected_current_policy_id=payload.get("expectedCurrentPolicyId"),
                expected_current_policy_hash=payload.get("expectedCurrentPolicyHash"),
                rationale=payload.get("rationale"),
            ),
            TrustPolicyResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


@policy_router.post(
    "/policies/{policy_id}/retire",
    response_model=TrustPolicyResponse,
    openapi_extra=_request_body_schema(RationaleRequest),
)
async def retire_policy(
    org_id: str,
    request: Request,
    policy_id: str = Path(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    service: TrustAdministrationService = Depends(get_trust_administration_service),
) -> Response:
    authorize(membership, org_id)
    payload = await _payload(request, RationaleRequest)
    try:
        return _respond(
            service.retire_policy(
                organization_id=membership.org_id,
                policy_id=policy_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            ),
            TrustPolicyResponse,
        )
    except EvaluationWorkbenchError as error:
        raise_application(error)


__all__ = ["policy_router"]

"""Default-off, organization-scoped evaluator registration administration.

The catalog records an audited identity authorization ceremony only. It does
not attest to an evaluator's quality, readiness, or any compliance outcome.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request, Response
from pydantic import Field
from sqlalchemy.orm import Session

from api.composition.evaluator_catalog import build_evaluator_catalog_service
from api.routes.evaluation_workbench import (
    StrictModel,
    _payload,
    _request_body_schema,
    _respond,
)
from config.settings import settings
from database.connection import get_db
from src.api.evaluation_permissions import (
    EVALUATION_CATALOG_ADMIN_PERMISSION,
    require_evaluation_permission,
)
from src.api.routers.governance_assurance import organization_membership
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.evaluator_catalog_service import (
    DEFAULT_CATALOG_LIST_LIMIT,
    MAX_CATALOG_LIST_LIMIT,
    MAX_CATALOG_LIST_OFFSET,
    EvaluatorCatalogService,
)
from src.application.services.evaluator_registration import EvaluatorIdentityBinding
from src.application.services.governance_assurance_service import OrgMembership

_IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"

evaluator_catalog_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-evaluator-catalog"],
)


class EvaluatorCatalogSubmitRequest(StrictModel):
    """Immutable evaluator identity tuple; server-owned lifecycle fields are absent."""

    evaluator_id: str = Field(
        alias="evaluatorId",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )
    source_type: Literal["fairmind_worker", "external_provider"] = Field(alias="sourceType")
    adapter_name: str = Field(
        alias="adapterName",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )
    adapter_version: str = Field(
        alias="adapterVersion",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )
    result_contract_version: str = Field(
        alias="resultContractVersion",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )
    issuer_id: str = Field(
        alias="issuerId",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )
    signing_key_id: str = Field(
        alias="signingKeyId",
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    )


class EvaluatorCatalogDecisionRequest(StrictModel):
    """Reviewer rationale only; status and reviewers are always server-owned."""

    rationale: str = Field(min_length=1, max_length=2_000)


class EvaluatorCatalogRegistrationResponse(StrictModel):
    """A registration ceremony record, not an evaluator performance claim."""

    id: str
    organization_id: str = Field(alias="organizationId")
    evaluator_id: str = Field(alias="evaluatorId")
    source_type: Literal["fairmind_worker", "external_provider"] = Field(alias="sourceType")
    adapter_name: str = Field(alias="adapterName")
    adapter_version: str = Field(alias="adapterVersion")
    result_contract_version: str = Field(alias="resultContractVersion")
    issuer_id: str = Field(alias="issuerId")
    signing_key_id: str = Field(alias="signingKeyId")
    binding_hash: str = Field(alias="bindingHash", pattern="^[0-9a-f]{64}$")
    status: Literal["pending", "approved", "rejected", "revoked"]
    submitted_by: str = Field(alias="submittedBy")
    submitted_at: str = Field(alias="submittedAt")
    reviewed_by: str | None = Field(alias="reviewedBy")
    reviewed_at: str | None = Field(alias="reviewedAt")
    review_rationale: str | None = Field(alias="reviewRationale")
    revoked_by: str | None = Field(alias="revokedBy")
    revoked_at: str | None = Field(alias="revokedAt")
    revocation_rationale: str | None = Field(alias="revocationRationale")


class EvaluatorCatalogRegistrationPage(StrictModel):
    """Explicit stable page; no response silently represents an entire catalog."""

    items: list[EvaluatorCatalogRegistrationResponse]
    limit: int = Field(ge=1, le=MAX_CATALOG_LIST_LIMIT)
    offset: int = Field(ge=0, le=MAX_CATALOG_LIST_OFFSET)
    has_more: bool = Field(alias="hasMore")


def get_evaluator_catalog_service(
    db: Session = Depends(get_db),
) -> EvaluatorCatalogService:
    """Compose the service only at the feature-gated HTTP boundary."""

    return build_evaluator_catalog_service(db)


def _require_evaluator_catalog_enabled() -> None:
    """Fail closed even if a test or embedding app mounts the router directly."""

    if not (settings.assurance_v2_enabled and settings.assurance_v2_evaluator_catalog_enabled):
        raise HTTPException(
            status_code=404,
            detail={
                "code": "assurance_feature_disabled",
                "message": "Evaluator catalog administration is not enabled.",
            },
        )


def _require_catalog_scope(membership: OrgMembership, org_id: str) -> None:
    """Use only the membership-derived organization identity for service calls."""

    if membership.org_id != org_id:
        _missing_registration()


def _missing_registration() -> None:
    raise HTTPException(
        status_code=404,
        detail={
            "code": "evaluator_registration_not_found",
            "message": "The evaluator registration was not found in this organization.",
        },
    )


def _raise(error: EvaluationWorkbenchError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail()) from error


def _binding_from_payload(payload: dict[str, object]) -> EvaluatorIdentityBinding:
    """Construct the service tuple after strict HTTP contract validation."""

    return EvaluatorIdentityBinding(
        evaluator_id=payload["evaluatorId"],
        source_type=payload["sourceType"],
        adapter_name=payload["adapterName"],
        adapter_version=payload["adapterVersion"],
        result_contract_version=payload["resultContractVersion"],
        issuer_id=payload["issuerId"],
        key_id=payload["signingKeyId"],
    )


async def _transition(
    *,
    transition: str,
    org_id: str,
    registration_id: str,
    request: Request,
    idempotency_key: str,
    membership: OrgMembership,
    catalog_service: EvaluatorCatalogService,
) -> Response:
    _require_catalog_scope(membership, org_id)
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    payload = await _payload(request, EvaluatorCatalogDecisionRequest)
    try:
        if transition == "approve":
            result = catalog_service.approve(
                organization_id=membership.org_id,
                registration_id=registration_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            )
        elif transition == "reject":
            result = catalog_service.reject(
                organization_id=membership.org_id,
                registration_id=registration_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            )
        elif transition == "revoke":
            result = catalog_service.revoke(
                organization_id=membership.org_id,
                registration_id=registration_id,
                actor_id=membership.user_id,
                idempotency_key=idempotency_key,
                rationale=payload["rationale"],
            )
        else:
            raise RuntimeError("Unsupported evaluator catalog transition.")
        return _respond(result, EvaluatorCatalogRegistrationResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@evaluator_catalog_router.post(
    "/evaluation-v2/evaluator-catalog/registrations",
    status_code=201,
    response_model=EvaluatorCatalogRegistrationResponse,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
    openapi_extra=_request_body_schema(EvaluatorCatalogSubmitRequest),
)
async def submit_evaluator_registration(
    org_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> Response:
    """Submit one immutable binding for independent organization review."""

    _require_catalog_scope(membership, org_id)
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    payload = await _payload(request, EvaluatorCatalogSubmitRequest)
    try:
        result = catalog_service.submit(
            organization_id=membership.org_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            binding=_binding_from_payload(payload),
        )
        return _respond(result, EvaluatorCatalogRegistrationResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@evaluator_catalog_router.get(
    "/evaluation-v2/evaluator-catalog/registrations",
    response_model=EvaluatorCatalogRegistrationPage,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
)
def list_evaluator_registrations(
    org_id: str,
    limit: int = Query(
        default=DEFAULT_CATALOG_LIST_LIMIT,
        ge=1,
        le=MAX_CATALOG_LIST_LIMIT,
    ),
    offset: int = Query(default=0, ge=0, le=MAX_CATALOG_LIST_OFFSET),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> dict[str, object]:
    """Return one explicit, stable page in the caller's active organization scope."""

    _require_catalog_scope(membership, org_id)
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    try:
        return catalog_service.list(
            organization_id=membership.org_id,
            limit=limit,
            offset=offset,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)


@evaluator_catalog_router.get(
    "/evaluation-v2/evaluator-catalog/registrations/{registration_id}",
    response_model=EvaluatorCatalogRegistrationResponse,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
)
def get_evaluator_registration(
    org_id: str,
    registration_id: str = Path(
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    ),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> dict[str, object]:
    """Read one registration without disclosing a record from another organization."""

    _require_catalog_scope(membership, org_id)
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    try:
        registration = catalog_service.get(
            organization_id=membership.org_id,
            registration_id=registration_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if registration is None:
        _missing_registration()
    return registration


@evaluator_catalog_router.post(
    "/evaluation-v2/evaluator-catalog/registrations/{registration_id}/approve",
    response_model=EvaluatorCatalogRegistrationResponse,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
    openapi_extra=_request_body_schema(EvaluatorCatalogDecisionRequest),
)
async def approve_evaluator_registration(
    org_id: str,
    request: Request,
    registration_id: str = Path(
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    ),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> Response:
    """Record an independent approval; the service enforces four-eyes review."""

    return await _transition(
        transition="approve",
        org_id=org_id,
        registration_id=registration_id,
        request=request,
        idempotency_key=idempotency_key,
        membership=membership,
        catalog_service=catalog_service,
    )


@evaluator_catalog_router.post(
    "/evaluation-v2/evaluator-catalog/registrations/{registration_id}/reject",
    response_model=EvaluatorCatalogRegistrationResponse,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
    openapi_extra=_request_body_schema(EvaluatorCatalogDecisionRequest),
)
async def reject_evaluator_registration(
    org_id: str,
    request: Request,
    registration_id: str = Path(
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    ),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> Response:
    """Record an independent rejection without changing the immutable binding."""

    return await _transition(
        transition="reject",
        org_id=org_id,
        registration_id=registration_id,
        request=request,
        idempotency_key=idempotency_key,
        membership=membership,
        catalog_service=catalog_service,
    )


@evaluator_catalog_router.post(
    "/evaluation-v2/evaluator-catalog/registrations/{registration_id}/revoke",
    response_model=EvaluatorCatalogRegistrationResponse,
    dependencies=[Depends(_require_evaluator_catalog_enabled)],
    openapi_extra=_request_body_schema(EvaluatorCatalogDecisionRequest),
)
async def revoke_evaluator_registration(
    org_id: str,
    request: Request,
    registration_id: str = Path(
        min_length=1,
        max_length=128,
        pattern=_IDENTIFIER_PATTERN,
    ),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    catalog_service: EvaluatorCatalogService = Depends(get_evaluator_catalog_service),
) -> Response:
    """Record a revocation of an approved binding through the audited service."""

    return await _transition(
        transition="revoke",
        org_id=org_id,
        registration_id=registration_id,
        request=request,
        idempotency_key=idempotency_key,
        membership=membership,
        catalog_service=catalog_service,
    )


__all__ = [
    "evaluator_catalog_router",
    "get_evaluator_catalog_service",
]

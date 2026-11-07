"""Organization-scoped AI policy routes: draft, distribute, map and enforce."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.governance_assurance import _require_mutation, organization_membership
from database.connection import get_db
from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService,
    OrgMembership,
)
from src.application.services.policy_service import (
    DRAFT_SCHEMA,
    DRAFT_SYSTEM,
    FACTS,
    OPS,
    PolicyService,
    PolicyStateError,
)

router = APIRouter(prefix="/organizations/{org_id}/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=2000)
    body: str = Field(default="", max_length=200_000)
    owner: str | None = Field(default=None, max_length=200)
    rules: list[dict[str, Any]] = Field(default_factory=list, max_length=200)


class PolicyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    body: str | None = Field(default=None, max_length=200_000)
    owner: str | None = Field(default=None, max_length=200)
    rules: list[dict[str, Any]] | None = Field(default=None, max_length=200)


class PolicyDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brief: str = Field(min_length=10, max_length=4000)


class PolicyAction(BaseModel):
    action: Literal["submit", "reject", "approve", "publish", "revise", "retire"]


class EnforceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    policy_id: str | None = Field(default=None, alias="policyId")
    system_id: str | None = Field(default=None, alias="systemId")


def _mutator(membership: OrgMembership, db: Session) -> PolicyService:
    _require_mutation(membership, GovernanceAssuranceService(db))
    return PolicyService(db)


def _found(value, what: str = "Policy"):
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")
    return value


def _invalid(error: ValueError) -> HTTPException:
    code = status.HTTP_409_CONFLICT if isinstance(error, PolicyStateError) else status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=code, detail=str(error))


@router.get("/language")
def rule_language(_membership: OrgMembership = Depends(organization_membership)) -> dict:
    """The facts and operators a rule may use."""
    return {"facts": [{"name": k, "description": v} for k, v in FACTS.items()], "ops": list(OPS)}


@router.get("")
def list_policies(membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)) -> list[dict]:
    return PolicyService(db).list(membership.org_id, membership.user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_policy(
    request: PolicyCreate, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    try:
        return _mutator(membership, db).create(membership.org_id, membership.user_id, request.model_dump())
    except ValueError as error:
        raise _invalid(error) from error


def _org_model(db: Session, org_id: str) -> llm.Connection:
    """The organization's own model (bring your own key), as set up in organization settings."""
    from api.routes.packs import _ai_row, _stored_connection

    row = _ai_row(db, org_id)
    if not row or not row["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Connect your organisation's AI model in Organisation settings to draft policies with AI",
        )
    return _stored_connection(row)


@router.post("/draft", status_code=status.HTTP_201_CREATED)
async def draft_policy(
    request: PolicyDraftRequest, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    """The organization's model drafts a policy from a brief; it is saved as a draft for people to review."""
    service = _mutator(membership, db)
    conn = _org_model(db, membership.org_id)
    context = service.draft_context(membership.org_id, request.brief.strip())
    db.rollback()  # hold no transaction open while the model works
    try:
        data, meta = await llm.complete(conn, DRAFT_SYSTEM, context, DRAFT_SCHEMA)
    except llm.LLMError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    policy, dropped = service.create_from_draft(membership.org_id, membership.user_id, data)
    return {**policy, "draft": {"provider": conn.provider.id, "model": meta["model"], "dropped": dropped}}


@router.get("/alerts")
def list_alerts(
    include_resolved: bool = False,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    return PolicyService(db).alerts(membership.org_id, include_resolved)


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    return _found(_mutator(membership, db).acknowledge_alert(membership.org_id, alert_id, membership.user_id), "Alert")


@router.get("/coverage")
def framework_coverage(membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)) -> list[dict]:
    return PolicyService(db).coverage(membership.org_id)


@router.post("/enforce")
def enforce(
    request: EnforceRequest, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    service = _mutator(membership, db)
    run = _found(service.enforce(membership.org_id, request.policy_id, request.system_id), "System")
    service.sync_alerts(membership.org_id)  # alerts show at once; the next sweep emails them
    return run


@router.get("/evaluations")
def current_evaluations(membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)) -> list[dict]:
    return PolicyService(db).current_results(membership.org_id)


@router.get("/gate/{system_id}")
def policy_gate(
    system_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    """CI and release checks call this: allowed is false while a blocking rule fails."""
    return _found(PolicyService(db).gate(membership.org_id, system_id), "System")


@router.get("/{policy_id}")
def get_policy(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    return _found(PolicyService(db).get(membership.org_id, policy_id, membership.user_id))


@router.patch("/{policy_id}")
def update_policy(
    policy_id: str,
    request: PolicyUpdate,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return _found(
            _mutator(membership, db).update(
                membership.org_id, policy_id, membership.user_id, request.model_dump(exclude_unset=True)
            )
        )
    except ValueError as error:
        raise _invalid(error) from error


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    try:
        if not _mutator(membership, db).delete(membership.org_id, policy_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    except PolicyStateError as error:
        raise _invalid(error) from error
    return {"id": policy_id, "deleted": True}


@router.post("/{policy_id}/actions")
def policy_action(
    policy_id: str,
    request: PolicyAction,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return _found(_mutator(membership, db).transition(membership.org_id, policy_id, membership.user_id, request.action))
    except PolicyStateError as error:
        raise _invalid(error) from error


@router.post("/{policy_id}/acknowledge")
def acknowledge(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> dict:
    try:
        return _found(PolicyService(db).acknowledge(membership.org_id, policy_id, membership.user_id))
    except PolicyStateError as error:
        raise _invalid(error) from error


@router.get("/{policy_id}/acknowledgements")
def acknowledgements(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> list[dict]:
    return _found(PolicyService(db).acknowledgements(membership.org_id, policy_id))


@router.get("/{policy_id}/versions")
def versions(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> list[dict]:
    return _found(PolicyService(db).versions(membership.org_id, policy_id))


@router.get("/{policy_id}/evaluations")
def policy_evaluations(
    policy_id: str, membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> list[dict]:
    _found(PolicyService(db).get(membership.org_id, policy_id, membership.user_id))
    return PolicyService(db).current_results(membership.org_id, policy_id)

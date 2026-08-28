"""Shared feature, authorization, and response helpers for trust HTTP routes."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from api.composition.trust_administration import build_trust_administration_service
from config.settings import settings
from database.connection import get_db
from src.api.evaluation_permissions import (
    EVALUATION_TRUST_ADMIN_PERMISSION,
    require_evaluation_permission,
)
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.trust_administration_service import TrustAdministrationService


def get_trust_administration_service(
    db: Session = Depends(get_db),
) -> TrustAdministrationService:
    return build_trust_administration_service(db)


def require_trust_administration_enabled() -> None:
    if not (
        settings.assurance_v2_enabled
        and settings.assurance_v2_trust_administration_enabled
    ):
        raise HTTPException(
            404,
            detail={
                "code": "assurance_feature_disabled",
                "message": "Trust administration is not enabled.",
            },
        )


def authorize(membership: OrgMembership, org_id: str) -> None:
    if membership.org_id != org_id:
        missing("trust_resource_not_found", "The trust resource was not found in this organization.")
    require_evaluation_permission(membership, EVALUATION_TRUST_ADMIN_PERMISSION)


def missing(code: str, message: str) -> None:
    raise HTTPException(404, detail={"code": code, "message": message})


def raise_application(error: EvaluationWorkbenchError) -> None:
    raise HTTPException(error.status_code, detail=error.detail()) from error

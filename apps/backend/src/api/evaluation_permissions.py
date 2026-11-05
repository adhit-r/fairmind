"""Fail-closed permission vocabulary for Assurance V2 HTTP boundaries.

Only permissions in ``LIVE_HUMAN_PERMISSION_ERRORS`` authorize ordinary human
API routes. Worker authority has a separate, unmounted, tenant-bound service
principal predicate. Separation override is reserved for the PostgreSQL-proven
canonical owner and exact delegated grants rather than generic human role
checks. Trust admin is live only at the independently gated administration
route.
"""

from __future__ import annotations

import re
from typing import Final

from fastapi import HTTPException

from config.auth import PrincipalKind, TokenData, TokenType
from config.settings import settings
from src.application.services.governance_assurance_service import OrgMembership

EVALUATION_PLAN_WRITE_PERMISSION: Final = "evaluation:plan:write"
EVALUATION_PLAN_ACTIVATE_PERMISSION: Final = "evaluation:plan:activate"
EVALUATION_RUN_CREATE_PERMISSION: Final = "evaluation:run:create"
EVALUATION_EVIDENCE_SUBMIT_PERMISSION: Final = "evaluation:evidence:submit"
EVALUATION_EVIDENCE_IMPORT_PERMISSION: Final = "evaluation:evidence:import"
EVALUATION_EVIDENCE_LINK_PERMISSION: Final = "evaluation:evidence:link"
EVALUATION_EVIDENCE_REVIEW_PERMISSION: Final = "evaluation:evidence:review"
EVALUATION_DECISION_PERMISSION: Final = "evaluation:decision"
EVALUATION_CATALOG_ADMIN_PERMISSION: Final = "evaluation:catalog:admin"

EVALUATION_TRUST_ADMIN_PERMISSION: Final = "evaluation:trust:admin"
# Reserved vocabulary. These constants do not authorize an ordinary human route.
EVALUATION_SEPARATION_OVERRIDE_PERMISSION: Final = "evaluation:separation:override"
EVALUATION_WORKER_PERMISSION: Final = "evaluation:worker"  # Service principals only.
_MAX_SERVICE_PERMISSIONS: Final = 64
_MAX_SERVICE_PERMISSION_LENGTH: Final = 128
_SERVICE_PERMISSION_PATTERN: Final = re.compile(
    r"^[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]*)*$"
)

LIVE_HUMAN_PERMISSION_ERRORS: Final[dict[str, tuple[str, str]]] = {
    EVALUATION_PLAN_WRITE_PERMISSION: (
        "evaluation_plan_write_forbidden",
        "The evaluation:plan:write permission is required.",
    ),
    EVALUATION_PLAN_ACTIVATE_PERMISSION: (
        "evaluation_plan_activate_forbidden",
        "The evaluation:plan:activate permission is required.",
    ),
    EVALUATION_RUN_CREATE_PERMISSION: (
        "evaluation_run_create_forbidden",
        "The evaluation:run:create permission is required.",
    ),
    EVALUATION_EVIDENCE_SUBMIT_PERMISSION: (
        "evaluation_evidence_submit_forbidden",
        "The evaluation:evidence:submit permission is required.",
    ),
    EVALUATION_EVIDENCE_IMPORT_PERMISSION: (
        "evaluation_evidence_import_forbidden",
        "The evaluation:evidence:import permission is required.",
    ),
    EVALUATION_EVIDENCE_LINK_PERMISSION: (
        "evaluation_evidence_link_forbidden",
        "The evaluation:evidence:link permission is required.",
    ),
    EVALUATION_EVIDENCE_REVIEW_PERMISSION: (
        "evaluation_evidence_review_forbidden",
        "The evaluation:evidence:review permission is required.",
    ),
    EVALUATION_DECISION_PERMISSION: (
        "evaluation_decision_write_forbidden",
        "The evaluation:decision permission is required.",
    ),
    EVALUATION_CATALOG_ADMIN_PERMISSION: (
        "evaluation_catalog_admin_forbidden",
        "The evaluation:catalog:admin permission is required.",
    ),
    EVALUATION_TRUST_ADMIN_PERMISSION: (
        "evaluation_trust_admin_forbidden",
        "The evaluation:trust:admin permission is required.",
    ),
}


def require_evaluation_worker_principal(
    principal: TokenData,
    *,
    expected_org_id: str,
) -> TokenData:
    """Authorize only one tenant-bound service principal for future worker use.

    ``expected_org_id`` must come from a persisted run or execution envelope,
    never from untrusted request input. This predicate intentionally mounts no
    worker route and provides no credential issuer or runtime implementation.
    """

    permissions = tuple(principal.permissions)
    permissions_are_canonical = (
        0 < len(permissions) <= _MAX_SERVICE_PERMISSIONS
        and len(permissions) == len(set(permissions))
        and all(
            isinstance(permission, str)
            and 0 < len(permission) <= _MAX_SERVICE_PERMISSION_LENGTH
            and _SERVICE_PERMISSION_PATTERN.fullmatch(permission) is not None
            for permission in permissions
        )
    )
    authorized = (
        principal.principal_kind is PrincipalKind.SERVICE
        and principal.token_type is TokenType.ACCESS
        and isinstance(expected_org_id, str)
        and bool(expected_org_id)
        and expected_org_id == expected_org_id.strip()
        and principal.organization_id == expected_org_id
        and permissions_are_canonical
        and "*" not in permissions
        and EVALUATION_WORKER_PERMISSION in permissions
    )
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "evaluation_worker_forbidden",
                "message": "A tenant-bound FairMind worker principal is required.",
            },
        )
    return principal


def require_assurance_v2_enabled() -> None:
    """Fail closed when a caller mounts the core router directly."""

    if not settings.assurance_v2_enabled:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "assurance_feature_disabled",
                "message": "Assurance-contract v2 is not enabled.",
            },
        )


def require_evaluation_permission(
    membership: OrgMembership,
    permission: str,
) -> None:
    """Require one literal permission from persisted organization membership."""

    error = LIVE_HUMAN_PERMISSION_ERRORS.get(permission)
    if error is None:
        raise RuntimeError("Permission is not exposed to human Assurance V2 routes.")
    if permission not in membership.permissions:
        code, message = error
        raise HTTPException(
            status_code=403,
            detail={"code": code, "message": message},
        )


__all__ = [
    "EVALUATION_CATALOG_ADMIN_PERMISSION",
    "EVALUATION_DECISION_PERMISSION",
    "EVALUATION_EVIDENCE_LINK_PERMISSION",
    "EVALUATION_EVIDENCE_IMPORT_PERMISSION",
    "EVALUATION_EVIDENCE_REVIEW_PERMISSION",
    "EVALUATION_EVIDENCE_SUBMIT_PERMISSION",
    "EVALUATION_PLAN_ACTIVATE_PERMISSION",
    "EVALUATION_PLAN_WRITE_PERMISSION",
    "EVALUATION_RUN_CREATE_PERMISSION",
    "EVALUATION_SEPARATION_OVERRIDE_PERMISSION",
    "EVALUATION_TRUST_ADMIN_PERMISSION",
    "EVALUATION_WORKER_PERMISSION",
    "LIVE_HUMAN_PERMISSION_ERRORS",
    "require_assurance_v2_enabled",
    "require_evaluation_permission",
]

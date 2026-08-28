"""Canonical default-off trust-administration router.

The compatibility package ``api.routes`` is a repository symlink to this
canonical router directory, so this module is also the thin legacy import
surface without duplicated transport logic.
"""

from fastapi import APIRouter, Depends

from src.api.routers.trust_administration_http import (
    get_trust_administration_service,
    require_trust_administration_enabled,
)
from src.api.routers.trust_issuer_routes import issuer_router
from src.api.routers.trust_policy_routes import policy_router
from src.api.routers.trust_signing_key_routes import signing_key_router


trust_administration_router = APIRouter(
    prefix="/organizations/{org_id}/evaluation-v2/trust",
    tags=["evaluation-workbench-v2-trust-administration"],
    dependencies=[Depends(require_trust_administration_enabled)],
)
trust_administration_router.include_router(issuer_router)
trust_administration_router.include_router(signing_key_router)
trust_administration_router.include_router(policy_router)

# Conventional name for loaders that do not use the explicit attribute.
router = trust_administration_router


__all__ = [
    "get_trust_administration_service",
    "router",
    "trust_administration_router",
]

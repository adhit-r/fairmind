from .compliance_routes import router as automation_router
from api.routes.india_compliance import router as india_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(automation_router)
router.include_router(india_router)

__all__ = ["router"]

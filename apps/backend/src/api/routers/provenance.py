from fastapi import APIRouter, Depends, HTTPException

from config.auth import get_current_active_user

# Both routes answer 501 until lineage is recorded; keep them behind sign-in so
# the tenant check has a place to land when they do.
router = APIRouter(dependencies=[Depends(get_current_active_user)])

_NOT_RECORDED = "Model provenance is not recorded yet. Register lineage through the AI-BOM before reading it here."


@router.get("/{model_id}")
def get_model_provenance(model_id: str):
    """Model provenance. Returns 501 until real lineage is recorded."""
    raise HTTPException(status_code=501, detail=_NOT_RECORDED)


@router.get("/{model_id}/dna")
def get_model_dna(model_id: str):
    """Model DNA. Returns 501 until real lineage is recorded."""
    raise HTTPException(status_code=501, detail=_NOT_RECORDED)

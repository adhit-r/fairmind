from fastapi import APIRouter, HTTPException

router = APIRouter()

_NOT_RECORDED = "Model provenance is not recorded yet. Register lineage through the AI-BOM before reading it here."


@router.get("/{model_id}")
async def get_model_provenance(model_id: str):
    """Model provenance. Returns 501 until real lineage is recorded."""
    raise HTTPException(status_code=501, detail=_NOT_RECORDED)


@router.get("/{model_id}/dna")
async def get_model_dna(model_id: str):
    """Model DNA. Returns 501 until real lineage is recorded."""
    raise HTTPException(status_code=501, detail=_NOT_RECORDED)

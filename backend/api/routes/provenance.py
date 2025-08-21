"""
Provenance Tracking API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid

from ..models.core import ProvenanceRequest, ProvenanceResponse
from ..services.model_provenance_service import ModelProvenanceService

router = APIRouter(prefix="/provenance", tags=["provenance"])

# Initialize services
provenance_service = ModelProvenanceService()

logger = logging.getLogger(__name__)

@router.post("/dataset")
async def create_dataset_provenance(
    dataset_name: str = Form(...),
    dataset_description: str = Form(...),
    source: str = Form(...),
    metadata: str = Form("{}")  # JSON string
):
    """Create provenance record for a dataset"""
    try:
        import json
        metadata_dict = json.loads(metadata)
        
        provenance = provenance_service.create_dataset_provenance(
            name=dataset_name,
            description=dataset_description,
            source=source,
            metadata=metadata_dict
        )
        
        return {
            "success": True,
            "provenance": provenance
        }
    except Exception as e:
        logger.error(f"Error creating dataset provenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/model")
async def create_model_provenance(
    model_name: str = Form(...),
    model_description: str = Form(...),
    model_type: str = Form(...),
    version: str = Form(...),
    metadata: str = Form("{}")  # JSON string
):
    """Create provenance record for a model"""
    try:
        import json
        metadata_dict = json.loads(metadata)
        
        provenance = provenance_service.create_model_provenance(
            name=model_name,
            description=model_description,
            model_type=model_type,
            version=version,
            metadata=metadata_dict
        )
        
        return {
            "success": True,
            "provenance": provenance
        }
    except Exception as e:
        logger.error(f"Error creating model provenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan-model")
async def scan_model(
    model_file: UploadFile = File(...),
    scan_type: str = Form("security")
):
    """Scan a model for security and quality issues"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
            content = await model_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            scan_result = provenance_service.scan_model(
                model_path=tmp_file_path,
                scan_type=scan_type
            )
            
            return {
                "success": True,
                "scan_result": scan_result
            }
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Error scanning model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-authenticity")
async def verify_model_authenticity(
    model_id: str = Form(...),
    signature: str = Form(...)
):
    """Verify the authenticity of a model using digital signature"""
    try:
        verification_result = provenance_service.verify_model_authenticity(
            model_id=model_id,
            signature=signature
        )
        
        return {
            "success": True,
            "verification": verification_result
        }
    except Exception as e:
        logger.error(f"Error verifying model authenticity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-card/{model_id}")
async def generate_model_card(model_id: str):
    """Generate a model card for a specific model"""
    try:
        model_card = provenance_service.generate_model_card(model_id)
        
        return {
            "success": True,
            "model_card": model_card
        }
    except Exception as e:
        logger.error(f"Error generating model card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chain/{model_id}")
async def get_provenance_chain(model_id: str):
    """Get the complete provenance chain for a model"""
    try:
        provenance_chain = provenance_service.get_provenance_chain(model_id)
        
        return {
            "success": True,
            "provenance_chain": provenance_chain
        }
    except Exception as e:
        logger.error(f"Error getting provenance chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{model_id}")
async def export_provenance_report(model_id: str):
    """Export a comprehensive provenance report for a model"""
    try:
        report = provenance_service.export_provenance_report(model_id)
        
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"Error exporting provenance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_provenance_models():
    """List all models with provenance tracking"""
    try:
        models = provenance_service.list_provenance_models()
        
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error listing provenance models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


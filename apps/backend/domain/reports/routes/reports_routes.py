"""
Reports API Routes

Endpoints for generating and downloading reports.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
import os

# Import service
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.reports.services.report_generator_service import report_generator_service

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)

class ReportRequest(BaseModel):
    report_type: str  # "bias_audit", "compliance_cert", "model_card"
    model_data: Dict[str, Any]
    report_data: Dict[str, Any]  # Bias results or compliance data

@router.post("/generate")
async def generate_report(request: ReportRequest):
    """Generate a PDF report"""
    try:
        if request.report_type == "bias_audit":
            filepath = await report_generator_service.generate_bias_audit_report(
                request.model_data, request.report_data
            )
        elif request.report_type == "compliance_cert":
            filepath = await report_generator_service.generate_compliance_certificate(
                request.model_data, request.report_data
            )
        elif request.report_type == "model_card":
            filepath = await report_generator_service.generate_model_card(
                request.model_data, request.report_data
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
            
        return {"success": True, "filepath": filepath, "filename": os.path.basename(filepath)}
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_report(filename: str):
    """Download a generated report"""
    filepath = os.path.join("uploads/reports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
        
    return FileResponse(
        path=filepath, 
        filename=filename, 
        media_type='application/pdf'
    )

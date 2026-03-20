"""
Report Generation API Routes

Endpoints for generating audit-ready reports in PDF and DOCX formats
with compliance documentation and bias evaluation summaries.
"""

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import io
import logging

from ..services.report_generator import (
    ReportGenerator,
    BiasReportData,
    EvaluationSummary,
    ComplianceStatus,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
logger = logging.getLogger(__name__)


# Request/Response Models
class EvaluationSummaryRequest(BaseModel):
    """Request model for evaluation summary data"""
    total_tests: int = Field(..., description="Total number of tests run")
    tests_passed: int = Field(..., description="Number of tests passed")
    tests_failed: int = Field(..., description="Number of tests failed")
    overall_bias_rate: float = Field(..., description="Overall bias rate as percentage")
    evaluation_time: float = Field(..., description="Time taken to run evaluation in seconds")


class ComplianceStatusRequest(BaseModel):
    """Request model for compliance status"""
    gdpr_compliant: bool = Field(..., description="GDPR compliance status")
    ai_act_compliant: bool = Field(..., description="EU AI Act compliance status")
    fairness_score: float = Field(..., description="Fairness score from 0-100")


class BiasEvaluationReportRequest(BaseModel):
    """Request model for bias evaluation report generation"""
    model_type: str = Field(..., description="Type of model (e.g., 'language_model', 'image_classifier')")
    model_description: str = Field(..., description="Description of the model")
    evaluation_summary: EvaluationSummaryRequest = Field(..., description="Summary of evaluation results")
    overall_risk: str = Field(..., description="Overall risk level: 'low', 'medium', 'high', or 'critical'")
    risk_factors: List[str] = Field(default_factory=list, description="List of identified risk factors")
    recommendations: List[str] = Field(default_factory=list, description="List of remediation recommendations")
    compliance_status: ComplianceStatusRequest = Field(..., description="Compliance status across frameworks")
    explainability_insights: Optional[Dict[str, Any]] = Field(None, description="Model explainability insights")


@router.post("/bias-evaluation/pdf", response_description="PDF report file")
async def generate_pdf_report(request: BiasEvaluationReportRequest = Body(...)):
    """
    Generate a PDF report for bias evaluation results.

    Returns a downloadable PDF with:
    - Executive summary with risk level indicators
    - Evaluation metrics and test results
    - Compliance status across regulatory frameworks
    - Risk factors and remediation recommendations
    - Report metadata and timestamp

    Args:
        request: Bias evaluation data including model info, test results, and compliance status

    Returns:
        Binary PDF file with Content-Type: application/pdf

    Example:
        ```json
        {
            "model_type": "language_model",
            "model_description": "BERT-based sentiment analysis model",
            "evaluation_summary": {
                "total_tests": 50,
                "tests_passed": 45,
                "tests_failed": 5,
                "overall_bias_rate": 10.0,
                "evaluation_time": 120.5
            },
            "overall_risk": "medium",
            "risk_factors": ["Gender bias in pronouns", "Ethnic bias in entity recognition"],
            "recommendations": ["Add diverse training data", "Implement fairness constraints"],
            "compliance_status": {
                "gdpr_compliant": true,
                "ai_act_compliant": true,
                "fairness_score": 75.5
            }
        }
        ```
    """
    try:
        # Convert request to domain model
        evaluation_summary = EvaluationSummary(
            total_tests=request.evaluation_summary.total_tests,
            tests_passed=request.evaluation_summary.tests_passed,
            tests_failed=request.evaluation_summary.tests_failed,
            overall_bias_rate=request.evaluation_summary.overall_bias_rate,
            evaluation_time=request.evaluation_summary.evaluation_time,
        )

        compliance_status = ComplianceStatus(
            gdpr_compliant=request.compliance_status.gdpr_compliant,
            ai_act_compliant=request.compliance_status.ai_act_compliant,
            fairness_score=request.compliance_status.fairness_score,
        )

        report_data = BiasReportData(
            timestamp=datetime.now().isoformat(),
            model_type=request.model_type,
            model_description=request.model_description,
            evaluation_summary=evaluation_summary,
            overall_risk=request.overall_risk,
            risk_factors=request.risk_factors,
            recommendations=request.recommendations,
            compliance_status=compliance_status,
            explainability_insights=request.explainability_insights or {},
        )

        # Generate PDF
        generator = ReportGenerator()
        pdf_bytes = generator.generate_pdf(report_data)

        # Create filename with timestamp
        filename = f"bias_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )


@router.post("/bias-evaluation/docx", response_description="DOCX report file")
async def generate_docx_report(request: BiasEvaluationReportRequest = Body(...)):
    """
    Generate a DOCX report for bias evaluation results.

    Returns a downloadable Word document with:
    - Executive summary with risk level color coding
    - Evaluation metrics and test results table
    - Compliance status across regulatory frameworks
    - Risk factors and remediation recommendations
    - Professional formatting and report metadata

    Args:
        request: Bias evaluation data including model info, test results, and compliance status

    Returns:
        Binary DOCX file with Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document

    Example:
        ```json
        {
            "model_type": "language_model",
            "model_description": "BERT-based sentiment analysis model",
            "evaluation_summary": {
                "total_tests": 50,
                "tests_passed": 45,
                "tests_failed": 5,
                "overall_bias_rate": 10.0,
                "evaluation_time": 120.5
            },
            "overall_risk": "medium",
            "risk_factors": ["Gender bias in pronouns", "Ethnic bias in entity recognition"],
            "recommendations": ["Add diverse training data", "Implement fairness constraints"],
            "compliance_status": {
                "gdpr_compliant": true,
                "ai_act_compliant": true,
                "fairness_score": 75.5
            }
        }
        ```
    """
    try:
        # Convert request to domain model
        evaluation_summary = EvaluationSummary(
            total_tests=request.evaluation_summary.total_tests,
            tests_passed=request.evaluation_summary.tests_passed,
            tests_failed=request.evaluation_summary.tests_failed,
            overall_bias_rate=request.evaluation_summary.overall_bias_rate,
            evaluation_time=request.evaluation_summary.evaluation_time,
        )

        compliance_status = ComplianceStatus(
            gdpr_compliant=request.compliance_status.gdpr_compliant,
            ai_act_compliant=request.compliance_status.ai_act_compliant,
            fairness_score=request.compliance_status.fairness_score,
        )

        report_data = BiasReportData(
            timestamp=datetime.now().isoformat(),
            model_type=request.model_type,
            model_description=request.model_description,
            evaluation_summary=evaluation_summary,
            overall_risk=request.overall_risk,
            risk_factors=request.risk_factors,
            recommendations=request.recommendations,
            compliance_status=compliance_status,
            explainability_insights=request.explainability_insights or {},
        )

        # Generate DOCX
        generator = ReportGenerator()
        docx_bytes = generator.generate_docx(report_data)

        # Create filename with timestamp
        filename = f"bias_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error generating DOCX report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate DOCX report: {str(e)}"
        )


@router.get("/formats")
async def get_supported_formats():
    """
    Get list of supported report formats.

    Returns:
        List of available report formats with descriptions
    """
    return {
        "formats": [
            {
                "id": "pdf",
                "name": "PDF Report",
                "description": "Professional PDF format with color-coded risk levels and audit-ready formatting",
                "endpoint": "/api/v1/reports/bias-evaluation/pdf",
                "content_type": "application/pdf"
            },
            {
                "id": "docx",
                "name": "Word Document",
                "description": "Editable Word format compatible with Microsoft Office and Google Docs",
                "endpoint": "/api/v1/reports/bias-evaluation/docx",
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        ]
    }

"""
Compliance Audit Engine Endpoints

Evaluates AI models against regulatory frameworks (EU AI Act, GDPR,
DPDP Act, ISO 42001, NIST AI RMF) and returns gap analysis with
severity ratings and actionable recommendations.
"""

import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.compliance_audit import (
    ComplianceAuditRequest,
    ComplianceAuditResponse,
    ComplianceGapResponse,
    FrameworkInfoResponse,
    FrameworkResultResponse,
)
from src.domain.compliance.services.compliance_audit_engine import (
    ComplianceAuditEngine,
)

logger = logging.getLogger("fairmind.compliance_audit")
router = APIRouter(prefix="/api/v1/compliance/audit", tags=["compliance-audit"])

_engine = ComplianceAuditEngine()


@router.post(
    "",
    response_model=ComplianceAuditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run compliance audit",
    description=(
        "Evaluate an AI model against one or more regulatory frameworks. "
        "Returns per-framework scores, compliance gaps, and recommendations."
    ),
)
async def run_compliance_audit(body: ComplianceAuditRequest) -> ComplianceAuditResponse:
    audit_id = str(uuid.uuid4())

    try:
        reports, _ = await _engine.run_audit(
            frameworks=[fw.value for fw in body.frameworks],
            risk_level=body.risk_level.value if body.risk_level else None,
            model_context=body.model_context,
        )

        report_dict = await _engine.generate_report(
            audit_id=audit_id,
            model_name=body.model_name,
            model_version=body.model_version,
            risk_level=body.risk_level.value if body.risk_level else None,
            reports=reports,
        )

        return ComplianceAuditResponse(
            audit_id=report_dict["audit_id"],
            model_name=report_dict["model_name"],
            model_version=report_dict.get("model_version"),
            overall_compliant=report_dict["overall_compliant"],
            overall_score=report_dict["overall_score"],
            risk_level=report_dict.get("risk_level"),
            framework_results=[
                FrameworkResultResponse(
                    framework=fr["framework"],
                    framework_name=fr["framework_name"],
                    compliant=fr["compliant"],
                    score=fr["score"],
                    checks_passed=fr["checks_passed"],
                    checks_total=fr["checks_total"],
                    gaps=[ComplianceGapResponse(**g) for g in fr["gaps"]],
                )
                for fr in report_dict["framework_results"]
            ],
            generated_at=report_dict["generated_at"],
        )
    except Exception as exc:
        logger.error(f"Compliance audit failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Compliance audit engine error",
        )


@router.get(
    "/frameworks",
    response_model=List[FrameworkInfoResponse],
    summary="List supported frameworks",
    description="Return metadata about all regulatory frameworks supported by the audit engine.",
)
async def list_supported_frameworks() -> List[FrameworkInfoResponse]:
    return [FrameworkInfoResponse(**fw) for fw in _engine.list_frameworks()]

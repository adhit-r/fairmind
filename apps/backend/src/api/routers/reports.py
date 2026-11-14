"""
Report Export API Routes

PDF and DOCX export of stored audit-report snapshots (ai-governance /reports).
Nothing is typeset from caller-posted content: the data is loaded server-side,
with the same organization scoping as GET /api/v1/ai-governance/reports/{id}.
"""

import hashlib

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from ..services.report_generator import generate_snapshot_docx, generate_snapshot_pdf
from .ai_governance import _require_report_access, _serialize_audit_report_row

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_active_user)],
)

_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_FORMATS = {"pdf": ("application/pdf", generate_snapshot_pdf), "docx": (_DOCX, generate_snapshot_docx)}


class StoredReportExport(BaseModel):
    """The only accepted body: a stored snapshot id. Any other field is rejected with 422."""

    model_config = ConfigDict(extra="forbid")
    report_id: str


def _export(report_id: str, fmt: str, current_user: TokenData, db: Session) -> Response:
    row = _require_report_access(db, report_id, current_user)  # 404 across organizations
    content_hash = hashlib.sha256((row.data_json or "").encode()).hexdigest()
    media_type, render = _FORMATS[fmt]
    return Response(
        render(_serialize_audit_report_row(row), content_hash),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=audit_report_{row.id}.{fmt}"},
    )


@router.get("/snapshots/{report_id}/pdf")
def export_snapshot_pdf(
    report_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _export(report_id, "pdf", current_user, db)


@router.get("/snapshots/{report_id}/docx")
def export_snapshot_docx(
    report_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _export(report_id, "docx", current_user, db)


@router.post("/bias-evaluation/pdf")
def generate_pdf_report(
    request: StoredReportExport,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _export(request.report_id, "pdf", current_user, db)


@router.post("/bias-evaluation/docx")
def generate_docx_report(
    request: StoredReportExport,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _export(request.report_id, "docx", current_user, db)


@router.get("/formats")
def get_supported_formats():
    """List supported export formats; both take a stored report snapshot id."""
    return {
        "formats": [
            {
                "id": "pdf",
                "name": "PDF Report",
                "description": "PDF export of a stored report snapshot",
                "endpoint": "/api/v1/reports/snapshots/{report_id}/pdf",
                "content_type": "application/pdf",
            },
            {
                "id": "docx",
                "name": "Word Document",
                "description": "Editable Word export of a stored report snapshot",
                "endpoint": "/api/v1/reports/snapshots/{report_id}/docx",
                "content_type": _DOCX,
            },
        ]
    }

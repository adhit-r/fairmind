"""HTTP boundary for uploading evaluation input artifacts (CSV or JSON)."""

from __future__ import annotations

from typing import Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from api.composition.evaluation_artifacts import build_evaluation_artifact_service
from api.routes.evaluation_workbench import (
    StrictModel,
    _missing,
    _require_assurance_v2_capability,
)
from config.settings import settings
from database.connection import get_db
from src.api.evaluation_permissions import (
    EVALUATION_ARTIFACT_UPLOAD_PERMISSION,
    require_evaluation_permission,
)
from src.api.routers.governance_assurance import organization_membership
from src.application.ports.evaluation_artifacts import ArtifactStoreError
from src.application.services.evaluation_artifact_service import (
    ArtifactUploadError,
    EvaluationArtifactService,
)
from src.application.services.governance_assurance_service import OrgMembership


def _require_artifact_upload_enabled() -> None:
    _require_assurance_v2_capability(
        settings.assurance_v2_artifact_upload_enabled,
        "Evaluation artifact upload is not enabled.",
    )


evaluation_artifacts_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-artifacts"],
    dependencies=[Depends(_require_artifact_upload_enabled)],
)


class EvaluationArtifactResponse(StrictModel):
    artifact_id: str = Field(alias="artifactId")
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    media_type: str = Field(alias="mediaType")
    size_bytes: int = Field(alias="sizeBytes")
    state: Literal["quarantined", "available"]
    scan_policy: str = Field(alias="scanPolicy")
    created_at: str = Field(alias="createdAt")
    available_at: str | None = Field(alias="availableAt")


_ERRORS: dict[str, tuple[int, str]] = {
    "unsupported_media_type": (415, "Upload text/csv or application/json."),
    "artifact_empty": (400, "The artifact is empty."),
    "artifact_too_large": (413, "The artifact exceeds the upload limit."),
    "artifact_rejected": (422, "The artifact was rejected by the input scan."),
    "artifact_store_unavailable": (503, "The artifact store is unavailable."),
    "artifact_not_found": (404, "artifact was not found in this scope."),
}


def _error(code: str, reason_code: str | None = None) -> HTTPException:
    status, message = _ERRORS[code]
    detail: dict[str, str] = {"code": code, "message": message}
    if reason_code is not None:
        detail["reasonCode"] = reason_code
    return HTTPException(status_code=status, detail=detail)


def get_evaluation_artifact_service_builder(
    db: Session = Depends(get_db),
) -> Callable[[], EvaluationArtifactService]:
    """Built only after authorization, so an unconfigured store never leaks first."""

    return lambda: build_evaluation_artifact_service(db)


async def _bounded_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise _error("artifact_too_large")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > limit:
            raise _error("artifact_too_large")
    return bytes(body)


@evaluation_artifacts_router.post(
    "/evaluation-v2/artifacts",
    status_code=201,
    response_model=EvaluationArtifactResponse,
    responses={200: {"model": EvaluationArtifactResponse}},
)
async def upload_evaluation_artifact(
    org_id: str,
    request: Request,
    membership: OrgMembership = Depends(organization_membership),
    build_service: Callable[[], EvaluationArtifactService] = Depends(
        get_evaluation_artifact_service_builder
    ),
):
    """Store one scanned input under its SHA-256. Replays return the same artifact."""

    require_evaluation_permission(membership, EVALUATION_ARTIFACT_UPLOAD_PERMISSION)
    if membership.org_id != org_id:
        _missing("organization")
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    data = await _bounded_body(request, settings.evaluation_artifact_max_bytes)

    def upload():
        return build_service().upload(
            organization_id=membership.org_id,
            actor_id=membership.user_id,
            media_type=media_type,
            data=data,
        )

    try:
        # Hashing, scanning, PostgreSQL and S3 calls all block: keep them off the loop.
        result = await run_in_threadpool(upload)
    except ArtifactStoreError:
        raise _error("artifact_store_unavailable") from None
    except ArtifactUploadError as error:
        raise _error(error.code, error.reason_code) from None
    record = result.record
    if record.state == "rejected":
        raise _error("artifact_rejected", record.rejection_reason)
    body = EvaluationArtifactResponse.model_validate(
        {
            "artifactId": record.artifact_id,
            "sha256": record.sha256,
            "mediaType": record.media_type,
            "sizeBytes": record.size_bytes,
            "state": record.state,
            "scanPolicy": record.scan_policy,
            "createdAt": record.created_at,
            "availableAt": record.available_at,
        }
    )
    return JSONResponse(
        status_code=201 if result.created else 200,
        content=body.model_dump(by_alias=True),
    )


router = evaluation_artifacts_router

__all__ = [
    "EvaluationArtifactResponse",
    "evaluation_artifacts_router",
    "get_evaluation_artifact_service_builder",
    "router",
]

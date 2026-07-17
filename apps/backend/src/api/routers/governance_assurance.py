"""Organization-scoped framework and control-assessment routes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.framework_catalog_service import FrameworkCatalogService
from src.application.services.governance_assurance_service import GovernanceAssuranceService, OrgMembership


router = APIRouter(prefix="/organizations/{org_id}", tags=["governance-assurance"])


class WorkspaceRequest(BaseModel):
    name: str = Field(min_length=1)
    owner: str | None = None


class SystemRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workspace_id: str = Field(alias="workspaceId", min_length=1)
    name: str = Field(min_length=1)
    owner: str | None = None


class FrameworkImportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workbook_path: str = Field(alias="workbookPath", min_length=1)


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    framework_version_id: str = Field(alias="frameworkVersionId", min_length=1)


class AssessmentUpdateRequest(BaseModel):
    status: str | None = None
    applicability: str | None = None
    owner: str | None = None


def organization_membership(
    org_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    membership = GovernanceAssuranceService(db).membership(org_id, current_user.user_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization membership required")
    return membership


def _service(db: Session) -> GovernanceAssuranceService:
    return GovernanceAssuranceService(db)


def _require_mutation(membership: OrgMembership, service: GovernanceAssuranceService) -> None:
    if not service.may_mutate(membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mutation permission required")


def _require_import(membership: OrgMembership, service: GovernanceAssuranceService) -> None:
    if not service.may_import(membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization admin permission required")


@router.get("/frameworks")
def list_frameworks(
    _membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> list[dict]:
    return _service(db).list_frameworks()


@router.post("/frameworks/import", status_code=status.HTTP_201_CREATED)
def import_framework(
    request: FrameworkImportRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_import(membership, service)
    path = Path(request.workbook_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found")
    return asdict(FrameworkCatalogService(db).import_workbook(path, membership.user_id))


@router.get("/frameworks/{framework_key}/versions")
def list_framework_versions(
    framework_key: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    return _service(db).list_versions(framework_key)


@router.get("/framework-versions/{version_id}/controls")
def list_framework_controls(
    version_id: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    controls = _service(db).list_controls(version_id)
    if controls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found")
    return controls


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    request: WorkspaceRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    return service.create_workspace(membership.org_id, request.name, request.owner)


@router.post("/systems", status_code=status.HTTP_201_CREATED)
def create_system(
    request: SystemRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    system = service.create_system(membership.org_id, request.workspace_id, request.name, request.owner)
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return system


@router.post("/systems/{system_id}/framework-assignments")
def assign_framework(
    system_id: str,
    request: AssignmentRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    service = _service(db)
    _require_mutation(membership, service)
    assignment, created = service.assign_framework(membership.org_id, system_id, request.framework_version_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System or framework version not found")
    return JSONResponse(assignment, status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@router.get("/systems/{system_id}/framework-assignments")
def list_system_assignments(
    system_id: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    assignments = _service(db).list_assignments(_membership.org_id, system_id)
    if assignments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    return assignments


@router.get("/framework-assignments/{assignment_id}/controls")
def list_assignment_controls(
    assignment_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    controls = _service(db).assignment_controls(membership.org_id, assignment_id)
    if controls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework assignment not found")
    return controls


@router.patch("/control-assessments/{assessment_id}")
def update_control_assessment(
    assessment_id: str,
    request: AssessmentUpdateRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    try:
        assessment = service.update_assessment(
            membership.org_id, assessment_id, request.model_dump(exclude_unset=True)
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control assessment not found")
    return assessment


@router.get("/framework-assignments/{assignment_id}/readiness")
def assignment_readiness(
    assignment_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    readiness = _service(db).readiness(membership.org_id, assignment_id)
    if readiness is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework assignment not found")
    return readiness

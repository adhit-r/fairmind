"""Tenant-scoped evaluation planning and evidence-link workflow."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any
import uuid

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationPlan,
    GovernanceEvaluationRun,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceWorkspace,
)
from database.models import OrganizationAuditLog
from src.domain.assurance.evidence_passport import CapabilityState, EvaluationStatus


TARGET_KINDS = frozenset(
    {
        "predictive_model",
        "llm_application",
        "agent",
        "code_generator",
        "image_generator",
        "audio_model",
        "video_model",
        "multimodal_system",
    }
)
LIFECYCLE_PHASES = frozenset({"pre_deploy", "realtime", "post_deploy"})
EXECUTION_DEPTHS = frozenset({"inline", "deep", "hybrid"})
ENFORCEMENT_MODES = frozenset({"advisory", "human_approval", "automatic"})
DELIVERY_MODES = frozenset({"fairmind_worker", "external_provider", "imported_report"})
RUN_TRIGGERS = frozenset(
    {"manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"}
)
SUITE_REF_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*@[A-Za-z0-9][A-Za-z0-9._-]*$"
)


class EvaluationWorkflowError(ValueError):
    """Stable workflow error rendered by the FastAPI boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        next_action: str,
        *,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.next_action = next_action
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "nextAction": self.next_action,
        }


def _error(
    code: str,
    message: str,
    next_action: str,
    status_code: int,
) -> EvaluationWorkflowError:
    return EvaluationWorkflowError(
        code,
        message,
        next_action,
        status_code=status_code,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize the framework-independent plan contract."""
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("name must contain 1 to 120 non-whitespace characters")

    target_kind = payload.get("targetKind")
    if target_kind not in TARGET_KINDS:
        raise ValueError("targetKind is not supported")

    lifecycle_phases = payload.get("lifecyclePhases")
    if (
        not isinstance(lifecycle_phases, list)
        or not 1 <= len(lifecycle_phases) <= 3
        or any(phase not in LIFECYCLE_PHASES for phase in lifecycle_phases)
        or len(set(lifecycle_phases)) != len(lifecycle_phases)
    ):
        raise ValueError("lifecyclePhases must contain one to three distinct supported phases")

    execution_depth = payload.get("executionDepth", "hybrid")
    if execution_depth not in EXECUTION_DEPTHS:
        raise ValueError("executionDepth is not supported")
    enforcement_mode = payload.get("enforcementMode", "human_approval")
    if enforcement_mode not in ENFORCEMENT_MODES:
        raise ValueError("enforcementMode is not supported")
    delivery_mode = payload.get("deliveryMode")
    if delivery_mode not in DELIVERY_MODES:
        raise ValueError("deliveryMode is not supported")

    suite_refs = payload.get("suiteRefs")
    if (
        not isinstance(suite_refs, list)
        or not 1 <= len(suite_refs) <= 32
        or len(set(suite_refs)) != len(suite_refs)
        or any(
            not isinstance(ref, str)
            or len(ref) > 160
            or SUITE_REF_PATTERN.fullmatch(ref) is None
            for ref in suite_refs
        )
    ):
        raise ValueError("suiteRefs must contain one to 32 distinct immutable suite references")

    return {
        "name": name.strip(),
        "targetKind": target_kind,
        "lifecyclePhases": list(lifecycle_phases),
        "executionDepth": execution_depth,
        "enforcementMode": enforcement_mode,
        "deliveryMode": delivery_mode,
        "suiteRefs": list(suite_refs),
    }


def validate_trigger(trigger: str) -> str:
    if trigger not in RUN_TRIGGERS:
        raise ValueError("trigger is not supported")
    return trigger


class EvaluationRunsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _system_scope(self, org_id: str, system_id: str):
        systems = GovernanceAISystem.__table__
        workspaces = GovernanceWorkspace.__table__
        return self.db.execute(
            select(
                systems.c.id.label("system_id"),
                systems.c.workspace_id,
                systems.c.org_id,
            )
            .select_from(
                systems.join(
                    workspaces,
                    (workspaces.c.id == systems.c.workspace_id)
                    & (workspaces.c.org_id == systems.c.org_id),
                )
            )
            .where(
                systems.c.id == system_id,
                systems.c.org_id == org_id,
                workspaces.c.id == systems.c.workspace_id,
                workspaces.c.org_id == org_id,
            )
        ).mappings().one_or_none()

    @staticmethod
    def _plan_dict(row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "orgId": row["org_id"],
            "workspaceId": row["workspace_id"],
            "systemId": row["system_id"],
            "name": row["name"],
            "targetKind": row["target_kind"],
            "lifecyclePhases": json.loads(row["lifecycle_phases_json"]),
            "executionDepth": row["execution_depth"],
            "enforcementMode": row["enforcement_mode"],
            "deliveryMode": row["delivery_mode"],
            "suiteRefs": json.loads(row["suite_refs_json"]),
            "status": row["status"],
            "createdBy": row["created_by"],
            "updatedBy": row["updated_by"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    @staticmethod
    def _run_dict(row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "orgId": row["org_id"],
            "workspaceId": row["workspace_id"],
            "systemId": row["system_id"],
            "planId": row["plan_id"],
            "trigger": row["trigger"],
            "technicalStatus": row["technical_status"],
            "overallVerdict": row["overall_verdict"],
            "layerVerdicts": json.loads(row["layer_verdicts_json"]),
            "linkedEvidenceRunId": row["linked_evidence_run_id"],
            "linkedPassportRevisionId": row["linked_passport_revision_id"],
            "linkedBy": row["linked_by"],
            "linkedAt": row["linked_at"],
            "requestedBy": row["requested_by"],
            "startedAt": row["started_at"],
            "completedAt": row["completed_at"],
            "failureCode": row["failure_code"],
            "failureMessage": row["failure_message"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _plan_row(self, *, org_id: str, system_id: str, workspace_id: str, plan_id: str):
        plans = GovernanceEvaluationPlan.__table__
        return self.db.execute(
            select(plans).where(
                plans.c.id == plan_id,
                plans.c.org_id == org_id,
                plans.c.workspace_id == workspace_id,
                plans.c.system_id == system_id,
            )
        ).mappings().one_or_none()

    def _run_row(self, *, org_id: str, system_id: str, workspace_id: str, run_id: str):
        runs = GovernanceEvaluationRun.__table__
        return self.db.execute(
            select(runs).where(
                runs.c.id == run_id,
                runs.c.org_id == org_id,
                runs.c.workspace_id == workspace_id,
                runs.c.system_id == system_id,
            )
        ).mappings().one_or_none()

    def _write_audit(
        self,
        *,
        org_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        changes: dict[str, Any],
    ) -> None:
        self.db.execute(
            insert(OrganizationAuditLog.__table__).values(
                id=uuid.uuid4(),
                org_id=uuid.UUID(org_id),
                user_id=uuid.UUID(actor_id),
                action=action,
                resource_type=resource_type,
                resource_id=uuid.UUID(resource_id),
                changes=changes,
                status="success",
            )
        )

    def _persistence_failure(self) -> EvaluationWorkflowError:
        return _error(
            "evaluation_persistence_failed",
            "The evaluation workflow change could not be persisted atomically.",
            "Retry the request. If it continues to fail, contact an administrator.",
            500,
        )

    def create_plan(
        self,
        *,
        org_id: str,
        system_id: str,
        actor_id: str,
        payload: dict,
    ) -> dict:
        normalized = validate_plan_payload(payload)
        try:
            scope = self._system_scope(org_id, system_id)
            if scope is None:
                raise _error(
                    "passport_scope_mismatch",
                    "The selected AI system is not in this organization scope.",
                    "Select an AI system in the current organization and workspace.",
                    404,
                )
            plan_id = str(uuid.uuid4())
            now = _now()
            self.db.execute(
                insert(GovernanceEvaluationPlan.__table__).values(
                    id=plan_id,
                    org_id=org_id,
                    workspace_id=scope["workspace_id"],
                    system_id=system_id,
                    name=normalized["name"],
                    target_kind=normalized["targetKind"],
                    lifecycle_phases_json=_canonical_json(normalized["lifecyclePhases"]),
                    execution_depth=normalized["executionDepth"],
                    enforcement_mode=normalized["enforcementMode"],
                    delivery_mode=normalized["deliveryMode"],
                    suite_refs_json=_canonical_json(normalized["suiteRefs"]),
                    status="draft",
                    created_by=actor_id,
                    updated_by=actor_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._write_audit(
                org_id=org_id,
                actor_id=actor_id,
                action="evaluation_plan.created",
                resource_type="evaluation_plan",
                resource_id=plan_id,
                changes={"systemId": system_id, "status": "draft"},
            )
            response = self._plan_dict(
                self._plan_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    plan_id=plan_id,
                )
            )
            self.db.commit()
            return response
        except EvaluationWorkflowError:
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise self._persistence_failure() from error

    def list_plans(self, *, org_id: str, system_id: str) -> list[dict] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        plans = GovernanceEvaluationPlan.__table__
        rows = self.db.execute(
            select(plans)
            .where(
                plans.c.org_id == org_id,
                plans.c.workspace_id == scope["workspace_id"],
                plans.c.system_id == system_id,
            )
            .order_by(plans.c.created_at.desc(), plans.c.id.desc())
        ).mappings().all()
        return [self._plan_dict(row) for row in rows]

    def activate_plan(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        actor_id: str,
    ) -> dict | None:
        try:
            scope = self._system_scope(org_id, system_id)
            if scope is None:
                return None
            row = self._plan_row(
                org_id=org_id,
                system_id=system_id,
                workspace_id=scope["workspace_id"],
                plan_id=plan_id,
            )
            if row is None:
                return None
            if row["status"] == "archived":
                raise _error(
                    "plan_archived",
                    "Archived evaluation plans cannot be activated.",
                    "Create a new versioned plan instead of reopening an archived plan.",
                    409,
                )
            if row["status"] == "active":
                return self._plan_dict(row)

            now = _now()
            result = self.db.execute(
                update(GovernanceEvaluationPlan.__table__)
                .where(
                    GovernanceEvaluationPlan.id == plan_id,
                    GovernanceEvaluationPlan.org_id == org_id,
                    GovernanceEvaluationPlan.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationPlan.system_id == system_id,
                    GovernanceEvaluationPlan.status == "draft",
                )
                .values(status="active", updated_by=actor_id, updated_at=now)
            )
            if result.rowcount != 1:
                self.db.rollback()
                refreshed = self._plan_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    plan_id=plan_id,
                )
                if refreshed and refreshed["status"] == "active":
                    return self._plan_dict(refreshed)
                raise _error(
                    "plan_archived",
                    "The evaluation plan is no longer activatable.",
                    "Refresh the plan and create a new version if it was archived.",
                    409,
                )
            self._write_audit(
                org_id=org_id,
                actor_id=actor_id,
                action="evaluation_plan.activated",
                resource_type="evaluation_plan",
                resource_id=plan_id,
                changes={"from": "draft", "to": "active"},
            )
            response = self._plan_dict(
                self._plan_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    plan_id=plan_id,
                )
            )
            self.db.commit()
            return response
        except EvaluationWorkflowError:
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise self._persistence_failure() from error

    def preflight(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
    ) -> dict | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        plan = self._plan_row(
            org_id=org_id,
            system_id=system_id,
            workspace_id=scope["workspace_id"],
            plan_id=plan_id,
        )
        if plan is None:
            return None
        if plan["delivery_mode"] == "fairmind_worker":
            return {
                "planId": plan_id,
                "canPrepareRun": False,
                "fairmindExecutionAvailable": False,
                "code": "executor_unavailable",
                "message": "No FairMind worker is installed for this plan.",
                "nextAction": (
                    "Select an external provider or imported report, or install a compatible worker."
                ),
            }
        if plan["status"] == "draft":
            return {
                "planId": plan_id,
                "canPrepareRun": False,
                "fairmindExecutionAvailable": False,
                "code": "evidence_link_required",
                "message": "This evaluation plan is still a draft and cannot prepare runs.",
                "nextAction": "Activate the plan before preparing a run.",
            }
        if plan["status"] == "archived":
            return {
                "planId": plan_id,
                "canPrepareRun": False,
                "fairmindExecutionAvailable": False,
                "code": "evidence_link_required",
                "message": "This evaluation plan is archived and cannot prepare runs.",
                "nextAction": (
                    "Create and activate a new versioned plan before preparing a run."
                ),
            }
        return {
            "planId": plan_id,
            "canPrepareRun": True,
            "fairmindExecutionAvailable": False,
            "code": "evidence_link_required",
            "message": "This plan requires evidence from its configured delivery source.",
            "nextAction": "Prepare the run, then link an exact Evidence Passport revision.",
        }

    def create_run(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        actor_id: str,
        trigger: str,
    ) -> dict:
        validate_trigger(trigger)
        try:
            scope = self._system_scope(org_id, system_id)
            if scope is None:
                raise _error(
                    "passport_scope_mismatch",
                    "The selected evaluation plan is not in this organization scope.",
                    "Select a plan from the current AI system.",
                    404,
                )
            plan = self._plan_row(
                org_id=org_id,
                system_id=system_id,
                workspace_id=scope["workspace_id"],
                plan_id=plan_id,
            )
            if plan is None:
                raise _error(
                    "passport_scope_mismatch",
                    "The selected evaluation plan was not found.",
                    "Refresh the plan list and select an available plan.",
                    404,
                )
            if plan["status"] != "active":
                raise _error(
                    "plan_inactive",
                    "Only an active evaluation plan can prepare a run.",
                    "Activate the plan before preparing a run.",
                    409,
                )
            if plan["delivery_mode"] == "fairmind_worker":
                raise _error(
                    "executor_unavailable",
                    "No FairMind worker is installed for this plan.",
                    "Select an external provider or imported report, or install a compatible worker.",
                    409,
                )

            run_id = str(uuid.uuid4())
            now = _now()
            self.db.execute(
                insert(GovernanceEvaluationRun.__table__).values(
                    id=run_id,
                    org_id=org_id,
                    workspace_id=scope["workspace_id"],
                    system_id=system_id,
                    plan_id=plan_id,
                    trigger=trigger,
                    technical_status="awaiting_evidence",
                    overall_verdict="insufficient",
                    layer_verdicts_json="{}",
                    requested_by=actor_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._write_audit(
                org_id=org_id,
                actor_id=actor_id,
                action="evaluation_run.prepared",
                resource_type="evaluation_run",
                resource_id=run_id,
                changes={"planId": plan_id, "technicalStatus": "awaiting_evidence"},
            )
            response = self._run_dict(
                self._run_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    run_id=run_id,
                )
            )
            self.db.commit()
            return response
        except EvaluationWorkflowError:
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise self._persistence_failure() from error

    def list_runs(self, *, org_id: str, system_id: str) -> list[dict] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        runs = GovernanceEvaluationRun.__table__
        rows = self.db.execute(
            select(runs)
            .where(
                runs.c.org_id == org_id,
                runs.c.workspace_id == scope["workspace_id"],
                runs.c.system_id == system_id,
            )
            .order_by(runs.c.created_at.desc(), runs.c.id.desc())
        ).mappings().all()
        return [self._run_dict(row) for row in rows]

    def get_run(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
    ) -> dict | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        row = self._run_row(
            org_id=org_id,
            system_id=system_id,
            workspace_id=scope["workspace_id"],
            run_id=run_id,
        )
        return self._run_dict(row) if row else None

    @staticmethod
    def _passport_projection(snapshot_json: str) -> dict[str, str | None]:
        try:
            snapshot = json.loads(snapshot_json)
            if not isinstance(snapshot, dict):
                raise ValueError
            schema_version = snapshot["schemaVersion"]
            ai_system = snapshot["aiSystem"]
            evaluation = snapshot["evaluation"]
            suite = evaluation["suite"]
            result = evaluation["result"]
            capability_state = CapabilityState(evaluation["capabilityState"]).value
            result_status = EvaluationStatus(result["status"]).value
            expected_status = {
                CapabilityState.UNAVAILABLE.value: EvaluationStatus.UNAVAILABLE.value,
                CapabilityState.INSUFFICIENT_DATA.value: (
                    EvaluationStatus.INSUFFICIENT_DATA.value
                ),
            }.get(capability_state)
            if expected_status is not None and result_status != expected_status:
                raise ValueError
            projection = {
                "schemaVersion": schema_version,
                "targetKind": ai_system["kind"],
                "suiteRef": f"{suite['name']}@{suite['version']}",
                "capabilityState": capability_state,
                "resultStatus": result_status,
                "resultSummary": result["summary"],
                "errorCode": result.get("errorCode"),
                "errorMessage": result.get("errorMessage"),
                "startedAt": result["startedAt"],
                "endedAt": result["endedAt"],
            }
            required_keys = {
                "schemaVersion",
                "targetKind",
                "suiteRef",
                "capabilityState",
                "resultStatus",
                "resultSummary",
                "startedAt",
                "endedAt",
            }
            if any(
                not isinstance(projection[key], str) or not projection[key]
                for key in required_keys
            ):
                raise ValueError
            if any(
                value is not None and (not isinstance(value, str) or not value)
                for value in (projection["errorCode"], projection["errorMessage"])
            ):
                raise ValueError
            if schema_version != "1.0.0":
                raise ValueError
            return projection
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise _error(
                "passport_snapshot_invalid",
                "The stored Evidence Passport snapshot is invalid for exact linking.",
                "Re-ingest a valid canonical Evidence Passport revision.",
                500,
            ) from error

    @staticmethod
    def _passport_run_outcome(passport: dict[str, str | None]) -> dict[str, str | None]:
        result_status = passport["resultStatus"]
        completed_outcomes = {
            EvaluationStatus.PASSED.value,
            EvaluationStatus.PASSED_WITH_LIMITATIONS.value,
            EvaluationStatus.FAILED.value,
            EvaluationStatus.INFORMATIONAL.value,
        }
        if result_status in completed_outcomes:
            return {
                "technicalStatus": "succeeded",
                "overallVerdict": "review",
                "failureCode": None,
                "failureMessage": None,
            }
        return {
            "technicalStatus": "failed",
            "overallVerdict": "insufficient",
            "failureCode": passport["errorCode"] or f"passport_result_{result_status}",
            "failureMessage": passport["errorMessage"] or passport["resultSummary"],
        }

    def link_passport_revision(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
        evidence_run_id: str,
        passport_revision_id: str,
        actor_id: str,
    ) -> dict | None:
        try:
            scope = self._system_scope(org_id, system_id)
            if scope is None:
                return None
            run = self._run_row(
                org_id=org_id,
                system_id=system_id,
                workspace_id=scope["workspace_id"],
                run_id=run_id,
            )
            if run is None:
                return None
            if run["linked_passport_revision_id"] is not None:
                if (
                    run["linked_evidence_run_id"] == evidence_run_id
                    and run["linked_passport_revision_id"] == passport_revision_id
                ):
                    return self._run_dict(run)
                raise _error(
                    "passport_link_conflict",
                    "This evaluation run is already linked to a different Passport revision.",
                    "Create a separately audited replacement workflow to change the evidence link.",
                    409,
                )

            plans = GovernanceEvaluationPlan.__table__
            plan = self.db.execute(
                select(plans).where(
                    plans.c.id == run["plan_id"],
                    plans.c.org_id == org_id,
                    plans.c.workspace_id == scope["workspace_id"],
                    plans.c.system_id == system_id,
                )
            ).mappings().one_or_none()
            if plan is None:
                raise _error(
                    "passport_scope_mismatch",
                    "The evaluation run's immutable plan scope is unavailable.",
                    "Refresh the run and verify its organization, workspace, and system.",
                    422,
                )

            revisions = GovernanceEvidencePassportRevision.__table__
            evidence_runs = GovernanceEvidenceRun.__table__
            revision = self.db.execute(
                select(revisions.c.snapshot_json)
                .select_from(
                    revisions.join(
                        evidence_runs,
                        (evidence_runs.c.id == revisions.c.evidence_run_id)
                        & (evidence_runs.c.org_id == revisions.c.org_id)
                        & (evidence_runs.c.system_id == revisions.c.system_id),
                    )
                )
                .where(
                    revisions.c.id == passport_revision_id,
                    revisions.c.evidence_run_id == evidence_run_id,
                    revisions.c.org_id == org_id,
                    revisions.c.system_id == system_id,
                    evidence_runs.c.id == evidence_run_id,
                    evidence_runs.c.org_id == org_id,
                    evidence_runs.c.workspace_id == scope["workspace_id"],
                    evidence_runs.c.system_id == system_id,
                )
            ).mappings().one_or_none()
            if revision is None:
                raise _error(
                    "passport_scope_mismatch",
                    "The exact Evidence Passport revision is outside this run's scope.",
                    "Select a revision from the same organization, workspace, system, and evidence run.",
                    422,
                )

            passport = self._passport_projection(revision["snapshot_json"])
            target_kind = plan["target_kind"]
            expected_passport_kind = {
                "predictive_model": "model",
                "agent": "agent",
            }.get(target_kind)
            if expected_passport_kind is None:
                raise _error(
                    "target_kind_unverifiable",
                    "Evidence Passport 1.0 cannot explicitly bind this evaluation target kind.",
                    "Keep the run awaiting evidence until a versioned Passport contract supports this modality.",
                    422,
                )
            if passport["targetKind"] != expected_passport_kind:
                raise _error(
                    "target_kind_mismatch",
                    "The Passport AI system kind does not match the evaluation plan target.",
                    "Select a Passport with the exact verifiable target kind.",
                    422,
                )
            if passport["suiteRef"] not in json.loads(plan["suite_refs_json"]):
                raise _error(
                    "suite_mismatch",
                    "The Passport suite name and version do not match this plan.",
                    "Select a Passport whose exact suite name@version appears in the immutable plan.",
                    422,
                )

            outcome = self._passport_run_outcome(passport)
            linked_at = _now()
            result = self.db.execute(
                update(GovernanceEvaluationRun.__table__)
                .where(
                    GovernanceEvaluationRun.id == run_id,
                    GovernanceEvaluationRun.org_id == org_id,
                    GovernanceEvaluationRun.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationRun.system_id == system_id,
                    GovernanceEvaluationRun.technical_status == "awaiting_evidence",
                    GovernanceEvaluationRun.linked_evidence_run_id.is_(None),
                    GovernanceEvaluationRun.linked_passport_revision_id.is_(None),
                )
                .values(
                    linked_evidence_run_id=evidence_run_id,
                    linked_passport_revision_id=passport_revision_id,
                    linked_by=actor_id,
                    linked_at=linked_at,
                    started_at=passport["startedAt"],
                    completed_at=passport["endedAt"],
                    technical_status=outcome["technicalStatus"],
                    overall_verdict=outcome["overallVerdict"],
                    failure_code=outcome["failureCode"],
                    failure_message=outcome["failureMessage"],
                    updated_at=linked_at,
                )
            )
            if result.rowcount != 1:
                self.db.rollback()
                winner = self._run_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    run_id=run_id,
                )
                if winner and (
                    winner["linked_evidence_run_id"] == evidence_run_id
                    and winner["linked_passport_revision_id"] == passport_revision_id
                ):
                    return self._run_dict(winner)
                raise _error(
                    "passport_link_conflict",
                    "Another exact Passport revision already won the link operation.",
                    "Refresh the run before attempting a replacement workflow.",
                    409,
                )
            self._write_audit(
                org_id=org_id,
                actor_id=actor_id,
                action="evaluation_run.passport_linked",
                resource_type="evaluation_run",
                resource_id=run_id,
                changes={
                    "evidenceRunId": evidence_run_id,
                    "passportRevisionId": passport_revision_id,
                },
            )
            response = self._run_dict(
                self._run_row(
                    org_id=org_id,
                    system_id=system_id,
                    workspace_id=scope["workspace_id"],
                    run_id=run_id,
                )
            )
            self.db.commit()
            return response
        except EvaluationWorkflowError:
            self.db.rollback()
            raise
        except Exception as error:
            self.db.rollback()
            raise self._persistence_failure() from error

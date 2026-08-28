"""
FairMind-E environmental governance service.

The domain engine stays framework-agnostic. This module owns ingestion,
versioned persistence, governance-evidence mirroring, and the approval gate.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, timezone
from typing import Any, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.environmental import (
    EnvironmentalAssessment,
    EnvironmentalEngineResult,
    get_thresholds,
    run_assessment,
)
from src.domain.environmental.controls import CONTROLS

ENV_EVIDENCE_TYPE = "environmental_impact"
ENV_FRAMEWORK = "environmental_governance"
PROFILE_VERSION = "0.2.0"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "normalized_payload"):
        return value.normalized_payload()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError("assessment must be a mapping or EnvironmentalAssessment")


def _normalise_payload(raw: Any, *, system_id: str | None = None) -> dict[str, Any]:
    payload = _as_mapping(raw)
    if system_id:
        payload["system_id"] = system_id

    metrics = payload.get("metrics") or {}
    if hasattr(metrics, "model_dump"):
        metrics = metrics.model_dump(mode="json")
    metrics = dict(metrics)

    if metrics.get("total_kg_co2e_location") is None and metrics.get("total_kg_co2e") is not None:
        metrics["total_kg_co2e_location"] = metrics["total_kg_co2e"]
    if metrics.get("total_kg_co2e_market") is None and metrics.get("total_kg_co2e") is not None:
        metrics["total_kg_co2e_market"] = metrics["total_kg_co2e"]
    if metrics.get("kg_co2e_per_1000_requests") is None and metrics.get("kg_co2e_per_1k_requests") is not None:
        metrics["kg_co2e_per_1000_requests"] = metrics["kg_co2e_per_1k_requests"]
    if metrics.get("kg_co2e_per_1k_requests") is None and metrics.get("kg_co2e_per_1000_requests") is not None:
        metrics["kg_co2e_per_1k_requests"] = metrics["kg_co2e_per_1000_requests"]
    if (
        metrics.get("location_carbon_intensity_g_co2e_per_kwh") is None
        and metrics.get("carbon_intensity_gco2e_kwh") is not None
    ):
        metrics["location_carbon_intensity_g_co2e_per_kwh"] = metrics["carbon_intensity_gco2e_kwh"]

    payload["metrics"] = metrics
    if not payload.get("measurement_source") and payload.get("source"):
        payload["measurement_source"] = payload["source"]

    # Validate and apply the domain schema's compatibility mapping.
    return EnvironmentalAssessment(**payload).normalized_payload()


def evaluate_assessment(raw: Any, *, system_id: str | None = None) -> tuple[dict[str, Any], EnvironmentalEngineResult]:
    assessment = _normalise_payload(raw, system_id=system_id)
    result = run_assessment(assessment)
    assessment.update(
        {
            "confidence_score": result.confidence_score,
            "evidence_confidence": result.evidence_confidence,
            "provenance_class": result.provenance_class,
            "risk_tier": result.risk_tier,
            "impact_tier": result.impact_tier,
            "recommendation": result.recommendation,
            "mitigation_readiness": result.mitigation_readiness,
        }
    )
    return assessment, result


def _control_rows(coverage: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "code": control.code,
            "name": control.name,
            "status": coverage.get(control.code, "missing"),
            "governanceTest": control.governance_test,
            "optional": control.optional,
        }
        for control in CONTROLS
    ]


def _blockers(result: EnvironmentalEngineResult) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if result.recommendation == "no_go":
        items.append(
            {
                "code": "environmental_no_go",
                "severity": "high",
                "message": "Latest environmental assessment is no_go.",
            }
        )
    if result.mitigation_blocking:
        items.append(
            {
                "code": "environmental_mitigation_missing",
                "severity": "medium",
                "message": "conditional_go requires documented mitigation or a valid exception.",
            }
        )
    return items


def seed_env_controls(db: Session) -> int:
    """Idempotently seed ENV-1..ENV-6 into governance_framework_controls."""
    inserted = 0
    for control in CONTROLS:
        exists = db.execute(
            text(
                "SELECT id FROM governance_framework_controls "
                "WHERE framework = :framework AND control_id = :control_id"
            ),
            {"framework": ENV_FRAMEWORK, "control_id": control.code},
        ).fetchone()
        if exists:
            continue
        now = _now_iso()
        db.execute(
            text(
                "INSERT INTO governance_framework_controls "
                "(id, framework, control_id, title, description, status, evidence_required, created_at, updated_at) "
                "VALUES (:id, :framework, :control_id, :title, :description, :status, :evidence_required, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "framework": ENV_FRAMEWORK,
                "control_id": control.code,
                "title": control.name,
                "description": control.governance_test,
                "status": "not_started",
                "evidence_required": 0 if control.optional else 1,
                "created_at": now,
                "updated_at": now,
            },
        )
        inserted += 1
    if inserted:
        db.commit()
    return inserted


def benchmark_thresholds() -> dict[str, Any]:
    return {"provisional": True, "thresholds": get_thresholds()}


def control_definitions() -> list[dict[str, Any]]:
    return [
        {
            "code": control.code,
            "name": control.name,
            "governance_test": control.governance_test,
            "optional": control.optional,
        }
        for control in CONTROLS
    ]


def controls_payload(
    db: Session,
    system_id: str | None = None,
    *,
    org_id: str | None = None,
) -> dict[str, Any]:
    cov = None
    if system_id:
        latest = get_latest_env_assessment(db, system_id, org_id=org_id)
        if latest is not None:
            cov = latest.get("coverage") or (latest.get("result") or {}).get("coverage")
    return {"controls": control_definitions(), "coverage": cov}


def _next_version(db: Session, org_id: str, system_id: str) -> int:
    row = db.execute(
        text(
            "SELECT COALESCE(MAX(version), 0) AS current_version "
            "FROM governance_environmental_assessments "
            "WHERE org_id = :org_id AND system_id = :system_id"
        ),
        {"org_id": org_id, "system_id": system_id},
    ).fetchone()
    return int((row.current_version if row else 0) or 0) + 1


def resolve_system_org(
    db: Session,
    system_id: str,
    *,
    org_id: str | None = None,
) -> str:
    """Resolve an immutable tenant binding or fail closed."""
    row = db.execute(
        text("SELECT org_id FROM governance_ai_systems WHERE id = :id"),
        {"id": system_id},
    ).fetchone()
    if row is None or not row[0]:
        raise LookupError(f"AI system '{system_id}' was not found")
    resolved_org_id = str(row[0])
    if org_id is not None and resolved_org_id != str(org_id):
        raise LookupError(f"AI system '{system_id}' was not found")
    return resolved_org_id


def _payload_for_storage(
    assessment: Mapping[str, Any],
    result: EnvironmentalEngineResult,
    *,
    assessment_id: str,
    evidence_id: str,
    version: int,
) -> dict[str, Any]:
    return {
        "profile_version": PROFILE_VERSION,
        "generated_at": _now_iso(),
        "assessment_id": assessment_id,
        "evidence_id": evidence_id,
        "version": version,
        "assessment": dict(assessment),
        "result": result.to_dict(),
        "controls": _control_rows(result.coverage),
        "blockers": _blockers(result),
    }


def _create_risk_and_task(
    db: Session,
    *,
    system_id: str,
    assessment_id: str,
    result: EnvironmentalEngineResult,
) -> tuple[str | None, str | None]:
    if not result.approval_blocking:
        return None, None

    now = _now_iso()
    severity = "high" if result.recommendation == "no_go" else "medium"
    risk_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_risks "
            "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
            "VALUES (:id, :system_id, :title, :severity, :status, :description, :mitigation, :likelihood, :risk_score, :source, :categories_json, :metadata_json, :created_at, :updated_at)"
        ),
        {
            "id": risk_id,
            "system_id": system_id,
            "title": "Environmental release gate blocked",
            "severity": severity,
            "status": "open",
            "description": (
                f"FairMind-E recommendation is {result.recommendation} with "
                f"{result.impact_tier} impact and {result.confidence_score:.2f} confidence."
            ),
            "mitigation": "Provide higher quality evidence, documented mitigation, or a valid exception.",
            "likelihood": "possible",
            "risk_score": 85.0 if severity == "high" else 60.0,
            "source": ENV_EVIDENCE_TYPE,
            "categories_json": _json_dumps(["environmental", "release_gate"]),
            "metadata_json": _json_dumps(
                {
                    "assessment_id": assessment_id,
                    "recommendation": result.recommendation,
                    "coverage": result.coverage,
                }
            ),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.execute(
        text(
            "INSERT INTO governance_remediation_tasks "
            "(id, system_id, title, description, source_type, source_id, linked_risk_ids_json, priority, status, retest_required, retest_status, notes, created_at, updated_at) "
            "VALUES (:id, :system_id, :title, :description, :source_type, :source_id, :linked_risk_ids_json, :priority, :status, :retest_required, :retest_status, :notes, :created_at, :updated_at)"
        ),
        {
            "id": task_id,
            "system_id": system_id,
            "title": "Resolve environmental gate blocker",
            "description": "Attach measured or tool-estimated evidence and document mitigation before release approval.",
            "source_type": "environmental_assessment",
            "source_id": assessment_id,
            "linked_risk_ids_json": _json_dumps([risk_id]),
            "priority": "high" if severity == "high" else "medium",
            "status": "open",
            "retest_required": 1,
            "retest_status": "not_started",
            "notes": "Created by FairMind-E assessment ingestion.",
            "created_at": now,
            "updated_at": now,
        },
    )
    return risk_id, task_id


def save_assessment(
    db: Session,
    system_id: str,
    assessment_input: Any,
    *,
    org_id: str | None = None,
    uploaded_by: Optional[str] = None,
) -> dict[str, Any]:
    """Evaluate, append, and mirror one environmental assessment."""
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)

    assessment, result = evaluate_assessment(assessment_input, system_id=system_id)
    version = _next_version(db, resolved_org_id, system_id)
    assessment_id = str(uuid.uuid4())
    evidence_id = str(uuid.uuid4())
    evidence_refs = list(assessment.get("evidence_refs_json") or [])
    evidence_refs.append(f"governance_evidence:{evidence_id}")
    assessment["evidence_refs_json"] = evidence_refs

    payload = _payload_for_storage(
        assessment,
        result,
        assessment_id=assessment_id,
        evidence_id=evidence_id,
        version=version,
    )
    now = _now_iso()
    metrics = assessment.get("metrics") or {}
    blockers = _blockers(result)

    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, org_id, system_id, control_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :org_id, :system_id, :control_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "org_id": resolved_org_id,
            "system_id": system_id,
            "control_id": "ENV-5",
            "evidence_type": ENV_EVIDENCE_TYPE,
            "title": f"Environmental impact assessment v{version} - {result.recommendation}",
            "source": str(assessment.get("measurement_source") or assessment.get("source") or "unknown"),
            "content_json": _json_dumps(payload),
            "confidence": result.confidence_score,
            "status": "accepted",
            "uploaded_by": uploaded_by,
            "metadata_json": _json_dumps(
                {
                    "assessment_id": assessment_id,
                    "version": version,
                    "impact_tier": result.impact_tier,
                    "recommendation": result.recommendation,
                    "coverage_rate": result.coverage_rate,
                    "approval_blocking": result.approval_blocking,
                }
            ),
            "captured_at": now,
            "created_at": now,
        },
    )
    db.execute(
        text(
            "INSERT INTO governance_environmental_assessments "
            "(id, org_id, system_id, evidence_id, version, boundary_json, period_start, period_end, lifecycle_phase, functional_unit, impact_type, total_kwh, total_kg_co2e_location, total_kg_co2e_market, kg_co2e_per_1000_requests, kg_co2e_per_1m_tokens, measurement_source, provenance_class, uncertainty_pct, confidence_score, intensity_vs_baseline, risk_tier, recommendation, mitigation_readiness, mitigations_json, evidence_refs_json, controls_json, blockers_json, reviewer_state, exception_json, payload_json, created_at) "
            "VALUES (:id, :org_id, :system_id, :evidence_id, :version, :boundary_json, :period_start, :period_end, :lifecycle_phase, :functional_unit, :impact_type, :total_kwh, :total_kg_co2e_location, :total_kg_co2e_market, :kg_co2e_per_1000_requests, :kg_co2e_per_1m_tokens, :measurement_source, :provenance_class, :uncertainty_pct, :confidence_score, :intensity_vs_baseline, :risk_tier, :recommendation, :mitigation_readiness, :mitigations_json, :evidence_refs_json, :controls_json, :blockers_json, :reviewer_state, :exception_json, :payload_json, :created_at)"
        ),
        {
            "id": assessment_id,
            "org_id": resolved_org_id,
            "system_id": system_id,
            "evidence_id": evidence_id,
            "version": version,
            "boundary_json": _json_dumps(assessment.get("boundary_json") or {}),
            "period_start": assessment.get("period_start"),
            "period_end": assessment.get("period_end"),
            "lifecycle_phase": assessment.get("lifecycle_phase") or "inference",
            "functional_unit": assessment.get("functional_unit") or "1000_requests",
            "impact_type": assessment.get("impact_type") or "carbon",
            "total_kwh": _to_float(metrics.get("total_kwh")),
            "total_kg_co2e_location": _to_float(metrics.get("total_kg_co2e_location")),
            "total_kg_co2e_market": _to_float(metrics.get("total_kg_co2e_market")),
            "kg_co2e_per_1000_requests": _to_float(metrics.get("kg_co2e_per_1000_requests")),
            "kg_co2e_per_1m_tokens": _to_float(metrics.get("kg_co2e_per_1m_tokens")),
            "measurement_source": str(assessment.get("measurement_source") or "unknown"),
            "provenance_class": result.provenance_class,
            "uncertainty_pct": _to_float(assessment.get("uncertainty_pct")),
            "confidence_score": result.confidence_score,
            "intensity_vs_baseline": _to_float(assessment.get("intensity_vs_baseline")),
            "risk_tier": result.risk_tier,
            "recommendation": result.recommendation,
            "mitigation_readiness": result.mitigation_readiness,
            "mitigations_json": _json_dumps(assessment.get("mitigations_json") or []),
            "evidence_refs_json": _json_dumps(evidence_refs),
            "controls_json": _json_dumps(result.coverage),
            "blockers_json": _json_dumps(blockers),
            "reviewer_state": assessment.get("reviewer_state") or "draft",
            "exception_json": _json_dumps(assessment.get("exception") or {}),
            "payload_json": _json_dumps(payload),
            "created_at": now,
        },
    )
    risk_id, remediation_task_id = _create_risk_and_task(
        db,
        system_id=system_id,
        assessment_id=assessment_id,
        result=result,
    )
    db.commit()

    latest = get_latest_env_assessment(db, system_id, org_id=resolved_org_id)
    return {
        "assessmentId": assessment_id,
        "evidenceId": evidence_id,
        "version": version,
        "recommendation": result.recommendation,
        "impactTier": result.impact_tier,
        "riskTier": result.risk_tier,
        "confidenceScore": result.confidence_score,
        "confidenceBand": result.confidence_band,
        "mitigationBlocking": result.mitigation_blocking,
        "approvalBlocking": result.approval_blocking,
        "coverageRate": result.coverage_rate,
        "controls": _control_rows(result.coverage),
        "blockers": blockers,
        "riskId": risk_id,
        "remediationTaskId": remediation_task_id,
        "latest": latest,
        "versionTrail": get_env_assessment_history(db, system_id, org_id=resolved_org_id),
        "warnings": result.warnings,
    }


def _row_to_dict(row: Any) -> dict[str, Any]:
    payload = _json_loads(row.payload_json, {})
    assessment = payload.get("assessment") or {}
    result = payload.get("result") or {}
    controls = _control_rows(result.get("coverage", _json_loads(row.controls_json, {})))
    return {
        "id": row.id,
        "assessmentId": row.id,
        "orgId": row.org_id,
        "systemId": row.system_id,
        "system_id": row.system_id,
        "evidenceId": row.evidence_id,
        "version": row.version,
        "createdAt": row.created_at,
        "created_at": row.created_at,
        "lifecyclePhase": row.lifecycle_phase,
        "functionalUnit": row.functional_unit,
        "impactType": row.impact_type,
        "metrics": assessment.get("metrics", {}),
        "measurementSource": row.measurement_source,
        "provenanceClass": row.provenance_class,
        "uncertaintyPct": row.uncertainty_pct,
        "confidenceScore": row.confidence_score,
        "confidenceBand": result.get("confidence_band"),
        "intensityVsBaseline": row.intensity_vs_baseline,
        "riskTier": row.risk_tier,
        "impactTier": result.get("impact_tier", row.risk_tier),
        "recommendation": row.recommendation,
        "mitigationReadiness": row.mitigation_readiness,
        "reviewerState": row.reviewer_state,
        "exception": _json_loads(row.exception_json, {}),
        "assessment": assessment,
        "result": result,
        "controls": controls,
        "coverage": result.get("coverage", _json_loads(row.controls_json, {})),
        "coverageRate": result.get("coverage_rate", 0.0),
        "blockers": _json_loads(row.blockers_json, []),
        "evidenceRefs": _json_loads(row.evidence_refs_json, []),
        "profileVersion": payload.get("profile_version", PROFILE_VERSION),
    }


def get_latest_env_assessment(
    db: Session,
    system_id: str,
    *,
    org_id: str | None = None,
) -> Optional[dict[str, Any]]:
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    row = db.execute(
        text(
            "SELECT * FROM governance_environmental_assessments "
            "WHERE org_id = :org_id AND system_id = :system_id "
            "ORDER BY version DESC LIMIT 1"
        ),
        {"org_id": resolved_org_id, "system_id": system_id},
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_env_assessment_history(
    db: Session,
    system_id: str,
    *,
    org_id: str | None = None,
) -> list[dict[str, Any]]:
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    rows = db.execute(
        text(
            "SELECT * FROM governance_environmental_assessments "
            "WHERE org_id = :org_id AND system_id = :system_id ORDER BY version DESC"
        ),
        {"org_id": resolved_org_id, "system_id": system_id},
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_assessment_by_id(
    db: Session,
    system_id: str,
    assessment_id: str,
    *,
    org_id: str | None = None,
) -> Optional[dict[str, Any]]:
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    row = db.execute(
        text(
            "SELECT * FROM governance_environmental_assessments "
            "WHERE id = :id AND org_id = :org_id AND system_id = :system_id"
        ),
        {"id": assessment_id, "org_id": resolved_org_id, "system_id": system_id},
    ).fetchone()
    return _row_to_dict(row) if row else None


def update_mitigation(
    db: Session,
    system_id: str,
    assessment_id: str,
    mitigation: Mapping[str, Any],
    *,
    org_id: str | None = None,
    uploaded_by: str | None = None,
) -> Optional[dict[str, Any]]:
    """Append a mitigation by creating a new assessment version."""
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    current = get_assessment_by_id(
        db,
        system_id,
        assessment_id,
        org_id=resolved_org_id,
    )
    if current is None:
        return None
    assessment = dict(current.get("assessment") or {})
    mitigations = list(assessment.get("mitigations_json") or [])
    mitigations.append(dict(mitigation))
    assessment["mitigations_json"] = mitigations
    assessment["mitigation_readiness"] = "documented"
    return save_assessment(
        db,
        system_id,
        assessment,
        org_id=resolved_org_id,
        uploaded_by=uploaded_by,
    ).get("latest")


def _valid_exception(exception: Any) -> bool:
    if not isinstance(exception, Mapping):
        return False
    if not (exception.get("owner") and exception.get("expiry") and exception.get("rationale")):
        return False
    try:
        expiry = date.fromisoformat(str(exception["expiry"]))
    except ValueError:
        return False
    return expiry >= date.today()


def env_gate_status(
    db: Session,
    system_id: str,
    *,
    org_id: str | None = None,
) -> dict[str, Any]:
    """Environmental release-gate status for approval decisions."""
    row = db.execute(
        text("SELECT org_id FROM governance_ai_systems WHERE id = :id"),
        {"id": system_id},
    ).fetchone()
    if row is None:
        return {
            "blocked": False,
            "code": "system_not_registered",
            "reason": "",
            "recommendation": None,
            "assessmentId": None,
        }
    if not row[0] or (org_id is not None and str(row[0]) != str(org_id)):
        return {
            "blocked": True,
            "code": "system_scope_unavailable",
            "reason": "Environmental approval requires an organization-bound AI system.",
            "recommendation": "no_go",
            "assessmentId": None,
        }
    resolved_org_id = str(row[0])

    latest = get_latest_env_assessment(db, system_id, org_id=resolved_org_id)
    if latest is None:
        return {
            "blocked": True,
            "code": "missing_environmental_evidence",
            "reason": "Environmental impact evidence is required before AI system approval.",
            "recommendation": "no_go",
            "assessmentId": None,
        }

    reco = latest.get("recommendation") or "no_go"
    base = {
        "recommendation": reco,
        "impactTier": latest.get("impactTier"),
        "confidenceScore": latest.get("confidenceScore"),
        "assessmentId": latest.get("assessmentId"),
        "version": latest.get("version"),
    }
    if reco == "no_go":
        return {
            **base,
            "blocked": True,
            "code": "environmental_no_go",
            "reason": "Latest environmental impact assessment is no_go.",
        }
    if reco == "conditional_go":
        result = latest.get("result") or {}
        if (
            latest.get("mitigationReadiness") != "documented"
            and not result.get("has_dated_mitigation")
            and not _valid_exception(latest.get("exception"))
        ):
            return {
                **base,
                "blocked": True,
                "code": "environmental_mitigation_required",
                "reason": "conditional_go requires documented mitigation or a valid owner/expiry/rationale exception.",
            }
    return {**base, "blocked": False, "code": "pass", "reason": ""}


def mark_assessment_reviewed(
    db: Session,
    system_id: str,
    assessment_id: str,
    *,
    org_id: str | None = None,
    reviewer: str,
    attestation: str = "",
) -> Optional[dict[str, Any]]:
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    row = db.execute(
        text(
            "SELECT * FROM governance_environmental_assessments "
            "WHERE id = :id AND org_id = :org_id AND system_id = :system_id"
        ),
        {"id": assessment_id, "org_id": resolved_org_id, "system_id": system_id},
    ).fetchone()
    if row is None:
        return None

    payload = _json_loads(row.payload_json, {})
    payload["review"] = {
        "reviewer": reviewer,
        "attestation": attestation,
        "reviewed_at": _now_iso(),
    }
    payload_json = _json_dumps(payload)
    db.execute(
        text(
            "UPDATE governance_environmental_assessments "
            "SET payload_json = :payload_json, reviewer_state = :reviewer_state "
            "WHERE id = :id AND org_id = :org_id AND system_id = :system_id"
        ),
        {
            "payload_json": payload_json,
            "reviewer_state": "accepted",
            "id": assessment_id,
            "org_id": resolved_org_id,
            "system_id": system_id,
        },
    )
    if row.evidence_id:
        db.execute(
            text(
                "UPDATE governance_evidence "
                "SET status = :status, uploaded_by = COALESCE(uploaded_by, :uploaded_by) "
                "WHERE id = :id AND org_id = :org_id AND system_id = :system_id"
            ),
            {
                "status": "accepted",
                "uploaded_by": reviewer,
                "id": row.evidence_id,
                "org_id": resolved_org_id,
                "system_id": system_id,
            },
        )
    db.commit()
    return get_assessment_by_id(
        db,
        system_id,
        assessment_id,
        org_id=resolved_org_id,
    )


def build_csrd_export(assessment_record: Mapping[str, Any]) -> dict[str, Any]:
    assessment = assessment_record.get("assessment", {})
    result = assessment_record.get("result", {})
    metrics = assessment.get("metrics", {})
    return {
        "standard": "ESRS E1 (Climate change)",
        "disclosure_generated_at": _now_iso(),
        "assessment_id": assessment_record.get("assessmentId"),
        "boundary": assessment.get("boundary_json") or assessment.get("boundary"),
        "lifecycle_phase": assessment.get("lifecycle_phase"),
        "functional_unit": assessment.get("functional_unit"),
        "E1_5_energy_consumption_kwh": metrics.get("total_kwh"),
        "E1_5_renewable_energy_share_pct": metrics.get("energy_renewable_pct"),
        "E1_6_gross_ghg_emissions_location_kg_co2e": metrics.get("total_kg_co2e_location"),
        "E1_6_gross_ghg_emissions_market_kg_co2e": metrics.get("total_kg_co2e_market"),
        "E1_6_ghg_intensity_per_1m_tokens": metrics.get("kg_co2e_per_1m_tokens"),
        "E1_6_ghg_intensity_per_1000_requests": metrics.get("kg_co2e_per_1000_requests"),
        "location_carbon_intensity_g_co2e_per_kwh": metrics.get("location_carbon_intensity_g_co2e_per_kwh"),
        "market_carbon_intensity_g_co2e_per_kwh": metrics.get("market_carbon_intensity_g_co2e_per_kwh"),
        "embodied_carbon_kg_co2e": metrics.get("embodied_kg_co2e"),
        "water_use_litres": metrics.get("water_litres"),
        "measurement_source": assessment.get("measurement_source"),
        "provenance_class": result.get("provenance_class"),
        "evidence_confidence": result.get("evidence_confidence"),
        "confidence_band": result.get("confidence_band"),
        "impact_tier": result.get("impact_tier"),
        "governance_recommendation": result.get("recommendation"),
        "targets_and_mitigations": assessment.get("mitigations_json", []),
        "control_coverage": result.get("coverage", {}),
        "assumptions": (assessment.get("boundary_json") or {}).get("assumptions"),
    }


def _parse_json_or_csv(content: Any) -> Any:
    if isinstance(content, (Mapping, list)):
        return content
    if content is None:
        return {}
    text = str(content).strip()
    if not text:
        return {}
    if text.startswith("{") or text.startswith("["):
        return json.loads(text)
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def _first_record(parsed: Any) -> dict[str, Any]:
    if isinstance(parsed, list):
        return dict(parsed[0]) if parsed else {}
    if isinstance(parsed, Mapping):
        return dict(parsed)
    return {}


def _metric(record: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _to_float(record.get(key))
        if value is not None:
            return value
    return None


def fetch_connector_url(url: str) -> Any:
    """Fail closed until URL ingestion is mediated by a restricted fetch broker."""
    del url
    raise ValueError(
        "URL connector ingestion is disabled; upload evidence content directly"
    )


def normalize_connector_payload(connector_type: str, content: Any) -> dict[str, Any]:
    """Normalize supported file/export formats into an assessment fragment."""
    parsed = _parse_json_or_csv(content)
    record = _first_record(parsed)
    kind = connector_type.strip().lower().replace("-", "_").replace(" ", "_")

    base: dict[str, Any] = {
        "measurement_source": kind,
        "provenance_class": "tool_estimated",
        "uncertainty_pct": 20.0,
        "metrics": {},
    }

    if kind in {"codecarbon", "codecarbon_csv", "codecarbon_json"}:
        base["measurement_source"] = "codecarbon"
        base["metrics"] = {
            "total_kwh": _metric(record, "energy_consumed", "energy_kwh", "total_kwh"),
            "total_kg_co2e_location": _metric(record, "emissions", "emissions_kg", "co2e_kg"),
            "total_kg_co2e_market": _metric(record, "emissions", "emissions_kg", "co2e_kg"),
        }
        return base

    if kind in {"ecologits", "ecologits_json"}:
        base["measurement_source"] = "ecologits"
        base["metrics"] = {
            "total_kwh": _metric(record, "energy_kwh", "energy_consumption_kwh", "total_energy_kwh"),
            "total_kg_co2e_location": _metric(record, "co2e_kg", "kg_co2e", "emissions_kg"),
            "total_kg_co2e_market": _metric(record, "co2e_kg", "kg_co2e", "emissions_kg"),
            "kg_co2e_per_1m_tokens": _metric(record, "kg_co2e_per_1m_tokens"),
        }
        return base

    if kind in {"cloud_billing", "cloud_billing_csv", "aws_billing", "gcp_billing", "azure_billing"}:
        base["measurement_source"] = kind
        base["provenance_class"] = "vendor_reported"
        base["uncertainty_pct"] = 30.0
        base["metrics"] = {
            "total_kwh": _metric(record, "total_kwh", "kwh", "energy_kwh"),
            "total_kg_co2e_location": _metric(record, "total_kg_co2e_location", "location_kg_co2e", "kg_co2e"),
            "total_kg_co2e_market": _metric(record, "total_kg_co2e_market", "market_kg_co2e", "kg_co2e_market"),
            "kg_co2e_per_1000_requests": _metric(record, "kg_co2e_per_1000_requests", "kg_co2e_per_1k_requests"),
        }
        return base

    if kind in {"boavizta", "boavizta_json"}:
        base["measurement_source"] = "boavizta"
        base["impact_type"] = "embodied"
        base["metrics"] = {
            "embodied_kg_co2e": _metric(record, "embodied_kg_co2e", "gwp_embodied", "manufacture"),
            "total_kg_co2e_location": _metric(record, "use_kg_co2e", "gwp_use", "use"),
            "total_kg_co2e_market": _metric(record, "use_kg_co2e", "gwp_use", "use"),
        }
        return base

    raise ValueError(f"Unsupported environmental evidence connector '{connector_type}'")


def _deep_merge_assessment(base: dict[str, Any], overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = dict(base)
    overrides = dict(overrides or {})
    metrics = dict(merged.get("metrics") or {})
    metrics.update(overrides.pop("metrics", {}) or {})
    merged.update(overrides)
    merged["metrics"] = {k: v for k, v in metrics.items() if v is not None}
    return merged


def ingest_environmental_evidence(
    db: Session,
    system_id: str,
    *,
    org_id: str | None = None,
    connector_type: str,
    content: Any = None,
    url: str | None = None,
    assessment_overrides: Mapping[str, Any] | None = None,
    uploaded_by: str | None = None,
) -> dict[str, Any]:
    resolved_org_id = resolve_system_org(db, system_id, org_id=org_id)
    if url:
        content = fetch_connector_url(url)
    fragment = normalize_connector_payload(connector_type, content)
    assessment = _deep_merge_assessment(fragment, assessment_overrides)
    return save_assessment(
        db,
        system_id,
        assessment,
        org_id=resolved_org_id,
        uploaded_by=uploaded_by,
    )

"""Build the reviewable source set for a single-system assurance report."""

import json
import math
from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.evidence_pack_service import manifest_digest
from src.application.services.governance_assurance_service import CATALOGUE_RUN_SCHEMA, GovernanceAssuranceService, _is_stale

REPORT_TYPE = "system-assurance"
TEMPLATE_VERSION = 1


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def report_revision(title: str, config: dict, data: dict, narrative: str | None) -> str:
    return manifest_digest({"version": 2, "title": title, "config": config, "data": data, "narrative": narrative})


def _source_measurements(run) -> dict:
    provenance = json.loads(run.provenance_json or "{}")
    evaluation = provenance.get("evaluation", {})
    result = evaluation.get("result", {})
    scope = evaluation.get("scope", {})
    metrics = result.get("metrics", [])
    if run.schema_version == CATALOGUE_RUN_SCHEMA and run.catalogue_content:
        catalogue = json.loads(run.catalogue_content)
        metrics = [{"name": name, "value": value} for name, value in (catalogue.get("metrics") or {}).items()
                   if type(value) in (int, float) and (not isinstance(value, float) or math.isfinite(value))]
    return {
        "assuranceSource": run.assurance_source, "sampleCount": scope.get("sampleCount"),
        "scopeExclusions": scope.get("exclusions", []), "measurements": metrics,
        "thresholds": evaluation.get("thresholds", []), "capabilityState": run.capability_state,
        "suiteName": evaluation.get("suite", {}).get("name") or provenance.get("suite_name"),
        "suiteVersion": evaluation.get("suite", {}).get("version") or provenance.get("suite_version"),
        "subjectVersion": evaluation.get("subject", {}).get("version") or provenance.get("subject_version"),
        "runnerVersion": evaluation.get("evaluator", {}).get("runnerVersion") or provenance.get("runner_version"),
    }


def build_system_assurance_report(
    db: Session, *, org_id: str, system_id: str, assignment_id: str,
    date_from: date, date_to: date, generated_at: str,
) -> tuple[str, dict, dict] | None:
    scope = {"org": org_id, "sid": system_id, "assignment": assignment_id}
    row = db.execute(text(
        "SELECT s.name AS system_name, s.version, s.owner, s.risk_tier, s.lifecycle_stage, "
        "v.id AS version_id, v.framework_key, v.name AS framework_name, v.version_label "
        "FROM governance_framework_assignments a "
        "JOIN governance_ai_systems s ON s.id = a.system_id AND s.org_id = a.org_id "
        "JOIN governance_framework_versions v ON v.id = a.framework_version_id "
        "WHERE a.id = :assignment AND a.org_id = :org AND a.system_id = :sid"
    ), scope).one_or_none()
    if row is None:
        return None

    control_rows = db.execute(text(
        "SELECT a.id, a.applicability, a.status, a.owner, a.justification, d.external_id, d.title, d.frequency "
        "FROM governance_control_assessments a JOIN governance_control_definitions d ON d.id = a.control_definition_id "
        "WHERE a.framework_assignment_id = :assignment AND a.org_id = :org AND a.system_id = :sid "
        "AND d.framework_version_id = :version AND d.active = 1 ORDER BY d.external_id, a.id"
    ), {**scope, "version": row.version_id}).all()
    controls_by_id = {control.id: control for control in control_rows}
    service = GovernanceAssuranceService(db)
    runs = db.execute(text(
        "SELECT r.id, r.captured_at, r.expires_at, r.schema_version, r.assurance_source, r.capability_state, "
        "r.provenance_json, e.content_json AS catalogue_content FROM governance_evidence_runs r "
        "LEFT JOIN governance_evidence e ON r.schema_version = :catalogue_schema "
        "AND e.id = r.evidence_id AND e.system_id = r.system_id AND e.org_id = r.org_id "
        "WHERE r.org_id = :org AND r.system_id = :sid ORDER BY r.id"
    ), {**scope, "catalogue_schema": CATALOGUE_RUN_SCHEMA}).all()
    mapped_runs = set(db.execute(text(
        "SELECT DISTINCT m.evidence_id FROM governance_control_evidence m "
        "JOIN governance_control_assessments a ON a.id = m.control_assessment_id "
        "JOIN governance_control_definitions d ON d.id = a.control_definition_id "
        "WHERE a.framework_assignment_id = :assignment AND a.org_id = :org AND a.system_id = :sid "
        "AND m.org_id = a.org_id AND m.system_id = a.system_id AND d.framework_version_id = :version AND d.active = 1"
    ), {**scope, "version": row.version_id}).scalars())

    as_of = datetime.fromisoformat(generated_at)
    evidence = []
    accepted_by_control: dict[str, list[bool]] = {}
    excluded_undated = 0
    excluded_unmapped = 0
    for run in runs:
        captured = _timestamp(run.captured_at) if run.captured_at and len(run.captured_at) > 10 else None
        if captured is None:
            excluded_undated += 1
            continue
        if not date_from <= captured.date() <= date_to:
            continue
        if run.id not in mapped_runs:
            excluded_unmapped += 1
            continue

        detail = service._evidence_run(run.id)
        mappings = sorted(
            (mapping for mapping in detail["candidateMappings"] if mapping["controlAssessmentId"] in controls_by_id),
            key=lambda mapping: mapping["id"],
        )
        expires = _timestamp(run.expires_at)
        detail.update(_source_measurements(run), candidateMappings=mappings, expiresAt=run.expires_at,
                      stale=expires is not None and expires <= as_of)
        evidence.append((captured, detail))
        for mapping in mappings:
            if mapping["state"] == "accepted" and mapping["relation"] == "supports" and detail["result"] == "passed":
                control = controls_by_id[mapping["controlAssessmentId"]]
                stale = detail["stale"] or _is_stale(run.captured_at, control.frequency, as_of=as_of)
                accepted_by_control.setdefault(control.id, []).append(stale)

    evidence.sort(key=lambda item: (item[0], item[1]["id"]), reverse=True)
    controls = []
    for control in control_rows:
        accepted = accepted_by_control.get(control.id, [])
        controls.append({
            "id": control.id, "externalId": control.external_id, "title": control.title,
            "applicability": control.applicability, "status": control.status, "owner": control.owner,
            "justification": control.justification, "acceptedEvidenceCount": len(accepted),
            "evidenceStatus": "missing" if not accepted else "stale" if all(accepted) else "current",
        })

    findings = []
    for finding in db.execute(text(
        "SELECT id, title, severity, status, created_at FROM governance_risks "
        "WHERE system_id = :sid AND status NOT IN ('accepted', 'closed', 'resolved', 'mitigated') "
        "ORDER BY risk_score DESC, id"
    ), scope):
        created = _timestamp(finding.created_at)
        if created is not None and date_from <= created.date() <= date_to:
            findings.append({"id": finding.id, "title": finding.title, "severity": finding.severity,
                             "status": finding.status, "createdAt": finding.created_at})

    period = {"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat(), "timeZone": "UTC"}
    config = {"templateVersion": TEMPLATE_VERSION, "assignmentId": assignment_id,
              "frameworkVersionId": row.version_id, "frameworks": [row.framework_name], **period}
    limitations = [
        "The evidence period includes both UTC dates and uses the capture time of each run.",
        "Only runs mapped to a control of the selected assignment contribute evidence. Policy checks and unmapped artifacts are outside this population.",
        "System and control status, mapping reviews and evidence freshness reflect the state at preview time. Historical status at the end of the period is unavailable.",
        "Evidence freshness uses the recorded expiration and control frequency. Release eligibility requires a separate decision.",
        "Sample sizes, measurements and thresholds are shown when their source recorded them in a supported form.",
        "Findings were opened on the selected system during this period. Their current status is shown as system context without an assignment attribution.",
    ]
    if not evidence:
        limitations.append("No evidence runs with a valid capture time and a mapping to the selected assignment were recorded in the period.")
    data = {
        "system": {"id": system_id, "name": row.system_name, "version": row.version, "owner": row.owner,
                   "riskTier": row.risk_tier, "lifecycleStage": row.lifecycle_stage},
        "framework": {"assignmentId": assignment_id, "versionId": row.version_id, "key": row.framework_key,
                      "name": row.framework_name, "versionLabel": row.version_label},
        "period": period, "controls": controls, "evidence": [detail for _, detail in evidence], "findings": findings,
        "coverage": {"evidenceRuns": len(evidence), "controls": len(controls), "excludedUnmappedRuns": excluded_unmapped,
                     "excludedUndatedRuns": excluded_undated},
        "limitations": limitations, "generatedAt": generated_at,
    }
    return f"System Assurance Report · {row.system_name}", config, data

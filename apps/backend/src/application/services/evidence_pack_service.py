"""Inspection packs: a hashed manifest an auditor can verify offline.

The manifest freezes, per system, the release gate, the clause map for the chosen
frameworks, every evidence record with the fields its hash covers, and every decision seal
with the gate it saw and the approver's notes, its control applicability decisions (the
Statement of Applicability), risk register, remediation tasks and evidence links; and, for the
organisation, the plan attestations people made for organisation-level controls, the done
workflow runs, and the AI policies with their version history. Canonical form:
``json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()``;
from version 2 every float with an integral value is written as an integer first, so a pack
re-saved by a browser (``JSON.stringify`` writes 0.0 as 0) still verifies.
``manifest_hash`` is its SHA-256. The chain head of each system is recomputed from its
entries with the same fold as ``decision_seal_service.chain_head``, and each entry's hash
from its fields with ``decision_seal_service.entry_hash``.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.clause_map_service import CATALOGUE_PATH, _csv_cell as _csv_text, clause_map
from src.application.services.decision_seal_service import chain_head, entry_hash, evidence_records, list_seals

MANIFEST_VERSION = 2
SHARE_TTL = timedelta(days=30)


def _integral_floats_as_ints(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _integral_floats_as_ints(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_integral_floats_as_ints(v) for v in value]
    return value


def canonical_bytes(manifest: Dict[str, Any]) -> bytes:
    # Version 1 packs were hashed before the integer rule; they keep their own form.
    value = _integral_floats_as_ints(manifest) if manifest.get("version", 1) >= 2 else manifest
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def manifest_digest(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def _rows(db: Session, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]


# Per system: the Statement of Applicability (every assessed control, included or excluded, with the reason),
# accepted reviewer mappings per control, the risk register, remediation and evidence links. Deterministic order.
_SOA_SQL = (
    "SELECT v.framework_key AS framework, v.version_label AS version, d.external_id AS control, d.title, "
    "a.applicability, a.justification, a.status, a.owner, a.updated_at, "
    "(SELECT string_agg(m.artifact_evidence_id, ',' ORDER BY m.artifact_evidence_id) FROM governance_control_evidence m "
    " WHERE m.control_assessment_id = a.id AND m.state = 'accepted') AS accepted_evidence "
    "FROM governance_control_assessments a "
    "JOIN governance_control_definitions d ON d.id = a.control_definition_id "
    "JOIN governance_framework_assignments f ON f.id = a.framework_assignment_id "
    "JOIN governance_framework_versions v ON v.id = f.framework_version_id "
    "WHERE a.system_id = :id AND a.org_id = :org ORDER BY v.framework_key, v.version_label, d.external_id"
)
_RISKS_SQL = (
    "SELECT id, title, severity, likelihood, risk_score, status, mitigation, source, created_at, updated_at "
    "FROM governance_risks WHERE system_id = :id ORDER BY created_at, id"
)
_REMEDIATION_SQL = (
    "SELECT id, title, owner, priority, status, due_date, linked_risk_ids_json, retest_status, created_at, updated_at "
    "FROM governance_remediation_tasks WHERE system_id = :id ORDER BY created_at, id"
)
_LINKS_SQL = (
    "SELECT l.id, l.evidence_id, l.entity_type, l.entity_id, l.created_at FROM governance_evidence_links l "
    "JOIN governance_evidence e ON e.id = l.evidence_id WHERE e.system_id = :id ORDER BY l.created_at, l.id"
)
# Organisation: done workflow runs a reviewer did not reject (the rule packs._org_coverage uses), and policies.
_WORKFLOWS_SQL = (
    "SELECT r.id, r.workflow_id, r.workflow_version, r.ai_system_id, r.finished_at, a.status AS approval "
    "FROM workflow_runs r LEFT JOIN governance_approval_requests a ON a.id = r.approval_request_id "
    "WHERE r.org_id = :org AND r.status = 'done' AND (a.status IS NULL OR a.status <> 'rejected') "
    "ORDER BY r.finished_at, r.id"
)
_POLICIES_SQL = (
    "SELECT id, name, framework, description, status, version, owner, reviewer, approver, approved_at, created_at, updated_at "
    "FROM governance_policies WHERE org_id = :org ORDER BY created_at, id"
)
_POLICY_VERSIONS_SQL = (
    "SELECT v.policy_id, v.version, v.status, v.description, v.changed_by, v.change_summary, v.created_at "
    "FROM governance_policy_versions v JOIN governance_policies p ON p.id = v.policy_id "
    "WHERE p.org_id = :org ORDER BY v.policy_id, v.version, v.created_at"
)


@lru_cache(maxsize=1)
def _workflows() -> Dict[str, Dict[str, Any]]:
    return {w["id"]: w for w in json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))["workflows"]}


def _organisation(db: Session, org_id: str) -> Dict[str, Any]:
    params = {"org": org_id}
    workflows = _rows(db, _WORKFLOWS_SQL, params)
    for run in workflows:
        workflow = _workflows().get(run["workflow_id"]) or {}
        run.update(name=workflow.get("name"), common_control=workflow.get("commonControl"))
    versions: Dict[str, List[Dict[str, Any]]] = {}
    for row in _rows(db, _POLICY_VERSIONS_SQL, params):
        versions.setdefault(row.pop("policy_id"), []).append(row)
    return {
        "attestations": _rows(
            db, "SELECT task_key, statement, reference, attested_by, created_at FROM plan_attestations WHERE org_id = :org ORDER BY created_at", params
        ),
        "workflows": workflows,
        "policies": [{**p, "versions": versions.get(p["id"], [])} for p in _rows(db, _POLICIES_SQL, params)],
    }


def _risks(db: Session, system_id: str, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The risk register, each risk with the latest treatment decision recorded for it (risk_acceptance evidence), or None.
    An acceptance names both people, who proposed it and who approved it; a mitigation and older acceptances carry None for both."""
    decisions: Dict[str, Dict[str, Any]] = {}
    for entry in entries:  # oldest first, so the latest decision wins
        if entry["type"] == "risk_acceptance":
            content = json.loads(entry["content"]) if isinstance(entry["content"], str) else entry["content"]
            decisions[content["riskId"]] = {k: content.get(k) for k in ("decision", "rationale", "owner", "decidedBy", "decidedAt", "proposedBy", "approvedBy")}
    return [{**risk, "decision": decisions.get(risk["id"])} for risk in _rows(db, _RISKS_SQL, {"id": system_id})]


def build_manifest(
    db: Session, *, org_id: str, title: str, frameworks: List[str], systems: List[Dict[str, Any]], created_by: Optional[str]
) -> Dict[str, Any]:
    """systems: [{"id", "name", "riskTier", "gate"}], gate being the release gate payload."""
    out: List[Dict[str, Any]] = []
    for system in systems:
        gate = system["gate"]
        entries = evidence_records(db, system["id"])
        seals = [
            {
                **{k: seal[k] for k in ("id", "decisionId", "decision", "chainHead", "evidenceCount", "gate", "sealedBy", "createdAt", "verification")},
                "notes": db.execute(text("SELECT notes FROM governance_approval_decisions WHERE id = :id"), {"id": seal["decisionId"]}).scalar(),
            }
            for seal in list_seals(db, system["id"])
        ]
        out.append({
            "system": {"id": system["id"], "name": system["name"], "riskTier": system["riskTier"]},
            "gate": {k: gate.get(k) for k in ("verdict", "confidence", "checks", "reasons")},
            "clauseMap": clause_map(gate, frameworks=frameworks),
            "evidence": entries,
            "chainHead": chain_head(entries),
            "seals": seals,
            "controlApplicability": [
                {**row, "accepted_evidence": row["accepted_evidence"].split(",") if row["accepted_evidence"] else []}
                for row in _rows(db, _SOA_SQL, {"id": system["id"], "org": org_id})
            ],
            "risks": _risks(db, system["id"], entries),
            "remediation": _rows(db, _REMEDIATION_SQL, {"id": system["id"]}),
            "controlLinks": _rows(db, _LINKS_SQL, {"id": system["id"]}),
        })
    return {
        "version": MANIFEST_VERSION,
        "title": title,
        "organisation": _organisation(db, org_id),
        "frameworks": frameworks,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "createdBy": created_by,
        "systems": out,
    }


_CSV_SYSTEM_SECTIONS = ("evidence", "seals", "controlApplicability", "risks", "remediation", "controlLinks")


def _flat(row: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, dict):
            out.update(_flat(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return _csv_text(value) if isinstance(value, str) else value


def manifest_csv(manifest: Dict[str, Any]) -> str:
    """The pack as one CSV, a row per record with a section column, read from the same manifest the JSON pack holds,
    so every count and value matches it. Nested objects become dotted columns; lists are written as JSON."""
    rows: List[Dict[str, Any]] = []
    org = manifest.get("organisation") or {}
    for section in ("attestations", "workflows", "policies"):
        rows += [{"section": section, **_flat(r)} for r in org.get(section) or []]
    for item in manifest.get("systems", []):
        system = item.get("system") or {}
        base = {"system_id": system.get("id"), "system_name": system.get("name")}
        gate = item.get("gate") or {}
        rows.append({"section": "gate", **base, "riskTier": system.get("riskTier"), "chainHead": item.get("chainHead"),
                     **{k: gate.get(k) for k in ("verdict", "confidence", "reasons")}})
        rows += [{"section": "gate_checks", **base, **_flat(check)} for check in gate.get("checks") or []]
        for fw in (item.get("clauseMap") or {}).get("frameworks", []):
            rows += [{"section": "clauses", **base, "framework": fw.get("key"), **_flat(clause)} for clause in fw.get("clauses", [])]
        for section in _CSV_SYSTEM_SECTIONS:
            rows += [{"section": section, **base, **_flat(r)} for r in item.get(section) or []]
    columns = list(dict.fromkeys(["section", "system_id", "system_name", *(k for r in rows for k in r)]))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, restval="")
    writer.writeheader()
    writer.writerows({k: _csv_cell(v) for k, v in r.items()} for r in rows)
    return buf.getvalue()


def verify_manifest(manifest: Dict[str, Any], expected_hash: str) -> Dict[str, Any]:
    """Recompute the manifest hash and every system's chain head. Pure; no database."""
    actual = manifest_digest(manifest)
    systems = []
    for item in manifest.get("systems", []):
        entries = item.get("evidence", [])
        recomputed = chain_head(entries)
        # Version 1 entries carry only the hash; from version 2 each one carries the fields it covers.
        bad = [e.get("id") for e in entries if not hmac.compare_digest(str(e.get("hash")), entry_hash(e))] if manifest.get("version", 1) >= 2 else []
        systems.append({
            "id": (item.get("system") or {}).get("id"),
            "name": (item.get("system") or {}).get("name"),
            "evidenceCount": len(entries),
            "chainHead": item.get("chainHead"),
            "recomputedChainHead": recomputed,
            "chainIntact": hmac.compare_digest(str(item.get("chainHead")), recomputed),
            "entriesNotMatchingHash": bad,
        })
    hash_ok = hmac.compare_digest(str(expected_hash), actual)
    return {"intact": hash_ok and all(s["chainIntact"] and not s["entriesNotMatchingHash"] for s in systems), "hashMatches": hash_ok, "expectedHash": expected_hash, "actualHash": actual, "systems": systems}


def new_share_token() -> Dict[str, str]:
    """The token is returned to the caller once; only its SHA-256 and expiry are stored."""
    token = secrets.token_urlsafe(32)
    return {"token": token, "hash": hash_token(token), "expiresAt": (datetime.now(timezone.utc) + SHARE_TTL).isoformat()}


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def token_matches(token: str, stored_hash: Optional[str]) -> bool:
    return bool(stored_hash) and hmac.compare_digest(hash_token(token), stored_hash)


def is_expired(expires_at: Optional[str]) -> bool:
    if not expires_at:
        return True
    when = datetime.fromisoformat(expires_at)
    return (when if when.tzinfo else when.replace(tzinfo=timezone.utc)) <= datetime.now(timezone.utc)


def clause_frameworks() -> List[Dict[str, str]]:
    """Frameworks the clause map can speak to (the lead four first), as {key, name}."""
    from src.application.services.clause_map_service import CHECK_CONTROLS, LEAD_FRAMEWORKS, _catalogue, evaluation_links

    cat = _catalogue()
    keys = {e["requirement"]["framework"] for control in CHECK_CONTROLS.values() for e in cat["by_control"].get(control, [])}
    keys |= {cat["active"][k]["framework"] for ev in cat["evaluations"] for k in evaluation_links(ev)}  # evaluation runs reach these too
    order = {k: i for i, k in enumerate(LEAD_FRAMEWORKS)}
    rows = [{"key": k, "name": cat["frameworks"].get(k, {}).get("name", k)} for k in keys]
    return sorted(rows, key=lambda r: (order.get(r["key"], len(order)), r["name"]))

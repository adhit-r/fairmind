"""Stored LLM-judge and advanced-bias analyses: one row per run, tied to an AI system and its org.

A failing or high-severity result opens one finding on the system; a second is not opened while one
for the same kind is still open.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

FINDING_SOURCE = "fairmind.bias_analysis"
FAILING_SEVERITIES = ("high", "critical")


def verdict_for(severity: Optional[str], *, insufficient: bool = False) -> str:
    if insufficient:
        return "insufficient"
    return "fail" if (severity or "").lower() in FAILING_SEVERITIES else "pass"


def _open_finding(db: Session, system_id: str, source: str, closed: List[str]) -> Optional[str]:
    row = db.execute(
        text("SELECT id FROM governance_risks WHERE system_id = :id AND source = :source AND status NOT IN :closed LIMIT 1").bindparams(
            bindparam("closed", expanding=True)
        ),
        {"id": system_id, "source": source, "closed": closed},
    ).fetchone()
    return row[0] if row else None


def record(
    db: Session, *, org_id: str, system_id: str, kind: str, inputs: Dict[str, Any], result: Dict[str, Any],
    verdict: str, severity: Optional[str], actor: str, closed_statuses: List[str], risk_score: float,
) -> Dict[str, Any]:
    """Store the run; open a finding when it failed. Returns {"id", "findingId"}."""
    now = datetime.now(timezone.utc).isoformat()
    analysis_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_bias_analyses (id, org_id, system_id, kind, inputs_json, result_json, verdict, severity, created_by, created_at) "
            "VALUES (:id, :org_id, :system_id, :kind, :inputs, :result, :verdict, :severity, :by, :at)"
        ),
        {"id": analysis_id, "org_id": org_id, "system_id": system_id, "kind": kind, "inputs": json.dumps(inputs, default=str),
         "result": json.dumps(result, default=str), "verdict": verdict, "severity": severity, "by": actor, "at": now},
    )
    finding_id = None
    if verdict == "fail":
        source = f"{FINDING_SOURCE}:{kind}"
        finding_id = _open_finding(db, system_id, source, closed_statuses)
        if finding_id is None:
            finding_id = str(uuid.uuid4())
            db.execute(
                text(
                    "INSERT INTO governance_risks "
                    "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
                    "VALUES (:id, :system_id, :title, :severity, 'open', :description, :mitigation, 'likely', :risk_score, :source, :categories, :metadata, :at, :at)"
                ),
                {
                    "id": finding_id, "system_id": system_id, "title": f"Bias analysis ({kind}) found {severity} severity",
                    "severity": "critical" if (severity or "").lower() == "critical" else "high",
                    "description": f"A stored {kind} analysis ended {severity}. Open the analysis for the full result.",
                    "mitigation": "Review the analysis recommendations, mitigate, then run the analysis again.",
                    "risk_score": risk_score, "source": source, "categories": json.dumps(["bias", kind]),
                    "metadata": json.dumps({"analysis_id": analysis_id}), "at": now,
                },
            )
    db.commit()
    return {"id": analysis_id, "findingId": finding_id}


def _row(r: Any, with_result: bool) -> Dict[str, Any]:
    out = {"id": r[0], "systemId": r[1], "kind": r[2], "inputs": json.loads(r[3] or "{}"), "verdict": r[4], "severity": r[5], "createdBy": r[6], "createdAt": r[7]}
    if with_result:
        out["result"] = json.loads(r[8] or "{}")
    return out


_COLS = "id, system_id, kind, inputs_json, verdict, severity, created_by, created_at, result_json"


def list_for_system(db: Session, org_id: str, system_id: str, kinds: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
    sql = f"SELECT {_COLS} FROM governance_bias_analyses WHERE org_id = :org AND system_id = :sid"
    stmt = text(sql + (" AND kind IN :kinds" if kinds else "") + " ORDER BY created_at DESC LIMIT :n")
    if kinds:
        stmt = stmt.bindparams(bindparam("kinds", expanding=True))
    rows = db.execute(stmt, {"org": org_id, "sid": system_id, "kinds": kinds or [], "n": limit}).fetchall()
    return [_row(r, False) for r in rows]


def get_one(db: Session, org_id: str, analysis_id: str, kinds: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    r = db.execute(
        text(f"SELECT {_COLS} FROM governance_bias_analyses WHERE id = :id AND org_id = :org"), {"id": analysis_id, "org": org_id}
    ).fetchone()
    if not r or (kinds and r[2] not in kinds):
        return None
    return _row(r, True)

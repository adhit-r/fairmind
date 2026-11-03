"""Seal a system's evidence when a release decision is recorded, and verify it later.

Each evidence row hashes to SHA-256 over its stable fields; the chain head folds those
hashes in creation order. A seal stores the head and every entry, so verification can
say exactly which record changed or disappeared after the decision. Records added
after the decision do not break the seal; they are counted.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

_EVIDENCE_SQL = (
    "SELECT id, evidence_type, title, source, content_json, confidence, status, metadata_json, created_at "
    "FROM governance_evidence WHERE system_id = :system_id ORDER BY created_at ASC, id ASC"
)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _row_hash(row: Any) -> str:
    return _digest({
        "id": row[0], "type": row[1], "title": row[2], "source": row[3], "content": row[4],
        "confidence": None if row[5] is None else float(row[5]), "status": row[6], "metadata": row[7], "created_at": str(row[8]),
    })


def evidence_entries(db: Session, system_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(text(_EVIDENCE_SQL), {"system_id": system_id}).fetchall()
    return [{"id": r[0], "type": r[1], "hash": _row_hash(r), "createdAt": str(r[8])} for r in rows]


def chain_head(entries: List[Dict[str, Any]]) -> str:
    head = hashlib.sha256(b"fairmind-evidence-chain-v1").hexdigest()
    for entry in entries:
        head = hashlib.sha256(f"{head}:{entry['hash']}".encode()).hexdigest()
    return head


def seal_decision(db: Session, *, system_id: str, request_id: str, decision_id: str, decision: str, sealed_by: Optional[str], gate: Dict[str, Any]) -> Dict[str, Any]:
    entries = evidence_entries(db, system_id)
    gate_summary = {"verdict": gate.get("verdict"), "confidence": gate.get("confidence"), "checks": [{"key": c.get("key"), "state": c.get("state"), "confidence": c.get("confidence")} for c in gate.get("checks", [])]}
    row = {
        "id": str(uuid.uuid4()), "system_id": system_id, "request_id": request_id, "decision_id": decision_id, "decision": decision,
        "chain_head": chain_head(entries), "evidence_count": len(entries), "entries_json": json.dumps(entries), "gate_json": json.dumps(gate_summary),
        "sealed_by": sealed_by, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.execute(
        text(
            "INSERT INTO governance_decision_seals (id, system_id, request_id, decision_id, decision, chain_head, evidence_count, entries_json, gate_json, sealed_by, created_at) "
            "VALUES (:id, :system_id, :request_id, :decision_id, :decision, :chain_head, :evidence_count, :entries_json, :gate_json, :sealed_by, :created_at)"
        ),
        row,
    )
    return _serialize(row, entries, evidence_entries(db, system_id))


def verify(sealed: List[Dict[str, Any]], current: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = {e["id"]: e["hash"] for e in current}
    changed = [e["id"] for e in sealed if e["id"] in now and now[e["id"]] != e["hash"]]
    missing = [e["id"] for e in sealed if e["id"] not in now]
    sealed_ids = {e["id"] for e in sealed}
    added = [e["id"] for e in current if e["id"] not in sealed_ids]
    return {"status": "intact" if not changed and not missing else "broken", "changed": changed, "missing": missing, "addedSince": len(added)}


def _serialize(row: Dict[str, Any], sealed: List[Dict[str, Any]], current: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": row["id"], "systemId": row["system_id"], "requestId": row["request_id"], "decisionId": row["decision_id"], "decision": row["decision"],
        "chainHead": row["chain_head"], "evidenceCount": row["evidence_count"], "gate": json.loads(row["gate_json"] or "{}"),
        "sealedBy": row["sealed_by"], "createdAt": row["created_at"], "verification": verify(sealed, current),
    }


def list_seals(db: Session, system_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text("SELECT id, system_id, request_id, decision_id, decision, chain_head, evidence_count, entries_json, gate_json, sealed_by, created_at FROM governance_decision_seals WHERE system_id = :system_id ORDER BY created_at DESC"),
        {"system_id": system_id},
    ).fetchall()
    current = evidence_entries(db, system_id)
    keys = ("id", "system_id", "request_id", "decision_id", "decision", "chain_head", "evidence_count", "entries_json", "gate_json", "sealed_by", "created_at")
    return [_serialize(dict(zip(keys, r)), json.loads(r[7] or "[]"), current) for r in rows]

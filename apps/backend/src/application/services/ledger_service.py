"""The organisation's hash-chained ledger: one writer any feature can call, and one verifier.

Each entry's hash is SHA-256 over its own fields and the previous entry's hash, so changing or removing an entry
breaks every hash after it. append() runs in the caller's transaction (the caller commits), so an entry exists only if
the change it records does. Keep payloads to ids, hashes and counts: the ledger is permanent, so no names or emails.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

GENESIS = "0" * 64
_TRIES = 5


def _canonical(org_id: str, seq: int, kind: str, subject_type: str, subject_id: str, actor: Optional[str], payload: Dict[str, Any], created_at: str, prev_hash: str) -> str:
    return json.dumps(
        {"org_id": org_id, "seq": seq, "kind": kind, "subject_type": subject_type, "subject_id": subject_id, "actor": actor,
         "payload": payload, "created_at": created_at, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )


def append(db: Session, org_id: str, kind: str, subject_type: str, subject_id: str, actor: Optional[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Add the next entry to the organisation's chain in the caller's transaction. Caller commits.

    Two writers can pick the same seq; the unique index stops the second, which then reads the new head and tries again."""
    for _ in range(_TRIES):
        last = db.execute(text("SELECT seq, hash FROM ledger_entries WHERE org_id = :o ORDER BY seq DESC LIMIT 1"), {"o": org_id}).fetchone()
        seq, prev = (last[0] + 1, last[1]) if last else (1, GENESIS)
        created_at = datetime.now(timezone.utc).isoformat()
        canonical = _canonical(org_id, seq, kind, subject_type, subject_id, actor, payload, created_at, prev)
        entry = {"id": str(uuid.uuid4()), "seq": seq, "kind": kind, "hash": hashlib.sha256(canonical.encode()).hexdigest(), "prevHash": prev, "createdAt": created_at}
        try:
            with db.begin_nested():  # a lost race rolls back this insert only, not the caller's work
                db.execute(
                    text(
                        "INSERT INTO ledger_entries (id, org_id, seq, kind, subject_type, subject_id, actor, payload_json, canonical_json, prev_hash, hash, created_at) "
                        "VALUES (:id, :o, :seq, :kind, :st, :sid, :actor, :payload, :canonical, :prev, :hash, :at)"
                    ),
                    {"id": entry["id"], "o": org_id, "seq": seq, "kind": kind, "st": subject_type, "sid": subject_id, "actor": actor,
                     "payload": json.dumps(payload, sort_keys=True), "canonical": canonical, "prev": prev, "hash": entry["hash"], "at": created_at},
                )
            return entry
        except IntegrityError:
            continue
    raise RuntimeError("The ledger is busy; try again")


def entries(db: Session, org_id: str, subject_type: Optional[str] = None, subject_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM ledger_entries WHERE org_id = :o"
    params: Dict[str, Any] = {"o": org_id, "n": limit}
    if subject_type and subject_id:
        sql += " AND subject_type = :st AND subject_id = :sid"
        params.update(st=subject_type, sid=subject_id)
    rows = db.execute(text(sql + " ORDER BY seq DESC LIMIT :n"), params).mappings().all()
    return [
        {"seq": r["seq"], "kind": r["kind"], "subjectType": r["subject_type"], "subjectId": r["subject_id"], "actor": r["actor"],
         "payload": json.loads(r["payload_json"]), "prevHash": r["prev_hash"], "hash": r["hash"], "createdAt": r["created_at"]}
        for r in reversed(rows)
    ]


def verify(db: Session, org_id: str) -> Dict[str, Any]:
    """Walk the whole chain from the start. brokenAt is the first seq that no longer matches, else None."""
    rows = db.execute(text("SELECT * FROM ledger_entries WHERE org_id = :o ORDER BY seq"), {"o": org_id}).mappings().all()
    prev, broken = GENESIS, None
    for index, r in enumerate(rows, start=1):
        rebuilt = _canonical(r["org_id"], r["seq"], r["kind"], r["subject_type"], r["subject_id"], r["actor"], json.loads(r["payload_json"]), r["created_at"], r["prev_hash"])
        if r["seq"] != index or r["prev_hash"] != prev or rebuilt != r["canonical_json"] or hashlib.sha256(rebuilt.encode()).hexdigest() != r["hash"]:
            broken = r["seq"]
            break
        prev = r["hash"]
    return {"valid": broken is None, "count": len(rows), "head": prev, "brokenAt": broken}

"""The organisation's hash-chained ledger: one writer any feature can call, and one verifier.

Each entry's hash is SHA-256 over its own fields and the previous entry's hash, so changing or removing an entry
breaks every hash after it. append() runs in the caller's transaction (the caller commits), so an entry exists only if
the change it records does. Keep payloads to ids, hashes, counts and text: the ledger is permanent, so no names or emails, and no floats (a pack saved by a browser rewrites 1.0 as 1, which would break the hash).
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


def export(db: Session, org_id: str) -> List[Dict[str, Any]]:
    """The whole chain with every field its hashes cover, oldest first, so a reader can recompute it without the database."""
    rows = db.execute(text("SELECT * FROM ledger_entries WHERE org_id = :o ORDER BY seq"), {"o": org_id}).mappings().all()
    return [
        {"org_id": r["org_id"], "seq": r["seq"], "kind": r["kind"], "subject_type": r["subject_type"], "subject_id": r["subject_id"], "actor": r["actor"],
         "payload": json.loads(r["payload_json"]), "created_at": r["created_at"], "prev_hash": r["prev_hash"], "hash": r["hash"]}
        for r in rows
    ]


def check(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pure walk of an exported chain from the start. brokenAt is the first seq that no longer matches, else None."""
    prev, broken = GENESIS, None
    for index, e in enumerate(chain, start=1):
        rebuilt = _canonical(e["org_id"], e["seq"], e["kind"], e["subject_type"], e["subject_id"], e["actor"], e["payload"], e["created_at"], e["prev_hash"])
        if e["seq"] != index or e["prev_hash"] != prev or hashlib.sha256(rebuilt.encode()).hexdigest() != e["hash"]:
            broken = e["seq"]
            break
        prev = e["hash"]
    return {"valid": broken is None, "count": len(chain), "head": prev, "brokenAt": broken}


def verify(db: Session, org_id: str) -> Dict[str, Any]:
    """The stored chain, checked from the start, including that each stored canonical form is the one its fields give."""
    rows = db.execute(text("SELECT seq, canonical_json FROM ledger_entries WHERE org_id = :o ORDER BY seq"), {"o": org_id}).all()
    chain = export(db, org_id)
    result = check(chain)
    if result["valid"]:
        for e, (_, stored) in zip(chain, rows):
            if stored != _canonical(e["org_id"], e["seq"], e["kind"], e["subject_type"], e["subject_id"], e["actor"], e["payload"], e["created_at"], e["prev_hash"]):
                return {**result, "valid": False, "brokenAt": e["seq"]}
    return result

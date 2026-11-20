"""What the release gate reads of a system's Art 5 screen: the stored record and whether it still blocks.

The record lives in governance_ai_systems.metadata_json.prohibitedScreen, written by the applicability routes.
A system never screened is not blocked here: the gate only acts on a screen someone ran.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

KEY = "prohibitedScreen"


def read(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(text("SELECT metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    try:
        record = (json.loads(row[0] or "{}") if row else {}).get(KEY)
    except (TypeError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def blocking_state(record: Optional[Dict[str, Any]]) -> Optional[str]:
    """"indicated" or "needs_legal_review" while no person has recorded a clearance; None when clear, cleared or never screened."""
    if not record or record.get("outcome") not in ("indicated", "needs_legal_review") or record.get("clearance"):
        return None
    return record["outcome"]


def gate_reason(state: str) -> str:
    return {
        "indicated": "EU AI Act Art 5 screen indicates a prohibited practice: no go until legal counsel records a clearance",
        "needs_legal_review": "EU AI Act Art 5 screen cannot conclude: approval is blocked until legal counsel records a decision",
    }[state]

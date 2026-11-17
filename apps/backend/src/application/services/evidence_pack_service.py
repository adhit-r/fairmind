"""Inspection packs: a hashed manifest an auditor can verify offline.

The manifest freezes, per system, the release gate, the clause map for the chosen
frameworks, every evidence record with the fields its hash covers, and every decision seal
with the gate it saw and the approver's notes; and, for the organisation, the plan
attestations people made for organisation-level controls. Canonical form:
``json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()``;
from version 2 every float with an integral value is written as an integer first, so a pack
re-saved by a browser (``JSON.stringify`` writes 0.0 as 0) still verifies.
``manifest_hash`` is its SHA-256. The chain head of each system is recomputed from its
entries with the same fold as ``decision_seal_service.chain_head``, and each entry's hash
from its fields with ``decision_seal_service.entry_hash``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.clause_map_service import clause_map
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
        })
    attestations = db.execute(
        text("SELECT task_key, statement, reference, attested_by, created_at FROM plan_attestations WHERE org_id = :org ORDER BY created_at"),
        {"org": org_id},
    ).mappings().all()
    return {
        "version": MANIFEST_VERSION,
        "title": title,
        "organisation": {"attestations": [dict(r) for r in attestations]},
        "frameworks": frameworks,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "createdBy": created_by,
        "systems": out,
    }


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
    from src.application.services.clause_map_service import CHECK_CONTROLS, LEAD_FRAMEWORKS, _catalogue

    cat = _catalogue()
    keys = {e["requirement"]["framework"] for control in CHECK_CONTROLS.values() for e in cat["by_control"].get(control, [])}
    order = {k: i for i, k in enumerate(LEAD_FRAMEWORKS)}
    rows = [{"key": k, "name": cat["frameworks"].get(k, {}).get("name", k)} for k in keys]
    return sorted(rows, key=lambda r: (order.get(r["key"], len(order)), r["name"]))

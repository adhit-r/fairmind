"""Inspection packs: a hashed manifest an auditor can verify offline.

The manifest freezes, per system, the release gate, the clause map for the chosen
frameworks, every evidence record's hash and the latest decision seals. Canonical form:
``json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()``;
``manifest_hash`` is its SHA-256. The chain head of each system is recomputed from its
entries with the same fold as ``decision_seal_service.chain_head``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.application.services.clause_map_service import clause_map
from src.application.services.decision_seal_service import chain_head, evidence_entries, list_seals

MANIFEST_VERSION = 1
SHARE_TTL = timedelta(days=30)
LATEST_SEALS = 5


def canonical_bytes(manifest: Dict[str, Any]) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def manifest_digest(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def build_manifest(db: Session, *, title: str, frameworks: List[str], systems: List[Dict[str, Any]], created_by: Optional[str]) -> Dict[str, Any]:
    """systems: [{"id", "name", "riskTier", "gate"}], gate being the release gate payload."""
    out: List[Dict[str, Any]] = []
    for system in systems:
        gate = system["gate"]
        entries = evidence_entries(db, system["id"])
        seals = [
            {k: seal[k] for k in ("id", "decision", "chainHead", "evidenceCount", "sealedBy", "createdAt", "verification")}
            for seal in list_seals(db, system["id"])[:LATEST_SEALS]
        ]
        out.append({
            "system": {"id": system["id"], "name": system["name"], "riskTier": system["riskTier"]},
            "gate": {k: gate.get(k) for k in ("verdict", "confidence", "checks", "reasons")},
            "clauseMap": clause_map(gate, frameworks=frameworks),
            "evidence": entries,
            "chainHead": chain_head(entries),
            "seals": seals,
        })
    return {
        "version": MANIFEST_VERSION,
        "title": title,
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
        systems.append({
            "id": (item.get("system") or {}).get("id"),
            "name": (item.get("system") or {}).get("name"),
            "evidenceCount": len(entries),
            "chainHead": item.get("chainHead"),
            "recomputedChainHead": recomputed,
            "chainIntact": hmac.compare_digest(str(item.get("chainHead")), recomputed),
        })
    hash_ok = hmac.compare_digest(str(expected_hash), actual)
    return {"intact": hash_ok and all(s["chainIntact"] for s in systems), "hashMatches": hash_ok, "expectedHash": expected_hash, "actualHash": actual, "systems": systems}


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

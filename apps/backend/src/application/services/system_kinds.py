"""What kind of AI system a governed system is, and which catalogue evaluations fit that kind.

The kind lives in governance_ai_systems.metadata_json["asset_kind"], the key discovery writes
(discovery_sources.catalog.asset_kind and integrations.py). The system_type column is never written.
"""

import json
from typing import Any, Dict, FrozenSet, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# The kinds discovery writes; registration accepts the same values.
SYSTEM_KINDS = ("llm_app", "ml_model", "agent", "ai_service", "ai_assisted_dev", "mcp_server")
_ALL: FrozenSet[str] = frozenset(SYSTEM_KINDS)

# Every distinct appliesTo string in pack_catalogue_data/catalogue.json -> the kinds it applies to.
APPLIES_TO: Dict[str, FrozenSet[str]] = {
    "Agent": frozenset({"agent"}),
    "Agent, decision systems": frozenset({"agent", "ml_model"}),
    "Any": _ALL,
    "Any user-facing system": _ALL,
    "Browser agent": frozenset({"agent"}),
    "Coding agent": frozenset({"agent", "ai_assisted_dev"}),
    "Coding agent, agent": frozenset({"agent", "ai_assisted_dev"}),
    "Decision systems": frozenset({"ml_model"}),
    "Decision systems (credit)": frozenset({"ml_model"}),
    "Decision systems (education)": frozenset({"ml_model"}),
    "Decision systems (employment)": frozenset({"ml_model"}),
    "Decision systems (insurance)": frozenset({"ml_model"}),
    "Decision systems (public sector)": frozenset({"ml_model"}),
    "Decision systems, LLM app": frozenset({"ml_model", "llm_app"}),
    "FairMind agent": frozenset(),  # tests FairMind's own agent, never the organisation's system
    "Generative systems": frozenset({"llm_app", "agent", "ai_service"}),
    "LLM app": frozenset({"llm_app"}),
    "LLM app (customer service)": frozenset({"llm_app"}),
    "LLM app (finance)": frozenset({"llm_app"}),
    "LLM app (health)": frozenset({"llm_app"}),
    "LLM app, agent": frozenset({"llm_app", "agent"}),
    "Model": frozenset({"ml_model"}),
    "Model, LLM app": frozenset({"ml_model", "llm_app"}),
    "Model, agent": frozenset({"ml_model", "agent"}),
    "Multi-agent system": frozenset({"agent"}),
    "Organisation": _ALL,  # an organisation-wide check holds for every system it governs
    "RAG apps": frozenset({"llm_app"}),
    "RAG apps, agents": frozenset({"llm_app", "agent"}),
    "Training and evaluation data": frozenset({"ml_model", "llm_app"}),
    "Training data": frozenset({"ml_model", "llm_app"}),  # fine-tune sets are training data too
    "Training data, RAG sources": frozenset({"ml_model", "llm_app"}),
    "Voice channels": frozenset({"llm_app", "agent"}),
}


def kind_of(metadata: Any, target_kind: Optional[str] = None) -> Optional[str]:
    """The stored kind; with none, a saved OpenAI-compatible connection means an LLM app; else None (not known)."""
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata or "{}")
        except ValueError:
            metadata = {}
    kind = metadata.get("asset_kind") if isinstance(metadata, dict) else None
    if kind in SYSTEM_KINDS:
        return kind
    return "llm_app" if target_kind == "openai" else None


def system_kind(db: Session, system_id: str) -> Optional[str]:
    row = db.execute(
        text(
            "SELECT s.metadata_json, t.kind FROM governance_ai_systems s "
            "LEFT JOIN governance_ai_system_targets t ON t.system_id = s.id WHERE s.id = :id"
        ),
        {"id": system_id},
    ).fetchone()
    return kind_of(row[0], row[1]) if row else None


def fit(applies_to: Optional[str], kind: Optional[str]) -> str:
    """applies, other (meant for another kind of system) or unknown (the system has no kind)."""
    if kind is None:
        return "unknown"
    return "applies" if kind in APPLIES_TO.get(applies_to or "", _ALL) else "other"

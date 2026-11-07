"""Suggest a system's risk tier and the frameworks it answers to, from a few plain answers.

A fixed rule table, no model: every rule that fires is returned with its text and,
where the EU AI Act applies, the catalogue requirement it rests on. A person then
confirms the tier and frameworks; changing the suggestion needs a written reason.
Framework availability and citation titles are read from the pack catalogue, the
same file GET /api/v1/packs/journeys serves.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from src.application.services.clause_map_service import CATALOGUE_PATH

RULES_VERSION = "2026-11.1"
TIERS = ("low", "medium", "high", "critical")
TIER_ORDER = {tier: i for i, tier in enumerate(TIERS)}
MIN_REASON = 12

# key, label, EU AI Act anchor (an Annex III area, Art 6 for a medical device, or None)
USES = (
    ("credit", "Credit or lending decisions", "Annex III.5"),
    ("insurance", "Life or health insurance pricing or eligibility", "Annex III.5"),
    ("public_benefits", "Eligibility for public benefits or essential services", "Annex III.5"),
    ("employment", "Hiring, promotion or work allocation", "Annex III.4"),
    ("education", "Admissions, grading or proctoring", "Annex III.3"),
    ("biometric", "Biometric identification or categorisation", "Annex III.1"),
    ("critical_infrastructure", "Safety components of critical infrastructure", "Annex III.2"),
    ("law_enforcement", "Law enforcement", "Annex III.6"),
    ("migration", "Migration, asylum or border control", "Annex III.7"),
    ("justice", "Courts or elections", "Annex III.8"),
    ("medical", "Medical diagnosis or treatment (a medical device)", "Art 6"),
    ("fraud", "Fraud or financial-crime detection", None),
    ("marketing", "Marketing, offers or recommendations", None),
    ("operations", "Internal operations, no decisions about people", None),
    ("other", "Something else", None),
)
USE_KEYS = {key for key, _, _ in USES}

TIER_RULES = (
    ("T1", "high", "High: the use is in an EU AI Act Annex III high-risk area or is a medical device, and it decides about individual people."),
    ("T2", "critical", "Critical: T1 applies and no person reviews decisions before they take effect."),
    ("T3", "medium", "Medium: it decides about individual people, in a use that is not in a high-impact category."),
    ("T4", "low", "Low: it does not make or shape decisions about individual people."),
)

# id, framework key, display name when the catalogue lacks it, rule table text
FRAMEWORK_RULES = (
    ("F1", "EUAIA", "EU AI Act", "EU AI Act: people in the EU are affected."),
    ("F2", "INDAI", "India AI Governance Guidelines", "India AI Governance Guidelines: people in India are affected."),
    ("F3", "RBIFREEAI", "RBI FREE-AI", "RBI FREE-AI: your organisation is RBI-regulated, or you are not sure whether it is."),
    ("F4", "DPDP", "DPDP Act 2023", "DPDP Act 2023: it uses personal data of people in India."),
    ("F5", "NITI", "NITI Aayog Responsible AI", "NITI Aayog Responsible AI: people in India are affected."),
)


class ApplicabilityError(ValueError):
    """An answer set or confirmation the rules cannot accept; the message is shown to the person."""


@lru_cache(maxsize=1)
def _catalogue() -> Dict[str, Dict[str, Any]]:
    data = json.loads(CATALOGUE_PATH.read_text())
    return {
        "frameworks": {f["key"]: f for f in data["frameworks"]},
        "requirements": {r["key"]: r for r in data["requirements"]},
    }


def catalogue_frameworks() -> Dict[str, Dict[str, Any]]:
    return _catalogue()["frameworks"]


def _cite(key: str) -> Dict[str, str]:
    req = _catalogue()["requirements"].get(key)
    return {"key": key, "title": req["title"] if req else key}


def _tier_rules(answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every tier rule that fires, highest tier first; empty until the use and the people question are answered."""
    use, decides = answers.get("use"), answers.get("decidesAboutPeople")
    if use is None or decides is None:
        return []
    eu = "EU" in (answers.get("markets") or [])
    label, anchor = next(((lbl, a) for key, lbl, a in USES if key == use), (use, None))
    fired: List[Dict[str, Any]] = []
    t1 = bool(anchor) and decides is True
    if t1:
        # "Credit or lending decisions decisions ..." would stutter.
        text = f"{label.removesuffix(' decisions')} decisions about individual people are a high-impact use."
        fired.append({"id": "T1", "tier": "high", "text": text if eu else f"{text} FairMind treats them as high risk.", "cite": _cite(f"EUAIA|{anchor}") if eu else None})
        if answers.get("humanReview") == "automatic":
            fired.append({"id": "T2", "tier": "critical", "text": "No person reviews decisions before they take effect.", "cite": _cite("EUAIA|Art 14") if eu else None})
    elif decides is True:
        text, cite = "It decides about individual people, in a use that is not in a high-impact category.", None
        if use == "fraud" and eu:
            text, cite = f"{text} The EU AI Act excludes fraud detection from its credit high-risk area.", _cite("EUAIA|Annex III.5")
        fired.append({"id": "T3", "tier": "medium", "text": text, "cite": cite})
    if decides is False:
        fired.append({"id": "T4", "tier": "low", "text": "It does not make or shape decisions about individual people.", "cite": None})
    return sorted(fired, key=lambda r: -TIER_ORDER[r["tier"]])


def _framework_rules(answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    markets = answers.get("markets") or []
    rbi = answers.get("rbiRegulated")
    texts = {
        "F1": "People in the EU are affected." if "EU" in markets else None,
        "F2": "People in India are affected." if "IN" in markets else None,
        "F3": {"yes": "Your organisation is RBI-regulated.", "unsure": "You are not sure whether your organisation is RBI-regulated, so it stays in until someone confirms it is not."}.get(rbi),
        "F4": "It uses personal data of people in India." if answers.get("personalDataIndia") is True else None,
        "F5": "NITI Aayog Responsible AI principles apply to AI deployed in India." if "IN" in markets else None,
    }
    catalogue = catalogue_frameworks()
    out = []
    for rule_id, key, fallback, _ in FRAMEWORK_RULES:
        if texts[rule_id] is None:
            continue
        fw = catalogue.get(key)
        out.append({
            "key": key, "name": fw["name"] if fw else fallback, "available": fw is not None,
            "rule": {"id": rule_id, "text": texts[rule_id]}, "binding": fw.get("binding") if fw else None,
        })
    return out


def suggest(answers: Dict[str, Any]) -> Dict[str, Any]:
    fired = _tier_rules(answers)
    return {
        "rulesVersion": RULES_VERSION,
        "tier": fired[0]["tier"] if fired else None,
        "tierRules": [{k: r[k] for k in ("id", "text", "cite")} for r in fired],
        "frameworks": _framework_rules(answers),
        "uses": [{"key": key, "label": label} for key, label, _ in USES],
        "rules": [{"id": i, "text": t} for i, _, t in TIER_RULES] + [{"id": i, "text": t} for i, _, _, t in FRAMEWORK_RULES],
    }


def build_record(answers: Dict[str, Any], *, tier: str, frameworks: List[str], reason: Optional[str], confirmed_by: str, confirmed_at: str) -> Dict[str, Any]:
    """The confirmed record, recomputing the suggestion from the answers; raises ApplicabilityError when it cannot be recorded."""
    if answers.get("use") is None or answers.get("decidesAboutPeople") is None:
        raise ApplicabilityError("Answer what it decides and whether it decides about people")
    if tier not in TIER_ORDER:
        raise ApplicabilityError(f"{tier} is not a risk tier")
    catalogue = catalogue_frameworks()
    chosen = list(dict.fromkeys(frameworks))
    for key in chosen:
        if key not in catalogue:
            raise ApplicabilityError(f"{key} is not in the framework catalogue")
    suggestion = suggest(answers)
    suggested = [f["key"] for f in suggestion["frameworks"] if f["available"]]
    removed = [k for k in suggested if k not in chosen]
    reason = (reason or "").strip() or None
    if (tier != suggestion["tier"] or removed) and len(reason or "") < MIN_REASON:
        raise ApplicabilityError("Say why you changed the suggestion")
    return {
        "rulesVersion": RULES_VERSION,
        "answers": answers,
        "suggestedTier": suggestion["tier"],
        "tier": tier,
        "tierRules": suggestion["tierRules"],
        "suggestedFrameworks": suggested,
        "frameworks": [{"key": k, "name": catalogue[k]["name"]} for k in chosen],
        "added": [k for k in chosen if k not in suggested],
        "removed": removed,
        "reason": reason,
        "tierBelowSuggestion": TIER_ORDER[tier] < TIER_ORDER[suggestion["tier"]],
        "overrideAcceptedBy": None,
        "overrideAcceptedAt": None,
        "confirmedBy": confirmed_by,
        "confirmedAt": confirmed_at,
    }

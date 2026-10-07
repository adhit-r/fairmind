#!/usr/bin/env python3
"""
Seed script for the risk taxonomy data model (Issue #157).

Populates risk_taxonomies / risk_categories / risk_factors /
risk_assessment_templates with the initial IBM AI Risk Atlas and
MIT AI Risk Repository taxonomies.

Factual basis:
- IBM AI Risk Atlas (github.com/IBM/ai-risk-atlas)
- MIT AI Risk Repository (airisk.mit.edu, Slattery et al. 2024)

Usage:
    cd apps/backend
    python scripts/seed_risk_taxonomy.py [--database-url sqlite:///dev.db]

Idempotent: re-running skips taxonomies whose `key` already exists.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text  # noqa: E402

from database.connection import db_manager  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


CATEGORIES = [
    ("fairness", "Fairness",
     "Equitable treatment across groups; freedom from unjust bias.",
     [("data_bias", "Data bias",
       "Training data that under- or mis-represents groups.",
       ["Audit dataset composition", "Representative sampling"]),
      ("representation_disparity", "Representation disparity",
       "Performance gaps across protected attributes.",
       ["Disaggregated evaluation", "Fairness metrics per group"]),
      ("outcome_disparity", "Outcome disparity",
       "Decisions disadvantaging protected groups.",
       ["Impact assessments", "Human review of high-stakes outputs"])]),
    ("explainability", "Explainability",
     "Ability to understand and communicate system outputs.",
     [("model_opacity", "Model opacity",
       "Outputs without inspectable reasoning.",
       ["Model cards", "Rationale traces where feasible"]),
      ("stakeholder_communication", "Stakeholder communication",
       "Explanations not adapted to users/auditors.",
       ["Layered explanations", "Published evaluation summaries"])]),
    ("robustness", "Robustness",
     "Reliable behavior under shift, noise, and adversarial inputs.",
     [("distribution_shift", "Distribution shift",
       "Degradation on out-of-distribution inputs.",
       ["OOD test suites", "Drift monitoring"]),
      ("adversarial_inputs", "Adversarial inputs",
       "Prompt injection, jailbreaks, poisoning.",
       ["Red-teaming", "Input/output guardrails"])]),
    ("privacy", "Privacy",
     "Protection of personal and sensitive information.",
     [("training_data_leakage", "Training data leakage",
       "Memorized PII regurgitated at inference.",
       ["PII scrubbing", "Membership-inference testing"]),
      ("inference_disclosure", "Inference-time disclosure",
       "Sensitive user data exposed via logs/outputs.",
       ["Data minimization", "Retention policies"])]),
    ("security", "Security",
     "Resistance to misuse and attack.",
     [("malicious_use", "Malicious use",
       "Abuse for fraud, malware, disallowed content.",
       ["Usage policies", "Abuse monitoring"]),
      ("system_compromise", "System compromise",
       "Model or supply-chain compromise.",
       ["Dependency scanning", "Model signing"])]),
    ("accountability", "Accountability",
     "Clear ownership, auditability, and recourse.",
     [("ownership_gaps", "Ownership gaps",
       "No accountable owner for system behavior.",
       ["RACI for AI systems", "Incident runbooks"]),
      ("audit_trail", "Audit trail",
       "Decisions and data flows not traceable.",
       ["Immutable audit logs", "Provenance tracking"])]),
    ("hallucination", "Hallucination",
     "Confident but false or fabricated outputs.",
     [("factual_fabrication", "Factual fabrication",
       "Invented facts/citations presented as true.",
       ["Grounding/RAG", "Citation requirements"]),
      ("overconfidence", "Overconfidence",
       "High-certainty tone on uncertain content.",
       ["Calibrated uncertainty", "Hedging guidelines"])]),
]

TAXONOMIES = [
    {"key": "ibm", "name": "IBM AI Risk Atlas", "version": "1.0",
     "description": "IBM risk taxonomy: fairness, explainability, "
                    "robustness, privacy, value alignment.",
     "source_uri": "https://github.com/IBM/ai-risk-atlas",
     "template_name": "IBM AI Risk Atlas - baseline assessment"},
    {"key": "mit", "name": "MIT AI Risk Repository", "version": "1.0",
     "description": "MIT Domain Taxonomy (Slattery et al. 2024).",
     "source_uri": "https://airisk.mit.edu",
     "template_name": "MIT AI Risk Repository - baseline assessment"},
]


def _build_template_structure():
    sections = []
    for cat_key, cat_name, _desc, factors in CATEGORIES:
        questions = [{"id": cat_key + "." + fk,
                      "text": "How does the system mitigate " + fn.lower() + "?",
                      "factor_key": fk, "weight": 1.0}
                     for fk, fn, _fd, _g in factors]
        sections.append({"title": cat_name, "category_key": cat_key,
                         "questions": questions})
    return {"sections": sections}


def seed():
    session = db_manager.get_session().__enter__()
    created = {"taxonomies": 0, "categories": 0, "factors": 0, "templates": 0}
    try:
        for tax in TAXONOMIES:
            exists = session.execute(
                text("SELECT id FROM risk_taxonomies WHERE key = :k"),
                {"k": tax["key"]}).scalar()
            if exists:
                print("skip taxonomy '%s' (already seeded)" % tax["key"])
                continue
            taxonomy_id = str(uuid.uuid4())
            now = _now()
            session.execute(text(
                "INSERT INTO risk_taxonomies (id, key, name, version, "
                "description, source_uri, is_active, created_at, updated_at) "
                "VALUES (:id, :key, :name, :version, :desc, :uri, 1, :now, :now)"),
                {"id": taxonomy_id, "key": tax["key"], "name": tax["name"],
                 "version": tax["version"], "desc": tax["description"],
                 "uri": tax["source_uri"], "now": now})
            created["taxonomies"] += 1
            for order, (cat_key, cat_name, cat_desc, factors) in enumerate(CATEGORIES):
                category_id = str(uuid.uuid4())
                session.execute(text(
                    "INSERT INTO risk_categories (id, taxonomy_id, key, name, "
                    "description, sort_order, created_at, updated_at) "
                    "VALUES (:id, :tid, :key, :name, :desc, :ord, :now, :now)"),
                    {"id": category_id, "tid": taxonomy_id, "key": cat_key,
                     "name": cat_name, "desc": cat_desc, "ord": order, "now": now})
                created["categories"] += 1
                for forg, (fkey, fname, fdesc, guidance) in enumerate(factors):
                    session.execute(text(
                        "INSERT INTO risk_factors (id, category_id, key, name, "
                        "description, guidance_json, sort_order, created_at, "
                        "updated_at) VALUES (:id, :cid, :key, :name, :desc, "
                        ":guid, :ord, :now, :now)"),
                        {"id": str(uuid.uuid4()), "cid": category_id,
                         "key": fkey, "name": fname, "desc": fdesc,
                         "guid": json.dumps(guidance), "ord": forg, "now": now})
                    created["factors"] += 1
            session.execute(text(
                "INSERT INTO risk_assessment_templates (id, taxonomy_id, name, "
                "version, description, structure_json, is_active, created_at, "
                "updated_at) VALUES (:id, :tid, :name, '1.0', :desc, :struct, "
                "1, :now, :now)"),
                {"id": str(uuid.uuid4()), "tid": taxonomy_id,
                 "name": tax["template_name"],
                 "desc": "Baseline questionnaire for " + tax["name"] + ".",
                 "struct": json.dumps(_build_template_structure()), "now": now})
            created["templates"] += 1
            print("seeded taxonomy '%s'" % tax["key"])
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return created


def main():
    parser = argparse.ArgumentParser(description="Seed risk taxonomy (issue #157)")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    if args.database_url:
        import os
        os.environ["DATABASE_URL"] = args.database_url
    print(json.dumps(seed(), indent=2))


if __name__ == "__main__":
    main()


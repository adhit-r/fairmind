#!/usr/bin/env python3
"""
Seed script for the risk taxonomy data model (Issue #157).

Populates risk_taxonomies / risk_categories / risk_factors /
risk_assessment_templates with the initial IBM AI Risk Atlas and
MIT AI Risk Repository taxonomies. Each taxonomy is seeded with its
own published categories so audit output correctly reflects the
source framework.

Factual basis:
- IBM AI Risk Atlas (github.com/IBM/ai-risk-atlas)
- MIT AI Risk Repository (airisk.mit.edu, Slattery et al. 2024)

Usage:
cd apps/backend
python scripts/seed_risk_taxonomy.py [--database-url sqlite:///dev.db]

Idempotent: re-running skips taxonomies whose \`key\` already exists.
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


# Each factor tuple: (key, name, description, guidance_list)
IBM_FAIRNESS_FACTORS = [
("data_bias", "Data bias",
 "Training data that under- or mis-represents groups.",
 ["Audit dataset composition", "Representative sampling"]),
("representation_disparity", "Representation disparity",
 "Performance gaps across protected attributes.",
 ["Disaggregated evaluation", "Fairness metrics per group"]),
("outcome_disparity", "Outcome disparity",
 "Decisions disadvantaging protected groups.",
 ["Impact assessments", "Human review of high-stakes outputs"]),
]

IBM_EXPLAINABILITY_FACTORS = [
("model_opacity", "Model opacity",
 "Outputs without inspectable reasoning.",
 ["Model cards", "Rationale traces where feasible"]),
("stakeholder_communication", "Stakeholder communication",
 "Explanations not adapted to users/auditors.",
 ["Layered explanations", "Published evaluation summaries"]),
]

IBM_ROBUSTNESS_FACTORS = [
("distribution_shift", "Distribution shift",
 "Degradation on out-of-distribution inputs.",
 ["OOD test suites", "Drift monitoring"]),
("adversarial_inputs", "Adversarial inputs",
 "Prompt injection, jailbreaks, poisoning.",
 ["Red-teaming", "Input/output guardrails"]),
]

IBM_PRIVACY_FACTORS = [
("training_data_leakage", "Training data leakage",
 "Memorized PII regurgitated at inference.",
 ["PII scrubbing", "Membership-inference testing"]),
("inference_disclosure", "Inference-time disclosure",
 "Sensitive user data exposed via logs/outputs.",
 ["Data minimization", "Retention policies"]),
]

IBM_SECURITY_FACTORS = [
("malicious_use", "Malicious use",
 "Abuse for fraud, malware, disallowed content.",
 ["Usage policies", "Abuse monitoring"]),
("system_compromise", "System compromise",
 "Model or supply-chain compromise.",
 ["Dependency scanning", "Model signing"]),
]

IBM_ACCOUNTABILITY_FACTORS = [
("ownership_gaps", "Ownership gaps",
 "No accountable owner for system behavior.",
 ["RACI for AI systems", "Incident runbooks"]),
("audit_trail", "Audit trail",
 "Decisions and data flows not traceable.",
 ["Immutable audit logs", "Provenance tracking"]),
]

IBM_HALLUCINATION_FACTORS = [
("factual_fabrication", "Factual fabrication",
 "Invented facts/citations presented as true.",
 ["Grounding/RAG", "Citation requirements"]),
("overconfidence", "Overconfidence",
 "High-certainty tone on uncertain content.",
 ["Calibrated uncertainty", "Hedging guidelines"]),
]

IBM_VALUE_ALIGNMENT_FACTORS = [
("objective_misalignment", "Objective misalignment",
 "System optimizes for a proxy rather than intended human values.",
 ["Reward modeling review", "Human-in-the-loop validation"]),
("value_lock_in", "Value lock-in",
 "System entrenches a narrow set of values across contexts.",
 ["Pluralistic input", "Stakeholder review"]),
]

# IBM AI Risk Atlas categories
IBM_CATEGORIES = [
("fairness", "Fairness",
 "Equitable treatment across groups; freedom from unjust bias.",
 IBM_FAIRNESS_FACTORS),
("explainability", "Explainability",
 "Ability to understand and communicate system outputs.",
 IBM_EXPLAINABILITY_FACTORS),
("robustness", "Robustness",
 "Reliable behavior under shift, noise, and adversarial inputs.",
 IBM_ROBUSTNESS_FACTORS),
("privacy", "Privacy",
 "Protection of personal and sensitive information.",
 IBM_PRIVACY_FACTORS),
("security", "Security",
 "Resistance to misuse and attack.",
 IBM_SECURITY_FACTORS),
("accountability", "Accountability",
 "Clear ownership, auditability, and recourse.",
 IBM_ACCOUNTABILITY_FACTORS),
("hallucination", "Hallucination",
 "Confident but false or fabricated outputs.",
 IBM_HALLUCINATION_FACTORS),
("value_alignment", "Value Alignment",
 "Alignment with human values and societal norms.",
 IBM_VALUE_ALIGNMENT_FACTORS),
]

# MIT AI Risk Repository domain taxonomy (Slattery et al. 2024)
MIT_FACTORS = {
"discrimination_toxicity": [
    ("bias_outputs", "Biased outputs",
     "Model outputs that discriminate against protected groups.",
     ["Disaggregated evaluation", "Bias mitigation"]),
    ("toxic_language", "Toxic language",
     "Hate speech, harassment, or abusive content generation.",
     ["Content filters", "Red-teaming"]),
],
"privacy_data_governance": [
    ("data_leakage", "Data leakage",
     "Personal data exposed in model outputs or training data.",
     ["PII scrubbing", "Data minimization"]),
    ("consent_governance", "Consent and governance",
     "Data used without proper consent or governance oversight.",
     ["Data provenance tracking", "Governance audits"]),
],
"misinformation": [
    ("false_generation", "False generation",
     "Model generates false or misleading information as fact.",
     ["Grounding/RAG", "Citation requirements"]),
    ("amplification", "Amplification",
     "System amplifies existing misinformation at scale.",
     ["Source verification", "Downranking unverified claims"]),
],
"malicious_actors_misuse": [
    ("fraud_malware", "Fraud and malware",
     "AI used to generate fraudulent content or malware.",
     ["Usage policies", "Abuse monitoring"]),
    ("disallowed_content", "Disallowed content",
     "System used to produce prohibited or harmful content.",
     ["Content moderation", "Safety filters"]),
],
"human_computer_interaction": [
    ("overreliance", "Overreliance",
     "Users trust system outputs beyond warranted confidence.",
     ["Uncertainty communication", "Human-in-the-loop design"]),
    ("manipulation", "Manipulation",
     "System influences user behavior in hidden or deceptive ways.",
     ["Transparency disclosures", "User control"]),
],
"socioeconomic_environmental": [
    ("labor_impact", "Labor impact",
     "AI displaces or degrades jobs without adequate transition.",
     ["Workforce impact assessment", "Reskilling programs"]),
    ("environmental", "Environmental impact",
     "Training and inference carbon footprint and resource use.",
     ["Efficient model design", "Carbon monitoring"]),
],
"ai_safety": [
    ("system_failure", "System failure",
     "AI system fails in unsafe or unpredictable ways.",
     ["Fail-safes", "Red-teaming"]),
    ("goal_misalignment", "Goal misalignment",
     "System pursues objectives misaligned with human intent.",
     ["Reward modeling review", "Human-in-the-loop validation"]),
],
"transparency_accountability": [
    ("opacity", "Opacity",
     "System behavior not explainable or auditable.",
     ["Model cards", "Rationale traces"]),
    ("accountability_gap", "Accountability gap",
     "No clear owner responsible for system behavior.",
     ["RACI for AI systems", "Incident runbooks"]),
],
}

MIT_CATEGORIES = [
("discrimination_toxicity", "Discrimination & toxicity",
 "Outputs that discriminate against or are toxic toward groups.",
 MIT_FACTORS["discrimination_toxicity"]),
("privacy_data_governance", "Privacy & data governance",
 "Improper collection, use, or governance of personal data.",
 MIT_FACTORS["privacy_data_governance"]),
("misinformation", "Misinformation",
 "Generation or amplification of false or misleading information.",
 MIT_FACTORS["misinformation"]),
("malicious_actors_misuse", "Malicious actors & misuse",
 "Use of AI by malicious actors for harmful purposes.",
 MIT_FACTORS["malicious_actors_misuse"]),
("human_computer_interaction", "Human-computer interaction",
 "Risks from how humans interact with AI systems.",
 MIT_FACTORS["human_computer_interaction"]),
("socioeconomic_environmental", "Socioeconomic & environmental harms",
 "Broader societal and environmental impacts.",
 MIT_FACTORS["socioeconomic_environmental"]),
("ai_safety", "AI safety",
 "Risks from AI system failures, limitations, or unsafe behavior.",
 MIT_FACTORS["ai_safety"]),
("transparency_accountability", "Transparency & accountability",
 "Lack of transparency in AI systems or accountability for outputs.",
 MIT_FACTORS["transparency_accountability"]),
]

TAXONOMIES = [
{"key": "ibm", "name": "IBM AI Risk Atlas", "version": "1.0",
 "description": "IBM risk taxonomy: fairness, explainability, "
                "robustness, privacy, security, accountability, "
                "hallucination, value alignment.",
 "source_uri": "https://github.com/IBM/ai-risk-atlas",
 "template_name": "IBM AI Risk Atlas - baseline assessment",
 "categories": IBM_CATEGORIES},
{"key": "mit", "name": "MIT AI Risk Repository", "version": "1.0",
 "description": "MIT Domain Taxonomy (Slattery et al. 2024).",
 "source_uri": "https://airisk.mit.edu",
 "template_name": "MIT AI Risk Repository - baseline assessment",
 "categories": MIT_CATEGORIES},
]


def _build_template_structure(categories):
 sections = []
 for cat_key, cat_name, _desc, factors in categories:
    questions = [{"id": cat_key + "." + fk,
                  "text": "How does the system mitigate " + fn.lower() + "?",
                  "factor_key": fk, "weight": 1.0}
                 for fk, fn, _fd, _g in factors]
    sections.append({"title": cat_name, "category_key": cat_key,
                     "questions": questions})
 return {"sections": sections}


def seed():
    created = {"taxonomies": 0, "categories": 0, "factors": 0, "templates": 0}
    try:
        with db_manager.get_session() as session:
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
                    "VALUES (:id, :key, :name, :version, :desc, :uri, true, "
                    ":now, :now)"),
                    {"id": taxonomy_id, "key": tax["key"], "name": tax["name"],
                     "version": tax["version"], "desc": tax["description"],
                     "uri": tax["source_uri"], "now": now})
                created["taxonomies"] += 1
                for order, (cat_key, cat_name, cat_desc, factors) in enumerate(
                        tax["categories"]):
                    category_id = str(uuid.uuid4())
                    session.execute(text(
                        "INSERT INTO risk_categories (id, taxonomy_id, key, name, "
                        "description, sort_order, created_at, updated_at) "
                        "VALUES (:id, :tid, :key, :name, :desc, :ord, :now, "
                        ":now)"),
                        {"id": category_id, "tid": taxonomy_id, "key": cat_key,
                         "name": cat_name, "desc": cat_desc, "ord": order,
                         "now": now})
                    created["categories"] += 1
                    for forg, (fkey, fname, fdesc, guidance) in enumerate(factors):
                        session.execute(text(
                            "INSERT INTO risk_factors (id, category_id, key, name, "
                            "description, guidance_json, sort_order, created_at, "
                            "updated_at) VALUES (:id, :cid, :key, :name, :desc, "
                            ":guid, :ord, :now, :now)"),
                            {"id": str(uuid.uuid4()), "cid": category_id,
                             "key": fkey, "name": fname, "desc": fdesc,
                             "guid": json.dumps(guidance), "ord": forg,
                             "now": now})
                        created["factors"] += 1
                    session.execute(text(
                        "INSERT INTO risk_assessment_templates (id, taxonomy_id, "
                        "name, version, description, structure_json, is_active, "
                        "created_at, updated_at) VALUES (:id, :tid, :name, '1.0', "
                        ":desc, :struct, true, :now, :now)"),
                        {"id": str(uuid.uuid4()), "tid": taxonomy_id,
                         "name": tax["template_name"],
                         "desc": "Baseline questionnaire for " + tax["name"] + ".",
                         "struct": json.dumps(
                             _build_template_structure(tax["categories"])),
                         "now": now})
                    created["templates"] += 1
                    print("seeded taxonomy '%s'" % tax["key"])
    except Exception:
        raise
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

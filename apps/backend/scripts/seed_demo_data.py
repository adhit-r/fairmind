"""
Seed meaningful pilot data for FairMind on Neon/Postgres.

This is intentionally "working mock" data:
- deterministic IDs (idempotent reruns)
- coherent business scenarios
- linked governance/evidence trail
- realistic fairness/compliance signals
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db_manager


NOW = datetime.now(timezone.utc)

DEMO_USER = {
    "id": "pilot-user-adhi",
    "email": "adhi@axonome.xyz",
    "username": "adhi",
    "role": "admin",
    "password_hash": "$2b$12$7TjiHtGXh1fo/DZ7J3.1oeIP8ZU.QB9mfb2gF7YnFmgQJ2bL7XHVS",
    "permissions": ["admin", "governance", "monitoring", "approvals"],
}

MODELS = [
    {
        "id": "pilot-model-credit-v1",
        "name": "Axonome Credit Scoring Alpha",
        "model_type": "classification",
        "version": "1.2.0",
        "description": "Credit underwriting model for retail lending with fairness constraints.",
        "status": "active",
        "tags": ["finance", "credit", "underwriting", "fairness"],
        "metadata": {
            "organization": "Axonome",
            "business_unit": "Retail Lending",
            "risk_tier": "high",
            "owner": "risk-ml@axonome.xyz",
            "deployment_env": "production",
        },
    },
    {
        "id": "pilot-model-hiring-v1",
        "name": "Axonome Talent Scout",
        "model_type": "nlp",
        "version": "2.0.1",
        "description": "Candidate screening and ranking assistant for recruiting operations.",
        "status": "active",
        "tags": ["hr", "hiring", "nlp", "screening"],
        "metadata": {
            "organization": "Axonome",
            "business_unit": "People Operations",
            "risk_tier": "medium",
            "owner": "people-analytics@axonome.xyz",
            "deployment_env": "staging",
        },
    },
]

DATASETS = [
    {
        "id": "pilot-ds-credit-q1",
        "name": "Credit Applicants Q1 2026",
        "description": "Quarterly credit applicant cohort with protected attributes and outcomes.",
        "source": "s3://axonome-risk/credit/q1-2026.csv",
        "file_type": "csv",
        "row_count": 120000,
        "column_count": 42,
        "columns": [
            "applicant_income",
            "credit_history_length",
            "debt_to_income",
            "region",
            "gender",
            "age_band",
            "approval_label",
        ],
        "schema_json": {
            "gender": "category",
            "age_band": "category",
            "approval_label": "int",
        },
        "tags": ["credit", "regulated", "pilot"],
    },
    {
        "id": "pilot-ds-hiring-q1",
        "name": "Hiring Pipeline Q1 2026",
        "description": "Recruitment funnel dataset for screening fairness and drift checks.",
        "source": "s3://axonome-people/hiring/q1-2026.csv",
        "file_type": "csv",
        "row_count": 87000,
        "column_count": 31,
        "columns": [
            "years_experience",
            "skill_score",
            "education_level",
            "gender",
            "ethnicity",
            "shortlist_label",
        ],
        "schema_json": {
            "gender": "category",
            "ethnicity": "category",
            "shortlist_label": "int",
        },
        "tags": ["hiring", "fairness", "pilot"],
    },
]

BIAS_ANALYSES = [
    {
        "id": "pilot-bias-credit-dp",
        "model_id": "pilot-model-credit-v1",
        "dataset_id": "pilot-ds-credit-q1",
        "analysis_type": "demographic_parity",
        "status": "completed",
        "results": {
            "passed": False,
            "summary": "Disparity detected in approval rates across age_band groups.",
            "protected_attributes": ["gender", "age_band"],
        },
        "metrics": {
            "demographic_parity_difference": 0.147,
            "equalized_odds_difference": 0.091,
            "threshold": 0.1,
        },
    },
    {
        "id": "pilot-bias-hiring-eo",
        "model_id": "pilot-model-hiring-v1",
        "dataset_id": "pilot-ds-hiring-q1",
        "analysis_type": "equal_opportunity",
        "status": "completed",
        "results": {
            "passed": True,
            "summary": "No material disparity for shortlist outcomes by gender.",
            "protected_attributes": ["gender", "ethnicity"],
        },
        "metrics": {
            "demographic_parity_difference": 0.043,
            "equalized_odds_difference": 0.039,
            "threshold": 0.1,
        },
    },
]

BIAS_TEST_RESULTS = [
    {
        "id": "pilot-bias-test-credit",
        "test_name": "Credit Fairness Regression Pack",
        "bias_score": 0.62,
        "is_biased": True,
        "confidence": 0.94,
        "category": "fairness-regression",
        "explainability_method": "shap_group_delta",
        "insights": "Top disparity drivers: age_band and region interaction.",
    },
    {
        "id": "pilot-bias-test-hiring",
        "test_name": "Hiring Fairness Regression Pack",
        "bias_score": 0.18,
        "is_biased": False,
        "confidence": 0.91,
        "category": "fairness-regression",
        "explainability_method": "counterfactual_pairs",
        "insights": "Stable parity across shortlist decisions for monitored groups.",
    },
]

COMPLIANCE_RESULTS = [
    {
        "id": "pilot-compliance-dpdp-credit",
        "compliance_score": 0.74,
        "framework": "DPDP_2023",
        "status": "needs_remediation",
    },
    {
        "id": "pilot-compliance-euai-hiring",
        "compliance_score": 0.88,
        "framework": "EU_AI_ACT",
        "status": "pass_with_observations",
    },
]

GOVERNANCE_POLICY = {
    "id": "pilot-policy-credit-release-gate",
    "name": "Credit Model Release Gate",
    "framework": "DPDP_2023",
    "description": "Block production release when fairness disparity exceeds threshold.",
    "status": "submitted",
    "rules_json": {
        "max_demographic_parity_difference": 0.1,
        "required_evidence_types": ["bias_report", "risk_assessment", "approval_record"],
        "required_approvers": ["compliance_lead", "model_risk_officer"],
    },
}

APPROVAL_WORKFLOW = {
    "id": "pilot-workflow-credit",
    "name": "Credit Release Approvals",
    "entity_type": "policy",
    "steps_json": [
        {"step": 1, "role": "compliance_lead", "sla_hours": 24},
        {"step": 2, "role": "model_risk_officer", "sla_hours": 24},
    ],
    "is_active": True,
}

APPROVAL_REQUEST = {
    "id": "pilot-approval-request-credit",
    "workflow_id": "pilot-workflow-credit",
    "entity_type": "policy",
    "entity_id": "pilot-policy-credit-release-gate",
    "requested_by": DEMO_USER["id"],
    "status": "pending",
    "current_step": 1,
    "decision_notes": "Awaiting compliance sign-off after remediation plan publication.",
}

EVIDENCE = {
    "id": "pilot-evidence-credit-bias",
    "system_id": "pilot-model-credit-v1",
    "evidence_type": "bias_report",
    "confidence": 0.93,
    "content_json": {
        "analysis_id": "pilot-bias-credit-dp",
        "finding": "Age band disparity above threshold",
        "recommended_action": "Apply calibrated post-processing and reassess",
    },
    "metadata_json": {
        "owner": "risk-ml@axonome.xyz",
        "generated_by": "seed_demo_data.py",
    },
}

EVIDENCE_LINK = {
    "id": "pilot-evidence-link-credit",
    "evidence_id": "pilot-evidence-credit-bias",
    "entity_type": "policy",
    "entity_id": "pilot-policy-credit-release-gate",
}

AUDIT_EVENTS = [
    ("model_registered", "models", "pilot-model-credit-v1", "Credit scoring model onboarded"),
    ("dataset_registered", "datasets", "pilot-ds-credit-q1", "Credit dataset validated and catalogued"),
    ("bias_analysis_completed", "bias_analyses", "pilot-bias-credit-dp", "Disparity finding raised"),
    ("policy_submitted", "governance_policies", "pilot-policy-credit-release-gate", "Release gate submitted for approval"),
]


def seed_demo_data() -> bool:
    print("=" * 80)
    print("Seeding Meaningful Pilot Data (Axonome)")
    print("=" * 80)

    if not db_manager.test_connection():
        print("ERROR: Database connection failed")
        return False

    with db_manager.get_session() as session:
        # User
        session.execute(
            text(
                """
                INSERT INTO users (id, email, username, role, password_hash, is_active, permissions, created_at, updated_at)
                VALUES (:id, :email, :username, :role, :password_hash, true, CAST(:permissions AS jsonb), :created_at, :updated_at)
                ON CONFLICT (email) DO UPDATE SET
                  email = EXCLUDED.email,
                  username = EXCLUDED.username,
                  role = EXCLUDED.role,
                  password_hash = EXCLUDED.password_hash,
                  permissions = EXCLUDED.permissions,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                **DEMO_USER,
                "permissions": json.dumps(DEMO_USER["permissions"]),
                "created_at": NOW - timedelta(days=30),
                "updated_at": NOW,
            },
        )
        user_row = session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": DEMO_USER["email"]},
        ).fetchone()
        active_user_id = str(user_row[0]) if user_row else DEMO_USER["id"]

        # Models
        for model in MODELS:
            session.execute(
                text(
                    """
                    INSERT INTO models (id, name, description, model_type, version, status, tags, metadata, created_by, upload_date, updated_at, file_path, file_size)
                    VALUES (:id, :name, :description, :model_type, :version, :status, CAST(:tags AS jsonb), CAST(:metadata AS jsonb), :created_by, :upload_date, :updated_at, :file_path, :file_size)
                    ON CONFLICT (id) DO UPDATE SET
                      name = EXCLUDED.name,
                      description = EXCLUDED.description,
                      model_type = EXCLUDED.model_type,
                      version = EXCLUDED.version,
                      status = EXCLUDED.status,
                      tags = EXCLUDED.tags,
                      metadata = EXCLUDED.metadata,
                      updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    **model,
                    "tags": json.dumps(model["tags"]),
                    "metadata": json.dumps(model["metadata"]),
                    "created_by": active_user_id,
                    "upload_date": NOW - timedelta(days=15),
                    "updated_at": NOW - timedelta(days=1),
                    "file_path": f"/models/{model['id']}.pkl",
                    "file_size": 5 * 1024 * 1024,
                },
            )

        # Datasets
        for ds in DATASETS:
            session.execute(
                text(
                    """
                    INSERT INTO datasets (id, name, description, source, file_path, file_type, file_size, row_count, column_count, columns, schema_json, tags, created_by, upload_date, updated_at, size)
                    VALUES (:id, :name, :description, :source, :file_path, :file_type, :file_size, :row_count, :column_count, CAST(:columns AS jsonb), CAST(:schema_json AS jsonb), CAST(:tags AS jsonb), :created_by, :upload_date, :updated_at, :size)
                    ON CONFLICT (id) DO UPDATE SET
                      name = EXCLUDED.name,
                      description = EXCLUDED.description,
                      source = EXCLUDED.source,
                      file_type = EXCLUDED.file_type,
                      row_count = EXCLUDED.row_count,
                      column_count = EXCLUDED.column_count,
                      columns = EXCLUDED.columns,
                      schema_json = EXCLUDED.schema_json,
                      tags = EXCLUDED.tags,
                      updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    **ds,
                    "file_path": f"/datasets/{ds['id']}.csv",
                    "file_size": ds["row_count"] * 64,
                    "size": ds["row_count"] * 64,
                    "columns": json.dumps(ds["columns"]),
                    "schema_json": json.dumps(ds["schema_json"]),
                    "tags": json.dumps(ds["tags"]),
                    "created_by": active_user_id,
                    "upload_date": NOW - timedelta(days=10),
                    "updated_at": NOW - timedelta(days=1),
                },
            )

        # Bias analyses
        for analysis in BIAS_ANALYSES:
            session.execute(
                text(
                    """
                    INSERT INTO bias_analyses (id, model_id, dataset_id, analysis_type, status, results, metrics, created_by, created_at, completed_at)
                    VALUES (:id, :model_id, :dataset_id, :analysis_type, :status, CAST(:results AS jsonb), CAST(:metrics AS jsonb), :created_by, :created_at, :completed_at)
                    ON CONFLICT (id) DO UPDATE SET
                      status = EXCLUDED.status,
                      results = EXCLUDED.results,
                      metrics = EXCLUDED.metrics,
                      completed_at = EXCLUDED.completed_at
                    """
                ),
                {
                    **analysis,
                    "results": json.dumps(analysis["results"]),
                    "metrics": json.dumps(analysis["metrics"]),
                    "created_by": active_user_id,
                    "created_at": NOW - timedelta(days=3),
                    "completed_at": NOW - timedelta(days=2),
                },
            )

        # Bias test results
        for result in BIAS_TEST_RESULTS:
            session.execute(
                text(
                    """
                    INSERT INTO bias_test_results (id, test_name, bias_score, is_biased, confidence, category, explainability_method, insights, created_at, updated_at)
                    VALUES (:id, :test_name, :bias_score, :is_biased, :confidence, :category, :explainability_method, :insights, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                      bias_score = EXCLUDED.bias_score,
                      is_biased = EXCLUDED.is_biased,
                      confidence = EXCLUDED.confidence,
                      insights = EXCLUDED.insights,
                      updated_at = EXCLUDED.updated_at
                    """
                ),
                {**result, "created_at": NOW - timedelta(days=2), "updated_at": NOW - timedelta(days=1)},
            )

        # Compliance results
        for row in COMPLIANCE_RESULTS:
            session.execute(
                text(
                    """
                    INSERT INTO compliance_results (id, compliance_score, framework, status, created_at)
                    VALUES (:id, :compliance_score, :framework, :status, :created_at)
                    ON CONFLICT (id) DO UPDATE SET
                      compliance_score = EXCLUDED.compliance_score,
                      framework = EXCLUDED.framework,
                      status = EXCLUDED.status
                    """
                ),
                {**row, "created_at": NOW - timedelta(days=1)},
            )

        # Governance artifacts
        session.execute(
            text(
                """
                INSERT INTO governance_policies (id, name, framework, description, rules_json, status, created_at, updated_at)
                VALUES (:id, :name, :framework, :description, :rules_json, :status, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                  name = EXCLUDED.name,
                  description = EXCLUDED.description,
                  rules_json = EXCLUDED.rules_json,
                  status = EXCLUDED.status,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                **GOVERNANCE_POLICY,
                "rules_json": json.dumps(GOVERNANCE_POLICY["rules_json"]),
                "created_at": NOW - timedelta(days=2),
                "updated_at": NOW - timedelta(days=1),
            },
        )

        session.execute(
            text(
                """
                INSERT INTO governance_approval_workflows (id, name, entity_type, steps_json, is_active, created_at, updated_at)
                VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                  name = EXCLUDED.name,
                  steps_json = EXCLUDED.steps_json,
                  is_active = EXCLUDED.is_active,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                **APPROVAL_WORKFLOW,
                "steps_json": json.dumps(APPROVAL_WORKFLOW["steps_json"]),
                "created_at": NOW - timedelta(days=2),
                "updated_at": NOW - timedelta(days=1),
            },
        )

        session.execute(
            text(
                """
                INSERT INTO governance_approval_requests (id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at)
                VALUES (:id, :workflow_id, :entity_type, :entity_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                  status = EXCLUDED.status,
                  current_step = EXCLUDED.current_step,
                  decision_notes = EXCLUDED.decision_notes,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {**APPROVAL_REQUEST, "created_at": NOW - timedelta(days=1), "updated_at": NOW},
        )

        session.execute(
            text(
                """
                INSERT INTO governance_evidence (id, system_id, evidence_type, content_json, confidence, metadata_json, created_at)
                VALUES (:id, :system_id, :evidence_type, :content_json, :confidence, :metadata_json, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                  content_json = EXCLUDED.content_json,
                  confidence = EXCLUDED.confidence,
                  metadata_json = EXCLUDED.metadata_json
                """
            ),
            {
                **EVIDENCE,
                "content_json": json.dumps(EVIDENCE["content_json"]),
                "metadata_json": json.dumps(EVIDENCE["metadata_json"]),
                "created_at": NOW - timedelta(days=1),
            },
        )

        session.execute(
            text(
                """
                INSERT INTO governance_evidence_links (id, evidence_id, entity_type, entity_id, created_at)
                VALUES (:id, :evidence_id, :entity_type, :entity_id, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                  evidence_id = EXCLUDED.evidence_id,
                  entity_id = EXCLUDED.entity_id
                """
            ),
            {**EVIDENCE_LINK, "created_at": NOW - timedelta(days=1)},
        )

        # Audit trail
        for idx, (action, resource_type, resource_id, message) in enumerate(AUDIT_EVENTS, start=1):
            session.execute(
                text(
                    """
                    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, created_at)
                    VALUES (:user_id, :action, :resource_type, :resource_id, CAST(:details AS jsonb), :created_at)
                    """
                ),
                    {
                    "user_id": active_user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": json.dumps({"message": message, "source": "meaningful_seed"}),
                    "created_at": NOW - timedelta(hours=idx * 3),
                },
            )

        session.commit()

    print("✓ Meaningful pilot seed complete.")
    print("  - User: adhi@axonome.xyz")
    print("  - Models: credit scoring + hiring assistant")
    print("  - Datasets: linked to model scenarios")
    print("  - Bias/compliance findings: realistic mixed outcomes")
    print("  - Governance approvals + evidence: populated")
    return True


if __name__ == "__main__":
    seed_demo_data()

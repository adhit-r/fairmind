#!/usr/bin/env python3
"""
Create/patch runtime-required tables for Neon (idempotent).
"""

import os
from sqlalchemy import create_engine, text


SQL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS bias_test_results (
        id TEXT PRIMARY KEY,
        test_name TEXT,
        bias_score DOUBLE PRECISION DEFAULT 0,
        is_biased BOOLEAN DEFAULT FALSE,
        confidence DOUBLE PRECISION DEFAULT 0,
        category TEXT,
        explainability_method TEXT,
        insights TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulation_runs (
        id TEXT PRIMARY KEY,
        model_id TEXT,
        dataset_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS compliance_results (
        id TEXT PRIMARY KEY,
        compliance_score DOUBLE PRECISION DEFAULT 0,
        framework TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        avatar_url TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS geographic_bias_analyses (
        id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        source_country TEXT NOT NULL,
        target_country TEXT NOT NULL,
        bias_score DOUBLE PRECISION,
        risk_level TEXT,
        cultural_factors JSONB DEFAULT '{}'::jsonb,
        compliance_status TEXT DEFAULT 'pending',
        analysis_date TIMESTAMPTZ DEFAULT NOW(),
        created_by TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_bom_documents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        description TEXT NOT NULL,
        project_name TEXT NOT NULL,
        organization TEXT NOT NULL,
        overall_risk_level TEXT NOT NULL,
        overall_compliance_status TEXT NOT NULL,
        total_components INTEGER DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        tags JSONB DEFAULT '[]'::jsonb,
        risk_assessment JSONB DEFAULT '{}'::jsonb,
        compliance_report JSONB DEFAULT '{}'::jsonb,
        recommendations JSONB DEFAULT '[]'::jsonb,
        data_layer JSONB DEFAULT '{}'::jsonb,
        model_development_layer JSONB DEFAULT '{}'::jsonb,
        infrastructure_layer JSONB DEFAULT '{}'::jsonb,
        deployment_layer JSONB DEFAULT '{}'::jsonb,
        monitoring_layer JSONB DEFAULT '{}'::jsonb,
        security_layer JSONB DEFAULT '{}'::jsonb,
        compliance_layer JSONB DEFAULT '{}'::jsonb
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_bom_components (
        id TEXT PRIMARY KEY,
        bom_id TEXT NOT NULL REFERENCES ai_bom_documents(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        version TEXT NOT NULL,
        description TEXT NOT NULL,
        vendor TEXT,
        license TEXT,
        risk_level TEXT NOT NULL,
        compliance_status TEXT NOT NULL,
        dependencies JSONB DEFAULT '[]'::jsonb,
        component_metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_bom_analyses (
        id TEXT PRIMARY KEY,
        bom_id TEXT NOT NULL REFERENCES ai_bom_documents(id) ON DELETE CASCADE,
        analysis_type TEXT NOT NULL,
        risk_score DOUBLE PRECISION NOT NULL,
        compliance_score DOUBLE PRECISION NOT NULL,
        security_score DOUBLE PRECISION NOT NULL,
        performance_score DOUBLE PRECISION NOT NULL,
        cost_analysis JSONB DEFAULT '{}'::jsonb,
        recommendations JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # Governance tables used by /api/v1/ai-governance routes.
    """
    CREATE TABLE IF NOT EXISTS governance_policies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        framework TEXT NOT NULL,
        description TEXT,
        rules_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_approval_workflows (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        steps_json TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_approval_requests (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL REFERENCES governance_approval_workflows(id) ON DELETE CASCADE,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        requested_by TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        current_step INTEGER DEFAULT 1,
        decision_notes TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_evidence (
        id TEXT PRIMARY KEY,
        system_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        content_json TEXT NOT NULL,
        confidence DOUBLE PRECISION,
        metadata_json TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_evidence_links (
        id TEXT PRIMARY KEY,
        evidence_id TEXT NOT NULL REFERENCES governance_evidence(id) ON DELETE CASCADE,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # Patch datasets table used by /api/v1/core/datasets insert path.
    "ALTER TABLE datasets ADD COLUMN IF NOT EXISTS size BIGINT",
]


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    engine = create_engine(database_url)
    with engine.begin() as conn:
        for stmt in SQL_STATEMENTS:
            conn.execute(text(stmt))

    print("Neon runtime table migration complete.")


if __name__ == "__main__":
    main()


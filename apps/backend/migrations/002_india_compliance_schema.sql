-- India Compliance Automation Schema
-- This migration creates tables for India-specific AI compliance tracking

-- India compliance evidence table
CREATE TABLE IF NOT EXISTS india_compliance_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id VARCHAR(255) NOT NULL,
    control_id VARCHAR(50) NOT NULL,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_data JSONB NOT NULL,
    evidence_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India compliance results table
CREATE TABLE IF NOT EXISTS india_compliance_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    framework VARCHAR(100) NOT NULL,
    overall_score FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    requirements_met INTEGER NOT NULL,
    total_requirements INTEGER NOT NULL,
    evidence_count INTEGER NOT NULL,
    results JSONB NOT NULL,
    gaps JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India bias test results table
CREATE TABLE IF NOT EXISTS india_bias_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    bias_type VARCHAR(100) NOT NULL,
    bias_detected BOOLEAN NOT NULL,
    severity VARCHAR(50),
    affected_groups JSONB,
    fairness_metrics JSONB NOT NULL,
    recommendations JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India compliance reports table
CREATE TABLE IF NOT EXISTS india_compliance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    frameworks JSONB NOT NULL,
    overall_score FLOAT NOT NULL,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Integration credentials table
CREATE TABLE IF NOT EXISTS integration_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    integration_name VARCHAR(100) NOT NULL,
    credentials JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_india_compliance_evidence_system_id ON india_compliance_evidence(system_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_evidence_control_id ON india_compliance_evidence(control_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_evidence_collected_at ON india_compliance_evidence(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_india_compliance_evidence_source ON india_compliance_evidence(source);

CREATE INDEX IF NOT EXISTS idx_india_compliance_results_system_id ON india_compliance_results(system_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_results_user_id ON india_compliance_results(user_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_results_framework ON india_compliance_results(framework);
CREATE INDEX IF NOT EXISTS idx_india_compliance_results_status ON india_compliance_results(status);
CREATE INDEX IF NOT EXISTS idx_india_compliance_results_timestamp ON india_compliance_results(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_india_bias_test_results_system_id ON india_bias_test_results(system_id);
CREATE INDEX IF NOT EXISTS idx_india_bias_test_results_user_id ON india_bias_test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_india_bias_test_results_model_id ON india_bias_test_results(model_id);
CREATE INDEX IF NOT EXISTS idx_india_bias_test_results_bias_type ON india_bias_test_results(bias_type);
CREATE INDEX IF NOT EXISTS idx_india_bias_test_results_timestamp ON india_bias_test_results(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_india_compliance_reports_system_id ON india_compliance_reports(system_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_reports_user_id ON india_compliance_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_india_compliance_reports_generated_at ON india_compliance_reports(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_integration_credentials_user_id ON integration_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_integration_credentials_integration_name ON integration_credentials(integration_name);
CREATE INDEX IF NOT EXISTS idx_integration_credentials_status ON integration_credentials(status);

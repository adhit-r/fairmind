-- India Compliance Metrics Table
-- Stores metrics for monitoring and observability

CREATE TABLE IF NOT EXISTS india_compliance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_type VARCHAR(100) NOT NULL,
    
    -- Compliance check metrics
    system_id VARCHAR(255),
    framework VARCHAR(100),
    latency_ms FLOAT,
    status VARCHAR(50),
    requirements_met INTEGER,
    total_requirements INTEGER,
    compliance_score FLOAT,
    
    -- Integration metrics
    integration_name VARCHAR(100),
    success BOOLEAN,
    evidence_count INTEGER,
    error_message TEXT,
    
    -- AI automation metrics
    automation_type VARCHAR(100),
    tokens_used INTEGER,
    
    -- Evidence collection metrics
    control_id VARCHAR(50),
    
    -- Bias detection metrics
    model_id VARCHAR(255),
    bias_type VARCHAR(100),
    bias_detected BOOLEAN,
    affected_groups INTEGER,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT metric_type_check CHECK (metric_type IN (
        'compliance_check_latency',
        'integration_success_rate',
        'integration_failure_rate',
        'ai_automation_usage',
        'evidence_collection_count',
        'bias_detection_count',
        'compliance_score',
        'framework_evaluation_time'
    ))
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_metric_type 
    ON india_compliance_metrics(metric_type);

CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_system_id 
    ON india_compliance_metrics(system_id);

CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_framework 
    ON india_compliance_metrics(framework);

CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_integration_name 
    ON india_compliance_metrics(integration_name);

CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_timestamp 
    ON india_compliance_metrics(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_metric_timestamp 
    ON india_compliance_metrics(metric_type, timestamp DESC);

-- Create index for time-series queries
CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_time_series 
    ON india_compliance_metrics(metric_type, system_id, timestamp DESC);

-- Create index for integration metrics
CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_integration_time 
    ON india_compliance_metrics(integration_name, timestamp DESC);

-- Create index for automation metrics
CREATE INDEX IF NOT EXISTS idx_india_compliance_metrics_automation_time 
    ON india_compliance_metrics(automation_type, timestamp DESC);

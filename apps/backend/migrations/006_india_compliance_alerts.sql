-- India Compliance Alerts Table
-- Stores alerts for monitoring and observability

CREATE TABLE IF NOT EXISTS india_compliance_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Alert identification
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    
    -- Context information
    system_id VARCHAR(255),
    framework VARCHAR(100),
    integration_name VARCHAR(100),
    model_id VARCHAR(255),
    bias_type VARCHAR(100),
    component VARCHAR(100),
    metric_name VARCHAR(100),
    
    -- Alert details
    message TEXT NOT NULL,
    alert_data JSONB,
    
    -- User information
    user_id VARCHAR(255),
    
    -- Alert status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT alert_type_check CHECK (alert_type IN (
        'compliance_status_change',
        'integration_failure',
        'regulatory_update',
        'bias_detected',
        'performance_degradation',
        'evidence_collection_failure',
        'threshold_exceeded'
    )),
    CONSTRAINT severity_check CHECK (severity IN (
        'critical',
        'high',
        'medium',
        'low',
        'info'
    ))
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_alert_type 
    ON india_compliance_alerts(alert_type);

CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_severity 
    ON india_compliance_alerts(severity);

CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_system_id 
    ON india_compliance_alerts(system_id);

CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_created_at 
    ON india_compliance_alerts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_acknowledged 
    ON india_compliance_alerts(acknowledged);

CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_user_id 
    ON india_compliance_alerts(user_id);

-- Create index for alert queries
CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_type_severity 
    ON india_compliance_alerts(alert_type, severity);

-- Create index for time-series queries
CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_time_series 
    ON india_compliance_alerts(created_at DESC, severity);

-- Create index for unacknowledged alerts
CREATE INDEX IF NOT EXISTS idx_india_compliance_alerts_unacknowledged 
    ON india_compliance_alerts(acknowledged, created_at DESC);

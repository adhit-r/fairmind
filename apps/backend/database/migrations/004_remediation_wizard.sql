-- Remediation Wizard Database Schema
-- Created: 2025-11-28
-- Purpose: Track remediation sessions, plans, and results

-- Remediation Sessions Table
CREATE TABLE IF NOT EXISTS remediation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Test/Model References
    test_id UUID REFERENCES bias_test_results(id) ON DELETE SET NULL,
    model_id UUID REFERENCES ml_models(id) ON DELETE SET NULL,
    dataset_id UUID REFERENCES datasets(id) ON DELETE SET NULL,
    
    -- Analysis Input
    bias_metrics JSONB NOT NULL,
    sensitive_attributes JSONB NOT NULL,
    
    -- Recommendations
    recommended_steps JSONB NOT NULL,  -- Array of RemediationStep objects
    estimated_total_improvement DECIMAL(5,4),
    estimated_total_time_minutes INTEGER,
    priority_score DECIMAL(5,2),
    
    -- Session Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, in_progress, completed, failed
    selected_step_ids INTEGER[],
    
    -- Results
    metrics_before JSONB,
    metrics_after JSONB,
    actual_improvement DECIMAL(5,4),
    generated_code TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_by UUID  -- Future: link to user when auth is implemented
);

-- Remediation Step Applications Table
CREATE TABLE IF NOT EXISTS remediation_step_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES remediation_sessions(id) ON DELETE CASCADE,
    
    step_id INTEGER NOT NULL,
    strategy VARCHAR(50) NOT NULL,  -- reweighting, resampling, etc.
    title VARCHAR(200) NOT NULL,
    
    -- Parameters
    parameters JSONB,
    
    -- Results
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, success, failed
    metrics_before JSONB,
    metrics_after JSONB,
    improvement DECIMAL(5,4),
    execution_time_seconds INTEGER,
    error_message TEXT,
    
    -- Code
    generated_code TEXT,
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Remediation Strategy Registry Table (for tracking strategy effectiveness)
CREATE TABLE IF NOT EXISTS remediation_strategy_stats (
    strategy VARCHAR(50) PRIMARY KEY,
    
    -- Usage Stats
    total_applications INTEGER DEFAULT 0,
    successful_applications INTEGER DEFAULT 0,
    failed_applications INTEGER DEFAULT 0,
    
    -- Performance Stats
    avg_improvement DECIMAL(5,4),
    avg_execution_time_seconds INTEGER,
    
    -- Ratings
    avg_user_rating DECIMAL(3,2),
    total_ratings INTEGER DEFAULT 0,
    
    -- Timestamps
    last_used_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_remediation_sessions_model ON remediation_sessions(model_id);
CREATE INDEX idx_remediation_sessions_test ON remediation_sessions(test_id);
CREATE INDEX idx_remediation_sessions_status ON remediation_sessions(status);
CREATE INDEX idx_remediation_sessions_created ON remediation_sessions(created_at DESC);
CREATE INDEX idx_remediation_sessions_plan ON remediation_sessions(plan_id);

CREATE INDEX idx_remediation_steps_session ON remediation_step_applications(session_id);
CREATE INDEX idx_remediation_steps_status ON remediation_step_applications(status);
CREATE INDEX idx_remediation_steps_strategy ON remediation_step_applications(strategy);

-- Insert initial strategy stats
INSERT INTO remediation_strategy_stats (strategy) VALUES
    ('reweighting'),
    ('resampling'),
    ('threshold_optimization'),
    ('fairness_constraints'),
    ('adversarial_debiasing'),
    ('feature_engineering')
ON CONFLICT (strategy) DO NOTHING;

-- Function to update session timestamp on update
CREATE OR REPLACE FUNCTION update_remediation_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER remediation_session_updated
    BEFORE UPDATE ON remediation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_remediation_session_timestamp();

-- Function to update strategy stats
CREATE OR REPLACE FUNCTION update_strategy_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'success' AND OLD.status != 'success' THEN
        UPDATE remediation_strategy_stats
        SET 
            total_applications = total_applications + 1,
            successful_applications = successful_applications + 1,
            avg_improvement = CASE 
                WHEN successful_applications = 0 THEN NEW.improvement
                ELSE (avg_improvement * successful_applications + NEW.improvement) / (successful_applications + 1)
            END,
            avg_execution_time_seconds = CASE 
                WHEN successful_applications = 0 THEN NEW.execution_time_seconds
                ELSE (avg_execution_time_seconds * successful_applications + NEW.execution_time_seconds) / (successful_applications + 1)
            END,
            last_used_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE strategy = NEW.strategy;
    ELSIF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        UPDATE remediation_strategy_stats
        SET 
            total_applications = total_applications + 1,
            failed_applications = failed_applications + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE strategy = NEW.strategy;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_strategy_stats_trigger
    AFTER UPDATE ON remediation_step_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_strategy_stats();

-- View for remediation session summary
CREATE OR REPLACE VIEW remediation_session_summary AS
SELECT 
    rs.id,
    rs.plan_id,
    rs.status,
    rs.estimated_total_improvement,
    rs.actual_improvement,
    rs.created_at,
    rs.completed_at,
    COUNT(rsa.id) AS total_steps,
    COUNT(CASE WHEN rsa.status = 'success' THEN 1 END) AS successful_steps,
    COUNT(CASE WHEN rsa.status = 'failed' THEN 1 END) AS failed_steps,
    SUM(rsa.execution_time_seconds) AS total_execution_time_seconds
FROM remediation_sessions rs
LEFT JOIN remediation_step_applications rsa ON rs.id = rsa.session_id
GROUP BY rs.id, rs.plan_id, rs.status, rs.estimated_total_improvement, rs.actual_improvement, rs.created_at, rs.completed_at;

-- Comments for documentation
COMMENT ON TABLE remediation_sessions IS 'Stores bias remediation wizard sessions and results';
COMMENT ON TABLE remediation_step_applications IS 'Tracks individual remediation step applications and outcomes';
COMMENT ON TABLE remediation_strategy_stats IS 'Aggregate statistics for remediation strategy effectiveness';
COMMENT ON VIEW remediation_session_summary IS 'Summary view of remediation sessions with step counts';

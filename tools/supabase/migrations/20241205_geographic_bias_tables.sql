-- Create geographic bias analysis tables

-- Main geographic bias analysis table
CREATE TABLE IF NOT EXISTS geographic_bias_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    source_country VARCHAR(100) NOT NULL,
    target_country VARCHAR(100) NOT NULL,
    bias_detected BOOLEAN NOT NULL,
    bias_score DECIMAL(3,3) NOT NULL CHECK (bias_score >= 0 AND bias_score <= 1),
    performance_drop DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    affected_metrics JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    cultural_factors JSONB NOT NULL,
    compliance_issues JSONB NOT NULL,
    model_performance_data JSONB NOT NULL,
    demographic_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    organization_id UUID REFERENCES organizations(id)
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_geographic_bias_model_id ON geographic_bias_analyses(model_id);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_countries ON geographic_bias_analyses(source_country, target_country);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_risk_level ON geographic_bias_analyses(risk_level);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_created_at ON geographic_bias_analyses(created_at);

-- Country performance tracking table
CREATE TABLE IF NOT EXISTS country_performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    country_code VARCHAR(10) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    models_deployed INTEGER DEFAULT 0,
    avg_bias_score DECIMAL(3,3) DEFAULT 0,
    compliance_status VARCHAR(20) DEFAULT 'UNKNOWN' CHECK (compliance_status IN ('COMPLIANT', 'WARNING', 'NON_COMPLIANT', 'UNKNOWN')),
    total_analyses INTEGER DEFAULT 0,
    high_risk_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for country performance
CREATE INDEX IF NOT EXISTS idx_country_performance_code ON country_performance_metrics(country_code);
CREATE INDEX IF NOT EXISTS idx_country_performance_status ON country_performance_metrics(compliance_status);

-- Cultural factors reference table
CREATE TABLE IF NOT EXISTS cultural_factors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    factor_name VARCHAR(100) NOT NULL,
    factor_category VARCHAR(50) NOT NULL CHECK (factor_category IN ('LANGUAGE', 'ECONOMIC', 'CULTURAL', 'REGULATORY')),
    description TEXT,
    weight DECIMAL(3,3) DEFAULT 0.25 CHECK (weight >= 0 AND weight <= 1),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default cultural factors
INSERT INTO cultural_factors (factor_name, factor_category, description, weight) VALUES
('Language Differences', 'LANGUAGE', 'Linguistic variations affecting model performance', 0.3),
('Economic Factors', 'ECONOMIC', 'GDP, income levels, economic indicators', 0.25),
('Cultural Norms', 'CULTURAL', 'Social customs, traditions, behavioral patterns', 0.25),
('Regulatory Environment', 'REGULATORY', 'Data protection laws, AI regulations', 0.2)
ON CONFLICT DO NOTHING;

-- Geographic bias alerts table
CREATE TABLE IF NOT EXISTS geographic_bias_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    analysis_id UUID REFERENCES geographic_bias_analyses(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('HIGH_BIAS', 'COMPLIANCE_VIOLATION', 'PERFORMANCE_DROP', 'CULTURAL_FACTOR_CHANGE')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for alerts
CREATE INDEX IF NOT EXISTS idx_geographic_bias_alerts_type ON geographic_bias_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_alerts_severity ON geographic_bias_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_alerts_resolved ON geographic_bias_alerts(is_resolved);

-- Enable Row Level Security (RLS)
ALTER TABLE geographic_bias_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE cultural_factors ENABLE ROW LEVEL SECURITY;
ALTER TABLE geographic_bias_alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for geographic_bias_analyses
CREATE POLICY "Users can view their own organization's analyses" ON geographic_bias_analyses
    FOR SELECT USING (organization_id IN (
        SELECT organization_id FROM user_organizations 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert analyses for their organization" ON geographic_bias_analyses
    FOR INSERT WITH CHECK (organization_id IN (
        SELECT organization_id FROM user_organizations 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update their own organization's analyses" ON geographic_bias_analyses
    FOR UPDATE USING (organization_id IN (
        SELECT organization_id FROM user_organizations 
        WHERE user_id = auth.uid()
    ));

-- RLS Policies for country_performance_metrics (read-only for all authenticated users)
CREATE POLICY "Authenticated users can view country performance" ON country_performance_metrics
    FOR SELECT USING (auth.role() = 'authenticated');

-- RLS Policies for cultural_factors (read-only for all authenticated users)
CREATE POLICY "Authenticated users can view cultural factors" ON cultural_factors
    FOR SELECT USING (auth.role() = 'authenticated');

-- RLS Policies for geographic_bias_alerts
CREATE POLICY "Users can view their organization's alerts" ON geographic_bias_alerts
    FOR SELECT USING (analysis_id IN (
        SELECT id FROM geographic_bias_analyses 
        WHERE organization_id IN (
            SELECT organization_id FROM user_organizations 
            WHERE user_id = auth.uid()
        )
    ));

CREATE POLICY "Users can insert alerts for their organization" ON geographic_bias_alerts
    FOR INSERT WITH CHECK (analysis_id IN (
        SELECT id FROM geographic_bias_analyses 
        WHERE organization_id IN (
            SELECT organization_id FROM user_organizations 
            WHERE user_id = auth.uid()
        )
    ));

-- Create function to update country performance metrics
CREATE OR REPLACE FUNCTION update_country_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert country performance metrics
    INSERT INTO country_performance_metrics (country_code, country_name, models_deployed, avg_bias_score, compliance_status, total_analyses, high_risk_count)
    VALUES (
        NEW.target_country,
        NEW.target_country,
        1,
        NEW.bias_score,
        CASE 
            WHEN NEW.risk_level IN ('HIGH', 'CRITICAL') THEN 'NON_COMPLIANT'
            WHEN NEW.risk_level = 'MEDIUM' THEN 'WARNING'
            ELSE 'COMPLIANT'
        END,
        1,
        CASE WHEN NEW.risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END
    )
    ON CONFLICT (country_code) DO UPDATE SET
        models_deployed = country_performance_metrics.models_deployed + 1,
        avg_bias_score = (country_performance_metrics.avg_bias_score * country_performance_metrics.total_analyses + NEW.bias_score) / (country_performance_metrics.total_analyses + 1),
        compliance_status = CASE 
            WHEN NEW.risk_level IN ('HIGH', 'CRITICAL') THEN 'NON_COMPLIANT'
            WHEN NEW.risk_level = 'MEDIUM' THEN 'WARNING'
            ELSE 'COMPLIANT'
        END,
        total_analyses = country_performance_metrics.total_analyses + 1,
        high_risk_count = country_performance_metrics.high_risk_count + CASE WHEN NEW.risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END,
        last_updated = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update country performance metrics
CREATE TRIGGER trigger_update_country_performance
    AFTER INSERT ON geographic_bias_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_country_performance_metrics();

-- Create function to generate alerts for high-risk analyses
CREATE OR REPLACE FUNCTION generate_geographic_bias_alerts()
RETURNS TRIGGER AS $$
BEGIN
    -- Generate alert for high bias
    IF NEW.bias_score > 0.5 THEN
        INSERT INTO geographic_bias_alerts (analysis_id, alert_type, severity, message)
        VALUES (
            NEW.id,
            'HIGH_BIAS',
            CASE 
                WHEN NEW.bias_score > 0.7 THEN 'CRITICAL'
                ELSE 'HIGH'
            END,
            'High geographic bias detected: ' || NEW.bias_score || ' for model ' || NEW.model_id || ' from ' || NEW.source_country || ' to ' || NEW.target_country
        );
    END IF;
    
    -- Generate alert for compliance issues
    IF NEW.risk_level IN ('HIGH', 'CRITICAL') THEN
        INSERT INTO geographic_bias_alerts (analysis_id, alert_type, severity, message)
        VALUES (
            NEW.id,
            'COMPLIANCE_VIOLATION',
            NEW.risk_level,
            'Compliance violation detected for model ' || NEW.model_id || ' deployment from ' || NEW.source_country || ' to ' || NEW.target_country
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically generate alerts
CREATE TRIGGER trigger_generate_geographic_bias_alerts
    AFTER INSERT ON geographic_bias_analyses
    FOR EACH ROW
    EXECUTE FUNCTION generate_geographic_bias_alerts(); 
-- Initial database schema for FairMind AI Governance Platform
-- This creates the basic tables needed for the application

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    permissions JSONB DEFAULT '[]'::jsonb
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    file_path VARCHAR(500),
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'active',
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(255),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size BIGINT,
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    columns JSONB DEFAULT '[]'::jsonb,
    schema_json JSONB DEFAULT '{}'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    created_by VARCHAR(255),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Bias analyses table
CREATE TABLE IF NOT EXISTS bias_analyses (
    id VARCHAR(255) PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(255),
    analysis_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    results JSONB DEFAULT '{}'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Model metrics table for monitoring
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accuracy DECIMAL(5,4),
    bias_score DECIMAL(5,4),
    drift_score DECIMAL(5,4),
    latency DECIMAL(10,4),
    throughput DECIMAL(10,4),
    error_rate DECIMAL(5,4),
    custom_metrics JSONB DEFAULT '{}'::jsonb,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(255) PRIMARY KEY,
    model_id VARCHAR(255),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    key_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, name)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_models_created_by ON models(created_by);
CREATE INDEX IF NOT EXISTS idx_models_upload_date ON models(upload_date DESC);

CREATE INDEX IF NOT EXISTS idx_datasets_created_by ON datasets(created_by);
CREATE INDEX IF NOT EXISTS idx_datasets_upload_date ON datasets(upload_date DESC);

CREATE INDEX IF NOT EXISTS idx_bias_analyses_model_id ON bias_analyses(model_id);
CREATE INDEX IF NOT EXISTS idx_bias_analyses_status ON bias_analyses(status);
CREATE INDEX IF NOT EXISTS idx_bias_analyses_created_at ON bias_analyses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON model_metrics(model_id);
CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON model_metrics(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_model_id ON alerts(model_id);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Insert default admin user (password: admin123)
INSERT INTO users (id, email, username, password_hash, role, permissions)
VALUES (
    'admin',
    'admin@fairmind.ai',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm', -- bcrypt hash of 'admin123'
    'admin',
    '["*"]'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- Insert default analyst user (password: analyst123)
INSERT INTO users (id, email, username, password_hash, role, permissions)
VALUES (
    'analyst',
    'analyst@fairmind.ai',
    'analyst',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm', -- bcrypt hash of 'analyst123'
    'analyst',
    '["model:read", "model:write", "dataset:read", "dataset:write", "analysis:run", "analysis:read"]'::jsonb
) ON CONFLICT (id) DO NOTHING;
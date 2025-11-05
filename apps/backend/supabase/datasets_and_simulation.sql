-- Datasets and Simulation Runs Tables
-- Migration for Phase 1: Real Simulation Data Path

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Datasets table for storing uploaded CSV/Parquet files
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type TEXT NOT NULL, -- 'csv', 'parquet', etc.
    schema_json JSONB, -- Column definitions, types, etc.
    row_count INTEGER,
    column_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Simulation runs table for storing ML model execution results
CREATE TABLE IF NOT EXISTS public.simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID REFERENCES public.models(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES public.datasets(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    config_json JSONB NOT NULL, -- Simulation parameters
    results_json JSONB, -- Performance and fairness metrics
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    execution_time_ms INTEGER, -- Time taken in milliseconds
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_datasets_owner_id ON public.datasets(owner_id);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON public.datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_owner_id ON public.simulation_runs(owner_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_model_id ON public.simulation_runs(model_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_dataset_id ON public.simulation_runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_status ON public.simulation_runs(status);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_created_at ON public.simulation_runs(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_runs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for datasets table
CREATE POLICY "Users can view their own datasets" ON public.datasets
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert their own datasets" ON public.datasets
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update their own datasets" ON public.datasets
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete their own datasets" ON public.datasets
    FOR DELETE USING (auth.uid() = owner_id);

-- RLS Policies for simulation_runs table
CREATE POLICY "Users can view their own simulation runs" ON public.simulation_runs
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert their own simulation runs" ON public.simulation_runs
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update their own simulation runs" ON public.simulation_runs
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete their own simulation runs" ON public.simulation_runs
    FOR DELETE USING (auth.uid() = owner_id);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER handle_datasets_updated_at
    BEFORE UPDATE ON public.datasets
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_simulation_runs_updated_at
    BEFORE UPDATE ON public.simulation_runs
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Add comments for documentation
COMMENT ON TABLE public.datasets IS 'Stores uploaded datasets (CSV/Parquet) with metadata and schema information';
COMMENT ON TABLE public.simulation_runs IS 'Stores ML model simulation execution results and metrics';
COMMENT ON COLUMN public.datasets.schema_json IS 'JSON object containing column definitions, types, and sample data';
COMMENT ON COLUMN public.simulation_runs.config_json IS 'JSON object containing simulation parameters (target, features, protected_attributes)';
COMMENT ON COLUMN public.simulation_runs.results_json IS 'JSON object containing performance metrics, fairness metrics, and analysis results';

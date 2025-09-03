-- Phase 1 Database Migration - Execute this in Supabase SQL Editor
-- This script adds dataset management and enhanced simulation capabilities

-- Step 1: Add datasets table
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type TEXT NOT NULL CHECK (file_type IN ('csv', 'parquet')),
    schema_json JSONB,
    row_count INTEGER,
    column_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Create indexes for datasets
CREATE INDEX IF NOT EXISTS idx_datasets_owner_id ON public.datasets(owner_id);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON public.datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_datasets_file_type ON public.datasets(file_type);

-- Step 3: Enable RLS on datasets
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

-- Step 4: Add RLS policies for datasets
CREATE POLICY "Users can view their own datasets" ON public.datasets
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert their own datasets" ON public.datasets
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update their own datasets" ON public.datasets
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete their own datasets" ON public.datasets
    FOR DELETE USING (auth.uid() = owner_id);

-- Step 5: Extend existing simulation_runs table
ALTER TABLE public.simulation_runs 
ADD COLUMN IF NOT EXISTS dataset_id UUID REFERENCES public.datasets(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS config_json JSONB,
ADD COLUMN IF NOT EXISTS results_json JSONB,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER;

-- Step 6: Create new indexes for simulation_runs
CREATE INDEX IF NOT EXISTS idx_sim_runs_user_id ON public.simulation_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_dataset_id ON public.simulation_runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_status ON public.simulation_runs(status);

-- Step 7: Add updated_at trigger function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Add updated_at triggers
CREATE TRIGGER handle_datasets_updated_at
    BEFORE UPDATE ON public.datasets
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Step 9: Verify migration
SELECT 
    'datasets' as table_name,
    COUNT(*) as row_count
FROM public.datasets
UNION ALL
SELECT 
    'simulation_runs' as table_name,
    COUNT(*) as row_count
FROM public.simulation_runs;

-- Step 10: Show new columns in simulation_runs
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'simulation_runs' 
AND column_name IN ('dataset_id', 'user_id', 'config_json', 'results_json', 'status')
ORDER BY column_name;

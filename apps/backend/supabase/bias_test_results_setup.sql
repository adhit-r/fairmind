-- Create bias_test_results table for storing test history
-- This table stores all bias detection test results with full details

CREATE TABLE IF NOT EXISTS public.bias_test_results (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    dataset_id TEXT,
    test_type TEXT NOT NULL CHECK (test_type IN ('ml_bias', 'llm_bias')),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    overall_risk TEXT NOT NULL CHECK (overall_risk IN ('low', 'medium', 'high', 'critical')),
    metrics_passed INTEGER NOT NULL DEFAULT 0,
    metrics_failed INTEGER NOT NULL DEFAULT 0,
    results JSONB NOT NULL,
    summary TEXT NOT NULL,
    recommendations TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_test_results_user_id ON public.bias_test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_test_results_model_id ON public.bias_test_results(model_id);
CREATE INDEX IF NOT EXISTS idx_test_results_dataset_id ON public.bias_test_results(dataset_id);
CREATE INDEX IF NOT EXISTS idx_test_results_test_type ON public.bias_test_results(test_type);
CREATE INDEX IF NOT EXISTS idx_test_results_timestamp ON public.bias_test_results(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_test_results_overall_risk ON public.bias_test_results(overall_risk);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_test_results_user_model ON public.bias_test_results(user_id, model_id, timestamp DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE public.bias_test_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own test results
CREATE POLICY "Users can view their own test results"
    ON public.bias_test_results
    FOR SELECT
    USING (auth.uid()::text = user_id);

-- Policy: Users can insert their own test results
CREATE POLICY "Users can insert their own test results"
    ON public.bias_test_results
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- Policy: Users can update their own test results
CREATE POLICY "Users can update their own test results"
    ON public.bias_test_results
    FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Policy: Users can delete their own test results
CREATE POLICY "Users can delete their own test results"
    ON public.bias_test_results
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_test_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_test_results_updated_at
    BEFORE UPDATE ON public.bias_test_results
    FOR EACH ROW
    EXECUTE FUNCTION update_test_results_updated_at();

-- Create view for test result summaries (optimized for listing)
CREATE OR REPLACE VIEW public.test_result_summaries AS
SELECT 
    id,
    user_id,
    model_id,
    dataset_id,
    test_type,
    timestamp,
    overall_risk,
    metrics_passed,
    metrics_failed,
    summary,
    created_at
FROM public.bias_test_results
ORDER BY timestamp DESC;

-- Grant access to the view
GRANT SELECT ON public.test_result_summaries TO authenticated;

COMMENT ON TABLE public.bias_test_results IS 'Stores complete history of bias detection test results';
COMMENT ON COLUMN public.bias_test_results.id IS 'Unique test identifier (format: ml-test-YYYYMMDDHHMMSS or llm-test-YYYYMMDDHHMMSS)';
COMMENT ON COLUMN public.bias_test_results.user_id IS 'ID of the user who ran the test';
COMMENT ON COLUMN public.bias_test_results.model_id IS 'ID of the model being tested';
COMMENT ON COLUMN public.bias_test_results.dataset_id IS 'ID of the dataset used (null for LLM tests with sample data)';
COMMENT ON COLUMN public.bias_test_results.test_type IS 'Type of bias test: ml_bias or llm_bias';
COMMENT ON COLUMN public.bias_test_results.timestamp IS 'When the test was run';
COMMENT ON COLUMN public.bias_test_results.overall_risk IS 'Overall risk assessment: low, medium, high, or critical';
COMMENT ON COLUMN public.bias_test_results.metrics_passed IS 'Number of fairness metrics that passed';
COMMENT ON COLUMN public.bias_test_results.metrics_failed IS 'Number of fairness metrics that failed';
COMMENT ON COLUMN public.bias_test_results.results IS 'Complete test results including all metrics (JSONB)';
COMMENT ON COLUMN public.bias_test_results.summary IS 'Human-readable summary of test results';
COMMENT ON COLUMN public.bias_test_results.recommendations IS 'Array of recommendations for addressing bias';
COMMENT ON COLUMN public.bias_test_results.metadata IS 'Additional metadata (test parameters, configuration, etc.)';

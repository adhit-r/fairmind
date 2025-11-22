-- Create datasets table for persistent dataset storage
-- This table stores metadata about uploaded CSV datasets for bias analysis

CREATE TABLE IF NOT EXISTS public.datasets (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    rows INTEGER NOT NULL,
    columns TEXT[] NOT NULL,
    column_types JSONB NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    preview JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON public.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_uploaded_at ON public.datasets(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_file_hash ON public.datasets(file_hash);

-- Add RLS (Row Level Security) policies
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own datasets
CREATE POLICY "Users can view their own datasets"
    ON public.datasets
    FOR SELECT
    USING (auth.uid()::text = user_id);

-- Policy: Users can insert their own datasets
CREATE POLICY "Users can insert their own datasets"
    ON public.datasets
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- Policy: Users can update their own datasets
CREATE POLICY "Users can update their own datasets"
    ON public.datasets
    FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Policy: Users can delete their own datasets
CREATE POLICY "Users can delete their own datasets"
    ON public.datasets
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_datasets_updated_at
    BEFORE UPDATE ON public.datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create storage bucket for dataset files (if not exists)
-- Note: This needs to be run separately in Supabase dashboard or via API
-- INSERT INTO storage.buckets (id, name, public) 
-- VALUES ('datasets', 'datasets', false)
-- ON CONFLICT (id) DO NOTHING;

-- Add storage policies for the datasets bucket
-- CREATE POLICY "Users can upload their own datasets"
--     ON storage.objects FOR INSERT
--     WITH CHECK (bucket_id = 'datasets' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can view their own datasets"
--     ON storage.objects FOR SELECT
--     USING (bucket_id = 'datasets' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can delete their own datasets"
--     ON storage.objects FOR DELETE
--     USING (bucket_id = 'datasets' AND auth.uid()::text = (storage.foldername(name))[1]);

COMMENT ON TABLE public.datasets IS 'Stores metadata for uploaded CSV datasets used in bias detection analysis';
COMMENT ON COLUMN public.datasets.id IS 'Unique dataset identifier (format: ds_YYYYMMDDHHMMSS_hash)';
COMMENT ON COLUMN public.datasets.user_id IS 'ID of the user who uploaded the dataset';
COMMENT ON COLUMN public.datasets.filename IS 'Original filename of the uploaded CSV';
COMMENT ON COLUMN public.datasets.file_path IS 'Path to the file in Supabase Storage';
COMMENT ON COLUMN public.datasets.file_hash IS 'MD5 hash of file content for deduplication';
COMMENT ON COLUMN public.datasets.rows IS 'Number of rows in the dataset';
COMMENT ON COLUMN public.datasets.columns IS 'Array of column names';
COMMENT ON COLUMN public.datasets.column_types IS 'JSON object mapping column names to data types';
COMMENT ON COLUMN public.datasets.file_size_bytes IS 'Size of the CSV file in bytes';
COMMENT ON COLUMN public.datasets.metadata IS 'Additional metadata (uploaded_by, upload_source, etc.)';
COMMENT ON COLUMN public.datasets.preview IS 'JSON array of first 10 rows for preview';

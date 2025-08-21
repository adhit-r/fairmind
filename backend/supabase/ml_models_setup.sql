-- Create ML Models table and related enums for FairMind
-- This script sets up the database structure for the model registry

-- Create enums if they don't exist
DO $$ BEGIN
    CREATE TYPE public."RiskLevel" AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public."ModelType" AS ENUM ('classification', 'regression', 'clustering', 'nlp', 'computer_vision', 'reinforcement_learning', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public."DeploymentEnvironment" AS ENUM ('development', 'staging', 'production', 'testing', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create ML Models table
CREATE TABLE IF NOT EXISTS public.ml_models (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    type public."ModelType" NOT NULL,
    framework TEXT NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    org_id TEXT NOT NULL,
    risk_level public."RiskLevel" DEFAULT 'medium',
    deployment_environment public."DeploymentEnvironment" DEFAULT 'development',
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    performance_metrics JSONB DEFAULT '{}',
    bias_analysis JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    model_file_url TEXT,
    documentation_url TEXT,
    license TEXT,
    use_case TEXT,
    training_data_info JSONB DEFAULT '{}',
    validation_metrics JSONB DEFAULT '{}',
    deployment_info JSONB DEFAULT '{}'
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ml_models_org_id ON public.ml_models(org_id);
CREATE INDEX IF NOT EXISTS idx_ml_models_type ON public.ml_models(type);
CREATE INDEX IF NOT EXISTS idx_ml_models_risk_level ON public.ml_models(risk_level);
CREATE INDEX IF NOT EXISTS idx_ml_models_deployment_environment ON public.ml_models(deployment_environment);
CREATE INDEX IF NOT EXISTS idx_ml_models_created_at ON public.ml_models(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_models_created_by ON public.ml_models(created_by);

-- Enable Row Level Security
ALTER TABLE public.ml_models ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view models from their organization" ON public.ml_models
    FOR SELECT USING (org_id IN (
        SELECT org_id FROM public.organization_memberships 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert models for their organization" ON public.ml_models
    FOR INSERT WITH CHECK (org_id IN (
        SELECT org_id FROM public.organization_memberships 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update models from their organization" ON public.ml_models
    FOR UPDATE USING (org_id IN (
        SELECT org_id FROM public.organization_memberships 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can delete models from their organization" ON public.ml_models
    FOR DELETE USING (org_id IN (
        SELECT org_id FROM public.organization_memberships 
        WHERE user_id = auth.uid()
    ));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_ml_models_updated_at 
    BEFORE UPDATE ON public.ml_models 
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_updated_at_column();

-- Insert sample data for testing
INSERT INTO public.ml_models (
    name, version, type, framework, description, tags, org_id, 
    risk_level, deployment_environment, path, sha256, created_by
) VALUES 
(
    'Credit Risk Assessment Model',
    '2.1.0',
    'classification',
    'scikit-learn',
    'Advanced credit risk assessment model using gradient boosting for loan approval decisions',
    ARRAY['finance', 'credit', 'risk', 'lending'],
    'demo_org',
    'high',
    'production',
    'storage/models/demo_org/credit_risk_v2.1.pkl',
    'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
    '00000000-0000-0000-0000-000000000000'
),
(
    'Real-time Fraud Detection',
    '1.5.2',
    'classification',
    'tensorflow',
    'Deep learning model for real-time credit card fraud detection using transaction patterns',
    ARRAY['security', 'fraud', 'finance', 'real-time'],
    'demo_org',
    'high',
    'production',
    'storage/models/demo_org/fraud_detection_v1.5.2.h5',
    'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890',
    '00000000-0000-0000-0000-000000000000'
),
(
    'Customer Segmentation Model',
    '1.0.0',
    'clustering',
    'scikit-learn',
    'K-means clustering model for customer segmentation based on purchasing behavior',
    ARRAY['marketing', 'segmentation', 'clustering'],
    'demo_org',
    'medium',
    'staging',
    'storage/models/demo_org/customer_segmentation_v1.0.pkl',
    'c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcd',
    '00000000-0000-0000-0000-000000000000'
),
(
    'Sentiment Analysis Model',
    '1.2.1',
    'nlp',
    'pytorch',
    'BERT-based sentiment analysis model for social media monitoring',
    ARRAY['nlp', 'sentiment', 'bert', 'social-media'],
    'demo_org',
    'medium',
    'production',
    'storage/models/demo_org/sentiment_analysis_v1.2.1.pt',
    'd4e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcdef',
    '00000000-0000-0000-0000-000000000000'
),
(
    'Image Classification Model',
    '1.0.0',
    'computer_vision',
    'tensorflow',
    'CNN model for image classification trained on ImageNet dataset',
    ARRAY['computer-vision', 'cnn', 'image-classification'],
    'demo_org',
    'low',
    'development',
    'storage/models/demo_org/image_classification_v1.0.h5',
    'e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcdef12',
    '00000000-0000-0000-0000-000000000000'
)
ON CONFLICT DO NOTHING;

-- Enable realtime for the table
ALTER PUBLICATION supabase_realtime ADD TABLE public.ml_models;

-- Grant permissions
GRANT ALL ON public.ml_models TO authenticated;
GRANT ALL ON public.ml_models TO service_role;

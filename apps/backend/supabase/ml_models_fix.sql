-- Fix ML Models table issues
-- Drop existing RLS policies that reference non-existent tables
DROP POLICY IF EXISTS "Users can view models from their organization" ON public.ml_models;
DROP POLICY IF EXISTS "Users can insert models for their organization" ON public.ml_models;
DROP POLICY IF EXISTS "Users can update models from their organization" ON public.ml_models;
DROP POLICY IF EXISTS "Users can delete models from their organization" ON public.ml_models;

-- Create simpler RLS policies
CREATE POLICY "Enable read access for authenticated users" ON public.ml_models
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON public.ml_models
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.ml_models
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.ml_models
    FOR DELETE USING (auth.role() = 'authenticated');

-- Insert sample data without foreign key constraint issues
INSERT INTO public.ml_models (
    name, version, type, framework, description, tags, org_id, 
    risk_level, deployment_environment, path, sha256
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
    'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456'
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
    'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890'
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
    'c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcd'
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
    'd4e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcdef'
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
    'e5f6789012345678901234567890abcdef1234567890abcdef1234567890abcdef12'
)
ON CONFLICT DO NOTHING;

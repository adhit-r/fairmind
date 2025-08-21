-- Create AI BOM tables for FairMind (Remote Database)
-- This script sets up the database structure for the AI Bill of Materials system

-- Create AI BOM Documents table
CREATE TABLE IF NOT EXISTS public.ai_bom_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL,
    project_name TEXT NOT NULL,
    organization TEXT NOT NULL,
    overall_risk_level public."RiskLevel" NOT NULL,
    overall_compliance_status VARCHAR(20) NOT NULL,
    total_components INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    compliance_report JSONB DEFAULT '{}',
    recommendations TEXT[] DEFAULT '{}',
    
    -- Layer data
    data_layer JSONB DEFAULT '{}',
    model_development_layer JSONB DEFAULT '{}',
    infrastructure_layer JSONB DEFAULT '{}',
    deployment_layer JSONB DEFAULT '{}',
    monitoring_layer JSONB DEFAULT '{}',
    security_layer JSONB DEFAULT '{}',
    compliance_layer JSONB DEFAULT '{}'
);

-- Create AI BOM Components table
CREATE TABLE IF NOT EXISTS public.ai_bom_components (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    bom_id UUID NOT NULL REFERENCES public.ai_bom_documents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL,
    vendor TEXT,
    license TEXT,
    risk_level public."RiskLevel" NOT NULL,
    compliance_status VARCHAR(20) NOT NULL,
    dependencies TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create AI BOM Analyses table
CREATE TABLE IF NOT EXISTS public.ai_bom_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    bom_id UUID NOT NULL REFERENCES public.ai_bom_documents(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL,
    risk_score FLOAT NOT NULL,
    compliance_score FLOAT NOT NULL,
    security_score FLOAT NOT NULL,
    performance_score FLOAT NOT NULL,
    cost_analysis JSONB DEFAULT '{}',
    recommendations TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_bom_documents_created_by ON public.ai_bom_documents(created_by);
CREATE INDEX IF NOT EXISTS idx_ai_bom_documents_project_name ON public.ai_bom_documents(project_name);
CREATE INDEX IF NOT EXISTS idx_ai_bom_documents_risk_level ON public.ai_bom_documents(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_ai_bom_documents_created_at ON public.ai_bom_documents(created_at);

CREATE INDEX IF NOT EXISTS idx_ai_bom_components_bom_id ON public.ai_bom_components(bom_id);
CREATE INDEX IF NOT EXISTS idx_ai_bom_components_type ON public.ai_bom_components(type);
CREATE INDEX IF NOT EXISTS idx_ai_bom_components_risk_level ON public.ai_bom_components(risk_level);

CREATE INDEX IF NOT EXISTS idx_ai_bom_analyses_bom_id ON public.ai_bom_analyses(bom_id);
CREATE INDEX IF NOT EXISTS idx_ai_bom_analyses_type ON public.ai_bom_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_ai_bom_analyses_created_at ON public.ai_bom_analyses(created_at);

-- Enable Row Level Security
ALTER TABLE public.ai_bom_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_bom_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_bom_analyses ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for AI BOM Documents
CREATE POLICY "Enable read access for authenticated users" ON public.ai_bom_documents
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON public.ai_bom_documents
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.ai_bom_documents
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.ai_bom_documents
    FOR DELETE USING (auth.role() = 'authenticated');

-- Create RLS policies for AI BOM Components
CREATE POLICY "Enable read access for authenticated users" ON public.ai_bom_components
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON public.ai_bom_components
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.ai_bom_components
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.ai_bom_components
    FOR DELETE USING (auth.role() = 'authenticated');

-- Create RLS policies for AI BOM Analyses
CREATE POLICY "Enable read access for authenticated users" ON public.ai_bom_analyses
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for authenticated users" ON public.ai_bom_analyses
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.ai_bom_analyses
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.ai_bom_analyses
    FOR DELETE USING (auth.role() = 'authenticated');

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_ai_bom_documents_updated_at 
    BEFORE UPDATE ON public.ai_bom_documents 
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_ai_bom_components_updated_at 
    BEFORE UPDATE ON public.ai_bom_components 
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_updated_at_column();

-- Enable realtime for the tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_bom_documents;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_bom_components;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_bom_analyses;

-- Grant permissions
GRANT ALL ON public.ai_bom_documents TO authenticated;
GRANT ALL ON public.ai_bom_documents TO service_role;
GRANT ALL ON public.ai_bom_components TO authenticated;
GRANT ALL ON public.ai_bom_components TO service_role;
GRANT ALL ON public.ai_bom_analyses TO authenticated;
GRANT ALL ON public.ai_bom_analyses TO service_role;

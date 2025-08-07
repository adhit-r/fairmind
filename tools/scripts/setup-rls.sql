-- Enable Row Level Security on all tables
ALTER TABLE "User" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Simulation" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "BiasDetectionResult" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "FairnessAssessment" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "ExplainabilityAnalysis" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "ComplianceRecord" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "RiskAssessment" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "AuditLog" ENABLE ROW LEVEL SECURITY;

-- Drop all existing policies to ensure idempotency
DO $$
DECLARE
    policy_record RECORD;
    table_name TEXT;
    policy_name TEXT;
BEGIN
    -- Drop all policies on all tables
    FOR policy_record IN 
        SELECT tablename, policyname 
        FROM pg_policies 
        WHERE schemaname = 'public'
    LOOP
        table_name := policy_record.tablename;
        policy_name := policy_record.policyname;
        
        -- Skip system tables
        CONTINUE WHEN table_name LIKE 'pg_%';
        CONTINUE WHEN table_name LIKE 'sql_%';
        
        -- Drop the policy
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', policy_name, table_name);
        RAISE NOTICE 'Dropped policy % on %', policy_name, table_name;
    END LOOP;
END $$;

-- User Table Policies
CREATE POLICY "Users can view their own profile" 
ON "User" FOR SELECT 
USING (id = (auth.uid()::text)::integer);

-- Simulation Table Policies
CREATE POLICY "Users can view their own simulations" 
ON "Simulation" FOR SELECT 
USING ("userId" = (auth.uid()::text)::integer);

CREATE POLICY "Users can insert their own simulations"
ON "Simulation" FOR INSERT
WITH CHECK ("userId" = (auth.uid()::text)::integer);

CREATE POLICY "Users can update their own simulations"
ON "Simulation" FOR UPDATE
USING ("userId" = (auth.uid()::text)::integer);

CREATE POLICY "Users can delete their own simulations"
ON "Simulation" FOR DELETE
USING ("userId" = (auth.uid()::text)::integer);

-- Similar policies for other tables
CREATE POLICY "Users can view their own bias detection results" 
ON "BiasDetectionResult" FOR SELECT 
USING (EXISTS (
  SELECT 1 FROM "Simulation" 
  WHERE "Simulation".id = "BiasDetectionResult"."simulationId"
  AND "Simulation"."userId" = (auth.uid()::text)::integer
));

CREATE POLICY "Users can view their own compliance records" 
ON "ComplianceRecord" FOR SELECT 
USING (EXISTS (
  SELECT 1 FROM "Simulation" 
  WHERE "Simulation".id = "ComplianceRecord"."simulationId"
  AND "Simulation"."userId" = (auth.uid()::text)::integer
));

CREATE POLICY "Users can view their own fairness assessments" 
ON "FairnessAssessment" FOR SELECT 
USING (EXISTS (
  SELECT 1 FROM "Simulation" 
  WHERE "Simulation".id = "FairnessAssessment"."simulationId"
  AND "Simulation"."userId" = (auth.uid()::text)::integer
));

CREATE POLICY "Users can view their own explainability analyses" 
ON "ExplainabilityAnalysis" FOR SELECT 
USING (EXISTS (
  SELECT 1 FROM "Simulation" 
  WHERE "Simulation".id = "ExplainabilityAnalysis"."simulationId"
  AND "Simulation"."userId" = (auth.uid()::text)::integer
));

-- Create a function to get current user's role
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS text AS $$
  SELECT raw_user_meta_data->>'role' 
  FROM auth.users 
  WHERE id::text = auth.uid()::text
$$ LANGUAGE sql SECURITY DEFINER;

-- Allow admins to view all data
-- We'll create individual policies for each table

-- For User table
CREATE POLICY "Admins have full access to users"
ON "User"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

-- For Simulation table
CREATE POLICY "Admins have full access to simulations"
ON "Simulation"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

-- For other tables...
CREATE POLICY "Admins have full access to bias results"
ON "BiasDetectionResult"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

CREATE POLICY "Admins have full access to fairness assessments"
ON "FairnessAssessment"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

CREATE POLICY "Admins have full access to explainability analyses"
ON "ExplainabilityAnalysis"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

CREATE POLICY "Admins have full access to compliance records"
ON "ComplianceRecord"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

CREATE POLICY "Admins have full access to risk assessments"
ON "RiskAssessment"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

CREATE POLICY "Admins have full access to audit logs"
ON "AuditLog"
FOR ALL
TO authenticated
USING (public.get_user_role() = 'ADMIN');

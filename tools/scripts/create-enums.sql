-- Create missing enum types for Prisma schema
-- Run this in Supabase SQL Editor

-- Risk Level enum
CREATE TYPE public."RiskLevel" AS ENUM ('low', 'medium', 'high', 'critical');

-- Alert Severity enum  
CREATE TYPE public."AlertSeverity" AS ENUM ('low', 'medium', 'high', 'critical');

-- Simulation Status enum
CREATE TYPE public."SimulationStatus" AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');

-- User Role enum (if not already exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'UserRole') THEN
        CREATE TYPE public."UserRole" AS ENUM ('user', 'admin', 'auditor', 'developer', 'analyst', 'manager', 'guest');
    END IF;
END $$;

-- Enable pgvector extension for vector operations (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the enums were created
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname IN ('RiskLevel', 'AlertSeverity', 'SimulationStatus', 'UserRole')
ORDER BY typname, enumlabel;

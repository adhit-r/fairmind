-- Check which enum types exist and create missing ones
-- Run this in Supabase SQL Editor

-- Check existing enum types
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname IN ('RiskLevel', 'AlertSeverity', 'SimulationStatus', 'UserRole')
ORDER BY typname, enumlabel;

-- Create RiskLevel enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'RiskLevel') THEN
        CREATE TYPE public."RiskLevel" AS ENUM ('low', 'medium', 'high', 'critical');
        RAISE NOTICE 'Created RiskLevel enum';
    ELSE
        RAISE NOTICE 'RiskLevel enum already exists';
    END IF;
END $$;

-- Create AlertSeverity enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'AlertSeverity') THEN
        CREATE TYPE public."AlertSeverity" AS ENUM ('low', 'medium', 'high', 'critical');
        RAISE NOTICE 'Created AlertSeverity enum';
    ELSE
        RAISE NOTICE 'AlertSeverity enum already exists';
    END IF;
END $$;

-- Create SimulationStatus enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'SimulationStatus') THEN
        CREATE TYPE public."SimulationStatus" AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        RAISE NOTICE 'Created SimulationStatus enum';
    ELSE
        RAISE NOTICE 'SimulationStatus enum already exists';
    END IF;
END $$;

-- Create UserRole enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'UserRole') THEN
        CREATE TYPE public."UserRole" AS ENUM ('user', 'admin', 'auditor', 'developer', 'analyst', 'manager', 'guest');
        RAISE NOTICE 'Created UserRole enum';
    ELSE
        RAISE NOTICE 'UserRole enum already exists';
    END IF;
END $$;

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Show final status
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname IN ('RiskLevel', 'AlertSeverity', 'SimulationStatus', 'UserRole')
ORDER BY typname, enumlabel;

-- Create only the missing RiskLevel enum
-- Run this in Supabase SQL Editor

-- Create RiskLevel enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'RiskLevel') THEN
        CREATE TYPE public."RiskLevel" AS ENUM ('low', 'medium', 'high', 'critical');
        RAISE NOTICE 'Created RiskLevel enum successfully';
    ELSE
        RAISE NOTICE 'RiskLevel enum already exists';
    END IF;
END $$;

-- Verify it was created
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname = 'RiskLevel'
ORDER BY enumlabel;

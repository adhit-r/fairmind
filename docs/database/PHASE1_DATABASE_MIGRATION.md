# Phase 1 Database Migration Plan

## 🎯 **Objective**
Add dataset management and enhanced simulation capabilities to the existing Supabase database.

## 📊 **Current State Analysis**

### ✅ **Existing Tables:**
- `simulation_runs` - Organization-based simulation tracking
- `model_registry` - ML model storage and metadata
- `organizations` & `organization_members` - Multi-tenant structure
- `profiles` - User authentication and profiles

### ❌ **Missing Tables:**
- `datasets` - For storing uploaded CSV/Parquet files
- User-based simulation runs (current ones are org-based)

## 🔧 **Required Changes**

### **1. Add Datasets Table**
```sql
-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create datasets table
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type TEXT NOT NULL, -- 'csv', 'parquet', etc.
    schema_json JSONB, -- Column definitions, types, etc.
    row_count INTEGER,
    column_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_datasets_owner_id ON public.datasets(owner_id);
CREATE INDEX idx_datasets_created_at ON public.datasets(created_at);

-- Enable RLS
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own datasets" ON public.datasets
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert their own datasets" ON public.datasets
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update their own datasets" ON public.datasets
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete their own datasets" ON public.datasets
    FOR DELETE USING (auth.uid() = owner_id);
```

### **2. Extend Simulation Runs Table**
```sql
-- Add new columns to existing simulation_runs table
ALTER TABLE public.simulation_runs 
ADD COLUMN IF NOT EXISTS dataset_id UUID REFERENCES public.datasets(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS config_json JSONB, -- Simulation parameters
ADD COLUMN IF NOT EXISTS results_json JSONB, -- Performance and fairness metrics
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER;

-- Create new indexes for user-based queries
CREATE INDEX IF NOT EXISTS idx_sim_runs_user_id ON public.simulation_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_dataset_id ON public.simulation_runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_status ON public.simulation_runs(status);

-- Update RLS policies to include user-based access
CREATE POLICY IF NOT EXISTS "Users can view their own simulation runs" ON public.simulation_runs
    FOR SELECT USING (
        auth.uid() = user_id OR 
        EXISTS (
            SELECT 1 FROM public.organization_members m
            WHERE m.org_id = simulation_runs.org_id AND m.user_id = auth.uid() AND m.status = 'active'
        )
    );

CREATE POLICY IF NOT EXISTS "Users can insert their own simulation runs" ON public.simulation_runs
    FOR INSERT WITH CHECK (
        auth.uid() = user_id OR 
        EXISTS (
            SELECT 1 FROM public.organization_members m
            WHERE m.org_id = simulation_runs.org_id AND m.user_id = auth.uid() AND m.status = 'active'
        )
    );
```

### **3. Add Updated At Triggers**
```sql
-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER handle_datasets_updated_at
    BEFORE UPDATE ON public.datasets
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_simulation_runs_updated_at
    BEFORE UPDATE ON public.simulation_runs
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
```

## 🚀 **Migration Execution Steps**

### **Step 1: Backup (Recommended)**
```bash
# Export current database schema
pg_dump -h your-supabase-host -U postgres -d postgres --schema-only > backup_schema.sql

# Export data (if needed)
pg_dump -h your-supabase-host -U postgres -d postgres --data-only > backup_data.sql
```

### **Step 2: Execute Migration**
1. **Run datasets table creation** (safe - new table)
2. **Run simulation_runs extension** (safe - adding columns)
3. **Run RLS policy updates** (safe - adding policies)
4. **Run trigger creation** (safe - new functionality)

### **Step 3: Verify Migration**
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('datasets', 'simulation_runs');

-- Check columns added
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'simulation_runs' AND column_name IN ('dataset_id', 'user_id', 'config_json');

-- Check RLS policies
SELECT schemaname, tablename, policyname FROM pg_policies 
WHERE tablename IN ('datasets', 'simulation_runs');
```

## 🔒 **Security Considerations**

### **Row Level Security (RLS)**
- All tables have RLS enabled
- Users can only access their own data
- Organization members can access org data
- No public access to sensitive data

### **Data Validation**
- File type restrictions (CSV, Parquet only)
- File size limits (configurable)
- Schema validation for uploaded datasets
- Input sanitization for all user inputs

## 📊 **Expected Impact**

### **Performance**
- New indexes will improve query performance
- JSONB columns for flexible metadata storage
- Efficient user-based data access patterns

### **Storage**
- Datasets table will store file metadata (not file contents)
- Actual files will be stored in Supabase Storage
- JSONB columns for efficient metadata storage

## ✅ **Rollback Plan**

If issues occur, rollback is straightforward:

```sql
-- Remove new columns from simulation_runs
ALTER TABLE public.simulation_runs 
DROP COLUMN IF EXISTS dataset_id,
DROP COLUMN IF EXISTS user_id,
DROP COLUMN IF EXISTS config_json,
DROP COLUMN IF EXISTS results_json,
DROP COLUMN IF EXISTS status,
DROP COLUMN IF EXISTS started_at,
DROP COLUMN IF EXISTS completed_at,
DROP COLUMN IF EXISTS error_message,
DROP COLUMN IF EXISTS execution_time_ms;

-- Drop datasets table
DROP TABLE IF EXISTS public.datasets CASCADE;

-- Drop new indexes
DROP INDEX IF EXISTS idx_sim_runs_user_id;
DROP INDEX IF EXISTS idx_sim_runs_dataset_id;
DROP INDEX IF EXISTS idx_sim_runs_status;
```

## 🎯 **Next Steps After Migration**

1. **Test database connectivity** with new schema
2. **Implement dataset upload service** in backend
3. **Create dataset management API endpoints**
4. **Build frontend dataset upload interface**
5. **Integrate with existing bias detection system**

## 📞 **Support**

This migration is designed to be safe and non-destructive. All changes use `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` to ensure idempotency.

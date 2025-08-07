# Supabase Integration & ORM

## 🚀 Supabase Integration Overview

Fairmind v2 leverages Supabase as a comprehensive Backend-as-a-Service (BaaS) solution, providing:
- **PostgreSQL Database** with advanced features
- **Authentication & Authorization** with Row Level Security
- **Real-time Subscriptions** for live updates
- **Storage** for file management
- **Edge Functions** for serverless computing

## 📡 Supabase Client Configuration

### Environment Configuration

```typescript
// apps/web/src/lib/supabase/config.ts
export const supabaseConfig = {
  url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  serviceKey: process.env.SUPABASE_SERVICE_ROLE_KEY!, // Server-side only
  
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'pkce' // More secure for SPA applications
  },
  
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
  
  global: {
    headers: {
      'X-Client-Info': 'fairmind-web@2.0.0',
    },
  },
}
```

### Client Initialization

```typescript
// apps/web/src/lib/supabase/client.ts
import { createClientComponentClient, createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import type { Database } from './database.types'

// Client-side Supabase client
export const createSupabaseClient = () => {
  return createClientComponentClient<Database>()
}

// Server-side Supabase client (for Server Components)
export const createSupabaseServerClient = () => {
  const cookieStore = cookies()
  return createServerComponentClient<Database>({ cookies: () => cookieStore })
}

// Service role client (for server-side operations that bypass RLS)
export const createSupabaseServiceClient = () => {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    }
  )
}
```

### Type-Safe Database Types

```typescript
// apps/web/src/lib/supabase/database.types.ts
export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          full_name: string
          metadata: Json
          created_at: string
          updated_at: string
          role: 'admin' | 'user' | 'viewer'
          active: boolean
        }
        Insert: {
          id?: string
          email: string
          full_name: string
          metadata?: Json
          created_at?: string
          updated_at?: string
          role?: 'admin' | 'user' | 'viewer'
          active?: boolean
        }
        Update: {
          id?: string
          email?: string
          full_name?: string
          metadata?: Json
          created_at?: string
          updated_at?: string
          role?: 'admin' | 'user' | 'viewer'
          active?: boolean
        }
      }
      organizations: {
        Row: {
          id: string
          name: string
          slug: string
          description: string | null
          settings: Json
          created_at: string
          updated_at: string
          active: boolean
        }
        Insert: {
          id?: string
          name: string
          slug: string
          description?: string | null
          settings?: Json
          created_at?: string
          updated_at?: string
          active?: boolean
        }
        Update: {
          id?: string
          name?: string
          slug?: string
          description?: string | null
          settings?: Json
          created_at?: string
          updated_at?: string
          active?: boolean
        }
      }
      models: {
        Row: {
          id: string
          organization_id: string
          created_by: string
          name: string
          description: string | null
          model_type: 'classification' | 'regression' | 'clustering' | 'recommendation'
          metadata: Json
          schema: Json
          status: 'draft' | 'active' | 'archived' | 'deprecated'
          created_at: string
          updated_at: string
          version: string
        }
        Insert: {
          id?: string
          organization_id: string
          created_by: string
          name: string
          description?: string | null
          model_type: 'classification' | 'regression' | 'clustering' | 'recommendation'
          metadata?: Json
          schema: Json
          status?: 'draft' | 'active' | 'archived' | 'deprecated'
          created_at?: string
          updated_at?: string
          version?: string
        }
        Update: {
          id?: string
          organization_id?: string
          created_by?: string
          name?: string
          description?: string | null
          model_type?: 'classification' | 'regression' | 'clustering' | 'recommendation'
          metadata?: Json
          schema?: Json
          status?: 'draft' | 'active' | 'archived' | 'deprecated'
          created_at?: string
          updated_at?: string
          version?: string
        }
      }
      bias_analyses: {
        Row: {
          id: string
          model_id: string
          dataset_id: string
          created_by: string
          analysis_type: 'demographic_parity' | 'equalized_odds' | 'individual_fairness' | 'comprehensive'
          parameters: Json
          metrics: Json
          compliance_score: number | null
          recommendations: Json
          status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
          started_at: string | null
          completed_at: string | null
          created_at: string
          metadata: Json
        }
        Insert: {
          id?: string
          model_id: string
          dataset_id: string
          created_by: string
          analysis_type: 'demographic_parity' | 'equalized_odds' | 'individual_fairness' | 'comprehensive'
          parameters?: Json
          metrics?: Json
          compliance_score?: number | null
          recommendations?: Json
          status?: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
          started_at?: string | null
          completed_at?: string | null
          created_at?: string
          metadata?: Json
        }
        Update: {
          id?: string
          model_id?: string
          dataset_id?: string
          created_by?: string
          analysis_type?: 'demographic_parity' | 'equalized_odds' | 'individual_fairness' | 'comprehensive'
          parameters?: Json
          metrics?: Json
          compliance_score?: number | null
          recommendations?: Json
          status?: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
          started_at?: string | null
          completed_at?: string | null
          created_at?: string
          metadata?: Json
        }
      }
    }
    Views: {
      model_performance_summary: {
        Row: {
          id: string
          name: string
          organization_id: string
          total_analyses: number
          avg_compliance_score: number
          best_compliance_score: number
          worst_compliance_score: number
          completed_analyses: number
          failed_analyses: number
          last_analysis_date: string
        }
      }
      organization_dashboard: {
        Row: {
          organization_id: string
          organization_name: string
          total_models: number
          total_analyses: number
          avg_compliance_score: number
          critical_alerts: number
          high_alerts: number
          total_members: number
        }
      }
    }
    Functions: {
      calculate_compliance_score: {
        Args: {
          bias_metrics: Json
          thresholds?: Json
        }
        Returns: number
      }
    }
  }
}
```

## 🏗️ Database Access Layer (DAL)

### Base Repository Pattern

```typescript
// apps/web/src/lib/dal/base-repository.ts
import { createSupabaseClient } from '@/lib/supabase/client'
import type { Database } from '@/lib/supabase/database.types'

export abstract class BaseRepository<T extends keyof Database['public']['Tables']> {
  protected supabase = createSupabaseClient()
  protected tableName: T

  constructor(tableName: T) {
    this.tableName = tableName
  }

  async findById(id: string) {
    const { data, error } = await this.supabase
      .from(this.tableName)
      .select('*')
      .eq('id', id)
      .single()

    if (error) throw new Error(`Failed to find ${this.tableName}: ${error.message}`)
    return data
  }

  async findMany(filters?: Record<string, any>, limit?: number) {
    let query = this.supabase.from(this.tableName).select('*')

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        query = query.eq(key, value)
      })
    }

    if (limit) {
      query = query.limit(limit)
    }

    const { data, error } = await query
    if (error) throw new Error(`Failed to find ${this.tableName}: ${error.message}`)
    return data
  }

  async create(data: Database['public']['Tables'][T]['Insert']) {
    const { data: created, error } = await this.supabase
      .from(this.tableName)
      .insert(data)
      .select()
      .single()

    if (error) throw new Error(`Failed to create ${this.tableName}: ${error.message}`)
    return created
  }

  async update(id: string, data: Database['public']['Tables'][T]['Update']) {
    const { data: updated, error } = await this.supabase
      .from(this.tableName)
      .update({ ...data, updated_at: new Date().toISOString() })
      .eq('id', id)
      .select()
      .single()

    if (error) throw new Error(`Failed to update ${this.tableName}: ${error.message}`)
    return updated
  }

  async delete(id: string) {
    const { error } = await this.supabase
      .from(this.tableName)
      .delete()
      .eq('id', id)

    if (error) throw new Error(`Failed to delete ${this.tableName}: ${error.message}`)
    return true
  }

  // Real-time subscription helper
  subscribe(callback: (payload: any) => void, filters?: Record<string, any>) {
    let channel = this.supabase
      .channel(`${this.tableName}-changes`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: this.tableName,
        ...filters
      }, callback)

    return channel.subscribe()
  }
}
```

### Model Repository

```typescript
// apps/web/src/lib/dal/models-repository.ts
import { BaseRepository } from './base-repository'
import type { Database } from '@/lib/supabase/database.types'

type Model = Database['public']['Tables']['models']['Row']
type ModelInsert = Database['public']['Tables']['models']['Insert']
type ModelUpdate = Database['public']['Tables']['models']['Update']

export class ModelsRepository extends BaseRepository<'models'> {
  constructor() {
    super('models')
  }

  async findByOrganization(organizationId: string, status?: string) {
    let query = this.supabase
      .from('models')
      .select(`
        *,
        created_by_user:users!models_created_by_fkey(full_name, email),
        latest_analysis:bias_analyses(
          id,
          compliance_score,
          status,
          created_at
        )
      `)
      .eq('organization_id', organizationId)
      .order('created_at', { ascending: false })

    if (status) {
      query = query.eq('status', status)
    }

    const { data, error } = await query
    if (error) throw new Error(`Failed to find models: ${error.message}`)
    return data
  }

  async findWithAnalyses(modelId: string) {
    const { data, error } = await this.supabase
      .from('models')
      .select(`
        *,
        bias_analyses(
          id,
          analysis_type,
          compliance_score,
          status,
          created_at,
          metrics,
          recommendations
        ),
        model_explanations(
          id,
          explanation_type,
          created_at
        )
      `)
      .eq('id', modelId)
      .single()

    if (error) throw new Error(`Failed to find model with analyses: ${error.message}`)
    return data
  }

  async updateStatus(modelId: string, status: Model['status']) {
    return this.update(modelId, { status })
  }

  async getPerformanceSummary(organizationId: string) {
    const { data, error } = await this.supabase
      .from('model_performance_summary')
      .select('*')
      .eq('organization_id', organizationId)
      .order('avg_compliance_score', { ascending: false })

    if (error) throw new Error(`Failed to get performance summary: ${error.message}`)
    return data
  }
}
```

### Bias Analyses Repository

```typescript
// apps/web/src/lib/dal/bias-analyses-repository.ts
import { BaseRepository } from './base-repository'
import type { Database } from '@/lib/supabase/database.types'

type BiasAnalysis = Database['public']['Tables']['bias_analyses']['Row']
type BiasAnalysisInsert = Database['public']['Tables']['bias_analyses']['Insert']

export class BiasAnalysesRepository extends BaseRepository<'bias_analyses'> {
  constructor() {
    super('bias_analyses')
  }

  async findByModel(modelId: string, limit = 50) {
    const { data, error } = await this.supabase
      .from('bias_analyses')
      .select(`
        *,
        model:models(name, model_type),
        dataset:datasets(name),
        created_by_user:users!bias_analyses_created_by_fkey(full_name)
      `)
      .eq('model_id', modelId)
      .order('created_at', { ascending: false })
      .limit(limit)

    if (error) throw new Error(`Failed to find analyses: ${error.message}`)
    return data
  }

  async findByStatus(status: BiasAnalysis['status'], organizationId?: string) {
    let query = this.supabase
      .from('bias_analyses')
      .select(`
        *,
        model:models!inner(
          name,
          organization_id
        )
      `)
      .eq('status', status)

    if (organizationId) {
      query = query.eq('model.organization_id', organizationId)
    }

    const { data, error } = await query
    if (error) throw new Error(`Failed to find analyses by status: ${error.message}`)
    return data
  }

  async createAnalysis(analysisData: BiasAnalysisInsert) {
    const analysis = await this.create(analysisData)
    
    // Trigger real-time notification
    await this.supabase
      .from('bias_analyses')
      .update({ status: 'queued' })
      .eq('id', analysis.id)

    return analysis
  }

  async updateAnalysisResults(
    analysisId: string, 
    metrics: any, 
    complianceScore: number, 
    recommendations: any[]
  ) {
    const { data, error } = await this.supabase
      .from('bias_analyses')
      .update({
        metrics,
        compliance_score: complianceScore,
        recommendations,
        status: 'completed',
        completed_at: new Date().toISOString()
      })
      .eq('id', analysisId)
      .select()
      .single()

    if (error) throw new Error(`Failed to update analysis results: ${error.message}`)
    return data
  }

  async getComplianceStats(organizationId: string, timeRange = '30 days') {
    const { data, error } = await this.supabase.rpc('get_compliance_stats', {
      org_id: organizationId,
      time_range: timeRange
    })

    if (error) throw new Error(`Failed to get compliance stats: ${error.message}`)
    return data
  }
}
```

## 🔐 Authentication Integration

### Auth Context Provider

```typescript
// apps/web/src/lib/auth/auth-provider.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { createSupabaseClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, metadata?: any) => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createSupabaseClient()

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)

        if (event === 'SIGNED_IN') {
          router.push('/dashboard')
        } else if (event === 'SIGNED_OUT') {
          router.push('/auth/login')
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [supabase.auth, router])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    })

    if (error) throw error
  }

  const signUp = async (email: string, password: string, metadata?: any) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata
      }
    })

    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`
    })

    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{
      user,
      session,
      loading,
      signIn,
      signUp,
      signOut,
      resetPassword
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### Protected Route Component

```typescript
// apps/web/src/lib/auth/protected-route.tsx
'use client'

import { useAuth } from './auth-provider'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: 'admin' | 'user' | 'viewer'
  redirectTo?: string
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  redirectTo = '/auth/login' 
}: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push(redirectTo)
        return
      }

      if (requiredRole && user.user_metadata?.role !== requiredRole) {
        router.push('/unauthorized')
        return
      }
    }
  }, [user, loading, requiredRole, router, redirectTo])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  if (requiredRole && user.user_metadata?.role !== requiredRole) {
    return null
  }

  return <>{children}</>
}
```

## 📡 Real-time Subscriptions

### Real-time Hooks

```typescript
// apps/web/src/lib/hooks/use-realtime-subscription.ts
import { useEffect, useRef } from 'react'
import { createSupabaseClient } from '@/lib/supabase/client'
import type { RealtimeChannel } from '@supabase/supabase-js'

interface UseRealtimeSubscriptionOptions {
  table: string
  filter?: string
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*'
  onInsert?: (payload: any) => void
  onUpdate?: (payload: any) => void
  onDelete?: (payload: any) => void
  onChange?: (payload: any) => void
}

export function useRealtimeSubscription({
  table,
  filter,
  event = '*',
  onInsert,
  onUpdate,
  onDelete,
  onChange
}: UseRealtimeSubscriptionOptions) {
  const supabase = createSupabaseClient()
  const channelRef = useRef<RealtimeChannel | null>(null)

  useEffect(() => {
    const channel = supabase
      .channel(`${table}-changes`)
      .on('postgres_changes', {
        event,
        schema: 'public',
        table,
        filter
      }, (payload) => {
        const { eventType, new: newRecord, old: oldRecord } = payload

        switch (eventType) {
          case 'INSERT':
            onInsert?.(newRecord)
            break
          case 'UPDATE':
            onUpdate?.({ new: newRecord, old: oldRecord })
            break
          case 'DELETE':
            onDelete?.(oldRecord)
            break
        }

        onChange?.(payload)
      })
      .subscribe()

    channelRef.current = channel

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current)
      }
    }
  }, [table, filter, event, onInsert, onUpdate, onDelete, onChange, supabase])

  return channelRef.current
}

// Specific hook for analysis updates
export function useAnalysisUpdates(modelId: string, onUpdate: (analysis: any) => void) {
  return useRealtimeSubscription({
    table: 'bias_analyses',
    filter: `model_id=eq.${modelId}`,
    onUpdate: ({ new: newAnalysis }) => {
      onUpdate(newAnalysis)
    }
  })
}
```

## 🔧 Database Migrations

### Migration Management

```sql
-- Migration: 001_initial_schema.sql
-- Create core tables and relationships

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security
ALTER DATABASE postgres SET row_security = on;

-- Create users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    active BOOLEAN DEFAULT true
);

-- Create organizations table
CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Create organization_members table
CREATE TABLE public.organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true,
    UNIQUE(user_id, organization_id)
);

-- Create remaining tables...
-- (models, datasets, bias_analyses, etc.)

COMMIT;
```

### Migration Runner

```typescript
// apps/web/src/lib/migrations/migration-runner.ts
import { createSupabaseServiceClient } from '@/lib/supabase/client'
import fs from 'fs'
import path from 'path'

interface Migration {
  id: string
  name: string
  sql: string
  checksum: string
}

export class MigrationRunner {
  private supabase = createSupabaseServiceClient()
  private migrationsPath = path.join(process.cwd(), 'migrations')

  async runMigrations() {
    // Ensure migrations table exists
    await this.createMigrationsTable()

    // Get pending migrations
    const pendingMigrations = await this.getPendingMigrations()

    // Run each migration
    for (const migration of pendingMigrations) {
      await this.runMigration(migration)
    }
  }

  private async createMigrationsTable() {
    await this.supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS _migrations (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          checksum TEXT NOT NULL,
          executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
      `
    })
  }

  private async getPendingMigrations(): Promise<Migration[]> {
    const files = fs.readdirSync(this.migrationsPath)
      .filter(file => file.endsWith('.sql'))
      .sort()

    const { data: executedMigrations } = await this.supabase
      .from('_migrations')
      .select('id')

    const executedIds = new Set(executedMigrations?.map(m => m.id) || [])

    return files
      .filter(file => !executedIds.has(file))
      .map(file => {
        const sql = fs.readFileSync(
          path.join(this.migrationsPath, file), 
          'utf-8'
        )
        return {
          id: file,
          name: file.replace(/^\d+_/, '').replace(/\.sql$/, ''),
          sql,
          checksum: this.calculateChecksum(sql)
        }
      })
  }

  private async runMigration(migration: Migration) {
    try {
      // Execute migration SQL
      await this.supabase.rpc('exec_sql', { sql: migration.sql })

      // Record migration as executed
      await this.supabase
        .from('_migrations')
        .insert({
          id: migration.id,
          name: migration.name,
          checksum: migration.checksum
        })

      console.log(`Migration ${migration.id} executed successfully`)
    } catch (error) {
      console.error(`Failed to execute migration ${migration.id}:`, error)
      throw error
    }
  }

  private calculateChecksum(content: string): string {
    return require('crypto')
      .createHash('md5')
      .update(content)
      .digest('hex')
  }
}
```

This comprehensive integration provides a robust foundation for working with Supabase in the Fairmind v2 platform, ensuring type safety, security, and optimal performance.

# Supabase BaaS Migration Plan

## Overview
This document outlines the plan to migrate from a NestJS backend to Supabase Backend-as-a-Service (BaaS) for the Fairmind Ethical Sandbox project.

## Current Architecture
- Frontend: Next.js with React Aria
- Backend: NestJS API with Prisma
- Auth: Supabase Auth (partially implemented)
- Database: PostgreSQL (via Supabase)

## Target Architecture
- Frontend: Next.js with React Aria
- Backend: Supabase BaaS for:
  - Authentication
  - Database (PostgreSQL with Row Level Security)
  - Storage
  - Edge Functions (for custom backend logic)
  - Realtime subscriptions
- Legacy NestJS API (phased out gradually)

## Migration Phases

### Phase 1: Authentication Migration (Week 1-2)
- [ ] Document current auth flow and requirements
- [ ] Map current user roles/permissions to Supabase RLS policies
- [ ] Migrate user data to Supabase Auth
- [ ] Update frontend to use Supabase Auth exclusively
- [ ] Remove legacy auth code from NestJS
- [ ] Test all auth flows (signup, login, password reset, etc.)

### Phase 2: Database Migration (Week 3-4)
- [ ] Document current database schema
- [ ] Design Supabase database schema with RLS policies
- [ ] Create migration scripts for existing data
- [ ] Set up database backups
- [ ] Test data migration
- [ ] Update frontend to use Supabase client directly

### Phase 3: API Migration (Week 5-6)
- [ ] Identify custom API endpoints in NestJS
- [ ] Convert endpoints to Supabase Edge Functions where needed
- [ ] Update frontend to use Supabase client and Edge Functions
- [ ] Test all API endpoints
- [ ] Monitor performance and optimize

### Phase 4: Realtime Features (Week 7-8)
- [ ] Identify features that would benefit from realtime updates
- [ ] Implement realtime subscriptions in the frontend
- [ ] Test realtime functionality
- [ ] Optimize subscription performance

### Phase 5: Cleanup and Optimization (Week 9-10)
- [ ] Remove unused NestJS code
- [ ] Optimize database queries and indexes
- [ ] Implement monitoring and logging
- [ ] Document new architecture
- [ ] Create runbook for operations

## Benefits
- Reduced backend maintenance
- Built-in scalability
- Faster development cycles
- Built-in authentication and authorization
- Realtime capabilities out of the box
- Managed infrastructure

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | High | Thorough testing, backup strategy, phased rollout |
| Downtime during migration | Medium | Plan maintenance window, implement feature flags |
| Performance issues | Medium | Load testing, monitoring, optimization |
| Vendor lock-in | Low | Abstract Supabase client usage, use standard SQL |

## Next Steps
1. Review and finalize this plan
2. Begin Phase 1 implementation
3. Update documentation after each phase
4. Monitor and adjust plan as needed

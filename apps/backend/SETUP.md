# Backend Environment Setup

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp apps/backend/config/env.example apps/backend/.env
   ```

2. **Get your Supabase Connection String:**
   - Go to [Supabase Dashboard](https://supabase.com/dashboard)
   - Select project: **Fairmind** (`swapkvhzyhcruoyjpkyr`)
   - Navigate to **Project Settings** > **Database**
   - Copy the **URI** connection string from the "Connection String" section
   - Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true`

3. **Update `apps/backend/.env`:**
   ```bash
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
   ```
   Replace `[ref]`, `[password]`, and `[region]` with your actual values.

4. **Generate a secure SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```
   Add this to your `.env` file as `SECRET_KEY=...`

5. **Start the backend:**
   ```bash
   cd apps/backend
   python main.py
   ```

## Current Database Status

- ✅ **ml_models**: 7 active models
- ✅ **audit_logs**: 5+ activity logs
- ✅ **datasets**: Table created, ready for uploads
- ✅ **geographic_bias_analyses**: 6 active scans

All tables are properly connected and ready to use!


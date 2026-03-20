# Backend Environment Setup (Neon-first)

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp apps/backend/config/env.example apps/backend/.env
   ```

2. **Set your database connection string (Neon):**
   ```bash
   DATABASE_URL=postgresql://<user>:<password>@<neon-host>/<db>?sslmode=require
   ```

3. **Generate a secure `SECRET_KEY`:**
   ```bash
   openssl rand -hex 32
   ```
   Add this to your `.env` as `SECRET_KEY=...`.

4. **Start the backend:**
   ```bash
   cd apps/backend
   python main.py
   ```

## Notes

- FairMind now uses Neon/PostgreSQL as the primary database target.
- Local SQLite is still supported for quick development runs.
- Dataset and model file artifacts are stored locally unless a separate object storage adapter is configured.

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
   uv run python -m uvicorn api.main:app --reload --port 8000
   ```

## Notes

- FairMind now uses Neon/PostgreSQL as the primary database target.
- PostgreSQL is required (local, Docker, or a Neon branch), plus the `psql` client for a first install. Create the schema with `uv run python scripts/setup_db.py`; check it with `uv run python scripts/setup_db.py verify`.
- Framework, pack, workflow and evaluation reference data (51 frameworks incl. ISO 42001, NIST AI RMF, EU AI Act, RBI FREE-AI) ships in `src/api/routers/pack_catalogue_data/` and needs no seeding. To change it, edit `docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx` and run `uv run --with openpyxl python scripts/export_pack_catalogue.py ../../docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx src/api/routers/pack_catalogue_data/catalogue.json` (it also rewrites `workbook.json`, every sheet verbatim, and merges `additions.json`).
- Tests need `FAIRMIND_TEST_POSTGRES_URL` pointing at a disposable server they may create databases on (never Neon).
- Dataset and model file artifacts are stored locally unless a separate object storage adapter is configured.

# Database Seeding Guide

## Overview

FairMind uses **factual data only** - no mock or generated data. All seed scripts populate the database with real models, datasets, and audit logs based on actual research and public sources.

## Main Seed Script

**Location:** `apps/backend/scripts/seed_database.py`

**Usage:**
```bash
cd apps/backend
python scripts/seed_database.py
```

**What it seeds:**
- **ML Models**: Real models like GPT-4, BERT, ResNet-50, COMPAS with factual metadata
- **Datasets**: Real datasets from UCI ML Repository, ProPublica (Adult Income, COMPAS, German Credit)
- **Audit Logs**: Realistic audit trail entries based on actual system events

**Data Sources:**
- All models are based on real research papers and official documentation
- All datasets are from public repositories (UCI, ProPublica, Kaggle)
- All metadata includes real citations, release dates, and known limitations

## Legacy Seed Scripts

The following scripts are deprecated in favor of `seed_database.py`:
- `seed_models.py` - Use `seed_database.py` instead
- `seed_models_simple.py` - Use `seed_database.py` instead
- `seed_models_realistic.py` - Use `seed_database.py` instead
- `seed_models_api.py` - Use `seed_database.py` instead

## Requirements

1. **Database Connection**: Set `DATABASE_URL` in `apps/backend/.env`
2. **Python Dependencies**: Install requirements: `pip install -r requirements.txt`
3. **Database Tables**: Ensure all migrations have been run

## Verification

After seeding, verify data:
```bash
# Check models
python -c "from database.connection import db_manager; from sqlalchemy import text; session = db_manager.get_session().__enter__(); print(session.execute(text('SELECT COUNT(*) FROM ml_models')).scalar())"

# Check datasets
python -c "from database.connection import db_manager; from sqlalchemy import text; session = db_manager.get_session().__enter__(); print(session.execute(text('SELECT COUNT(*) FROM datasets')).scalar())"

# Check audit logs
python -c "from database.connection import db_manager; from sqlalchemy import text; session = db_manager.get_session().__enter__(); print(session.execute(text('SELECT COUNT(*) FROM audit_logs')).scalar())"
```

## API Changes

**All API endpoints now return real data only:**
- `/api/v1/core/models` - Returns models from database (no mock fallback)
- `/api/v1/core/datasets` - Returns datasets from database (no mock fallback)
- `/api/v1/core/activity/recent` - Returns audit logs from database (no mock fallback)
- `/api/v1/bias-detection-v2/*` - Requires real dataset_id (no sample data generation)
- `/api/v1/modern-bias-detection/*` - Returns data from bias_test_results table

**Error Handling:**
- If database is empty, endpoints return empty arrays `[]` or proper HTTP errors
- No mock data fallbacks - seed the database first!


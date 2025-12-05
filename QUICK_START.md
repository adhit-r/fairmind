# Quick Start Guide

## Start Backend Server

```bash
cd apps/backend
# Create developer account (dev@fairmind.ai / dev)
uv run python scripts/create_dev_user.py
uv run uvicorn api.main:app --reload --port 8000
```

The backend will be available at: **http://localhost:8000**

## Start Frontend Server

In a **new terminal**:

```bash
cd apps/frontend-new
bun run dev
```

The frontend will be available at: **http://localhost:1111**

## Verify Setup

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check Database Models**:
   ```bash
   cd apps/backend
   python3 -c "import sqlite3; conn = sqlite3.connect('fairmind.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM models'); print(f'Models: {cursor.fetchone()[0]}')"
   ```

3. **Frontend**:
   - Open http://localhost:1111
   - Should see dashboard with real data

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Kill existing process: `kill -9 $(lsof -t -i:8000)`
- Check Python/uv is installed: `uv --version`

### Frontend won't start
- Check if port 1111 is already in use: `lsof -i :1111`
- Kill existing process: `kill -9 $(lsof -t -i:1111)`
- Check bun is installed: `bun --version`

### No models showing
- Seed database: `cd apps/backend && python3 scripts/seed_models_realistic.py`

### API errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`

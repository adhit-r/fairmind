Phases and milestones
Phase 0 — Stabilize foundations (1–2 days)
Frontend: Ensure NEXT_PUBLIC_API_URL and Supabase auth keys set; remove any leftover hardcoded demo data from pages/components.
Backend: Confirm upload/simulation endpoints; add basic logging, error-handling, and 2xx/4xx/5xx response shapes consistently.
DB: Run seed; ensure profiles and RLS working; add tables to persist simulations and artifacts.
Phase 1 — Real simulation data path (Option 1: dataset ingestion) (3–5 days)
Backend:
Add POST /datasets/upload (CSV/Parquet), validate columns; store in datasets/ and persist a datasets table: id, path, schema_json, created_by, created_at.
Add POST /simulation/run to accept {model_path, dataset_id|dataset_path, target, features, protected_attributes}; for sklearn pickles run predict/predict_proba; compute performance metrics (accuracy, precision, recall, F1, AUC).
Add fairness metrics (demographic parity, disparate impact, equal opportunity, equalized odds) and subgroup metrics across protected attributes.
Persist simulation runs to simulation_runs table: id, model_path, dataset_id, config_json, metrics_json, status, created_by, created_at.
Frontend:
Extend ModelUpload with dataset upload form (file input + form for target, features, protected_attributes).
Add “Run simulation” modal to select dataset + parameters.
Surfacing results: show metric cards + downloads; show subgroup breakdown table.
Visualizations:
Tie fairness-chart, risk-heatmap, performance-matrix to live simulation results.
Acceptance: Upload model + dataset → run simulation → view real metrics/visualizations → persisted in DB.
Phase 2 — Real simulation data path (Option 2: synthetic data) (2–4 days)
Backend:
Add POST /datasets/synthetic to generate tabular data given a schema template and distributions (e.g., normal, categorical priors) and protected attributes; persist like real datasets.
Frontend:
“Generate synthetic dataset” wizard: choose features, types, sizes, correlations, protected attribute distributions.
Visualizations: same as Phase 1; mark data source as “synthetic”.
Acceptance: Generate synthetic dataset → run simulation → results/visuals.
Phase 3 — Explainability and robustness (3–5 days)
Backend:
Explainability: enrich /simulation/run with SHAP for top features; return local and global importances (only if feasible for model type).
Robustness: simple perturbation tests (noise, feature dropout) to estimate robustness metrics.
Frontend: Add SHAP summary chart + local explanations; add robustness score panel.
Visuals: wire explainability-treemap, robustness-chart.
Phase 4 — Monitoring and drift (3–5 days)
Backend:
Add /monitor/drift/run to compute PSI/KS on sliding windows; persist drift_runs.
WebSocket/SSE for long-running jobs status (or polling).
Frontend: Add monitoring dashboard with trend lines; alerts.
Visuals: extend model-drift-chart, time-series-chart.
Phase 5 — Storage, metadata, and governance (2–4 days)
Supabase Storage: store artifacts (models/datasets) with signed URLs; move files out of local uploads/.
Persist metadata for lineage, runs, and artifacts; link to users via profiles.
RBAC and RLS on run results (owner can read/write; org read; public read if flagged).
Detailed task breakdown (developer checklist)
Backend (FastAPI)
Datasets:
POST /datasets/upload (multipart form); detect CSV/Parquet; sniff schema; persist datasets (id, owner_id, path, schema_json, created_at).
Optional: GET /datasets (paginated) and GET /datasets/{id} for browsing.
Simulations:
POST /simulation/run: load model (joblib/pickle); load dataset (pandas); validate target, features; run predict; compute metrics:
performance: accuracy, precision, recall, F1, AUC
fairness: demographic parity, disparate impact, equalized odds, equal opportunity; subgroup metrics
Persist simulation_runs (id, owner_id, model_path, dataset_id, config_json, metrics_json, status, created_at).
Synthetic data:
POST /datasets/synthetic: accept schema and distributions; generate with numpy/pandas; persist and return dataset_id.
Explainability:
Add optional SHAP if sklearn-compatible and dataset small enough; return feature importances (global + per-sample top-N).
Robustness:
Perturbation tests: feature noise/dropout; recompute accuracy/fairness deltas.
Monitoring:
Drift metrics (PSI/KS) across runs/time windows; endpoints to query by model/dataset/time range.
Infra:
Move file storage to Supabase Storage (signed uploads/downloads).
Background jobs (optional): RQ/Celery for long jobs; polling/WebSocket for status updates.
Database (Supabase SQL)
Tables:
datasets (id uuid, owner uuid, path text, schema_json jsonb, created_at timestamptz)
simulation_runs (id uuid, owner uuid, model_path text, dataset_id uuid, config_json jsonb, metrics_json jsonb, status text, created_at timestamptz)
RLS policies:
dataset owner read/write; org read if needed; public read only if flagged.
runs owner read/write; org read; public read if flagged.
Indexes: by owner, created_at; runs by dataset_id.
Frontend (Next.js)
Dataset UI:
New page/section to upload datasets, set target, pick features, select protected_attributes.
Validations: ensure target ∈ columns; protected attributes exist.
Simulation UI:
From ModelUpload, allow selecting dataset + params; show job status; display metrics and subgroup tables.
Export: CSV/JSON download for metrics and charts.
Visualizations (replace hardcoded):
fairness-chart → fairness metrics from last run
risk-heatmap → subgroup fairness metrics
performance-matrix → performance metrics
explainability-treemap → SHAP global importances
model-drift-chart → drift metrics time series
State/UX:
Toasts/spinners; error boundaries; pagination for datasets and runs.
Security and compliance
Never send service-role key to frontend; service operations via backend only.
Validate file types and size limits; sanitize filenames; scan CSV headers.
Add rate limits on upload/run endpoints.
QA and acceptance
E2E flow:
Upload model + dataset → run → metrics visible → visualizations render → entries persisted → re-open run details.
Unit tests:
Metrics calculations, schema validation, fairness functions.
Load tests (basic): ensure large CSVs chunked/streamed; timeouts guarded.
API contracts (concise)
POST /datasets/upload (multipart)
form: file, name?, description?
returns: { success, dataset_id, path, schema: { columns: [{name,type}], rows: n } }
POST /datasets/synthetic
body: { rows, columns: [{ name, type, distribution, params }], protected_attributes: [...] }
returns: { success, dataset_id, path, schema }
POST /simulation/run
body: { model_path, dataset_id|dataset_path, target, features, protected_attributes }
returns: { success, run_id, metrics: { performance: {...}, fairness: {..., subgroups: [...] }, explainability?, robustness? }, artifacts? }
Priorities to start with (actionable)
Implement /datasets/upload + datasets table and RLS.
Extend /simulation/run to accept dataset + params and compute real metrics (sklearn path).
Wire UI: dataset upload form; run simulation modal; results in charts.
Replace dashboard hardcodings with backend data.
Optional next: synthetic data generator; SHAP; robustness; drift; Supabase Storage.
Acceptance criteria
No hardcoded metrics remain on key pages.
Simulation results are computed from real data and persist in DB.
Visualizations reflect real results with clear legends and tooltips.
Timeline (rough)
Week 1: Phase 1 core + visuals wired.
Week 2: Explainability/robustness + polish; begin drift.
Week 3: Monitoring/drift + storage move + background jobs.
Definition of done
Upload model and dataset; run; view/export real metrics; revisit runs from history; charts reflect runs; RLS-secured; no demo keys or hardcoded data.
If you want, I’ll start by adding /datasets/upload + DB tables and wiring the UI form.
go ahead with implementation

Implemented real simulation flow:
New endpoint: POST /datasets/upload (CSV/Parquet). Returns path + inferred schema.
Extended POST /simulation/run to accept dataset_path, target, features, protected_attributes. Loads sklearn .pkl/.joblib, runs predict, computes performance (accuracy, precision_macro, recall_macro, f1_macro) and simple fairness (demographic parity difference per protected attribute). Falls back to mock metrics if dataset not provided.
Verified locally: dataset upload 200; simulation with a dummy sklearn model and sample CSV returns real metrics.
How to run now:
Backend: PORT=8001 python backend/main.py
Upload dataset:
curl -s -F "file=@/absolute/path/to/data.csv" http://127.0.0.1:8001/datasets/upload
Note the returned "path".
Upload model (frontend or curl). Use returned model path from upload, or a local pickle path.
Run simulation:
POST http://127.0.0.1:8001/simulation/run
Body example:
{
"path": "/abs/path/to/model.pkl",
"dataset_path": "/abs/path/to/data.csv",
"target": "label",
"features": ["age", "income"],
"protected_attributes": ["gender"]
}
Frontend reminder:
Ensure frontend/.env.local has NEXT_PUBLIC_API_URL=http://localhost:8001
The Model Upload UI already handles model upload and can show simulation results; we can add a dataset upload form next.
i have set NEXT_PUBLIC_API_URL=http://localhost:8000

Set it to the backend port you’re actually running.
If backend runs on 8001 (current setup):
In frontend/.env.local set: NEXT_PUBLIC_API_URL=http://localhost:8001
Restart frontend
If you want to keep 8000:
Start backend as: PORT=8000 python backend/main.py
Then NEXT_PUBLIC_API_URL=http://localhost:8000 is fine
Quick check:
Open http://localhost:8001/health (or 8000 if you switch). Should return status healthy.
Summary
Your current value points to 8000, but backend is on 8001. Update the env or backend port so they match.
changed to 8001 whihc port is front end at

Frontend runs on http://localhost:3000
Backend runs on http://localhost:8001
Make sure in frontend/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:8001
Restart frontend after changing env, then use http://localhost:3000.



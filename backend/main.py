"""
Fairmind ML Service - AI Governance and Bias Detection

This service provides ML capabilities specifically for:
- Bias detection and fairness analysis
- Model explainability (SHAP, LIME)
- Compliance scoring and reporting
- Real-time monitoring and alerts
"""

from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import random
import json
import os
import uuid
from websocket import websocket_endpoint, start_periodic_updates
import asyncio
from email_service import email_service
from supabase_client import supabase_service
from models.ai_dna_profiling import (
    ModelDNAProfile, BiasInheritancePattern, ModelLineageNode, ModelEvolution,
    generate_dna_signature, analyze_bias_inheritance, create_model_lineage_tree, analyze_model_evolution
)
from models.ai_genetic_engineering import (
    ModelModification, GeneticEngineeringSession, BiasRemovalTool, FairnessEnhancement,
    analyze_model_for_modification, apply_model_modification, create_genetic_engineering_session,
    validate_modification_safety, create_bias_removal_tools, create_fairness_enhancements
)
from models.ai_time_travel import (
    HistoricalScenario, ModelBehaviorAnalysis, BiasEvolution, PerformanceComparison,
    create_historical_scenarios, analyze_model_in_historical_scenario, analyze_bias_evolution_timeline,
    analyze_performance_timeline, create_time_travel_dashboard_data
)
from models.ai_circus import (
    TestScenario, StressTest, EdgeCase, AdversarialChallenge,
    create_test_scenarios, create_stress_tests, create_edge_cases, create_adversarial_challenges,
    run_comprehensive_test, create_circus_dashboard_data
)
from models.ai_ethics_observatory import (
    EthicsFramework, EthicsViolation, EthicsScore,
    create_ethics_frameworks, assess_model_ethics, create_observatory_dashboard_data
)

# Catalog manager for public datasets and models
from catalog_manager import CatalogManager
catalog_manager = CatalogManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fairmind ML Service",
    description="AI Governance and Bias Detection ML Service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR = Path(os.getenv("DATASET_DIR", "datasets"))
DATASET_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = Path(os.getenv("MODEL_REGISTRY", "models_registry.json"))
RESULTS_FILE = Path(os.getenv("SIM_RESULTS", "simulation_results.json"))

# Data Models
class ModelPrediction(BaseModel):
    prediction: float
    confidence: float
    features: Dict[str, Any]
    protected_attributes: Dict[str, Any]  # age, gender, race, etc.
    timestamp: datetime

class BiasAnalysisRequest(BaseModel):
    model_path: str
    dataset_path: str
    target: str
    features: List[str]
    protected_attributes: List[str]

class FairnessMetrics(BaseModel):
    demographic_parity: float
    equalized_odds: float
    equal_opportunity: float
    disparate_impact: float
    statistical_parity_difference: float

class BiasAnalysisResponse(BaseModel):
    model_id: str
    fairness_metrics: FairnessMetrics
    bias_detected: bool
    risk_level: str  # LOW, MEDIUM, HIGH
    recommendations: List[str]
    affected_groups: List[str]

# Email Models
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    from_email: Optional[str] = None

class NotificationRequest(BaseModel):
    to: str
    type: str
    message: str
    additional_data: Optional[Dict[str, Any]] = None

class AlertRequest(BaseModel):
    to: str
    alert_type: str
    severity: str
    description: str
    timestamp: str

# Geographic Bias Models
class GeographicBiasRequest(BaseModel):
    model_id: str
    source_country: str
    target_country: str
    model_performance_data: Dict[str, Any]  # Performance metrics by country
    demographic_data: Dict[str, Any]  # Population demographics
    cultural_factors: Dict[str, Any]  # Cultural, linguistic, economic factors

class GeographicBiasResponse(BaseModel):
    model_id: str
    source_country: str
    target_country: str
    bias_detected: bool
    bias_score: float  # 0-1 scale
    performance_drop: float  # Percentage drop in performance
    affected_metrics: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: List[str]
    cultural_factors: Dict[str, Any]
    compliance_issues: List[str]

# Mock data generators (to be deprecated)
def generate_governance_metrics():
    """Generate mock governance metrics"""
    categories = ['FAIRNESS', 'ROBUSTNESS', 'EXPLAINABILITY', 'COMPLIANCE', 'LLM_SAFETY']
    metrics = []
    
    for i, category in enumerate(categories):
        for j in range(3):
            value = random.uniform(70, 95)
            trend = random.uniform(-5, 10)
            status = 'GOOD' if value > 80 else 'WARNING' if value > 60 else 'CRITICAL'
            
            metrics.append({
                "id": f"metric_{category.lower()}_{j}",
                "name": f"{category} Metric {j+1}",
                "value": round(value, 1),
                "unit": "%",
                "trend": round(trend, 1),
                "threshold": 80,
                "status": status,
                "category": category,
                "updatedAt": datetime.now().isoformat()
            })
    
    return metrics

def generate_models():
    """Generate mock AI models"""
    model_types = ['TRADITIONAL_ML', 'LLM', 'DEEP_LEARNING', 'ENSEMBLE']
    statuses = ['DRAFT', 'TRAINING', 'ACTIVE', 'DEPRECATED', 'ARCHIVED']
    models = []
    
    for i in range(10):
        model_type = random.choice(model_types)
        status = random.choice(statuses)
        
        models.append({
            "id": f"model_{i+1}",
            "name": f"AI Model {i+1}",
            "version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "type": model_type,
            "status": status,
            "filePath": f"/models/model_{i+1}.pkl",
            "metadata": {
                "description": f"AI model for {model_type.lower()} tasks",
                "tags": ["ai", "ml", model_type.lower()],
                "framework": "scikit-learn" if model_type == 'TRADITIONAL_ML' else "pytorch",
                "algorithm": "random_forest" if model_type == 'TRADITIONAL_ML' else "transformer",
                "hyperparameters": {"learning_rate": 0.001, "batch_size": 32},
                "trainingData": {
                    "size": random.randint(1000, 100000),
                    "features": random.randint(10, 100),
                    "samples": random.randint(5000, 50000)
                },
                "performance": {
                    "accuracy": round(random.uniform(0.75, 0.95), 3),
                    "precision": round(random.uniform(0.70, 0.90), 3),
                    "recall": round(random.uniform(0.70, 0.90), 3),
                    "f1Score": round(random.uniform(0.70, 0.90), 3)
                }
            },
            "createdAt": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "updatedAt": datetime.now().isoformat()
        })
    
    return models

def generate_simulations():
    """Generate mock simulations"""
    simulation_types = ['FAIRNESS', 'ROBUSTNESS', 'EXPLAINABILITY', 'COMPLIANCE', 'LLM_SAFETY']
    statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED']
    simulations = []
    
    for i in range(5):
        sim_type = random.choice(simulation_types)
        status = random.choice(statuses)
        
        simulations.append({
            "id": f"sim_{i+1}",
            "name": f"{sim_type} Simulation {i+1}",
            "modelId": f"model_{random.randint(1, 10)}",
            "model": {
                "id": f"model_{i+1}",
                "name": f"AI Model {i+1}"
            },
            "status": status,
            "type": sim_type,
            "config": {
                "testCases": random.randint(100, 1000),
                "scenarios": ["scenario_1", "scenario_2", "scenario_3"],
                "thresholds": {"fairness": 0.8, "robustness": 0.7},
                "parameters": {"timeout": 300, "max_iterations": 1000}
            },
            "results": {
                "fairness": round(random.uniform(0.70, 0.95), 2),
                "robustness": round(random.uniform(0.65, 0.90), 2),
                "explainability": round(random.uniform(0.60, 0.85), 2),
                "compliance": round(random.uniform(0.75, 0.95), 2),
                "llmSafety": round(random.uniform(0.70, 0.90), 2) if sim_type == 'LLM_SAFETY' else None,
                "details": {"execution_time": random.randint(30, 300)},
                "charts": [],
                "logs": []
            },
            "createdAt": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "completedAt": datetime.now().isoformat() if status == 'COMPLETED' else None
        })
    
    return simulations


# ---------------------------------------------------------------------------
# Model upload and simulation endpoints
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


@app.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accept CSV or Parquet datasets, store under datasets/, and return inferred schema.
    """
    try:
        safe_name = file.filename.replace("..", "_") if file.filename else f"dataset_{int(datetime.now().timestamp())}.csv"
        target_path = DATASET_DIR / safe_name
        content = await file.read()
        target_path.write_bytes(content)

        lname = safe_name.lower()
        if lname.endswith(".csv"):
            df = pd.read_csv(target_path, nrows=2500)
        elif lname.endswith(".parquet"):
            df = pd.read_parquet(target_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported dataset format. Use CSV or Parquet.")

        columns = [{"name": c, "dtype": str(df[c].dtype)} for c in df.columns]
        return {
            "success": True,
            "path": str(target_path.resolve()),
            "schema": {"columns": columns, "rows_sampled": int(df.shape[0])},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Dataset upload failed")
        raise HTTPException(status_code=500, detail=f"Dataset upload failed: {e}")


class GenerateDatasetRequest(BaseModel):
    row_count: int = 1000
    schema: Optional[Dict[str, Any]] = None  # {columns: [{name, dtype}]}
    sample_path: Optional[str] = None
    engine: Optional[str] = "builtin"  # builtin | sdv


@app.post("/datasets/generate")
async def generate_dataset(req: GenerateDatasetRequest):
    """
    Generate a synthetic tabular dataset using a simple statistical approach.
    - If sample_path provided: infer distributions from sample data
    - Else if schema provided: synthesize based on dtypes
    - Returns a CSV path under datasets/
    """
    try:
        # Load reference dataframe if provided
        df_ref: Optional[pd.DataFrame] = None
        if req.sample_path:
            sp = Path(req.sample_path)
            if not sp.exists():
                raise HTTPException(status_code=400, detail="sample_path does not exist")
            if sp.name.lower().endswith(".csv"):
                df_ref = pd.read_csv(sp)
            elif sp.name.lower().endswith(".parquet"):
                df_ref = pd.read_parquet(sp)
            else:
                raise HTTPException(status_code=400, detail="Unsupported sample format")

        # Build column spec
        if df_ref is not None:
            columns = [(c, str(df_ref[c].dtype)) for c in df_ref.columns]
        elif req.schema and isinstance(req.schema.get("columns"), list):
            columns = [(c["name"], c.get("dtype", "object")) for c in req.schema["columns"]]
        else:
            raise HTTPException(status_code=400, detail="Provide sample_path or schema.columns")

        num_rows = max(1, int(req.row_count))

        # Engine: SDV (requires sample_path or df_ref)
        if (req.engine or "builtin").lower() == "sdv":
            try:
                if df_ref is None:
                    raise HTTPException(status_code=400, detail="SDV engine requires a sample_path with real data. Provide a sample or use engine=builtin.")
                # Import SDV lazily
                from sdv.metadata import SingleTableMetadata  # type: ignore
                from sdv.single_table import GaussianCopulaSynthesizer  # type: ignore

                metadata = SingleTableMetadata()
                metadata.detect_from_dataframe(df_ref)
                synthesizer = GaussianCopulaSynthesizer(metadata)
                synthesizer.fit(df_ref)
                df_gen = synthesizer.sample(num_rows)
            except HTTPException:
                raise
            except ImportError:
                raise HTTPException(status_code=400, detail="SDV is not installed. Install 'sdv' or use engine=builtin.")
            except Exception as e:
                logger.exception("SDV generation failed")
                raise HTTPException(status_code=500, detail=f"SDV generation failed: {e}")
        else:
            # Built-in lightweight generator (NumPy/Pandas)
            data: Dict[str, Any] = {}
            rng = np.random.default_rng()
            for name, dtype in columns:
                if df_ref is not None:
                    series = df_ref[name]
                    if pd.api.types.is_numeric_dtype(series):
                        mu = float(series.mean()) if len(series) else 0.0
                        sigma = float(series.std()) if len(series) else 1.0
                        sigma = sigma if sigma > 0 else max(1e-6, abs(mu) * 0.1)
                        data[name] = rng.normal(mu, sigma, size=num_rows)
                    elif pd.api.types.is_datetime64_any_dtype(series):
                        if len(series.dropna()) == 0:
                            data[name] = pd.date_range("2020-01-01", periods=num_rows, freq="D")
                        else:
                            s = pd.to_datetime(series.dropna())
                            start, end = s.min().value, s.max().value
                            if start == end:
                                end = start + 86_400_000_000_000  # +1 day in ns
                            rand_ns = rng.integers(low=start, high=end, size=num_rows)
                            data[name] = pd.to_datetime(rand_ns)
                    else:
                        vals = series.dropna().astype(str)
                        if len(vals) == 0:
                            data[name] = rng.choice(["A", "B"], size=num_rows)
                        else:
                            value_counts = vals.value_counts(normalize=True)
                            cats = value_counts.index.tolist()
                            probs = value_counts.values.tolist()
                            data[name] = rng.choice(cats, p=probs, size=num_rows)
                else:
                    dt = dtype.lower()
                    if any(k in dt for k in ["int", "float", "double", "decimal"]):
                        data[name] = rng.normal(0, 1, size=num_rows)
                    elif "date" in dt or "time" in dt:
                        base = pd.Timestamp("2022-01-01").value
                        rand_ns = rng.integers(low=base, high=base + 365*24*3600*1_000_000_000, size=num_rows)
                        data[name] = pd.to_datetime(rand_ns)
                    else:
                        data[name] = rng.choice(["A", "B", "C"], size=num_rows)

            df_gen = pd.DataFrame(data)
        # Cast datetimes to iso strings for CSV
        for col in df_gen.columns:
            if pd.api.types.is_datetime64_any_dtype(df_gen[col]):
                df_gen[col] = df_gen[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        out_path = DATASET_DIR / f"synthetic_{int(datetime.now().timestamp())}.csv"
        df_gen.to_csv(out_path, index=False)

        columns_resp = [{"name": c, "dtype": str(df_gen[c].dtype)} for c in df_gen.columns]
        return {
            "success": True,
            "path": str(out_path.resolve()),
            "rows": int(df_gen.shape[0]),
            "schema": {"columns": columns_resp},
            "engine": (req.engine or "builtin").lower(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Synthetic generation failed")
        raise HTTPException(status_code=500, detail=f"Synthetic generation failed: {e}")


@app.post("/models/upload")
async def upload_model(
    file: UploadFile = File(...),
    model_id: Optional[str] = Form(None),
    framework: Optional[str] = Form(None),
):
    """
    Accept a model artifact (e.g., .pkl, .joblib, .pt, .onnx, .h5) and store it.
    Returns basic metadata. For pickle/joblib, attempts a safe load to validate.
    """
    try:
        safe_name = file.filename.replace("..", "_") if file.filename else f"model_{int(datetime.now().timestamp())}"
        target_path = UPLOAD_DIR / safe_name
        content = await file.read()
        target_path.write_bytes(content)

        file_hash = _sha256_file(target_path)
        size_bytes = target_path.stat().st_size

        load_result = None
        lower = safe_name.lower()
        if lower.endswith((".pkl", ".pickle", ".joblib")):
            try:
                import joblib  # type: ignore
                _ = joblib.load(target_path)
                load_result = "loaded_ok"
            except Exception as load_err:
                load_result = f"load_failed: {load_err.__class__.__name__}"

        return {
            "success": True,
            "model_id": model_id or safe_name,
            "filename": safe_name,
            "path": str(target_path.resolve()),
            "size_bytes": size_bytes,
            "sha256": file_hash,
            "framework": framework,
            "validation": load_result,
        }
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


class ModelRegistryEntry(BaseModel):
    id: str
    name: str
    version: Optional[str] = None
    type: Optional[str] = None
    framework: Optional[str] = None
    tags: Optional[List[str]] = None
    company: Optional[str] = None
    risk_level: Optional[str] = None
    deployment_environment: Optional[str] = None
    path: Optional[str] = None
    sha256: Optional[str] = None
    created_at: str


def _read_registry() -> List[Dict[str, Any]]:
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text())
        except Exception:
            return []
    return []


def _write_registry(entries: List[Dict[str, Any]]):
    REGISTRY_FILE.write_text(json.dumps(entries, indent=2))


@app.post("/models/register")
async def register_model(entry: ModelRegistryEntry):
    try:
        entries = _read_registry()
        entries.append(entry.model_dump())
        _write_registry(entries)
        return {"success": True}
    except Exception as e:
        logger.exception("Model register failed")
        raise HTTPException(status_code=500, detail=f"Register failed: {e}")

class RunSimulationRequest(BaseModel):
    path: str  # model artifact path
    simulation_type: Optional[str] = "baseline"
    dataset_path: Optional[str] = None
    target: Optional[str] = None
    features: Optional[List[str]] = None
    protected_attributes: Optional[List[str]] = None
    org_id: Optional[str] = None  # organization scoping


@app.post("/simulation/run")
async def run_simulation(req: RunSimulationRequest):
    try:
        artifact = Path(req.path)
        if not artifact.exists():
            raise HTTPException(status_code=400, detail="Artifact path does not exist")

        size_bytes = artifact.stat().st_size
        sha = _sha256_file(artifact)
        ext = artifact.suffix.lower()

        performance: Dict[str, Any] = {}
        fairness: Dict[str, Any] = {}

        # If dataset info provided, attempt real sklearn-based evaluation
        if req.dataset_path and req.target and req.features:
            ds_path = Path(req.dataset_path)
            if not ds_path.exists():
                raise HTTPException(status_code=400, detail="Dataset path does not exist")

            # Load dataset
            if ds_path.name.lower().endswith(".csv"):
                df = pd.read_csv(ds_path)
            elif ds_path.name.lower().endswith(".parquet"):
                df = pd.read_parquet(ds_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported dataset format")

            missing = [c for c in [req.target, *req.features] if c not in df.columns]
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing columns in dataset: {missing}")

            X = df[req.features]
            y = df[req.target]

            # Try to load sklearn model and predict
            try:
                import joblib  # type: ignore
                model = joblib.load(artifact)
                if hasattr(model, "predict"):
                    y_pred = model.predict(X)
                else:
                    y_pred = None
            except Exception as load_err:
                logger.warning(f"Model load/predict failed: {load_err}")
                y_pred = None

            # Fallback majority baseline
            if y_pred is None:
                majority = y.mode().iloc[0]
                y_pred = [majority] * len(y)

            # Compute metrics
            try:
                from sklearn.metrics import (
                    accuracy_score,
                    precision_score,
                    recall_score,
                    f1_score,
                    confusion_matrix,
                    roc_auc_score,
                    precision_recall_fscore_support,
                )  # type: ignore

                acc = float(accuracy_score(y, y_pred))
                prec_macro = float(precision_score(y, y_pred, average="macro", zero_division=0))
                rec_macro = float(recall_score(y, y_pred, average="macro", zero_division=0))
                f1_macro = float(f1_score(y, y_pred, average="macro", zero_division=0))

                # Per-class metrics
                per_prec, per_rec, per_f1, per_support = precision_recall_fscore_support(
                    y, y_pred, average=None, zero_division=0
                )
                labels_sorted = sorted(list(pd.Series(y).unique()))
                per_class = [
                    {
                        "label": int(lbl) if isinstance(lbl, (int, float, bool)) and not pd.isna(lbl) else str(lbl),
                        "precision": float(per_prec[idx]) if idx < len(per_prec) else 0.0,
                        "recall": float(per_rec[idx]) if idx < len(per_rec) else 0.0,
                        "f1": float(per_f1[idx]) if idx < len(per_f1) else 0.0,
                        "support": int(per_support[idx]) if idx < len(per_support) else 0,
                    }
                    for idx, lbl in enumerate(labels_sorted)
                ]

                # Confusion matrix
                cm = confusion_matrix(y, y_pred, labels=labels_sorted)
                cm_list = cm.tolist()

                # ROC AUC (if possible)
                auc_roc = None
                try:
                    if hasattr(model, "predict_proba"):
                        y_scores = model.predict_proba(X)
                        if y_scores.ndim == 2 and y_scores.shape[1] == 2:
                            auc_roc = float(roc_auc_score(y, y_scores[:, 1]))
                        else:
                            # multiclass macro-average
                            auc_roc = float(roc_auc_score(y, y_scores, multi_class="ovr", average="macro"))
                    elif hasattr(model, "decision_function"):
                        y_scores = model.decision_function(X)
                        if y_scores.ndim == 1:
                            auc_roc = float(roc_auc_score(y, y_scores))
                        else:
                            auc_roc = float(roc_auc_score(y, y_scores, multi_class="ovr", average="macro"))
                except Exception as auc_err:
                    logger.info(f"AUC computation skipped: {auc_err}")

                performance = {
                    "accuracy": acc,
                    "precision_macro": prec_macro,
                    "recall_macro": rec_macro,
                    "f1_macro": f1_macro,
                    "per_class": per_class,
                    "confusion_matrix": {
                        "labels": labels_sorted,
                        "matrix": cm_list,
                    },
                    **({"roc_auc": auc_roc} if auc_roc is not None else {}),
                }
            except Exception as met_err:
                logger.warning(f"Metric computation failed: {met_err}")

            # Simple demographic parity proxy by protected attributes
            fairness_by_attr = []
            for attr in (req.protected_attributes or []):
                if attr in df.columns:
                    try:
                        grp_rates: Dict[str, float] = {}
                        for grp_val, grp_df in df.groupby(df[attr].astype(str)):
                            pos_label = y.value_counts().index[0]
                            grp_idx = grp_df.index
                            grp_pred = pd.Series(y_pred).iloc[grp_idx]
                            grp_rates[str(grp_val)] = float((grp_pred == pos_label).mean())
                        if grp_rates:
                            vals = list(grp_rates.values())
                            dp_diff = float(max(vals) - min(vals))
                            fairness_by_attr.append({
                                "attribute": attr,
                                "demographic_parity_difference": dp_diff,
                                "group_positive_rates": grp_rates,
                            })
                    except Exception as fe:
                        logger.warning(f"Fairness metric failed for {attr}: {fe}")
            fairness = {"by_attribute": fairness_by_attr}
        else:
            # Mock metrics if dataset not provided
            rng = random.Random(int(size_bytes) ^ int(sha[:8], 16))
            performance = {
                "accuracy": round(0.6 + rng.random() * 0.35, 3),
                "precision_macro": round(0.55 + rng.random() * 0.4, 3),
                "recall_macro": round(0.55 + rng.random() * 0.4, 3),
                "f1_macro": round(0.55 + rng.random() * 0.4, 3),
            }
            fairness = {"by_attribute": []}

        result = {
            "success": True,
            "simulation_type": req.simulation_type,
            "artifact": {
                "path": str(artifact.resolve()),
                "extension": ext,
                "size_bytes": size_bytes,
                "sha256": sha,
            },
            "metrics": {
                "performance": performance,
                "fairness": fairness,
            },
            "org_id": req.org_id,
            "created_at": datetime.now().isoformat(),
        }

        # Persist lightweight result summary for dashboards
        try:
            existing: List[Dict[str, Any]]
            if RESULTS_FILE.exists():
                existing = json.loads(RESULTS_FILE.read_text())
            else:
                existing = []
            existing.append(result)
            # cap file size
            if len(existing) > 200:
                existing = existing[-200:]
            RESULTS_FILE.write_text(json.dumps(existing))
        except Exception as write_err:
            logger.warning(f"Failed to persist simulation result: {write_err}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Simulation failed")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

def generate_ai_bill_requirements():
    """Generate mock AI Bill requirements"""
    categories = ['TRANSPARENCY', 'ACCOUNTABILITY', 'FAIRNESS', 'PRIVACY', 'SECURITY', 'HUMAN_OVERSIGHT', 'RISK_ASSESSMENT', 'DOCUMENTATION']
    statuses = ['PENDING', 'IN_PROGRESS', 'COMPLIANT', 'NON_COMPLIANT']
    impacts = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    requirements = []
    
    for i in range(8):
        category = categories[i]
        status = random.choice(statuses)
        impact = random.choice(impacts)
        
        requirements.append({
            "id": f"req_{i+1}",
            "title": f"{category} Requirement {i+1}",
            "description": f"Ensure {category.lower()} compliance for AI systems",
            "category": category,
            "status": status,
            "deadline": (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
            "impact": impact,
            "requirements": [
                f"Implement {category.lower()} monitoring",
                f"Document {category.lower()} procedures",
                f"Train staff on {category.lower()} requirements"
            ],
            "evidence": [
                f"{category.lower()}_policy.pdf",
                f"{category.lower()}_training_certificate.pdf"
            ],
            "assignedTo": f"user_{random.randint(1, 5)}",
            "createdAt": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "updatedAt": datetime.now().isoformat()
        })
    
    return requirements

@app.get("/")
async def root():
    return {"message": "Fairmind ML Service - AI Governance API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fairmind-ml", "version": "1.0.0"}

# Mock data endpoints
@app.get("/governance/metrics")
async def get_governance_metrics():
    """Get governance metrics"""
    try:
        metrics = generate_governance_metrics()
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching governance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch governance metrics: {str(e)}")

@app.get("/models")
async def get_models(page: int = 1, limit: int = 10, company: Optional[str] = None, org_id: Optional[str] = None):
    """Get registered models from catalog and registry."""
    try:
        models = []
        
        # Get models from catalog
        catalog_models = catalog_manager.get_available_models()
        for model in catalog_models:
            if model.get("available"):
                models.append({
                    "id": model["key"],
                    "name": model["name"],
                    "source": model["source"],
                    "type": model["type"],
                    "framework": model["framework"],
                    "dataset": model["dataset"],
                    "description": model["description"],
                    "tags": model["tags"],
                    "path": model["path"],
                    "available": True,
                    "created_at": model.get("downloaded_at", model.get("trained_at", datetime.now().isoformat())),
                    "org_id": "public"  # Catalog models are public
                })
        
        # Get models from registry
        entries = _read_registry()
        
        # Filter by org_id (preferred) or company
        if org_id:
            entries = [e for e in entries if (e.get("org_id") or "") == org_id]
        elif company:
            entries = [e for e in entries if (e.get("company") or "").lower() == company.lower()]
        
        # Add registry models
        for entry in entries:
            models.append({
                "id": entry.get("id"),
                "name": entry.get("name"),
                "source": "registry",
                "type": entry.get("type"),
                "framework": entry.get("framework"),
                "tags": entry.get("tags"),
                "path": entry.get("path"),
                "available": True,
                "created_at": entry.get("created_at"),
                "org_id": entry.get("org_id")
            })
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated = models[start_idx:end_idx]
        return {"success": True, "data": paginated, "total": len(models)}
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@app.get("/simulations/recent")
async def get_recent_simulations(limit: int = 10, company: Optional[str] = None, org_id: Optional[str] = None):
    try:
        if not RESULTS_FILE.exists():
            return {"success": True, "data": []}
        items: List[Dict[str, Any]] = json.loads(RESULTS_FILE.read_text())
        
        # Filter by org_id (preferred) or company
        if org_id:
            items = [i for i in items if (i.get("org_id") or "") == org_id]
        elif company:
            items = [i for i in items if (i.get("org_id") or "") == company or (i.get("company") or "").lower() == (company or "").lower()]
        
        # Transform to match frontend expectations
        transformed_items = []
        for item in sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]:
            transformed_items.append({
                "id": item.get("id", str(uuid.uuid4())),
                "model_name": item.get("model_name", "Unknown Model"),
                "created_at": item.get("created_at", datetime.now().isoformat()),
                "status": "completed" if item.get("metrics") else "failed",
                "metrics": item.get("metrics", {})
            })
        
        return transformed_items
    except Exception as e:
        logger.error(f"Error fetching recent simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch simulations: {str(e)}")


@app.get("/datasets")
async def get_datasets(org_id: Optional[str] = None):
    """Get available datasets from catalog and uploads"""
    try:
        datasets = []
        
        # Get datasets from catalog
        catalog_datasets = catalog_manager.get_available_datasets()
        for dataset in catalog_datasets:
            if dataset.get("available"):
                datasets.append({
                    "name": dataset["name"],
                    "path": dataset["path"],
                    "source": dataset["source"],
                    "description": dataset["description"],
                    "target": dataset["target"],
                    "features": dataset["features"],
                    "protected_attributes": dataset["protected_attributes"],
                    "available": True,
                    "created_at": dataset.get("downloaded_at", datetime.now().isoformat())
                })
        
        # Get uploaded datasets
        if DATASET_DIR.exists():
            for file_path in DATASET_DIR.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.parquet']:
                    try:
                        # Read sample data to get schema
                        if file_path.suffix.lower() == '.csv':
                            df = pd.read_csv(file_path, nrows=5)
                        else:
                            df = pd.read_parquet(file_path)
                        
                        dataset_info = {
                            "name": f"Uploaded: {file_path.name}",
                            "path": str(file_path),
                            "source": "uploaded",
                            "description": "User uploaded dataset",
                            "target": None,
                            "features": list(df.columns),
                            "protected_attributes": [],
                            "available": True,
                            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                        datasets.append(dataset_info)
                        
                    except Exception as e:
                        logger.warning(f"Could not read dataset {file_path}: {e}")
                        continue
        
        return {"success": True, "data": datasets}
    except Exception as e:
        logger.error(f"Error fetching datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")

@app.get("/metrics/summary")
async def get_metrics_summary(company: Optional[str] = None):
    """
    Aggregate basic fairness/performance metrics for dashboard charts.
    """
    try:
        if not RESULTS_FILE.exists():
            return {"success": True, "fairness": {"attributes": []}, "runs": 0}
        items: List[Dict[str, Any]] = json.loads(RESULTS_FILE.read_text())
        if company:
            items = [i for i in items if (i.get("org_id") or "") == company or (i.get("company") or "").lower() == (company or "").lower()]
        runs = len(items)

        # Collect demographic_parity_difference per attribute across runs
        dp_by_attr: Dict[str, List[float]] = {}
        for it in items:
            by_attr = (it.get("metrics", {}).get("fairness", {}).get("by_attribute") or [])
            for entry in by_attr:
                attr = str(entry.get("attribute"))
                dp = float(entry.get("demographic_parity_difference", 0.0))
                dp_by_attr.setdefault(attr, []).append(dp)

        attributes_summary = []
        for attr, dps in dp_by_attr.items():
            if not dps:
                continue
            avg_dp = float(sum(dps) / len(dps))
            attributes_summary.append({
                "attribute": attr,
                "avg_demographic_parity_difference": avg_dp,
            })

        return {"success": True, "fairness": {"attributes": attributes_summary}, "runs": runs}
    except Exception as e:
        logger.error(f"Error building metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")

@app.get("/simulations")
async def get_simulations(page: int = 1, limit: int = 10, status: Optional[str] = None, type: Optional[str] = None):
    """Get simulations"""
    try:
        simulations = generate_simulations()
        
        # Filter by status and type if provided
        if status:
            simulations = [s for s in simulations if s["status"] == status]
        if type:
            simulations = [s for s in simulations if s["type"] == type]
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_simulations = simulations[start_idx:end_idx]
        
        return {
            "success": True,
            "data": paginated_simulations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch simulations: {str(e)}")

@app.get("/ai-bill/requirements")
async def get_ai_bill_requirements():
    """Get AI Bill requirements"""
    try:
        requirements = generate_ai_bill_requirements()
        return {
            "success": True,
            "data": requirements,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching AI Bill requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI Bill requirements: {str(e)}")

# Placeholder endpoints - to be implemented with actual ML algorithms
@app.post("/analyze/bias")
async def analyze_bias(request: BiasAnalysisRequest):
    """
    Analyze model predictions for bias across protected groups using real algorithms
    """
    try:
        logger.info(f"Analyzing bias for model at: {request.model_path}")
        
        # Load model
        try:
            model = joblib.load(request.model_path)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid model file: {e}")
        
        # Load dataset
        try:
            if request.dataset_path.endswith('.csv'):
                df = pd.read_csv(request.dataset_path)
            else:
                df = pd.read_parquet(request.dataset_path)
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid dataset file: {e}")
        
        # Validate columns exist
        missing_cols = [col for col in [request.target] + request.features + request.protected_attributes if col not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing_cols}")
        
        # Prepare data
        X = df[request.features]
        y = df[request.target]
        
        # Get predictions
        try:
            if hasattr(model, 'predict_proba'):
                predictions = model.predict_proba(X)[:, 1]  # Probability of positive class
            else:
                predictions = model.predict(X)
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            raise HTTPException(status_code=400, detail=f"Model prediction error: {e}")
        
        # Calculate bias metrics for each protected attribute
        bias_metrics = []
        overall_score = 1.0
        bias_detected = False
        risk_level = "LOW"
        affected_groups = []
        recommendations = []
        
        for attr in request.protected_attributes:
            if attr not in df.columns:
                continue
                
            # Get unique values for this attribute
            unique_values = df[attr].unique()
            if len(unique_values) < 2:
                continue
            
            # Calculate demographic parity difference
            dp_differences = []
            for val in unique_values:
                group_mask = df[attr] == val
                if group_mask.sum() < 10:  # Skip small groups
                    continue
                    
                group_predictions = predictions[group_mask]
                group_positive_rate = np.mean(group_predictions > 0.5)
                dp_differences.append(abs(group_positive_rate - np.mean(predictions > 0.5)))
            
            if dp_differences:
                max_dp_diff = max(dp_differences)
                threshold = 0.1  # 10% difference threshold
                
                bias_metrics.append({
                    "name": f"Demographic Parity - {attr}",
                    "value": max_dp_diff,
                    "threshold": threshold,
                    "status": "fail" if max_dp_diff > threshold else "pass",
                    "description": f"Maximum difference in positive prediction rates across {attr} groups"
                })
                
                if max_dp_diff > threshold:
                    bias_detected = True
                    affected_groups.append(f"{attr}_groups")
                    overall_score = min(overall_score, 1 - max_dp_diff)
        
        # Determine risk level
        if overall_score < 0.7:
            risk_level = "CRITICAL"
        elif overall_score < 0.8:
            risk_level = "HIGH"
        elif overall_score < 0.9:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate recommendations
        if bias_detected:
            recommendations.extend([
                "Consider rebalancing training data across protected groups",
                "Apply bias mitigation techniques like reweighting or adversarial debiasing",
                "Monitor model performance across different demographic groups",
                "Review feature engineering to ensure no proxy discrimination"
            ])
        else:
            recommendations.append("Model appears fair across analyzed protected attributes")
        
        return {
            "overall_score": overall_score,
            "bias_detected": bias_detected,
            "risk_level": risk_level,
            "metrics": bias_metrics,
            "recommendations": recommendations,
            "affected_groups": affected_groups,
            "protected_attributes": request.protected_attributes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing bias: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bias analysis failed: {str(e)}")

@app.post("/explain/model")
async def explain_model_prediction(model_id: str, prediction_data: Dict[str, Any]):
    """
    Generate SHAP/LIME explanations for model predictions
    """
    try:
        # TODO: Implement SHAP/LIME integration
        logger.info(f"Generating explanation for model: {model_id}")
        
        return {
            "model_id": model_id,
            "explanation_type": "SHAP",
            "feature_importance": {
                "credit_score": 0.34,
                "income": 0.28,
                "debt_to_income": 0.22,
                "employment_length": 0.16
            },
            "local_explanation": {
                "prediction": 0.78,
                "base_value": 0.5,
                "contributions": {
                    "credit_score": 0.15,
                    "income": 0.08,
                    "debt_to_income": 0.05
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@app.post("/compliance/nist-score")
async def calculate_nist_compliance(model_id: str, assessment_data: Dict[str, Any]):
    """
    Calculate NIST AI RMF compliance score
    """
    try:
        # TODO: Implement NIST compliance scoring algorithm
        logger.info(f"Calculating NIST compliance for model: {model_id}")
        
        return {
            "model_id": model_id,
            "overall_score": 82,
            "framework_scores": {
                "GOVERN": 84,
                "MAP": 78,
                "MEASURE": 82,
                "MANAGE": 85
            },
            "compliance_status": "COMPLIANT",
            "areas_for_improvement": [
                "Improve model documentation",
                "Enhance bias monitoring"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error calculating NIST compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"NIST compliance calculation failed: {str(e)}")

@app.post("/monitor/drift")
async def detect_model_drift(model_id: str, current_data: List[Dict[str, Any]], reference_data: List[Dict[str, Any]]):
    """
    Detect data/concept drift in model inputs and outputs
    """
    try:
        # TODO: Implement drift detection algorithms
        logger.info(f"Detecting drift for model: {model_id}")
        
        return {
            "model_id": model_id,
            "drift_detected": True,
            "drift_type": "DATA_DRIFT",
            "drift_score": 0.23,
            "affected_features": ["age", "income"],
            "recommendation": "Retrain model with recent data"
        }
        
    except Exception as e:
        logger.error(f"Error detecting drift: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket(websocket: WebSocket):
    await websocket_endpoint(websocket)

# Geographic Bias Detection
@app.post("/analyze/geographic-bias", response_model=GeographicBiasResponse)
async def analyze_geographic_bias(request: GeographicBiasRequest):
    """
    Analyze geographic bias when deploying models across different countries
    """
    try:
        logger.info(f"Analyzing geographic bias for model {request.model_id} from {request.source_country} to {request.target_country}")
        
        # Simulate geographic bias analysis
        source_performance = request.model_performance_data.get(request.source_country, {})
        target_performance = request.model_performance_data.get(request.target_country, {})
        
        # Calculate performance differences
        accuracy_drop = 0.0
        bias_score = 0.0
        affected_metrics = []
        
        if source_performance and target_performance:
            source_acc = source_performance.get('accuracy', 0.85)
            target_acc = target_performance.get('accuracy', 0.75)
            accuracy_drop = (source_acc - target_acc) / source_acc * 100
            bias_score = min(accuracy_drop / 20, 1.0)  # Normalize to 0-1
        
        # Determine risk level
        if bias_score > 0.7:
            risk_level = "CRITICAL"
        elif bias_score > 0.5:
            risk_level = "HIGH"
        elif bias_score > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate recommendations
        recommendations = []
        if bias_score > 0.5:
            recommendations.extend([
                "Retrain model with target country data",
                "Implement local data collection strategy",
                "Consider federated learning approach",
                "Add cultural adaptation layers"
            ])
        elif bias_score > 0.3:
            recommendations.extend([
                "Fine-tune model with local data",
                "Implement bias monitoring",
                "Add cultural context features"
            ])
        else:
            recommendations.append("Monitor performance regularly")
        
        # Compliance issues
        compliance_issues = []
        if bias_score > 0.5:
            compliance_issues.extend([
                "Potential violation of equal treatment laws",
                "Risk of discriminatory outcomes",
                "May violate local AI regulations"
            ])
        
        # Cultural factors analysis
        cultural_factors = {
            "language_differences": request.cultural_factors.get("language", "Unknown"),
            "economic_factors": request.cultural_factors.get("economic", "Unknown"),
            "cultural_norms": request.cultural_factors.get("cultural", "Unknown"),
            "regulatory_environment": request.cultural_factors.get("regulatory", "Unknown")
        }
        
        # Create response
        response_data = {
            "model_id": request.model_id,
            "source_country": request.source_country,
            "target_country": request.target_country,
            "bias_detected": bias_score > 0.3,
            "bias_score": round(bias_score, 3),
            "performance_drop": round(accuracy_drop, 2),
            "affected_metrics": ["accuracy", "precision", "recall"],
            "risk_level": risk_level,
            "recommendations": recommendations,
            "cultural_factors": cultural_factors,
            "compliance_issues": compliance_issues
        }
        
        # Save to database
        await supabase_service.insert_geographic_bias_analysis({
            **response_data,
            "model_performance_data": request.model_performance_data,
            "demographic_data": request.demographic_data
        })
        
        return GeographicBiasResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error analyzing geographic bias: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Geographic bias analysis failed: {str(e)}")

# Geographic Bias Dashboard Data
@app.get("/geographic-bias/dashboard")
async def get_geographic_bias_dashboard():
    """
    Get dashboard data for geographic bias monitoring
    """
    try:
        # Get data from Supabase
        dashboard_data = await supabase_service.get_geographic_bias_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting geographic bias dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

# AI Model DNA Profiling Endpoints
@app.post("/dna/profile", response_model=ModelDNAProfile)
async def create_model_dna_profile(model_data: Dict[str, Any]):
    """
    Create a DNA profile for an AI model
    """
    try:
        logger.info(f"Creating DNA profile for model: {model_data.get('model_id', 'unknown')}")
        
        # Generate DNA signature
        dna_signature = generate_dna_signature(model_data)
        
        # Create DNA profile
        dna_profile = ModelDNAProfile(
            model_id=model_data.get("model_id", ""),
            dna_signature=dna_signature,
            parent_models=model_data.get("parent_models", []),
            child_models=model_data.get("child_models", []),
            inheritance_type=model_data.get("inheritance_type", "direct"),
            creation_date=datetime.now(),
            version=model_data.get("version", "1.0.0"),
            algorithm_family=model_data.get("algorithm_family", ""),
            training_data_sources=model_data.get("training_data_sources", []),
            bias_inheritance=model_data.get("bias_inheritance", []),
            performance_characteristics=model_data.get("performance_characteristics", {}),
            ethical_framework=model_data.get("ethical_framework", {}),
            risk_profile=model_data.get("risk_profile", {})
        )
        
        # Save to database (mock for now)
        logger.info(f"DNA profile created with signature: {dna_signature}")
        
        return dna_profile
        
    except Exception as e:
        logger.error(f"Error creating DNA profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DNA profile creation failed: {str(e)}")

@app.post("/dna/analyze-inheritance")
async def analyze_model_inheritance(parent_model: Dict[str, Any], child_model: Dict[str, Any]):
    """
    Analyze bias inheritance between parent and child models
    """
    try:
        logger.info(f"Analyzing inheritance from {parent_model.get('model_id')} to {child_model.get('model_id')}")
        
        inheritance_patterns = analyze_bias_inheritance(parent_model, child_model)
        
        return {
            "parent_model_id": parent_model.get("model_id"),
            "child_model_id": child_model.get("model_id"),
            "inheritance_patterns": inheritance_patterns,
            "total_patterns": len(inheritance_patterns),
            "amplified_biases": len([p for p in inheritance_patterns if p.inheritance_type == "amplified"]),
            "reduced_biases": len([p for p in inheritance_patterns if p.inheritance_type == "reduced"]),
            "new_biases": len([p for p in inheritance_patterns if p.inheritance_type == "new"]),
            "eliminated_biases": len([p for p in inheritance_patterns if p.inheritance_type == "eliminated"])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing inheritance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inheritance analysis failed: {str(e)}")

@app.get("/dna/lineage/{model_id}")
async def get_model_lineage(model_id: str):
    """
    Get the complete lineage tree for a model
    """
    try:
        logger.info(f"Getting lineage for model: {model_id}")
        
        # Mock lineage data
        lineage_data = [
            {
                "model_id": "gpt-4-base",
                "generation": 0,
                "parent_models": [],
                "child_models": ["gpt-4-finetuned"],
                "dna_signature": "a1b2c3d4e5f6g7h8",
                "creation_date": "2023-01-01T00:00:00",
                "bias_score": 0.15,
                "performance_score": 0.92,
                "risk_level": "LOW"
            },
            {
                "model_id": "gpt-4-finetuned",
                "generation": 1,
                "parent_models": ["gpt-4-base"],
                "child_models": ["gpt-4-specialized"],
                "dna_signature": "b2c3d4e5f6g7h8i9",
                "creation_date": "2023-06-01T00:00:00",
                "bias_score": 0.22,
                "performance_score": 0.89,
                "risk_level": "MEDIUM"
            },
            {
                "model_id": "gpt-4-specialized",
                "generation": 2,
                "parent_models": ["gpt-4-finetuned"],
                "child_models": [],
                "dna_signature": "c3d4e5f6g7h8i9j0",
                "creation_date": "2023-12-01T00:00:00",
                "bias_score": 0.18,
                "performance_score": 0.94,
                "risk_level": "LOW"
            }
        ]
        
        lineage_tree = create_model_lineage_tree(lineage_data)
        
        return {
            "model_id": model_id,
            "lineage_tree": lineage_tree,
            "total_generations": max([node.generation for node in lineage_tree]) + 1,
            "total_models": len(lineage_tree)
        }
        
    except Exception as e:
        logger.error(f"Error getting lineage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lineage retrieval failed: {str(e)}")

@app.get("/dna/evolution/{model_id}")
async def get_model_evolution(model_id: str):
    """
    Analyze the evolution of a model through its lineage
    """
    try:
        logger.info(f"Analyzing evolution for model: {model_id}")
        
        # Mock evolution data
        evolution_data = [
            {
                "model_id": "gpt-4-base",
                "generation": 0,
                "parent_models": [],
                "child_models": ["gpt-4-finetuned"],
                "dna_signature": "a1b2c3d4e5f6g7h8",
                "creation_date": "2023-01-01T00:00:00",
                "bias_score": 0.15,
                "performance_score": 0.92,
                "risk_level": "LOW",
                "bias_characteristics": {
                    "gender_bias": 0.12,
                    "racial_bias": 0.08,
                    "age_bias": 0.15
                }
            },
            {
                "model_id": "gpt-4-finetuned",
                "generation": 1,
                "parent_models": ["gpt-4-base"],
                "child_models": ["gpt-4-specialized"],
                "dna_signature": "b2c3d4e5f6g7h8i9",
                "creation_date": "2023-06-01T00:00:00",
                "bias_score": 0.22,
                "performance_score": 0.89,
                "risk_level": "MEDIUM",
                "bias_characteristics": {
                    "gender_bias": 0.18,
                    "racial_bias": 0.15,
                    "age_bias": 0.12
                }
            },
            {
                "model_id": "gpt-4-specialized",
                "generation": 2,
                "parent_models": ["gpt-4-finetuned"],
                "child_models": [],
                "dna_signature": "c3d4e5f6g7h8i9j0",
                "creation_date": "2023-12-01T00:00:00",
                "bias_score": 0.18,
                "performance_score": 0.94,
                "risk_level": "LOW",
                "bias_characteristics": {
                    "gender_bias": 0.10,
                    "racial_bias": 0.12,
                    "age_bias": 0.08
                }
            }
        ]
        
        evolution = analyze_model_evolution(model_id, evolution_data)
        
        return evolution
        
    except Exception as e:
        logger.error(f"Error analyzing evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evolution analysis failed: {str(e)}")

@app.get("/dna/dashboard")
async def get_dna_dashboard():
    """
    Get DNA profiling dashboard data
    """
    try:
        # Mock dashboard data
        dashboard_data = {
            "total_models_profiled": 47,
            "models_with_lineage": 23,
            "average_generations": 2.3,
            "bias_inheritance_stats": {
                "amplified": 12,
                "reduced": 8,
                "new": 5,
                "eliminated": 3
            },
            "recent_profiles": [
                {
                    "model_id": "gpt-4-specialized",
                    "dna_signature": "c3d4e5f6g7h8i9j0",
                    "generation": 2,
                    "bias_score": 0.18,
                    "risk_level": "LOW",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "model_id": "bert-finetuned",
                    "dna_signature": "d4e5f6g7h8i9j0k1",
                    "generation": 1,
                    "bias_score": 0.25,
                    "risk_level": "MEDIUM",
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ],
            "lineage_families": [
                {
                    "family_name": "GPT-4 Family",
                    "root_model": "gpt-4-base",
                    "total_models": 5,
                    "generations": 3,
                    "avg_bias_score": 0.18
                },
                {
                    "family_name": "BERT Family",
                    "root_model": "bert-base",
                    "total_models": 8,
                    "generations": 4,
                    "avg_bias_score": 0.22
                }
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting DNA dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

# AI Model Genetic Engineering Endpoints
@app.post("/genetic-engineering/analyze")
async def analyze_model_for_genetic_engineering(model_data: Dict[str, Any]):
    """
    Analyze a model to determine what genetic engineering modifications are needed
    """
    try:
        logger.info(f"Analyzing model for genetic engineering: {model_data.get('model_id', 'unknown')}")
        
        analysis = analyze_model_for_modification(model_data)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing model for genetic engineering: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Genetic engineering analysis failed: {str(e)}")

@app.post("/genetic-engineering/apply-modification")
async def apply_genetic_engineering_modification(model_data: Dict[str, Any], modification_config: Dict[str, Any]):
    """
    Apply a genetic engineering modification to a model
    """
    try:
        logger.info(f"Applying genetic engineering modification to model: {model_data.get('model_id', 'unknown')}")
        
        modification = apply_model_modification(model_data, modification_config)
        
        # Validate the modification
        safety_validation = validate_modification_safety(modification)
        
        return {
            "modification": modification,
            "safety_validation": safety_validation,
            "success": safety_validation["overall_safety"]
        }
        
    except Exception as e:
        logger.error(f"Error applying genetic engineering modification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Genetic engineering modification failed: {str(e)}")

@app.post("/genetic-engineering/session")
async def create_genetic_engineering_session_endpoint(model_id: str, modifications: List[Dict[str, Any]]):
    """
    Create a genetic engineering session with multiple modifications
    """
    try:
        logger.info(f"Creating genetic engineering session for model: {model_id}")
        
        # Convert modification data to ModelModification objects
        model_modifications = []
        for mod_data in modifications:
            modification = ModelModification(
                modification_id=mod_data.get("modification_id", ""),
                model_id=mod_data.get("model_id", model_id),
                modification_type=mod_data.get("modification_type", "bias_removal"),
                target_biases=mod_data.get("target_biases", []),
                removal_methods=mod_data.get("removal_methods", []),
                safety_level=mod_data.get("safety_level", "medium"),
                performance_impact=mod_data.get("performance_impact", {}),
                bias_reduction=mod_data.get("bias_reduction", {}),
                ethical_improvements=mod_data.get("ethical_improvements", {}),
                validation_results=mod_data.get("validation_results", {}),
                created_at=datetime.now()
            )
            model_modifications.append(modification)
        
        session = create_genetic_engineering_session(model_id, model_modifications)
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating genetic engineering session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Genetic engineering session creation failed: {str(e)}")

@app.get("/genetic-engineering/tools")
async def get_genetic_engineering_tools():
    """
    Get available genetic engineering tools
    """
    try:
        bias_removal_tools = create_bias_removal_tools()
        fairness_enhancements = create_fairness_enhancements()
        
        return {
            "bias_removal_tools": bias_removal_tools,
            "fairness_enhancements": fairness_enhancements,
            "total_tools": len(bias_removal_tools) + len(fairness_enhancements)
        }
        
    except Exception as e:
        logger.error(f"Error getting genetic engineering tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool retrieval failed: {str(e)}")

@app.get("/genetic-engineering/dashboard")
async def get_genetic_engineering_dashboard():
    """
    Get genetic engineering dashboard data
    """
    try:
        # Mock dashboard data
        dashboard_data = {
            "total_sessions": 23,
            "successful_modifications": 18,
            "average_bias_reduction": 0.35,
            "average_performance_impact": -0.04,
            "safety_score": 0.92,
            "recent_sessions": [
                {
                    "session_id": "session-001",
                    "model_id": "gpt-4-specialized",
                    "modifications_applied": 2,
                    "bias_reduction": 0.42,
                    "performance_impact": -0.03,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "session_id": "session-002",
                    "model_id": "bert-finetuned",
                    "modifications_applied": 1,
                    "bias_reduction": 0.28,
                    "performance_impact": -0.02,
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ],
            "popular_tools": [
                {
                    "tool_name": "Adversarial Debiasing",
                    "usage_count": 12,
                    "success_rate": 0.92,
                    "avg_effectiveness": 0.88
                },
                {
                    "tool_name": "Fairness Constraints",
                    "usage_count": 8,
                    "success_rate": 0.87,
                    "avg_effectiveness": 0.85
                }
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting genetic engineering dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

# AI Model Time Travel Endpoints
@app.get("/time-travel/scenarios")
async def get_historical_scenarios():
    """
    Get available historical scenarios for time travel analysis
    """
    try:
        scenarios = create_historical_scenarios()
        return {
            "scenarios": scenarios,
            "total_scenarios": len(scenarios)
        }
        
    except Exception as e:
        logger.error(f"Error getting historical scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scenario retrieval failed: {str(e)}")

@app.post("/time-travel/analyze")
async def analyze_model_in_time_travel(model_data: Dict[str, Any], scenario_id: str):
    """
    Analyze how a model would behave in a historical scenario
    """
    try:
        logger.info(f"Analyzing model in time travel scenario: {scenario_id}")
        
        scenarios = create_historical_scenarios()
        scenario = next((s for s in scenarios if s.scenario_id == scenario_id), None)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        
        analysis = analyze_model_in_historical_scenario(model_data, scenario)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing model in time travel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Time travel analysis failed: {str(e)}")

@app.post("/time-travel/bias-evolution")
async def analyze_bias_evolution_timeline_endpoint(model_data: Dict[str, Any]):
    """
    Analyze bias evolution over time
    """
    try:
        logger.info(f"Analyzing bias evolution timeline for model: {model_data.get('model_id', 'unknown')}")
        
        bias_evolution = analyze_bias_evolution_timeline(model_data)
        
        return {
            "model_id": model_data.get("model_id"),
            "bias_evolution": bias_evolution,
            "total_evolution_points": len(bias_evolution)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing bias evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bias evolution analysis failed: {str(e)}")

@app.post("/time-travel/performance-timeline")
async def analyze_performance_timeline_endpoint(model_data: Dict[str, Any]):
    """
    Analyze performance changes over time
    """
    try:
        logger.info(f"Analyzing performance timeline for model: {model_data.get('model_id', 'unknown')}")
        
        performance_comparisons = analyze_performance_timeline(model_data)
        
        return {
            "model_id": model_data.get("model_id"),
            "performance_comparisons": performance_comparisons,
            "total_comparisons": len(performance_comparisons)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing performance timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance timeline analysis failed: {str(e)}")

@app.get("/time-travel/dashboard")
async def get_time_travel_dashboard():
    """
    Get time travel dashboard data
    """
    try:
        dashboard_data = create_time_travel_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting time travel dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

# AI Circus Endpoints
@app.get("/circus/scenarios")
async def get_test_scenarios():
    """
    Get available test scenarios for AI Circus
    """
    try:
        scenarios = create_test_scenarios()
        return {
            "scenarios": scenarios,
            "total_scenarios": len(scenarios)
        }
    except Exception as e:
        logger.error(f"Error getting test scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scenario retrieval failed: {str(e)}")

@app.post("/circus/run-test")
async def run_comprehensive_test_endpoint(model_id: str, scenario_id: str):
    """
    Run a comprehensive test scenario for a model
    """
    try:
        logger.info(f"Running comprehensive test for model: {model_id} in scenario: {scenario_id}")
        
        scenarios = create_test_scenarios()
        scenario = next((s for s in scenarios if s.scenario_id == scenario_id), None)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        
        test_results = run_comprehensive_test(model_id, scenario)
        
        return test_results
        
    except Exception as e:
        logger.error(f"Error running comprehensive test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comprehensive test failed: {str(e)}")

@app.get("/circus/dashboard")
async def get_circus_dashboard():
    """
    Get AI Circus dashboard data
    """
    try:
        dashboard_data = create_circus_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting circus dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

# AI Ethics Observatory Endpoints
@app.get("/ethics/frameworks")
async def get_ethics_frameworks():
    """
    Get available ethics frameworks
    """
    try:
        frameworks = create_ethics_frameworks()
        return {
            "frameworks": frameworks,
            "total_frameworks": len(frameworks)
        }
    except Exception as e:
        logger.error(f"Error getting ethics frameworks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Framework retrieval failed: {str(e)}")

@app.post("/ethics/assess")
async def assess_model_ethics_endpoint(model_data: dict, framework_id: str):
    """
    Assess a model's compliance with a specific ethics framework
    """
    try:
        logger.info(f"Assessing model ethics for framework: {framework_id}")
        
        ethics_score = assess_model_ethics(model_data, framework_id)
        return ethics_score
        
    except Exception as e:
        logger.error(f"Error assessing model ethics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ethics assessment failed: {str(e)}")

@app.get("/ethics/dashboard")
async def get_ethics_dashboard():
    """
    Get Global AI Ethics Observatory dashboard data
    """
    try:
        dashboard_data = create_observatory_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting ethics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

# Email endpoints
@app.post("/api/email/send")
async def send_email(request: EmailRequest):
    """
    Send a general email
    """
    try:
        success = await email_service.send_email(
            to_email=request.to,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            from_email=request.from_email
        )
        
        return {
            "success": success,
            "message": "Email sent successfully" if success else "Failed to send email"
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

@app.post("/api/email/notification")
async def send_notification(request: NotificationRequest):
    """
    Send a notification email
    """
    try:
        success = await email_service.send_notification_email(
            to_email=request.to,
            notification_type=request.type,
            message=request.message,
            additional_data=request.additional_data
        )
        
        return {
            "success": success,
            "message": "Notification sent successfully" if success else "Failed to send notification"
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Notification sending failed: {str(e)}")

@app.post("/api/email/alert")
async def send_alert(request: AlertRequest):
    """
    Send an alert email
    """
    try:
        success = await email_service.send_alert_email(
            to_email=request.to,
            alert_type=request.alert_type,
            severity=request.severity,
            description=request.description,
            timestamp=request.timestamp
        )
        
        return {
            "success": success,
            "message": "Alert sent successfully" if success else "Failed to send alert"
        }
        
    except Exception as e:
        logger.error(f"Error sending alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Alert sending failed: {str(e)}")

@app.get("/api/email/test")
async def test_email():
    """
    Test email functionality
    """
    try:
        # Send a test email to support@fairmind.xyz
        success = await email_service.send_notification_email(
            to_email="support@fairmind.xyz",
            notification_type="System Test",
            message="This is a test email from FairMind AI Governance Platform. The email system is working correctly.",
            additional_data={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        return {
            "success": success,
            "message": "Test email sent successfully" if success else "Failed to send test email",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logging.getLogger(__name__).info(f"Starting backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

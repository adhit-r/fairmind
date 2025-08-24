"""
Fairness Governance API Routes
Integration endpoints for the comprehensive fairness library.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from fairness_library import (
    demographic_parity_diff, equalized_odds_diff, equal_opportunity_diff,
    weat_score, seat_score, minimal_pairs_test, behavioral_bias_detection,
    ModelRegistry, DatasetRegistry, RegistryManager,
    GovernanceGate, FairnessMonitor, BiasDetector, AlertManager, DriftDetector
)

router = APIRouter(prefix="/api/v1/fairness", tags=["Fairness Governance"])

# Initialize components
registry_manager = RegistryManager()
governance_gate = GovernanceGate()
fairness_monitor = FairnessMonitor()
bias_detector = BiasDetector()
alert_manager = AlertManager()
drift_detector = DriftDetector()

@router.post("/metrics/classic-ml")
async def compute_classic_ml_fairness(
    y_true: List[int],
    y_pred: List[int],
    sensitive_attributes: Dict[str, List],
    metrics: List[str] = ["demographic_parity", "equalized_odds", "equal_opportunity"],
    confidence_level: float = 0.95,
    threshold: float = 0.05
):
    """Compute classic ML fairness metrics"""
    try:
        import numpy as np
        
        # Convert to numpy arrays
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        
        results = {}
        
        for metric in metrics:
            if metric == "demographic_parity":
                result = demographic_parity_diff(
                    y_pred_arr, 
                    np.array(sensitive_attributes.get("primary", [])),
                    confidence_level, threshold
                )
                results[metric] = {
                    "value": result.value,
                    "confidence_interval": result.confidence_interval,
                    "p_value": result.p_value,
                    "is_fair": result.is_fair,
                    "details": result.details
                }
            
            elif metric == "equalized_odds":
                result = equalized_odds_diff(
                    y_true_arr, y_pred_arr,
                    np.array(sensitive_attributes.get("primary", [])),
                    confidence_level, threshold
                )
                results[metric] = {
                    "value": result.value,
                    "confidence_interval": result.confidence_interval,
                    "p_value": result.p_value,
                    "is_fair": result.is_fair,
                    "details": result.details
                }
            
            elif metric == "equal_opportunity":
                result = equal_opportunity_diff(
                    y_true_arr, y_pred_arr,
                    np.array(sensitive_attributes.get("primary", [])),
                    confidence_level, threshold
                )
                results[metric] = {
                    "value": result.value,
                    "confidence_interval": result.confidence_interval,
                    "p_value": result.p_value,
                    "is_fair": result.is_fair,
                    "details": result.details
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": results,
            "overall_fair": all(r["is_fair"] for r in results.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing fairness metrics: {str(e)}")

@router.post("/metrics/llm")
async def compute_llm_fairness(
    embeddings: Dict[str, List[float]],
    target_words: List[str],
    attribute_words_a: List[str],
    attribute_words_b: List[str],
    test_type: str = "weat",
    threshold: float = 0.1
):
    """Compute LLM fairness metrics"""
    try:
        import numpy as np
        
        # Convert embeddings to numpy arrays
        embeddings_np = {k: np.array(v) for k, v in embeddings.items()}
        
        if test_type == "weat":
            result = weat_score(
                embeddings_np, target_words, attribute_words_a, attribute_words_b, threshold
            )
        elif test_type == "seat":
            # For SEAT, we need sentence templates
            sentence_templates = [f"The {target} is" for target in target_words]
            result = seat_score(
                embeddings_np, sentence_templates, target_words, 
                attribute_words_a, attribute_words_b, threshold
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown test type: {test_type}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "test_type": test_type,
            "score": result.score,
            "confidence_interval": result.confidence_interval,
            "is_biased": result.is_biased,
            "bias_type": result.bias_type.value,
            "details": result.details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing LLM fairness: {str(e)}")

@router.post("/registry/model")
async def register_model(
    name: str = Form(...),
    version: str = Form(...),
    description: str = Form(...),
    intended_use: str = Form(...),
    created_by: str = Form(...),
    tags: str = Form("[]")
):
    """Register a new model in the registry"""
    try:
        from fairness_library.registry import ModelCard, ModelStatus
        
        # Parse tags
        tags_list = json.loads(tags) if tags else []
        
        # Create model card
        model_card = ModelCard(
            model_id="",
            name=name,
            version=version,
            description=description,
            intended_use=intended_use,
            training_data={},
            evaluation_data={},
            performance_metrics={},
            fairness_metrics={},
            known_limitations=[],
            bias_analysis={},
            risk_assessment="pending",
            deployment_notes="",
            created_by=created_by,
            created_at=None,
            updated_at=None,
            status=ModelStatus.DEVELOPMENT,
            tags=tags_list
        )
        
        # Register model
        model_id = registry_manager.model_registry.register_model(model_card)
        
        return {
            "model_id": model_id,
            "message": "Model registered successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering model: {str(e)}")

@router.post("/registry/dataset")
async def register_dataset(
    name: str = Form(...),
    version: str = Form(...),
    description: str = Form(...),
    collection_method: str = Form(...),
    created_by: str = Form(...),
    tags: str = Form("[]")
):
    """Register a new dataset in the registry"""
    try:
        from fairness_library.registry import DatasetDatasheet, DatasetStatus
        
        # Parse tags
        tags_list = json.loads(tags) if tags else []
        
        # Create dataset datasheet
        datasheet = DatasetDatasheet(
            dataset_id="",
            name=name,
            version=version,
            description=description,
            collection_method=collection_method,
            data_sources=[],
            data_processing={},
            data_quality={},
            potential_biases=[],
            representational_gaps=[],
            privacy_considerations=[],
            usage_restrictions=[],
            created_by=created_by,
            created_at=None,
            updated_at=None,
            status=DatasetStatus.ACTIVE,
            tags=tags_list
        )
        
        # Register dataset
        dataset_id = registry_manager.dataset_registry.register_dataset(datasheet)
        
        return {
            "dataset_id": dataset_id,
            "message": "Dataset registered successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering dataset: {str(e)}")

@router.post("/governance/compliance-check")
async def check_model_compliance(
    model_id: str,
    fairness_metrics: Dict[str, Any],
    bias_detection_results: Dict[str, Any] = {},
    performance_metrics: Dict[str, float] = {}
):
    """Check model compliance with governance policies"""
    try:
        compliance_result = governance_gate.check_model_compliance(
            model_id, fairness_metrics, bias_detection_results, performance_metrics
        )
        
        return compliance_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking compliance: {str(e)}")

@router.post("/governance/deployment-gate")
async def enforce_deployment_gate(
    model_id: str,
    deployment_stage: str,
    fairness_metrics: Dict[str, Any],
    bias_detection_results: Dict[str, Any] = {}
):
    """Enforce deployment gate for model deployment"""
    try:
        can_deploy = governance_gate.enforce_deployment_gate(
            model_id, deployment_stage, fairness_metrics, bias_detection_results
        )
        
        return {
            "model_id": model_id,
            "deployment_stage": deployment_stage,
            "can_deploy": can_deploy,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enforcing deployment gate: {str(e)}")

@router.post("/monitoring/metric")
async def add_monitoring_metric(
    metric_name: str,
    value: float,
    model_id: str,
    metadata: str = "{}"
):
    """Add a monitoring metric to the fairness monitor"""
    try:
        from fairness_library.monitoring import MonitoringMetric
        
        # Parse metadata
        metadata_dict = json.loads(metadata) if metadata else {}
        metadata_dict["model_id"] = model_id
        
        # Create monitoring metric
        metric = MonitoringMetric(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata_dict
        )
        
        # Add to monitor
        fairness_monitor.add_metric(metric)
        
        return {
            "message": "Metric added successfully",
            "metric_name": metric_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding monitoring metric: {str(e)}")

@router.post("/monitoring/bias-detection")
async def detect_bias_realtime(
    model_outputs: List[Dict[str, Any]],
    protected_attributes: List[str]
):
    """Detect bias in real-time model outputs"""
    try:
        bias_result = bias_detector.detect_bias(model_outputs, protected_attributes)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "bias_detection": bias_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting bias: {str(e)}")

@router.get("/monitoring/summary")
async def get_monitoring_summary(metric_name: Optional[str] = None):
    """Get monitoring metrics summary"""
    try:
        summary = fairness_monitor.get_metrics_summary(metric_name)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring summary: {str(e)}")

@router.get("/monitoring/alerts")
async def get_recent_alerts(hours: int = 24):
    """Get recent monitoring alerts"""
    try:
        alerts = fairness_monitor.get_recent_alerts(hours)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": [asdict(alert) for alert in alerts],
            "count": len(alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.get("/registry/models")
async def list_models(status: Optional[str] = None):
    """List all registered models"""
    try:
        from fairness_library.registry import ModelStatus
        
        status_enum = None
        if status:
            status_enum = ModelStatus(status)
        
        models = registry_manager.model_registry.list_models(status_enum)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "models": [asdict(model) for model in models],
            "count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@router.get("/registry/datasets")
async def list_datasets(status: Optional[str] = None):
    """List all registered datasets"""
    try:
        from fairness_library.registry import DatasetStatus
        
        status_enum = None
        if status:
            status_enum = DatasetStatus(status)
        
        datasets = registry_manager.dataset_registry.list_datasets(status_enum)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "datasets": [asdict(dataset) for dataset in datasets],
            "count": len(datasets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")

@router.get("/registry/model/{model_id}")
async def get_model_lineage(model_id: str):
    """Get complete model lineage including datasets and fairness reports"""
    try:
        lineage = registry_manager.get_model_lineage(model_id)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "lineage": lineage
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model lineage: {str(e)}")

@router.post("/policies/create")
async def create_policy(
    name: str,
    description: str,
    policy_type: str,
    metric_name: str,
    threshold: float,
    operator: str,
    severity: str
):
    """Create a new governance policy"""
    try:
        from fairness_library.governance import PolicyRule, PolicyType
        
        # Map policy type string to enum
        policy_type_map = {
            "fairness_threshold": PolicyType.FAIRNESS_THRESHOLD,
            "bias_detection": PolicyType.BIAS_DETECTION,
            "performance_degradation": PolicyType.PERFORMANCE_DEGRADATION,
            "data_quality": PolicyType.DATA_QUALITY,
            "compliance": PolicyType.COMPLIANCE
        }
        
        if policy_type not in policy_type_map:
            raise HTTPException(status_code=400, detail=f"Unknown policy type: {policy_type}")
        
        # Create policy rule
        policy_rule = PolicyRule(
            rule_id=f"policy_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            policy_type=policy_type_map[policy_type],
            metric_name=metric_name,
            threshold=threshold,
            operator=operator,
            severity=severity
        )
        
        # Create policy
        policy_id = governance_gate.policy_engine.create_policy(policy_rule)
        
        return {
            "policy_id": policy_id,
            "message": "Policy created successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating policy: {str(e)}")

@router.get("/policies")
async def list_policies():
    """List all governance policies"""
    try:
        policies = governance_gate.policy_engine.load_policies()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "policies": [asdict(policy) for policy in policies],
            "count": len(policies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing policies: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for fairness governance system"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "registry_manager": "active",
                "governance_gate": "active",
                "fairness_monitor": "active",
                "bias_detector": "active",
                "alert_manager": "active",
                "drift_detector": "active"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

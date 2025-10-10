"""
Lifecycle Integration Service
Integrates AI governance and compliance checks throughout the AI/ML lifecycle
"""

import json
import yaml
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import hashlib
import uuid

logger = logging.getLogger(__name__)

class LifecycleStage(Enum):
    DATA_INGESTION = "data_ingestion"
    DATA_PREPROCESSING = "data_preprocessing"
    MODEL_TRAINING = "model_training"
    MODEL_VALIDATION = "model_validation"
    MODEL_DEPLOYMENT = "model_deployment"
    MODEL_MONITORING = "model_monitoring"
    MODEL_RETRAINING = "model_retraining"
    MODEL_DECOMMISSION = "model_decommission"

class CheckType(Enum):
    BIAS_DETECTION = "bias_detection"
    PRIVACY_COMPLIANCE = "privacy_compliance"
    SECURITY_SCAN = "security_scan"
    EXPLAINABILITY = "explainability"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    REPRODUCIBILITY = "reproducibility"
    COMPLIANCE = "compliance"

class CheckStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class LifecycleCheck:
    """Represents a governance check in the lifecycle"""
    id: str
    name: str
    description: str
    stage: LifecycleStage
    check_type: CheckType
    required: bool
    timeout_seconds: int
    check_function: str  # Function name to call
    parameters: Dict[str, Any]
    dependencies: List[str]  # IDs of checks that must pass first
    metadata: Dict[str, Any]

@dataclass
class CheckResult:
    """Result of a lifecycle check"""
    check_id: str
    status: CheckStatus
    score: float
    message: str
    evidence: Dict[str, Any]
    recommendations: List[str]
    execution_time: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class LifecycleEvent:
    """Represents an event in the AI/ML lifecycle"""
    id: str
    system_id: str
    stage: LifecycleStage
    event_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class LifecycleContext:
    """Context information for lifecycle processing"""
    system_id: str
    project_id: str
    user_id: str
    stage: LifecycleStage
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime

class LifecycleIntegration:
    """Main lifecycle integration service"""
    
    def __init__(self, policy_engine=None, compliance_mapper=None):
        self.policy_engine = policy_engine
        self.compliance_mapper = compliance_mapper
        self.checks: Dict[str, LifecycleCheck] = {}
        self.check_results: Dict[str, List[CheckResult]] = {}
        self.lifecycle_events: List[LifecycleEvent] = []
        self.check_functions: Dict[str, Callable] = {}
        self._initialize_default_checks()
        self._register_check_functions()
    
    def _initialize_default_checks(self):
        """Initialize default lifecycle checks"""
        
        # Data Ingestion Checks
        self._add_check(LifecycleCheck(
            id="data_bias_detection",
            name="Data Bias Detection",
            description="Detect bias in training data",
            stage=LifecycleStage.DATA_INGESTION,
            check_type=CheckType.BIAS_DETECTION,
            required=True,
            timeout_seconds=300,
            check_function="check_data_bias",
            parameters={"threshold": 0.8, "protected_attributes": ["gender", "race", "age"]},
            dependencies=[],
            metadata={"priority": "high", "category": "fairness"}
        ))
        
        self._add_check(LifecycleCheck(
            id="data_privacy_compliance",
            name="Data Privacy Compliance",
            description="Check data privacy compliance",
            stage=LifecycleStage.DATA_INGESTION,
            check_type=CheckType.PRIVACY_COMPLIANCE,
            required=True,
            timeout_seconds=180,
            check_function="check_data_privacy",
            parameters={"gdpr_compliance": True, "ccpa_compliance": True},
            dependencies=[],
            metadata={"priority": "high", "category": "privacy"}
        ))
        
        self._add_check(LifecycleCheck(
            id="data_quality_assessment",
            name="Data Quality Assessment",
            description="Assess data quality and completeness",
            stage=LifecycleStage.DATA_INGESTION,
            check_type=CheckType.PERFORMANCE,
            required=True,
            timeout_seconds=120,
            check_function="check_data_quality",
            parameters={"min_completeness": 0.95, "max_duplicates": 0.05},
            dependencies=[],
            metadata={"priority": "medium", "category": "quality"}
        ))
        
        # Model Training Checks
        self._add_check(LifecycleCheck(
            id="training_bias_monitoring",
            name="Training Bias Monitoring",
            description="Monitor bias during model training",
            stage=LifecycleStage.MODEL_TRAINING,
            check_type=CheckType.BIAS_DETECTION,
            required=True,
            timeout_seconds=600,
            check_function="check_training_bias",
            parameters={"monitoring_frequency": "epoch", "bias_threshold": 0.1},
            dependencies=["data_bias_detection"],
            metadata={"priority": "high", "category": "fairness"}
        ))
        
        self._add_check(LifecycleCheck(
            id="training_reproducibility",
            name="Training Reproducibility",
            description="Ensure training is reproducible",
            stage=LifecycleStage.MODEL_TRAINING,
            check_type=CheckType.REPRODUCIBILITY,
            required=True,
            timeout_seconds=60,
            check_function="check_training_reproducibility",
            parameters={"seed_documentation": True, "environment_documentation": True},
            dependencies=[],
            metadata={"priority": "medium", "category": "reproducibility"}
        ))
        
        # Model Validation Checks
        self._add_check(LifecycleCheck(
            id="validation_bias_testing",
            name="Validation Bias Testing",
            description="Test for bias in model validation",
            stage=LifecycleStage.MODEL_VALIDATION,
            check_type=CheckType.BIAS_DETECTION,
            required=True,
            timeout_seconds=300,
            check_function="check_validation_bias",
            parameters={"test_sets": ["validation", "test"], "bias_metrics": ["demographic_parity", "equalized_odds"]},
            dependencies=["training_bias_monitoring"],
            metadata={"priority": "high", "category": "fairness"}
        ))
        
        self._add_check(LifecycleCheck(
            id="model_explainability",
            name="Model Explainability",
            description="Ensure model is explainable",
            stage=LifecycleStage.MODEL_VALIDATION,
            check_type=CheckType.EXPLAINABILITY,
            required=True,
            timeout_seconds=240,
            check_function="check_model_explainability",
            parameters={"explainability_methods": ["shap", "lime", "grad_cam"]},
            dependencies=[],
            metadata={"priority": "high", "category": "explainability"}
        ))
        
        # Model Deployment Checks
        self._add_check(LifecycleCheck(
            id="deployment_security_scan",
            name="Deployment Security Scan",
            description="Security scan before deployment",
            stage=LifecycleStage.MODEL_DEPLOYMENT,
            check_type=CheckType.SECURITY_SCAN,
            required=True,
            timeout_seconds=180,
            check_function="check_deployment_security",
            parameters={"scan_types": ["vulnerability", "malware", "configuration"]},
            dependencies=[],
            metadata={"priority": "high", "category": "security"}
        ))
        
        self._add_check(LifecycleCheck(
            id="deployment_documentation",
            name="Deployment Documentation",
            description="Ensure deployment documentation is complete",
            stage=LifecycleStage.MODEL_DEPLOYMENT,
            check_type=CheckType.DOCUMENTATION,
            required=True,
            timeout_seconds=60,
            check_function="check_deployment_documentation",
            parameters={"required_docs": ["deployment_guide", "api_docs", "monitoring_guide"]},
            dependencies=[],
            metadata={"priority": "medium", "category": "documentation"}
        ))
        
        # Model Monitoring Checks
        self._add_check(LifecycleCheck(
            id="runtime_bias_monitoring",
            name="Runtime Bias Monitoring",
            description="Monitor bias in production",
            stage=LifecycleStage.MODEL_MONITORING,
            check_type=CheckType.BIAS_DETECTION,
            required=True,
            timeout_seconds=120,
            check_function="check_runtime_bias",
            parameters={"monitoring_frequency": "hourly", "alert_threshold": 0.15},
            dependencies=[],
            metadata={"priority": "high", "category": "fairness"}
        ))
        
        self._add_check(LifecycleCheck(
            id="performance_monitoring",
            name="Performance Monitoring",
            description="Monitor model performance",
            stage=LifecycleStage.MODEL_MONITORING,
            check_type=CheckType.PERFORMANCE,
            required=True,
            timeout_seconds=90,
            check_function="check_performance_monitoring",
            parameters={"metrics": ["accuracy", "latency", "throughput"], "alert_threshold": 0.1},
            dependencies=[],
            metadata={"priority": "medium", "category": "performance"}
        ))
    
    def _add_check(self, check: LifecycleCheck):
        """Add a lifecycle check"""
        self.checks[check.id] = check
        if check.id not in self.check_results:
            self.check_results[check.id] = []
    
    def _register_check_functions(self):
        """Register all check functions"""
        self.check_functions = {
            "check_data_bias": self._check_data_bias,
            "check_data_privacy": self._check_data_privacy,
            "check_data_quality": self._check_data_quality,
            "check_training_bias": self._check_training_bias,
            "check_training_reproducibility": self._check_training_reproducibility,
            "check_validation_bias": self._check_validation_bias,
            "check_model_explainability": self._check_model_explainability,
            "check_deployment_security": self._check_deployment_security,
            "check_deployment_documentation": self._check_deployment_documentation,
            "check_runtime_bias": self._check_runtime_bias,
            "check_performance_monitoring": self._check_performance_monitoring
        }
    
    async def process_lifecycle_stage(self, context: LifecycleContext) -> Dict[str, Any]:
        """Process a lifecycle stage with all applicable checks"""
        stage = context.stage
        system_id = context.system_id
        
        logger.info(f"Processing lifecycle stage {stage.value} for system {system_id}")
        
        # Get checks for this stage
        stage_checks = [check for check in self.checks.values() if check.stage == stage]
        
        # Sort checks by dependencies
        sorted_checks = self._sort_checks_by_dependencies(stage_checks)
        
        # Execute checks
        results = {}
        all_passed = True
        
        for check in sorted_checks:
            try:
                result = await self._execute_check(check, context)
                results[check.id] = result
                
                if check.required and result.status == CheckStatus.FAILED:
                    all_passed = False
                    logger.warning(f"Required check {check.id} failed for system {system_id}")
                
                # Store result
                if check.id not in self.check_results:
                    self.check_results[check.id] = []
                self.check_results[check.id].append(result)
                
            except Exception as e:
                logger.error(f"Error executing check {check.id}: {e}")
                error_result = CheckResult(
                    check_id=check.id,
                    status=CheckStatus.FAILED,
                    score=0.0,
                    message=f"Check execution error: {str(e)}",
                    evidence={},
                    recommendations=["Fix check execution error"],
                    execution_time=0.0,
                    timestamp=datetime.now(),
                    metadata={"error": str(e)}
                )
                results[check.id] = error_result
                all_passed = False
        
        # Record lifecycle event
        event = LifecycleEvent(
            id=str(uuid.uuid4()),
            system_id=system_id,
            stage=stage,
            event_type="stage_completed",
            data={"results": {k: asdict(v) for k, v in results.items()}},
            metadata={"all_passed": all_passed, "total_checks": len(stage_checks)},
            timestamp=datetime.now()
        )
        self.lifecycle_events.append(event)
        
        return {
            "stage": stage.value,
            "system_id": system_id,
            "all_passed": all_passed,
            "results": results,
            "event_id": event.id
        }
    
    def _sort_checks_by_dependencies(self, checks: List[LifecycleCheck]) -> List[LifecycleCheck]:
        """Sort checks by their dependencies"""
        sorted_checks = []
        remaining_checks = checks.copy()
        
        while remaining_checks:
            # Find checks with no unmet dependencies
            ready_checks = []
            for check in remaining_checks:
                dependencies_met = all(
                    dep_id in [c.id for c in sorted_checks] 
                    for dep_id in check.dependencies
                )
                if dependencies_met:
                    ready_checks.append(check)
            
            if not ready_checks:
                # Circular dependency or missing dependency
                logger.warning("Circular dependency detected in checks")
                sorted_checks.extend(remaining_checks)
                break
            
            # Add ready checks to sorted list
            sorted_checks.extend(ready_checks)
            for check in ready_checks:
                remaining_checks.remove(check)
        
        return sorted_checks
    
    async def _execute_check(self, check: LifecycleCheck, context: LifecycleContext) -> CheckResult:
        """Execute a single check"""
        start_time = datetime.now()
        
        try:
            # Get check function
            if check.check_function not in self.check_functions:
                raise ValueError(f"Unknown check function: {check.check_function}")
            
            check_func = self.check_functions[check.check_function]
            
            # Execute check with timeout
            result_data = await asyncio.wait_for(
                check_func(context, check.parameters),
                timeout=check.timeout_seconds
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_id=check.id,
                status=CheckStatus.PASSED if result_data["passed"] else CheckStatus.FAILED,
                score=result_data.get("score", 1.0 if result_data["passed"] else 0.0),
                message=result_data.get("message", "Check completed"),
                evidence=result_data.get("evidence", {}),
                recommendations=result_data.get("recommendations", []),
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata=result_data.get("metadata", {})
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_id=check.id,
                status=CheckStatus.FAILED,
                score=0.0,
                message=f"Check timed out after {check.timeout_seconds} seconds",
                evidence={},
                recommendations=["Increase timeout or optimize check"],
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={"timeout": True}
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_id=check.id,
                status=CheckStatus.FAILED,
                score=0.0,
                message=f"Check failed: {str(e)}",
                evidence={},
                recommendations=["Fix check implementation"],
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
    
    # Check function implementations
    async def _check_data_bias(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check for bias in training data"""
        # Simulate bias detection
        threshold = parameters.get("threshold", 0.8)
        protected_attributes = parameters.get("protected_attributes", [])
        
        # Mock bias analysis
        bias_scores = {}
        for attr in protected_attributes:
            bias_scores[attr] = 0.75  # Simulated bias score
        
        max_bias = max(bias_scores.values()) if bias_scores else 0.0
        passed = max_bias <= threshold
        
        return {
            "passed": passed,
            "score": 1.0 - max_bias,
            "message": f"Data bias check {'passed' if passed else 'failed'} (max bias: {max_bias:.2f})",
            "evidence": {
                "bias_scores": bias_scores,
                "threshold": threshold,
                "protected_attributes": protected_attributes
            },
            "recommendations": ["Review data collection process"] if not passed else [],
            "metadata": {"check_type": "bias_detection"}
        }
    
    async def _check_data_privacy(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check data privacy compliance"""
        gdpr_compliance = parameters.get("gdpr_compliance", True)
        ccpa_compliance = parameters.get("ccpa_compliance", True)
        
        # Mock privacy compliance check
        privacy_checks = {
            "gdpr": gdpr_compliance,
            "ccpa": ccpa_compliance,
            "data_anonymization": True,
            "consent_management": True
        }
        
        passed = all(privacy_checks.values())
        score = sum(privacy_checks.values()) / len(privacy_checks)
        
        return {
            "passed": passed,
            "score": score,
            "message": f"Privacy compliance check {'passed' if passed else 'failed'}",
            "evidence": {
                "privacy_checks": privacy_checks,
                "compliance_frameworks": ["gdpr", "ccpa"]
            },
            "recommendations": ["Implement missing privacy controls"] if not passed else [],
            "metadata": {"check_type": "privacy_compliance"}
        }
    
    async def _check_data_quality(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check data quality"""
        min_completeness = parameters.get("min_completeness", 0.95)
        max_duplicates = parameters.get("max_duplicates", 0.05)
        
        # Mock data quality metrics
        quality_metrics = {
            "completeness": 0.97,
            "duplicates": 0.03,
            "consistency": 0.95,
            "validity": 0.98
        }
        
        passed = (quality_metrics["completeness"] >= min_completeness and 
                 quality_metrics["duplicates"] <= max_duplicates)
        
        score = sum(quality_metrics.values()) / len(quality_metrics)
        
        return {
            "passed": passed,
            "score": score,
            "message": f"Data quality check {'passed' if passed else 'failed'}",
            "evidence": {
                "quality_metrics": quality_metrics,
                "thresholds": {"min_completeness": min_completeness, "max_duplicates": max_duplicates}
            },
            "recommendations": ["Improve data quality"] if not passed else [],
            "metadata": {"check_type": "data_quality"}
        }
    
    async def _check_training_bias(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check bias during training"""
        monitoring_frequency = parameters.get("monitoring_frequency", "epoch")
        bias_threshold = parameters.get("bias_threshold", 0.1)
        
        # Mock training bias monitoring
        bias_metrics = {
            "demographic_parity": 0.08,
            "equalized_odds": 0.12,
            "calibration": 0.05
        }
        
        max_bias = max(bias_metrics.values())
        passed = max_bias <= bias_threshold
        
        return {
            "passed": passed,
            "score": 1.0 - max_bias,
            "message": f"Training bias check {'passed' if passed else 'failed'} (max bias: {max_bias:.2f})",
            "evidence": {
                "bias_metrics": bias_metrics,
                "monitoring_frequency": monitoring_frequency,
                "threshold": bias_threshold
            },
            "recommendations": ["Adjust training parameters"] if not passed else [],
            "metadata": {"check_type": "training_bias"}
        }
    
    async def _check_training_reproducibility(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check training reproducibility"""
        seed_documentation = parameters.get("seed_documentation", True)
        environment_documentation = parameters.get("environment_documentation", True)
        
        # Mock reproducibility checks
        reproducibility_checks = {
            "seed_documented": seed_documentation,
            "environment_documented": environment_documentation,
            "dependencies_locked": True,
            "version_control": True
        }
        
        passed = all(reproducibility_checks.values())
        score = sum(reproducibility_checks.values()) / len(reproducibility_checks)
        
        return {
            "passed": passed,
            "score": score,
            "message": f"Reproducibility check {'passed' if passed else 'failed'}",
            "evidence": {
                "reproducibility_checks": reproducibility_checks
            },
            "recommendations": ["Document missing reproducibility elements"] if not passed else [],
            "metadata": {"check_type": "reproducibility"}
        }
    
    async def _check_validation_bias(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check bias in validation"""
        test_sets = parameters.get("test_sets", ["validation", "test"])
        bias_metrics = parameters.get("bias_metrics", ["demographic_parity", "equalized_odds"])
        
        # Mock validation bias results
        validation_results = {}
        for test_set in test_sets:
            validation_results[test_set] = {
                "demographic_parity": 0.09,
                "equalized_odds": 0.11
            }
        
        # Check if any bias exceeds threshold
        max_bias = 0.0
        for test_set_results in validation_results.values():
            for metric in bias_metrics:
                if metric in test_set_results:
                    max_bias = max(max_bias, test_set_results[metric])
        
        passed = max_bias <= 0.1  # 10% threshold
        
        return {
            "passed": passed,
            "score": 1.0 - max_bias,
            "message": f"Validation bias check {'passed' if passed else 'failed'} (max bias: {max_bias:.2f})",
            "evidence": {
                "validation_results": validation_results,
                "test_sets": test_sets,
                "bias_metrics": bias_metrics
            },
            "recommendations": ["Retrain model with bias mitigation"] if not passed else [],
            "metadata": {"check_type": "validation_bias"}
        }
    
    async def _check_model_explainability(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check model explainability"""
        explainability_methods = parameters.get("explainability_methods", ["shap", "lime"])
        
        # Mock explainability assessment
        explainability_results = {}
        for method in explainability_methods:
            explainability_results[method] = {
                "available": True,
                "coverage": 0.95,
                "interpretability_score": 0.88
            }
        
        # Check if all methods are available and meet threshold
        all_available = all(result["available"] for result in explainability_results.values())
        avg_interpretability = sum(result["interpretability_score"] for result in explainability_results.values()) / len(explainability_results)
        
        passed = all_available and avg_interpretability >= 0.8
        
        return {
            "passed": passed,
            "score": avg_interpretability,
            "message": f"Explainability check {'passed' if passed else 'failed'} (avg score: {avg_interpretability:.2f})",
            "evidence": {
                "explainability_results": explainability_results,
                "methods": explainability_methods
            },
            "recommendations": ["Improve model explainability"] if not passed else [],
            "metadata": {"check_type": "explainability"}
        }
    
    async def _check_deployment_security(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check deployment security"""
        scan_types = parameters.get("scan_types", ["vulnerability", "malware"])
        
        # Mock security scan results
        security_results = {}
        for scan_type in scan_types:
            security_results[scan_type] = {
                "passed": True,
                "issues_found": 0,
                "severity": "low"
            }
        
        all_passed = all(result["passed"] for result in security_results.values())
        
        return {
            "passed": all_passed,
            "score": 1.0 if all_passed else 0.5,
            "message": f"Security scan {'passed' if all_passed else 'failed'}",
            "evidence": {
                "security_results": security_results,
                "scan_types": scan_types
            },
            "recommendations": ["Address security issues"] if not all_passed else [],
            "metadata": {"check_type": "security_scan"}
        }
    
    async def _check_deployment_documentation(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check deployment documentation"""
        required_docs = parameters.get("required_docs", ["deployment_guide", "api_docs"])
        
        # Mock documentation check
        doc_status = {}
        for doc in required_docs:
            doc_status[doc] = {
                "exists": True,
                "up_to_date": True,
                "completeness": 0.95
            }
        
        all_docs_present = all(status["exists"] for status in doc_status.values())
        avg_completeness = sum(status["completeness"] for status in doc_status.values()) / len(doc_status)
        
        passed = all_docs_present and avg_completeness >= 0.9
        
        return {
            "passed": passed,
            "score": avg_completeness,
            "message": f"Documentation check {'passed' if passed else 'failed'} (completeness: {avg_completeness:.2f})",
            "evidence": {
                "documentation_status": doc_status,
                "required_docs": required_docs
            },
            "recommendations": ["Complete missing documentation"] if not passed else [],
            "metadata": {"check_type": "documentation"}
        }
    
    async def _check_runtime_bias(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check runtime bias monitoring"""
        monitoring_frequency = parameters.get("monitoring_frequency", "hourly")
        alert_threshold = parameters.get("alert_threshold", 0.15)
        
        # Mock runtime bias monitoring
        runtime_bias = {
            "demographic_parity": 0.12,
            "equalized_odds": 0.14,
            "calibration": 0.08
        }
        
        max_bias = max(runtime_bias.values())
        passed = max_bias <= alert_threshold
        
        return {
            "passed": passed,
            "score": 1.0 - max_bias,
            "message": f"Runtime bias check {'passed' if passed else 'failed'} (max bias: {max_bias:.2f})",
            "evidence": {
                "runtime_bias": runtime_bias,
                "monitoring_frequency": monitoring_frequency,
                "alert_threshold": alert_threshold
            },
            "recommendations": ["Investigate bias drift"] if not passed else [],
            "metadata": {"check_type": "runtime_bias"}
        }
    
    async def _check_performance_monitoring(self, context: LifecycleContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check performance monitoring"""
        metrics = parameters.get("metrics", ["accuracy", "latency"])
        alert_threshold = parameters.get("alert_threshold", 0.1)
        
        # Mock performance monitoring
        performance_metrics = {
            "accuracy": 0.92,
            "latency": 0.05,  # 50ms
            "throughput": 1000  # requests per second
        }
        
        # Check if performance is within acceptable range
        baseline_accuracy = 0.95
        accuracy_drop = baseline_accuracy - performance_metrics["accuracy"]
        passed = accuracy_drop <= alert_threshold
        
        return {
            "passed": passed,
            "score": 1.0 - accuracy_drop,
            "message": f"Performance monitoring {'passed' if passed else 'failed'} (accuracy drop: {accuracy_drop:.2f})",
            "evidence": {
                "performance_metrics": performance_metrics,
                "baseline_accuracy": baseline_accuracy,
                "alert_threshold": alert_threshold
            },
            "recommendations": ["Investigate performance degradation"] if not passed else [],
            "metadata": {"check_type": "performance_monitoring"}
        }
    
    def get_lifecycle_summary(self, system_id: str) -> Dict[str, Any]:
        """Get lifecycle summary for a system"""
        system_events = [event for event in self.lifecycle_events if event.system_id == system_id]
        
        # Group events by stage
        stage_events = {}
        for event in system_events:
            stage = event.stage.value
            if stage not in stage_events:
                stage_events[stage] = []
            stage_events[stage].append(event)
        
        # Calculate stage completion status
        stage_status = {}
        for stage in LifecycleStage:
            stage_name = stage.value
            events = stage_events.get(stage_name, [])
            
            if events:
                latest_event = max(events, key=lambda e: e.timestamp)
                stage_status[stage_name] = {
                    "status": "completed",
                    "last_event": latest_event.timestamp.isoformat(),
                    "event_count": len(events)
                }
            else:
                stage_status[stage_name] = {
                    "status": "not_started",
                    "last_event": None,
                    "event_count": 0
                }
        
        return {
            "system_id": system_id,
            "stage_status": stage_status,
            "total_events": len(system_events),
            "last_activity": max(event.timestamp for event in system_events).isoformat() if system_events else None
        }
    
    def get_check_results(self, system_id: str, check_id: str = None) -> Dict[str, Any]:
        """Get check results for a system"""
        if check_id:
            # Get specific check results
            results = self.check_results.get(check_id, [])
            system_results = [r for r in results if r.metadata.get("system_id") == system_id]
            return {
                "check_id": check_id,
                "system_id": system_id,
                "results": [asdict(r) for r in system_results]
            }
        else:
            # Get all check results for system
            all_results = {}
            for cid, results in self.check_results.items():
                system_results = [r for r in results if r.metadata.get("system_id") == system_id]
                if system_results:
                    all_results[cid] = [asdict(r) for r in system_results]
            
            return {
                "system_id": system_id,
                "check_results": all_results
            }
    
    def add_custom_check(self, check: LifecycleCheck, check_function: Callable):
        """Add a custom lifecycle check"""
        self.checks[check.id] = check
        self.check_functions[check.check_function] = check_function
        
        if check.id not in self.check_results:
            self.check_results[check.id] = []
    
    def get_available_checks(self, stage: LifecycleStage = None) -> List[LifecycleCheck]:
        """Get available checks, optionally filtered by stage"""
        if stage:
            return [check for check in self.checks.values() if check.stage == stage]
        return list(self.checks.values())


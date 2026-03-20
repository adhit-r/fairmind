"""
Comprehensive Bias Evaluation Pipeline
Implements the multi-layered approach outlined in the 2025 analysis
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class EvaluationPhase(Enum):
    """Evaluation phases in the comprehensive pipeline"""
    PRE_DEPLOYMENT = "pre_deployment"
    REAL_TIME_MONITORING = "real_time_monitoring"
    POST_DEPLOYMENT_AUDITING = "post_deployment_auditing"
    HUMAN_IN_LOOP = "human_in_loop"
    CONTINUOUS_LEARNING = "continuous_learning"

class BiasRiskLevel(Enum):
    """Bias risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EvaluationResult:
    """Result from a single evaluation phase"""
    phase: EvaluationPhase
    timestamp: str
    success: bool
    bias_detected: bool
    risk_level: BiasRiskLevel
    metrics: Dict[str, Any]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    details: Dict[str, Any]

@dataclass
class ComprehensiveEvaluationReport:
    """Comprehensive evaluation report"""
    evaluation_id: str
    model_id: str
    model_type: str
    start_time: str
    end_time: str
    phases_completed: List[EvaluationPhase]
    overall_risk: BiasRiskLevel
    bias_summary: Dict[str, Any]
    recommendations: List[str]
    compliance_status: Dict[str, Any]
    next_evaluation_due: str
    results: Dict[str, EvaluationResult]

class ComprehensiveBiasEvaluationPipeline:
    """
    Comprehensive bias evaluation pipeline implementing the 2025 analysis approach
    """
    
    def __init__(self):
        self.evaluation_configs = self._initialize_evaluation_configs()
        self.monitoring_thresholds = self._initialize_monitoring_thresholds()
        self.compliance_frameworks = self._initialize_compliance_frameworks()
        self.evaluation_history = []
        
    def _initialize_evaluation_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize evaluation configurations for each phase"""
        return {
            "pre_deployment": {
                "enabled": True,
                "required_tests": [
                    "stereoset", "crowspairs", "bbq", "weat", "seat", 
                    "minimal_pairs", "red_teaming"
                ],
                "sample_size_min": 1000,
                "confidence_level": 0.95,
                "bias_threshold": 0.1,
                "timeout_minutes": 30
            },
            "real_time_monitoring": {
                "enabled": True,
                "monitoring_interval_minutes": 5,
                "alert_thresholds": {
                    "bias_spike": 0.2,
                    "drift_detection": 0.15,
                    "performance_degradation": 0.1
                },
                "retention_days": 30
            },
            "post_deployment_auditing": {
                "enabled": True,
                "audit_frequency_days": 7,
                "audit_depth": "comprehensive",
                "human_review_required": True,
                "compliance_check": True
            },
            "human_in_loop": {
                "enabled": True,
                "expert_review_required": True,
                "crowd_evaluation_size": 50,
                "inter_rater_reliability_threshold": 0.8,
                "review_timeout_hours": 24
            },
            "continuous_learning": {
                "enabled": True,
                "learning_rate": 0.01,
                "adaptation_threshold": 0.05,
                "model_update_frequency_days": 14
            }
        }
    
    def _initialize_monitoring_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize monitoring thresholds for different bias types"""
        return {
            "demographic_parity": {
                "low": 0.05,
                "medium": 0.1,
                "high": 0.2,
                "critical": 0.3
            },
            "equalized_odds": {
                "low": 0.05,
                "medium": 0.1,
                "high": 0.15,
                "critical": 0.25
            },
            "calibration": {
                "low": 0.03,
                "medium": 0.06,
                "high": 0.1,
                "critical": 0.15
            },
            "representational_bias": {
                "low": 0.1,
                "medium": 0.2,
                "high": 0.3,
                "critical": 0.4
            }
        }
    
    def _initialize_compliance_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance framework configurations"""
        return {
            "EU_AI_ACT": {
                "enabled": True,
                "requirements": [
                    "transparency",
                    "human_oversight",
                    "technical_robustness",
                    "privacy_and_data_governance",
                    "diversity_non_discrimination",
                    "societal_environmental_wellbeing",
                    "accountability"
                ],
                "bias_thresholds": {
                    "high_risk": 0.1,
                    "limited_risk": 0.15,
                    "minimal_risk": 0.2
                }
            },
            "FTC_GUIDELINES": {
                "enabled": True,
                "requirements": [
                    "transparency",
                    "explainability",
                    "fairness",
                    "accountability"
                ],
                "bias_thresholds": {
                    "unfair": 0.15,
                    "deceptive": 0.2
                }
            },
            "GDPR": {
                "enabled": True,
                "requirements": [
                    "lawfulness_fairness_transparency",
                    "purpose_limitation",
                    "data_minimization",
                    "accuracy",
                    "storage_limitation",
                    "integrity_confidentiality",
                    "accountability"
                ],
                "bias_thresholds": {
                    "privacy_risk": 0.1
                }
            }
        }

    async def run_comprehensive_evaluation(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> ComprehensiveEvaluationReport:
        """
        Run comprehensive bias evaluation pipeline
        
        Implements the multi-layered approach:
        1. Pre-deployment comprehensive testing
        2. Real-time monitoring simulation
        3. Post-deployment auditing
        4. Human-in-the-loop evaluation
        5. Continuous learning adaptation
        """
        try:
            evaluation_id = f"eval_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()
            
            logger.info(f"Starting comprehensive evaluation {evaluation_id} for model {model_id}")
            
            # Merge with default configuration
            config = {**self.evaluation_configs, **(evaluation_config or {})}
            
            results = {}
            phases_completed = []
            
            # Phase 1: Pre-deployment comprehensive testing
            if config.get("pre_deployment", {}).get("enabled", True):
                logger.info("Running pre-deployment comprehensive testing...")
                pre_deployment_result = await self._run_pre_deployment_evaluation(
                    model_id, model_type, model_outputs, config["pre_deployment"]
                )
                results["pre_deployment"] = pre_deployment_result
                phases_completed.append(EvaluationPhase.PRE_DEPLOYMENT)
            
            # Phase 2: Real-time monitoring simulation
            if config.get("real_time_monitoring", {}).get("enabled", True):
                logger.info("Running real-time monitoring simulation...")
                real_time_result = await self._run_real_time_monitoring(
                    model_id, model_type, model_outputs, config["real_time_monitoring"]
                )
                results["real_time_monitoring"] = real_time_result
                phases_completed.append(EvaluationPhase.REAL_TIME_MONITORING)
            
            # Phase 3: Post-deployment auditing
            if config.get("post_deployment_auditing", {}).get("enabled", True):
                logger.info("Running post-deployment auditing...")
                post_deployment_result = await self._run_post_deployment_auditing(
                    model_id, model_type, model_outputs, config["post_deployment_auditing"]
                )
                results["post_deployment_auditing"] = post_deployment_result
                phases_completed.append(EvaluationPhase.POST_DEPLOYMENT_AUDITING)
            
            # Phase 4: Human-in-the-loop evaluation
            if config.get("human_in_loop", {}).get("enabled", True):
                logger.info("Running human-in-the-loop evaluation...")
                human_evaluation_result = await self._run_human_in_loop_evaluation(
                    model_id, model_type, model_outputs, config["human_in_loop"]
                )
                results["human_in_loop"] = human_evaluation_result
                phases_completed.append(EvaluationPhase.HUMAN_IN_LOOP)
            
            # Phase 5: Continuous learning adaptation
            if config.get("continuous_learning", {}).get("enabled", True):
                logger.info("Running continuous learning adaptation...")
                continuous_learning_result = await self._run_continuous_learning(
                    model_id, model_type, model_outputs, config["continuous_learning"]
                )
                results["continuous_learning"] = continuous_learning_result
                phases_completed.append(EvaluationPhase.CONTINUOUS_LEARNING)
            
            # Generate comprehensive report
            end_time = datetime.now()
            report = await self._generate_comprehensive_report(
                evaluation_id, model_id, model_type, start_time, end_time,
                phases_completed, results
            )
            
            # Store evaluation history
            self.evaluation_history.append(report)
            
            logger.info(f"Comprehensive evaluation {evaluation_id} completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            raise

    async def _run_pre_deployment_evaluation(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> EvaluationResult:
        """Run pre-deployment comprehensive testing"""
        try:
            start_time = datetime.now()
            
            # Run required bias tests
            test_results = {}
            bias_detected = False
            max_bias_score = 0.0
            
            for test_name in config["required_tests"]:
                test_result = await self._run_bias_test(test_name, model_outputs)
                test_results[test_name] = test_result
                
                if test_result["is_biased"]:
                    bias_detected = True
                    max_bias_score = max(max_bias_score, test_result["bias_score"])
            
            # Determine risk level
            risk_level = self._determine_risk_level(max_bias_score, "pre_deployment")
            
            # Generate recommendations
            recommendations = self._generate_pre_deployment_recommendations(test_results, risk_level)
            
            # Generate alerts
            alerts = self._generate_pre_deployment_alerts(test_results, risk_level)
            
            return EvaluationResult(
                phase=EvaluationPhase.PRE_DEPLOYMENT,
                timestamp=start_time.isoformat(),
                success=True,
                bias_detected=bias_detected,
                risk_level=risk_level,
                metrics={
                    "tests_run": len(config["required_tests"]),
                    "bias_tests_passed": sum(1 for r in test_results.values() if not r["is_biased"]),
                    "max_bias_score": max_bias_score,
                    "test_results": test_results
                },
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "sample_size": len(model_outputs),
                    "confidence_level": config["confidence_level"],
                    "bias_threshold": config["bias_threshold"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in pre-deployment evaluation: {e}")
            return EvaluationResult(
                phase=EvaluationPhase.PRE_DEPLOYMENT,
                timestamp=datetime.now().isoformat(),
                success=False,
                bias_detected=False,
                risk_level=BiasRiskLevel.CRITICAL,
                metrics={},
                recommendations=["Fix pre-deployment evaluation errors"],
                alerts=[{"type": "error", "message": str(e)}],
                details={"error": str(e)}
            )

    async def _run_real_time_monitoring(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> EvaluationResult:
        """Run real-time monitoring simulation"""
        try:
            start_time = datetime.now()
            
            # Simulate real-time monitoring metrics
            monitoring_metrics = {
                "bias_trend": np.random.uniform(0, 0.2, 24).tolist(),  # 24 hours
                "drift_score": np.random.uniform(0, 0.3),
                "performance_metrics": {
                    "accuracy": np.random.uniform(0.8, 0.95),
                    "precision": np.random.uniform(0.75, 0.9),
                    "recall": np.random.uniform(0.7, 0.85)
                },
                "demographic_analysis": {
                    "group_a": {"bias_score": np.random.uniform(0, 0.15)},
                    "group_b": {"bias_score": np.random.uniform(0, 0.2)},
                    "group_c": {"bias_score": np.random.uniform(0, 0.1)}
                }
            }
            
            # Check for alerts
            alerts = []
            bias_detected = False
            max_bias = 0.0
            
            # Check bias spike
            if monitoring_metrics["bias_trend"][-1] > config["alert_thresholds"]["bias_spike"]:
                alerts.append({
                    "type": "bias_spike",
                    "severity": "high",
                    "message": f"Bias spike detected: {monitoring_metrics['bias_trend'][-1]:.3f}"
                })
                bias_detected = True
                max_bias = monitoring_metrics["bias_trend"][-1]
            
            # Check drift
            if monitoring_metrics["drift_score"] > config["alert_thresholds"]["drift_detection"]:
                alerts.append({
                    "type": "drift_detection",
                    "severity": "medium",
                    "message": f"Data drift detected: {monitoring_metrics['drift_score']:.3f}"
                })
            
            # Check performance degradation
            if monitoring_metrics["performance_metrics"]["accuracy"] < (1 - config["alert_thresholds"]["performance_degradation"]):
                alerts.append({
                    "type": "performance_degradation",
                    "severity": "medium",
                    "message": f"Performance degradation detected: {monitoring_metrics['performance_metrics']['accuracy']:.3f}"
                })
            
            # Determine risk level
            risk_level = self._determine_risk_level(max_bias, "real_time")
            
            # Generate recommendations
            recommendations = self._generate_monitoring_recommendations(monitoring_metrics, alerts)
            
            return EvaluationResult(
                phase=EvaluationPhase.REAL_TIME_MONITORING,
                timestamp=start_time.isoformat(),
                success=True,
                bias_detected=bias_detected,
                risk_level=risk_level,
                metrics=monitoring_metrics,
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "monitoring_interval": config["monitoring_interval_minutes"],
                    "retention_days": config["retention_days"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in real-time monitoring: {e}")
            return EvaluationResult(
                phase=EvaluationPhase.REAL_TIME_MONITORING,
                timestamp=datetime.now().isoformat(),
                success=False,
                bias_detected=False,
                risk_level=BiasRiskLevel.CRITICAL,
                metrics={},
                recommendations=["Fix real-time monitoring errors"],
                alerts=[{"type": "error", "message": str(e)}],
                details={"error": str(e)}
            )

    async def _run_post_deployment_auditing(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> EvaluationResult:
        """Run post-deployment auditing"""
        try:
            start_time = datetime.now()
            
            # Simulate audit findings
            audit_findings = {
                "bias_incidents": np.random.randint(0, 5),
                "fairness_violations": np.random.randint(0, 3),
                "compliance_issues": [],
                "user_complaints": np.random.randint(0, 10),
                "performance_issues": np.random.randint(0, 2)
            }
            
            # Check compliance if required
            compliance_status = {}
            if config.get("compliance_check", True):
                for framework, framework_config in self.compliance_frameworks.items():
                    if framework_config["enabled"]:
                        compliance_status[framework] = {
                            "compliant": np.random.choice([True, False], p=[0.8, 0.2]),
                            "score": np.random.uniform(0.7, 0.95),
                            "issues": [] if np.random.random() > 0.3 else ["Documentation gap", "Monitoring frequency"]
                        }
            
            # Determine if bias was detected
            bias_detected = audit_findings["bias_incidents"] > 0 or audit_findings["fairness_violations"] > 0
            
            # Calculate risk level
            risk_score = (
                audit_findings["bias_incidents"] * 0.3 +
                audit_findings["fairness_violations"] * 0.4 +
                audit_findings["user_complaints"] * 0.1 +
                audit_findings["performance_issues"] * 0.2
            )
            risk_level = self._determine_risk_level(risk_score, "post_deployment")
            
            # Generate recommendations
            recommendations = self._generate_audit_recommendations(audit_findings, compliance_status)
            
            # Generate alerts
            alerts = []
            if audit_findings["bias_incidents"] > 0:
                alerts.append({
                    "type": "bias_incident",
                    "severity": "high",
                    "message": f"{audit_findings['bias_incidents']} bias incidents detected"
                })
            
            if audit_findings["fairness_violations"] > 0:
                alerts.append({
                    "type": "fairness_violation",
                    "severity": "critical",
                    "message": f"{audit_findings['fairness_violations']} fairness violations detected"
                })
            
            return EvaluationResult(
                phase=EvaluationPhase.POST_DEPLOYMENT_AUDITING,
                timestamp=start_time.isoformat(),
                success=True,
                bias_detected=bias_detected,
                risk_level=risk_level,
                metrics={
                    "audit_findings": audit_findings,
                    "compliance_status": compliance_status,
                    "audit_depth": config["audit_depth"]
                },
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "audit_frequency_days": config["audit_frequency_days"],
                    "human_review_required": config["human_review_required"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in post-deployment auditing: {e}")
            return EvaluationResult(
                phase=EvaluationPhase.POST_DEPLOYMENT_AUDITING,
                timestamp=datetime.now().isoformat(),
                success=False,
                bias_detected=False,
                risk_level=BiasRiskLevel.CRITICAL,
                metrics={},
                recommendations=["Fix post-deployment auditing errors"],
                alerts=[{"type": "error", "message": str(e)}],
                details={"error": str(e)}
            )

    async def _run_human_in_loop_evaluation(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> EvaluationResult:
        """Run human-in-the-loop evaluation"""
        try:
            start_time = datetime.now()
            
            # Simulate expert review
            expert_review = {
                "expert_id": f"expert_{np.random.randint(1000, 9999)}",
                "bias_detected": np.random.choice([True, False], p=[0.2, 0.8]),
                "severity": np.random.choice(["low", "medium", "high"], p=[0.6, 0.3, 0.1]),
                "confidence": np.random.uniform(0.7, 0.95),
                "notes": "Model shows acceptable bias levels with minor concerns about demographic representation"
            }
            
            # Simulate crowd evaluation
            crowd_evaluation = {
                "participants": config["crowd_evaluation_size"],
                "bias_rating": np.random.uniform(1.5, 4.5),  # 1-5 scale
                "fairness_rating": np.random.uniform(3.0, 4.8),
                "inter_rater_reliability": np.random.uniform(0.75, 0.95),
                "consensus": np.random.choice(["strong", "moderate", "weak"], p=[0.4, 0.4, 0.2])
            }
            
            # Determine bias detection
            bias_detected = expert_review["bias_detected"] or crowd_evaluation["bias_rating"] < 2.5
            
            # Calculate risk level
            risk_score = 0.0
            if expert_review["bias_detected"]:
                risk_score += 0.4
            if crowd_evaluation["bias_rating"] < 3.0:
                risk_score += 0.3
            if crowd_evaluation["inter_rater_reliability"] < config["inter_rater_reliability_threshold"]:
                risk_score += 0.3
            
            risk_level = self._determine_risk_level(risk_score, "human_evaluation")
            
            # Generate recommendations
            recommendations = self._generate_human_evaluation_recommendations(expert_review, crowd_evaluation)
            
            # Generate alerts
            alerts = []
            if expert_review["bias_detected"] and expert_review["severity"] in ["high", "critical"]:
                alerts.append({
                    "type": "expert_bias_detection",
                    "severity": expert_review["severity"],
                    "message": f"Expert detected {expert_review['severity']} bias"
                })
            
            if crowd_evaluation["inter_rater_reliability"] < config["inter_rater_reliability_threshold"]:
                alerts.append({
                    "type": "low_reliability",
                    "severity": "medium",
                    "message": f"Low inter-rater reliability: {crowd_evaluation['inter_rater_reliability']:.3f}"
                })
            
            return EvaluationResult(
                phase=EvaluationPhase.HUMAN_IN_LOOP,
                timestamp=start_time.isoformat(),
                success=True,
                bias_detected=bias_detected,
                risk_level=risk_level,
                metrics={
                    "expert_review": expert_review,
                    "crowd_evaluation": crowd_evaluation
                },
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "expert_review_required": config["expert_review_required"],
                    "review_timeout_hours": config["review_timeout_hours"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in human-in-the-loop evaluation: {e}")
            return EvaluationResult(
                phase=EvaluationPhase.HUMAN_IN_LOOP,
                timestamp=datetime.now().isoformat(),
                success=False,
                bias_detected=False,
                risk_level=BiasRiskLevel.CRITICAL,
                metrics={},
                recommendations=["Fix human-in-the-loop evaluation errors"],
                alerts=[{"type": "error", "message": str(e)}],
                details={"error": str(e)}
            )

    async def _run_continuous_learning(
        self,
        model_id: str,
        model_type: str,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> EvaluationResult:
        """Run continuous learning adaptation"""
        try:
            start_time = datetime.now()
            
            # Simulate continuous learning metrics
            learning_metrics = {
                "adaptation_triggered": np.random.choice([True, False], p=[0.3, 0.7]),
                "bias_reduction": np.random.uniform(0, 0.15),
                "performance_improvement": np.random.uniform(0, 0.1),
                "learning_rate": config["learning_rate"],
                "adaptation_threshold": config["adaptation_threshold"],
                "model_updates": np.random.randint(0, 5)
            }
            
            # Determine if adaptation is needed
            adaptation_needed = learning_metrics["adaptation_triggered"]
            bias_detected = learning_metrics["bias_reduction"] > 0
            
            # Calculate risk level
            risk_score = 0.0
            if adaptation_needed:
                risk_score += 0.3
            if learning_metrics["bias_reduction"] > config["adaptation_threshold"]:
                risk_score += 0.4
            if learning_metrics["model_updates"] > 3:
                risk_score += 0.3
            
            risk_level = self._determine_risk_level(risk_score, "continuous_learning")
            
            # Generate recommendations
            recommendations = self._generate_continuous_learning_recommendations(learning_metrics, adaptation_needed)
            
            # Generate alerts
            alerts = []
            if adaptation_needed:
                alerts.append({
                    "type": "adaptation_triggered",
                    "severity": "medium",
                    "message": "Model adaptation triggered due to bias changes"
                })
            
            if learning_metrics["model_updates"] > 3:
                alerts.append({
                    "type": "frequent_updates",
                    "severity": "low",
                    "message": f"Model updated {learning_metrics['model_updates']} times recently"
                })
            
            return EvaluationResult(
                phase=EvaluationPhase.CONTINUOUS_LEARNING,
                timestamp=start_time.isoformat(),
                success=True,
                bias_detected=bias_detected,
                risk_level=risk_level,
                metrics=learning_metrics,
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "learning_rate": config["learning_rate"],
                    "update_frequency_days": config["model_update_frequency_days"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in continuous learning: {e}")
            return EvaluationResult(
                phase=EvaluationPhase.CONTINUOUS_LEARNING,
                timestamp=datetime.now().isoformat(),
                success=False,
                bias_detected=False,
                risk_level=BiasRiskLevel.CRITICAL,
                metrics={},
                recommendations=["Fix continuous learning errors"],
                alerts=[{"type": "error", "message": str(e)}],
                details={"error": str(e)}
            )

    async def _run_bias_test(self, test_name: str, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run individual bias test (placeholder implementation)"""
        # This would integrate with the actual bias detection services
        bias_score = np.random.uniform(0, 0.3)
        is_biased = bias_score > 0.1
        
        return {
            "test_name": test_name,
            "bias_score": bias_score,
            "is_biased": is_biased,
            "confidence": np.random.uniform(0.8, 0.95),
            "details": {
                "sample_size": len(model_outputs),
                "test_type": "simulated"
            }
        }

    def _determine_risk_level(self, score: float, context: str) -> BiasRiskLevel:
        """Determine risk level based on score and context"""
        if context == "pre_deployment":
            if score < 0.1:
                return BiasRiskLevel.LOW
            elif score < 0.2:
                return BiasRiskLevel.MEDIUM
            elif score < 0.3:
                return BiasRiskLevel.HIGH
            else:
                return BiasRiskLevel.CRITICAL
        elif context == "real_time":
            if score < 0.15:
                return BiasRiskLevel.LOW
            elif score < 0.25:
                return BiasRiskLevel.MEDIUM
            elif score < 0.35:
                return BiasRiskLevel.HIGH
            else:
                return BiasRiskLevel.CRITICAL
        else:
            if score < 0.2:
                return BiasRiskLevel.LOW
            elif score < 0.4:
                return BiasRiskLevel.MEDIUM
            elif score < 0.6:
                return BiasRiskLevel.HIGH
            else:
                return BiasRiskLevel.CRITICAL

    def _generate_pre_deployment_recommendations(
        self, 
        test_results: Dict[str, Any], 
        risk_level: BiasRiskLevel
    ) -> List[str]:
        """Generate pre-deployment recommendations"""
        recommendations = []
        
        if risk_level in [BiasRiskLevel.HIGH, BiasRiskLevel.CRITICAL]:
            recommendations.extend([
                "Do not deploy model in current state",
                "Implement additional bias mitigation techniques",
                "Consider retraining with more diverse data",
                "Implement post-processing bias correction"
            ])
        elif risk_level == BiasRiskLevel.MEDIUM:
            recommendations.extend([
                "Deploy with enhanced monitoring",
                "Implement bias detection alerts",
                "Schedule regular bias audits",
                "Consider bias mitigation post-processing"
            ])
        else:
            recommendations.extend([
                "Model ready for deployment",
                "Implement standard monitoring",
                "Schedule regular bias evaluations"
            ])
        
        return recommendations

    def _generate_monitoring_recommendations(
        self, 
        metrics: Dict[str, Any], 
        alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = []
        
        if any(alert["type"] == "bias_spike" for alert in alerts):
            recommendations.extend([
                "Investigate bias spike immediately",
                "Check for data drift or model degradation",
                "Consider temporary model rollback"
            ])
        
        if any(alert["type"] == "drift_detection" for alert in alerts):
            recommendations.extend([
                "Monitor data quality closely",
                "Consider model retraining",
                "Update monitoring thresholds"
            ])
        
        if any(alert["type"] == "performance_degradation" for alert in alerts):
            recommendations.extend([
                "Investigate performance issues",
                "Check for bias-performance trade-offs",
                "Consider model optimization"
            ])
        
        return recommendations

    def _generate_audit_recommendations(
        self, 
        findings: Dict[str, Any], 
        compliance: Dict[str, Any]
    ) -> List[str]:
        """Generate audit recommendations"""
        recommendations = []
        
        if findings["bias_incidents"] > 0:
            recommendations.extend([
                "Investigate all bias incidents",
                "Implement incident response procedures",
                "Enhance bias detection monitoring"
            ])
        
        if findings["fairness_violations"] > 0:
            recommendations.extend([
                "Address fairness violations immediately",
                "Review model training process",
                "Implement fairness constraints"
            ])
        
        for framework, status in compliance.items():
            if not status["compliant"]:
                recommendations.append(f"Address {framework} compliance issues")
        
        return recommendations

    def _generate_human_evaluation_recommendations(
        self, 
        expert_review: Dict[str, Any], 
        crowd_evaluation: Dict[str, Any]
    ) -> List[str]:
        """Generate human evaluation recommendations"""
        recommendations = []
        
        if expert_review["bias_detected"]:
            recommendations.extend([
                "Address expert-identified bias issues",
                "Implement expert recommendations",
                "Schedule follow-up expert review"
            ])
        
        if crowd_evaluation["bias_rating"] < 3.0:
            recommendations.extend([
                "Improve user experience based on feedback",
                "Address crowd-identified bias concerns",
                "Implement user feedback mechanisms"
            ])
        
        if crowd_evaluation["inter_rater_reliability"] < 0.8:
            recommendations.extend([
                "Improve evaluation criteria clarity",
                "Provide better training for evaluators",
                "Increase evaluation sample size"
            ])
        
        return recommendations

    def _generate_continuous_learning_recommendations(
        self, 
        metrics: Dict[str, Any], 
        adaptation_needed: bool
    ) -> List[str]:
        """Generate continuous learning recommendations"""
        recommendations = []
        
        if adaptation_needed:
            recommendations.extend([
                "Implement model adaptation",
                "Monitor adaptation effectiveness",
                "Update learning parameters"
            ])
        
        if metrics["bias_reduction"] > 0.1:
            recommendations.extend([
                "Continue current learning approach",
                "Monitor for over-adaptation",
                "Document learning progress"
            ])
        
        return recommendations

    def _generate_pre_deployment_alerts(
        self, 
        test_results: Dict[str, Any], 
        risk_level: BiasRiskLevel
    ) -> List[Dict[str, Any]]:
        """Generate pre-deployment alerts"""
        alerts = []
        
        if risk_level in [BiasRiskLevel.HIGH, BiasRiskLevel.CRITICAL]:
            alerts.append({
                "type": "deployment_blocked",
                "severity": "critical",
                "message": f"Deployment blocked due to {risk_level.value} bias risk"
            })
        
        for test_name, result in test_results.items():
            if result["is_biased"] and result["bias_score"] > 0.2:
                alerts.append({
                    "type": "high_bias_test",
                    "severity": "high",
                    "message": f"High bias detected in {test_name}: {result['bias_score']:.3f}"
                })
        
        return alerts

    async def _generate_comprehensive_report(
        self,
        evaluation_id: str,
        model_id: str,
        model_type: str,
        start_time: datetime,
        end_time: datetime,
        phases_completed: List[EvaluationPhase],
        results: Dict[str, EvaluationResult]
    ) -> ComprehensiveEvaluationReport:
        """Generate comprehensive evaluation report"""
        
        # Calculate overall risk
        risk_scores = []
        bias_detected_phases = []
        
        for phase, result in results.items():
            if result.success:
                risk_scores.append(self._risk_score_to_numeric(result.risk_level))
                if result.bias_detected:
                    bias_detected_phases.append(phase)
        
        overall_risk_score = np.mean(risk_scores) if risk_scores else 0.0
        overall_risk = self._numeric_to_risk_level(overall_risk_score)
        
        # Generate bias summary
        bias_summary = {
            "phases_with_bias": bias_detected_phases,
            "overall_bias_detected": len(bias_detected_phases) > 0,
            "risk_distribution": {
                phase: result.risk_level.value for phase, result in results.items()
            },
            "total_alerts": sum(len(result.alerts) for result in results.values())
        }
        
        # Generate comprehensive recommendations
        all_recommendations = []
        for result in results.values():
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        prioritized_recommendations = self._prioritize_recommendations(unique_recommendations, overall_risk)
        
        # Generate compliance status
        compliance_status = {}
        for result in results.values():
            if "compliance_status" in result.metrics:
                compliance_status.update(result.metrics["compliance_status"])
        
        # Calculate next evaluation due date
        next_evaluation_due = (datetime.now() + timedelta(days=7)).isoformat()
        
        return ComprehensiveEvaluationReport(
            evaluation_id=evaluation_id,
            model_id=model_id,
            model_type=model_type,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            phases_completed=phases_completed,
            overall_risk=overall_risk,
            bias_summary=bias_summary,
            recommendations=prioritized_recommendations,
            compliance_status=compliance_status,
            next_evaluation_due=next_evaluation_due,
            results={phase.value: result for phase, result in results.items()}
        )

    def _risk_score_to_numeric(self, risk_level: BiasRiskLevel) -> float:
        """Convert risk level to numeric score"""
        mapping = {
            BiasRiskLevel.LOW: 0.25,
            BiasRiskLevel.MEDIUM: 0.5,
            BiasRiskLevel.HIGH: 0.75,
            BiasRiskLevel.CRITICAL: 1.0
        }
        return mapping.get(risk_level, 0.5)

    def _numeric_to_risk_level(self, score: float) -> BiasRiskLevel:
        """Convert numeric score to risk level"""
        if score < 0.3:
            return BiasRiskLevel.LOW
        elif score < 0.6:
            return BiasRiskLevel.MEDIUM
        elif score < 0.8:
            return BiasRiskLevel.HIGH
        else:
            return BiasRiskLevel.CRITICAL

    def _prioritize_recommendations(
        self, 
        recommendations: List[str], 
        overall_risk: BiasRiskLevel
    ) -> List[str]:
        """Prioritize recommendations based on risk level"""
        # Simple prioritization - in practice, this would be more sophisticated
        critical_keywords = ["immediately", "critical", "blocked", "violation"]
        high_keywords = ["investigate", "enhance", "implement", "address"]
        
        critical_recs = [r for r in recommendations if any(kw in r.lower() for kw in critical_keywords)]
        high_recs = [r for r in recommendations if any(kw in r.lower() for kw in high_keywords)]
        other_recs = [r for r in recommendations if r not in critical_recs + high_recs]
        
        return critical_recs + high_recs + other_recs

    def get_evaluation_history(self, limit: int = 10) -> List[ComprehensiveEvaluationReport]:
        """Get evaluation history"""
        return self.evaluation_history[-limit:] if self.evaluation_history else []

    def get_evaluation_by_id(self, evaluation_id: str) -> Optional[ComprehensiveEvaluationReport]:
        """Get specific evaluation by ID"""
        for report in self.evaluation_history:
            if report.evaluation_id == evaluation_id:
                return report
        return None

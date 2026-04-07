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
from scipy import stats as scipy_stats
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
        """Run real-time monitoring using actual model output data"""
        try:
            start_time = datetime.now()

            # Extract scores and group labels from model_outputs for real computation
            scores = np.array([
                o.get("score", o.get("prediction", 0.0)) for o in model_outputs
            ], dtype=float)
            labels = np.array([
                o.get("label", o.get("ground_truth", 0)) for o in model_outputs
            ], dtype=float)
            groups = [o.get("group", o.get("demographic_group", "unknown")) for o in model_outputs]

            # Compute rolling bias trend from sequential chunks of data
            # Split data into 24 equal time-windows (simulating 24-hour monitoring)
            n = len(scores)
            num_windows = min(24, max(1, n))
            chunk_size = max(1, n // num_windows)
            bias_trend = []
            for i in range(num_windows):
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, n)
                chunk_scores = scores[start_idx:end_idx]
                if len(chunk_scores) > 1:
                    # Bias proxy: deviation of chunk mean from overall mean
                    overall_mean = float(np.mean(scores)) if len(scores) > 0 else 0.0
                    chunk_mean = float(np.mean(chunk_scores))
                    bias_trend.append(abs(chunk_mean - overall_mean))
                else:
                    bias_trend.append(0.0)

            # Compute drift score using Population Stability Index (PSI)
            drift_score = self._calculate_psi(scores, num_windows)

            # Compute real performance metrics from labels vs scores
            predictions_binary = (scores >= 0.5).astype(int) if len(scores) > 0 else np.array([])
            labels_binary = labels.astype(int) if len(labels) > 0 else np.array([])
            accuracy, precision, recall = self._compute_classification_metrics(
                labels_binary, predictions_binary
            )

            # Compute per-group bias scores from actual data
            unique_groups = sorted(set(groups))
            demographic_analysis = {}
            overall_positive_rate = float(np.mean(predictions_binary)) if len(predictions_binary) > 0 else 0.0
            for grp in unique_groups:
                grp_mask = np.array([g == grp for g in groups])
                grp_preds = predictions_binary[grp_mask] if len(predictions_binary) > 0 else np.array([])
                if len(grp_preds) > 0:
                    grp_positive_rate = float(np.mean(grp_preds))
                    group_bias = abs(grp_positive_rate - overall_positive_rate)
                else:
                    group_bias = 0.0
                demographic_analysis[grp] = {"bias_score": group_bias}

            monitoring_metrics = {
                "bias_trend": bias_trend,
                "drift_score": drift_score,
                "performance_metrics": {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall
                },
                "demographic_analysis": demographic_analysis
            }

            # Check for alerts using real computed values
            alerts = []
            bias_detected = False
            max_bias = max(bias_trend) if bias_trend else 0.0

            # Check bias spike (last window value)
            latest_bias = bias_trend[-1] if bias_trend else 0.0
            if latest_bias > config["alert_thresholds"]["bias_spike"]:
                alerts.append({
                    "type": "bias_spike",
                    "severity": "high",
                    "message": f"Bias spike detected: {latest_bias:.3f}"
                })
                bias_detected = True
                max_bias = latest_bias

            # Check drift
            if drift_score > config["alert_thresholds"]["drift_detection"]:
                alerts.append({
                    "type": "drift_detection",
                    "severity": "medium",
                    "message": f"Data drift detected: {drift_score:.3f}"
                })

            # Check performance degradation
            if accuracy < (1 - config["alert_thresholds"]["performance_degradation"]):
                alerts.append({
                    "type": "performance_degradation",
                    "severity": "medium",
                    "message": f"Performance degradation detected: {accuracy:.3f}"
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
        """Run post-deployment auditing using real data aggregation"""
        try:
            start_time = datetime.now()

            # Extract data arrays
            scores = np.array([
                o.get("score", o.get("prediction", 0.0)) for o in model_outputs
            ], dtype=float)
            labels = np.array([
                o.get("label", o.get("ground_truth", 0)) for o in model_outputs
            ], dtype=float)
            groups = [o.get("group", o.get("demographic_group", "unknown")) for o in model_outputs]
            predictions_binary = (scores >= 0.5).astype(int) if len(scores) > 0 else np.array([])
            labels_binary = labels.astype(int) if len(labels) > 0 else np.array([])

            # Count real bias incidents: cases where per-group positive rate
            # differs from overall by more than the demographic_parity high threshold
            unique_groups = sorted(set(groups))
            overall_positive_rate = float(np.mean(predictions_binary)) if len(predictions_binary) > 0 else 0.0
            dp_threshold = self.monitoring_thresholds["demographic_parity"]["high"]
            eq_threshold = self.monitoring_thresholds["equalized_odds"]["high"]

            bias_incidents = 0
            fairness_violations = 0
            group_details = {}

            for grp in unique_groups:
                grp_mask = np.array([g == grp for g in groups])
                grp_preds = predictions_binary[grp_mask]
                grp_labels = labels_binary[grp_mask]

                if len(grp_preds) == 0:
                    continue

                grp_positive_rate = float(np.mean(grp_preds))
                dp_diff = abs(grp_positive_rate - overall_positive_rate)

                # Equalized odds: difference in TPR
                tpr_overall = self._true_positive_rate(labels_binary, predictions_binary)
                tpr_group = self._true_positive_rate(grp_labels, grp_preds)
                eq_diff = abs(tpr_group - tpr_overall)

                if dp_diff > dp_threshold:
                    bias_incidents += 1
                if eq_diff > eq_threshold:
                    fairness_violations += 1

                group_details[grp] = {
                    "count": int(grp_mask.sum()),
                    "positive_rate": grp_positive_rate,
                    "demographic_parity_diff": dp_diff,
                    "equalized_odds_diff": eq_diff,
                }

            # Compute performance issues: groups where accuracy is notably lower
            performance_issues = 0
            overall_accuracy = float(np.mean(predictions_binary == labels_binary)) if len(labels_binary) > 0 else 0.0
            for grp in unique_groups:
                grp_mask = np.array([g == grp for g in groups])
                grp_preds = predictions_binary[grp_mask]
                grp_labels = labels_binary[grp_mask]
                if len(grp_labels) > 0:
                    grp_accuracy = float(np.mean(grp_preds == grp_labels))
                    if (overall_accuracy - grp_accuracy) > self.monitoring_thresholds["calibration"]["high"]:
                        performance_issues += 1

            # Trend analysis via linear regression on sequential bias measurements
            n = len(scores)
            num_windows = min(10, max(1, n))
            chunk_size = max(1, n // num_windows)
            window_biases = []
            for i in range(num_windows):
                s = i * chunk_size
                e = min(s + chunk_size, n)
                chunk = scores[s:e]
                if len(chunk) > 0:
                    window_biases.append(abs(float(np.mean(chunk)) - float(np.mean(scores))))
                else:
                    window_biases.append(0.0)

            trend_slope, trend_intercept = 0.0, 0.0
            if len(window_biases) >= 2:
                x = np.arange(len(window_biases), dtype=float)
                y = np.array(window_biases, dtype=float)
                slope, intercept, _, _, _ = scipy_stats.linregress(x, y)
                trend_slope = float(slope)
                trend_intercept = float(intercept)

            # User complaints proxy: count outputs flagged by user or with low confidence
            user_complaints = sum(
                1 for o in model_outputs
                if o.get("flagged", False) or o.get("user_complaint", False)
            )

            audit_findings = {
                "bias_incidents": bias_incidents,
                "fairness_violations": fairness_violations,
                "compliance_issues": [],
                "user_complaints": user_complaints,
                "performance_issues": performance_issues,
                "group_details": group_details,
                "trend_analysis": {
                    "slope": trend_slope,
                    "intercept": trend_intercept,
                    "direction": "increasing" if trend_slope > 0.001 else ("decreasing" if trend_slope < -0.001 else "stable"),
                    "window_values": window_biases,
                }
            }

            # Check compliance using real bias metrics
            compliance_status = {}
            if config.get("compliance_check", True):
                max_dp_diff = max(
                    (d["demographic_parity_diff"] for d in group_details.values()),
                    default=0.0
                )
                for framework, framework_config in self.compliance_frameworks.items():
                    if framework_config["enabled"]:
                        thresholds = framework_config["bias_thresholds"]
                        # Compliant if max bias diff is below the strictest threshold
                        strictest = min(thresholds.values())
                        is_compliant = max_dp_diff <= strictest
                        compliance_score = max(0.0, 1.0 - (max_dp_diff / strictest)) if strictest > 0 else 0.0
                        issues = []
                        if not is_compliant:
                            issues.append(
                                f"Demographic parity difference {max_dp_diff:.3f} exceeds threshold {strictest:.3f}"
                            )
                        if trend_slope > 0.001:
                            issues.append("Bias trend is increasing over time")
                        compliance_status[framework] = {
                            "compliant": is_compliant,
                            "score": min(1.0, compliance_score),
                            "issues": issues
                        }

            # Determine if bias was detected
            bias_detected = audit_findings["bias_incidents"] > 0 or audit_findings["fairness_violations"] > 0

            # Calculate risk level from real counts
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
        """Run human-in-the-loop evaluation using actual threshold-based flagging"""
        try:
            start_time = datetime.now()

            # Extract data
            scores = np.array([
                o.get("score", o.get("prediction", 0.0)) for o in model_outputs
            ], dtype=float)
            labels = np.array([
                o.get("label", o.get("ground_truth", 0)) for o in model_outputs
            ], dtype=float)
            groups = [o.get("group", o.get("demographic_group", "unknown")) for o in model_outputs]
            predictions_binary = (scores >= 0.5).astype(int) if len(scores) > 0 else np.array([])
            labels_binary = labels.astype(int) if len(labels) > 0 else np.array([])

            # Compute per-group fairness metrics to identify flagged cases
            unique_groups = sorted(set(groups))
            overall_positive_rate = float(np.mean(predictions_binary)) if len(predictions_binary) > 0 else 0.0
            flagged_groups = []
            group_bias_scores = {}

            for grp in unique_groups:
                grp_mask = np.array([g == grp for g in groups])
                grp_preds = predictions_binary[grp_mask]
                if len(grp_preds) > 0:
                    grp_rate = float(np.mean(grp_preds))
                    dp_diff = abs(grp_rate - overall_positive_rate)
                    group_bias_scores[grp] = dp_diff
                    # Flag groups exceeding medium threshold
                    if dp_diff > self.monitoring_thresholds["demographic_parity"]["medium"]:
                        flagged_groups.append(grp)
                else:
                    group_bias_scores[grp] = 0.0

            # Identify individual cases that need expert review:
            # cases where the model disagrees with the label or where confidence is extreme
            flagged_cases = []
            for i, output in enumerate(model_outputs):
                score = scores[i] if i < len(scores) else 0.0
                label = labels[i] if i < len(labels) else 0
                pred = 1 if score >= 0.5 else 0
                confidence = abs(score - 0.5) * 2  # 0 = uncertain, 1 = certain
                reasons = []
                if pred != int(label):
                    reasons.append("prediction_disagrees_with_label")
                if confidence < 0.2:
                    reasons.append("low_confidence")
                if output.get("group", output.get("demographic_group", "unknown")) in flagged_groups:
                    reasons.append("flagged_demographic_group")
                if reasons:
                    flagged_cases.append({
                        "index": i,
                        "score": float(score),
                        "label": float(label),
                        "group": groups[i] if i < len(groups) else "unknown",
                        "reasons": reasons
                    })

            # Structure expert review from data analysis
            bias_detected_by_data = len(flagged_groups) > 0
            max_group_bias = max(group_bias_scores.values()) if group_bias_scores else 0.0
            severity = "low"
            if max_group_bias > self.monitoring_thresholds["demographic_parity"]["high"]:
                severity = "high"
            elif max_group_bias > self.monitoring_thresholds["demographic_parity"]["medium"]:
                severity = "medium"

            expert_review = {
                "bias_detected": bias_detected_by_data,
                "severity": severity,
                "confidence": 1.0 - (1.0 / (1.0 + len(model_outputs))),  # confidence scales with data size
                "flagged_groups": flagged_groups,
                "group_bias_scores": group_bias_scores,
                "flagged_cases_count": len(flagged_cases),
                "notes": (
                    f"Analysis of {len(model_outputs)} outputs identified "
                    f"{len(flagged_groups)} groups with elevated bias and "
                    f"{len(flagged_cases)} individual cases requiring review."
                )
            }

            # Compute crowd evaluation proxy from agreement analysis
            # Use inter-annotator agreement if ratings are present, otherwise from label consistency
            ratings = [o.get("bias_rating", None) for o in model_outputs if o.get("bias_rating") is not None]
            if len(ratings) >= 2:
                ratings_arr = np.array(ratings, dtype=float)
                bias_rating = float(np.mean(ratings_arr))
                fairness_ratings = [
                    o.get("fairness_rating", None) for o in model_outputs
                    if o.get("fairness_rating") is not None
                ]
                fairness_rating = float(np.mean(fairness_ratings)) if fairness_ratings else bias_rating
                # Inter-rater reliability via coefficient of variation (lower CV = higher agreement)
                cv = float(np.std(ratings_arr) / np.mean(ratings_arr)) if np.mean(ratings_arr) > 0 else 1.0
                inter_rater_reliability = max(0.0, min(1.0, 1.0 - cv))
            else:
                # No crowd ratings available; use prediction-label agreement as proxy
                if len(predictions_binary) > 0 and len(labels_binary) > 0:
                    agreement_rate = float(np.mean(predictions_binary == labels_binary))
                    bias_rating = agreement_rate * 5.0  # Scale to 1-5
                    fairness_rating = agreement_rate * 5.0
                    inter_rater_reliability = agreement_rate
                else:
                    bias_rating = 0.0
                    fairness_rating = 0.0
                    inter_rater_reliability = 0.0

            consensus = "strong" if inter_rater_reliability >= 0.8 else ("moderate" if inter_rater_reliability >= 0.6 else "weak")

            crowd_evaluation = {
                "participants": len(ratings) if ratings else len(model_outputs),
                "bias_rating": bias_rating,
                "fairness_rating": fairness_rating,
                "inter_rater_reliability": inter_rater_reliability,
                "consensus": consensus
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
                    "crowd_evaluation": crowd_evaluation,
                    "flagged_cases_sample": flagged_cases[:20],  # first 20 for review
                },
                recommendations=recommendations,
                alerts=alerts,
                details={
                    "expert_review_required": config["expert_review_required"],
                    "review_timeout_hours": config["review_timeout_hours"],
                    "total_flagged_cases": len(flagged_cases),
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
        """Run continuous learning adaptation using metric deltas between evaluation periods"""
        try:
            start_time = datetime.now()

            # Compute current metrics from the provided data
            scores = np.array([
                o.get("score", o.get("prediction", 0.0)) for o in model_outputs
            ], dtype=float)
            labels = np.array([
                o.get("label", o.get("ground_truth", 0)) for o in model_outputs
            ], dtype=float)
            groups = [o.get("group", o.get("demographic_group", "unknown")) for o in model_outputs]
            predictions_binary = (scores >= 0.5).astype(int) if len(scores) > 0 else np.array([])
            labels_binary = labels.astype(int) if len(labels) > 0 else np.array([])

            # Current bias metric: statistical parity difference
            current_spd = self._compute_statistical_parity_difference(predictions_binary, groups)
            current_accuracy = float(np.mean(predictions_binary == labels_binary)) if len(labels_binary) > 0 else 0.0

            # Compare with previous evaluation if available
            previous_spd = 0.0
            previous_accuracy = 0.0
            model_updates = 0
            if self.evaluation_history:
                last_report = self.evaluation_history[-1]
                # Try to extract previous metrics from the last pre_deployment or monitoring result
                for phase_key in ["pre_deployment", "real_time_monitoring"]:
                    prev_result = last_report.results.get(phase_key)
                    if prev_result and prev_result.success:
                        prev_metrics = prev_result.metrics
                        if "max_bias_score" in prev_metrics:
                            previous_spd = prev_metrics["max_bias_score"]
                        if "performance_metrics" in prev_metrics:
                            previous_accuracy = prev_metrics["performance_metrics"].get("accuracy", 0.0)
                        break
                model_updates = len(self.evaluation_history)

            bias_reduction = max(0.0, previous_spd - current_spd)
            performance_improvement = max(0.0, current_accuracy - previous_accuracy)
            bias_delta = current_spd - previous_spd  # positive = worsening

            # Determine if adaptation is needed based on real threshold comparison
            adaptation_needed = abs(bias_delta) > config["adaptation_threshold"]

            learning_metrics = {
                "adaptation_triggered": adaptation_needed,
                "bias_reduction": bias_reduction,
                "bias_delta": bias_delta,
                "current_spd": current_spd,
                "previous_spd": previous_spd,
                "performance_improvement": performance_improvement,
                "current_accuracy": current_accuracy,
                "previous_accuracy": previous_accuracy,
                "learning_rate": config["learning_rate"],
                "adaptation_threshold": config["adaptation_threshold"],
                "model_updates": model_updates,
                "direction": "improving" if bias_delta < 0 else ("degrading" if bias_delta > 0 else "stable"),
            }

            # Determine if bias is present in current data
            bias_detected = current_spd > config["adaptation_threshold"]

            # Calculate risk level from real deltas
            risk_score = 0.0
            if adaptation_needed:
                risk_score += 0.3
            if bias_delta > config["adaptation_threshold"]:
                # Bias is getting worse
                risk_score += 0.4
            if model_updates > 3:
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
                    "message": f"Model adaptation triggered: bias delta {bias_delta:.4f} exceeds threshold {config['adaptation_threshold']}"
                })

            if model_updates > 3:
                alerts.append({
                    "type": "frequent_updates",
                    "severity": "low",
                    "message": f"Model evaluated {model_updates} times recently"
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
        """
        Run individual bias test computing real fairness metrics from model_outputs.

        Each output dict is expected to contain:
          - score/prediction (float): model output score
          - label/ground_truth (int/float): true label
          - group/demographic_group (str): protected attribute group
        """
        if not model_outputs:
            return {
                "test_name": test_name,
                "bias_score": 0.0,
                "is_biased": False,
                "confidence": 0.0,
                "details": {
                    "sample_size": 0,
                    "test_type": test_name,
                    "note": "No data provided"
                }
            }

        scores = np.array([
            o.get("score", o.get("prediction", 0.0)) for o in model_outputs
        ], dtype=float)
        labels = np.array([
            o.get("label", o.get("ground_truth", 0)) for o in model_outputs
        ], dtype=float)
        groups = [o.get("group", o.get("demographic_group", "unknown")) for o in model_outputs]
        predictions_binary = (scores >= 0.5).astype(int)
        labels_binary = labels.astype(int)

        unique_groups = sorted(set(groups))

        # Route to specific metric computation based on test name
        if test_name in ("stereoset", "weat", "seat"):
            # Association-based tests: compute effect size between group score distributions
            bias_score, confidence, extra = self._compute_association_bias(scores, groups, unique_groups)
        elif test_name in ("crowspairs", "minimal_pairs"):
            # Paired comparison tests: statistical parity difference
            bias_score = self._compute_statistical_parity_difference(predictions_binary, groups)
            confidence = self._compute_confidence(predictions_binary, groups)
            extra = {"metric": "statistical_parity_difference"}
        elif test_name == "bbq":
            # Equalized odds difference
            bias_score, confidence, extra = self._compute_equalized_odds_difference(
                labels_binary, predictions_binary, groups, unique_groups
            )
        elif test_name == "red_teaming":
            # Disparate impact ratio deviation from 1.0
            bias_score, confidence, extra = self._compute_disparate_impact(
                predictions_binary, groups, unique_groups
            )
        else:
            # Default: statistical parity difference
            bias_score = self._compute_statistical_parity_difference(predictions_binary, groups)
            confidence = self._compute_confidence(predictions_binary, groups)
            extra = {"metric": "statistical_parity_difference"}

        is_biased = bias_score > 0.1

        return {
            "test_name": test_name,
            "bias_score": float(bias_score),
            "is_biased": is_biased,
            "confidence": float(confidence),
            "details": {
                "sample_size": len(model_outputs),
                "test_type": test_name,
                "groups_analyzed": unique_groups,
                **extra
            }
        }

    # ---- Helper methods for real statistical computations ----

    @staticmethod
    def _true_positive_rate(labels: np.ndarray, predictions: np.ndarray) -> float:
        """Compute true positive rate (recall) from binary arrays."""
        if len(labels) == 0:
            return 0.0
        positives = labels == 1
        if positives.sum() == 0:
            return 0.0
        return float(np.mean(predictions[positives] == 1))

    @staticmethod
    def _false_positive_rate(labels: np.ndarray, predictions: np.ndarray) -> float:
        """Compute false positive rate from binary arrays."""
        if len(labels) == 0:
            return 0.0
        negatives = labels == 0
        if negatives.sum() == 0:
            return 0.0
        return float(np.mean(predictions[negatives] == 1))

    @staticmethod
    def _compute_classification_metrics(
        labels: np.ndarray, predictions: np.ndarray
    ) -> Tuple[float, float, float]:
        """Compute accuracy, precision, recall from binary arrays."""
        if len(labels) == 0 or len(predictions) == 0:
            return 0.0, 0.0, 0.0
        accuracy = float(np.mean(labels == predictions))
        tp = int(np.sum((predictions == 1) & (labels == 1)))
        fp = int(np.sum((predictions == 1) & (labels == 0)))
        fn = int(np.sum((predictions == 0) & (labels == 1)))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        return accuracy, precision, recall

    @staticmethod
    def _compute_statistical_parity_difference(
        predictions: np.ndarray, groups: List[str]
    ) -> float:
        """
        Statistical parity difference: max absolute difference in positive
        prediction rates across groups.
        """
        if len(predictions) == 0:
            return 0.0
        unique_groups = sorted(set(groups))
        if len(unique_groups) < 2:
            return 0.0
        rates = []
        for grp in unique_groups:
            mask = np.array([g == grp for g in groups])
            grp_preds = predictions[mask]
            if len(grp_preds) > 0:
                rates.append(float(np.mean(grp_preds)))
        if len(rates) < 2:
            return 0.0
        return float(max(rates) - min(rates))

    @staticmethod
    def _compute_confidence(predictions: np.ndarray, groups: List[str]) -> float:
        """
        Confidence based on sample size per group.
        Uses the smallest group size relative to a minimum useful size (30).
        """
        unique_groups = sorted(set(groups))
        if not unique_groups:
            return 0.0
        min_group_size = min(
            sum(1 for g in groups if g == grp) for grp in unique_groups
        )
        # Confidence scales with sample size, saturating around 100 samples
        return float(min(1.0, min_group_size / 100.0))

    def _compute_association_bias(
        self,
        scores: np.ndarray,
        groups: List[str],
        unique_groups: List[str],
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Association-based bias: compute effect size (Cohen's d) between
        the two most different group score distributions.
        """
        if len(unique_groups) < 2 or len(scores) == 0:
            return 0.0, 0.0, {"metric": "cohens_d", "note": "insufficient groups"}

        group_stats = {}
        for grp in unique_groups:
            mask = np.array([g == grp for g in groups])
            grp_scores = scores[mask]
            if len(grp_scores) > 0:
                group_stats[grp] = {
                    "mean": float(np.mean(grp_scores)),
                    "std": float(np.std(grp_scores, ddof=1)) if len(grp_scores) > 1 else 0.0,
                    "n": int(len(grp_scores)),
                }

        if len(group_stats) < 2:
            return 0.0, 0.0, {"metric": "cohens_d", "note": "insufficient data per group"}

        # Find max Cohen's d across all pairs
        max_d = 0.0
        grp_names = list(group_stats.keys())
        for i in range(len(grp_names)):
            for j in range(i + 1, len(grp_names)):
                g1 = group_stats[grp_names[i]]
                g2 = group_stats[grp_names[j]]
                pooled_std = np.sqrt(
                    ((g1["n"] - 1) * g1["std"] ** 2 + (g2["n"] - 1) * g2["std"] ** 2)
                    / max(1, g1["n"] + g2["n"] - 2)
                )
                if pooled_std > 0:
                    d = abs(g1["mean"] - g2["mean"]) / pooled_std
                else:
                    d = 0.0 if g1["mean"] == g2["mean"] else 1.0
                max_d = max(max_d, d)

        min_n = min(gs["n"] for gs in group_stats.values())
        confidence = float(min(1.0, min_n / 100.0))

        return float(max_d), confidence, {"metric": "cohens_d", "group_stats": group_stats}

    def _compute_equalized_odds_difference(
        self,
        labels: np.ndarray,
        predictions: np.ndarray,
        groups: List[str],
        unique_groups: List[str],
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Equalized odds difference: max difference in TPR or FPR across groups.
        """
        if len(unique_groups) < 2 or len(labels) == 0:
            return 0.0, 0.0, {"metric": "equalized_odds_difference", "note": "insufficient groups"}

        tprs = {}
        fprs = {}
        for grp in unique_groups:
            mask = np.array([g == grp for g in groups])
            grp_labels = labels[mask]
            grp_preds = predictions[mask]
            tprs[grp] = self._true_positive_rate(grp_labels, grp_preds)
            fprs[grp] = self._false_positive_rate(grp_labels, grp_preds)

        tpr_vals = list(tprs.values())
        fpr_vals = list(fprs.values())
        tpr_diff = max(tpr_vals) - min(tpr_vals) if len(tpr_vals) >= 2 else 0.0
        fpr_diff = max(fpr_vals) - min(fpr_vals) if len(fpr_vals) >= 2 else 0.0
        eq_odds_diff = max(tpr_diff, fpr_diff)

        confidence = self._compute_confidence(predictions, groups)
        return float(eq_odds_diff), confidence, {
            "metric": "equalized_odds_difference",
            "tpr_by_group": tprs,
            "fpr_by_group": fprs,
        }

    def _compute_disparate_impact(
        self,
        predictions: np.ndarray,
        groups: List[str],
        unique_groups: List[str],
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Disparate impact: deviation of the min(rate_a/rate_b, rate_b/rate_a) from 1.0.
        A ratio of 1.0 means no disparate impact; the four-fifths rule uses 0.8 as threshold.
        Returns bias_score as 1.0 - ratio (so 0 is no bias, approaching 1 is full bias).
        """
        if len(unique_groups) < 2 or len(predictions) == 0:
            return 0.0, 0.0, {"metric": "disparate_impact_ratio", "note": "insufficient groups"}

        rates = {}
        for grp in unique_groups:
            mask = np.array([g == grp for g in groups])
            grp_preds = predictions[mask]
            if len(grp_preds) > 0:
                rates[grp] = float(np.mean(grp_preds))

        if len(rates) < 2:
            return 0.0, 0.0, {"metric": "disparate_impact_ratio", "note": "insufficient data"}

        min_ratio = 1.0
        rate_vals = list(rates.values())
        for i in range(len(rate_vals)):
            for j in range(i + 1, len(rate_vals)):
                r1, r2 = rate_vals[i], rate_vals[j]
                if r1 > 0 and r2 > 0:
                    ratio = min(r1 / r2, r2 / r1)
                    min_ratio = min(min_ratio, ratio)
                elif r1 == 0 and r2 == 0:
                    pass  # both zero, no disparity
                else:
                    min_ratio = 0.0  # one group has zero rate

        bias_score = 1.0 - min_ratio
        confidence = self._compute_confidence(predictions, groups)
        return float(bias_score), confidence, {
            "metric": "disparate_impact_ratio",
            "rates_by_group": rates,
            "min_ratio": float(min_ratio),
        }

    @staticmethod
    def _calculate_psi(scores: np.ndarray, num_windows: int) -> float:
        """
        Population Stability Index (PSI) between the first half and second half
        of the score distribution, using histogram binning.
        """
        if len(scores) < 4:
            return 0.0
        mid = len(scores) // 2
        expected = scores[:mid]
        actual = scores[mid:]

        # Use 10 equal-width bins spanning the full range
        min_val = float(np.min(scores))
        max_val = float(np.max(scores))
        if max_val == min_val:
            return 0.0
        bins = np.linspace(min_val, max_val, 11)

        expected_counts, _ = np.histogram(expected, bins=bins)
        actual_counts, _ = np.histogram(actual, bins=bins)

        # Convert to proportions with small epsilon to avoid division by zero
        eps = 1e-6
        expected_prop = (expected_counts + eps) / (len(expected) + eps * len(expected_counts))
        actual_prop = (actual_counts + eps) / (len(actual) + eps * len(actual_counts))

        psi = float(np.sum((actual_prop - expected_prop) * np.log(actual_prop / expected_prop)))
        return max(0.0, psi)

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

        overall_risk_score = float(np.mean(risk_scores)) if risk_scores else 0.0
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

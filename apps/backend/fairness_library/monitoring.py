"""
Real-time Production Monitoring
Continuously monitors model performance and fairness metrics in production.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import numpy as np
from threading import Lock

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class MonitoringMetric:
    """Individual monitoring metric"""
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """Alert for fairness drift or bias detection"""
    alert_id: str
    alert_type: str
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    model_id: str
    details: Dict[str, Any]

class FairnessMonitor:
    """Real-time fairness monitoring system"""
    
    def __init__(self, window_size: int = 1000, alert_threshold: float = 0.05):
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=window_size))
        self.alerts = []
        self.alert_callbacks = []
        self.lock = Lock()
        
        # Initialize monitoring for different metric types
        self.fairness_metrics = {}
        self.bias_metrics = {}
        self.performance_metrics = {}
    
    def add_metric(self, metric: MonitoringMetric) -> None:
        """Add a new metric to the monitoring system"""
        try:
            with self.lock:
                # Add to appropriate buffer
                if "fairness" in metric.metric_name.lower():
                    self.fairness_metrics[metric.metric_name] = metric
                    self.metrics_buffer[metric.metric_name].append(metric)
                elif "bias" in metric.metric_name.lower():
                    self.bias_metrics[metric.metric_name] = metric
                    self.metrics_buffer[metric.metric_name].append(metric)
                else:
                    self.performance_metrics[metric.metric_name] = metric
                    self.metrics_buffer[metric.metric_name].append(metric)
                
                # Check for drift
                self._check_drift(metric)
                
        except Exception as e:
            logger.error(f"Error adding metric: {e}")
    
    def _check_drift(self, metric: MonitoringMetric) -> None:
        """Check for fairness drift in the metric"""
        try:
            if len(self.metrics_buffer[metric.metric_name]) < 10:
                return  # Need minimum data points
            
            # Calculate baseline (first 20% of data)
            baseline_size = min(20, len(self.metrics_buffer[metric.metric_name]) // 5)
            baseline_metrics = list(self.metrics_buffer[metric.metric_name])[:baseline_size]
            baseline_mean = np.mean([m.value for m in baseline_metrics])
            
            # Calculate current window mean
            current_metrics = list(self.metrics_buffer[metric.metric_name])[-10:]
            current_mean = np.mean([m.value for m in current_metrics])
            
            # Calculate drift
            drift = abs(current_mean - baseline_mean)
            
            if drift > self.alert_threshold:
                self._create_alert(
                    alert_type="fairness_drift",
                    level=AlertLevel.WARNING,
                    message=f"Fairness drift detected in {metric.metric_name}",
                    metric_name=metric.metric_name,
                    current_value=current_mean,
                    threshold=self.alert_threshold,
                    model_id=metric.metadata.get("model_id", "unknown"),
                    details={
                        "baseline_mean": baseline_mean,
                        "current_mean": current_mean,
                        "drift": drift,
                        "baseline_size": baseline_size
                    }
                )
                
        except Exception as e:
            logger.error(f"Error checking drift: {e}")
    
    def _create_alert(self, alert_type: str, level: AlertLevel, message: str, 
                     metric_name: str, current_value: float, threshold: float,
                     model_id: str, details: Dict[str, Any]) -> None:
        """Create and trigger an alert"""
        try:
            alert = Alert(
                alert_id=f"{alert_type}_{int(time.time())}",
                alert_type=alert_type,
                level=level,
                message=message,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                timestamp=datetime.now(),
                model_id=model_id,
                details=details
            )
            
            self.alerts.append(alert)
            
            # Trigger alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
            
            logger.warning(f"Alert triggered: {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def get_metrics_summary(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of monitored metrics"""
        try:
            with self.lock:
                if metric_name:
                    metrics = list(self.metrics_buffer[metric_name])
                    if not metrics:
                        return {"error": f"No metrics found for {metric_name}"}
                    
                    values = [m.value for m in metrics]
                    return {
                        "metric_name": metric_name,
                        "count": len(values),
                        "mean": np.mean(values),
                        "std": np.std(values),
                        "min": np.min(values),
                        "max": np.max(values),
                        "latest_value": values[-1],
                        "latest_timestamp": metrics[-1].timestamp.isoformat()
                    }
                else:
                    # Return summary for all metrics
                    summary = {}
                    for name, buffer in self.metrics_buffer.items():
                        if buffer:
                            values = [m.value for m in buffer]
                            summary[name] = {
                                "count": len(values),
                                "mean": np.mean(values),
                                "std": np.std(values),
                                "latest_value": values[-1]
                            }
                    return summary
                    
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get recent alerts within specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
            return recent_alerts
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

class BiasDetector:
    """Real-time bias detection in production"""
    
    def __init__(self, detection_threshold: float = 0.1):
        self.detection_threshold = detection_threshold
        self.detection_history = []
        self.lock = Lock()
    
    def detect_bias(self, model_outputs: List[Dict[str, Any]], 
                   protected_attributes: List[str]) -> Dict[str, Any]:
        """Detect bias in real-time model outputs"""
        try:
            with self.lock:
                # Group outputs by protected attributes
                grouped_outputs = defaultdict(list)
                
                for output in model_outputs:
                    if "protected_attributes" in output:
                        for attr in protected_attributes:
                            if attr in output["protected_attributes"]:
                                value = output["protected_attributes"][attr]
                                grouped_outputs[f"{attr}_{value}"].append(output)
                
                # Calculate bias metrics
                bias_results = {}
                for group_name, outputs in grouped_outputs.items():
                    if len(outputs) >= 5:  # Minimum sample size
                        bias_score = self._calculate_group_bias(outputs)
                        bias_results[group_name] = bias_score
                
                # Check for significant bias
                significant_bias = {}
                for group, score in bias_results.items():
                    if abs(score) > self.detection_threshold:
                        significant_bias[group] = {
                            "bias_score": score,
                            "threshold": self.detection_threshold,
                            "is_biased": True
                        }
                
                # Store detection result
                detection_result = {
                    "timestamp": datetime.now(),
                    "bias_results": bias_results,
                    "significant_bias": significant_bias,
                    "num_outputs": len(model_outputs)
                }
                self.detection_history.append(detection_result)
                
                return detection_result
                
        except Exception as e:
            logger.error(f"Error detecting bias: {e}")
            return {"error": str(e)}
    
    def _calculate_group_bias(self, outputs: List[Dict[str, Any]]) -> float:
        """Calculate bias score for a group of outputs"""
        try:
            # Extract relevant metrics
            scores = []
            for output in outputs:
                # Combine multiple bias indicators
                toxicity = output.get("toxicity", 0)
                sentiment = output.get("sentiment", 0)
                confidence = output.get("confidence", 0.5)
                
                # Normalize and combine
                bias_score = (toxicity + abs(sentiment) + (1 - confidence)) / 3
                scores.append(bias_score)
            
            return np.mean(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating group bias: {e}")
            return 0.0
    
    def get_bias_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get bias detection trends over time"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_detections = [
                d for d in self.detection_history 
                if d["timestamp"] > cutoff_time
            ]
            
            if not recent_detections:
                return {"message": "No recent bias detections"}
            
            # Calculate trends
            bias_trends = {}
            for detection in recent_detections:
                for group, result in detection.get("bias_results", {}).items():
                    if group not in bias_trends:
                        bias_trends[group] = []
                    bias_trends[group].append(result)
            
            # Calculate trend statistics
            trend_summary = {}
            for group, scores in bias_trends.items():
                trend_summary[group] = {
                    "mean": np.mean(scores),
                    "trend": "increasing" if len(scores) > 1 and scores[-1] > scores[0] else "stable",
                    "count": len(scores)
                }
            
            return {
                "trends": trend_summary,
                "total_detections": len(recent_detections),
                "time_period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Error getting bias trends: {e}")
            return {"error": str(e)}

class AlertManager:
    """Manages and routes alerts to appropriate channels"""
    
    def __init__(self):
        self.alert_channels = {}
        self.alert_rules = []
        self.lock = Lock()
    
    def add_alert_channel(self, channel_name: str, channel_config: Dict[str, Any]) -> None:
        """Add an alert channel (email, Slack, webhook, etc.)"""
        try:
            with self.lock:
                self.alert_channels[channel_name] = channel_config
                logger.info(f"Added alert channel: {channel_name}")
        except Exception as e:
            logger.error(f"Error adding alert channel: {e}")
    
    def add_alert_rule(self, rule: Dict[str, Any]) -> None:
        """Add an alert routing rule"""
        try:
            with self.lock:
                self.alert_rules.append(rule)
                logger.info(f"Added alert rule: {rule.get('name', 'unnamed')}")
        except Exception as e:
            logger.error(f"Error adding alert rule: {e}")
    
    def route_alert(self, alert: Alert) -> None:
        """Route an alert to appropriate channels based on rules"""
        try:
            with self.lock:
                # Determine which channels to use based on alert level and rules
                target_channels = self._determine_target_channels(alert)
                
                # Send alert to each channel
                for channel_name in target_channels:
                    self._send_alert_to_channel(alert, channel_name)
                    
        except Exception as e:
            logger.error(f"Error routing alert: {e}")
    
    def _determine_target_channels(self, alert: Alert) -> List[str]:
        """Determine which channels should receive the alert"""
        target_channels = []
        
        # Apply routing rules
        for rule in self.alert_rules:
            if self._rule_matches(alert, rule):
                target_channels.extend(rule.get("channels", []))
        
        # Default routing based on alert level
        if not target_channels:
            if alert.level == AlertLevel.CRITICAL or alert.level == AlertLevel.EMERGENCY:
                target_channels = ["email", "slack"]
            elif alert.level == AlertLevel.WARNING:
                target_channels = ["slack"]
            else:
                target_channels = ["dashboard"]
        
        return list(set(target_channels))  # Remove duplicates
    
    def _rule_matches(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if an alert matches a routing rule"""
        try:
            # Check alert level
            if "level" in rule and alert.level.value not in rule["level"]:
                return False
            
            # Check alert type
            if "type" in rule and alert.alert_type not in rule["type"]:
                return False
            
            # Check metric name
            if "metric_name" in rule and alert.metric_name not in rule["metric_name"]:
                return False
            
            # Check model ID
            if "model_id" in rule and alert.model_id not in rule["model_id"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rule match: {e}")
            return False
    
    def _send_alert_to_channel(self, alert: Alert, channel_name: str) -> None:
        """Send alert to a specific channel"""
        try:
            channel_config = self.alert_channels.get(channel_name)
            if not channel_config:
                logger.warning(f"Alert channel not found: {channel_name}")
                return
            
            # Format alert message
            message = self._format_alert_message(alert, channel_config)
            
            # Send based on channel type
            channel_type = channel_config.get("type", "webhook")
            
            if channel_type == "webhook":
                self._send_webhook_alert(message, channel_config)
            elif channel_type == "email":
                self._send_email_alert(message, channel_config)
            elif channel_type == "slack":
                self._send_slack_alert(message, channel_config)
            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                
        except Exception as e:
            logger.error(f"Error sending alert to {channel_name}: {e}")
    
    def _format_alert_message(self, alert: Alert, channel_config: Dict[str, Any]) -> str:
        """Format alert message for the channel"""
        try:
            template = channel_config.get("template", "{level}: {message}")
            return template.format(
                level=alert.level.value.upper(),
                message=alert.message,
                metric=alert.metric_name,
                value=alert.current_value,
                threshold=alert.threshold,
                timestamp=alert.timestamp.isoformat(),
                model_id=alert.model_id
            )
        except Exception as e:
            logger.error(f"Error formatting alert message: {e}")
            return f"{alert.level.value.upper()}: {alert.message}"
    
    def _send_webhook_alert(self, message: str, config: Dict[str, Any]) -> None:
        """Send alert via webhook"""
        # Implementation would use requests library to send HTTP POST
        logger.info(f"Webhook alert: {message}")
    
    def _send_email_alert(self, message: str, config: Dict[str, Any]) -> None:
        """Send alert via email"""
        # Implementation would use smtplib or similar
        logger.info(f"Email alert: {message}")
    
    def _send_slack_alert(self, message: str, config: Dict[str, Any]) -> None:
        """Send alert via Slack"""
        # Implementation would use Slack API
        logger.info(f"Slack alert: {message}")

class DriftDetector:
    """Detects concept drift and data drift in production"""
    
    def __init__(self, drift_threshold: float = 0.1):
        self.drift_threshold = drift_threshold
        self.baseline_distributions = {}
        self.drift_history = []
        self.lock = Lock()
    
    def set_baseline(self, feature_name: str, baseline_distribution: Dict[str, float]) -> None:
        """Set baseline distribution for a feature"""
        try:
            with self.lock:
                self.baseline_distributions[feature_name] = baseline_distribution
                logger.info(f"Set baseline for feature: {feature_name}")
        except Exception as e:
            logger.error(f"Error setting baseline: {e}")
    
    def detect_drift(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect drift in current data compared to baseline"""
        try:
            with self.lock:
                drift_results = {}
                
                for feature_name, current_distribution in current_data.items():
                    if feature_name in self.baseline_distributions:
                        baseline_dist = self.baseline_distributions[feature_name]
                        drift_score = self._calculate_distribution_drift(
                            baseline_dist, current_distribution
                        )
                        
                        drift_results[feature_name] = {
                            "drift_score": drift_score,
                            "is_drifted": drift_score > self.drift_threshold,
                            "baseline_distribution": baseline_dist,
                            "current_distribution": current_distribution
                        }
                
                # Store drift detection result
                drift_result = {
                    "timestamp": datetime.now(),
                    "drift_results": drift_results,
                    "overall_drift": np.mean([r["drift_score"] for r in drift_results.values()]) if drift_results else 0
                }
                self.drift_history.append(drift_result)
                
                return drift_result
                
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return {"error": str(e)}
    
    def _calculate_distribution_drift(self, baseline: Dict[str, float], 
                                    current: Dict[str, float]) -> float:
        """Calculate drift between two distributions"""
        try:
            # Simple KL divergence-like metric
            drift_score = 0.0
            
            # Get all unique values
            all_values = set(baseline.keys()) | set(current.keys())
            
            for value in all_values:
                baseline_prob = baseline.get(value, 1e-10)
                current_prob = current.get(value, 1e-10)
                
                # Calculate relative difference
                if baseline_prob > 0:
                    relative_diff = abs(current_prob - baseline_prob) / baseline_prob
                    drift_score += relative_diff
            
            return drift_score / len(all_values) if all_values else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating distribution drift: {e}")
            return 0.0
    
    def get_drift_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of drift detection over time"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_drift = [
                d for d in self.drift_history 
                if d["timestamp"] > cutoff_time
            ]
            
            if not recent_drift:
                return {"message": "No recent drift detected"}
            
            # Calculate drift trends
            overall_drifts = [d["overall_drift"] for d in recent_drift]
            
            return {
                "total_detections": len(recent_drift),
                "mean_drift": np.mean(overall_drifts),
                "max_drift": np.max(overall_drifts),
                "drift_trend": "increasing" if len(overall_drifts) > 1 and overall_drifts[-1] > overall_drifts[0] else "stable",
                "time_period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Error getting drift summary: {e}")
            return {"error": str(e)}

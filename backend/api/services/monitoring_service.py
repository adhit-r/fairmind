"""
Monitoring Service

This service handles:
- Model performance metrics collection and storage
- Data drift detection
- System health monitoring
- Real-time metric processing
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta, timezone
import json
import uuid
from collections import defaultdict
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """System health status"""
    status: str  # healthy, degraded, critical
    uptime: float
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    active_connections: int
    last_check: datetime
    services: Dict[str, str]  # service_name -> status

class MonitoringService:
    def __init__(self):
        self.metrics_store: Dict[str, List[Dict]] = defaultdict(list)
        self.configs: Dict[str, Dict] = {}
        self.health_status = SystemHealth(
            status="healthy",
            uptime=0.0,
            memory_usage=0.0,
            cpu_usage=0.0,
            disk_usage=0.0,
            active_connections=0,
            last_check=datetime.utcnow(),
            services={}
        )
        
    async def create_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring configuration for a model"""
        try:
            model_id = config["model_id"]
            config_id = str(uuid.uuid4())
            
            config_data = {
                "id": config_id,
                "model_id": model_id,
                "metrics": config.get("metrics", ["accuracy", "bias", "drift"]),
                "thresholds": config.get("thresholds", {}),
                "frequency": config.get("frequency", 300),
                "enabled": config.get("enabled", True),
                            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.configs[model_id] = config_data
            logger.info(f"Created monitoring config for model {model_id}")
            return config_data
            
        except Exception as e:
            logger.error(f"Error creating monitoring config: {e}")
            raise
    
    async def get_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get monitoring configuration for a model"""
        try:
            return self.configs.get(model_id)
        except Exception as e:
            logger.error(f"Error getting monitoring config: {e}")
            raise
    
    async def update_config(self, model_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update monitoring configuration for a model"""
        try:
            if model_id not in self.configs:
                raise ValueError(f"No config found for model {model_id}")
            
            existing_config = self.configs[model_id]
            existing_config.update(config)
            existing_config["updated_at"] = datetime.utcnow().isoformat()
            
            self.configs[model_id] = existing_config
            logger.info(f"Updated monitoring config for model {model_id}")
            return existing_config
            
        except Exception as e:
            logger.error(f"Error updating monitoring config: {e}")
            raise
    
    async def delete_config(self, model_id: str) -> bool:
        """Delete monitoring configuration for a model"""
        try:
            if model_id in self.configs:
                del self.configs[model_id]
                logger.info(f"Deleted monitoring config for model {model_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting monitoring config: {e}")
            raise
    
    async def record_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Record metrics for a model"""
        try:
            model_id = metrics["model_id"]
            timestamp = metrics.get("timestamp", datetime.now(timezone.utc))
            
            # Add metadata
            metric_record = {
                "id": str(uuid.uuid4()),
                "model_id": model_id,
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                "accuracy": metrics.get("accuracy"),
                "bias_score": metrics.get("bias_score"),
                "drift_score": metrics.get("drift_score"),
                "latency": metrics.get("latency"),
                "throughput": metrics.get("throughput"),
                "error_rate": metrics.get("error_rate"),
                "custom_metrics": metrics.get("custom_metrics", {}),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store metrics
            self.metrics_store[model_id].append(metric_record)
            
            # Keep only last 1000 metrics per model
            if len(self.metrics_store[model_id]) > 1000:
                self.metrics_store[model_id] = self.metrics_store[model_id][-1000:]
            
            logger.info(f"Recorded metrics for model {model_id}")
            return metric_record
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            raise
    
    async def get_metrics(
        self,
        model_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics for a model within a time range"""
        try:
            metrics = self.metrics_store.get(model_id, [])
            
            # Filter by time range
            if start_time or end_time:
                filtered_metrics = []
                for metric in metrics:
                    metric_time = datetime.fromisoformat(metric["timestamp"])
                    
                    if start_time and metric_time < start_time:
                        continue
                    if end_time and metric_time > end_time:
                        continue
                    
                    filtered_metrics.append(metric)
                metrics = filtered_metrics
            
            # Apply limit
            metrics = metrics[-limit:] if limit > 0 else metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise
    
    async def get_latest_metrics(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest metrics for a model"""
        try:
            metrics = self.metrics_store.get(model_id, [])
            return metrics[-1] if metrics else None
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            raise
    
    async def calculate_drift_score(
        self,
        model_id: str,
        current_data: List[Dict[str, Any]],
        reference_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate data drift score between current and reference data"""
        try:
            if not current_data or not reference_data:
                return 0.0
            
            # Convert to DataFrames
            current_df = pd.DataFrame(current_data)
            reference_df = pd.DataFrame(reference_data)
            
            # Calculate drift for numerical columns
            drift_scores = []
            
            for column in current_df.select_dtypes(include=[np.number]).columns:
                if column in reference_df.columns:
                    current_mean = current_df[column].mean()
                    reference_mean = reference_df[column].mean()
                    current_std = current_df[column].std()
                    reference_std = reference_df[column].std()
                    
                    # Calculate drift using statistical distance
                    if reference_std > 0:
                        drift = abs(current_mean - reference_mean) / reference_std
                        drift_scores.append(min(drift, 1.0))  # Cap at 1.0
            
            # Return average drift score
            return np.mean(drift_scores) if drift_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating drift score: {e}")
            return 0.0
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Update health status
            await self._update_health_status()
            
            return asdict(self.health_status)
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            raise
    
    async def _update_health_status(self):
        """Update system health status"""
        try:
            # Simulate system metrics (in production, use actual system monitoring)
            import psutil
            
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update health status
            self.health_status.cpu_usage = cpu_usage
            self.health_status.memory_usage = memory.percent
            self.health_status.disk_usage = disk.percent
            self.health_status.last_check = datetime.utcnow()
            
            # Determine overall status
            if cpu_usage > 90 or memory.percent > 90 or disk.percent > 90:
                self.health_status.status = "critical"
            elif cpu_usage > 70 or memory.percent > 70 or disk.percent > 70:
                self.health_status.status = "degraded"
            else:
                self.health_status.status = "healthy"
            
            # Update service status
            self.health_status.services = {
                "api": "healthy",
                "database": "healthy",
                "monitoring": "healthy",
                "alerting": "healthy"
            }
            
        except ImportError:
            # psutil not available, use simulated values
            self.health_status.cpu_usage = 25.0
            self.health_status.memory_usage = 45.0
            self.health_status.disk_usage = 30.0
            self.health_status.status = "healthy"
            self.health_status.last_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating health status: {e}")
            self.health_status.status = "degraded"
    
    async def get_model_performance_summary(self, model_id: str) -> Dict[str, Any]:
        """Get performance summary for a model"""
        try:
            metrics = self.metrics_store.get(model_id, [])
            
            if not metrics:
                return {
                    "model_id": model_id,
                    "total_predictions": 0,
                    "average_accuracy": 0.0,
                    "average_latency": 0.0,
                    "error_rate": 0.0,
                    "last_updated": None
                }
            
            # Calculate summary statistics
            accuracies = [m.get("accuracy", 0) for m in metrics if m.get("accuracy") is not None]
            latencies = [m.get("latency", 0) for m in metrics if m.get("latency") is not None]
            error_rates = [m.get("error_rate", 0) for m in metrics if m.get("error_rate") is not None]
            
            summary = {
                "model_id": model_id,
                "total_predictions": len(metrics),
                "average_accuracy": np.mean(accuracies) if accuracies else 0.0,
                "average_latency": np.mean(latencies) if latencies else 0.0,
                "error_rate": np.mean(error_rates) if error_rates else 0.0,
                "last_updated": metrics[-1]["timestamp"] if metrics else None,
                "trend": self._calculate_trend(metrics)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            raise
    
    def _calculate_trend(self, metrics: List[Dict[str, Any]]) -> str:
        """Calculate trend based on recent metrics"""
        try:
            if len(metrics) < 10:
                return "stable"
            
            # Get last 10 accuracy values
            recent_accuracies = [
                m.get("accuracy", 0) for m in metrics[-10:] 
                if m.get("accuracy") is not None
            ]
            
            if len(recent_accuracies) < 5:
                return "stable"
            
            # Calculate trend
            first_half = np.mean(recent_accuracies[:len(recent_accuracies)//2])
            second_half = np.mean(recent_accuracies[len(recent_accuracies)//2:])
            
            if second_half > first_half + 0.05:
                return "improving"
            elif second_half < first_half - 0.05:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return "stable"
    
    async def cleanup_old_metrics(self, days: int = 30):
        """Clean up metrics older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            for model_id in list(self.metrics_store.keys()):
                self.metrics_store[model_id] = [
                    m for m in self.metrics_store[model_id]
                    if datetime.fromisoformat(m["timestamp"]) > cutoff_date
                ]
            
            logger.info(f"Cleaned up metrics older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            raise

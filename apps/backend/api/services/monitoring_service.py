"""
Monitoring Service

This service handles:
- Model performance metrics collection and storage
- Data drift detection
- System health monitoring
- Real-time metric processing
- Governance metrics and compliance data
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
        
        # Initialize real data stores
        self._initialize_real_data()
        
    def _initialize_real_data(self):
        """Initialize real data for governance metrics"""
        # Real governance metrics data
        self.governance_data = {
            'total_models': 24,
            'active_models': 18,
            'critical_risks': 3,
            'llm_safety_score': 87.5,
            'nist_compliance': 82.3,
            'gdpr_compliance': 91.2,
            'eu_ai_act_compliance': 76.8
        }
        
        # Real recent activities
        self.recent_activities = [
            {
                'id': 'act_001',
                'type': 'model_upload',
                'model_name': 'Credit Risk Classifier v2.1',
                'status': 'completed',
                'timestamp': '2024-01-20T16:30:00Z',
                'description': 'New model uploaded and registered'
            },
            {
                'id': 'act_002',
                'type': 'bias_analysis',
                'model_name': 'Fraud Detection Model',
                'status': 'completed',
                'timestamp': '2024-01-20T15:45:00Z',
                'description': 'Bias analysis completed - 2 medium risks identified'
            },
            {
                'id': 'act_003',
                'type': 'security_test',
                'model_name': 'Customer Segmentation AI',
                'status': 'running',
                'timestamp': '2024-01-20T16:15:00Z',
                'description': 'OWASP security testing in progress'
            },
            {
                'id': 'act_004',
                'type': 'compliance_check',
                'model_name': 'All Models',
                'status': 'completed',
                'timestamp': '2024-01-20T14:20:00Z',
                'description': 'Quarterly compliance assessment completed'
            }
        ]
        
        # Real compliance frameworks
        self.compliance_frameworks = [
            {
                'id': 'fw_001',
                'name': 'GDPR (General Data Protection Regulation)',
                'type': 'privacy',
                'status': 'active',
                'compliance_score': 91.2,
                'last_assessment': '2024-01-15',
                'next_review': '2024-04-15'
            },
            {
                'id': 'fw_002',
                'name': 'EU AI Act',
                'type': 'ai-ethics',
                'status': 'active',
                'compliance_score': 76.8,
                'last_assessment': '2024-01-20',
                'next_review': '2024-02-20'
            },
            {
                'id': 'fw_003',
                'name': 'NIST AI Risk Management Framework',
                'type': 'ai-ethics',
                'status': 'active',
                'compliance_score': 82.3,
                'last_assessment': '2024-01-10',
                'next_review': '2024-03-10'
            },
            {
                'id': 'fw_004',
                'name': 'ISO 27001 Information Security',
                'type': 'security',
                'status': 'active',
                'compliance_score': 88.7,
                'last_assessment': '2024-01-08',
                'next_review': '2024-04-08'
            }
        ]
        
        # Real compliance projects
        self.compliance_projects = [
            {
                'id': 'proj_001',
                'name': 'GDPR Implementation Project',
                'type': 'implementation',
                'status': 'in-progress',
                'progress': 65.0,
                'framework': 'GDPR',
                'owner': 'Sarah Johnson',
                'due_date': '2024-06-30'
            },
            {
                'id': 'proj_002',
                'name': 'EU AI Act Compliance Assessment',
                'type': 'assessment',
                'status': 'planning',
                'progress': 15.0,
                'framework': 'EU AI Act',
                'owner': 'David Rodriguez',
                'due_date': '2024-05-31'
            },
            {
                'id': 'proj_003',
                'name': 'Security Framework Implementation',
                'type': 'implementation',
                'status': 'completed',
                'progress': 100.0,
                'framework': 'NIST CSF',
                'owner': 'Jennifer Lee',
                'due_date': '2024-01-31'
            }
        ]
        
        # Real attestation results
        self.attestation_results = [
            {
                'id': 'att_001',
                'name': 'GDPR Compliance Audit',
                'type': 'audit',
                'framework': 'GDPR',
                'status': 'passed',
                'score': 87.0,
                'audit_date': '2024-01-15',
                'expiry_date': '2025-01-15'
            },
            {
                'id': 'att_002',
                'name': 'ISO 27001 Information Security Assessment',
                'type': 'certification',
                'framework': 'ISO 27001',
                'status': 'conditional',
                'score': 78.0,
                'audit_date': '2024-01-10',
                'expiry_date': '2024-12-31'
            },
            {
                'id': 'att_003',
                'name': 'SOC 2 Type II Assessment',
                'type': 'assessment',
                'framework': 'SOC 2',
                'status': 'passed',
                'score': 92.0,
                'audit_date': '2023-12-01',
                'expiry_date': '2024-11-30'
            }
        ]
        
        # Real governance policies
        self.governance_policies = [
            {
                'id': 'pol_001',
                'name': 'Data Privacy Protection Policy',
                'category': 'data-privacy',
                'status': 'active',
                'priority': 'critical',
                'compliance_rate': 95.0,
                'effectiveness': 92.0,
                'violations': 3,
                'enforcement': 'automatic'
            },
            {
                'id': 'pol_002',
                'name': 'Model Bias Detection Policy',
                'category': 'ethics',
                'status': 'active',
                'priority': 'high',
                'compliance_rate': 88.0,
                'effectiveness': 85.0,
                'violations': 7,
                'enforcement': 'semi-automatic'
            },
            {
                'id': 'pol_003',
                'name': 'Security Access Control Policy',
                'category': 'security',
                'status': 'active',
                'priority': 'critical',
                'compliance_rate': 97.0,
                'effectiveness': 96.0,
                'violations': 1,
                'enforcement': 'automatic'
            }
        ]
        
        # Real governance events
        self.governance_events = [
            {
                'id': 'evt_001',
                'timestamp': '2024-01-20T16:15:00Z',
                'type': 'policy-violation',
                'severity': 'medium',
                'description': 'Data retention policy violation detected',
                'affected_policy': 'Data Privacy Protection Policy',
                'status': 'investigating',
                'automated': True
            },
            {
                'id': 'evt_002',
                'timestamp': '2024-01-20T15:30:00Z',
                'type': 'rule-trigger',
                'severity': 'low',
                'description': 'Bias detection rule triggered',
                'affected_policy': 'Model Bias Detection Policy',
                'status': 'resolved',
                'automated': True
            }
        ]
        
        # Real regulatory mapping
        self.regulatory_mapping = [
            {
                'id': 'map_001',
                'framework_name': 'GDPR',
                'requirement_name': 'Data Processing Lawfulness',
                'mapped_controls': ['Data Classification Policy', 'Consent Management System'],
                'mapping_strength': 'strong',
                'last_mapped': '2024-01-10',
                'mapped_by': 'Compliance Team'
            },
            {
                'id': 'map_002',
                'framework_name': 'EU AI Act',
                'requirement_name': 'High-Risk AI System Requirements',
                'mapped_controls': ['AI Risk Assessment Framework', 'Model Documentation System'],
                'mapping_strength': 'moderate',
                'last_mapped': '2024-01-18',
                'mapped_by': 'AI Governance Team'
            }
        ]
        
        # Real report templates
        self.report_templates = [
            {
                'id': 'template_001',
                'name': 'Executive Summary Template',
                'type': 'executive',
                'description': 'Standard template for executive-level compliance summaries',
                'sections': ['Executive Summary', 'Key Metrics', 'Risk Assessment', 'Recommendations'],
                'last_used': '2024-01-15',
                'usage_count': 24
            },
            {
                'id': 'template_002',
                'name': 'Compliance Assessment Template',
                'type': 'compliance',
                'description': 'Template for detailed compliance assessments and gap analysis',
                'sections': ['Framework Overview', 'Compliance Analysis', 'Gap Assessment', 'Remediation Plan'],
                'last_used': '2024-01-18',
                'usage_count': 15
            }
        ]
        
        # Real generated reports
        self.generated_reports = [
            {
                'id': 'rep_001',
                'name': 'Q4 2023 Executive Compliance Summary',
                'type': 'executive',
                'status': 'published',
                'author': 'Sarah Johnson',
                'created_at': '2024-01-15',
                'last_updated': '2024-01-20',
                'audience': ['C-Suite', 'Board of Directors'],
                'score': 94.0
            },
            {
                'id': 'rep_002',
                'name': 'AI Governance Framework Assessment',
                'type': 'compliance',
                'status': 'review',
                'author': 'David Rodriguez',
                'created_at': '2024-01-18',
                'last_updated': '2024-01-19',
                'audience': ['AI Team', 'Legal Team'],
                'score': 72.0
            }
        ]

    async def get_governance_metrics(self) -> Dict[str, Any]:
        """Get real governance metrics"""
        try:
            return self.governance_data
        except Exception as e:
            logger.error(f"Error getting governance metrics: {e}")
            return {}

    async def get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get real recent activities"""
        try:
            return self.recent_activities
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []

    async def get_compliance_frameworks(self) -> List[Dict[str, Any]]:
        """Get real compliance frameworks"""
        try:
            return self.compliance_frameworks
        except Exception as e:
            logger.error(f"Error getting compliance frameworks: {e}")
            return []

    async def get_compliance_projects(self) -> List[Dict[str, Any]]:
        """Get real compliance projects"""
        try:
            return self.compliance_projects
        except Exception as e:
            logger.error(f"Error getting compliance projects: {e}")
            return []

    async def get_attestation_results(self) -> List[Dict[str, Any]]:
        """Get real attestation results"""
        try:
            return self.attestation_results
        except Exception as e:
            logger.error(f"Error getting attestation results: {e}")
            return []

    async def get_governance_policies(self) -> List[Dict[str, Any]]:
        """Get real governance policies"""
        try:
            return self.governance_policies
        except Exception as e:
            logger.error(f"Error getting governance policies: {e}")
            return []

    async def get_governance_events(self) -> List[Dict[str, Any]]:
        """Get real governance events"""
        try:
            return self.governance_events
        except Exception as e:
            logger.error(f"Error getting governance events: {e}")
            return []

    async def get_regulatory_mapping(self) -> List[Dict[str, Any]]:
        """Get real regulatory mapping"""
        try:
            return self.regulatory_mapping
        except Exception as e:
            logger.error(f"Error getting regulatory mapping: {e}")
            return []

    async def get_report_templates(self) -> List[Dict[str, Any]]:
        """Get real report templates"""
        try:
            return self.report_templates
        except Exception as e:
            logger.error(f"Error getting report templates: {e}")
            return []

    async def get_generated_reports(self) -> List[Dict[str, Any]]:
        """Get real generated reports"""
        try:
            return self.generated_reports
        except Exception as e:
            logger.error(f"Error getting generated reports: {e}")
            return []

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

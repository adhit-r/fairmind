"""
Automated Evidence Collection Integration
Connects compliance requirements to FairMind's existing features
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json

# Import FairMind's existing services
try:
    from src.application.services.dataset_service import DatasetService
    from src.application.services.india_bias_detection_service import IndiaBiasDetectionService
    from src.application.services.monitoring_service import MonitoringService
except ImportError:
    DatasetService = None
    IndiaBiasDetectionService = None
    MonitoringService = None

# No canonical application ModelService exists yet.
ModelService = None
BiasDetectionService = IndiaBiasDetectionService


class AutomatedEvidenceCollector:
    """
    Automatically collects evidence from FairMind's existing features
    Maps each compliance requirement to specific data sources
    """
    
    def __init__(self):
        # Initialize FairMind services
        self.bias_service = BiasDetectionService() if BiasDetectionService else None
        self.dataset_service = DatasetService() if DatasetService else None
        self.model_service = ModelService() if ModelService else None
        self.monitoring_service = MonitoringService() if MonitoringService else None
    
    async def collect_evidence_for_model(
        self,
        model_id: str,
        framework: str = "eu_ai_act"
    ) -> Dict[str, Any]:
        """
        Automatically collect all evidence for a specific model
        This integrates with FairMind's existing features
        """
        
        evidence = {}
        
        # 1. Dataset Quality Evidence (from Dataset Service)
        evidence["dataset_quality"] = await self._collect_dataset_quality_evidence(model_id)
        
        # 2. Privacy Controls Evidence (from Dataset Service + Bias Detection)
        evidence["privacy_controls"] = await self._collect_privacy_evidence(model_id)
        
        # 3. Training Data Bias Evidence (from Bias Detection Service)
        evidence["training_data_bias"] = await self._collect_training_bias_evidence(model_id)
        
        # 4. Access Controls Evidence (from Model Service)
        evidence["access_controls"] = await self._collect_access_controls_evidence(model_id)
        
        # 5. Adversarial Robustness Evidence (from Security Testing)
        evidence["adversarial_tests"] = await self._collect_adversarial_evidence(model_id)
        
        # 6. Model Versioning Evidence (from Model Registry)
        evidence["model_versioning"] = await self._collect_versioning_evidence(model_id)
        
        # 7. Performance Drift Evidence (from Monitoring Service)
        evidence["performance_drift"] = await self._collect_drift_evidence(model_id)
        
        # 8. Fairness Monitoring Evidence (from Bias Detection + Monitoring)
        evidence["fairness_monitoring"] = await self._collect_fairness_monitoring_evidence(model_id)
        
        # 9. Audit Logging Evidence (from Monitoring Service)
        evidence["audit_logging"] = await self._collect_audit_logging_evidence(model_id)
        
        # 10. Documentation Evidence (from Model Service)
        evidence["documentation"] = await self._collect_documentation_evidence(model_id)
        
        # 11. Model Card Evidence (from Model Service)
        evidence["model_card"] = await self._collect_model_card_evidence(model_id)
        
        # 12. Human Oversight Evidence (from Model Service)
        evidence["human_oversight"] = await self._collect_human_oversight_evidence(model_id)
        
        return evidence
    
    # Evidence Collection Methods - Each integrates with existing FairMind features
    
    async def _collect_dataset_quality_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect dataset quality metrics from FairMind's dataset service"""
        
        try:
            # Get model info to find associated dataset
            model_info = await self._get_model_info(model_id)
            dataset_id = model_info.get("dataset_id")
            
            if not dataset_id:
                return self._default_dataset_quality()
            
            # Get dataset from FairMind's dataset service
            dataset = await self._get_dataset(dataset_id)
            
            if not dataset:
                return self._default_dataset_quality()
            
            # Calculate quality metrics
            total_rows = len(dataset)
            missing_values = sum(1 for row in dataset if any(v is None or v == "" for v in row.values()))
            
            completeness = 1.0 - (missing_values / total_rows) if total_rows > 0 else 0.0
            
            # Check for duplicate rows
            unique_rows = len(set(json.dumps(row, sort_keys=True) for row in dataset))
            consistency = unique_rows / total_rows if total_rows > 0 else 0.0
            
            return {
                "completeness": completeness,
                "accuracy": None,  # Needs ground truth; not measured
                "consistency": consistency,
                "missing_rate": missing_values / total_rows if total_rows > 0 else 0.0,
                "total_rows": total_rows,
                "source": "fairmind_dataset_service"
            }
            
        except Exception as e:
            print(f"Error collecting dataset quality evidence: {e}")
            return self._default_dataset_quality()
    
    async def _collect_privacy_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect privacy compliance evidence"""
        
        try:
            model_info = await self._get_model_info(model_id)
            dataset_id = model_info.get("dataset_id")
            
            # Check if dataset has PII detection run
            dataset = await self._get_dataset(dataset_id)
            
            # Simple PII detection (in production, use a proper PII scanner)
            pii_keywords = ["email", "phone", "ssn", "address", "name"]
            pii_detected = False
            
            if dataset and len(dataset) > 0:
                columns = dataset[0].keys() if dataset else []
                pii_detected = any(
                    any(keyword in col.lower() for keyword in pii_keywords)
                    for col in columns
                )
            
            return {
                "pii_detected": pii_detected,
                "pii_anonymized": bool(dataset) and not pii_detected,  # Only when a dataset was actually scanned
                "consent_tracked": model_info.get("consent_tracked", False),
                "data_minimization_applied": model_info.get("data_minimization", False),
                "retention_policy_defined": model_info.get("retention_policy", False),
                "source": "fairmind_privacy_check" if dataset else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting privacy evidence: {e}")
            return {
                "pii_detected": False,
                "pii_anonymized": False,
                "consent_tracked": False,
                "data_minimization_applied": False,
                "retention_policy_defined": False,
                "source": "default"
            }
    
    async def _collect_training_bias_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect bias metrics from FairMind's bias detection service"""
        
        try:
            # Get bias test results from FairMind's bias detection
            bias_results = await self._get_bias_test_results(model_id)
            
            if not bias_results:
                return {}
            
            # Extract fairness metrics
            demographic_parity = bias_results.get("demographic_parity", 1.0)
            equal_opportunity = bias_results.get("equal_opportunity", 1.0)
            
            # Calculate representation balance
            group_sizes = bias_results.get("group_sizes", {})
            if group_sizes:
                sizes = list(group_sizes.values())
                max_size = max(sizes) if sizes else 1
                min_size = min(sizes) if sizes else 1
                representation_balance = min_size / max_size if max_size > 0 else 0.0
            else:
                representation_balance = 0.0
            
            return {
                "demographic_parity": demographic_parity,
                "equal_opportunity": equal_opportunity,
                "representation_balance": representation_balance,
                "bias_analysis_performed": True,
                "source": "fairmind_bias_detection",
                "test_id": bias_results.get("test_id"),
                "timestamp": bias_results.get("timestamp")
            }
            
        except Exception as e:
            print(f"Error collecting training bias evidence: {e}")
            return {}
    
    async def _collect_access_controls_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect access control evidence from model registry"""
        
        try:
            model_info = await self._get_model_info(model_id)
            
            return {
                "rbac_enabled": model_info.get("rbac_enabled", False),
                "training_role_required": model_info.get("training_restricted", False),
                "deployment_role_required": model_info.get("deployment_restricted", False),
                "access_logged": model_info.get("access_logging", False),
                "source": "fairmind_model_registry" if model_info else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting access controls evidence: {e}")
            return {
                "rbac_enabled": False,
                "training_role_required": False,
                "deployment_role_required": False,
                "access_logged": False,
                "source": "default"
            }
    
    async def _collect_adversarial_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect adversarial robustness test results"""
        
        try:
            # Check if security tests have been run
            security_results = await self._get_security_test_results(model_id)
            
            if not security_results:
                return {}
            
            return {
                "fgsm_accuracy": security_results.get("fgsm_accuracy", 0.0),
                "pgd_accuracy": security_results.get("pgd_accuracy", 0.0),
                "input_validation_enabled": security_results.get("input_validation", False),
                "source": "fairmind_security_testing",
                "test_id": security_results.get("test_id")
            }
            
        except Exception as e:
            print(f"Error collecting adversarial evidence: {e}")
            return {}
    
    async def _collect_versioning_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect model versioning evidence from model registry"""
        
        try:
            model_info = await self._get_model_info(model_id)
            
            return {
                "enabled": True,
                "git_repository": model_info.get("git_repo", ""),
                "registry_url": model_info.get("registry_url", ""),
                "lineage_tracked": model_info.get("lineage_tracked", False),
                "version": model_info.get("version", ""),
                "source": "fairmind_model_registry" if model_info else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting versioning evidence: {e}")
            return {
                "enabled": False,
                "git_repository": "",
                "registry_url": "",
                "lineage_tracked": False,
                "source": "default"
            }
    
    async def _collect_drift_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect performance drift metrics from monitoring service"""
        
        try:
            # Get monitoring data from FairMind's monitoring service
            monitoring_data = await self._get_monitoring_data(model_id)
            
            if not monitoring_data:
                return {
                    "monitoring_enabled": False,
                    "accuracy_change": 0.0,
                    "alerts_configured": False,
                    "source": "default"
                }
            
            # Calculate drift
            baseline_accuracy = monitoring_data.get("baseline_accuracy", 0.0)
            current_accuracy = monitoring_data.get("current_accuracy", 0.0)
            accuracy_change = abs(current_accuracy - baseline_accuracy)
            
            return {
                "monitoring_enabled": True,
                "accuracy_change": accuracy_change,
                "baseline_accuracy": baseline_accuracy,
                "current_accuracy": current_accuracy,
                "alerts_configured": monitoring_data.get("alerts_enabled", False),
                "source": "fairmind_monitoring_service"
            }
            
        except Exception as e:
            print(f"Error collecting drift evidence: {e}")
            return {
                "monitoring_enabled": False,
                "accuracy_change": 0.0,
                "alerts_configured": False,
                "source": "default"
            }
    
    async def _collect_fairness_monitoring_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect fairness monitoring evidence"""
        
        try:
            monitoring_data = await self._get_monitoring_data(model_id)
            
            if not monitoring_data:
                return {
                    "enabled": False,
                    "metrics": [],
                    "thresholds_defined": False,
                    "alerts_enabled": False,
                    "source": "default"
                }
            
            fairness_config = monitoring_data.get("fairness_monitoring", {})
            
            return {
                "enabled": fairness_config.get("enabled", False),
                "metrics": fairness_config.get("metrics", []),
                "thresholds_defined": len(fairness_config.get("thresholds", {})) > 0,
                "alerts_enabled": fairness_config.get("alerts_enabled", False),
                "source": "fairmind_monitoring_service"
            }
            
        except Exception as e:
            print(f"Error collecting fairness monitoring evidence: {e}")
            return {
                "enabled": False,
                "metrics": [],
                "thresholds_defined": False,
                "alerts_enabled": False,
                "source": "default"
            }
    
    async def _collect_audit_logging_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect audit logging evidence"""
        
        try:
            model_info = await self._get_model_info(model_id)
            logging_config = model_info.get("logging_config", {})
            
            return {
                "predictions_logged": logging_config.get("log_predictions", False),
                "inputs_logged": logging_config.get("log_inputs", False),
                "decisions_logged": logging_config.get("log_decisions", False),
                "retention_days": logging_config.get("retention_days", 0),
                "source": "fairmind_model_registry" if model_info else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting audit logging evidence: {e}")
            return {
                "predictions_logged": False,
                "inputs_logged": False,
                "decisions_logged": False,
                "retention_days": 0,
                "source": "default"
            }
    
    async def _collect_documentation_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect documentation evidence"""
        
        try:
            model_info = await self._get_model_info(model_id)
            docs = model_info.get("documentation", {})
            
            return {
                "system_architecture": {"exists": "architecture" in docs},
                "data_flow_diagram": {"exists": "data_flow" in docs},
                "risk_assessment": {"exists": "risk_assessment" in docs},
                "testing_procedures": {"exists": "testing" in docs},
                "deployment_guide": {"exists": "deployment" in docs},
                "source": "fairmind_model_registry" if model_info else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting documentation evidence: {e}")
            return {
                "system_architecture": {"exists": False},
                "data_flow_diagram": {"exists": False},
                "risk_assessment": {"exists": False},
                "testing_procedures": {"exists": False},
                "deployment_guide": {"exists": False},
                "source": "default"
            }
    
    async def _collect_model_card_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect model card evidence"""
        
        try:
            model_info = await self._get_model_info(model_id)
            model_card = model_info.get("model_card", {})
            
            return model_card if model_card else {}
            
        except Exception as e:
            print(f"Error collecting model card evidence: {e}")
            return {}
    
    async def _collect_human_oversight_evidence(self, model_id: str) -> Dict[str, Any]:
        """Collect human oversight evidence"""
        
        try:
            model_info = await self._get_model_info(model_id)
            oversight = model_info.get("human_oversight", {})
            
            return {
                "review_process": oversight.get("review_process_defined", False),
                "human_override_enabled": oversight.get("override_enabled", False),
                "escalation_defined": oversight.get("escalation_path", False),
                "operator_training": oversight.get("training_provided", False),
                "source": "fairmind_model_registry" if model_info else "not_available"
            }
            
        except Exception as e:
            print(f"Error collecting human oversight evidence: {e}")
            return {
                "review_process": False,
                "human_override_enabled": False,
                "escalation_defined": False,
                "operator_training": False,
                "source": "default"
            }
    
    # Helper methods to integrate with FairMind's existing services
    
    async def _get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Model registry record for this model.

        No model registry is wired into this collector, so nothing is known
        about the model and every check that depends on it reports missing
        evidence instead of an assumed pass.
        """
        return {}

    async def _get_dataset(self, dataset_id: Optional[str]) -> List[Dict[str, Any]]:
        """Dataset rows for this model. No dataset source is wired in."""
        return []

    async def _get_bias_test_results(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Stored bias test results for this model. No source is wired in."""
        return None

    async def _get_security_test_results(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Stored security test results for this model. No source is wired in."""
        return None

    async def _get_monitoring_data(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Monitoring data for this model. No source is wired in."""
        return None

    def _default_dataset_quality(self) -> Dict[str, Any]:
        """Default dataset quality metrics"""
        return {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0,
            "missing_rate": 1.0,
            "source": "default"
        }

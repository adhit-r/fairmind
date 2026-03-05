"""
Evidence Collection Service for AI Compliance
Implements automated and manual evidence collection similar to Vanta/PwC GRC tools
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import json
from pydantic import BaseModel


class EvidenceType(str, Enum):
    """Types of evidence that can be collected"""
    TEST_RESULT = "test_result"  # Pass/fail from automated checks
    DATASET = "dataset"  # Raw data with metadata
    DOCUMENT = "document"  # Uploaded files (policies, screenshots)
    AUDIT_TRAIL = "audit_trail"  # System logs
    MANUAL_ATTESTATION = "manual_attestation"  # Human verification
    TECHNICAL_SCAN = "technical_scan"  # Automated technical checks


class EvidenceStatus(str, Enum):
    """Status of collected evidence"""
    VALID = "valid"
    EXPIRED = "expired"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class Evidence(BaseModel):
    """Evidence model"""
    id: str
    type: EvidenceType
    control_id: str  # Which compliance control this supports
    framework: str  # EU AI Act, NIST, ISO, etc.
    collected_at: datetime
    expires_at: Optional[datetime] = None
    status: EvidenceStatus = EvidenceStatus.VALID
    
    # Evidence content
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    # Integrity
    hash: str
    source: str  # Where it came from (automated/manual/integration)
    
    # Audit
    collected_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    notes: Optional[str] = None


class TechnicalControl(BaseModel):
    """Technical control that can be automatically checked"""
    id: str
    name: str
    description: str
    category: str  # data_governance, model_security, system_monitoring, etc.
    check_function: str  # Name of function to run
    frequency: str  # continuous, daily, weekly, on_demand
    required_for: List[str]  # Which frameworks require this


class EvidenceCollectionService:
    """Service for collecting and managing compliance evidence"""
    
    def __init__(self):
        self.evidence_store: Dict[str, Evidence] = {}
        self.technical_controls = self._initialize_technical_controls()
    
    def _initialize_technical_controls(self) -> Dict[str, TechnicalControl]:
        """Initialize automated technical controls"""
        return {
            # Data Governance Controls
            "DG_001": TechnicalControl(
                id="DG_001",
                name="Dataset Quality Check",
                description="Verify dataset quality metrics (completeness, accuracy, consistency)",
                category="data_governance",
                check_function="check_dataset_quality",
                frequency="continuous",
                required_for=["eu_ai_act", "iso_42001", "nist_ai_rmf"]
            ),
            "DG_002": TechnicalControl(
                id="DG_002",
                name="Data Privacy Compliance",
                description="Check for PII handling, anonymization, consent tracking",
                category="data_governance",
                check_function="check_data_privacy",
                frequency="continuous",
                required_for=["eu_ai_act", "gdpr"]
            ),
            "DG_003": TechnicalControl(
                id="DG_003",
                name="Bias in Training Data",
                description="Detect statistical bias in training datasets",
                category="data_governance",
                check_function="check_training_data_bias",
                frequency="on_demand",
                required_for=["eu_ai_act", "nist_ai_rmf"]
            ),
            
            # Model Security Controls
            "MS_001": TechnicalControl(
                id="MS_001",
                name="Model Access Controls",
                description="Verify who can train, deploy, and access models",
                category="model_security",
                check_function="check_model_access_controls",
                frequency="daily",
                required_for=["eu_ai_act", "iso_42001"]
            ),
            "MS_002": TechnicalControl(
                id="MS_002",
                name="Adversarial Robustness",
                description="Test model resilience against adversarial attacks",
                category="model_security",
                check_function="check_adversarial_robustness",
                frequency="weekly",
                required_for=["eu_ai_act", "nist_ai_rmf"]
            ),
            "MS_003": TechnicalControl(
                id="MS_003",
                name="Model Version Control",
                description="Verify all models are versioned and tracked",
                category="model_security",
                check_function="check_model_versioning",
                frequency="continuous",
                required_for=["eu_ai_act", "iso_42001"]
            ),
            
            # System Monitoring Controls
            "SM_001": TechnicalControl(
                id="SM_001",
                name="Performance Drift Detection",
                description="Monitor for model performance degradation over time",
                category="system_monitoring",
                check_function="check_performance_drift",
                frequency="continuous",
                required_for=["eu_ai_act", "nist_ai_rmf"]
            ),
            "SM_002": TechnicalControl(
                id="SM_002",
                name="Fairness Metrics Monitoring",
                description="Continuous monitoring of fairness metrics in production",
                category="system_monitoring",
                check_function="check_fairness_metrics",
                frequency="continuous",
                required_for=["eu_ai_act", "nist_ai_rmf"]
            ),
            "SM_003": TechnicalControl(
                id="SM_003",
                name="Audit Logging",
                description="Verify all model predictions and decisions are logged",
                category="system_monitoring",
                check_function="check_audit_logging",
                frequency="continuous",
                required_for=["eu_ai_act", "iso_42001"]
            ),
            
            # Documentation Controls
            "DC_001": TechnicalControl(
                id="DC_001",
                name="Technical Documentation Completeness",
                description="Check if all required technical documentation exists",
                category="documentation",
                check_function="check_technical_documentation",
                frequency="weekly",
                required_for=["eu_ai_act", "iso_42001"]
            ),
            "DC_002": TechnicalControl(
                id="DC_002",
                name="Model Card Availability",
                description="Verify model cards exist with required information",
                category="documentation",
                check_function="check_model_cards",
                frequency="on_demand",
                required_for=["eu_ai_act", "nist_ai_rmf"]
            ),
            
            # Human Oversight Controls
            "HO_001": TechnicalControl(
                id="HO_001",
                name="Human-in-the-Loop Verification",
                description="Check if human oversight mechanisms are in place",
                category="human_oversight",
                check_function="check_human_oversight",
                frequency="weekly",
                required_for=["eu_ai_act"]
            ),
        }
    
    async def collect_evidence_for_control(
        self,
        control_id: str,
        system_data: Dict[str, Any],
        framework: str
    ) -> Evidence:
        """Collect evidence for a specific technical control"""
        
        control = self.technical_controls.get(control_id)
        if not control:
            raise ValueError(f"Unknown control: {control_id}")
        
        # Execute the check function
        check_result = await self._execute_check(control, system_data)
        
        # Create evidence record
        evidence_data = {
            "control_id": control_id,
            "control_name": control.name,
            "check_result": check_result,
            "system_data_snapshot": system_data,
        }
        
        # Calculate hash for integrity
        evidence_hash = hashlib.sha256(
            json.dumps(evidence_data, sort_keys=True).encode()
        ).hexdigest()
        
        evidence = Evidence(
            id=f"EV_{control_id}_{datetime.now().timestamp()}",
            type=EvidenceType.TEST_RESULT,
            control_id=control_id,
            framework=framework,
            collected_at=datetime.now(),
            status=EvidenceStatus.VALID,
            data=evidence_data,
            metadata={
                "control_category": control.category,
                "check_function": control.check_function,
                "automated": True
            },
            hash=evidence_hash,
            source="automated_check",
        )
        
        self.evidence_store[evidence.id] = evidence
        return evidence
    
    async def _execute_check(
        self,
        control: TechnicalControl,
        system_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a technical control check"""
        
        # Map check functions to actual implementations
        check_functions = {
            "check_dataset_quality": self._check_dataset_quality,
            "check_data_privacy": self._check_data_privacy,
            "check_training_data_bias": self._check_training_data_bias,
            "check_model_access_controls": self._check_model_access_controls,
            "check_adversarial_robustness": self._check_adversarial_robustness,
            "check_model_versioning": self._check_model_versioning,
            "check_performance_drift": self._check_performance_drift,
            "check_fairness_metrics": self._check_fairness_metrics,
            "check_audit_logging": self._check_audit_logging,
            "check_technical_documentation": self._check_technical_documentation,
            "check_model_cards": self._check_model_cards,
            "check_human_oversight": self._check_human_oversight,
        }
        
        check_fn = check_functions.get(control.check_function)
        if not check_fn:
            return {"status": "error", "message": f"Check function not implemented: {control.check_function}"}
        
        return await check_fn(system_data)
    
    # Technical Check Implementations
    
    async def _check_dataset_quality(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check dataset quality metrics"""
        # Look for dataset quality evidence
        dataset_quality = system_data.get("dataset_quality", {})
        
        checks = {
            "completeness": dataset_quality.get("completeness", 0) >= 0.95,
            "accuracy": dataset_quality.get("accuracy", 0) >= 0.90,
            "consistency": dataset_quality.get("consistency", 0) >= 0.95,
            "missing_values": dataset_quality.get("missing_rate", 1.0) <= 0.05,
        }
        
        passed = all(checks.values())
        
        return {
            "status": "pass" if passed else "fail",
            "checks": checks,
            "metrics": dataset_quality,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_data_privacy(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data privacy compliance"""
        privacy_controls = system_data.get("privacy_controls", {})
        
        checks = {
            "pii_detection": privacy_controls.get("pii_detected", False) == False or privacy_controls.get("pii_anonymized", False),
            "consent_tracking": privacy_controls.get("consent_tracked", False),
            "data_minimization": privacy_controls.get("data_minimization_applied", False),
            "retention_policy": privacy_controls.get("retention_policy_defined", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_training_data_bias(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for bias in training data"""
        bias_metrics = system_data.get("training_data_bias", {})
        
        # Check if bias analysis was performed
        analysis_performed = bool(bias_metrics)
        
        if not analysis_performed:
            return {
                "status": "fail",
                "message": "No bias analysis performed on training data",
                "timestamp": datetime.now().isoformat(),
            }
        
        # Check bias thresholds
        demographic_parity = bias_metrics.get("demographic_parity", 1.0)
        representation_balance = bias_metrics.get("representation_balance", 0.0)
        
        checks = {
            "bias_analysis_performed": True,
            "demographic_parity_acceptable": abs(1.0 - demographic_parity) <= 0.2,
            "representation_balanced": representation_balance >= 0.7,
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "metrics": bias_metrics,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_model_access_controls(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check model access controls"""
        access_controls = system_data.get("access_controls", {})
        
        checks = {
            "rbac_enabled": access_controls.get("rbac_enabled", False),
            "training_restricted": access_controls.get("training_role_required", False),
            "deployment_restricted": access_controls.get("deployment_role_required", False),
            "audit_logging": access_controls.get("access_logged", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_adversarial_robustness(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check adversarial robustness"""
        robustness_tests = system_data.get("adversarial_tests", {})
        
        if not robustness_tests:
            return {
                "status": "fail",
                "message": "No adversarial robustness testing performed",
                "timestamp": datetime.now().isoformat(),
            }
        
        checks = {
            "fgsm_tested": robustness_tests.get("fgsm_accuracy", 0) >= 0.7,
            "pgd_tested": robustness_tests.get("pgd_accuracy", 0) >= 0.6,
            "input_validation": robustness_tests.get("input_validation_enabled", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "metrics": robustness_tests,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_model_versioning(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check model version control"""
        versioning = system_data.get("model_versioning", {})
        
        checks = {
            "version_control_enabled": versioning.get("enabled", False),
            "git_tracked": versioning.get("git_repository", "") != "",
            "model_registry": versioning.get("registry_url", "") != "",
            "lineage_tracked": versioning.get("lineage_tracked", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_performance_drift(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for performance drift"""
        drift_metrics = system_data.get("performance_drift", {})
        
        checks = {
            "monitoring_enabled": drift_metrics.get("monitoring_enabled", False),
            "accuracy_stable": abs(drift_metrics.get("accuracy_change", 0)) <= 0.05,
            "alerts_configured": drift_metrics.get("alerts_configured", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "metrics": drift_metrics,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_fairness_metrics(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check fairness metrics monitoring"""
        fairness = system_data.get("fairness_monitoring", {})
        
        checks = {
            "monitoring_enabled": fairness.get("enabled", False),
            "metrics_tracked": len(fairness.get("metrics", [])) >= 3,
            "thresholds_defined": fairness.get("thresholds_defined", False),
            "alerts_configured": fairness.get("alerts_enabled", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_audit_logging(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check audit logging"""
        logging = system_data.get("audit_logging", {})
        
        checks = {
            "predictions_logged": logging.get("predictions_logged", False),
            "inputs_logged": logging.get("inputs_logged", False),
            "decisions_logged": logging.get("decisions_logged", False),
            "retention_policy": logging.get("retention_days", 0) >= 90,
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_technical_documentation(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check technical documentation completeness"""
        docs = system_data.get("documentation", {})
        
        required_docs = [
            "system_architecture",
            "data_flow_diagram",
            "risk_assessment",
            "testing_procedures",
            "deployment_guide",
        ]
        
        checks = {
            doc: docs.get(doc, {}).get("exists", False)
            for doc in required_docs
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "missing": [doc for doc, exists in checks.items() if not exists],
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_model_cards(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check model card availability"""
        model_card = system_data.get("model_card", {})
        
        required_sections = [
            "model_details",
            "intended_use",
            "factors",
            "metrics",
            "training_data",
            "evaluation_data",
            "ethical_considerations",
        ]
        
        checks = {
            section: section in model_card
            for section in required_sections
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "missing": [section for section, exists in checks.items() if not exists],
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _check_human_oversight(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check human oversight mechanisms"""
        oversight = system_data.get("human_oversight", {})
        
        checks = {
            "review_process_defined": oversight.get("review_process", False),
            "override_capability": oversight.get("human_override_enabled", False),
            "escalation_path": oversight.get("escalation_defined", False),
            "training_provided": oversight.get("operator_training", False),
        }
        
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def collect_all_evidence(
        self,
        system_data: Dict[str, Any],
        framework: str
    ) -> List[Evidence]:
        """Collect evidence for all applicable controls for a framework"""
        
        evidence_list = []
        
        # Find all controls required for this framework
        applicable_controls = [
            control for control in self.technical_controls.values()
            if framework in control.required_for
        ]
        
        for control in applicable_controls:
            try:
                evidence = await self.collect_evidence_for_control(
                    control.id,
                    system_data,
                    framework
                )
                evidence_list.append(evidence)
            except Exception as e:
                # Log error but continue collecting other evidence
                print(f"Error collecting evidence for {control.id}: {e}")
        
        return evidence_list
    
    def get_compliance_score(self, evidence_list: List[Evidence]) -> float:
        """Calculate compliance score based on collected evidence"""
        if not evidence_list:
            return 0.0
        
        passed = sum(
            1 for e in evidence_list
            if e.data.get("check_result", {}).get("status") == "pass"
        )
        
        return (passed / len(evidence_list)) * 100
    
    def get_gaps(self, evidence_list: List[Evidence]) -> List[Dict[str, Any]]:
        """Identify compliance gaps from evidence"""
        gaps = []
        
        for evidence in evidence_list:
            check_result = evidence.data.get("check_result", {})
            if check_result.get("status") != "pass":
                control = self.technical_controls.get(evidence.control_id)
                gaps.append({
                    "control_id": evidence.control_id,
                    "control_name": control.name if control else "Unknown",
                    "category": control.category if control else "Unknown",
                    "failed_checks": [
                        check_name for check_name, passed in check_result.get("checks", {}).items()
                        if not passed
                    ],
                    "message": check_result.get("message", ""),
                    "evidence_id": evidence.id,
                })
        
        return gaps

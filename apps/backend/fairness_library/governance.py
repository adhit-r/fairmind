"""
Automated Governance Gates and Policy Engine
Enforces compliance and policy "by default" with automated checks.
"""

import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PolicyType(Enum):
    FAIRNESS_THRESHOLD = "fairness_threshold"
    BIAS_DETECTION = "bias_detection"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_QUALITY = "data_quality"
    COMPLIANCE = "compliance"

class ComplianceStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"

@dataclass
class PolicyRule:
    """Policy rule definition"""
    rule_id: str
    name: str
    description: str
    policy_type: PolicyType
    metric_name: str
    threshold: float
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    severity: str  # "critical", "high", "medium", "low"
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class ComplianceResult:
    """Result of a compliance check"""
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    actual_value: float
    threshold: float
    operator: str
    message: str
    timestamp: datetime
    details: Dict[str, Any]

class GovernanceGate:
    """Automated governance gate for enforcing fairness policies"""
    
    def __init__(self, policies_path: str = "policies"):
        self.policies_path = Path(policies_path)
        self.policies_path.mkdir(parents=True, exist_ok=True)
        self.policy_engine = PolicyEngine()
        self.compliance_checker = ComplianceChecker()
        self.audit_logger = AuditLogger()
    
    def check_model_compliance(
        self,
        model_id: str,
        fairness_metrics: Dict[str, Any],
        bias_detection_results: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Check if a model meets all governance requirements"""
        try:
            # Load applicable policies
            policies = self.policy_engine.load_policies()
            
            # Run compliance checks
            compliance_results = []
            overall_status = ComplianceStatus.PASSED
            
            for policy in policies:
                if policy.enabled:
                    result = self.compliance_checker.check_policy(
                        policy, fairness_metrics, bias_detection_results, performance_metrics
                    )
                    compliance_results.append(result)
                    
                    # Update overall status
                    if result.status == ComplianceStatus.FAILED:
                        overall_status = ComplianceStatus.FAILED
                    elif result.status == ComplianceStatus.WARNING and overall_status == ComplianceStatus.PASSED:
                        overall_status = ComplianceStatus.WARNING
            
            # Log audit trail
            audit_entry = {
                "model_id": model_id,
                "timestamp": datetime.now(),
                "overall_status": overall_status.value,
                "compliance_results": [asdict(result) for result in compliance_results],
                "policies_checked": len(policies)
            }
            self.audit_logger.log_compliance_check(audit_entry)
            
            return {
                "model_id": model_id,
                "overall_status": overall_status.value,
                "compliance_results": [asdict(result) for result in compliance_results],
                "can_deploy": overall_status != ComplianceStatus.FAILED,
                "requires_review": overall_status == ComplianceStatus.WARNING,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking model compliance: {e}")
            raise
    
    def enforce_deployment_gate(
        self,
        model_id: str,
        deployment_stage: str,
        fairness_metrics: Dict[str, Any],
        bias_detection_results: Dict[str, Any]
    ) -> bool:
        """Enforce deployment gate - prevent deployment if compliance fails"""
        try:
            compliance_result = self.check_model_compliance(
                model_id, fairness_metrics, bias_detection_results, {}
            )
            
            if not compliance_result["can_deploy"]:
                logger.warning(f"Deployment blocked for model {model_id}: Compliance check failed")
                return False
            
            if compliance_result["requires_review"]:
                logger.info(f"Deployment requires review for model {model_id}: Warning status")
                # In a real implementation, this would trigger a human review workflow
                return True  # Allow with review requirement
            
            logger.info(f"Deployment approved for model {model_id}: All checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Error enforcing deployment gate: {e}")
            return False

class PolicyEngine:
    """Policy engine for managing and evaluating fairness policies"""
    
    def __init__(self, policies_path: str = "policies"):
        self.policies_path = Path(policies_path)
        self.policies_path.mkdir(parents=True, exist_ok=True)
        self.default_policies = self._create_default_policies()
    
    def load_policies(self) -> List[PolicyRule]:
        """Load all policies from storage"""
        policies = []
        
        # Load default policies
        policies.extend(self.default_policies)
        
        # Load custom policies from files
        for policy_file in self.policies_path.glob("*.yaml"):
            try:
                with open(policy_file, 'r') as f:
                    policy_data = yaml.safe_load(f)
                    policy = PolicyRule(**policy_data)
                    policies.append(policy)
            except Exception as e:
                logger.error(f"Error loading policy from {policy_file}: {e}")
        
        return policies
    
    def create_policy(self, policy_rule: PolicyRule) -> str:
        """Create a new policy rule"""
        try:
            # Set timestamps
            now = datetime.now()
            policy_rule.created_at = now
            policy_rule.updated_at = now
            
            # Save policy to file
            policy_file = self.policies_path / f"{policy_rule.rule_id}.yaml"
            with open(policy_file, 'w') as f:
                yaml.dump(asdict(policy_rule), f, default_flow_style=False)
            
            logger.info(f"Created policy: {policy_rule.name}")
            return policy_rule.rule_id
            
        except Exception as e:
            logger.error(f"Error creating policy: {e}")
            raise
    
    def update_policy(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing policy rule"""
        try:
            policy_file = self.policies_path / f"{rule_id}.yaml"
            if not policy_file.exists():
                raise ValueError(f"Policy {rule_id} not found")
            
            # Load existing policy
            with open(policy_file, 'r') as f:
                policy_data = yaml.safe_load(f)
            
            # Update fields
            for key, value in updates.items():
                if key in policy_data:
                    policy_data[key] = value
            
            # Update timestamp
            policy_data['updated_at'] = datetime.now()
            
            # Save updated policy
            with open(policy_file, 'w') as f:
                yaml.dump(policy_data, f, default_flow_style=False)
            
            logger.info(f"Updated policy: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating policy: {e}")
            return False
    
    def _create_default_policies(self) -> List[PolicyRule]:
        """Create default fairness policies"""
        now = datetime.now()
        
        default_policies = [
            PolicyRule(
                rule_id="demographic_parity_threshold",
                name="Demographic Parity Threshold",
                description="Ensure demographic parity difference is within acceptable limits",
                policy_type=PolicyType.FAIRNESS_THRESHOLD,
                metric_name="demographic_parity_difference",
                threshold=0.05,
                operator="<=",
                severity="critical",
                enabled=True,
                created_at=now,
                updated_at=now
            ),
            PolicyRule(
                rule_id="equalized_odds_threshold",
                name="Equalized Odds Threshold",
                description="Ensure equalized odds difference is within acceptable limits",
                policy_type=PolicyType.FAIRNESS_THRESHOLD,
                metric_name="equalized_odds_difference",
                threshold=0.05,
                operator="<=",
                severity="critical",
                enabled=True,
                created_at=now,
                updated_at=now
            ),
            PolicyRule(
                rule_id="weat_bias_threshold",
                name="WEAT Bias Threshold",
                description="Ensure WEAT score for embedding bias is within acceptable limits",
                policy_type=PolicyType.BIAS_DETECTION,
                metric_name="weat_score",
                threshold=0.1,
                operator="<=",
                severity="high",
                enabled=True,
                created_at=now,
                updated_at=now
            ),
            PolicyRule(
                rule_id="performance_degradation",
                name="Performance Degradation Limit",
                description="Ensure model performance doesn't degrade significantly",
                policy_type=PolicyType.PERFORMANCE_DEGRADATION,
                metric_name="accuracy_degradation",
                threshold=0.02,
                operator="<=",
                severity="medium",
                enabled=True,
                created_at=now,
                updated_at=now
            )
        ]
        
        return default_policies

class ComplianceChecker:
    """Compliance checker for evaluating policies against model metrics"""
    
    def check_policy(
        self,
        policy: PolicyRule,
        fairness_metrics: Dict[str, Any],
        bias_detection_results: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ) -> ComplianceResult:
        """Check if a policy is satisfied"""
        try:
            # Get the actual value for the metric
            actual_value = self._extract_metric_value(
                policy.metric_name, fairness_metrics, bias_detection_results, performance_metrics
            )
            
            # Evaluate the policy
            is_compliant = self._evaluate_policy(actual_value, policy.threshold, policy.operator)
            
            # Determine status
            if is_compliant:
                status = ComplianceStatus.PASSED
                message = f"Policy {policy.name} passed: {actual_value} {policy.operator} {policy.threshold}"
            else:
                if policy.severity == "critical":
                    status = ComplianceStatus.FAILED
                else:
                    status = ComplianceStatus.WARNING
                message = f"Policy {policy.name} failed: {actual_value} {policy.operator} {policy.threshold}"
            
            return ComplianceResult(
                rule_id=policy.rule_id,
                rule_name=policy.name,
                status=status,
                actual_value=actual_value,
                threshold=policy.threshold,
                operator=policy.operator,
                message=message,
                timestamp=datetime.now(),
                details={
                    "policy_type": policy.policy_type.value,
                    "severity": policy.severity,
                    "description": policy.description
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking policy {policy.rule_id}: {e}")
            return ComplianceResult(
                rule_id=policy.rule_id,
                rule_name=policy.name,
                status=ComplianceStatus.FAILED,
                actual_value=0.0,
                threshold=policy.threshold,
                operator=policy.operator,
                message=f"Error checking policy: {e}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def _extract_metric_value(
        self,
        metric_name: str,
        fairness_metrics: Dict[str, Any],
        bias_detection_results: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ) -> float:
        """Extract the actual value for a given metric"""
        try:
            # Check fairness metrics
            if metric_name in fairness_metrics:
                metric_data = fairness_metrics[metric_name]
                if isinstance(metric_data, dict) and 'value' in metric_data:
                    return metric_data['value']
                elif isinstance(metric_data, (int, float)):
                    return float(metric_data)
            
            # Check bias detection results
            if metric_name in bias_detection_results:
                bias_data = bias_detection_results[metric_name]
                if isinstance(bias_data, dict) and 'score' in bias_data:
                    return bias_data['score']
                elif isinstance(bias_data, (int, float)):
                    return float(bias_data)
            
            # Check performance metrics
            if metric_name in performance_metrics:
                return float(performance_metrics[metric_name])
            
            # Default value if metric not found
            logger.warning(f"Metric {metric_name} not found in any data source")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting metric value for {metric_name}: {e}")
            return 0.0
    
    def _evaluate_policy(self, actual_value: float, threshold: float, operator: str) -> bool:
        """Evaluate if a policy is satisfied"""
        try:
            if operator == ">":
                return actual_value > threshold
            elif operator == "<":
                return actual_value < threshold
            elif operator == ">=":
                return actual_value >= threshold
            elif operator == "<=":
                return actual_value <= threshold
            elif operator == "==":
                return abs(actual_value - threshold) < 1e-6
            elif operator == "!=":
                return abs(actual_value - threshold) >= 1e-6
            else:
                logger.error(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating policy: {e}")
            return False

class AuditLogger:
    """Audit logger for tracking all governance activities"""
    
    def __init__(self, audit_path: str = "audit_logs"):
        self.audit_path = Path(audit_path)
        self.audit_path.mkdir(parents=True, exist_ok=True)
    
    def log_compliance_check(self, audit_entry: Dict[str, Any]) -> None:
        """Log a compliance check audit entry"""
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")
            
            # Create audit file for the date
            audit_file = self.audit_path / f"compliance_{date_str}.jsonl"
            
            # Add timestamp to audit entry
            audit_entry["audit_timestamp"] = timestamp.isoformat()
            
            # Append to audit file
            with open(audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            logger.info(f"Logged compliance check audit: {audit_entry.get('model_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error logging compliance check: {e}")
    
    def log_policy_change(self, change_type: str, policy_id: str, user: str, details: Dict[str, Any]) -> None:
        """Log a policy change audit entry"""
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")
            
            audit_file = self.audit_path / f"policy_changes_{date_str}.jsonl"
            
            audit_entry = {
                "timestamp": timestamp.isoformat(),
                "change_type": change_type,
                "policy_id": policy_id,
                "user": user,
                "details": details
            }
            
            with open(audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            logger.info(f"Logged policy change: {change_type} for {policy_id}")
            
        except Exception as e:
            logger.error(f"Error logging policy change: {e}")
    
    def get_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail with optional filtering"""
        try:
            audit_entries = []
            
            # Determine date range
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            # Load audit files in date range
            current_date = start_date.date()
            end_date_obj = end_date.date()
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Load compliance checks
                compliance_file = self.audit_path / f"compliance_{date_str}.jsonl"
                if compliance_file.exists():
                    with open(compliance_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line.strip())
                            if model_id is None or entry.get('model_id') == model_id:
                                audit_entries.append(entry)
                
                # Load policy changes
                policy_file = self.audit_path / f"policy_changes_{date_str}.jsonl"
                if policy_file.exists():
                    with open(policy_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line.strip())
                            audit_entries.append(entry)
                
                current_date += timedelta(days=1)
            
            # Sort by timestamp
            audit_entries.sort(key=lambda x: x.get('timestamp', ''))
            
            return audit_entries
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {e}")
            return []

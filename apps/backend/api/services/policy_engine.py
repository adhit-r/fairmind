"""
Policy as Code Engine for AI Governance
Implements OPA/Rego-based policy evaluation and custom DSL support
"""

import json
import yaml
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PolicyRule:
    """Represents a single policy rule"""
    id: str
    name: str
    description: str
    category: str
    severity: str  # critical, high, medium, low
    framework: str  # nist, eu_ai_act, iso, custom
    rule_type: str  # rego, dsl, custom
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class PolicyEvaluation:
    """Result of policy evaluation"""
    rule_id: str
    passed: bool
    score: float
    message: str
    evidence: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class ComplianceResult:
    """Overall compliance result for a system"""
    system_id: str
    framework: str
    overall_score: float
    passed_rules: int
    failed_rules: int
    total_rules: int
    evaluations: List[PolicyEvaluation]
    risk_level: str
    timestamp: datetime

class PolicyEngine:
    """Core policy evaluation engine"""
    
    def __init__(self, policies_dir: str = "policies"):
        self.policies_dir = Path(policies_dir)
        self.policies_dir.mkdir(exist_ok=True)
        self.rules: Dict[str, PolicyRule] = {}
        self.frameworks = {
            "nist_ai_rmf": self._load_nist_framework(),
            "eu_ai_act": self._load_eu_ai_act_framework(),
            "iso_42001": self._load_iso_framework(),
            "oecd_ai_principles": self._load_oecd_framework()
        }
        self._load_policies()
    
    def _load_nist_framework(self) -> Dict[str, Any]:
        """Load NIST AI RMF framework policies"""
        return {
            "govern": {
                "govern_1": "Establish AI governance framework",
                "govern_2": "Define AI risk management roles",
                "govern_3": "Establish AI risk management processes"
            },
            "map": {
                "map_1": "Identify AI system context",
                "map_2": "Identify AI system components",
                "map_3": "Identify AI system risks"
            },
            "measure": {
                "measure_1": "Implement AI system testing",
                "measure_2": "Implement AI system monitoring",
                "measure_3": "Implement AI system evaluation"
            },
            "manage": {
                "manage_1": "Implement AI system risk responses",
                "manage_2": "Implement AI system risk monitoring",
                "manage_3": "Implement AI system risk reporting"
            }
        }
    
    def _load_eu_ai_act_framework(self) -> Dict[str, Any]:
        """Load EU AI Act framework policies"""
        return {
            "prohibited": {
                "prohibited_1": "No social scoring systems",
                "prohibited_2": "No manipulative AI systems",
                "prohibited_3": "No exploitation of vulnerabilities"
            },
            "high_risk": {
                "high_risk_1": "Risk management system required",
                "high_risk_2": "Data governance required",
                "high_risk_3": "Technical documentation required",
                "high_risk_4": "Record keeping required",
                "high_risk_5": "Transparency and provision of information required",
                "high_risk_6": "Human oversight required",
                "high_risk_7": "Accuracy, robustness and cybersecurity required"
            },
            "limited_risk": {
                "limited_risk_1": "Transparency obligations",
                "limited_risk_2": "User awareness requirements"
            },
            "minimal_risk": {
                "minimal_risk_1": "No specific requirements"
            }
        }
    
    def _load_iso_framework(self) -> Dict[str, Any]:
        """Load ISO/IEC 42001 framework policies"""
        return {
            "context": {
                "context_1": "Understanding organization and context",
                "context_2": "Understanding needs and expectations of interested parties",
                "context_3": "Determining scope of AI management system"
            },
            "leadership": {
                "leadership_1": "Leadership and commitment",
                "leadership_2": "Policy",
                "leadership_3": "Organizational roles, responsibilities and authorities"
            },
            "planning": {
                "planning_1": "Actions to address risks and opportunities",
                "planning_2": "AI management system objectives and planning"
            },
            "support": {
                "support_1": "Resources",
                "support_2": "Competence",
                "support_3": "Awareness",
                "support_4": "Communication",
                "support_5": "Documented information"
            },
            "operation": {
                "operation_1": "Operational planning and control",
                "operation_2": "AI system development and deployment",
                "operation_3": "AI system operation and monitoring"
            },
            "performance": {
                "performance_1": "Monitoring, measurement, analysis and evaluation",
                "performance_2": "Internal audit",
                "performance_3": "Management review"
            },
            "improvement": {
                "improvement_1": "Nonconformity and corrective action",
                "improvement_2": "Continual improvement"
            }
        }
    
    def _load_oecd_framework(self) -> Dict[str, Any]:
        """Load OECD AI Principles framework policies"""
        return {
            "inclusive_growth": {
                "inclusive_1": "AI should benefit people and the planet",
                "inclusive_2": "AI should be designed to be inclusive"
            },
            "human_centered": {
                "human_1": "AI should be designed to augment human capabilities",
                "human_2": "AI should respect human autonomy"
            },
            "transparency": {
                "transparency_1": "AI systems should be transparent",
                "transparency_2": "AI systems should be explainable"
            },
            "robustness": {
                "robustness_1": "AI systems should be robust and secure",
                "robustness_2": "AI systems should be reliable"
            },
            "accountability": {
                "accountability_1": "AI systems should be accountable",
                "accountability_2": "AI systems should be auditable"
            }
        }
    
    def _load_policies(self):
        """Load all policy files from the policies directory"""
        for policy_file in self.policies_dir.glob("*.yaml"):
            try:
                with open(policy_file, 'r') as f:
                    policy_data = yaml.safe_load(f)
                    self._parse_policy_file(policy_data)
            except Exception as e:
                logger.error(f"Error loading policy file {policy_file}: {e}")
    
    def _parse_policy_file(self, policy_data: Dict[str, Any]):
        """Parse a policy file and create PolicyRule objects"""
        for rule_data in policy_data.get('rules', []):
            rule = PolicyRule(
                id=rule_data['id'],
                name=rule_data['name'],
                description=rule_data['description'],
                category=rule_data['category'],
                severity=rule_data['severity'],
                framework=rule_data['framework'],
                rule_type=rule_data['rule_type'],
                content=rule_data['content'],
                metadata=rule_data.get('metadata', {}),
                created_at=datetime.fromisoformat(rule_data['created_at']),
                updated_at=datetime.fromisoformat(rule_data['updated_at'])
            )
            self.rules[rule.id] = rule
    
    def evaluate_rego_policy(self, rule: PolicyRule, context: Dict[str, Any]) -> PolicyEvaluation:
        """Evaluate a Rego policy rule"""
        try:
            # Simple Rego evaluation (in production, use OPA server)
            # This is a simplified implementation
            if rule.rule_type == "rego":
                # Parse Rego content and evaluate
                passed = self._evaluate_rego_content(rule.content, context)
                score = 1.0 if passed else 0.0
                message = "Policy passed" if passed else "Policy failed"
            else:
                passed = False
                score = 0.0
                message = "Invalid rule type for Rego evaluation"
            
            return PolicyEvaluation(
                rule_id=rule.id,
                passed=passed,
                score=score,
                message=message,
                evidence=context,
                recommendations=self._generate_recommendations(rule, passed),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error evaluating Rego policy {rule.id}: {e}")
            return PolicyEvaluation(
                rule_id=rule.id,
                passed=False,
                score=0.0,
                message=f"Evaluation error: {str(e)}",
                evidence=context,
                recommendations=["Fix policy evaluation error"],
                timestamp=datetime.now()
            )
    
    def evaluate_dsl_policy(self, rule: PolicyRule, context: Dict[str, Any]) -> PolicyEvaluation:
        """Evaluate a custom DSL policy rule"""
        try:
            # Custom DSL evaluation
            if rule.rule_type == "dsl":
                passed = self._evaluate_dsl_content(rule.content, context)
                score = 1.0 if passed else 0.0
                message = "Policy passed" if passed else "Policy failed"
            else:
                passed = False
                score = 0.0
                message = "Invalid rule type for DSL evaluation"
            
            return PolicyEvaluation(
                rule_id=rule.id,
                passed=passed,
                score=score,
                message=message,
                evidence=context,
                recommendations=self._generate_recommendations(rule, passed),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error evaluating DSL policy {rule.id}: {e}")
            return PolicyEvaluation(
                rule_id=rule.id,
                passed=False,
                score=0.0,
                message=f"Evaluation error: {str(e)}",
                evidence=context,
                recommendations=["Fix policy evaluation error"],
                timestamp=datetime.now()
            )
    
    def _evaluate_rego_content(self, content: str, context: Dict[str, Any]) -> bool:
        """Simplified Rego evaluation (production should use OPA server)"""
        # This is a placeholder - in production, you'd use the OPA Python SDK
        # or make HTTP calls to an OPA server
        
        # Simple pattern matching for demonstration
        if "allow" in content.lower():
            return True
        if "deny" in content.lower():
            return False
        
        # Check for specific conditions
        if "bias_detection" in content and context.get("has_bias_detection", False):
            return True
        if "explainability" in content and context.get("has_explainability", False):
            return True
        
        return False
    
    def _evaluate_dsl_content(self, content: str, context: Dict[str, Any]) -> bool:
        """Evaluate custom DSL content"""
        # Simple DSL evaluation
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse DSL conditions
            if ':' in line:
                condition, expected = line.split(':', 1)
                condition = condition.strip()
                expected = expected.strip()
                
                # Evaluate condition
                actual_value = self._get_context_value(context, condition)
                if str(actual_value).lower() != expected.lower():
                    return False
        
        return True
    
    def _get_context_value(self, context: Dict[str, Any], path: str) -> Any:
        """Get value from context using dot notation"""
        keys = path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _generate_recommendations(self, rule: PolicyRule, passed: bool) -> List[str]:
        """Generate recommendations based on rule evaluation"""
        if passed:
            return ["Continue monitoring compliance"]
        
        recommendations = []
        
        if rule.framework == "nist_ai_rmf":
            if "govern" in rule.category:
                recommendations.append("Establish AI governance framework")
            elif "map" in rule.category:
                recommendations.append("Conduct AI system risk mapping")
            elif "measure" in rule.category:
                recommendations.append("Implement AI system measurement")
            elif "manage" in rule.category:
                recommendations.append("Implement AI risk management")
        
        elif rule.framework == "eu_ai_act":
            if rule.category == "high_risk":
                recommendations.append("Implement high-risk AI system requirements")
            elif rule.category == "prohibited":
                recommendations.append("Remove prohibited AI practices")
        
        return recommendations
    
    def evaluate_system_compliance(self, system_id: str, framework: str, context: Dict[str, Any]) -> ComplianceResult:
        """Evaluate overall system compliance for a framework"""
        evaluations = []
        passed_rules = 0
        failed_rules = 0
        
        # Get rules for the framework
        framework_rules = [rule for rule in self.rules.values() if rule.framework == framework]
        
        for rule in framework_rules:
            if rule.rule_type == "rego":
                evaluation = self.evaluate_rego_policy(rule, context)
            elif rule.rule_type == "dsl":
                evaluation = self.evaluate_dsl_policy(rule, context)
            else:
                # Default evaluation
                evaluation = PolicyEvaluation(
                    rule_id=rule.id,
                    passed=False,
                    score=0.0,
                    message="Unsupported rule type",
                    evidence=context,
                    recommendations=["Update rule type"],
                    timestamp=datetime.now()
                )
            
            evaluations.append(evaluation)
            
            if evaluation.passed:
                passed_rules += 1
            else:
                failed_rules += 1
        
        total_rules = len(framework_rules)
        overall_score = (passed_rules / total_rules * 100) if total_rules > 0 else 0
        
        # Determine risk level
        if overall_score >= 90:
            risk_level = "low"
        elif overall_score >= 70:
            risk_level = "medium"
        elif overall_score >= 50:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return ComplianceResult(
            system_id=system_id,
            framework=framework,
            overall_score=overall_score,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            total_rules=total_rules,
            evaluations=evaluations,
            risk_level=risk_level,
            timestamp=datetime.now()
        )
    
    def create_policy_rule(self, rule_data: Dict[str, Any]) -> PolicyRule:
        """Create a new policy rule"""
        rule = PolicyRule(
            id=rule_data['id'],
            name=rule_data['name'],
            description=rule_data['description'],
            category=rule_data['category'],
            severity=rule_data['severity'],
            framework=rule_data['framework'],
            rule_type=rule_data['rule_type'],
            content=rule_data['content'],
            metadata=rule_data.get('metadata', {}),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.rules[rule.id] = rule
        self._save_policy_rule(rule)
        
        return rule
    
    def _save_policy_rule(self, rule: PolicyRule):
        """Save a policy rule to file"""
        policy_file = self.policies_dir / f"{rule.framework}.yaml"
        
        # Load existing policies or create new structure
        if policy_file.exists():
            with open(policy_file, 'r') as f:
                policy_data = yaml.safe_load(f) or {'rules': []}
        else:
            policy_data = {'rules': []}
        
        # Add or update rule
        rule_dict = asdict(rule)
        rule_dict['created_at'] = rule.created_at.isoformat()
        rule_dict['updated_at'] = rule.updated_at.isoformat()
        
        # Find existing rule and update or add new
        existing_rule_index = None
        for i, existing_rule in enumerate(policy_data['rules']):
            if existing_rule['id'] == rule.id:
                existing_rule_index = i
                break
        
        if existing_rule_index is not None:
            policy_data['rules'][existing_rule_index] = rule_dict
        else:
            policy_data['rules'].append(rule_dict)
        
        # Save to file
        with open(policy_file, 'w') as f:
            yaml.dump(policy_data, f, default_flow_style=False)
    
    def get_framework_mapping(self, rule_id: str) -> Dict[str, List[str]]:
        """Get framework mappings for a rule"""
        if rule_id not in self.rules:
            return {}
        
        rule = self.rules[rule_id]
        mappings = {}
        
        # Map to all applicable frameworks
        for framework_name, framework_data in self.frameworks.items():
            applicable_categories = []
            
            for category, controls in framework_data.items():
                if rule.category in controls or rule.name in controls:
                    applicable_categories.append(category)
            
            if applicable_categories:
                mappings[framework_name] = applicable_categories
        
        return mappings
    
    def get_all_rules(self) -> List[PolicyRule]:
        """Get all policy rules"""
        return list(self.rules.values())
    
    def get_rules_by_framework(self, framework: str) -> List[PolicyRule]:
        """Get rules for a specific framework"""
        return [rule for rule in self.rules.values() if rule.framework == framework]
    
    def delete_policy_rule(self, rule_id: str) -> bool:
        """Delete a policy rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            # Also remove from file
            self._remove_rule_from_file(rule_id)
            return True
        return False
    
    def _remove_rule_from_file(self, rule_id: str):
        """Remove a rule from its policy file"""
        for policy_file in self.policies_dir.glob("*.yaml"):
            try:
                with open(policy_file, 'r') as f:
                    policy_data = yaml.safe_load(f)
                
                if policy_data and 'rules' in policy_data:
                    policy_data['rules'] = [
                        rule for rule in policy_data['rules'] 
                        if rule['id'] != rule_id
                    ]
                    
                    with open(policy_file, 'w') as f:
                        yaml.dump(policy_data, f, default_flow_style=False)
            except Exception as e:
                logger.error(f"Error removing rule from {policy_file}: {e}")


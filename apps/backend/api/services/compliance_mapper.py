"""
Regulatory Compliance Mapping Engine
Maps policies to multiple regulatory frameworks and provides automated compliance assessment
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RiskCategory(Enum):
    PROHIBITED = "prohibited"
    HIGH_RISK = "high_risk"
    LIMITED_RISK = "limited_risk"
    MINIMAL_RISK = "minimal_risk"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"

@dataclass
class RegulatoryControl:
    """Represents a regulatory control/requirement"""
    id: str
    name: str
    description: str
    framework: str
    category: str
    subcategory: Optional[str]
    risk_level: RiskCategory
    requirements: List[str]
    evidence_types: List[str]
    assessment_criteria: List[str]
    related_controls: List[str]
    metadata: Dict[str, Any]

@dataclass
class ComplianceMapping:
    """Maps a policy rule to regulatory controls"""
    policy_rule_id: str
    regulatory_controls: List[str]
    mapping_confidence: float
    mapping_type: str  # direct, partial, inferred
    evidence: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class FrameworkAssessment:
    """Assessment result for a regulatory framework"""
    framework: str
    system_id: str
    overall_status: ComplianceStatus
    compliance_score: float
    risk_assessment: Dict[str, Any]
    control_assessments: Dict[str, ComplianceStatus]
    gaps: List[str]
    recommendations: List[str]
    evidence_summary: Dict[str, Any]
    assessment_date: datetime

class ComplianceMapper:
    """Maps policies to regulatory frameworks and assesses compliance"""
    
    def __init__(self):
        self.regulatory_frameworks = self._initialize_frameworks()
        self.compliance_mappings: Dict[str, ComplianceMapping] = {}
        self.assessment_history: List[FrameworkAssessment] = []
    
    def _initialize_frameworks(self) -> Dict[str, Dict[str, RegulatoryControl]]:
        """Initialize all regulatory frameworks with their controls"""
        frameworks = {}
        
        # NIST AI RMF
        frameworks["nist_ai_rmf"] = self._load_nist_controls()
        
        # EU AI Act
        frameworks["eu_ai_act"] = self._load_eu_ai_act_controls()
        
        # ISO/IEC 42001
        frameworks["iso_42001"] = self._load_iso_controls()
        
        # OECD AI Principles
        frameworks["oecd_ai_principles"] = self._load_oecd_controls()
        
        # Local regulations (extensible)
        frameworks["local_regulations"] = self._load_local_regulations()
        
        return frameworks
    
    def _load_nist_controls(self) -> Dict[str, RegulatoryControl]:
        """Load NIST AI RMF controls"""
        controls = {}
        
        # Govern function controls
        controls["govern_1"] = RegulatoryControl(
            id="govern_1",
            name="AI Governance Framework",
            description="Establish and maintain an AI governance framework",
            framework="nist_ai_rmf",
            category="govern",
            subcategory="governance_framework",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Define AI governance structure",
                "Establish AI governance roles and responsibilities",
                "Create AI governance policies and procedures",
                "Implement AI governance oversight mechanisms"
            ],
            evidence_types=["governance_documents", "role_definitions", "policy_documents"],
            assessment_criteria=[
                "Governance framework is documented",
                "Roles and responsibilities are clearly defined",
                "Policies are implemented and communicated",
                "Oversight mechanisms are operational"
            ],
            related_controls=["govern_2", "govern_3"],
            metadata={"priority": "high", "implementation_effort": "medium"}
        )
        
        controls["govern_2"] = RegulatoryControl(
            id="govern_2",
            name="AI Risk Management Roles",
            description="Define and assign AI risk management roles",
            framework="nist_ai_rmf",
            category="govern",
            subcategory="risk_management_roles",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Assign AI risk management responsibilities",
                "Define AI risk management authorities",
                "Establish AI risk management reporting lines",
                "Ensure AI risk management competency"
            ],
            evidence_types=["role_descriptions", "responsibility_matrices", "competency_assessments"],
            assessment_criteria=[
                "Risk management roles are clearly defined",
                "Responsibilities are assigned and documented",
                "Reporting lines are established",
                "Competency requirements are met"
            ],
            related_controls=["govern_1", "govern_3"],
            metadata={"priority": "high", "implementation_effort": "low"}
        )
        
        # Map function controls
        controls["map_1"] = RegulatoryControl(
            id="map_1",
            name="AI System Context",
            description="Identify and document AI system context",
            framework="nist_ai_rmf",
            category="map",
            subcategory="system_context",
            risk_level=RiskCategory.MEDIUM_RISK,
            requirements=[
                "Document AI system purpose and scope",
                "Identify AI system stakeholders",
                "Define AI system boundaries",
                "Document AI system dependencies"
            ],
            evidence_types=["system_documentation", "stakeholder_analysis", "dependency_maps"],
            assessment_criteria=[
                "System context is documented",
                "Stakeholders are identified",
                "System boundaries are defined",
                "Dependencies are mapped"
            ],
            related_controls=["map_2", "map_3"],
            metadata={"priority": "medium", "implementation_effort": "medium"}
        )
        
        # Measure function controls
        controls["measure_1"] = RegulatoryControl(
            id="measure_1",
            name="AI System Testing",
            description="Implement comprehensive AI system testing",
            framework="nist_ai_rmf",
            category="measure",
            subcategory="system_testing",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Implement functional testing",
                "Implement performance testing",
                "Implement security testing",
                "Implement bias and fairness testing"
            ],
            evidence_types=["test_plans", "test_results", "test_reports"],
            assessment_criteria=[
                "Testing is comprehensive",
                "Test results are documented",
                "Issues are tracked and resolved",
                "Testing is automated where possible"
            ],
            related_controls=["measure_2", "measure_3"],
            metadata={"priority": "high", "implementation_effort": "high"}
        )
        
        # Manage function controls
        controls["manage_1"] = RegulatoryControl(
            id="manage_1",
            name="AI Risk Response",
            description="Implement AI risk response mechanisms",
            framework="nist_ai_rmf",
            category="manage",
            subcategory="risk_response",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Implement risk mitigation strategies",
                "Establish incident response procedures",
                "Create risk escalation processes",
                "Implement risk monitoring mechanisms"
            ],
            evidence_types=["risk_response_plans", "incident_procedures", "escalation_matrices"],
            assessment_criteria=[
                "Risk responses are defined",
                "Incident procedures are documented",
                "Escalation processes are clear",
                "Monitoring is implemented"
            ],
            related_controls=["manage_2", "manage_3"],
            metadata={"priority": "high", "implementation_effort": "medium"}
        )
        
        return controls
    
    def _load_eu_ai_act_controls(self) -> Dict[str, RegulatoryControl]:
        """Load EU AI Act controls"""
        controls = {}
        
        # Prohibited AI practices
        controls["prohibited_1"] = RegulatoryControl(
            id="prohibited_1",
            name="No Social Scoring",
            description="Prohibition of social scoring systems",
            framework="eu_ai_act",
            category="prohibited",
            subcategory="social_scoring",
            risk_level=RiskCategory.PROHIBITED,
            requirements=[
                "No social scoring systems",
                "No evaluation or classification of natural persons",
                "No detrimental treatment based on social behavior"
            ],
            evidence_types=["system_documentation", "use_case_analysis"],
            assessment_criteria=[
                "System does not perform social scoring",
                "No evaluation of natural persons",
                "No detrimental treatment based on social behavior"
            ],
            related_controls=[],
            metadata={"priority": "critical", "implementation_effort": "none"}
        )
        
        # High-risk AI systems
        controls["high_risk_1"] = RegulatoryControl(
            id="high_risk_1",
            name="Risk Management System",
            description="Risk management system for high-risk AI",
            framework="eu_ai_act",
            category="high_risk",
            subcategory="risk_management",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Establish risk management system",
                "Identify and analyze known and foreseeable risks",
                "Implement risk mitigation measures",
                "Monitor and update risk management system"
            ],
            evidence_types=["risk_management_plan", "risk_assessments", "mitigation_measures"],
            assessment_criteria=[
                "Risk management system is established",
                "Risks are identified and analyzed",
                "Mitigation measures are implemented",
                "System is monitored and updated"
            ],
            related_controls=["high_risk_2", "high_risk_3"],
            metadata={"priority": "high", "implementation_effort": "high"}
        )
        
        controls["high_risk_2"] = RegulatoryControl(
            id="high_risk_2",
            name="Data Governance",
            description="Data governance for high-risk AI systems",
            framework="eu_ai_act",
            category="high_risk",
            subcategory="data_governance",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Implement data governance measures",
                "Ensure data quality and relevance",
                "Implement data protection measures",
                "Document data sources and processing"
            ],
            evidence_types=["data_governance_policy", "data_quality_reports", "data_protection_measures"],
            assessment_criteria=[
                "Data governance measures are implemented",
                "Data quality is ensured",
                "Data protection is implemented",
                "Data sources are documented"
            ],
            related_controls=["high_risk_1", "high_risk_3"],
            metadata={"priority": "high", "implementation_effort": "high"}
        )
        
        controls["high_risk_3"] = RegulatoryControl(
            id="high_risk_3",
            name="Technical Documentation",
            description="Technical documentation for high-risk AI systems",
            framework="eu_ai_act",
            category="high_risk",
            subcategory="technical_documentation",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Create comprehensive technical documentation",
                "Document system architecture and design",
                "Document training and testing procedures",
                "Document performance and accuracy metrics"
            ],
            evidence_types=["technical_documentation", "architecture_diagrams", "test_reports"],
            assessment_criteria=[
                "Technical documentation is comprehensive",
                "Architecture is documented",
                "Training procedures are documented",
                "Performance metrics are documented"
            ],
            related_controls=["high_risk_1", "high_risk_2"],
            metadata={"priority": "high", "implementation_effort": "medium"}
        )
        
        # Limited risk AI systems
        controls["limited_risk_1"] = RegulatoryControl(
            id="limited_risk_1",
            name="Transparency Obligations",
            description="Transparency obligations for limited risk AI",
            framework="eu_ai_act",
            category="limited_risk",
            subcategory="transparency",
            risk_level=RiskCategory.LIMITED_RISK,
            requirements=[
                "Inform users that they are interacting with AI",
                "Provide clear information about AI capabilities",
                "Ensure users can make informed decisions"
            ],
            evidence_types=["user_notifications", "capability_documentation", "user_guidance"],
            assessment_criteria=[
                "Users are informed about AI interaction",
                "AI capabilities are clearly communicated",
                "Users can make informed decisions"
            ],
            related_controls=[],
            metadata={"priority": "medium", "implementation_effort": "low"}
        )
        
        return controls
    
    def _load_iso_controls(self) -> Dict[str, RegulatoryControl]:
        """Load ISO/IEC 42001 controls"""
        controls = {}
        
        # Context controls
        controls["context_1"] = RegulatoryControl(
            id="context_1",
            name="Organization Context",
            description="Understanding organization and context",
            framework="iso_42001",
            category="context",
            subcategory="organization_context",
            risk_level=RiskCategory.MEDIUM_RISK,
            requirements=[
                "Understand organization context",
                "Identify external and internal issues",
                "Determine scope of AI management system",
                "Document context and scope"
            ],
            evidence_types=["context_analysis", "scope_documentation", "issue_registers"],
            assessment_criteria=[
                "Organization context is understood",
                "External and internal issues are identified",
                "Scope is determined and documented",
                "Context is documented"
            ],
            related_controls=["context_2", "context_3"],
            metadata={"priority": "medium", "implementation_effort": "medium"}
        )
        
        # Leadership controls
        controls["leadership_1"] = RegulatoryControl(
            id="leadership_1",
            name="Leadership and Commitment",
            description="Leadership and commitment to AI management system",
            framework="iso_42001",
            category="leadership",
            subcategory="leadership_commitment",
            risk_level=RiskCategory.HIGH_RISK,
            requirements=[
                "Demonstrate leadership and commitment",
                "Establish AI management system policy",
                "Assign roles and responsibilities",
                "Ensure resource availability"
            ],
            evidence_types=["leadership_statements", "policy_documents", "role_assignments"],
            assessment_criteria=[
                "Leadership commitment is demonstrated",
                "Policy is established and communicated",
                "Roles are assigned and documented",
                "Resources are allocated"
            ],
            related_controls=["leadership_2", "leadership_3"],
            metadata={"priority": "high", "implementation_effort": "medium"}
        )
        
        return controls
    
    def _load_oecd_controls(self) -> Dict[str, RegulatoryControl]:
        """Load OECD AI Principles controls"""
        controls = {}
        
        # Inclusive growth controls
        controls["inclusive_1"] = RegulatoryControl(
            id="inclusive_1",
            name="AI Benefits People and Planet",
            description="AI should benefit people and the planet",
            framework="oecd_ai_principles",
            category="inclusive_growth",
            subcategory="benefits",
            risk_level=RiskCategory.MEDIUM_RISK,
            requirements=[
                "Ensure AI benefits people and planet",
                "Consider environmental impact",
                "Promote sustainable development",
                "Address societal challenges"
            ],
            evidence_types=["impact_assessments", "sustainability_reports", "benefit_analyses"],
            assessment_criteria=[
                "AI benefits are clearly demonstrated",
                "Environmental impact is considered",
                "Sustainable development is promoted",
                "Societal challenges are addressed"
            ],
            related_controls=["inclusive_2"],
            metadata={"priority": "medium", "implementation_effort": "medium"}
        )
        
        # Human-centered controls
        controls["human_1"] = RegulatoryControl(
            id="human_1",
            name="Human Augmentation",
            description="AI should augment human capabilities",
            framework="oecd_ai_principles",
            category="human_centered",
            subcategory="augmentation",
            risk_level=RiskCategory.MEDIUM_RISK,
            requirements=[
                "Design AI to augment human capabilities",
                "Respect human autonomy",
                "Enable human oversight",
                "Support human decision-making"
            ],
            evidence_types=["design_documents", "human_oversight_mechanisms", "decision_support_systems"],
            assessment_criteria=[
                "AI augments rather than replaces humans",
                "Human autonomy is respected",
                "Human oversight is enabled",
                "Decision-making is supported"
            ],
            related_controls=["human_2"],
            metadata={"priority": "medium", "implementation_effort": "medium"}
        )
        
        return controls
    
    def _load_local_regulations(self) -> Dict[str, RegulatoryControl]:
        """Load local/regional regulations (extensible)"""
        controls = {}
        
        # Example: US state regulations
        controls["california_1"] = RegulatoryControl(
            id="california_1",
            name="California AI Transparency",
            description="California AI transparency requirements",
            framework="local_regulations",
            category="transparency",
            subcategory="california_requirements",
            risk_level=RiskCategory.MEDIUM_RISK,
            requirements=[
                "Provide AI transparency notices",
                "Disclose AI decision-making processes",
                "Enable human review of AI decisions"
            ],
            evidence_types=["transparency_notices", "decision_documentation", "review_processes"],
            assessment_criteria=[
                "Transparency notices are provided",
                "Decision processes are disclosed",
                "Human review is enabled"
            ],
            related_controls=[],
            metadata={"priority": "medium", "implementation_effort": "low", "jurisdiction": "california"}
        )
        
        return controls
    
    def map_policy_to_frameworks(self, policy_rule_id: str, policy_content: str, 
                                policy_metadata: Dict[str, Any]) -> ComplianceMapping:
        """Map a policy rule to applicable regulatory frameworks"""
        mappings = []
        mapping_confidence = 0.0
        
        # Analyze policy content for framework applicability
        for framework_name, controls in self.regulatory_frameworks.items():
            applicable_controls = []
            
            for control_id, control in controls.items():
                # Check if policy applies to this control
                if self._policy_applies_to_control(policy_content, control, policy_metadata):
                    applicable_controls.append(control_id)
            
            if applicable_controls:
                mappings.extend(applicable_controls)
        
        # Calculate mapping confidence based on keyword matches and metadata
        mapping_confidence = self._calculate_mapping_confidence(
            policy_content, mappings, policy_metadata
        )
        
        # Determine mapping type
        mapping_type = self._determine_mapping_type(mapping_confidence, len(mappings))
        
        mapping = ComplianceMapping(
            policy_rule_id=policy_rule_id,
            regulatory_controls=mappings,
            mapping_confidence=mapping_confidence,
            mapping_type=mapping_type,
            evidence={
                "policy_content": policy_content,
                "metadata": policy_metadata,
                "analysis_method": "keyword_matching_and_metadata_analysis"
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.compliance_mappings[policy_rule_id] = mapping
        return mapping
    
    def _policy_applies_to_control(self, policy_content: str, control: RegulatoryControl, 
                                 policy_metadata: Dict[str, Any]) -> bool:
        """Determine if a policy applies to a regulatory control"""
        # Keyword matching
        policy_lower = policy_content.lower()
        control_keywords = self._extract_control_keywords(control)
        
        keyword_matches = sum(1 for keyword in control_keywords if keyword in policy_lower)
        keyword_threshold = len(control_keywords) * 0.3  # 30% keyword match threshold
        
        # Metadata matching
        metadata_match = False
        if "category" in policy_metadata:
            metadata_match = (
                policy_metadata["category"].lower() == control.category.lower() or
                policy_metadata["category"].lower() == control.subcategory.lower()
            )
        
        # Framework matching
        framework_match = False
        if "framework" in policy_metadata:
            framework_match = policy_metadata["framework"].lower() == control.framework.lower()
        
        return (keyword_matches >= keyword_threshold or metadata_match or framework_match)
    
    def _extract_control_keywords(self, control: RegulatoryControl) -> List[str]:
        """Extract keywords from a regulatory control"""
        keywords = []
        
        # Extract from name and description
        text = f"{control.name} {control.description}"
        keywords.extend(self._extract_keywords_from_text(text))
        
        # Extract from requirements
        for requirement in control.requirements:
            keywords.extend(self._extract_keywords_from_text(requirement))
        
        # Extract from assessment criteria
        for criteria in control.assessment_criteria:
            keywords.extend(self._extract_keywords_from_text(criteria))
        
        return list(set(keywords))  # Remove duplicates
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction (in production, use NLP libraries)
        import re
        
        # Remove common words and extract meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
    
    def _calculate_mapping_confidence(self, policy_content: str, mappings: List[str], 
                                    policy_metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for policy-to-framework mapping"""
        confidence = 0.0
        
        # Base confidence from number of mappings
        if mappings:
            confidence += min(len(mappings) * 0.1, 0.5)
        
        # Boost confidence for explicit framework mentions
        if "framework" in policy_metadata:
            confidence += 0.3
        
        # Boost confidence for category matches
        if "category" in policy_metadata:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _determine_mapping_type(self, confidence: float, num_mappings: int) -> str:
        """Determine the type of mapping based on confidence and number of mappings"""
        if confidence >= 0.8 and num_mappings >= 3:
            return "direct"
        elif confidence >= 0.5 and num_mappings >= 1:
            return "partial"
        else:
            return "inferred"
    
    def assess_framework_compliance(self, system_id: str, framework: str, 
                                  system_evidence: Dict[str, Any]) -> FrameworkAssessment:
        """Assess compliance with a specific regulatory framework"""
        if framework not in self.regulatory_frameworks:
            raise ValueError(f"Unknown framework: {framework}")
        
        controls = self.regulatory_frameworks[framework]
        control_assessments = {}
        gaps = []
        recommendations = []
        evidence_summary = {}
        
        total_score = 0.0
        total_controls = len(controls)
        
        for control_id, control in controls.items():
            # Assess control compliance
            compliance_status, score, control_gaps, control_recommendations = self._assess_control_compliance(
                control, system_evidence
            )
            
            control_assessments[control_id] = compliance_status
            total_score += score
            gaps.extend(control_gaps)
            recommendations.extend(control_recommendations)
            
            # Collect evidence
            evidence_summary[control_id] = {
                "status": compliance_status.value,
                "score": score,
                "evidence_types": control.evidence_types,
                "requirements": control.requirements
            }
        
        # Calculate overall compliance score
        compliance_score = (total_score / total_controls * 100) if total_controls > 0 else 0
        
        # Determine overall status
        if compliance_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif compliance_score >= 70:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT
        
        # Assess risk
        risk_assessment = self._assess_framework_risk(controls, control_assessments, system_evidence)
        
        assessment = FrameworkAssessment(
            framework=framework,
            system_id=system_id,
            overall_status=overall_status,
            compliance_score=compliance_score,
            risk_assessment=risk_assessment,
            control_assessments=control_assessments,
            gaps=gaps,
            recommendations=recommendations,
            evidence_summary=evidence_summary,
            assessment_date=datetime.now()
        )
        
        self.assessment_history.append(assessment)
        return assessment
    
    def _assess_control_compliance(self, control: RegulatoryControl, 
                                 system_evidence: Dict[str, Any]) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Assess compliance with a specific control"""
        gaps = []
        recommendations = []
        score = 0.0
        
        # Check evidence availability
        evidence_available = 0
        for evidence_type in control.evidence_types:
            if evidence_type in system_evidence:
                evidence_available += 1
            else:
                gaps.append(f"Missing evidence: {evidence_type}")
        
        # Check requirement fulfillment
        requirements_met = 0
        for requirement in control.requirements:
            if self._requirement_is_met(requirement, system_evidence):
                requirements_met += 1
            else:
                gaps.append(f"Requirement not met: {requirement}")
                recommendations.append(f"Implement: {requirement}")
        
        # Calculate score
        evidence_score = (evidence_available / len(control.evidence_types)) if control.evidence_types else 1.0
        requirement_score = (requirements_met / len(control.requirements)) if control.requirements else 1.0
        score = (evidence_score + requirement_score) / 2
        
        # Determine compliance status
        if score >= 0.9:
            status = ComplianceStatus.COMPLIANT
        elif score >= 0.7:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return status, score, gaps, recommendations
    
    def _requirement_is_met(self, requirement: str, system_evidence: Dict[str, Any]) -> bool:
        """Check if a requirement is met based on system evidence"""
        # Simple keyword-based checking (in production, use more sophisticated NLP)
        requirement_lower = requirement.lower()
        
        # Check for evidence that suggests requirement is met
        for evidence_type, evidence_data in system_evidence.items():
            if isinstance(evidence_data, str):
                evidence_lower = evidence_data.lower()
                # Simple keyword matching
                if any(keyword in evidence_lower for keyword in requirement_lower.split()):
                    return True
            elif isinstance(evidence_data, dict):
                # Recursive check for nested evidence
                if self._requirement_is_met(requirement, evidence_data):
                    return True
        
        return False
    
    def _assess_framework_risk(self, controls: Dict[str, RegulatoryControl], 
                             control_assessments: Dict[str, ComplianceStatus],
                             system_evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk for a framework"""
        risk_factors = {
            "high_risk_controls_failed": 0,
            "prohibited_controls_failed": 0,
            "critical_gaps": 0,
            "overall_risk_score": 0.0
        }
        
        for control_id, control in controls.items():
            assessment = control_assessments.get(control_id, ComplianceStatus.NOT_ASSESSED)
            
            if assessment == ComplianceStatus.NON_COMPLIANT:
                if control.risk_level == RiskCategory.HIGH_RISK:
                    risk_factors["high_risk_controls_failed"] += 1
                elif control.risk_level == RiskCategory.PROHIBITED:
                    risk_factors["prohibited_controls_failed"] += 1
        
        # Calculate overall risk score
        total_controls = len(controls)
        failed_controls = sum(1 for status in control_assessments.values() 
                            if status == ComplianceStatus.NON_COMPLIANT)
        
        risk_factors["overall_risk_score"] = (failed_controls / total_controls) if total_controls > 0 else 0.0
        
        return risk_factors
    
    def get_framework_controls(self, framework: str) -> Dict[str, RegulatoryControl]:
        """Get all controls for a specific framework"""
        return self.regulatory_frameworks.get(framework, {})
    
    def get_cross_framework_mappings(self, control_id: str) -> Dict[str, List[str]]:
        """Get mappings of a control across different frameworks"""
        mappings = {}
        
        for framework_name, controls in self.regulatory_frameworks.items():
            if control_id in controls:
                control = controls[control_id]
                related_controls = []
                
                # Find related controls in other frameworks
                for other_framework, other_controls in self.regulatory_frameworks.items():
                    if other_framework != framework_name:
                        for other_control_id, other_control in other_controls.items():
                            if self._controls_are_related(control, other_control):
                                related_controls.append(other_control_id)
                
                if related_controls:
                    mappings[framework_name] = related_controls
        
        return mappings
    
    def _controls_are_related(self, control1: RegulatoryControl, control2: RegulatoryControl) -> bool:
        """Determine if two controls are related across frameworks"""
        # Check for similar categories
        if control1.category == control2.category or control1.subcategory == control2.subcategory:
            return True
        
        # Check for similar requirements
        common_requirements = set(control1.requirements) & set(control2.requirements)
        if len(common_requirements) > 0:
            return True
        
        # Check for similar keywords
        keywords1 = set(self._extract_control_keywords(control1))
        keywords2 = set(self._extract_control_keywords(control2))
        common_keywords = keywords1 & keywords2
        
        return len(common_keywords) >= 3  # At least 3 common keywords
    
    def generate_compliance_report(self, system_id: str, frameworks: List[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive compliance report"""
        if frameworks is None:
            frameworks = list(self.regulatory_frameworks.keys())
        
        report = {
            "system_id": system_id,
            "report_date": datetime.now().isoformat(),
            "frameworks_assessed": frameworks,
            "assessments": {},
            "summary": {
                "total_frameworks": len(frameworks),
                "compliant_frameworks": 0,
                "partially_compliant_frameworks": 0,
                "non_compliant_frameworks": 0,
                "overall_compliance_score": 0.0
            }
        }
        
        total_score = 0.0
        
        for framework in frameworks:
            # Get latest assessment for this framework
            latest_assessment = None
            for assessment in reversed(self.assessment_history):
                if assessment.framework == framework and assessment.system_id == system_id:
                    latest_assessment = assessment
                    break
            
            if latest_assessment:
                report["assessments"][framework] = {
                    "status": latest_assessment.overall_status.value,
                    "compliance_score": latest_assessment.compliance_score,
                    "risk_level": latest_assessment.risk_assessment.get("overall_risk_score", 0.0),
                    "gaps": latest_assessment.gaps,
                    "recommendations": latest_assessment.recommendations
                }
                
                total_score += latest_assessment.compliance_score
                
                # Update summary counts
                if latest_assessment.overall_status == ComplianceStatus.COMPLIANT:
                    report["summary"]["compliant_frameworks"] += 1
                elif latest_assessment.overall_status == ComplianceStatus.PARTIALLY_COMPLIANT:
                    report["summary"]["partially_compliant_frameworks"] += 1
                else:
                    report["summary"]["non_compliant_frameworks"] += 1
        
        # Calculate overall compliance score
        if frameworks:
            report["summary"]["overall_compliance_score"] = total_score / len(frameworks)
        
        return report


"""
Compliance & Reporting Service

This service provides comprehensive compliance checking, audit reporting,
and documentation generation for AI systems.

Supports:
- EU AI Act compliance
- GDPR compliance
- ISO/IEC standards
- Automated audit reports
- Fairness documentation generation
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import json


class RegulatoryFramework(str, Enum):
    """Supported regulatory frameworks"""
    EU_AI_ACT = "eu_ai_act"
    GDPR = "gdpr"
    ISO_IEC_42001 = "iso_iec_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    IEEE_7000 = "ieee_7000"
    # India-specific frameworks
    DPDP_ACT = "dpdp_act"
    INDIA_AI_FRAMEWORK = "india_ai_framework"


class RiskLevel(str, Enum):
    """AI system risk levels per EU AI Act"""
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class ComplianceStatus(str, Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class ComplianceReportingService:
    """Service for compliance checking and reporting"""

    def __init__(self):
        self.frameworks = {
            RegulatoryFramework.EU_AI_ACT: self._get_eu_ai_act_requirements(),
            RegulatoryFramework.GDPR: self._get_gdpr_requirements(),
            RegulatoryFramework.ISO_IEC_42001: self._get_iso_requirements(),
            RegulatoryFramework.NIST_AI_RMF: self._get_nist_requirements(),
            RegulatoryFramework.IEEE_7000: self._get_ieee_requirements(),
            # India-specific frameworks
            RegulatoryFramework.DPDP_ACT: self._get_dpdp_requirements(),
            RegulatoryFramework.INDIA_AI_FRAMEWORK: self._get_india_ai_requirements(),
        }

    def _get_eu_ai_act_requirements(self) -> List[Dict[str, Any]]:
        """Get EU AI Act requirements"""
        return [
            {
                "id": "EU-AI-1",
                "category": "Risk Classification",
                "requirement": "Classify AI system risk level",
                "description": "Determine if system is unacceptable, high, limited, or minimal risk",
                "article": "Article 6",
                "mandatory": True,
            },
            {
                "id": "EU-AI-2",
                "category": "Transparency",
                "requirement": "Provide transparency information",
                "description": "Users must be informed when interacting with AI systems",
                "article": "Article 52",
                "mandatory": True,
            },
            {
                "id": "EU-AI-3",
                "category": "Human Oversight",
                "requirement": "Implement human oversight measures",
                "description": "High-risk systems must have human oversight capabilities",
                "article": "Article 14",
                "mandatory": True,
            },
            {
                "id": "EU-AI-4",
                "category": "Data Governance",
                "requirement": "Ensure data quality and governance",
                "description": "Training data must be relevant, representative, and free of errors",
                "article": "Article 10",
                "mandatory": True,
            },
            {
                "id": "EU-AI-5",
                "category": "Technical Documentation",
                "requirement": "Maintain technical documentation",
                "description": "Comprehensive documentation of system design and operation",
                "article": "Article 11",
                "mandatory": True,
            },
            {
                "id": "EU-AI-6",
                "category": "Record Keeping",
                "requirement": "Implement automatic logging",
                "description": "Keep logs of system operations for traceability",
                "article": "Article 12",
                "mandatory": True,
            },
            {
                "id": "EU-AI-7",
                "category": "Accuracy & Robustness",
                "requirement": "Ensure accuracy and robustness",
                "description": "System must achieve appropriate accuracy levels",
                "article": "Article 15",
                "mandatory": True,
            },
            {
                "id": "EU-AI-8",
                "category": "Cybersecurity",
                "requirement": "Implement cybersecurity measures",
                "description": "Protect against unauthorized access and manipulation",
                "article": "Article 15",
                "mandatory": True,
            },
        ]

    def _get_gdpr_requirements(self) -> List[Dict[str, Any]]:
        """Get GDPR requirements for AI systems"""
        return [
            {
                "id": "GDPR-1",
                "category": "Lawful Processing",
                "requirement": "Establish lawful basis for processing",
                "description": "Must have legal basis for processing personal data",
                "article": "Article 6",
                "mandatory": True,
            },
            {
                "id": "GDPR-2",
                "category": "Data Minimization",
                "requirement": "Minimize data collection",
                "description": "Collect only necessary personal data",
                "article": "Article 5(1)(c)",
                "mandatory": True,
            },
            {
                "id": "GDPR-3",
                "category": "Automated Decision-Making",
                "requirement": "Right not to be subject to automated decisions",
                "description": "Provide safeguards for automated decision-making",
                "article": "Article 22",
                "mandatory": True,
            },
            {
                "id": "GDPR-4",
                "category": "Data Protection Impact Assessment",
                "requirement": "Conduct DPIA for high-risk processing",
                "description": "Assess impact on data protection for high-risk AI",
                "article": "Article 35",
                "mandatory": True,
            },
            {
                "id": "GDPR-5",
                "category": "Right to Explanation",
                "requirement": "Provide meaningful information about logic",
                "description": "Explain automated decision-making logic to data subjects",
                "article": "Article 13-15",
                "mandatory": True,
            },
        ]

    def _get_iso_requirements(self) -> List[Dict[str, Any]]:
        """Get ISO/IEC 42001 requirements"""
        return [
            {
                "id": "ISO-1",
                "category": "AI Management System",
                "requirement": "Establish AI management system",
                "description": "Implement systematic approach to AI governance",
                "clause": "4.4",
                "mandatory": True,
            },
            {
                "id": "ISO-2",
                "category": "Risk Management",
                "requirement": "Implement AI risk management",
                "description": "Identify and manage AI-specific risks",
                "clause": "6.1",
                "mandatory": True,
            },
            {
                "id": "ISO-3",
                "category": "Competence",
                "requirement": "Ensure personnel competence",
                "description": "Staff must have necessary AI competencies",
                "clause": "7.2",
                "mandatory": True,
            },
        ]

    def _get_nist_requirements(self) -> List[Dict[str, Any]]:
        """Get NIST AI Risk Management Framework requirements"""
        return [
            {
                "id": "NIST-1",
                "category": "Govern",
                "requirement": "Establish AI governance",
                "description": "Create governance structure for AI systems",
                "function": "Govern",
                "mandatory": True,
            },
            {
                "id": "NIST-2",
                "category": "Map",
                "requirement": "Map AI risks",
                "description": "Identify and document AI system risks",
                "function": "Map",
                "mandatory": True,
            },
            {
                "id": "NIST-3",
                "category": "Measure",
                "requirement": "Measure AI performance",
                "description": "Assess AI system trustworthiness",
                "function": "Measure",
                "mandatory": True,
            },
            {
                "id": "NIST-4",
                "category": "Manage",
                "requirement": "Manage AI risks",
                "description": "Implement risk mitigation strategies",
                "function": "Manage",
                "mandatory": True,
            },
        ]

    def _get_ieee_requirements(self) -> List[Dict[str, Any]]:
        """Get IEEE 7000 requirements"""
        return [
            {
                "id": "IEEE-1",
                "category": "Value-Based Design",
                "requirement": "Implement value-based design",
                "description": "Design systems aligned with human values",
                "standard": "IEEE 7000",
                "mandatory": True,
            },
        ]

    def _get_dpdp_requirements(self) -> List[Dict[str, Any]]:
        """Get Digital Personal Data Protection Act (India, 2023) requirements"""
        return [
            {
                "id": "DPDP-1",
                "category": "Lawful Processing",
                "requirement": "Obtain valid consent for data processing",
                "description": "Process personal data only with valid consent or for legitimate use",
                "section": "Section 6",
                "mandatory": True,
            },
            {
                "id": "DPDP-2",
                "category": "Purpose Limitation",
                "requirement": "Process data only for specified purpose",
                "description": "Personal data must be processed only for the purpose for which consent was obtained",
                "section": "Section 4",
                "mandatory": True,
            },
            {
                "id": "DPDP-3",
                "category": "Data Minimization",
                "requirement": "Collect only necessary data",
                "description": "Collect only such personal data as is necessary for the specified purpose",
                "section": "Section 4",
                "mandatory": True,
            },
            {
                "id": "DPDP-4",
                "category": "Data Accuracy",
                "requirement": "Ensure data accuracy",
                "description": "Take reasonable steps to ensure personal data is complete, accurate, and consistent",
                "section": "Section 4",
                "mandatory": True,
            },
            {
                "id": "DPDP-5",
                "category": "Data Retention",
                "requirement": "Limit data retention period",
                "description": "Retain data only as long as necessary for the specified purpose",
                "section": "Section 4",
                "mandatory": True,
            },
            {
                "id": "DPDP-6",
                "category": "Data Security",
                "requirement": "Implement reasonable security safeguards",
                "description": "Implement appropriate technical and organizational measures to protect personal data",
                "section": "Section 8",
                "mandatory": True,
            },
            {
                "id": "DPDP-7",
                "category": "Data Breach Notification",
                "requirement": "Notify data breaches",
                "description": "Notify Data Protection Board and affected individuals of data breaches",
                "section": "Section 8",
                "mandatory": True,
            },
            {
                "id": "DPDP-8",
                "category": "Right to Access",
                "requirement": "Provide data access to individuals",
                "description": "Enable individuals to obtain information about their personal data",
                "section": "Section 11",
                "mandatory": True,
            },
            {
                "id": "DPDP-9",
                "category": "Right to Correction",
                "requirement": "Enable data correction",
                "description": "Allow individuals to correct, complete, or update their personal data",
                "section": "Section 11",
                "mandatory": True,
            },
            {
                "id": "DPDP-10",
                "category": "Right to Erasure",
                "requirement": "Enable data erasure",
                "description": "Allow individuals to erase their personal data (with exceptions)",
                "section": "Section 11",
                "mandatory": True,
            },
            {
                "id": "DPDP-11",
                "category": "Consent Management",
                "requirement": "Implement consent management",
                "description": "Provide mechanism for individuals to give, manage, review, and withdraw consent",
                "section": "Section 6",
                "mandatory": True,
            },
            {
                "id": "DPDP-12",
                "category": "Cross-Border Data Transfer",
                "requirement": "Comply with cross-border transfer rules",
                "description": "Transfer data outside India only to notified countries/territories",
                "section": "Section 16",
                "mandatory": True,
            },
            {
                "id": "DPDP-13",
                "category": "Children's Data Protection",
                "requirement": "Obtain verifiable parental consent for children",
                "description": "Process children's data only with verifiable consent of parent/guardian",
                "section": "Section 9",
                "mandatory": True,
            },
            {
                "id": "DPDP-14",
                "category": "Data Protection Officer",
                "requirement": "Appoint Data Protection Officer (if applicable)",
                "description": "Significant data fiduciaries must appoint a Data Protection Officer",
                "section": "Section 10",
                "mandatory": False,
            },
        ]

    def _get_india_ai_requirements(self) -> List[Dict[str, Any]]:
        """Get India National AI Framework requirements (based on NITI Aayog guidelines)"""
        return [
            {
                "id": "INDIA-AI-1",
                "category": "Safety and Reliability",
                "requirement": "Ensure AI system safety",
                "description": "AI systems must be safe, secure, and reliable throughout their lifecycle",
                "principle": "Safety and Reliability",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-2",
                "category": "Equality and Inclusiveness",
                "requirement": "Prevent discrimination and bias",
                "description": "AI systems must not discriminate and should be inclusive of all sections of society",
                "principle": "Equality",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-3",
                "category": "Privacy and Security",
                "requirement": "Protect privacy and ensure data security",
                "description": "Implement robust privacy protection and data security measures",
                "principle": "Privacy and Security",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-4",
                "category": "Transparency and Explainability",
                "requirement": "Ensure AI transparency",
                "description": "AI systems should be transparent and provide explanations for decisions",
                "principle": "Transparency",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-5",
                "category": "Accountability",
                "requirement": "Establish clear accountability",
                "description": "Clear accountability mechanisms must be in place for AI systems",
                "principle": "Accountability",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-6",
                "category": "Human Oversight",
                "requirement": "Maintain human control",
                "description": "Ensure meaningful human oversight and control over AI systems",
                "principle": "Human-Centered Design",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-7",
                "category": "Fairness Testing",
                "requirement": "Conduct regular fairness audits",
                "description": "Regularly test and audit AI systems for fairness and bias",
                "principle": "Equality",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-8",
                "category": "Data Quality",
                "requirement": "Ensure training data quality",
                "description": "Training data must be representative, accurate, and of high quality",
                "principle": "Safety and Reliability",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-9",
                "category": "Impact Assessment",
                "requirement": "Conduct AI impact assessments",
                "description": "Assess potential societal and individual impacts of AI systems",
                "principle": "Accountability",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-10",
                "category": "Redressal Mechanism",
                "requirement": "Provide grievance redressal",
                "description": "Establish mechanisms for users to raise concerns and seek redressal",
                "principle": "Accountability",
                "mandatory": True,
            },
            {
                "id": "INDIA-AI-11",
                "category": "Environmental Sustainability",
                "requirement": "Consider environmental impact",
                "description": "AI systems should be developed with consideration for environmental sustainability",
                "principle": "Sustainability",
                "mandatory": False,
            },
            {
                "id": "INDIA-AI-12",
                "category": "Local Context",
                "requirement": "Adapt to Indian context",
                "description": "AI systems should be designed considering Indian languages, culture, and diversity",
                "principle": "Inclusiveness",
                "mandatory": True,
            },
        ]

    async def check_compliance(
        self,
        framework: RegulatoryFramework,
        system_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check compliance against a regulatory framework
        
        Args:
            framework: Regulatory framework to check against
            system_data: AI system information and evidence
            
        Returns:
            Compliance assessment results
        """
        requirements = self.frameworks.get(framework, [])
        
        results = []
        compliant_count = 0
        total_count = len(requirements)
        
        for req in requirements:
            # Check if requirement is met based on system data
            status = self._assess_requirement(req, system_data)
            
            result = {
                "requirement_id": req["id"],
                "category": req["category"],
                "requirement": req["requirement"],
                "status": status,
                "evidence": system_data.get(f"evidence_{req['id']}", []),
                "gaps": self._identify_gaps(req, system_data, status),
            }
            
            results.append(result)
            
            if status == ComplianceStatus.COMPLIANT:
                compliant_count += 1
        
        compliance_score = (compliant_count / total_count * 100) if total_count > 0 else 0
        
        overall_status = self._determine_overall_status(compliance_score)
        
        return {
            "framework": framework,
            "assessment_date": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "compliance_score": compliance_score,
            "total_requirements": total_count,
            "compliant_requirements": compliant_count,
            "results": results,
            "recommendations": self._generate_recommendations(results),
        }

    def _assess_requirement(
        self,
        requirement: Dict[str, Any],
        system_data: Dict[str, Any],
    ) -> ComplianceStatus:
        """Assess if a requirement is met"""
        # Check if evidence exists for this requirement
        evidence_key = f"evidence_{requirement['id']}"
        
        if evidence_key not in system_data:
            return ComplianceStatus.NON_COMPLIANT
        
        evidence = system_data[evidence_key]
        
        # Simple assessment based on evidence presence and quality
        if isinstance(evidence, list) and len(evidence) > 0:
            # Check evidence quality
            quality_score = sum(e.get("quality", 0) for e in evidence) / len(evidence)
            
            if quality_score >= 0.8:
                return ComplianceStatus.COMPLIANT
            elif quality_score >= 0.5:
                return ComplianceStatus.PARTIALLY_COMPLIANT
            else:
                return ComplianceStatus.NON_COMPLIANT
        
        return ComplianceStatus.NON_COMPLIANT

    def _identify_gaps(
        self,
        requirement: Dict[str, Any],
        system_data: Dict[str, Any],
        status: ComplianceStatus,
    ) -> List[str]:
        """Identify compliance gaps"""
        gaps = []
        
        if status == ComplianceStatus.NON_COMPLIANT:
            gaps.append(f"No evidence provided for {requirement['requirement']}")
        elif status == ComplianceStatus.PARTIALLY_COMPLIANT:
            gaps.append(f"Incomplete evidence for {requirement['requirement']}")
        
        return gaps

    def _determine_overall_status(self, compliance_score: float) -> ComplianceStatus:
        """Determine overall compliance status"""
        if compliance_score >= 90:
            return ComplianceStatus.COMPLIANT
        elif compliance_score >= 60:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        for result in results:
            if result["status"] != ComplianceStatus.COMPLIANT:
                recommendations.append(
                    f"Address {result['category']}: {result['requirement']}"
                )
        
        return recommendations

    async def generate_audit_report(
        self,
        system_id: str,
        system_data: Dict[str, Any],
        frameworks: Optional[List[RegulatoryFramework]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report
        
        Args:
            system_id: AI system identifier
            system_data: System information and evidence
            frameworks: Frameworks to check (default: all)
            
        Returns:
            Comprehensive audit report
        """
        if frameworks is None:
            frameworks = list(RegulatoryFramework)
        
        compliance_results = []
        
        for framework in frameworks:
            result = await self.check_compliance(framework, system_data)
            compliance_results.append(result)
        
        # Calculate overall compliance
        avg_score = sum(r["compliance_score"] for r in compliance_results) / len(compliance_results)
        
        return {
            "report_id": f"AUDIT-{system_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "system_id": system_id,
            "report_date": datetime.utcnow().isoformat(),
            "system_name": system_data.get("name", "Unknown"),
            "system_description": system_data.get("description", ""),
            "risk_level": system_data.get("risk_level", RiskLevel.MINIMAL),
            "overall_compliance_score": avg_score,
            "frameworks_assessed": [f.value for f in frameworks],
            "compliance_results": compliance_results,
            "executive_summary": self._generate_executive_summary(compliance_results),
            "recommendations": self._consolidate_recommendations(compliance_results),
            "next_review_date": self._calculate_next_review_date(),
        }

    def _generate_executive_summary(
        self,
        compliance_results: List[Dict[str, Any]],
    ) -> str:
        """Generate executive summary for audit report"""
        total_frameworks = len(compliance_results)
        compliant_frameworks = sum(
            1 for r in compliance_results
            if r["overall_status"] == ComplianceStatus.COMPLIANT
        )
        
        avg_score = sum(r["compliance_score"] for r in compliance_results) / total_frameworks
        
        summary = f"""
        Compliance Assessment Summary:
        
        This AI system has been assessed against {total_frameworks} regulatory frameworks.
        Overall compliance score: {avg_score:.1f}%
        
        Fully compliant frameworks: {compliant_frameworks}/{total_frameworks}
        
        """
        
        if avg_score >= 90:
            summary += "The system demonstrates strong compliance across all frameworks."
        elif avg_score >= 70:
            summary += "The system shows good compliance with some areas requiring attention."
        else:
            summary += "The system requires significant improvements to meet compliance standards."
        
        return summary.strip()

    def _consolidate_recommendations(
        self,
        compliance_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Consolidate recommendations from all frameworks"""
        all_recommendations = []
        
        for result in compliance_results:
            for rec in result.get("recommendations", []):
                all_recommendations.append({
                    "framework": result["framework"],
                    "recommendation": rec,
                    "priority": "high" if "critical" in rec.lower() else "medium",
                })
        
        return all_recommendations

    def _calculate_next_review_date(self) -> str:
        """Calculate next review date (typically 6 months)"""
        from datetime import timedelta
        next_review = datetime.utcnow() + timedelta(days=180)
        return next_review.isoformat()

    async def generate_fairness_documentation(
        self,
        model_data: Dict[str, Any],
        bias_test_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive fairness documentation
        
        Args:
            model_data: Model information
            bias_test_results: Results from bias testing
            
        Returns:
            Fairness documentation
        """
        return {
            "document_id": f"FAIR-DOC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "generated_date": datetime.utcnow().isoformat(),
            "model_info": {
                "name": model_data.get("name", "Unknown"),
                "version": model_data.get("version", "1.0"),
                "type": model_data.get("type", "Unknown"),
                "purpose": model_data.get("purpose", ""),
            },
            "fairness_assessment": {
                "metrics_evaluated": bias_test_results.get("metrics", []),
                "protected_attributes": bias_test_results.get("protected_attributes", []),
                "fairness_scores": bias_test_results.get("scores", {}),
                "bias_detected": bias_test_results.get("bias_detected", False),
            },
            "mitigation_strategies": self._generate_mitigation_strategies(bias_test_results),
            "monitoring_plan": self._generate_monitoring_plan(),
            "stakeholder_communication": self._generate_stakeholder_communication(
                bias_test_results
            ),
        }

    def _generate_mitigation_strategies(
        self,
        bias_test_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate bias mitigation strategies"""
        strategies = []
        
        if bias_test_results.get("bias_detected", False):
            strategies.extend([
                {
                    "strategy": "Data Rebalancing",
                    "description": "Ensure training data is balanced across protected groups",
                    "priority": "high",
                },
                {
                    "strategy": "Algorithmic Debiasing",
                    "description": "Apply fairness constraints during model training",
                    "priority": "high",
                },
                {
                    "strategy": "Post-processing Calibration",
                    "description": "Adjust model outputs to ensure fairness",
                    "priority": "medium",
                },
            ])
        
        strategies.append({
            "strategy": "Continuous Monitoring",
            "description": "Implement ongoing bias monitoring in production",
            "priority": "high",
        })
        
        return strategies

    def _generate_monitoring_plan(self) -> Dict[str, Any]:
        """Generate fairness monitoring plan"""
        return {
            "frequency": "monthly",
            "metrics_to_track": [
                "Statistical Parity",
                "Equal Opportunity",
                "Predictive Parity",
                "Calibration",
            ],
            "alert_thresholds": {
                "statistical_parity": 0.8,
                "equal_opportunity": 0.8,
            },
            "review_process": "Quarterly fairness review with stakeholders",
        }

    def _generate_stakeholder_communication(
        self,
        bias_test_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate stakeholder communication plan"""
        return {
            "target_audiences": ["Users", "Regulators", "Internal Teams"],
            "key_messages": [
                "System has been tested for fairness",
                "Ongoing monitoring is in place",
                "Mitigation strategies are implemented",
            ],
            "transparency_measures": [
                "Publish fairness metrics",
                "Provide model cards",
                "Enable user feedback",
            ],
        }

    async def generate_stakeholder_dashboard_data(
        self,
        system_id: str,
        compliance_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate data for stakeholder dashboard
        
        Args:
            system_id: AI system identifier
            compliance_results: Compliance assessment results
            
        Returns:
            Dashboard data
        """
        return {
            "system_id": system_id,
            "last_updated": datetime.utcnow().isoformat(),
            "compliance_overview": {
                "overall_score": sum(r["compliance_score"] for r in compliance_results) / len(compliance_results),
                "frameworks": [
                    {
                        "name": r["framework"],
                        "status": r["overall_status"],
                        "score": r["compliance_score"],
                    }
                    for r in compliance_results
                ],
            },
            "risk_indicators": {
                "high_priority_issues": self._count_high_priority_issues(compliance_results),
                "open_recommendations": sum(len(r.get("recommendations", [])) for r in compliance_results),
            },
            "trends": {
                "compliance_trend": "improving",  # Would calculate from historical data
                "last_assessment_date": datetime.utcnow().isoformat(),
            },
            "key_metrics": {
                "total_requirements": sum(r["total_requirements"] for r in compliance_results),
                "met_requirements": sum(r["compliant_requirements"] for r in compliance_results),
            },
        }

    def _count_high_priority_issues(
        self,
        compliance_results: List[Dict[str, Any]],
    ) -> int:
        """Count high priority compliance issues"""
        count = 0
        for result in compliance_results:
            for req_result in result.get("results", []):
                if req_result["status"] == ComplianceStatus.NON_COMPLIANT:
                    count += 1
        return count

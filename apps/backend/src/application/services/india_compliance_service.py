"""
India-Specific AI Compliance Service

This service provides comprehensive India-specific compliance checking, evidence collection,
and reporting for AI systems. It extends the base ComplianceReportingService with India-specific
frameworks including:

- Digital Personal Data Protection (DPDP) Act 2023
- NITI Aayog Responsible AI Principles
- MeitY Guidelines for Responsible AI
- Digital India Act (emerging framework)

Supports automated evidence collection, bias detection for Indian demographics,
and AI-powered compliance automation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import hashlib
import json
import logging

from .compliance_reporting_service import ComplianceReportingService, ComplianceStatus
from ..schemas.india_compliance import (
    IndiaFramework,
    ComplianceResult,
    ComplianceGap,
    SeverityLevel,
    FairnessMetrics,
)
from fairness_library.india_regulatory_frameworks import (
    DPDP_ACT_2023_FRAMEWORK,
    NITI_AAYOG_PRINCIPLES_FRAMEWORK,
    MEITY_GUIDELINES_FRAMEWORK,
)

logger = logging.getLogger(__name__)


class IndiaComplianceService(ComplianceReportingService):
    """Service for India-specific AI compliance checking and reporting"""

    def __init__(self):
        """Initialize India compliance service"""
        super().__init__()
        self.india_frameworks = {
            IndiaFramework.DPDP_ACT_2023: DPDP_ACT_2023_FRAMEWORK,
            IndiaFramework.NITI_AAYOG_PRINCIPLES: NITI_AAYOG_PRINCIPLES_FRAMEWORK,
            IndiaFramework.MEITY_GUIDELINES: MEITY_GUIDELINES_FRAMEWORK,
        }

    # ========================================================================
    # Main Compliance Checking Methods (Task 3.1)
    # ========================================================================

    async def check_dpdp_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> ComplianceResult:
        """
        Check DPDP Act 2023 compliance for an AI system.

        Evaluates compliance against all 14 DPDP Act requirements including:
        - Consent management
        - Data localization
        - Cross-border transfer
        - Data principal rights
        - Children's data protection
        - Data breach notification
        - Data retention
        - Significant data fiduciary requirements
        - Grievance redressal
        - Data Protection Officer
        - Data audit
        - Data impact assessment
        - Security safeguards
        - Transparency and disclosure

        Args:
            system_data: AI system information and configuration
            evidence: Evidence collected for compliance assessment

        Returns:
            ComplianceResult with overall score, status, and gaps

        Requirements: 1.1, 1.2, 1.3, 2.1, 3.1
        """
        framework = self.india_frameworks[IndiaFramework.DPDP_ACT_2023]
        
        logger.info(f"Starting DPDP Act 2023 compliance check for system: {system_data.get('system_id')}")
        
        # Assess each requirement
        results = {}
        gaps = []
        requirements_met = 0
        total_requirements = framework["total_requirements"]

        for req_id, requirement in framework["requirements"].items():
            assessment = await self._assess_india_requirement(
                requirement,
                evidence,
                IndiaFramework.DPDP_ACT_2023,
            )
            
            results[req_id] = assessment
            
            if assessment["status"] == ComplianceStatus.COMPLIANT:
                requirements_met += 1
            else:
                gap = ComplianceGap(
                    control_id=requirement.get("controls", [None])[0] or req_id,
                    control_name=requirement["name"],
                    category=requirement["category"],
                    severity=assessment.get("severity", SeverityLevel.MEDIUM),
                    failed_checks=assessment.get("failed_checks", []),
                    remediation_steps=assessment.get("remediation_steps", []),
                    legal_citation=requirement["legal_citation"],
                    evidence_id=assessment.get("evidence_id"),
                )
                gaps.append(gap)

        # Calculate compliance score
        overall_score = await self._calculate_india_compliance_score(
            requirements_met,
            total_requirements,
        )

        compliance_result = ComplianceResult(
            framework=IndiaFramework.DPDP_ACT_2023,
            overall_score=overall_score,
            status=self._determine_compliance_status(overall_score),
            requirements_met=requirements_met,
            total_requirements=total_requirements,
            evidence_count=len(evidence),
            results=results,
            gaps=[gap.dict() for gap in gaps],
            timestamp=datetime.utcnow(),
        )

        logger.info(
            f"DPDP compliance check completed. Score: {overall_score:.1f}%, "
            f"Requirements met: {requirements_met}/{total_requirements}"
        )

        return compliance_result

    async def check_niti_aayog_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> ComplianceResult:
        """
        Check NITI Aayog Responsible AI Principles compliance.

        Evaluates compliance against all 12 NITI Aayog principles including:
        - Safety and reliability
        - Equality
        - Inclusivity
        - Privacy and security
        - Transparency
        - Accountability
        - Fairness
        - Human agency and autonomy
        - Robustness
        - Explainability
        - Continuous learning
        - Stakeholder engagement

        Args:
            system_data: AI system information and configuration
            evidence: Evidence collected for compliance assessment

        Returns:
            ComplianceResult with overall score, status, and gaps

        Requirements: 1.1, 1.2, 1.3, 2.1, 3.1
        """
        framework = self.india_frameworks[IndiaFramework.NITI_AAYOG_PRINCIPLES]
        
        logger.info(f"Starting NITI Aayog compliance check for system: {system_data.get('system_id')}")
        
        results = {}
        gaps = []
        requirements_met = 0
        total_requirements = framework["total_requirements"]

        for req_id, requirement in framework["requirements"].items():
            assessment = await self._assess_india_requirement(
                requirement,
                evidence,
                IndiaFramework.NITI_AAYOG_PRINCIPLES,
            )
            
            results[req_id] = assessment
            
            if assessment["status"] == ComplianceStatus.COMPLIANT:
                requirements_met += 1
            else:
                gap = ComplianceGap(
                    control_id=requirement.get("controls", [None])[0] or req_id,
                    control_name=requirement["name"],
                    category=requirement["category"],
                    severity=assessment.get("severity", SeverityLevel.MEDIUM),
                    failed_checks=assessment.get("failed_checks", []),
                    remediation_steps=assessment.get("remediation_steps", []),
                    legal_citation=requirement["legal_citation"],
                    evidence_id=assessment.get("evidence_id"),
                )
                gaps.append(gap)

        overall_score = await self._calculate_india_compliance_score(
            requirements_met,
            total_requirements,
        )

        compliance_result = ComplianceResult(
            framework=IndiaFramework.NITI_AAYOG_PRINCIPLES,
            overall_score=overall_score,
            status=self._determine_compliance_status(overall_score),
            requirements_met=requirements_met,
            total_requirements=total_requirements,
            evidence_count=len(evidence),
            results=results,
            gaps=[gap.dict() for gap in gaps],
            timestamp=datetime.utcnow(),
        )

        logger.info(
            f"NITI Aayog compliance check completed. Score: {overall_score:.1f}%, "
            f"Requirements met: {requirements_met}/{total_requirements}"
        )

        return compliance_result

    async def check_meity_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> ComplianceResult:
        """
        Check MeitY Guidelines for Responsible AI compliance.

        Evaluates compliance against MeitY guidelines including:
        - Responsible AI development
        - Algorithmic accountability
        - Ethical deployment
        - Bias mitigation
        - Transparency and explainability
        - Human oversight
        - Security and privacy
        - Stakeholder engagement

        Args:
            system_data: AI system information and configuration
            evidence: Evidence collected for compliance assessment

        Returns:
            ComplianceResult with overall score, status, and gaps

        Requirements: 1.1, 1.2, 1.3, 2.1, 3.1
        """
        framework = self.india_frameworks[IndiaFramework.MEITY_GUIDELINES]
        
        logger.info(f"Starting MeitY compliance check for system: {system_data.get('system_id')}")
        
        results = {}
        gaps = []
        requirements_met = 0
        total_requirements = framework["total_requirements"]

        for req_id, requirement in framework["requirements"].items():
            assessment = await self._assess_india_requirement(
                requirement,
                evidence,
                IndiaFramework.MEITY_GUIDELINES,
            )
            
            results[req_id] = assessment
            
            if assessment["status"] == ComplianceStatus.COMPLIANT:
                requirements_met += 1
            else:
                gap = ComplianceGap(
                    control_id=requirement.get("controls", [None])[0] or req_id,
                    control_name=requirement["name"],
                    category=requirement["category"],
                    severity=assessment.get("severity", SeverityLevel.MEDIUM),
                    failed_checks=assessment.get("failed_checks", []),
                    remediation_steps=assessment.get("remediation_steps", []),
                    legal_citation=requirement["legal_citation"],
                    evidence_id=assessment.get("evidence_id"),
                )
                gaps.append(gap)

        overall_score = await self._calculate_india_compliance_score(
            requirements_met,
            total_requirements,
        )

        compliance_result = ComplianceResult(
            framework=IndiaFramework.MEITY_GUIDELINES,
            overall_score=overall_score,
            status=self._determine_compliance_status(overall_score),
            requirements_met=requirements_met,
            total_requirements=total_requirements,
            evidence_count=len(evidence),
            results=results,
            gaps=[gap.dict() for gap in gaps],
            timestamp=datetime.utcnow(),
        )

        logger.info(
            f"MeitY compliance check completed. Score: {overall_score:.1f}%, "
            f"Requirements met: {requirements_met}/{total_requirements}"
        )

        return compliance_result

    async def check_digital_india_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> ComplianceResult:
        """
        Check Digital India Act compliance (emerging framework).

        The Digital India Act is an evolving regulatory framework. This method
        evaluates preliminary requirements based on draft legislation.

        Args:
            system_data: AI system information and configuration
            evidence: Evidence collected for compliance assessment

        Returns:
            ComplianceResult with overall score, status, and gaps

        Requirements: 1.1, 1.2, 1.3, 2.1, 3.1
        """
        logger.info(f"Starting Digital India Act compliance check for system: {system_data.get('system_id')}")
        
        # Digital India Act framework is still evolving
        # For now, return a pending status with preliminary assessment
        compliance_result = ComplianceResult(
            framework=IndiaFramework.DIGITAL_INDIA_ACT,
            overall_score=0.0,
            status=ComplianceStatus.PENDING,
            requirements_met=0,
            total_requirements=0,
            evidence_count=len(evidence),
            results={
                "status": "pending",
                "reason": "Digital India Act is an emerging framework. Preliminary requirements are being developed.",
                "note": "This framework will be updated as the legislation evolves.",
            },
            gaps=[],
            timestamp=datetime.utcnow(),
        )

        logger.info("Digital India Act compliance check completed with PENDING status")

        return compliance_result

    # ========================================================================
    # Compliance Assessment Logic (Task 3.2)
    # ========================================================================

    async def _assess_india_requirement(
        self,
        requirement: Dict[str, Any],
        evidence: Dict[str, Any],
        framework: IndiaFramework,
    ) -> Dict[str, Any]:
        """
        Assess if a specific India compliance requirement is met.

        Evaluates evidence against requirement criteria and determines
        compliance status with severity levels and remediation guidance.

        Args:
            requirement: Requirement definition from framework
            evidence: Collected evidence for assessment
            framework: Framework being assessed

        Returns:
            Assessment result with status, severity, and remediation steps

        Requirements: 1.6, 1.7, 2.7, 3.6
        """
        req_id = requirement["requirement_id"]
        controls = requirement.get("controls", [])
        key_requirements = requirement.get("key_requirements", [])
        
        # Check if evidence exists for this requirement
        evidence_found = False
        evidence_id = None
        failed_checks = []
        
        for control in controls:
            if control in evidence:
                evidence_found = True
                evidence_id = evidence[control].get("id")
                break
        
        if not evidence_found:
            # No evidence found - requirement not met
            return {
                "status": ComplianceStatus.NON_COMPLIANT,
                "severity": SeverityLevel.HIGH,
                "failed_checks": [f"No evidence provided for {requirement['name']}"],
                "remediation_steps": self._generate_remediation_steps(requirement, framework),
                "evidence_id": None,
            }
        
        # Evaluate evidence quality against key requirements
        evidence_data = evidence.get(controls[0], {})
        quality_score = self._evaluate_evidence_quality(evidence_data, key_requirements)
        
        if quality_score >= 0.8:
            status = ComplianceStatus.COMPLIANT
            severity = None
        elif quality_score >= 0.5:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            severity = SeverityLevel.MEDIUM
            failed_checks = self._identify_failed_checks(evidence_data, key_requirements)
        else:
            status = ComplianceStatus.NON_COMPLIANT
            severity = SeverityLevel.HIGH
            failed_checks = self._identify_failed_checks(evidence_data, key_requirements)
        
        return {
            "status": status,
            "severity": severity,
            "failed_checks": failed_checks,
            "remediation_steps": self._generate_remediation_steps(requirement, framework) if status != ComplianceStatus.COMPLIANT else [],
            "evidence_id": evidence_id,
        }

    async def _calculate_india_compliance_score(
        self,
        requirements_met: int,
        total_requirements: int,
    ) -> float:
        """
        Calculate overall India compliance score.

        Computes a percentage score based on requirements met.

        Args:
            requirements_met: Number of requirements met
            total_requirements: Total number of requirements

        Returns:
            Compliance score as percentage (0-100)

        Requirements: 1.6, 1.7, 2.7, 3.6
        """
        if total_requirements == 0:
            return 0.0
        
        score = (requirements_met / total_requirements) * 100
        return round(score, 2)

    async def _identify_india_gaps(
        self,
        compliance_results: List[ComplianceResult],
    ) -> List[ComplianceGap]:
        """
        Identify compliance gaps with India-specific remediation guidance.

        Analyzes compliance results to identify gaps and provides
        India-specific remediation recommendations with legal citations.

        Args:
            compliance_results: List of compliance check results

        Returns:
            List of identified compliance gaps with remediation steps

        Requirements: 1.6, 1.7, 2.7, 3.6
        """
        all_gaps = []
        
        for result in compliance_results:
            if result.gaps:
                for gap in result.gaps:
                    if isinstance(gap, dict):
                        gap_obj = ComplianceGap(**gap)
                    else:
                        gap_obj = gap
                    
                    all_gaps.append(gap_obj)
        
        # Sort gaps by severity
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
        }
        
        all_gaps.sort(
            key=lambda g: severity_order.get(g.severity, 4)
        )
        
        return all_gaps

    # ========================================================================
    # Report Generation (Task 3.3)
    # ========================================================================

    async def generate_india_compliance_report(
        self,
        system_id: str,
        user_id: str,
        compliance_results: List[ComplianceResult],
        system_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive India compliance report.

        Creates an audit-ready compliance report with executive summary,
        detailed findings, evidence references, and remediation recommendations
        with Indian legal citations.

        Args:
            system_id: AI system identifier
            user_id: User identifier
            compliance_results: List of compliance check results
            system_data: Optional system information for context

        Returns:
            Comprehensive compliance report

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
        """
        report_id = f"INDIA-COMPLIANCE-{system_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate overall metrics
        overall_score = sum(r.overall_score for r in compliance_results) / len(compliance_results) if compliance_results else 0
        overall_status = self._determine_compliance_status(overall_score)
        
        # Collect all gaps
        all_gaps = []
        for result in compliance_results:
            if result.gaps:
                all_gaps.extend(result.gaps if isinstance(result.gaps, list) else [result.gaps])
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            compliance_results,
            overall_score,
            system_data,
        )
        
        # Generate remediation recommendations
        remediation_recommendations = self._generate_remediation_recommendations(
            all_gaps,
            compliance_results,
        )
        
        report = {
            "report_id": report_id,
            "system_id": system_id,
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "system_info": {
                "name": system_data.get("name", "Unknown") if system_data else "Unknown",
                "description": system_data.get("description", "") if system_data else "",
                "type": system_data.get("type", "") if system_data else "",
            },
            "executive_summary": executive_summary,
            "overall_compliance": {
                "score": overall_score,
                "status": overall_status.value,
                "frameworks_assessed": [r.framework.value for r in compliance_results],
            },
            "detailed_findings": [
                {
                    "framework": r.framework.value,
                    "score": r.overall_score,
                    "status": r.status.value,
                    "requirements_met": r.requirements_met,
                    "total_requirements": r.total_requirements,
                    "gaps_count": len(r.gaps) if r.gaps else 0,
                }
                for r in compliance_results
            ],
            "compliance_gaps": all_gaps,
            "remediation_recommendations": remediation_recommendations,
            "legal_references": self._compile_legal_references(compliance_results),
            "next_review_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        }
        
        logger.info(f"Generated India compliance report: {report_id}")
        
        return report

    # ========================================================================
    # Compliance Trend Tracking (Task 3.4)
    # ========================================================================

    async def get_compliance_trends(
        self,
        system_id: str,
        framework: IndiaFramework,
        timeframe: str = "90d",
        historical_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Get compliance trends over time.

        Analyzes historical compliance scores to identify improvement or
        degradation patterns.

        Args:
            system_id: AI system identifier
            framework: Framework to analyze trends for
            timeframe: Timeframe for trend analysis (e.g., '30d', '90d', '1y')
            historical_results: Optional list of historical compliance results

        Returns:
            Trend analysis with improvement/degradation patterns

        Requirements: 7.7
        """
        if not historical_results:
            historical_results = []
        
        # Parse timeframe
        days = self._parse_timeframe(timeframe)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter results within timeframe
        filtered_results = [
            r for r in historical_results
            if datetime.fromisoformat(r.get("timestamp", "")) >= cutoff_date
        ]
        
        if not filtered_results:
            return {
                "system_id": system_id,
                "framework": framework.value,
                "timeframe": timeframe,
                "data_points": [],
                "trend": "insufficient_data",
                "improvement": None,
                "average_score": 0.0,
            }
        
        # Calculate trend metrics
        scores = [r.get("overall_score", 0) for r in filtered_results]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Determine trend direction
        if len(scores) >= 2:
            first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            improvement = second_half_avg > first_half_avg
            trend_direction = "improving" if improvement else "degrading"
        else:
            improvement = None
            trend_direction = "insufficient_data"
        
        trend_data = {
            "system_id": system_id,
            "framework": framework.value,
            "timeframe": timeframe,
            "data_points": [
                {
                    "timestamp": r.get("timestamp"),
                    "score": r.get("overall_score"),
                    "status": r.get("status"),
                }
                for r in filtered_results
            ],
            "trend": trend_direction,
            "improvement": improvement,
            "average_score": round(average_score, 2),
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }
        
        logger.info(
            f"Compliance trends for {system_id} ({framework.value}): "
            f"Average: {average_score:.1f}%, Trend: {trend_direction}"
        )
        
        return trend_data

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _determine_compliance_status(self, score: float) -> ComplianceStatus:
        """Determine compliance status based on score"""
        if score >= 90:
            return ComplianceStatus.COMPLIANT
        elif score >= 70:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _evaluate_evidence_quality(
        self,
        evidence_data: Dict[str, Any],
        key_requirements: List[str],
    ) -> float:
        """Evaluate quality of evidence against key requirements"""
        if not evidence_data:
            return 0.0
        
        # Check how many key requirements are addressed in evidence
        evidence_text = json.dumps(evidence_data).lower()
        matched_requirements = sum(
            1 for req in key_requirements
            if req.lower() in evidence_text
        )
        
        quality_score = matched_requirements / len(key_requirements) if key_requirements else 0.0
        return min(quality_score, 1.0)

    def _identify_failed_checks(
        self,
        evidence_data: Dict[str, Any],
        key_requirements: List[str],
    ) -> List[str]:
        """Identify which key requirements are not met by evidence"""
        evidence_text = json.dumps(evidence_data).lower()
        failed = [
            req for req in key_requirements
            if req.lower() not in evidence_text
        ]
        return failed

    def _generate_remediation_steps(
        self,
        requirement: Dict[str, Any],
        framework: IndiaFramework,
    ) -> List[str]:
        """Generate India-specific remediation steps for a requirement"""
        steps = []
        
        # Add framework-specific remediation guidance
        if framework == IndiaFramework.DPDP_ACT_2023:
            steps.extend([
                f"Review {requirement['name']} requirements per {requirement['legal_citation']}",
                "Collect evidence demonstrating compliance",
                "Document implementation of required controls",
                "Conduct internal audit to verify compliance",
            ])
        elif framework == IndiaFramework.NITI_AAYOG_PRINCIPLES:
            steps.extend([
                f"Implement {requirement['name']} as per NITI Aayog guidelines",
                "Conduct testing and validation",
                "Document compliance measures",
                "Establish monitoring and review procedures",
            ])
        elif framework == IndiaFramework.MEITY_GUIDELINES:
            steps.extend([
                f"Align with MeitY {requirement['name']} guidelines",
                "Implement required technical controls",
                "Establish governance procedures",
                "Conduct regular audits",
            ])
        
        return steps

    def _generate_executive_summary(
        self,
        compliance_results: List[ComplianceResult],
        overall_score: float,
        system_data: Optional[Dict[str, Any]],
    ) -> str:
        """Generate executive summary for compliance report"""
        system_name = system_data.get("name", "AI System") if system_data else "AI System"
        
        summary = f"""
EXECUTIVE SUMMARY

System: {system_name}
Assessment Date: {datetime.utcnow().strftime('%Y-%m-%d')}
Overall Compliance Score: {overall_score:.1f}%

This compliance assessment evaluates {system_name} against India's key AI regulatory frameworks:
- Digital Personal Data Protection (DPDP) Act 2023
- NITI Aayog Responsible AI Principles
- MeitY Guidelines for Responsible AI

"""
        
        if overall_score >= 90:
            summary += "ASSESSMENT: The system demonstrates strong compliance across all frameworks."
        elif overall_score >= 70:
            summary += "ASSESSMENT: The system shows good compliance with some areas requiring attention."
        elif overall_score >= 50:
            summary += "ASSESSMENT: The system requires significant improvements to meet compliance standards."
        else:
            summary += "ASSESSMENT: The system requires comprehensive remediation to achieve compliance."
        
        summary += f"""

Frameworks Assessed: {len(compliance_results)}
Compliant Frameworks: {sum(1 for r in compliance_results if r.overall_score >= 90)}/{len(compliance_results)}

Next Steps:
1. Review detailed findings and identified gaps
2. Prioritize remediation actions based on severity
3. Implement recommended controls
4. Conduct follow-up assessment in 90 days
"""
        
        return summary.strip()

    def _generate_remediation_recommendations(
        self,
        gaps: List[Any],
        compliance_results: List[ComplianceResult],
    ) -> List[Dict[str, Any]]:
        """Generate prioritized remediation recommendations"""
        recommendations = []
        
        # Group gaps by severity
        severity_groups = {}
        for gap in gaps:
            gap_dict = gap if isinstance(gap, dict) else gap.dict()
            severity = gap_dict.get("severity", "medium")
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(gap_dict)
        
        # Create recommendations in priority order
        priority_order = ["critical", "high", "medium", "low"]
        for priority in priority_order:
            if priority in severity_groups:
                for gap in severity_groups[priority]:
                    recommendations.append({
                        "priority": priority,
                        "control": gap.get("control_name"),
                        "category": gap.get("category"),
                        "legal_citation": gap.get("legal_citation"),
                        "remediation_steps": gap.get("remediation_steps", []),
                        "estimated_effort": self._estimate_remediation_effort(gap),
                    })
        
        return recommendations

    def _compile_legal_references(
        self,
        compliance_results: List[ComplianceResult],
    ) -> List[Dict[str, str]]:
        """Compile legal references from compliance results"""
        references = set()
        
        for result in compliance_results:
            if result.gaps:
                for gap in result.gaps:
                    gap_dict = gap if isinstance(gap, dict) else gap.dict()
                    citation = gap_dict.get("legal_citation")
                    if citation:
                        references.add(citation)
        
        return [{"citation": ref} for ref in sorted(references)]

    def _estimate_remediation_effort(self, gap: Dict[str, Any]) -> str:
        """Estimate effort required for remediation"""
        steps = gap.get("remediation_steps", [])
        if len(steps) <= 2:
            return "low"
        elif len(steps) <= 4:
            return "medium"
        else:
            return "high"

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to days"""
        if timeframe.endswith("d"):
            return int(timeframe[:-1])
        elif timeframe.endswith("m"):
            return int(timeframe[:-1]) * 30
        elif timeframe.endswith("y"):
            return int(timeframe[:-1]) * 365
        else:
            return 90  # Default to 90 days

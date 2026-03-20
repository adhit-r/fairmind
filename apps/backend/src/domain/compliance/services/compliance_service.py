"""
Compliance Domain Services.

Handles general compliance checking, reporting, and framework management.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

from core.base_service import AsyncBaseService
from core.container import service, ServiceLifetime
from core.exceptions import ValidationError
from core.interfaces import ILogger


class RegulatoryFramework(str, Enum):
    """Supported regulatory frameworks."""
    EU_AI_ACT = "eu_ai_act"
    GDPR = "gdpr"
    ISO_IEC_42001 = "iso_iec_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    IEEE_7000 = "ieee_7000"
    # India-specific frameworks
    DPDP_ACT = "dpdp_act"
    INDIA_AI_FRAMEWORK = "india_ai_framework"
    MEITY_GUIDELINES = "meity_guidelines"
    NITI_AAYOG_PRINCIPLES = "niti_aayog_principles"


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    framework: RegulatoryFramework
    overall_score: float
    status: ComplianceStatus
    requirements_met: int
    total_requirements: int
    evidence_count: int
    results: Dict[str, Any]
    gaps: List[Dict[str, Any]]
    timestamp: datetime


@service(lifetime=ServiceLifetime.SINGLETON)
class ComplianceService(AsyncBaseService):
    """
    Core compliance service.
    
    Handles general compliance checking and reporting.
    Base for region-specific compliance services.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.frameworks = self._initialize_frameworks()

    def _initialize_frameworks(self) -> Dict[RegulatoryFramework, List[Dict[str, Any]]]:
        """Initialize supported frameworks."""
        return {
            RegulatoryFramework.EU_AI_ACT: self._get_eu_ai_act_requirements(),
            RegulatoryFramework.GDPR: self._get_gdpr_requirements(),
            RegulatoryFramework.ISO_IEC_42001: self._get_iso_requirements(),
            RegulatoryFramework.NIST_AI_RMF: self._get_nist_requirements(),
        }

    async def check_compliance(
        self,
        framework: RegulatoryFramework,
        system_data: Dict[str, Any]
    ) -> ComplianceResult:
        """
        Check compliance against a regulatory framework.
        """
        self._validate_required(framework=framework, system_data=system_data)
        
        requirements = self.frameworks.get(framework, [])
        if not requirements:
            # If not in base frameworks, might be handled by specialized service
            # But here we just return empty result
            return self._create_empty_result(framework)
            
        results = {}
        compliant_count = 0
        gaps = []
        
        for req in requirements:
            status = self._assess_requirement(req, system_data)
            results[req["id"]] = {
                "status": status,
                "requirement": req["requirement"]
            }
            
            if status == ComplianceStatus.COMPLIANT:
                compliant_count += 1
            else:
                gaps.append({
                    "requirement_id": req["id"],
                    "description": req["requirement"],
                    "status": status
                })
        
        total = len(requirements)
        score = (compliant_count / total * 100) if total > 0 else 0
        
        result = ComplianceResult(
            framework=framework,
            overall_score=score,
            status=self._determine_status(score),
            requirements_met=compliant_count,
            total_requirements=total,
            evidence_count=len(system_data.get("evidence", [])),
            results=results,
            gaps=gaps,
            timestamp=datetime.now()
        )
        
        self._log_operation(
            "check_compliance",
            framework=framework,
            score=score,
            status=result.status
        )
        
        return result

    async def generate_report(
        self,
        system_id: str,
        frameworks: List[RegulatoryFramework],
        system_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate compliance report."""
        results = []
        for fw in frameworks:
            results.append(await self.check_compliance(fw, system_data))
            
        return {
            "report_id": f"RPT-{system_id}-{datetime.now().timestamp()}",
            "system_id": system_id,
            "timestamp": datetime.now().isoformat(),
            "frameworks": [fw.value for fw in frameworks],
            "results": [
                {
                    "framework": r.framework.value,
                    "score": r.overall_score,
                    "status": r.status.value,
                    "gaps": len(r.gaps)
                }
                for r in results
            ],
            "overall_compliance": sum(r.overall_score for r in results) / len(results) if results else 0
        }

    # Helper methods
    
    def _assess_requirement(self, req: Dict[str, Any], data: Dict[str, Any]) -> ComplianceStatus:
        """Assess single requirement (simplified)."""
        # In real implementation, this checks specific evidence keys
        evidence = data.get("evidence", {})
        if req["id"] in evidence:
            return ComplianceStatus.COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _determine_status(self, score: float) -> ComplianceStatus:
        if score >= 90: return ComplianceStatus.COMPLIANT
        if score >= 70: return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.NON_COMPLIANT

    def _create_empty_result(self, framework: RegulatoryFramework) -> ComplianceResult:
        return ComplianceResult(
            framework=framework,
            overall_score=0,
            status=ComplianceStatus.NOT_APPLICABLE,
            requirements_met=0,
            total_requirements=0,
            evidence_count=0,
            results={},
            gaps=[],
            timestamp=datetime.now()
        )

    # Framework Definitions (Simplified for migration)
    def _get_eu_ai_act_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "EU-AI-1", "requirement": "Risk Classification", "mandatory": True},
            {"id": "EU-AI-2", "requirement": "Transparency", "mandatory": True},
            {"id": "EU-AI-3", "requirement": "Human Oversight", "mandatory": True},
        ]

    def _get_gdpr_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "GDPR-1", "requirement": "Lawful Processing", "mandatory": True},
            {"id": "GDPR-2", "requirement": "Data Minimization", "mandatory": True},
        ]

    def _get_iso_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "ISO-1", "requirement": "AI Management System", "mandatory": True},
        ]

    def _get_nist_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "NIST-1", "requirement": "Governance", "mandatory": True},
        ]

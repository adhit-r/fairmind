"""
India Compliance Service.

Handles India-specific compliance frameworks (DPDP, NITI Aayog, MeitY).
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from core.container import service, ServiceLifetime, inject
from core.interfaces import ILogger
from .compliance_service import ComplianceService, RegulatoryFramework, ComplianceResult, ComplianceStatus


@service(lifetime=ServiceLifetime.SINGLETON)
class IndiaComplianceService(ComplianceService):
    """
    India-specific compliance service.
    
    Extends ComplianceService to add support for:
    - DPDP Act 2023
    - NITI Aayog Principles
    - MeitY Guidelines
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        # Add India frameworks
        self.frameworks.update({
            RegulatoryFramework.DPDP_ACT: self._get_dpdp_requirements(),
            RegulatoryFramework.INDIA_AI_FRAMEWORK: self._get_india_ai_requirements(),
            RegulatoryFramework.MEITY_GUIDELINES: self._get_meity_requirements(),
            RegulatoryFramework.NITI_AAYOG_PRINCIPLES: self._get_niti_aayog_requirements(),
        })

    async def check_dpdp_compliance(
        self,
        system_data: Dict[str, Any]
    ) -> ComplianceResult:
        """Check DPDP Act compliance."""
        return await self.check_compliance(RegulatoryFramework.DPDP_ACT, system_data)

    async def check_india_ai_compliance(
        self,
        system_data: Dict[str, Any]
    ) -> ComplianceResult:
        """Check India AI Framework compliance."""
        return await self.check_compliance(RegulatoryFramework.INDIA_AI_FRAMEWORK, system_data)

    # India Framework Definitions
    
    def _get_dpdp_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "DPDP-1", "requirement": "Consent Management", "mandatory": True},
            {"id": "DPDP-2", "requirement": "Purpose Limitation", "mandatory": True},
            {"id": "DPDP-3", "requirement": "Data Minimization", "mandatory": True},
            {"id": "DPDP-4", "requirement": "Data Localization", "mandatory": True},
            {"id": "DPDP-5", "requirement": "Grievance Redressal", "mandatory": True},
        ]

    def _get_india_ai_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "INDIA-AI-1", "requirement": "Safety and Reliability", "mandatory": True},
            {"id": "INDIA-AI-2", "requirement": "Equality and Inclusiveness", "mandatory": True},
            {"id": "INDIA-AI-3", "requirement": "Privacy and Security", "mandatory": True},
        ]

    def _get_meity_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "MEITY-1", "requirement": "Algorithmic Accountability", "mandatory": True},
            {"id": "MEITY-2", "requirement": "Ethical Deployment", "mandatory": True},
        ]

    def _get_niti_aayog_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"id": "NITI-1", "requirement": "Principle of Safety", "mandatory": True},
            {"id": "NITI-2", "requirement": "Principle of Equality", "mandatory": True},
        ]

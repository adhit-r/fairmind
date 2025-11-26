"""
Tests for AI Compliance Automation Service

Tests for LLM-based gap analysis, policy generation, and regulatory Q&A.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.ai_compliance_automation_service import AIComplianceAutomationService
from api.services.india_compliance_rag import IndiaComplianceRAG
from api.schemas.india_compliance import (
    IndiaFramework,
    ComplianceResult,
    ComplianceGap,
    SeverityLevel,
    ComplianceStatus,
)


@pytest.fixture
def rag_service():
    """Fixture for RAG service"""
    return IndiaComplianceRAG()


@pytest.fixture
async def ai_service():
    """Fixture for AI compliance automation service"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        service = AIComplianceAutomationService(api_key='test-key')
        return service


@pytest.fixture
def sample_compliance_result():
    """Fixture for sample compliance result"""
    return ComplianceResult(
        id="test-id",
        system_id="test-system",
        user_id="test-user",
        framework=IndiaFramework.DPDP_ACT_2023,
        overall_score=65.0,
        status=ComplianceStatus.PARTIAL,
        requirements_met=9,
        total_requirements=14,
        evidence_count=5,
        results={},
        gaps=[
            ComplianceGap(
                control_id="CM_001",
                control_name="Consent Management",
                category="Data Collection",
                severity=SeverityLevel.HIGH,
                failed_checks=["Consent withdrawal mechanism not implemented"],
                remediation_steps=["Implement consent withdrawal mechanism"],
                legal_citation="DPDP Act 2023, Section 6",
            ),
            ComplianceGap(
                control_id="DL_001",
                control_name="Data Localization",
                category="Data Storage",
                severity=SeverityLevel.CRITICAL,
                failed_checks=["Data stored outside India"],
                remediation_steps=["Migrate data to India"],
                legal_citation="DPDP Act 2023, Section 16",
            ),
        ],
        timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_system_context():
    """Fixture for sample system context"""
    return {
        "name": "AI Loan Approval System",
        "type": "Decision Support",
        "description": "AI system for loan approval decisions",
    }


# ============================================================================
# RAG Service Tests
# ============================================================================

class TestIndiaComplianceRAG:
    """Tests for India Compliance RAG service"""

    @pytest.mark.asyncio
    async def test_index_regulatory_documents(self, rag_service):
        """Test indexing regulatory documents"""
        await rag_service.index_regulatory_documents()
        
        assert rag_service.initialized
        assert len(rag_service.documents) > 0
        assert len(rag_service.document_index) > 0

    @pytest.mark.asyncio
    async def test_query_documents(self, rag_service):
        """Test querying documents"""
        await rag_service.index_regulatory_documents()
        
        results = await rag_service.query("What is consent?")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all("content" in doc for doc in results)

    @pytest.mark.asyncio
    async def test_query_by_framework(self, rag_service):
        """Test querying by specific framework"""
        await rag_service.index_regulatory_documents()
        
        results = await rag_service.query(
            "consent requirements",
            framework="dpdp_act_2023"
        )
        
        assert isinstance(results, list)
        assert all(doc.get("framework") == "dpdp_act_2023" for doc in results)

    @pytest.mark.asyncio
    async def test_query_by_section(self, rag_service):
        """Test querying specific section"""
        await rag_service.index_regulatory_documents()
        
        result = await rag_service.query_by_section("DPDP_6")
        
        assert result is not None
        assert result.get("section_id") == "DPDP_6"

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, rag_service):
        """Test keyword search"""
        await rag_service.index_regulatory_documents()
        
        results = await rag_service.search_by_keyword("consent")
        
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_framework_overview(self, rag_service):
        """Test getting framework overview"""
        await rag_service.index_regulatory_documents()
        
        overview = await rag_service.get_framework_overview("dpdp_act_2023")
        
        assert overview.get("framework") == "dpdp_act_2023"
        assert "total_sections" in overview
        assert "sections" in overview


# ============================================================================
# AI Compliance Automation Service Tests
# ============================================================================

class TestAIComplianceAutomationService:
    """Tests for AI Compliance Automation Service"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, ai_service):
        """Test service initialization"""
        assert ai_service is not None
        assert ai_service.rag is not None
        assert ai_service.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_prepare_gaps_summary(self, ai_service, sample_compliance_result):
        """Test gap summary preparation"""
        summary = ai_service._prepare_gaps_summary(sample_compliance_result.gaps)
        
        assert isinstance(summary, str)
        assert "Consent Management" in summary
        assert "Data Localization" in summary
        assert "CRITICAL" in summary

    @pytest.mark.asyncio
    async def test_create_gap_analysis_prompt(self, ai_service, sample_system_context):
        """Test gap analysis prompt creation"""
        gaps_summary = "Test gaps"
        prompt = ai_service._create_gap_analysis_prompt(
            IndiaFramework.DPDP_ACT_2023,
            gaps_summary,
            sample_system_context,
        )
        
        assert isinstance(prompt, str)
        assert "dpdp_act_2023" in prompt
        assert "AI Loan Approval System" in prompt

    @pytest.mark.asyncio
    async def test_create_remediation_plan_prompt(self, ai_service, sample_compliance_result):
        """Test remediation plan prompt creation"""
        prompt = ai_service._create_remediation_plan_prompt(
            sample_compliance_result.gaps,
            IndiaFramework.DPDP_ACT_2023,
            None,
        )
        
        assert isinstance(prompt, str)
        assert "dpdp_act_2023" in prompt
        assert "Consent Management" in prompt

    @pytest.mark.asyncio
    async def test_create_policy_generation_prompt(self, ai_service, sample_system_context):
        """Test policy generation prompt creation"""
        prompt = ai_service._create_policy_generation_prompt(
            sample_system_context,
            IndiaFramework.DPDP_ACT_2023,
            {"name": "Test Organization"},
        )
        
        assert isinstance(prompt, str)
        assert "privacy policy" in prompt.lower()
        assert "dpdp_act_2023" in prompt

    @pytest.mark.asyncio
    async def test_severity_to_priority(self, ai_service):
        """Test severity to priority conversion"""
        assert ai_service._severity_to_priority(SeverityLevel.CRITICAL) == 0
        assert ai_service._severity_to_priority(SeverityLevel.HIGH) == 1
        assert ai_service._severity_to_priority(SeverityLevel.MEDIUM) == 2
        assert ai_service._severity_to_priority(SeverityLevel.LOW) == 3

    @pytest.mark.asyncio
    async def test_calculate_total_effort(self, ai_service):
        """Test total effort calculation"""
        plan = [
            {"effort": "low"},
            {"effort": "low"},
            {"effort": "medium"},
        ]
        
        effort = ai_service._calculate_total_effort(plan)
        assert effort in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_generate_policy_compliance_checklist(self, ai_service):
        """Test policy compliance checklist generation"""
        checklist = ai_service._generate_policy_compliance_checklist(
            IndiaFramework.DPDP_ACT_2023
        )
        
        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert "Consent mechanism" in checklist[0]

    @pytest.mark.asyncio
    async def test_parse_gap_analysis_response(self, ai_service):
        """Test parsing gap analysis response"""
        response = """
        Key Insights:
        - Consent mechanism needs improvement
        - Data localization is critical
        
        Recommendations:
        - Implement consent withdrawal
        - Migrate data to India
        """
        
        parsed = ai_service._parse_gap_analysis_response(response)
        
        assert "insights" in parsed
        assert "recommendations" in parsed
        assert isinstance(parsed["insights"], list)
        assert isinstance(parsed["recommendations"], list)

    @pytest.mark.asyncio
    async def test_parse_remediation_plan_response(self, ai_service, sample_compliance_result):
        """Test parsing remediation plan response"""
        response = "Remediation plan details"
        
        plan = ai_service._parse_remediation_plan_response(
            response,
            sample_compliance_result.gaps,
        )
        
        assert isinstance(plan, list)
        assert len(plan) == len(sample_compliance_result.gaps)

    @pytest.mark.asyncio
    async def test_parse_risk_assessment(self, ai_service):
        """Test parsing risk assessment"""
        assessment = "Risk assessment details"
        
        parsed = ai_service._parse_risk_assessment(assessment)
        
        assert "risk_level" in parsed
        assert "likelihood" in parsed
        assert "impact" in parsed

    @pytest.mark.asyncio
    async def test_parse_regulatory_updates(self, ai_service):
        """Test parsing regulatory updates"""
        report = "Regulatory monitoring report"
        
        parsed = ai_service._parse_regulatory_updates(report)
        
        assert "updates" in parsed
        assert "alerts" in parsed


# ============================================================================
# Integration Tests
# ============================================================================

class TestAIComplianceAutomationIntegration:
    """Integration tests for AI compliance automation"""

    @pytest.mark.asyncio
    async def test_rag_initialization_and_query(self, rag_service):
        """Test RAG initialization and query flow"""
        # Initialize
        await rag_service.index_regulatory_documents()
        
        # Query
        results = await rag_service.query("What are data localization requirements?")
        
        # Verify
        assert len(results) > 0
        assert any("localization" in doc.get("content", "").lower() for doc in results)

    @pytest.mark.asyncio
    async def test_ai_service_with_rag(self, ai_service):
        """Test AI service integration with RAG"""
        # Initialize RAG
        await ai_service.rag.index_regulatory_documents()
        
        # Verify RAG is initialized
        assert ai_service.rag.initialized
        assert len(ai_service.rag.documents) > 0

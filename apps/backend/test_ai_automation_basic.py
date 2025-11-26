#!/usr/bin/env python3
"""
Basic integration test for AI Compliance Automation Service

This script tests the basic functionality without requiring pytest or external dependencies.
"""

import asyncio
import sys
from datetime import datetime

# Add the backend to path
sys.path.insert(0, '/Users/adhi/axonome/fairmind/apps/backend')

from api.services.india_compliance_rag import IndiaComplianceRAG
from api.schemas.india_compliance import (
    IndiaFramework,
    ComplianceGap,
    SeverityLevel,
)


async def test_rag_service():
    """Test RAG service functionality"""
    print("=" * 80)
    print("Testing India Compliance RAG Service")
    print("=" * 80)
    
    rag = IndiaComplianceRAG()
    
    # Test 1: Index documents
    print("\n[Test 1] Indexing regulatory documents...")
    await rag.index_regulatory_documents()
    
    assert rag.initialized, "RAG should be initialized"
    assert len(rag.documents) > 0, "Documents should be loaded"
    print(f"✓ Successfully indexed {len(rag.documents)} document sections")
    
    # Test 2: Query documents
    print("\n[Test 2] Querying documents...")
    results = await rag.query("What is consent?")
    
    assert isinstance(results, list), "Results should be a list"
    assert len(results) > 0, "Should return results"
    print(f"✓ Successfully retrieved {len(results)} relevant documents")
    
    # Test 3: Query by framework
    print("\n[Test 3] Querying by framework...")
    results = await rag.query("consent", framework="dpdp_act_2023")
    
    assert all(doc.get("framework") == "dpdp_act_2023" for doc in results), \
        "All results should be from DPDP framework"
    print(f"✓ Successfully filtered {len(results)} documents by framework")
    
    # Test 4: Query by section
    print("\n[Test 4] Querying specific section...")
    result = await rag.query_by_section("DPDP_6")
    
    assert result is not None, "Should find section DPDP_6"
    assert result.get("section_id") == "DPDP_6", "Should return correct section"
    print(f"✓ Successfully retrieved section: {result.get('title')}")
    
    # Test 5: Keyword search
    print("\n[Test 5] Searching by keyword...")
    results = await rag.search_by_keyword("consent")
    
    assert len(results) > 0, "Should find documents with keyword"
    print(f"✓ Found {len(results)} documents containing 'consent'")
    
    # Test 6: Framework overview
    print("\n[Test 6] Getting framework overview...")
    overview = await rag.get_framework_overview("dpdp_act_2023")
    
    assert overview.get("framework") == "dpdp_act_2023", "Should return correct framework"
    assert "total_sections" in overview, "Should include section count"
    print(f"✓ Framework overview: {overview.get('total_sections')} sections")
    
    print("\n" + "=" * 80)
    print("All RAG Service Tests Passed! ✓")
    print("=" * 80)


async def test_ai_service_helpers():
    """Test AI service helper methods"""
    print("\n" + "=" * 80)
    print("Testing AI Compliance Automation Service Helpers")
    print("=" * 80)
    
    # Import the service
    try:
        from api.services.ai_compliance_automation_service import AIComplianceAutomationService
    except ImportError as e:
        print(f"⚠ Skipping AI service tests (OpenAI not installed): {str(e)}")
        return
    
    # Create service with mock API key
    service = AIComplianceAutomationService(api_key='test-key')
    
    # Test 1: Severity to priority
    print("\n[Test 1] Testing severity to priority conversion...")
    assert service._severity_to_priority(SeverityLevel.CRITICAL) == 0
    assert service._severity_to_priority(SeverityLevel.HIGH) == 1
    assert service._severity_to_priority(SeverityLevel.MEDIUM) == 2
    assert service._severity_to_priority(SeverityLevel.LOW) == 3
    print("✓ Severity to priority conversion works correctly")
    
    # Test 2: Total effort calculation
    print("\n[Test 2] Testing total effort calculation...")
    plan = [
        {"effort": "low"},
        {"effort": "low"},
        {"effort": "medium"},
    ]
    effort = service._calculate_total_effort(plan)
    assert effort in ["low", "medium", "high"]
    print(f"✓ Total effort calculated: {effort}")
    
    # Test 3: Policy compliance checklist
    print("\n[Test 3] Testing policy compliance checklist generation...")
    checklist = service._generate_policy_compliance_checklist(
        IndiaFramework.DPDP_ACT_2023
    )
    assert isinstance(checklist, list)
    assert len(checklist) > 0
    print(f"✓ Generated checklist with {len(checklist)} items")
    
    # Test 4: Gap summary preparation
    print("\n[Test 4] Testing gap summary preparation...")
    gaps = [
        ComplianceGap(
            control_id="CM_001",
            control_name="Consent Management",
            category="Data Collection",
            severity=SeverityLevel.HIGH,
            failed_checks=["Consent withdrawal not implemented"],
            remediation_steps=["Implement withdrawal mechanism"],
            legal_citation="DPDP Act 2023, Section 6",
        ),
    ]
    summary = service._prepare_gaps_summary(gaps)
    assert isinstance(summary, str)
    assert "Consent Management" in summary
    print("✓ Gap summary prepared successfully")
    
    # Test 5: Prompt creation
    print("\n[Test 5] Testing prompt creation...")
    prompt = service._create_gap_analysis_prompt(
        IndiaFramework.DPDP_ACT_2023,
        "Test gaps",
        {"name": "Test System", "type": "AI", "description": "Test"},
    )
    assert isinstance(prompt, str)
    assert "dpdp_act_2023" in prompt
    print("✓ Gap analysis prompt created successfully")
    
    print("\n" + "=" * 80)
    print("All AI Service Helper Tests Passed! ✓")
    print("=" * 80)


async def main():
    """Run all tests"""
    try:
        await test_rag_service()
        await test_ai_service_helpers()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! ✓✓✓")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

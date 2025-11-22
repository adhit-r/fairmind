"""
Test script for Compliance & Reporting API endpoints
"""

import asyncio
from api.services.compliance_reporting_service import (
    ComplianceReportingService,
    RegulatoryFramework,
    RiskLevel,
)


async def test_compliance_service():
    """Test the compliance reporting service"""
    
    service = ComplianceReportingService()
    
    print("=" * 60)
    print("COMPLIANCE & REPORTING SERVICE TEST")
    print("=" * 60)
    
    # Test 1: List frameworks
    print("\n1. Testing Framework Listing...")
    frameworks = service.frameworks
    print(f"   ✓ Found {len(frameworks)} regulatory frameworks")
    for framework in frameworks:
        print(f"     - {framework}")
    
    # Test 2: Check compliance
    print("\n2. Testing Compliance Check...")
    system_data = {
        "name": "Test AI System",
        "description": "Sample system for testing",
        "risk_level": RiskLevel.HIGH,
        "evidence_EU_AI_1": [{"quality": 0.9, "description": "Risk classification completed"}],
        "evidence_EU_AI_2": [{"quality": 0.85, "description": "Transparency measures implemented"}],
        "evidence_EU_AI_3": [{"quality": 0.8, "description": "Human oversight in place"}],
        "evidence_EU_AI_4": [{"quality": 0.9, "description": "Data governance established"}],
        "evidence_EU_AI_5": [{"quality": 0.95, "description": "Technical documentation maintained"}],
        "evidence_EU_AI_6": [{"quality": 0.88, "description": "Logging system active"}],
        "evidence_EU_AI_7": [{"quality": 0.82, "description": "Accuracy monitoring in place"}],
        "evidence_EU_AI_8": [{"quality": 0.78, "description": "Cybersecurity measures in place"}],
    }
    
    result = await service.check_compliance(
        framework=RegulatoryFramework.EU_AI_ACT,
        system_data=system_data
    )
    
    print(f"   ✓ Compliance Score: {result['compliance_score']:.1f}%")
    print(f"   ✓ Overall Status: {result['overall_status']}")
    print(f"   ✓ Requirements Met: {result['compliant_requirements']}/{result['total_requirements']}")
    
    # Test 3: Generate audit report
    print("\n3. Testing Audit Report Generation...")
    audit_report = await service.generate_audit_report(
        system_id="TEST-001",
        system_data=system_data,
        frameworks=[RegulatoryFramework.EU_AI_ACT, RegulatoryFramework.GDPR]
    )
    
    print(f"   ✓ Report ID: {audit_report['report_id']}")
    print(f"   ✓ Overall Compliance: {audit_report['overall_compliance_score']:.1f}%")
    print(f"   ✓ Frameworks Assessed: {len(audit_report['frameworks_assessed'])}")
    
    # Test 4: Generate fairness documentation
    print("\n4. Testing Fairness Documentation...")
    model_data = {
        "name": "Test Model",
        "version": "1.0",
        "type": "classification",
        "purpose": "Testing fairness documentation"
    }
    
    bias_test_results = {
        "metrics": ["Statistical Parity", "Equal Opportunity"],
        "protected_attributes": ["gender", "race"],
        "scores": {
            "statistical_parity": 0.85,
            "equal_opportunity": 0.82
        },
        "bias_detected": True
    }
    
    documentation = await service.generate_fairness_documentation(
        model_data=model_data,
        bias_test_results=bias_test_results
    )
    
    print(f"   ✓ Document ID: {documentation['document_id']}")
    print(f"   ✓ Mitigation Strategies: {len(documentation['mitigation_strategies'])}")
    print(f"   ✓ Monitoring Frequency: {documentation['monitoring_plan']['frequency']}")
    
    # Test 5: Generate stakeholder dashboard data
    print("\n5. Testing Stakeholder Dashboard...")
    compliance_results = [result]
    
    dashboard_data = await service.generate_stakeholder_dashboard_data(
        system_id="TEST-001",
        compliance_results=compliance_results
    )
    
    print(f"   ✓ Overall Score: {dashboard_data['compliance_overview']['overall_score']:.1f}%")
    print(f"   ✓ High Priority Issues: {dashboard_data['risk_indicators']['high_priority_issues']}")
    print(f"   ✓ Compliance Trend: {dashboard_data['trends']['compliance_trend']}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_compliance_service())

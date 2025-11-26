"""
Quick test to verify India regulatory framework definitions
"""

from fairness_library.india_regulatory_frameworks import (
    get_framework,
    get_all_frameworks,
    get_framework_requirements,
    get_requirement,
    list_all_frameworks_summary,
    INDIA_COMPLIANCE_FRAMEWORKS
)


def test_frameworks_exist():
    """Test that all frameworks are defined"""
    frameworks = get_all_frameworks()
    assert len(frameworks) == 4, f"Expected 4 frameworks, got {len(frameworks)}"
    assert "dpdp_act_2023" in frameworks
    assert "niti_aayog_principles" in frameworks
    assert "meity_guidelines" in frameworks
    assert "digital_india_act" in frameworks
    print("✅ All 4 frameworks exist")


def test_dpdp_act_requirements():
    """Test DPDP Act 2023 requirements"""
    dpdp = get_framework("dpdp_act_2023")
    assert dpdp["total_requirements"] == 14
    requirements = get_framework_requirements("dpdp_act_2023")
    assert len(requirements) == 14
    
    # Test specific requirement
    consent = get_requirement("dpdp_act_2023", "dpdp_001")
    assert consent["name"] == "Consent Management"
    assert "DPDP Act 2023, Section 6" in consent["legal_citation"]
    print("✅ DPDP Act 2023: 14 requirements verified")


def test_niti_aayog_principles():
    """Test NITI Aayog principles"""
    niti = get_framework("niti_aayog_principles")
    assert niti["total_requirements"] == 12
    requirements = get_framework_requirements("niti_aayog_principles")
    assert len(requirements) == 12
    
    # Test specific principle
    equality = get_requirement("niti_aayog_principles", "niti_002")
    assert equality["name"] == "Equality"
    assert "NITI Aayog" in equality["legal_citation"]
    print("✅ NITI Aayog: 12 principles verified")


def test_meity_guidelines():
    """Test MeitY guidelines"""
    meity = get_framework("meity_guidelines")
    assert meity["total_requirements"] == 8
    requirements = get_framework_requirements("meity_guidelines")
    assert len(requirements) == 8
    
    # Test specific guideline
    rai = get_requirement("meity_guidelines", "meity_001")
    assert rai["name"] == "Responsible AI Development"
    assert "MeitY" in rai["legal_citation"]
    print("✅ MeitY Guidelines: 8 guidelines verified")


def test_digital_india_act():
    """Test Digital India Act (emerging)"""
    dia = get_framework("digital_india_act")
    assert dia["total_requirements"] == 6
    assert dia["status"] == "emerging"
    requirements = get_framework_requirements("digital_india_act")
    assert len(requirements) == 6
    
    # Test specific requirement
    di = get_requirement("digital_india_act", "dia_001")
    assert di["name"] == "Digital Infrastructure"
    print("✅ Digital India Act: 6 requirements verified (emerging)")


def test_framework_summaries():
    """Test framework summaries"""
    summaries = list_all_frameworks_summary()
    assert len(summaries) == 4
    
    for summary in summaries:
        assert "framework_id" in summary
        assert "name" in summary
        assert "description" in summary
        assert "status" in summary
        assert "total_requirements" in summary
    
    print("✅ Framework summaries: All 4 frameworks have proper structure")


def test_requirement_structure():
    """Test requirement structure"""
    req = get_requirement("dpdp_act_2023", "dpdp_001")
    
    required_fields = [
        "requirement_id",
        "name",
        "description",
        "legal_citation",
        "category",
        "controls",
        "key_requirements",
        "evidence_types"
    ]
    
    for field in required_fields:
        assert field in req, f"Missing field: {field}"
    
    assert isinstance(req["controls"], list)
    assert isinstance(req["key_requirements"], list)
    assert isinstance(req["evidence_types"], list)
    
    print("✅ Requirement structure: All required fields present")


def test_total_requirements():
    """Test total requirements across all frameworks"""
    total = 0
    for framework_id, framework in INDIA_COMPLIANCE_FRAMEWORKS.items():
        total += framework["total_requirements"]
    
    assert total == 40, f"Expected 40 total requirements, got {total}"
    print(f"✅ Total requirements: {total} (14 DPDP + 12 NITI + 8 MeitY + 6 Digital India)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing India Regulatory Framework Definitions")
    print("="*60 + "\n")
    
    test_frameworks_exist()
    test_dpdp_act_requirements()
    test_niti_aayog_principles()
    test_meity_guidelines()
    test_digital_india_act()
    test_framework_summaries()
    test_requirement_structure()
    test_total_requirements()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")

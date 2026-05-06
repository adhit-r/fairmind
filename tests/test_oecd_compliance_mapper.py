from src.application.services.compliance_mapper import ComplianceMapper, RiskCategory


def test_oecd_framework_loads_expected_controls():
    mapper = ComplianceMapper()

    oecd_controls = mapper.get_framework_controls("oecd_ai_principles")

    assert set(oecd_controls) >= {"inclusive_1", "human_1"}
    assert oecd_controls["inclusive_1"].framework == "oecd_ai_principles"
    assert oecd_controls["inclusive_1"].risk_level is RiskCategory.MEDIUM_RISK
    assert "impact_assessments" in oecd_controls["inclusive_1"].evidence_types


def test_oecd_policy_maps_to_oecd_controls():
    mapper = ComplianceMapper()

    mapping = mapper.map_policy_to_frameworks(
        "policy-oecd-human-oversight",
        "AI systems must respect human autonomy, enable human oversight, and document transparency.",
        {"framework": "oecd_ai_principles"},
    )

    assert "human_1" in mapping.regulatory_controls
    assert mapping.mapping_confidence > 0

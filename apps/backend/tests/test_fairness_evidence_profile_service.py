from datetime import datetime, timezone

from src.application.services.fairness_evidence_profile_service import (
    FairnessEvidenceProfileService,
)


def test_generate_profile_labels_missing_evidence_as_unknown_not_low():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-credit-001",
            "project_name": "Credit Pilot",
            "components": [
                {
                    "id": "credit.dataset.training",
                    "name": "Training Dataset",
                    "type": "dataset",
                    "version": "2026.05",
                    "dependencies": [],
                    "component_metadata": {
                        "downstream_components": ["credit.model.approval"],
                    },
                }
            ],
        },
        generated_at=datetime(2026, 5, 23, tzinfo=timezone.utc),
    )

    component = profile["components"][0]

    assert component["component_id"] == "credit.dataset.training"
    assert component["validation_state"] == "untested"
    assert component["review_status"] == "review_required"
    assert component["evidence_freshness"]["evidence_state"] == "unknown"
    assert component["risk_summary"]["overall_severity"] == "unknown"
    assert component["risk_summary"]["overall_severity"] != "low"
    assert "No protected attributes tested." in component["unknowns"]
    assert "No fairness metrics attached." in component["unknowns"]
    assert profile["risk_summary"]["unknown_count"] == len(component["unknowns"])


def test_generate_profile_preserves_simulated_evidence_state():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-hiring-001",
            "project_name": "Hiring Pilot",
            "components": [
                {
                    "id": "hiring.model.ranker",
                    "name": "Candidate Ranker",
                    "type": "model",
                    "version": "1.0.0",
                    "dependencies": ["hiring.dataset.applications"],
                    "component_metadata": {
                        "downstream_components": ["hiring.report.release"],
                    },
                }
            ],
        },
        evidence_records={
            "hiring.model.ranker": {
                "protected_attributes_tested": ["gender", "language"],
                "subgroup_coverage": {
                    "evaluated_groups": ["gender:female", "gender:male"],
                    "missing_groups": ["language:non_english"],
                    "coverage_notes": "Synthetic FairMind fixture.",
                },
                "fairness_metrics": [
                    {
                        "metric": "top_k_selection_gap",
                        "value": 0.16,
                        "threshold": 0.1,
                        "affected_groups": ["language:non_english"],
                        "evidence_state": "simulated",
                    }
                ],
                "bias_tests_run": [
                    {
                        "test_name": "FairMind synthetic ranking fairness test",
                        "test_type": "ranking_metric_test",
                        "result": "language subgroup exceeds threshold",
                        "evidence_state": "simulated",
                        "evidence_ref": "hiring-evidence-001",
                    }
                ],
                "evidence_refs": ["hiring-evidence-001"],
                "evidence_freshness": {
                    "last_updated": "2026-05-20T00:00:00Z",
                    "expires_at": "2026-08-20T00:00:00Z",
                    "staleness_rule": "Evidence expires after 90 days or model update.",
                    "evidence_state": "simulated",
                },
                "regulatory_mapping": [
                    {
                        "framework": "NIST AI RMF",
                        "control": "Measure 2.11",
                        "claim": "Fairness is measured across relevant subgroups.",
                        "evidence_state": "simulated",
                    }
                ],
            }
        },
        bias_results={
            "hiring.model.ranker": {
                "known_bias_risks": [
                    {
                        "risk_id": "hiring-risk-001",
                        "description": "Language-proxy risk remains visible.",
                        "affected_groups": ["language:non_english"],
                        "severity": "high",
                        "evidence_state": "simulated",
                    }
                ]
            }
        },
        remediation_records={
            "hiring.model.ranker": [
                {
                    "remediation_id": "hiring-remediation-001",
                    "description": "Feature deweighting proposed.",
                    "status": "attempted",
                    "validation_state": "untested",
                    "evidence_ref": "",
                }
            ]
        },
        generated_at=datetime(2026, 5, 23, tzinfo=timezone.utc),
    )

    component = profile["components"][0]

    assert profile["fairmind_context"]["platform_name"] == "FairMind"
    assert profile["fairmind_context"]["generation_mode"] == "fairmind_runtime_export"
    assert component["validation_state"] == "simulated"
    assert component["validation_state"] != "validated"
    assert component["fairness_metrics"][0]["evidence_state"] == "simulated"
    assert component["bias_tests_run"][0]["evidence_state"] == "simulated"
    assert component["known_bias_risks"][0]["severity"] == "high"
    assert component["risk_summary"]["simulated_evidence_count"] >= 3
    assert component["risk_summary"]["overall_severity"] == "high"


def test_generate_profile_uses_review_state_and_component_lineage():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-health-001",
            "project_name": "Healthcare Pilot",
            "organization": "FairMind",
            "components": [
                {
                    "id": "health.dataset.encounters",
                    "name": "Encounter Dataset",
                    "type": "dataset",
                    "version": "2026.05",
                    "dependencies": [],
                    "component_metadata": {
                        "downstream_components": ["health.model.triage"],
                    },
                },
                {
                    "id": "health.model.triage",
                    "name": "Triage Model",
                    "type": "model",
                    "version": "4.0.0",
                    "dependencies": ["health.dataset.encounters"],
                    "component_metadata": {
                        "downstream_components": ["health.report.release"],
                    },
                },
            ],
        },
        review_state={
            "status": "pending",
            "reviewer": None,
            "reviewed_at": None,
            "notes": "Awaiting clinical reviewer.",
            "pending_actions": ["Attach current fairness evaluation."],
        },
        generated_at=datetime(2026, 5, 23, tzinfo=timezone.utc),
    )

    dataset, model = profile["components"]

    assert profile["profile_id"] == "fairmind-healthcare-pilot-fairness-profile"
    assert profile["bom_ref"] == "bom-health-001"
    assert profile["system_name"] == "Healthcare Pilot"
    assert profile["review_summary"]["status"] == "pending"
    assert profile["review_summary"]["pending_actions"] == [
        "Attach current fairness evaluation."
    ]
    assert dataset["downstream_components"] == ["health.model.triage"]
    assert model["upstream_components"] == ["health.dataset.encounters"]
    assert model["downstream_components"] == ["health.report.release"]

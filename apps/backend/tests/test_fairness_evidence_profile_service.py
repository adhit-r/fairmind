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


def test_generate_profile_surfaces_stale_fairness_evidence_gap():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-credit-002",
            "project_name": "Credit Review",
            "components": [
                {
                    "id": "credit.model.score",
                    "name": "Credit Score Model",
                    "type": "model",
                    "version": "2.0.0",
                }
            ],
        },
        evidence_records={
            "credit.model.score": {
                "protected_attributes_tested": ["age", "gender"],
                "subgroup_coverage": {
                    "evaluated_groups": ["age:under_30", "gender:female"],
                    "missing_groups": [],
                },
                "fairness_metrics": [
                    {
                        "metric": "approval_rate_parity",
                        "value": 0.08,
                        "threshold": 0.1,
                        "affected_groups": [],
                        "evidence_state": "stale",
                    }
                ],
                "bias_tests_run": [
                    {
                        "test_name": "approval parity",
                        "test_type": "parity",
                        "result": "within threshold when last run",
                        "evidence_state": "stale",
                        "evidence_ref": "credit-evidence-001",
                    }
                ],
                "evidence_refs": ["credit-evidence-001"],
                "evidence_freshness": {
                    "last_updated": "2025-12-01T00:00:00Z",
                    "expires_at": "2026-03-01T00:00:00Z",
                    "staleness_rule": "Re-run after model update.",
                    "evidence_state": "stale",
                },
            }
        },
    )

    component = profile["components"][0]

    assert component["evidence_gap_type"] == ["stale_fairness_result"]
    assert component["claim_support"]["support_status"] == "unsupported"
    assert component["claim_support"]["supporting_evidence_refs"] == [
        "credit-evidence-001"
    ]
    assert component["evidence_state_reason"] == "Fairness evidence is stale."
    assert component["component_fault_localization"]["fault_component_id"] == (
        "credit.model.score"
    )
    assert component["component_fault_localization"]["upstream_faults"] == [
        "evidence_freshness.evidence_state"
    ]
    assert component["reviewer_required_action"] == "request_more_evidence"


def test_generate_profile_surfaces_unsupported_regulatory_claim_gap():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-report-001",
            "project_name": "Regulatory Review",
            "components": [
                {
                    "id": "release.report.fairness",
                    "name": "Release Fairness Report",
                    "type": "report",
                    "version": "2026.06",
                }
            ],
        },
        evidence_records={
            "release.report.fairness": {
                "protected_attributes_tested": ["gender"],
                "subgroup_coverage": {
                    "evaluated_groups": ["gender:female", "gender:male"],
                    "missing_groups": [],
                },
                "fairness_metrics": [
                    {
                        "metric": "selection_rate_gap",
                        "value": 0.04,
                        "threshold": 0.1,
                        "affected_groups": [],
                        "evidence_state": "current",
                    }
                ],
                "bias_tests_run": [
                    {
                        "test_name": "selection parity",
                        "test_type": "parity",
                        "result": "within threshold",
                        "evidence_state": "current",
                        "evidence_ref": "report-evidence-001",
                    }
                ],
                "evidence_refs": ["report-evidence-001"],
                "evidence_freshness": {
                    "last_updated": "2026-06-01T00:00:00Z",
                    "expires_at": "2026-09-01T00:00:00Z",
                    "staleness_rule": "Re-run quarterly.",
                    "evidence_state": "current",
                },
                "regulatory_mapping": [
                    {
                        "framework": "NIST AI RMF",
                        "control": "Measure 2.11",
                        "claim": "Fairness has reviewer-ready evidence.",
                        "evidence_state": "simulated",
                    }
                ],
            }
        },
    )

    component = profile["components"][0]

    assert component["evidence_gap_type"] == ["unsupported_regulatory_claim"]
    assert component["claim_support"]["support_status"] == "unsupported"
    assert component["component_fault_localization"]["upstream_faults"] == [
        "regulatory_mapping[0].evidence_state"
    ]
    assert component["component_fault_localization"]["downstream_claims_affected"] == [
        "Fairness has reviewer-ready evidence."
    ]
    assert component["reviewer_required_action"] == "request_more_evidence"


def test_generate_profile_surfaces_unvalidated_remediation_gap():
    service = FairnessEvidenceProfileService()

    profile = service.generate_profile(
        bom_document={
            "id": "bom-hiring-002",
            "project_name": "Hiring Remediation",
            "components": [
                {
                    "id": "hiring.model.ranker",
                    "name": "Candidate Ranker",
                    "type": "model",
                    "version": "1.1.0",
                }
            ],
        },
        evidence_records={
            "hiring.model.ranker": {
                "protected_attributes_tested": ["gender"],
                "subgroup_coverage": {
                    "evaluated_groups": ["gender:female", "gender:male"],
                    "missing_groups": [],
                },
                "fairness_metrics": [
                    {
                        "metric": "top_k_selection_gap",
                        "value": 0.13,
                        "threshold": 0.1,
                        "affected_groups": ["gender:female"],
                        "evidence_state": "current",
                    }
                ],
                "bias_tests_run": [
                    {
                        "test_name": "ranking fairness",
                        "test_type": "ranking",
                        "result": "gap exceeds threshold",
                        "evidence_state": "current",
                        "evidence_ref": "hiring-evidence-002",
                    }
                ],
                "evidence_refs": ["hiring-evidence-002"],
                "evidence_freshness": {
                    "last_updated": "2026-06-01T00:00:00Z",
                    "expires_at": "2026-09-01T00:00:00Z",
                    "staleness_rule": "Re-run quarterly.",
                    "evidence_state": "current",
                },
            }
        },
        remediation_records={
            "hiring.model.ranker": [
                {
                    "remediation_id": "hiring-remediation-002",
                    "description": "Adjust ranking features.",
                    "status": "attempted",
                    "validation_state": "simulated",
                    "evidence_ref": "simulation-only",
                }
            ]
        },
    )

    component = profile["components"][0]

    assert component["evidence_gap_type"] == ["unvalidated_remediation"]
    assert component["claim_support"]["support_status"] == "unsupported"
    assert component["evidence_state_reason"] == "Remediation is attempted or proposed without validated evidence."
    assert component["component_fault_localization"]["upstream_faults"] == [
        "remediation_history[0].validation_state"
    ]
    assert component["reviewer_required_action"] == "request_more_evidence"

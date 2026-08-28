import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import app
from api.models.ai_bom import AIBOMComponent, AIBOMDocument
from api.routes import real_ai_bom


class StubAIBOMService:
    def __init__(self, document):
        self.document = document
        self.calls: list[str] = []

    def get_bom_document(self, document_id: str):
        self.calls.append(document_id)
        if document_id == self.document.id:
            return self.document
        return None


@pytest.mark.asyncio
async def test_fairness_evidence_profile_route_exposes_missing_evidence_as_unknown(monkeypatch):
    document = AIBOMDocument(
        id="bom-loan-001",
        name="Loan Approval BOM",
        version="1.0.0",
        project_name="Loan Approval",
        organization="FairMind",
        overall_risk_level="medium",
        overall_compliance_status="partial",
        total_components=1,
        components=[
            AIBOMComponent(
                id="loan.dataset.training",
                name="Loan Training Dataset",
                type="dataset",
                version="2026.05",
                risk_level="medium",
                compliance_status="partial",
            )
        ],
    )
    monkeypatch.setattr(real_ai_bom, "ai_bom_service", StubAIBOMService(document))

    response = await real_ai_bom.get_fairness_evidence_profile("bom-loan-001")
    profile = response.data
    component = profile["components"][0]

    assert response.success is True
    assert profile["bom_ref"] == "bom-loan-001"
    assert profile["fairmind_context"]["platform_name"] == "FairMind"
    assert profile["review_summary"]["status"] == "review_required"
    assert component["component_id"] == "loan.dataset.training"
    assert component["validation_state"] == "untested"
    assert component["risk_summary"]["overall_severity"] == "unknown"
    assert "No fairness metrics attached." in component["unknowns"]
    assert "No bias tests attached." in component["unknowns"]


def test_fairness_evidence_profile_endpoint_is_not_registered_by_default() -> None:
    assert not any(
        route.path
        == "/api/v1/ai-bom/documents/{bom_id}/fairness-evidence-profile"
        and "GET" in (getattr(route, "methods", None) or set())
        for route in app.routes
    )


def test_quarantined_ai_bom_http_api_is_not_advertised() -> None:
    client = TestClient(app)

    root_payload = client.get("/").json()
    api_payload = client.get("/api").json()

    assert not any("AI BOM" in feature for feature in root_payload["features"])
    assert "ai_bom" not in api_payload["endpoints"]
    assert not any(tag["name"] == "ai-bom" for tag in app.openapi_tags)


def test_fairness_evidence_profile_router_fails_closed_when_mounted_directly(monkeypatch):
    document = AIBOMDocument(
        id="bom-direct-001",
        name="Direct Route BOM",
        version="1.0.0",
        project_name="Direct Route Coverage",
        organization="FairMind",
        overall_risk_level="medium",
        overall_compliance_status="partial",
        total_components=0,
    )
    service = StubAIBOMService(document)
    monkeypatch.setattr(real_ai_bom, "ai_bom_service", service)
    direct_app = FastAPI()
    direct_app.include_router(real_ai_bom.router, prefix="/api/v1")

    response = TestClient(direct_app).get(
        "/api/v1/ai-bom/documents/bom-direct-001/fairness-evidence-profile"
    )

    assert response.status_code == 404
    assert service.calls == []


@pytest.mark.asyncio
async def test_fairness_evidence_profile_route_preserves_component_metadata(monkeypatch):
    document = AIBOMDocument(
        id="bom-hiring-001",
        name="Hiring Ranker BOM",
        version="1.0.0",
        project_name="Hiring Ranker",
        organization="FairMind",
        overall_risk_level="high",
        overall_compliance_status="partial",
        total_components=1,
        risk_assessment={
            "fairness_review_state": {
                "status": "pending",
                "reviewer": "internal-reviewer",
                "pending_actions": ["Validate remediation before release approval."],
            }
        },
        components=[
            AIBOMComponent(
                id="hiring.model.ranker",
                name="Candidate Ranker",
                type="model",
                version="1.0.0",
                risk_level="high",
                compliance_status="partial",
                component_metadata={
                    "fairness_evidence": {
                        "protected_attributes_tested": ["gender", "language"],
                        "subgroup_coverage": {
                            "evaluated_groups": ["gender:female", "gender:male"],
                            "missing_groups": ["language:non_english"],
                            "coverage_notes": "FairMind synthetic route fixture.",
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
                                "test_name": "Synthetic ranking fairness test",
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
                    },
                    "bias_result": {
                        "known_bias_risks": [
                            {
                                "risk_id": "hiring-risk-001",
                                "description": "Language-proxy risk remains visible.",
                                "affected_groups": ["language:non_english"],
                                "severity": "high",
                                "evidence_state": "simulated",
                            }
                        ]
                    },
                    "remediation_history": [
                        {
                            "remediation_id": "hiring-remediation-001",
                            "description": "Feature deweighting proposed.",
                            "status": "attempted",
                            "validation_state": "untested",
                            "evidence_ref": "",
                        }
                    ],
                },
            )
        ],
    )
    monkeypatch.setattr(real_ai_bom, "ai_bom_service", StubAIBOMService(document))

    response = await real_ai_bom.get_fairness_evidence_profile("bom-hiring-001")
    profile = response.data
    component = profile["components"][0]

    assert response.success is True
    assert profile["review_summary"]["status"] == "pending"
    assert profile["review_summary"]["reviewer"] == "internal-reviewer"
    assert component["validation_state"] == "simulated"
    assert component["fairness_metrics"][0]["evidence_state"] == "simulated"
    assert component["known_bias_risks"][0]["severity"] == "high"
    assert component["risk_summary"]["overall_severity"] == "high"


@pytest.mark.asyncio
async def test_fairness_evidence_profile_route_surfaces_disconnected_monitor(monkeypatch):
    document = AIBOMDocument(
        id="bom-monitor-001",
        name="Monitor BOM",
        version="1.0.0",
        project_name="Monitor Coverage",
        organization="FairMind",
        overall_risk_level="medium",
        overall_compliance_status="partial",
        total_components=1,
        components=[
            AIBOMComponent(
                id="monitor.fairness.live",
                name="Fairness Live Monitor",
                type="monitor",
                version="1.0.0",
                risk_level="medium",
                compliance_status="partial",
                component_metadata={
                    "fairness_evidence": {
                        "protected_attributes_tested": ["gender"],
                        "subgroup_coverage": {
                            "evaluated_groups": ["gender:female", "gender:male"],
                            "missing_groups": [],
                        },
                        "fairness_metrics": [
                            {
                                "metric": "selection_rate_gap",
                                "value": 0.05,
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
                                "evidence_ref": "monitor-evidence-001",
                            }
                        ],
                        "evidence_refs": ["monitor-evidence-001"],
                        "evidence_freshness": {
                            "last_updated": "2026-06-01T00:00:00Z",
                            "expires_at": "2026-09-01T00:00:00Z",
                            "staleness_rule": "Re-run quarterly.",
                            "evidence_state": "current",
                        },
                        "live_feed_connected": False,
                    }
                },
            )
        ],
    )
    monkeypatch.setattr(real_ai_bom, "ai_bom_service", StubAIBOMService(document))

    response = await real_ai_bom.get_fairness_evidence_profile("bom-monitor-001")
    component = response.data["components"][0]

    assert response.success is True
    assert component["component_type"] == "monitor"
    assert component["evidence_gap_type"] == ["disconnected_monitor"]
    assert component["claim_support"]["support_status"] == "unsupported"
    assert component["component_fault_localization"]["fault_component_id"] == (
        "monitor.fairness.live"
    )
    assert component["component_fault_localization"]["upstream_faults"] == [
        "fairness_evidence.live_feed_connected"
    ]
    assert component["reviewer_required_action"] == "request_more_evidence"

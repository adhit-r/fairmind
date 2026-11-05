"""Mounted endpoints serve numbers computed from stored rows or request inputs, or leave them out.

Each test fails against the placeholder constants these routes used to return.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from database.governance_models import GovernanceRisk
from tests import pg
from tests.test_org_isolation_audit import (  # noqa: F401  (fixtures)
    A,
    B,
    ORG_A,
    ORG_B,
    _EngineConnection,
    _detect,
    _insert,
    _mini_app,
    clean_bias_history,
    client,
    db,
    legacy,
    stubbed_modules,
)




def _db_manager(monkeypatch, engine):
    import database.connection as connection

    class FakeManager:
        @contextmanager
        def get_session(self):
            session = sessionmaker(bind=engine)()
            try:
                yield session
            finally:
                session.close()

    monkeypatch.setattr(connection, "db_manager", FakeManager())


def test_detect_names_the_metrics_it_did_not_compute_instead_of_inventing_them(client, clean_bias_history):
    body = _detect(client, A).json()
    assert "confidence" not in body
    assert body["test_results"]
    for result in body["test_results"]:
        assert "fairness_metrics" not in result and "confidence" not in result
        requested = result["metadata"]["template"]["fairness_metrics"]
        assert result["not_computed"] == [*requested, "confidence"]
    for breakdown in body["bias_breakdown"].values():
        assert "confidence" not in breakdown


def test_custom_templates_are_not_reported_as_stored(client):
    response = client.post("/api/v1/bias-detection/templates", headers=A, json={"template": {"id": "mine"}})
    assert response.status_code == 501


def test_modern_bias_evaluation_history_lists_the_organisations_stored_rows(db, stubbed_modules, monkeypatch):
    engine = db[0]
    for org, name, day in ((ORG_A, "a-old", "2026-01-01"), (ORG_A, "a-new", "2026-02-01"), (ORG_B, "b-test", "2026-03-01")):
        _insert(engine, "bias_test_results", id=name, test_name=name, bias_score=0.3, is_biased=True, confidence=0.7,
                category="gender", created_at=day, org_id=org)
    _db_manager(monkeypatch, engine)

    with _mini_app(db, "api.routes.modern_bias_detection") as mini:
        assert mini.get("/api/v1/modern-bias/evaluation-history").status_code == 401
        history = mini.get("/api/v1/modern-bias/evaluation-history?limit=5", headers=A).json()["history"]
        assert [row["test_name"] for row in history] == ["a-new", "a-old"]
        assert history[0]["bias_score"] == 0.3
        only = mini.get("/api/v1/modern-bias/evaluation-history?limit=1", headers=A).json()["history"]
        assert [row["test_name"] for row in only] == ["a-new"]


def test_modern_bias_detection_results_carry_no_invented_compliance_or_confidence(db, stubbed_modules, monkeypatch):
    engine = db[0]
    _insert(engine, "bias_test_results", id="a-test", test_name="a-test", bias_score=0.2, is_biased=False,
            confidence=0.9, category="gender", explainability_method="shap", insights="i",
            created_at="2026-01-01", org_id=ORG_A)
    _db_manager(monkeypatch, engine)

    with _mini_app(db, "api.routes.modern_bias_detection") as mini:
        a = mini.get("/api/v1/modern-bias/detection-results", headers=A).json()["data"]
        assert [e["method"] for e in a["explainability_analysis"]] == ["shap"]
        assert "confidence" not in a["explainability_analysis"][0]
        assert a["compliance_status"] == {"fairness_score": 0.8}

        # No stored tests: nothing to score, so no risk level, fairness or bias rate is claimed.
        b = mini.get("/api/v1/modern-bias/detection-results", headers=B).json()["data"]
        assert b["overall_risk"] == "unknown"
        assert b["compliance_status"] == {"fairness_score": None}
        assert b["evaluation_summary"] == {"total_tests_run": 0, "biased_tests": 0, "bias_rate": None}


def test_core_metrics_are_computed_from_the_organisations_rows_or_left_out(client, legacy, db, monkeypatch):
    from api.routes import core as core_routes

    engine, _ = legacy
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE simulation_runs (id TEXT PRIMARY KEY, status TEXT, org_id TEXT)"))
        conn.execute(text("CREATE TABLE compliance_results (id TEXT PRIMARY KEY, compliance_score REAL, "
                          "framework TEXT, created_at TIMESTAMPTZ, org_id TEXT)"))
    connection = _EngineConnection(engine)

    @asynccontextmanager
    async def engine_connection():
        yield connection

    monkeypatch.setattr(core_routes, "get_db_connection", engine_connection)

    with db[1]() as session:
        session.add_all([
            GovernanceRisk(id="r-open", system_id="system-a", title="open", severity="critical", status="open"),
            GovernanceRisk(id="r-accepted", system_id="system-a", title="accepted", severity="critical", status="accepted"),
            GovernanceRisk(id="r-high", system_id="system-a", title="high", severity="high", status="open"),
            GovernanceRisk(id="r-b", system_id="system-b", title="b", severity="critical", status="open"),
        ])
        session.commit()
    recent = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    _insert(engine, "bias_test_results", id="t-a", test_name="t", bias_score=0.25, is_biased=True, created_at=recent, org_id=ORG_A)

    a = client.get("/api/v1/core/governance/metrics", headers=A).json()["data"]
    assert (a["criticalRisks"], a["biasAlerts"], a["fairnessScore"]) == (1, 1, 75.0)
    assert not {"llmSafetyScore", "nistCompliance"} & a.keys()

    b = client.get("/api/v1/core/governance/metrics", headers=B).json()["data"]
    assert (b["totalModels"], b["criticalRisks"], b["fairnessScore"]) == (0, 1, None)

    summary = client.get("/api/v1/core/metrics/summary", headers=B).json()["data"]
    assert not {"active_analyses", "security_score"} & summary.keys()
    assert (summary["bias_score"], summary["compliance_score"]) == (None, None)


def test_detect_reports_no_score_when_no_output_could_be_scored(client, clean_bias_history):
    # The text templates score output["text"]; these outputs carry none, so nothing is scored.
    body = client.post("/api/v1/bias-detection/detect", headers=A, json={
        "model_type": "text_generation",
        "test_category": "representational",
        "model_outputs": [
            {"prompt": "The doctor was", "output": "The doctor was a man"},
            {"prompt": "The nurse was", "output": "The nurse was a woman"},
        ],
    }).json()
    assert body["overall_bias_score"] is None
    assert body["test_results"]
    assert all(r["bias_score"] is None and r["detected_bias"] is None for r in body["test_results"])
    assert not any("Minimal bias" in r for r in body["recommendations"])


def test_modern_bias_detection_results_average_only_the_scored_tests(db, stubbed_modules, monkeypatch):
    engine = db[0]
    _insert(engine, "bias_test_results", id="scored", test_name="scored", bias_score=0.8, is_biased=True,
            category="gender", created_at="2026-01-02", org_id=ORG_A)
    _insert(engine, "bias_test_results", id="unscored", test_name="unscored", bias_score=None, is_biased=False,
            category="gender", created_at="2026-01-01", org_id=ORG_A)
    _db_manager(monkeypatch, engine)

    with _mini_app(db, "api.routes.modern_bias_detection") as mini:
        a = mini.get("/api/v1/modern-bias/detection-results", headers=A).json()["data"]
    assert a["overall_risk"] == "high"
    assert a["compliance_status"]["fairness_score"] == pytest.approx(0.2)
    assert a["evaluation_summary"]["total_tests_run"] == 2


def test_modern_bias_detection_results_query_runs_on_postgres(db, stubbed_modules, monkeypatch):
    # GROUP BY rather than DISTINCT ... ORDER BY an unselected column, which PostgreSQL rejects.
    engine = pg.fresh_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bias_test_results CASCADE"))
        conn.execute(text("CREATE TABLE bias_test_results (id TEXT PRIMARY KEY, test_name TEXT, "
                          "bias_score DOUBLE PRECISION, is_biased BOOLEAN, confidence DOUBLE PRECISION, "
                          "category TEXT, explainability_method TEXT, insights TEXT, "
                          "created_at TIMESTAMPTZ DEFAULT NOW(), org_id TEXT)"))
    for name, method, day in (("old", "shap", "2026-01-01"), ("again", "shap", "2026-01-03"), ("lime", "lime", "2026-01-02")):
        _insert(engine, "bias_test_results", id=name, test_name=name, bias_score=0.2, is_biased=False,
                explainability_method=method, insights="i", created_at=day, org_id=ORG_A)
    _db_manager(monkeypatch, engine)

    with _mini_app(db, "api.routes.modern_bias_detection") as mini:
        response = mini.get("/api/v1/modern-bias/detection-results", headers=A)
    assert response.status_code == 200, response.text
    assert [e["method"] for e in response.json()["data"]["explainability_analysis"]] == ["shap", "lime"]

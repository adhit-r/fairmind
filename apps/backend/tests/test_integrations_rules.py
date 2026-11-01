"""Rule checks for integration discovery suggestions."""

from api.routes.integrations import suggest_stage_mlflow, suggest_tier


def test_declared_tier_wins():
    assert suggest_tier("anything", {"fairmind.risk_tier": "critical"}, "ml_model") == "critical"


def test_high_impact_keywords_raise_tier():
    assert suggest_tier("loan-scoring-v4", {}, "ml_model") == "high"
    assert suggest_tier("churn-propensity", {}, "ml_model") == "medium"
    assert suggest_tier("resume screener", {}, "ai_assisted_dev") == "low"


def test_mlflow_stage_mapping():
    assert suggest_stage_mlflow([{"current_stage": "Production"}], {}) == "operate"
    assert suggest_stage_mlflow([{"current_stage": "None"}], {"champion": "3"}) == "operate"
    assert suggest_stage_mlflow([{"current_stage": "Staging"}], {}) == "govern"
    assert suggest_stage_mlflow([{"current_stage": "None"}], {}) == "assess"
    assert suggest_stage_mlflow([], {}) == "onboard"

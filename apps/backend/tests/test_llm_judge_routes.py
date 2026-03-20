"""Tests for LLM-as-Judge API routes."""

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_llm_judge_models_endpoint():
    response = client.get("/api/v1/bias/llm-judge/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "categories" in data
    assert len(data["models"]) > 0
    assert "gender" in data["categories"]


def test_llm_judge_batch_evaluate_endpoint():
    response = client.post(
        "/api/v1/bias/llm-judge/evaluate-batch",
        json={
            "text": "The engineer solved the issue quickly while the nurse was caring.",
            "judge_model": "gpt-4-turbo",
            "bias_categories": ["gender", "professional"],
            "target_model": "test-model",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert "results" in data
    assert "gender" in data["results"]


def test_llm_judge_single_evaluate_endpoint():
    response = client.post(
        "/api/v1/bias/llm-judge/evaluate",
        json={
            "text": "He is a decisive leader and she is a caring helper.",
            "judge_model": "gpt-4-turbo",
            "bias_categories": ["gender"],
            "target_model": "test-model",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bias_category"] == "gender"
    assert "bias_score" in data
    assert "reasoning" in data


def test_llm_judge_multi_judge_json_body_endpoint():
    response = client.post(
        "/api/v1/bias/llm-judge/evaluate-with-multiple-judges",
        json={
            "text": "The leader made a strong decision and the assistant supported him.",
            "judge_models": ["gpt-4-turbo", "claude-3-opus"],
            "bias_categories": ["gender", "race"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "judges_used" in data
    assert len(data["judges_used"]) >= 1

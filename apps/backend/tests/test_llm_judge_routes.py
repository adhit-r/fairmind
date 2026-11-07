"""Tests for LLM-as-Judge API routes."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.application.services import llm_as_judge_service as judge_module
from src.application.services.llm_as_judge_service import JudgeModel, LLMAsJudgeService
from tests.auth_helpers import auth_headers


client = TestClient(app, headers=auth_headers())


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
            "judge_model": "gpt-6.1-sol",
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
            "judge_model": "gpt-6.1-sol",
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
            "judge_models": ["gpt-6.1-sol", "claude-sonnet-5-5"],
            "bias_categories": ["gender", "race"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "judges_used" in data
    assert len(data["judges_used"]) >= 1


def test_llm_judge_models_endpoint_lists_every_judge():
    data = client.get("/api/v1/bias/llm-judge/models").json()
    assert [m["value"] for m in data["models"]] == [m.value for m in JudgeModel]


@pytest.mark.parametrize("retired", ["gpt-4-turbo", "claude-3-opus", "gemini-pro"])
def test_llm_judge_rejects_retired_models(retired):
    response = client.post(
        "/api/v1/bias/llm-judge/evaluate",
        json={"text": "Some text.", "judge_model": retired, "bias_categories": ["gender"]},
    )
    assert response.status_code == 400


class _Recorder:
    """Stands in for aiohttp.ClientSession and records the one request a judge call makes."""

    calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def post(self, url, headers=None, json=None):
        _Recorder.calls.append({"url": url, "headers": headers or {}, "json": json})
        return _Response(url)


class _Response:
    def __init__(self, url):
        self.url = url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    async def json(self):
        if "openai" in self.url:
            return {"choices": [{"message": {"content": "ok"}}]}
        if "anthropic" in self.url:
            # Claude 5 models think by default; the thinking block comes first.
            return {"content": [{"type": "thinking", "thinking": "", "signature": "s"}, {"type": "text", "text": "ok"}]}
        return {"candidates": [{"content": {"parts": [{"text": "draft", "thought": True}, {"text": "ok"}]}}]}


@pytest.mark.parametrize("judge", list(JudgeModel))
def test_each_judge_calls_its_provider_with_its_own_model_id(judge, monkeypatch):
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.setenv(key, "test-key-value")
    monkeypatch.setattr(judge_module.aiohttp, "ClientSession", _Recorder)
    _Recorder.calls = []

    assert asyncio.run(LLMAsJudgeService()._call_judge_llm("prompt", judge)) == "ok"

    (call,) = _Recorder.calls
    host = {"gpt-": "api.openai.com", "claude-": "api.anthropic.com", "gemini-": "generativelanguage.googleapis.com"}
    assert host[next(p for p in host if judge.value.startswith(p))] in call["url"]
    sent_model = (call["json"] or {}).get("model") or call["url"].split("/models/")[1].split(":")[0]
    assert sent_model == judge.value
    assert "test-key-value" not in call["url"]
    assert "temperature" not in (call["json"] or {})

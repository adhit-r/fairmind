"""Tests for LLM-as-Judge API routes."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.application.services import llm_as_judge_service as judge_module
from config.settings import settings
from src.application.services.llm_as_judge_service import JudgeModel, LLMAsJudgeService
from tests.auth_helpers import auth_headers
from tests.grok_helpers import fake_grok, recorded, stream


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


API_JUDGES = [m for m in JudgeModel if not m.value.startswith("grok-")]


def test_llm_judge_models_endpoint_lists_every_judge_and_grok_only_with_the_cli(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    data = client.get("/api/v1/bias/llm-judge/models").json()
    assert [m["value"] for m in data["models"]] == [m.value for m in API_JUDGES]
    fake_grok(monkeypatch, tmp_path)
    data = client.get("/api/v1/bias/llm-judge/models").json()
    assert [m["value"] for m in data["models"]] == [m.value for m in JudgeModel]
    assert {"value": "grok-4.7", "label": "Grok 4.7 (Grok CLI, local)"} in data["models"]


@pytest.mark.parametrize(
    "path, body",
    [
        ("/evaluate", {"judge_model": "grok-4.7"}),
        ("/evaluate-batch", {"judge_model": "grok-4.6"}),
        ("/evaluate-with-multiple-judges", {"judge_models": ["gpt-6.1-sol", "grok-4.7"]}),
    ],
)
def test_a_grok_judge_is_refused_when_the_cli_is_not_enabled(path, body, monkeypatch):
    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    response = client.post(f"/api/v1/bias/llm-judge{path}", json={"text": "Some text.", "bias_categories": ["gender"], **body})
    assert (response.status_code, response.json()["detail"]) == (400, "The Grok CLI is not enabled on this server")


def test_a_grok_judge_evaluation_runs_on_the_cli(monkeypatch, tmp_path):
    verdict = '{"bias_score": 0.8, "confidence": 0.9, "detected_biases": ["role stereotype"], "reasoning": "He leads, she helps.", "evidence": [], "recommendations": [], "severity": "high"}'
    calls = fake_grok(monkeypatch, tmp_path, out=stream(verdict))
    response = client.post(
        "/api/v1/bias/llm-judge/evaluate",
        json={"text": "He is a decisive leader and she is a caring helper.", "judge_model": "grok-4.6", "bias_categories": ["gender"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert (data["judge_model"], data["bias_score"], data["severity"], data["detected_biases"]) == ("grok-4.6", 0.8, "high", ["role stereotype"])
    (call,) = recorded(calls)
    assert "--model=grok-4.6" in call["argv"] and "--deny=*" in call["argv"]
    assert any(a.startswith("--single=") and "caring helper" in a for a in call["argv"])


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


@pytest.mark.parametrize("judge", API_JUDGES)
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

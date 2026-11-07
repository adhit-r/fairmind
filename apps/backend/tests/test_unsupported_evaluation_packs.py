"""Canonical quarantine contract for unsupported evaluation packs."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.auth_helpers import auth_headers
from src.domain.assurance.evaluation_v2 import TARGET_KINDS


client = TestClient(app, headers=auth_headers())

UNSUPPORTED_PACK_PREFIXES = (
    "/api/v1/modern-bias",
    "/api/v1/multimodal-bias",
)


def test_unsupported_evaluation_pack_routes_are_not_mounted() -> None:
    mounted_paths = set(app.openapi()["paths"])
    # Control: the kept LLM judge is visible here, so an empty schema cannot pass this test.
    assert any(path.startswith("/api/v1/bias/llm-judge") for path in mounted_paths)

    for prefix in UNSUPPORTED_PACK_PREFIXES:
        assert not any(path.startswith(prefix) for path in mounted_paths)


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    (
        (
            "post",
            "/api/v1/modern-bias/comprehensive-evaluation",
            {"model_description": "test", "model_type": "llm", "selected_tests": ["weat"]},
        ),
        (
            "post",
            "/api/v1/multimodal-bias/image-detection",
            {"model_outputs": []},
        ),
    ),
)
def test_unsupported_evaluation_pack_requests_fail_closed(
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = client.request(method, path, json=payload)

    # No route matches an unmounted family, so every method fails closed as 404.
    assert response.status_code == 404


def test_quarantine_preserves_assurance_v2_target_kind_vocabulary() -> None:
    assert TARGET_KINDS == {
        "predictive_model",
        "llm_application",
        "agent",
        "code_generator",
        "image_generator",
        "audio_model",
        "video_model",
        "multimodal_system",
        "vision_model",
    }

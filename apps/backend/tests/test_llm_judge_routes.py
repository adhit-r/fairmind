"""Canonical quarantine contract for unsupported evaluation packs."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.auth import User as AuthUser, UserRole, auth_manager
from middleware.security import _DEVELOPMENT_PUBLIC_PATH_PREFIXES
from src.domain.assurance.evaluation_v2 import TARGET_KINDS


client = TestClient(app)
client.headers["Authorization"] = "Bearer " + auth_manager.create_access_token(
    AuthUser(
        id="unsupported-pack-test-user",
        email="unsupported-pack@example.test",
        username="unsupported-pack-test-user",
        role=UserRole.ANALYST,
        created_at=datetime.now(timezone.utc),
        permissions=[],
    )
)

UNSUPPORTED_PACK_PREFIXES = (
    "/api/v1/bias/llm-judge",
    "/api/v1/modern-bias",
    "/api/v1/multimodal-bias",
)


def test_unsupported_evaluation_pack_routes_are_not_mounted() -> None:
    mounted_paths = {route.path for route in app.routes}

    for prefix in UNSUPPORTED_PACK_PREFIXES:
        assert not any(path.startswith(prefix) for path in mounted_paths)


def test_unsupported_evaluation_pack_families_are_not_development_public() -> None:
    for family in ("llm-judge", "modern-bias", "multimodal-bias"):
        assert not any(family in prefix for prefix in _DEVELOPMENT_PUBLIC_PATH_PREFIXES)


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    (
        ("get", "/api/v1/bias/llm-judge/models", None),
        (
            "post",
            "/api/v1/bias/llm-judge/evaluate",
            {
                "text": "Evaluate this response.",
                "judge_model": "gpt-4-turbo",
                "bias_categories": ["gender"],
                "target_model": "test-model",
            },
        ),
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
def test_unsupported_evaluation_pack_requests_fail_closed_behind_global_preflight(
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = client.request(method, path, json=payload)

    # The application-wide OPTIONS catch-all is the only matching route, so
    # Starlette reports non-preflight methods as unavailable with Allow: OPTIONS.
    assert response.status_code == 405
    assert response.headers["allow"] == "OPTIONS"
    assert response.json() == {"detail": "Method Not Allowed"}


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

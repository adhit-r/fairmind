import asyncio
from datetime import datetime, timezone

import httpx

from api.routes import consent
from config.auth import TokenData


def _user():
    now = datetime.now(timezone.utc)
    return TokenData(user_id="u-1", email="a@acme.test", role="viewer", token_type="access", exp=now, iat=now)


def _configure(monkeypatch, state_items):
    for k, v in {"olai_base_url": "https://olai.test", "olai_api_key": "ck_x", "olai_tenant_id": "fm", "olai_collection_point_id": "cp_1"}.items():
        monkeypatch.setattr(consent.settings, k, v)

    def handler(req: httpx.Request):
        if req.url.path.endswith("/consent-state"):
            return httpx.Response(200, json={"items": state_items})
        return httpx.Response(201, json={"token": "pt_abc", "expiresAt": "x"})

    real = httpx.AsyncClient
    monkeypatch.setattr(consent.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


def test_off_when_unconfigured(monkeypatch):
    monkeypatch.setattr(consent.settings, "olai_base_url", "")
    assert asyncio.run(consent.consent_status(_user())) == {"required": False}


def test_undecided_user_gets_hosted_page(monkeypatch):
    _configure(monkeypatch, [{"basis": "consent", "status": "none"}])
    out = asyncio.run(consent.consent_status(_user()))
    assert out["required"] and out["url"].startswith("https://olai.test/olai/api/v1/c/fm/cp_1?t=pt_abc&redirect=")


def test_decided_user_not_asked(monkeypatch):
    _configure(monkeypatch, [{"basis": "consent", "status": "denied"}, {"basis": "legitimate_use", "status": "none"}])
    assert asyncio.run(consent.consent_status(_user())) == {"required": False}

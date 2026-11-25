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
            assert req.url.params.get("purposes") == "all"  # else Olai omits undecided purposes
            return httpx.Response(200, json={"items": state_items})
        if "/collection-points/" in req.url.path:
            return httpx.Response(200, json={"purposes": [{"key": "emails"}, {"key": "ops"}]})
        return httpx.Response(201, json={"token": "pt_abc", "expiresAt": "x"})

    real = httpx.AsyncClient
    monkeypatch.setattr(consent.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


def test_off_when_unconfigured(monkeypatch):
    monkeypatch.setattr(consent.settings, "olai_base_url", "")
    assert asyncio.run(consent.consent_status(_user())) == {"required": False}


def test_undecided_user_gets_hosted_page(monkeypatch):
    _configure(monkeypatch, [{"purposeKey": "emails", "basis": "consent", "status": "none"}])
    out = asyncio.run(consent.consent_status(_user()))
    assert out["required"] and out["url"].startswith("https://olai.test/olai/api/v1/c/fm/cp_1?t=pt_abc&redirect=")


def test_decided_user_not_asked(monkeypatch):
    _configure(monkeypatch, [{"purposeKey": "emails", "basis": "consent", "status": "denied"}, {"purposeKey": "ops", "basis": "legitimate_use", "status": "none"}])
    assert asyncio.run(consent.consent_status(_user())) == {"required": False}


def test_purpose_outside_the_point_is_not_asked(monkeypatch):
    # Olai lists every purpose of the organisation; one this point does not ask can never be answered here.
    _configure(monkeypatch, [{"purposeKey": "emails", "basis": "consent", "status": "granted"}, {"purposeKey": "contact-form", "basis": "consent", "status": "none"}])
    assert asyncio.run(consent.consent_status(_user())) == {"required": False}

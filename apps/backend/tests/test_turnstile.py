"""Turnstile guards the public forms once a secret is configured (audit S6)."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from config import turnstile


def _request(token=None):
    headers = {"x-turnstile-token": token} if token else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host="203.0.113.7"))


class _Siteverify:
    def __init__(self, success):
        self.success, self.sent = success, None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, url, data):
        self.sent = (url, data)
        return SimpleNamespace(status_code=200, json=lambda: {"success": self.success})


@pytest.mark.asyncio
async def test_off_without_a_secret(monkeypatch):
    monkeypatch.setattr(turnstile.settings, "turnstile_secret_key", None)
    assert await turnstile.require_turnstile(_request()) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("token, success, status", [(None, True, 400), ("t", False, 400), ("t", True, None)])
async def test_on_with_a_secret(monkeypatch, token, success, status):
    monkeypatch.setattr(turnstile.settings, "turnstile_secret_key", "secret")
    verify = _Siteverify(success)
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", lambda **_: verify)
    if status is None:
        await turnstile.require_turnstile(_request(token))
        assert verify.sent[1] == {"secret": "secret", "response": "t", "remoteip": "203.0.113.7"}
    else:
        with pytest.raises(HTTPException) as refused:
            await turnstile.require_turnstile(_request(token))
        assert refused.value.status_code == status

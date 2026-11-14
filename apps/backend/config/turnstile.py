"""Cloudflare Turnstile on the public forms (audit S6).

Off until TURNSTILE_SECRET_KEY is set (with NEXT_PUBLIC_TURNSTILE_SITE_KEY on
the frontend). When on, the sign-in, signup, access request and password reset
forms must carry a token the browser widget issued, checked server-side.
"""

import httpx
from fastapi import HTTPException, Request

from config.settings import settings

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TOKEN_HEADER = "x-turnstile-token"


async def require_turnstile(request: Request) -> None:
    secret = settings.turnstile_secret_key
    if not secret:
        return
    token = request.headers.get(TOKEN_HEADER)
    if not token:
        raise HTTPException(status_code=400, detail="Complete the human check and try again.")
    from middleware.security import client_ip

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            answer = await client.post(
                VERIFY_URL, data={"secret": secret, "response": token, "remoteip": client_ip(request)}
            )
        passed = answer.status_code == 200 and answer.json().get("success") is True
    except (httpx.HTTPError, ValueError):
        # Fails closed: these forms are what bots target, and the site is behind Cloudflare anyway.
        raise HTTPException(status_code=503, detail="The human check is unavailable. Try again in a moment.")
    if not passed:
        raise HTTPException(status_code=400, detail="The human check did not pass. Try again.")

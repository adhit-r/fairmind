"""Evaluations ask chat models for temperature 0, and fall back to the provider default where it is refused."""

import anyio
import httpx

from api.routes import llm


def _post(handler):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await llm.post_at_zero(client, "https://model.test/v1/chat/completions", 1, {"model": "m", "messages": []})

    return anyio.run(go)


def test_temperature_zero_is_sent_and_dropped_only_when_refused():
    sent = []

    def accepts(request):
        sent.append(request.content)
        return httpx.Response(200, json={})

    assert _post(accepts).status_code == 200 and b'"temperature":0' in sent[0].replace(b" ", b"")

    def refuses(request):
        sent.append(request.content)
        if b"temperature" in request.content:
            return httpx.Response(400, json={"error": {"message": "Unsupported value: 'temperature' does not support 0"}})
        return httpx.Response(200, json={})

    sent.clear()
    assert _post(refuses).status_code == 200 and len(sent) == 2 and b"temperature" not in sent[1]

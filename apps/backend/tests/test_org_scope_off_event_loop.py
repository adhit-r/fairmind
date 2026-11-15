"""The per-request org scope queries never run on the event loop.

On the loop, a wait for a free pooled connection froze every request, including
the ones holding connections, until the 30 s pool timeout: under a page's burst
of parallel requests the backend stopped answering, health checks included.
"""

import asyncio
import threading
from types import SimpleNamespace

from api.routes import ai_governance


def test_org_scope_queries_run_in_the_threadpool(monkeypatch):
    seen = {}

    def check(request, db, body):
        seen["query_thread"] = threading.get_ident()
        seen["body"] = body

    monkeypatch.setattr(ai_governance, "_check_org_scope", check)
    request = SimpleNamespace(method="GET", headers={})

    async def run():
        seen["loop_thread"] = threading.get_ident()
        await ai_governance._enforce_org_scope(request, db=None)

    asyncio.run(run())
    assert seen["query_thread"] != seen["loop_thread"]
    assert seen["body"] is None


def test_json_body_ids_still_reach_the_check(monkeypatch):
    seen = {}
    monkeypatch.setattr(ai_governance, "_check_org_scope", lambda request, db, body: seen.update(body=body))

    async def body():
        return {"system_id": "s-1"}

    request = SimpleNamespace(method="POST", headers={"content-type": "application/json"}, json=body)
    asyncio.run(ai_governance._enforce_org_scope(request, db=None))
    assert seen["body"] == {"system_id": "s-1"}

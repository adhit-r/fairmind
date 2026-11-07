from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient

from core.middleware.audit import route_template


def test_route_template_carries_include_prefixes_and_picks_the_matched_inclusion() -> None:
    router = APIRouter()

    @router.get("/items/{item_id}")
    def item(item_id: str, request: Request) -> dict:
        return {"route": route_template(request)}

    inner = APIRouter()
    inner.include_router(router, prefix="/inner")
    app = FastAPI()
    app.include_router(inner, prefix="/api/v1")
    app.include_router(router, prefix="/legacy")

    client = TestClient(app)
    assert client.get("/api/v1/inner/items/secret").json() == {"route": "/api/v1/inner/items/{item_id}"}
    assert client.get("/legacy/items/secret").json() == {"route": "/legacy/items/{item_id}"}

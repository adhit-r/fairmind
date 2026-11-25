"""An `async def` route that never awaits runs on the event loop and stalls every
other request while it works (sync SQLAlchemy, pandas, file reads). Plain `def`
routes run in FastAPI's threadpool instead, so routes must be one or the other.
"""

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "api_route"}
# Needs the running loop for asyncio.create_task, which a threadpool thread lacks.
LOOP_BOUND = {("src/api/routers/compliance_automation.py", "run_compliance_schedule_now")}


def _is_plain_route(fn: ast.AsyncFunctionDef) -> bool:
    """A route with no other decorator; a wrapper such as isolate_by_org awaits the function itself."""
    targets = [d.func if isinstance(d, ast.Call) else d for d in fn.decorator_list]
    routes = [t for t in targets if isinstance(t, ast.Attribute) and t.attr in ROUTE_METHODS]
    return bool(routes) and len(routes) == len(targets)


def _awaits(fn: ast.AsyncFunctionDef) -> bool:
    return any(isinstance(n, (ast.Await, ast.AsyncFor, ast.AsyncWith)) for n in ast.walk(fn))


def test_async_routes_await_something():
    offenders = []
    for path in sorted((BACKEND / "src" / "api").rglob("*.py")) + sorted((BACKEND / "api").rglob("*.py")):
        rel = path.relative_to(BACKEND).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.AsyncFunctionDef) and _is_plain_route(node) and not _awaits(node):
                if (rel, node.name) not in LOOP_BOUND:
                    offenders.append(f"{rel}:{node.lineno} {node.name}")
    assert not offenders, "async routes that never await; make them plain def:\n" + "\n".join(offenders)

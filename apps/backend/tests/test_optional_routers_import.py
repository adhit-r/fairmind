"""Every router main.py mounts with required=False must import.

main.py skips an optional router with only a warning when its import fails,
so a missing module or dependency silently unmounts its routes. This test
turns that into a failure.
"""

import ast
import importlib
from pathlib import Path

import pytest

MAIN = Path(__file__).resolve().parents[1] / "api" / "main.py"

# Routers whose ML stack is not a declared dependency of the backend. They may
# skip only for these exact missing packages; any other import error fails.
UNDECLARED_ML_EXTRAS = {
    "api.routes.modern_bias_detection": {"torch", "transformers"},
}


def _optional_router_modules() -> list[str]:
    modules = []
    for node in ast.walk(ast.parse(MAIN.read_text())):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_include_router"):
            continue
        if any(kw.arg == "required" and getattr(kw.value, "value", True) is False for kw in node.keywords):
            modules.append(node.args[0].value)
    return sorted(set(modules))


OPTIONAL_ROUTERS = _optional_router_modules()


def test_main_lists_optional_routers():
    assert "api.routes.registration" in OPTIONAL_ROUTERS


@pytest.mark.parametrize("module_path", OPTIONAL_ROUTERS)
def test_optional_router_imports(module_path):
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        if exc.name in UNDECLARED_ML_EXTRAS.get(module_path, set()):
            pytest.skip(f"{module_path} needs undeclared package {exc.name}")
        raise
    assert hasattr(module, "router")

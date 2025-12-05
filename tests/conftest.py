import pytest
import sys
from pathlib import Path

# Add backend directory to python path
backend_path = Path(__file__).parent.parent / "apps" / "backend"
sys.path.append(str(backend_path))

from core.container import ServiceContainer
from api.registry import RouteRegistry

@pytest.fixture
def container():
    return ServiceContainer()

@pytest.fixture
def registry():
    return RouteRegistry()

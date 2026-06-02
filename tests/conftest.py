import pytest
import sys
from pathlib import Path

# Add project and backend directories to python path
project_path = Path(__file__).parent.parent
backend_path = project_path / "apps" / "backend"
sys.path.append(str(project_path))
sys.path.append(str(backend_path))

from core.container import ServiceContainer
from api.registry import RouteRegistry

@pytest.fixture
def container():
    return ServiceContainer()

@pytest.fixture
def registry():
    return RouteRegistry()

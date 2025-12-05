import pytest
from datetime import date, timedelta
from fastapi import FastAPI, Response, Request
from fastapi.testclient import TestClient

from api.versioning import (
    APIVersion,
    VersionStatus,
    VersionRegistry,
    deprecated,
    add_version_headers,
    get_version_registry
)

def test_api_version_model():
    """Test APIVersion dataclass."""
    v1 = APIVersion(
        version="v1",
        status=VersionStatus.STABLE,
        release_date=date(2024, 1, 1)
    )
    assert not v1.is_deprecated()
    assert not v1.is_sunset()
    
    v_dep = APIVersion(
        version="v0",
        status=VersionStatus.DEPRECATED,
        release_date=date(2023, 1, 1),
        sunset_date=date.today() + timedelta(days=30)
    )
    assert v_dep.is_deprecated()
    assert not v_dep.is_sunset()
    assert v_dep.days_until_sunset() == 30

def test_version_registry():
    """Test VersionRegistry."""
    registry = VersionRegistry()
    v1 = APIVersion(
        version="v1",
        status=VersionStatus.STABLE,
        release_date=date(2024, 1, 1)
    )
    registry.register(v1)
    
    assert registry.get("v1") == v1
    assert registry.get_latest_stable() == v1
    assert len(registry.get_all()) == 1

def test_deprecated_decorator():
    """Test deprecated decorator."""
    app = FastAPI()
    client = TestClient(app)
    
    sunset_date = date.today() + timedelta(days=30)
    
    @app.get("/deprecated")
    @deprecated(
        version="v1",
        sunset_date=sunset_date,
        migration_guide="https://example.com"
    )
    async def deprecated_endpoint():
        return {"message": "old"}
        
    response = client.get("/deprecated")
    assert response.status_code == 200
    assert response.headers["X-API-Deprecated"] == "true"
    assert response.headers["X-API-Sunset-Date"] == sunset_date.isoformat()
    assert response.headers["X-API-Migration-Guide"] == "https://example.com"

def test_global_registry():
    """Test global registry singleton."""
    reg1 = get_version_registry()
    reg2 = get_version_registry()
    assert reg1 is reg2
    assert reg1.get("v1") is not None

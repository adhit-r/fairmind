"""
Test configuration and fixtures for FairMind backend tests.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
import uuid

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from config.settings import Settings
from database.connection import Base, get_db
from database.models import Organization, OrganizationMember, User
from middleware.security import RateLimitMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.application.services import environmental_service


class TestSettings(Settings):
    """Test-specific settings."""
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "test-secret-key"
    jwt_secret: str = "test-jwt-secret"
    upload_dir: str = "test_uploads"
    database_dir: str = "test_datasets"
    model_cache_dir: str = "test_models"
    redis_url: str = "redis://localhost:6379/15"
    sentry_dsn: str = ""


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Get test settings."""
    return TestSettings()


def _reset_in_memory_rate_limit() -> None:
    middleware = app.middleware_stack
    while middleware is not None:
        if isinstance(middleware, RateLimitMiddleware):
            middleware.fallback_clients.clear()
            return
        middleware = getattr(middleware, "app", None)


@pytest.fixture(autouse=True)
def reset_in_memory_rate_limit() -> Generator[None, None, None]:
    """Keep request histories isolated between function-scoped API clients."""
    _reset_in_memory_rate_limit()
    yield
    _reset_in_memory_rate_limit()


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def client(test_settings: TestSettings, temp_dir: Path) -> Generator[TestClient, None, None]:
    """Create a test client."""
    # Override settings for tests
    app.dependency_overrides = {}

    # Set up test directories
    test_settings.upload_dir = str(temp_dir / "uploads")
    test_settings.database_dir = str(temp_dir / "datasets")
    test_settings.model_cache_dir = str(temp_dir / "models")

    # Create test directories
    Path(test_settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(test_settings.database_dir).mkdir(parents=True, exist_ok=True)
    Path(test_settings.model_cache_dir).mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides = {}


@pytest.fixture
def environmental_governance_client() -> Generator[tuple[TestClient, str], None, None]:
    """Provide an authenticated, organization-scoped isolated API client."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    org_id = str(uuid.uuid4())
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    active_user = TokenData(
        user_id=str(user_id),
        email="environment-owner@example.test",
        role=UserRole.ADMIN,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )

    session = session_factory()
    session.execute(
        User.__table__.insert().values(
            id=user_id,
            email=active_user.email,
            username="environment-owner",
        )
    )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(org_id),
            name="Environmental Test Organization",
            slug=f"environment-{org_id[:8]}",
            owner_id=user_id,
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=user_id,
            role="owner",
            status="active",
        )
    )
    environmental_service._ensure_environmental_schema(session)
    session.commit()
    session.close()

    def override_db():
        database_session = session_factory()
        try:
            yield database_session
        finally:
            database_session.close()

    async def override_user():
        return active_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        with TestClient(app) as test_client:
            yield test_client, org_id
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_settings: TestSettings, temp_dir: Path) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    # Override settings for tests
    app.dependency_overrides = {}
    
    # Set up test directories
    test_settings.upload_dir = str(temp_dir / "uploads")
    test_settings.database_dir = str(temp_dir / "datasets")
    test_settings.model_cache_dir = str(temp_dir / "models")
    
    # Create test directories
    Path(test_settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(test_settings.database_dir).mkdir(parents=True, exist_ok=True)
    Path(test_settings.model_cache_dir).mkdir(parents=True, exist_ok=True)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def sample_csv_file(temp_dir: Path) -> Path:
    """Create a sample CSV file for testing."""
    csv_content = """name,age,gender,salary
John,25,M,50000
Jane,30,F,60000
Bob,35,M,70000
Alice,28,F,55000
"""
    csv_file = temp_dir / "sample.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture(scope="function")
def sample_json_file(temp_dir: Path) -> Path:
    """Create a sample JSON file for testing."""
    json_content = """[
    {"name": "John", "age": 25, "gender": "M", "salary": 50000},
    {"name": "Jane", "age": 30, "gender": "F", "salary": 60000},
    {"name": "Bob", "age": 35, "gender": "M", "salary": 70000},
    {"name": "Alice", "age": 28, "gender": "F", "salary": 55000}
]"""
    json_file = temp_dir / "sample.json"
    json_file.write_text(json_content)
    return json_file


@pytest.fixture(scope="function")
def mock_model_data():
    """Mock model data for testing."""
    return {
        "model_id": "test-model-123",
        "model_name": "Test Model",
        "model_type": "classification",
        "version": "1.0.0",
        "features": ["feature1", "feature2", "feature3"],
        "target": "target_column",
        "metrics": {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85
        }
    }


@pytest.fixture(scope="function")
def mock_bias_detection_data():
    """Mock bias detection data for testing."""
    return {
        "dataset_id": "test-dataset-123",
        "protected_attributes": ["gender", "age_group"],
        "target_column": "approved",
        "bias_metrics": {
            "demographic_parity": 0.15,
            "equalized_odds": 0.12,
            "calibration": 0.08
        },
        "fairness_threshold": 0.1
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    
    # Clean up any test files
    test_files = [
        "test.db",
        "test.db-journal",
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )

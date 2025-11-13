"""
Test configuration and fixtures for FairMind backend tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os
from pathlib import Path

from api.main import app
from config.settings import Settings


class TestSettings(Settings):
    """Test-specific settings."""
    environment: str = "testing"
    debug: bool = True
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "test-secret-key"
    jwt_secret: str = "test-jwt-secret"
    upload_dir: str = "test_uploads"
    database_dir: str = "test_datasets"
    model_cache_dir: str = "test_models"
    redis_url: str = None  # Disable Redis for tests
    sentry_dsn: str = None  # Disable Sentry for tests


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Get test settings."""
    return TestSettings()


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


@pytest.fixture(scope="function")
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
    
    async with AsyncClient(app=app, base_url="http://test") as client:
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
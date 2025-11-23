"""
Pytest configuration and fixtures for E2E tests.
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext, Playwright
from typing import Generator
import os
from pathlib import Path


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get the base URL for the application."""
    return os.getenv("E2E_BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def api_url() -> str:
    """Get the API base URL."""
    return os.getenv("E2E_API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """Create a Playwright instance."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser_type_launch_args(playwright: Playwright) -> dict:
    """Browser launch arguments."""
    return {
        "headless": os.getenv("E2E_HEADLESS", "true").lower() == "true",
        "slow_mo": int(os.getenv("E2E_SLOW_MO", "0")),
    }


@pytest.fixture(scope="session")
def browser(
    playwright: Playwright, browser_type_launch_args: dict
) -> Generator[Browser, None, None]:
    """Create a browser instance."""
    browser = playwright.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Create a browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=Path("tests/e2e/videos") if os.getenv("E2E_RECORD_VIDEO") else None,
        record_video_size={"width": 1920, "height": 1080},
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Create a page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page, base_url: str) -> Generator[Page, None, None]:
    """Create an authenticated page for tests that require login."""
    # Navigate to login page
    page.goto(f"{base_url}/login")
    
    # TODO: Implement authentication flow
    # This should be customized based on your authentication mechanism
    # For now, this is a placeholder
    
    yield page


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Setup code here
    yield
    # Teardown code here


# Pytest markers for E2E tests
def pytest_configure(config):
    """Configure pytest markers for E2E tests."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "smoke: marks tests as smoke tests")
    config.addinivalue_line("markers", "critical: marks tests as critical path tests")




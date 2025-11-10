"""
E2E tests for dashboard interactions.
"""

import pytest
from playwright.sync_api import Page
from tests.e2e.pages.dashboard_page import DashboardPage


@pytest.mark.e2e
@pytest.mark.smoke
def test_dashboard_loads(page: Page, base_url: str):
    """Test that dashboard loads correctly.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    dashboard_page = DashboardPage(page, base_url)
    
    # Navigate to dashboard
    dashboard_page.navigate_to_dashboard()
    
    # Wait for page to load
    page.wait_for_load_state("networkidle")
    
    # Verify dashboard is loaded
    assert dashboard_page.is_dashboard_loaded(), "Dashboard should be loaded"


@pytest.mark.e2e
def test_navigate_to_bias_detection(page: Page, base_url: str):
    """Test navigation to bias detection page.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    dashboard_page = DashboardPage(page, base_url)
    
    # Navigate to dashboard first
    dashboard_page.navigate_to_dashboard()
    page.wait_for_load_state("networkidle")
    
    # Navigate to bias detection
    dashboard_page.navigate_to_bias_detection()
    page.wait_for_load_state("networkidle")
    
    # Verify we're on bias detection page
    assert "/bias" in page.url, "Should be on bias detection page"


@pytest.mark.e2e
def test_navigate_to_monitoring(page: Page, base_url: str):
    """Test navigation to monitoring page.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    dashboard_page = DashboardPage(page, base_url)
    
    # Navigate to dashboard first
    dashboard_page.navigate_to_dashboard()
    page.wait_for_load_state("networkidle")
    
    # Navigate to monitoring
    dashboard_page.navigate_to_monitoring()
    page.wait_for_load_state("networkidle")
    
    # Verify we're on monitoring page
    assert "/monitoring" in page.url, "Should be on monitoring page"


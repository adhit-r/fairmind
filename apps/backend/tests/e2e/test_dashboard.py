"""
E2E tests for dashboard interactions.
"""

import pytest
from playwright.sync_api import Page
from tests.e2e.pages.dashboard_page import DashboardPage


@pytest.mark.e2e
@pytest.mark.smoke
def test_dashboard_loads(page: Page, base_url: str, login_as_admin):
    """Test that dashboard loads correctly.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    login_as_admin()
    dashboard_page = DashboardPage(page, base_url)
    
    # Verify dashboard is loaded
    assert dashboard_page.is_dashboard_loaded(), "Dashboard should be loaded"
    assert not dashboard_page.is_dashboard_error(), "Dashboard should not show error"


@pytest.mark.e2e
def test_navigate_to_bias_detection(page: Page, base_url: str, login_as_admin):
    """Test navigation to bias detection page.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    login_as_admin()
    dashboard_page = DashboardPage(page, base_url)
    
    # Navigate to bias detection
    dashboard_page.navigate_to_bias_detection()
    page.wait_for_url("**/bias", timeout=10000)
    
    # Verify we're on bias detection page
    assert "/bias" in page.url, "Should be on bias detection page"


@pytest.mark.e2e
def test_navigate_to_monitoring(page: Page, base_url: str, login_as_admin):
    """Test navigation to monitoring page.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    login_as_admin()
    dashboard_page = DashboardPage(page, base_url)
    
    # Navigate to monitoring
    dashboard_page.navigate_to_monitoring()
    page.wait_for_url("**/monitoring", timeout=10000)
    
    # Verify we're on monitoring page
    assert "/monitoring" in page.url, "Should be on monitoring page"

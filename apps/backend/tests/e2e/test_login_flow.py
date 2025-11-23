"""
E2E tests for login flow.
"""

import pytest
from playwright.sync_api import Page
from tests.e2e.pages.login_page import LoginPage


@pytest.mark.e2e
@pytest.mark.smoke
def test_login_successful(page: Page, base_url: str):
    """Test successful login flow.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    login_page = LoginPage(page, base_url)
    
    # Navigate to login page
    login_page.navigate_to_login()
    
    # Verify we're on the login page
    assert login_page.is_login_page(), "Should be on login page"
    
    # TODO: Replace with actual test credentials
    # This is a placeholder - actual credentials should come from environment or test fixtures
    test_email = "test@example.com"
    test_password = "testpassword"
    
    # Perform login
    login_page.login(test_email, test_password)
    
    # Wait for navigation after login
    page.wait_for_load_state("networkidle")
    
    # Verify redirect after successful login (adjust based on your app's behavior)
    # This should redirect to dashboard or home page
    assert "/login" not in page.url, "Should be redirected away from login page"


@pytest.mark.e2e
def test_login_invalid_credentials(page: Page, base_url: str):
    """Test login with invalid credentials.

    Args:
        page: Playwright page instance
        base_url: Base URL of the application
    """
    login_page = LoginPage(page, base_url)
    
    # Navigate to login page
    login_page.navigate_to_login()
    
    # Attempt login with invalid credentials
    login_page.login("invalid@example.com", "wrongpassword")
    
    # Wait for error message
    page.wait_for_timeout(1000)  # Wait for error to appear
    
    # Verify error message is displayed
    error_message = login_page.get_error_message()
    assert error_message != "", "Error message should be displayed for invalid credentials"




"""
Dashboard page object.
"""

import time
from playwright.sync_api import Page
from tests.e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object for the dashboard page."""

    def __init__(self, page: Page, base_url: str = "http://localhost:1111"):
        """Initialize the dashboard page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
        self.dashboard_container = 'text="Release Readiness"'
        self.dashboard_empty_state = 'text="Register your first AI system"'
        self.dashboard_shell = 'text="DASHBOARD"'
        self.dashboard_loading = '[data-testid="dashboard-loading"]'
        self.dashboard_error = '[data-testid="dashboard-error"]'
        self.monitoring_card = '[data-testid="monitoring"], .monitoring-card'
        self.navigation_menu = 'nav, [role="navigation"], .navigation'

    def navigate_to_dashboard(self) -> None:
        """Navigate to the dashboard page."""
        self.navigate("/dashboard")

    def is_dashboard_loaded(self) -> bool:
        """Check if dashboard is loaded.

        Returns:
            True if dashboard is loaded, False otherwise
        """
        markers = [
            "ai estate",
            "under governance",
            "release readiness",
            "register your first ai system",
            "dashboard",
            # The E2E admin is never stored, so it belongs to no organisation; the shell then shows this one page.
            "you are not in an organisation yet",
        ]

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                body_text = self.page.locator("body").inner_text(timeout=1000).lower()
                if any(marker in body_text for marker in markers):
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(500)

        return False
    
    def is_dashboard_loading(self) -> bool:
            """Dashboard is in loading (skeleton) state."""
            return self.is_visible(self.dashboard_loading)
    
    def is_dashboard_error(self) -> bool:
            """Dashboard is in error state."""
            return self.is_visible(self.dashboard_error)        

    def click_monitoring(self) -> None:
        """Click on monitoring card or link."""
        if self.is_visible(self.monitoring_card):
            self.click(self.monitoring_card)

    def navigate_to_monitoring(self) -> None:
        """Navigate to monitoring page."""
        link = self.page.locator('a[href="/monitoring"]').first
        if self.page.locator('a[href="/monitoring"]').count() > 0:
            link.click()
        else:
            self.navigate("/monitoring")

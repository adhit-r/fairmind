"""
Dashboard page object.
"""

from playwright.sync_api import Page
from tests.e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object for the dashboard page."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """Initialize the dashboard page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
        self.dashboard_container = '[data-testid="dashboard"]'
        self.dashboard_loading = '[data-testid="dashboard-loading"]'
        self.dashboard_error = '[data-testid="dashboard-error"]'
        self.bias_detection_card = '[data-testid="bias-detection"], .bias-detection-card'
        self.monitoring_card = '[data-testid="monitoring"], .monitoring-card'
        self.navigation_menu = 'nav, [role="navigation"], .navigation'

    def navigate_to_dashboard(self) -> None:
        """Navigate to the dashboard page."""
        self.navigate("/")

    def is_dashboard_loaded(self) -> bool:
        """Check if dashboard is loaded.

        Returns:
            True if dashboard is loaded, False otherwise
        """
        return self.is_visible(self.dashboard_container)
    
    def is_dashboard_loading(self) -> bool:
            """Dashboard is in loading (skeleton) state."""
            return self.is_visible(self.dashboard_loading)
    
    def is_dashboard_error(self) -> bool:
            """Dashboard is in error state."""
            return self.is_visible(self.dashboard_error)        

    def click_bias_detection(self) -> None:
        """Click on bias detection card or link."""
        if self.is_visible(self.bias_detection_card):
            self.click(self.bias_detection_card)

    def click_monitoring(self) -> None:
        """Click on monitoring card or link."""
        if self.is_visible(self.monitoring_card):
            self.click(self.monitoring_card)

    def navigate_to_bias_detection(self) -> None:
        """Navigate to bias detection page."""
        self.navigate("/bias")

    def navigate_to_monitoring(self) -> None:
        """Navigate to monitoring page."""
        self.navigate("/monitoring")



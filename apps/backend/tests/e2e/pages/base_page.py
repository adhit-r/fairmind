"""
Base Page Object class for all page objects.
"""

from playwright.sync_api import Page
from typing import Optional


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """Initialize the base page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url

    def navigate(self, path: str = "") -> None:
        """Navigate to a specific path.

        Args:
            path: Path to navigate to (relative to base_url)
        """
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        self.page.goto(url)

    def wait_for_load_state(self, state: str = "networkidle") -> None:
        """Wait for the page to reach a specific load state.

        Args:
            state: Load state to wait for (load, domcontentloaded, networkidle)
        """
        self.page.wait_for_load_state(state)

    def get_title(self) -> str:
        """Get the page title.

        Returns:
            Page title
        """
        return self.page.title()

    def get_url(self) -> str:
        """Get the current page URL.

        Returns:
            Current page URL
        """
        return self.page.url

    def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot of the page.

        Args:
            path: Optional path to save the screenshot

        Returns:
            Screenshot bytes
        """
        return self.page.screenshot(path=path, full_page=True)

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to appear.

        Args:
            selector: CSS selector or XPath
            timeout: Maximum time to wait in milliseconds
        """
        self.page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str) -> None:
        """Click an element.

        Args:
            selector: CSS selector or XPath
        """
        self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        """Fill an input field.

        Args:
            selector: CSS selector or XPath
            value: Value to fill
        """
        self.page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """Get text content of an element.

        Args:
            selector: CSS selector or XPath

        Returns:
            Text content
        """
        return self.page.locator(selector).text_content() or ""

    def is_visible(self, selector: str) -> bool:
        """Check if an element is visible.

        Args:
            selector: CSS selector or XPath

        Returns:
            True if element is visible, False otherwise
        """
        return self.page.locator(selector).is_visible()



"""
Login page object.
"""

from playwright.sync_api import Page
from tests.e2e.pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """Initialize the login page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
        self.email_input = 'input[type="email"], input[name="email"], input[id="email"]'
        self.password_input = 'input[type="password"], input[name="password"], input[id="password"]'
        self.submit_button = 'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
        self.error_message = '.error, .alert-error, [role="alert"]'

    def navigate_to_login(self) -> None:
        """Navigate to the login page."""
        self.navigate("/login")

    def enter_email(self, email: str) -> None:
        """Enter email in the email field.

        Args:
            email: Email address to enter
        """
        self.fill(self.email_input, email)

    def enter_password(self, password: str) -> None:
        """Enter password in the password field.

        Args:
            password: Password to enter
        """
        self.fill(self.password_input, password)

    def click_login(self) -> None:
        """Click the login button."""
        self.click(self.submit_button)

    def login(self, email: str, password: str) -> None:
        """Perform complete login flow.

        Args:
            email: Email address
            password: Password
        """
        self.navigate_to_login()
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        """Get error message if login fails.

        Returns:
            Error message text
        """
        if self.is_visible(self.error_message):
            return self.get_text(self.error_message)
        return ""

    def is_login_page(self) -> bool:
        """Check if currently on login page.

        Returns:
            True if on login page, False otherwise
        """
        return "/login" in self.get_url() or self.is_visible(self.email_input)




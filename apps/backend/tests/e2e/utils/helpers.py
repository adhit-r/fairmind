"""
Helper functions for E2E tests.
"""

import time
from typing import Callable, Optional
from playwright.sync_api import Page


def wait_for_api_response(
    page: Page,
    url_pattern: str,
    timeout: int = 30000,
    method: str = "GET",
) -> Optional[dict]:
    """Wait for an API response and return the response data.

    Args:
        page: Playwright page instance
        url_pattern: URL pattern to wait for
        timeout: Maximum time to wait in milliseconds
        method: HTTP method to wait for

    Returns:
        Response data as dictionary, or None if timeout
    """
    try:
        with page.expect_response(
            lambda response: url_pattern in response.url and response.request.method == method,
            timeout=timeout,
        ) as response_info:
            response = response_info.value
            return response.json()
    except Exception:
        return None


def retry_action(
    action: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    *args,
    **kwargs,
) -> any:
    """Retry an action with exponential backoff.

    Args:
        action: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        *args: Positional arguments for the action
        **kwargs: Keyword arguments for the action

    Returns:
        Result of the action

    Raises:
        Exception: If all retries fail
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                raise last_exception
    raise last_exception


def take_screenshot_on_failure(page: Page, test_name: str) -> None:
    """Take a screenshot when a test fails.

    Args:
        page: Playwright page instance
        test_name: Name of the test
    """
    screenshot_path = f"tests/e2e/screenshots/failure_{test_name}_{int(time.time())}.png"
    page.screenshot(path=screenshot_path, full_page=True)




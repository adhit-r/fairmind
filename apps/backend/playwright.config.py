"""
Playwright configuration for E2E tests.
"""

from pathlib import Path
import os


# Base URL for the application
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")
API_URL = os.getenv("E2E_API_URL", "http://localhost:8000")

# Test directories
TEST_DIR = Path(__file__).parent / "tests" / "e2e"
SCREENSHOTS_DIR = TEST_DIR / "screenshots"
VIDEOS_DIR = TEST_DIR / "videos"

# Create directories if they don't exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Playwright settings
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "30000"))
RECORD_VIDEO = os.getenv("E2E_RECORD_VIDEO", "false").lower() == "true"

# Browser settings
BROWSER = os.getenv("E2E_BROWSER", "chromium")  # chromium, firefox, webkit
VIEWPORT_WIDTH = int(os.getenv("E2E_VIEWPORT_WIDTH", "1920"))
VIEWPORT_HEIGHT = int(os.getenv("E2E_VIEWPORT_HEIGHT", "1080"))




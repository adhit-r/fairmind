# E2E Tests with Playwright

This directory contains end-to-end tests for the Fairmind AI Governance Platform using Playwright and pytest.

## Structure

```
tests/e2e/
├── __init__.py
├── conftest.py          # Pytest fixtures and configuration
├── pages/               # Page Object Model (POM) classes
│   ├── __init__.py
│   ├── base_page.py     # Base page object class
│   ├── login_page.py    # Login page object
│   └── dashboard_page.py # Dashboard page object
├── fixtures/            # Test fixtures
│   └── __init__.py
├── utils/               # Utility functions
│   ├── __init__.py
│   └── helpers.py       # Helper functions
├── test_login_flow.py   # Login flow tests
├── test_dashboard.py    # Dashboard tests
├── test_bias_detection_workflow.py # Bias detection workflow tests
├── screenshots/         # Screenshots on test failures
└── videos/              # Test execution videos
```

## Setup

1. Install dependencies:
```bash
cd apps/backend
uv sync --extra test
```

2. Install Playwright browsers:
```bash
uv run playwright install chromium
```

## Running Tests

### Run all E2E tests:
```bash
uv run pytest tests/e2e/ -m e2e
```

### Run smoke tests only:
```bash
uv run pytest tests/e2e/ -m "e2e and smoke"
```

### Run specific test file:
```bash
uv run pytest tests/e2e/test_login_flow.py
```

### Run with verbose output:
```bash
uv run pytest tests/e2e/ -m e2e -v
```

### Run in headed mode (see browser):
```bash
E2E_HEADLESS=false uv run pytest tests/e2e/ -m e2e
```

## Environment Variables

- `E2E_BASE_URL`: Base URL of the frontend application (default: `http://localhost:3000`)
- `E2E_API_URL`: Base URL of the backend API (default: `http://localhost:8000`)
- `E2E_HEADLESS`: Run browser in headless mode (default: `true`)
- `E2E_SLOW_MO`: Slow down operations by specified milliseconds (default: `0`)
- `E2E_RECORD_VIDEO`: Record test execution videos (default: `false`)

## Page Object Model (POM)

Tests use the Page Object Model pattern to encapsulate page interactions:

- Each page has a corresponding Page Object class
- Page Objects inherit from `BasePage`
- Page Objects contain selectors and methods for page interactions
- This keeps tests maintainable and reusable

## Writing Tests

1. Create a Page Object class in `pages/` if needed
2. Write test functions in test files
3. Use `@pytest.mark.e2e` to mark tests as E2E tests
4. Use `@pytest.mark.smoke` for smoke tests
5. Use `@pytest.mark.critical` for critical path tests

Example:
```python
@pytest.mark.e2e
@pytest.mark.smoke
def test_login_successful(page: Page, base_url: str):
    login_page = LoginPage(page, base_url)
    login_page.navigate_to_login()
    login_page.login("test@example.com", "password")
    assert "/login" not in page.url
```

## CI/CD Integration

E2E tests run automatically in GitHub Actions on:
- Push to main/dev branches
- Pull requests to main/dev branches
- Manual workflow dispatch

The workflow:
1. Sets up Python and installs dependencies
2. Installs Playwright browsers
3. Starts backend and frontend servers
4. Runs E2E tests
5. Uploads screenshots and videos on failure

## Best Practices

1. Use Page Object Model for all page interactions
2. Keep tests independent and isolated
3. Use descriptive test names
4. Add appropriate markers (e2e, smoke, critical)
5. Clean up test data after tests
6. Take screenshots on failures
7. Use wait strategies instead of hard-coded sleeps
8. Test critical user flows first

## Troubleshooting

### Tests fail with browser not found:
```bash
uv run playwright install chromium
```

### Tests timeout:
- Increase timeout in `conftest.py`
- Check if servers are running
- Verify network connectivity

### Screenshots not saved:
- Ensure `screenshots/` directory exists
- Check file permissions

## Next Steps

- Add more page objects for all pages
- Implement visual regression testing
- Add tests for all critical user flows
- Set up test data fixtures
- Add performance testing




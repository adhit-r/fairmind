# E2E Testing Guide

## Overview

Comprehensive E2E tests for FairMind UI using Playwright. Tests cover:
- Dashboard with real data
- Models page with seeded models
- Bias detection forms
- Navigation between pages
- API integration
- Form validation
- Error handling

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
   ```bash
   cd apps/backend
   uv run uvicorn api.main:app --reload --port 8000
   ```

2. **Database seeded** with realistic models
   ```bash
   cd apps/backend
   python3 scripts/seed_models_realistic.py
   ```

3. **Frontend dependencies installed**
   ```bash
   cd apps/frontend-new
   bun install
   ```

## Running Tests

### Run all tests
```bash
bun test
```

### Run with UI (recommended for debugging)
```bash
bun test:ui
```

### Run in headed mode (see browser)
```bash
bun test:headed
```

### Run in debug mode
```bash
bun test:debug
```

### Run specific test file
```bash
bun test tests/e2e.spec.ts
```

## Test Files

- `e2e.spec.ts` - Comprehensive E2E tests (main test suite)
- `dashboard.spec.ts` - Dashboard-specific tests
- `models.spec.ts` - Models page tests
- `bias-detection.spec.ts` - Bias detection tests
- `navigation.spec.ts` - Navigation tests
- `api-integration.spec.ts` - API integration tests
- `forms.spec.ts` - Form validation tests
- `homepage.spec.ts` - Homepage and routing tests

## What's Tested

### ✅ Dashboard
- Loads with real data
- Displays stats cards
- Shows loading states
- Handles API errors
- Refresh functionality

### ✅ Models Page
- Displays real models from database
- Shows model registration dialog
- Handles empty state
- Displays model details

### ✅ Bias Detection
- Loads bias detection page
- Navigates to modern bias page
- Navigates to multimodal bias page
- Form submission

### ✅ Navigation
- All main pages load
- Sidebar navigation works
- Page routing functions

### ✅ API Integration
- Fetches data from backend
- Handles API errors gracefully
- Retries on failure
- Displays real model data

### ✅ Forms
- Form validation
- Error handling
- Toast notifications
- Submission flow

## Configuration

Tests are configured in `playwright.config.ts`:
- Base URL: `http://localhost:1111`
- Frontend server starts automatically
- Backend should be running separately

## Troubleshooting

### Tests fail with "Connection refused"
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

### Tests fail with "No models found"
- Run seed script: `python3 apps/backend/scripts/seed_models_realistic.py`

### Tests timeout
- Increase timeout in test file
- Check if backend is responding: `curl http://localhost:8000/health`

### Frontend doesn't start
- Check port 1111 is available
- Try: `bun run dev` manually

## CI/CD

For CI environments:
```bash
# Set CI environment variable
CI=true bun test
```

This will:
- Not reuse existing servers
- Retry failed tests
- Generate HTML report


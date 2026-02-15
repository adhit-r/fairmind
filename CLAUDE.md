# Claude Code Configuration

This file documents the project setup and conventions for Claude Code.

## Project Overview

FairMind is a comprehensive AI bias detection and compliance platform for India-specific regulatory requirements (NITI Aayog guidelines, RBI regulations, and other frameworks).

## Repository Structure

- **apps/backend/** - FastAPI backend for bias detection, compliance, and analytics
- **apps/frontend/** - Next.js frontend dashboard
- **apps/website/** - Marketing website (Astro)
- **apps/ml/** - ML models and visualization utilities
- **docs/** - Project documentation

## Development Guidelines

### Backend (Python/FastAPI)
- Location: `apps/backend/`
- Package manager: `uv`
- Main entry: `api/main.py`
- Structure: Domain-driven design with routes, services, and domain models

### Frontend (TypeScript/React)
- Location: `apps/frontend/`
- Framework: Next.js with App Router
- Package manager: `npm`
- Styling: Tailwind CSS
- Testing: Playwright

### Key Features
- Bias detection and remediation
- India compliance automation (NITI Aayog, RBI, UIDAI)
- Model monitoring and analytics
- Dataset management and marketplace
- Real-time compliance dashboard
- Audit report generation

## Common Tasks

### Run Backend
```bash
cd apps/backend
uv run fastapi dev api/main.py
```

### Run Frontend
```bash
cd apps/frontend
npm run dev
```

### Run Tests
```bash
# Backend tests
cd apps/backend
uv run pytest

# Frontend tests
cd apps/frontend
npm run test
```

## Git Workflow

- Main branch: `main`
- Feature branches: Follow naming convention `feature/description` or `task/description`
- Always create PRs for code review before merging to main
- Commit messages should be descriptive and reference issues when applicable

## Environment Setup

See `CONTRIBUTING.md` for detailed contribution guidelines.

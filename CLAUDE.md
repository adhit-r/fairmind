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

---

## Design Context

### Users
**Primary**: Organizations managing AI systems, compliance teams, data scientists, and ML engineers in India and global markets.
**Context**: Users are evaluating bias in production models, preparing regulatory audits, and documenting compliance evidence under frameworks like DPDP Act, EU AI Act, and GDPR.
**Job to do**: Detect bias quickly, generate remediation code, and produce audit-ready compliance documentation with minimal friction.

### Brand Personality
**Neobrutalist + Professional**
FairMind should feel bold, confident, and trustworthy—not corporate-sterile or playful. The interface communicates competence and seriousness about AI ethics without being cold or inaccessible. It's for engineers and compliance officers who value clarity and efficiency over visual decoration.

### Aesthetic Direction
**Neobrut Design System** (maintain current direction):
- **Bold geometric shadows**: 6px/8px hard-drop shadows communicate confidence and solidity
- **Strong borders**: Thick outlines (4px) create visual clarity and hierarchy
- **High contrast**: Teal primary (#FF6B35 orange accent), clean whites, deep blacks
- **Geometric confidence**: Square corners, deliberate spacing, no softness
- **No gradients or gloss**: Direct, no-nonsense visual communication
- **Light + Dark modes**: Professional in both contexts

**Design tokens already in place**:
- Primary: oklch(0.60 0.13 163) — confident teal
- Accent: #FF6B35 — bold orange
- Shadows: `brutal-shadow`, `brutal-shadow-lg`, `brutal-shadow-xl`
- Radius: 0 (sharp corners for authority)

### Design Principles
1. **Authority through clarity** — Bold typography, strong visual hierarchy, unambiguous interactive states. Users must never wonder what to do.
2. **Data over decoration** — Visualizations and metrics are the focus. Remove anything ornamental that doesn't serve the user's task.
3. **Compliance-first mindset** — Every page should support the user's regulatory documentation goal. Design for audit-readiness: screenshots, exports, and reports must be professional and exportable.
4. **Neobrutalism for confidence** — Thick shadows, sharp edges, and geometric strength signal "this handles serious work." No soft-edged, glassy, corporate look.
5. **Accessibility by default** — High contrast, clear hierarchy, predictable patterns. Works for compliance teams and engineers alike, with or without assistive tech.

### What to Avoid
- Generic SaaS aesthetic (bland blue, generic cards, indistinct hierarchy)
- Dark + moody (glassmorphism, neon glows, crypto/gaming vibes that undermine trustworthiness)
- Overly decorative elements (gradients, animations that don't reduce cognitive load, superfluous icons)
- Inconsistent neobrutalism (mix of soft and harsh aesthetics — commit to the bold approach or drop it entirely)

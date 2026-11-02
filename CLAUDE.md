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
**Calm, precise, trustworthy.**
FairMind should feel like a well-made instrument: quiet surfaces, clear hierarchy, and data that reads at a glance. It is for engineers and compliance officers who value clarity and efficiency over visual decoration.

### Aesthetic Direction
**Lifecycle-shell design** (the reference pages are `/dashboard`, `/integrations`, `/onboard`, `/systems/[id]`):
- **Soft surfaces**: white cards with 14px corners and a soft layered shadow, on a warm grey page background
- **Hairlines, not heavy borders**: 1px borders in `--fm-line`; no thick black outlines
- **Ink, not black**: text and primary fills use `--fm-ink`, secondary text `--fm-ink2`, labels `--fm-ink3`
- **Semibold type**: headings `font-semibold` with tight tracking; uppercase only on small (10-11px) section labels
- **Pill controls**: buttons are `rounded-full`, primary is a dark ink pill, secondary is white with a hairline border
- **Orange is a brand accent, not a button color**: `--fm-brand` (#FF6B35) for marks and highlights only
- **No gradients, gloss, hard offset shadows or press-down transforms**

**Design tokens** (`apps/frontend/src/app/globals.css`):
- `--fm-bg` #f4f4f2, `--fm-ink` #15171a, `--fm-ink2` #5a5f68, `--fm-ink3` #9096a0
- `--fm-line` rgba(21,23,26,.08), `--fm-brand` #ff6b35, `--fm-shadow` (soft card shadow)
- `--radius` 10px for shadcn primitives; cards 14px; inputs `rounded-[10px]`
- Use the shared primitives in `components/ui/` (Card, Button, dropdown) rather than restyling per page
- Use the tokens via `var(--fm-*)`, never hardcoded hex for ink, lines or backgrounds; status colors (red, amber, green) are fine as literals

### Design Principles
1. **Authority through clarity** — Strong hierarchy from size and weight, not from borders and shadows. Users must never wonder what to do.
2. **Data over decoration** — Visualizations and metrics are the focus. Remove anything ornamental that doesn't serve the user's task.
3. **Compliance-first mindset** — Every page should support the user's regulatory documentation goal. Design for audit-readiness: screenshots, exports, and reports must be professional and exportable.
4. **One system** — Every page uses the same tokens and primitives, so the product reads as one tool.
5. **Accessibility by default** — High contrast, clear hierarchy, predictable patterns. Works for compliance teams and engineers alike, with or without assistive tech.

### What to Avoid
- The retired neobrutalist style: `border-2`/`border-4 border-black`, `shadow-brutal*`, `shadow-[4px_4px_0_0_...]`, `font-black uppercase`, `rounded-none`, the `#0F1412`/`#FCFDF8` palette, orange fill buttons
- Generic SaaS aesthetic (bland blue, indistinct hierarchy)
- Dark + moody (glassmorphism, neon glows, crypto/gaming vibes that undermine trustworthiness)
- Overly decorative elements (gradients, animations that don't reduce cognitive load, superfluous icons)

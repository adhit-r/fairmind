# Claude Code Configuration

This file documents the project setup and conventions for Claude Code.

## Project Overview

FairMind is an open-source agentic AI governance platform. Agents do the governance work; a person decides at every gate. Governance runs as workflows (collect, check, suggest, ask a person, act, verify, file evidence), FairMind runs the evaluations, and every step lands on a hash-chained ledger. It covers AI systems including LLM applications and AI agents.

It helps a team prepare for review and shows an auditor the evidence. It does not certify compliance and never approves a release on its own. The framework catalogue holds 51 frameworks (38 with decomposed requirements). India frameworks (for example NITI Aayog, RBI, DPDP) are among them, not the product's whole scope. See `README.md` for current numbers and status.

## Repository Structure

- **apps/backend/** - FastAPI backend: governance, evaluations, release gate, evidence packs, catalogue
- **apps/frontend/** - Next.js frontend dashboard
- **apps/website/** - Marketing website (Astro)
- **apps/docs/** - Documentation site (Fumadocs)
- **apps/cli/** - `fairmind` CLI: release gate, fairness tests, monitoring, offline pack verification
- **apps/sdk/** - Python SDK (`fairmind`)
- **apps/mcp/** - MCP server (`fairmind-mcp`) for coding agents
- **apps/eval-runner/** - Container image that runs one evaluation inside the sandbox
- **apps/notifier/** - Small desktop app that shows the FairMind agent's messages (Rust)
- **apps/blog-theme/** - Ghost theme for the blog
- **apps/ml/** - MLflow config, pipelines and visualization utilities
- **docs/** - Project documentation (see `docs/STATUS.md` for claim boundaries)

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
- AI system registry and discovery (MLflow, GitHub, Hugging Face Hub)
- Agentic governance workflows in packs, with human approval at each gate
- Evaluations: 109 in the catalogue (fairness, security, data, agents, behaviour tests against live systems)
- Release gate (five checks) in CI, SDK and MCP
- Framework clause mapping across 51 frameworks (EU AI Act, ISO/IEC 42001, NIST AI RMF, India frameworks and more)
- Hash-chained evidence ledger, inspection packs and offline verification
- Monitoring snapshots and audit reports

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

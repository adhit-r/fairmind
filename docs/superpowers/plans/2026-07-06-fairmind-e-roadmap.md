# FairMind-E Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make FairMind-E environmental evidence a working governance control across backend, evidence storage, release gating, dashboard UI, docs, and deterministic research harnesses.

**Architecture:** Keep environmental decision logic in `src.domain.environmental`; expose it through a thin application service and AI Governance routes. Reuse `governance_evidence` for MVP proof packets while adding an append-only assessment table for versioned environmental decisions.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, Next.js App Router, Tailwind, existing FairMind neobrutalist UI components, Python stdlib research harness.

---

## Implementation Order

- [ ] Complete the environmental domain package and invariants.
- [ ] Add append-only persistence and runtime migration support.
- [ ] Add assessment, history, evidence-ingest, and approval-gate endpoints.
- [ ] Add focused backend tests for import, invariants, persistence, evidence mirroring, and approval blocking.
- [ ] Add Environmental Impact UI inside AI Governance using existing components and API hooks.
- [ ] Add FairMind-E docs and deterministic research harness artifacts.
- [ ] Run narrow backend, boundary, frontend, and harness validation.

## Constraints

- No emoji.
- No purple gradients or generic AI-looking UI.
- No external posting, publishing, credential creation, credential rotation, or secret handling.
- Offsets and RECs never improve provenance, uncertainty, confidence, risk tier, or recommendation.
- Provenance is categorical and remains separate from uncertainty.
- Vendor-reported figures cap confidence at `0.60`.
- Weak or missing environmental evidence is itself a release finding.

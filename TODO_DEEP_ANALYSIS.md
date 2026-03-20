# FairMind Deep Audit TODO

## Executive Focus

- Product problem: FairMind has many pages and capabilities, but the primary user journey is still unclear.
- Current state: backend/pilot stabilization is materially ahead of UX and workflow integration.
- Immediate objective: make the product feel like one governed AI-system workflow instead of a toolbox.
- Working principle: optimize for one successful enterprise path before expanding feature surface.

## Swimlane Execution Plan

### Current Read

- Frontend: partial workflow-first state; `Dashboard`, `Risks`, and `AI Governance` now share selected AI-system context.
- Backend: usable and stable enough to build on, but canonical `workspace` / `ai_system` modeling and auth/session hardening are still incomplete.
- Governance: partially real, but not yet decision-grade because evidence, release-gate rules, and remediation closure are not fully enforced.

### Critical Path

- [ ] Make `Evidence` the bridge between assessment, risk, governance, and approval.
- [ ] Connect remediation directly to governance blockers.
- [ ] Build a real `Onboard` entry flow.
- [ ] Add explicit release-gate and approval states.

### Evidence Execution

- [ ] Define evidence completeness as: every critical risk/control has at least one linked artifact, an owner, a timestamp, and a clear status.
- [ ] Define evidence provenance as: source system, generated-by, captured-at, and immutable linkage to the selected AI system and assessment run.
- [ ] Define approval-readiness as: no open critical evidence gaps, no unresolved high-severity blockers, and a traceable path from evidence to final decision.
- [ ] Treat missing evidence as a release blocker, not a reporting issue.
- [ ] Surface evidence gaps directly in `Risks` and `AI Governance`, then route them into `Remediation`.

### Remediation And Closure

- [ ] Create a remediation task when a governance blocker is high/critical, a control fails, or evidence is missing for a release decision.
- [ ] Require every remediation task to capture: `system`, `title`, `source`, `linked risk/control`, `owner`, `priority`, `status`, `re-test required`, `expected evidence`, and `closure notes`.
- [ ] Treat `re-test required` as a mandatory post-fix validation step that reruns the relevant check and records a changed outcome, not just a code or policy change.
- [ ] Do not advance approval while a critical remediation task is open, blocked, or missing re-test results.
- [ ] Mark a blocker closed only when the task is done, the fix evidence is attached, the re-test result is recorded, and the closure is linked back to the original risk/control.

### Swimlane: AI Governance / AI Ethics Engineer

- [ ] Define the governed lifecycle:
  - `AI system -> assessment -> risk -> evidence -> remediation -> approval -> release`
- [ ] Define explicit release-gate states:
  - `Go`
  - `Conditional Go`
  - `No-Go`
- [ ] Define evidence completeness rules for critical risks and controls.
- [ ] Define remediation closure and re-test criteria.
- [ ] Define full traceability chain:
  - risk -> control -> evidence -> remediation -> decision

Primary files/pages:
- `TODO_DEEP_ANALYSIS.md`
- `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`
- `apps/frontend/src/app/(dashboard)/risks/page.tsx`
- `apps/frontend/src/app/(dashboard)/evidence/page.tsx`
- `apps/frontend/src/app/(dashboard)/audit-reports/page.tsx`
- `apps/backend/src/api/routers/ai_governance.py`

Definition of done:
- Governance rules are explicit enough that the product can enforce them, not just describe them.

### Swimlane: Frontend Engineer

- [ ] Build `Evidence` as the missing bridge page and scope it to the selected AI system.
- [ ] Connect `Remediation` and `Remediation Wizard` directly to selected blockers and risks.
- [ ] Build a real `Onboard` entry flow and route users into the canonical path.
- [ ] Continue carrying selected AI-system context into reports, stakeholder, and compliance surfaces.
- [ ] Normalize navigation further around lifecycle flow instead of feature buckets.

Primary files/pages:
- `apps/frontend/src/components/workflow/SystemContext.tsx`
- `apps/frontend/src/app/(dashboard)/layout.tsx`
- `apps/frontend/src/app/(dashboard)/dashboard/page.tsx`
- `apps/frontend/src/app/(dashboard)/risks/page.tsx`
- `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`
- `apps/frontend/src/app/(dashboard)/evidence/page.tsx`
- `apps/frontend/src/app/(dashboard)/remediation/page.tsx`
- `apps/frontend/src/app/(dashboard)/remediation-wizard/page.tsx`
- `apps/frontend/src/lib/constants/navigation.ts`

Definition of done:
- A user can move through the workflow without losing scope or guessing the next action.

### Swimlane: Backend Engineer

- [ ] Add canonical `workspace` / `ai_system` backend entities.
- [ ] Anchor risks, evidence, approvals, and monitoring artifacts to those canonical entities.
- [ ] Promote governance tables to proper migrations instead of request-time lazy creation.
- [ ] Harden auth/session beyond demo-grade behavior.
- [ ] Remove route duplication between `api/routes` and `src/api/routers`.
- [ ] Expand pilot readiness checks to cover real governance workflow.

Primary files/routes:
- `apps/backend/api/main.py`
- `apps/backend/api/routes/auth.py`
- `apps/backend/api/routes/ai_governance.py`
- `apps/backend/src/api/routers/ai_governance.py`
- `apps/backend/api/routes/settings.py`
- `apps/backend/tests/test_ai_governance_routes.py`
- `apps/backend/scripts/pilot_readiness_check.py`

Definition of done:
- Frontend workflow is backed by one consistent AI-system-centric backend contract.

### Recommended Order

- [ ] Governance lane: define evidence and release-gate rules first.
- [ ] Frontend lane: implement `Evidence` workflow against current contracts.
- [ ] Backend lane: formalize canonical `ai_system` model and governance schema.
- [ ] Frontend lane: connect remediation directly to blockers.
- [ ] Governance + backend lanes: finalize approval state and decision history.

## Product UX/IA Deep TODO (User Adoption Focus)

### Why users will use FairMind (core jobs-to-be-done)

- Compliance/GRC user: prove audit readiness quickly with defensible evidence.
- ML/AI engineer: detect bias/risk, prioritize fixes, and pass release gates.
- Product/exec user: get a clear go/no-go decision and top blockers.
- Operations/security user: monitor live risk and act on incidents fast.

### Canonical Org Journey (Acme pilot baseline)

- [x] Define the canonical enterprise flow as:
  - Onboard workspace and users.
  - Connect model artifacts and representative datasets.
  - Run evaluations (bias, LLM judge where relevant, compliance, monitoring baselines).
  - Review risk, failed controls, and evidence.
  - Create remediation tasks and rerun tests.
  - Approve release with evidence-backed sign-off.
  - Operate continuously with alerts, reassessments, and audit exports.
- [ ] Make navigation and page hierarchy reflect this lifecycle instead of product modules.
- [ ] Add one visible "next step" action per stage so users do not have to infer the journey from the sidebar.

### Workflow-First Product Map

- [ ] Adopt one canonical object model:
  - `Workspace` -> `AI System` -> `Assessment Run` -> `Risk / Evidence / Decision`
- [ ] Reframe top-level product navigation to match the user journey:
  - `Dashboard`
  - `Onboard`
  - `Assess`
  - `Govern`
  - `Remediate`
  - `Operate`
  - `Reports`
  - `Settings`
- [ ] Map existing pages into workflow buckets instead of exposing them as peer tools:
  - `Onboard`: workspace setup, invites, model upload, dataset upload
  - `Assess`: `/bias`, `/modern-bias`, `/llm-judge`, `/compliance-dashboard`
  - `Govern`: `/risks`, `/ai-governance`, `/policies`, `/evidence`
  - `Remediate`: `/remediation`, `/remediation-wizard`
  - `Operate`: `/monitoring`, `/alerts`
  - `Reports`: `/reports`, `/audit-reports`, `/fairness-documentation`
- [ ] Add an always-visible system context bar:
  - selected AI system
  - owner
  - risk tier
  - readiness state
  - current stage
- [ ] Add one CTA per page that advances the system to the next lifecycle step.

### Next 3 Execution Sprints

#### Sprint A - Make the Journey Legible
- [ ] Convert dashboard into a decision screen:
  - readiness score
  - top blockers
  - missing evidence
  - next step CTA
- [ ] Replace module-first nav labels with workflow labels everywhere.
- [ ] Add a route audit for sidebar items and cross-links.
- [ ] Remove or hide low-frequency pages that do not support the canonical pilot path.

#### Sprint B - Make Governance Real
- [ ] Make `/risks` the working risk register for the selected AI system.
- [ ] Make `/ai-governance` the decision surface:
  - failed controls
  - evidence completeness
  - approval status
- [ ] Link remediation work from risks directly into `/remediation` and `/remediation-wizard`.
- [ ] Add release-gate status to policy and approval flows.

#### Sprint C - Make the Pilot Defensible
- [ ] Complete one end-to-end pilot happy path:
  - onboard
  - assess
  - review risk
  - remediate
  - approve
  - monitor
- [ ] Add exportable audit artifacts tied to evidence and decisions.
- [ ] Add operator/admin view for environment status and pilot support.
- [ ] Add analytics on conversion through the canonical journey.

### BUGS (Current Product-Breaking Issues)

- [x] Fix missing route/API mismatch causing dashboard error state:
  - `apps/frontend/src/lib/api/endpoints.ts` -> `/api/v1/database/dashboard-stats`
  - Verify backend endpoint exists and response contract matches `useDashboard`.
- [x] Fix broken nav link to non-existent route:
  - `apps/frontend/src/lib/constants/navigation.ts` contains `/alerts`
  - No `src/app/(dashboard)/alerts/page.tsx` currently present.
- [x] Fix collapsed sidebar hiding primary routes (`Dashboard`, `Settings`) when in icon mode:
  - `apps/frontend/src/components/layout/Sidebar.tsx` skips categories without `items` in collapsed state.
- [x] Fix Settings API contract mismatch:
  - `apps/frontend/src/app/(dashboard)/settings/page.tsx` calls `/api/v1/settings/`
  - Ensure backend route exists or wire to a real endpoint.
- [ ] Fix inconsistent deep links under Tests:
  - `apps/frontend/src/app/(dashboard)/tests/page.tsx` links to `/dashboard/bias-simple` path style; verify all links resolve and are intentional.

### ISSUES IN CURRENT DESIGN (UX + Information Architecture)

- [ ] Replace module-first IA with workflow-first IA:
  - Current: many parallel tools (`bias`, `modern-bias`, `advanced-bias`, `benchmarks`, etc.).
  - Target: `Scope -> Assess -> Remediate -> Monitor -> Prove`.
- [ ] Resolve current journey confusion explicitly:
  - `Risks`, `Policies`, `Evidence`, `Compliance`, `Monitoring`, and `Remediation` exist as separate destinations but not as one guided sequence.
  - Dashboard should expose the canonical journey and route users into the next required action.
- [ ] Define one canonical working object across product:
  - `AI System` (or `Compliance Project`) as the primary context.
  - Every page must be scoped to selected object.
- [ ] Redesign dashboard from descriptive to prescriptive:
  - Add top 3 blockers, next-best-actions, readiness score, owner/ETA.
- [ ] Reduce navigation entropy:
  - Merge overlapping pages and hide low-frequency/advanced tools behind second-level nav.
- [ ] Standardize page intent headers:
  - Each screen must clearly state: purpose, primary action, success criteria.
- [ ] Improve error/empty states:
  - Replace generic failures with guided recovery steps and fallback actions.
- [ ] Add role-oriented views:
  - Compliance mode, Engineering mode, Executive mode with tailored default widgets.
- [ ] Normalize terminology:
  - Use outcome language (`Assess Fairness Risk`, `Generate Audit Pack`) over tool names.

### Current UX Diagnosis

- [ ] The dashboard is descriptive, not directive.
- [ ] The sidebar exposes implementation modules, not business outcomes.
- [ ] There is no visible lifecycle state for an `AI System`.
- [ ] Risk, evidence, approvals, and remediation are not tightly linked in the UI.
- [ ] The user is asked to understand FairMind's architecture before they can complete a job.
- [ ] Several advanced pages compete with the primary pilot flow and should be demoted or grouped.

### FUTURE PRODUCT SCOPE EXPLANATION (What to Build Next and Why)

- [ ] Scope 1: Decision-Centric Dashboard (highest adoption impact)
  - Why: users need “what do I do next” before they need charts.
  - Deliverables: readiness scorecard, blockers, tasks, trend deltas.
- [ ] Scope 2: Workflow Engine for Governance Lifecycle
  - Why: converts features into repeatable compliance process.
  - Deliverables: guided flow states + completion checkpoints.
- [ ] Scope 3: Evidence and Audit Pack Layer
  - Why: core enterprise value is provability, not analysis alone.
  - Deliverables: evidence completeness, control mapping, one-click report bundle.
- [ ] Scope 4: Role-Based Experience
  - Why: mixed personas currently see too much irrelevant UI.
  - Deliverables: role-specific landing cards and defaults.
- [ ] Scope 5: Release Gate + Risk Acceptance
  - Why: ties analysis output to business decision and accountability.
  - Deliverables: pass/fail policy checks, approver flow, sign-off history.
- [ ] Scope 6: Post-Deployment Operations
  - Why: trust decays without continuous monitoring and incident handling.
  - Deliverables: alert routing, incident case workflow, remediation SLA tracking.

### Deep Implementation TODO (Prioritized)

#### P0 (Now)
- [ ] Close remaining route/API mismatches that still break journey continuity.
- [ ] Add frontend route audit test (assert every nav href resolves to page file or explicit redirect).
- [ ] Build workflow-first dashboard blocks:
  - current stage
  - blockers
  - evidence status
  - next recommended action
- [ ] Add AI-system context selection and persist it across core governance pages.
- [x] Backend full suite stabilization baseline:
  - Default pytest now runs deterministic local backend suite (`asyncio=strict`, excludes `e2e` by default).
  - Verified local result: `149 passed, 16 skipped, 6 deselected`.

#### P1 (Next)
- [ ] Finish workflow-first nav tree:
  - `Dashboard`
  - `Onboard`
  - `Assess`
  - `Govern`
  - `Remediate`
  - `Operate`
  - `Reports`
  - `Settings`
- [ ] Build unified “Assessment Run” entry flow from dashboard and onboarding.
- [ ] Link risk register, evidence, approvals, and remediation into one guided chain.

#### P2 (Scale)
- [ ] Add role presets and saved workspace layouts.
- [ ] Add in-product onboarding checklist tied to completion states.
- [ ] Add instrumentation events for funnel tracking:
  - `dashboard_loaded`
  - `next_action_clicked`
  - `assessment_completed`
  - `report_generated`
  - `incident_acknowledged`

### Success Metrics (Validation)

- [ ] Time-to-first-completed-assessment < 15 minutes.
- [ ] >60% of active users complete at least one guided next action per week.
- [ ] Report generation conversion increases week-over-week.
- [ ] Navigation backtracking rate decreases (proxy for IA confusion).
- [ ] Fewer dashboard hard-error sessions from API/route mismatches.

### Current Feature Working Status Audit (Product + Technical)

Legend:
- `Working`: usable end-to-end in current local setup.
- `Partial`: UI exists but backend/data flow or reliability gaps remain.
- `Blocked`: route/API missing or consistently failing.

#### Core App Access
- [x] Product frontend boots locally on `:1111` -> `Working`
- [x] Root (`/`) redirects to dashboard -> `Working`
- [ ] Authentication flow (`/login`, `/register`) end-to-end with real backend session -> `Partial`

#### Dashboard & Navigation
- [ ] Dashboard data widgets with real backend stats -> `Partial` (UI fallback and warning mode implemented; backend metric parity still pending)
- [x] Sidebar route integrity -> `Working` (`/alerts` route implemented)
- [x] Collapsed sidebar parity with expanded navigation -> `Working`

#### Bias / Fairness
- [ ] Bias Detection (`/bias`) core flow -> `Partial`
- [ ] Advanced/Modern/Multimodal bias pages coherence and shared outcomes -> `Partial`
- [ ] LLM Judge (`/llm-judge`) single + batch + multi-judge flow -> `Partial` (API contract stabilization in progress)
- [ ] Remediation Wizard (`/remediation-wizard`) with actionable downstream tasks -> `Partial`

#### Governance / Compliance
- [ ] Compliance dashboard (`/compliance-dashboard`) -> `Partial`
- [ ] Policies / risks / controls workflow continuity -> `Partial`
- [ ] Evidence collection and traceability -> `Partial`
- [ ] Compliance automation scheduling and execution visibility -> `Partial`

#### Monitoring / Operations
- [ ] Monitoring page (`/monitoring`) with live/near-live data -> `Partial`
- [ ] Alerts management UX -> `Partial` (route exists; end-to-end operations workflow still pending)
- [ ] Incident-style workflow (acknowledge, assign, resolve) -> `Partial/Missing`

#### Data / Models
- [ ] Datasets list + detail (`/datasets`, `/datasets/[id]`) -> `Partial`
- [ ] Models list + detail (`/models`, `/models/[id]`) -> `Partial`
- [ ] Model DNA / Provenance continuity into governance decisions -> `Partial`

#### Reports / Auditability
- [ ] Reports generation (`/reports`, `/audit-reports`) -> `Partial`
- [ ] Audit-evidence completeness scoring and export readiness -> `Partial`

#### Docs / Website Split
- [x] Marketing website isolation in `apps/website` -> `Working`
- [x] Docs app isolation in `apps/docs` -> `Working`
- [ ] Rich docs rendering/navigation (Fumadocs-grade experience) -> `Partial` (product landing content added; full Fumadocs navigation/search still pending)

#### Engineering Quality Signals
- [x] Backend non-e2e test gate passing (`149 passed`) -> `Working`
- [ ] Full stack e2e suite (with frontend + backend orchestration) -> `Partial` / environment-dependent
- [x] Archive import guardrails + backend boundary checks -> `Working`

### Pilot Readiness Fixes (Must Complete Before External Pilot)

#### PR0 - Hard blockers (pilot cannot start without these)
- [x] Resolve all nav dead-ends (`/alerts` and any 404-linked routes).
- [x] Ensure dashboard loads real org/project data by default (no user-facing “Not Found” noise).
- [ ] Validate login/session persistence and protected-route behavior.
- [ ] Establish one canonical “pilot happy path”:
  - create/select AI system
  - run assessment
  - review risks
  - remediate issues
  - approve release
  - generate report
- [x] Add deterministic demo/test seed data script for pilot environments.
  - `apps/backend/scripts/seed_demo_data.py` now seeds users/models/datasets/bias analyses/audit logs against Neon runtime schema.

### Canonical Pilot Pages

- [ ] `Dashboard`: readiness, blockers, next step
- [ ] `Onboard`: workspace/users/model/dataset setup
- [ ] `Assess`: run fairness, LLM, compliance, and monitoring baselines
- [ ] `Risks`: see automated and manual risk register entries
- [ ] `Governance`: review controls, evidence, and approval status
- [ ] `Remediation`: create and track fixes
- [ ] `Reports`: export artifacts for internal and external stakeholders
- [ ] `Operate`: monitor alerts and reassessment cadence

### Execution Status - March 12, 2026

- [x] Priority 1 complete: run full backend suite and close failures for default local backend run.
  - Resolved by test harness configuration for environment-sensitive failures:
    - E2E excluded by default test profile.
    - Async mode set to strict for Python 3.13 compatibility.
  - Backend command now green by default: `python -m pytest -q`.
- [x] Priority 2 complete: docs routing/navigation/search implemented in `apps/docs`.
  - Added docs index route with search: `/docs`.
  - Added per-doc routes: `/docs/[slug]`.
  - Added sidebar navigation between docs pages.
- [x] Priority 3 complete: Neon migration verification executed table-by-table.
  - Added audit script: `apps/backend/scripts/verify_neon_migration.py`.
  - Produced migration report: `apps/backend/docs/neon_migration_report.json`.
  - Current state: migration parity is incomplete (18 expected public tables missing; `auth.users` missing because Neon Auth uses `neon_auth.user` schema).

#### PR1 - Reliability and trust
- [ ] Add API health banner and graceful degraded-state messaging across main pages.
- [ ] Standardize frontend error handling and retry behavior for all critical hooks.
- [ ] Add telemetry for pilot funnel:
  - first login
  - first assessment run
  - first remediation action
  - first report export
- [ ] Lock copy and labels for pilot (remove “planned/missing” competitive wording from core task surfaces).

### Pilot Runtime Verification (Completed)

- [x] Neon runtime migration applied for required operational tables:
  - `apps/backend/scripts/migrate_neon_runtime_tables.py`
- [x] Pilot readiness automated check added and passing:
  - `apps/backend/scripts/pilot_readiness_check.py`
  - Report: `apps/backend/docs/pilot_readiness_report.json` (`overall_ok=true`)
- [x] Backend default test suite stabilized and passing:
  - `149 passed, 16 skipped, 6 deselected`
- [x] Frontend/docs/website production builds passing.

#### PR2 - Operator readiness
- [ ] Create pilot runbook:
  - startup steps
  - known limitations
  - incident response for common failures
  - rollback/fallback procedures
- [ ] Add “Pilot Admin” page or checklist with:
  - environment status
  - integration status
  - data freshness timestamps
- [ ] Define support SLA and ownership map for pilot issue triage.

#### PR3 - Outcome proof
- [ ] Add pilot success dashboard with:
  - assessments completed
  - open critical issues
  - evidence completeness
  - reports generated
- [ ] Add stakeholder-facing summary template (weekly) for pilot sponsors.

### Future Trends to Track (2026+)

- [ ] AI assurance over AI analytics:
  - Shift roadmap and messaging from “metrics dashboards” to “decision-grade assurance”.
  - Track buyer demand for evidence-backed release decisions.
- [ ] GenAI governance baseline requirements:
  - Track emerging expectations around prompt governance, content provenance, and misuse testing.
- [ ] Cybersecurity + AI governance convergence:
  - Track cross-functional controls connecting model risk and security risk.
- [ ] Continuous incident and near-miss governance:
  - Track requirements for structured incident capture, RCA, and regulator/auditor reporting.
- [ ] Standards/procurement-led adoption:
  - Track customer RFP requirements for framework/control mappings and assurance artifacts.

### Trend-Aligned New Features (Net-New Product Capabilities)

#### NF1 - AI Assurance Control Tower
- [ ] Add unified readiness score:
  - release readiness
  - compliance readiness
  - runtime risk posture
- [ ] Add decision panel:
  - `Go / Conditional Go / No-Go`
  - top blockers
  - blocker owners + ETA
- [ ] Add control coverage matrix:
  - control -> evidence -> status -> last verified

#### NF2 - Incident & Hazard Operations
- [ ] Build incident lifecycle object:
  - detect -> triage -> assign -> mitigate -> RCA -> close
- [ ] Add near-miss capture and trend reporting.
- [ ] Add export templates for incident summaries and regulator-ready records.

#### NF3 - GenAI Governance Pack
- [ ] Prompt/test set registry with version history.
- [ ] Prompt risk and guardrail policy checks.
- [ ] Content safety and provenance checks integrated into assessment runs.
- [ ] Red-team/abuse scenario test workflows with pass/fail gates.

#### NF4 - Cyber-AI Convergence Layer
- [ ] Add adversarial ML posture board tied to model/system entities.
- [ ] Map AI governance findings to security controls.
- [ ] Add threat-model snapshots by AI system and deployment context.

#### NF5 - Evidence Graph & Audit Pack
- [ ] Add evidence integrity metadata:
  - source
  - timestamp
  - owner
  - hash/checksum
- [ ] Build “missing evidence” assistant per framework.
- [ ] Add one-click auditor packet generator with traceability index.

#### NF6 - Enterprise Trust & Procurement Features
- [ ] Add trust-center output pipeline (approved public disclosures).
- [ ] Add vendor/model third-party assurance workspace.
- [ ] Add framework mapping pack for enterprise procurement responses.

### Pilot-to-Enterprise Expansion Plan

#### EP0 - Pilot Completion Gate
- [ ] Ensure one complete and measurable customer journey:
  - create scope
  - run assessment
  - remediate issue
  - generate report
  - monitor post-release

#### EP1 - Early Enterprise Readiness
- [ ] Add SSO/role model hardening for enterprise org structures.
- [ ] Add tenancy-safe audit exports and access controls.
- [ ] Add SLA-grade observability for core workflows.

#### EP2 - Enterprise Scale Features
- [ ] Cross-team workflow routing (compliance/ML/security ownership handoffs).
- [ ] Portfolio-level risk rollups across AI systems.
- [ ] Multi-jurisdiction policy packs and control inheritance.

### Standards/Framework Mapping Backlog

- [ ] Create canonical internal control schema:
  - `control_id`, `requirement_text`, `evidence_requirements`, `pass_criteria`
- [ ] Build crosswalk engine:
  - one internal control mapped to multiple frameworks.
- [ ] Add framework-specific evidence templates.
- [ ] Add framework delta reports:
  - “what additional controls needed for market X”.
- [ ] Add versioned framework packs with migration notes.

### Competitive Future Scope (What to Add Beyond Current Parity)

- [ ] AI release governance board with sign-off workflow.
- [ ] Autonomous compliance checks on CI/CD model promotion paths.
- [ ] Scenario simulation for regulatory stress-testing.
- [ ] Counterfactual fairness and intervention impact simulator.
- [ ] Continuous trust score with drift-aware confidence bounds.

## P0 - Restore Runtime Stability

- [x] Fix route import coupling in `apps/backend/api/routes/__init__.py` so one broken module does not block unrelated routes.
- [x] Fix invalid relative imports in `apps/backend/api/services/real_ai_bom_service.py` (`...database` import path issue).
- [x] Rename reserved SQLAlchemy attribute `metadata` in:
  - [x] `apps/backend/database/india_compliance_models.py`
  - [x] `apps/backend/database/india_rag_models.py`
- [ ] Remove import-time side effects in compliance automation:
  - [x] Stop starting `AsyncIOScheduler` during module import.
  - [x] Move scheduler start/stop to FastAPI lifespan hooks.
- [x] Re-verify active runtime routes after fixes (scripted route dump from `api.main`).
- [x] Fix domain dataset typing regression that blocked optional router import (`UploadedFile` protocol restore).

## P1 - Fix LLM-as-Judge End-to-End

- [ ] Ensure LLM Judge router reliably loads into app (`/api/v1/bias/llm-judge/*`).
- [ ] Align API contract for multi-judge endpoint:
  - [x] Backend should accept JSON body via Pydantic model.
  - [x] Frontend request shape should match backend model exactly.
- [x] Ensure `judge_model` is actually used in batch/multi-category evaluation calls.
- [ ] Add explicit `response_model` for batch and multi-judge endpoints.
- [ ] Mark mock-evaluation mode clearly in API response metadata and UI.

## P1 - Backend Architecture Reorg (Current Pass)

- [x] Split website/docs apps and make docs app build independently.
- [x] Introduce backend layered structure under `apps/backend/src`.
- [x] Centralize explicit API router registration.
- [x] Archive duplicate domain route trees.
- [x] Archive verified duplicate services:
  - [x] `domain/bias_detection/services/bias_detection_service.py`
  - [x] `domain/compliance/services/india_compliance_service.py`
  - [x] `application/services/bias_detection_service.py` (unused)
- [x] Add backend service ownership audit + ownership map docs.
- [ ] Decide whether to keep adapter duplicates (`dataset/monitoring/alert`) permanently or collapse imports directly to domain.

## P1 - Frontend API Contract Consistency

- [ ] Standardize all hooks to handle `ApiResponse<T>` (`success`, `data`, `error`) consistently.
- [x] Fix `useLLMJudge` to read `response.data` instead of treating wrapper as raw data.
- [ ] Audit/fix similar patterns in:
  - [ ] `apps/frontend/src/lib/api/hooks/useRemediation.ts`
  - [ ] `apps/frontend/src/lib/api/hooks/useDatasets.ts`
  - [ ] Other hooks under `apps/frontend/src/lib/api/hooks/`

## P1 - Test Harness Repair

- [ ] Fix `apps/backend/tests/conftest.py` `TestSettings` incompatibilities:
  - [ ] Handle `environment="testing"` cleanly.
  - [ ] Correct Optional types for `redis_url` and `sentry_dsn`.
- [ ] Add focused tests for LLM Judge:
  - [x] `/models`
  - [ ] `/evaluate`
  - [x] `/evaluate-batch`
  - [x] `/evaluate-with-multiple-judges`
- [ ] Add frontend integration test for LLM Judge page flow.
- [ ] Provide a local test command/profile that can run targeted suites without global coverage gate blocking.

## P2 - Config and Security Hardening

- [ ] Require explicit `SECRET_KEY` and `JWT_SECRET` in non-dev environments (no runtime-random defaults in prod paths).
- [ ] Simplify CORS behavior:
  - [ ] Remove custom OPTIONS handler unless strictly needed.
  - [ ] Ensure no `Access-Control-Allow-Origin: *` with credentials.
- [ ] Reduce blanket `except Exception` usage in high-impact services and routes.

## P2 - Migration and Codebase Hygiene

- [ ] Decide target architecture: fully domain-discovered routes vs legacy manual route includes.
- [ ] Remove dead/placeholder TODOs in production paths or track them as explicit issues.
- [ ] Reduce import style fragmentation (`apps.backend.*`, `domain.*`, `api.*`, relative).
- [ ] Update Pydantic v2 configs (`schema_extra` -> `json_schema_extra`, `class Config` modernization).

## Verification Checklist

- [ ] Import check passes for all route modules.
- [x] Import check passes for all active optional routes except expected env-dependent modules (e.g., torch-backed modern bias module).
- [ ] FastAPI startup has no route-load warnings.
- [ ] Route inventory includes expected LLM Judge endpoints.
- [ ] Backend targeted tests pass.
- [x] Backend targeted tests pass (`test_api.py`, `test_ai_governance_routes.py`).
- [ ] Frontend LLM Judge page works against local backend.
- [ ] No regression in existing dashboard/navigation flows.

# VerifyWise vs FairMind Compliance Gap Analysis

Date: 2026-03-03
Compared repositories:
- FairMind: `/Users/adhi/axonome/fairmind`
- VerifyWise: `/Users/adhi/axonome/fairmind/_external/verifywise`

## Executive Summary

FairMind is strong on bias/fairness analytics and has baseline compliance checks, but it is missing most enterprise GRC workflow surfaces that VerifyWise provides (approval workflows, policy lifecycle, vendor governance, incident management, post-market monitoring, trust center, automation engine, and shadow AI governance).

You can add these capabilities, but not as a small patch. A realistic path is a phased build:
- Phase 1 (4-6 weeks): compliance framework normalization + evidence hub hardening + policy lifecycle MVP.
- Phase 2 (6-10 weeks): incident + vendor/model risk + approval workflows.
- Phase 3 (8-12 weeks): post-market monitoring + trust center + automation rules + reporting parity.
- Phase 4 (optional, 8+ weeks): shadow AI/agent discovery/AI detection governance.

## Evidence Snapshot

FairMind implemented routes mainly include:
- `apps/backend/api/routes/compliance_check.py`
- `apps/backend/api/routes/compliance_reporting.py`
- `apps/backend/api/routes/india_compliance.py`
- `apps/backend/api/routes/real_ai_bom.py`
- `apps/backend/api/routes/monitoring.py`

FairMind route references in main include modules not present in `apps/backend/api/routes`:
- `security`, `fairness_governance`, `advanced_fairness`, `comprehensive_bias_evaluation`, `realtime_model_integration`, `benchmark_suite`, `model_performance_benchmarking`, `ai_governance`
- See `apps/backend/api/main.py` include blocks and `apps/backend/api/routes/__init__.py`.

VerifyWise has implemented domain routes/services for governance stack:
- `Servers/routes/approvalWorkflow.route.ts`, `approvalRequest.route.ts`
- `policy.route.ts`, `policyFolder.route.ts`, `policyLinkedObjects.route.ts`
- `vendor.route.ts`, `vendorRisk.route.ts`, change-history routes
- `aiIncidentManagement.route.ts`, `postMarketMonitoring.route.ts`
- `evidenceHub.route.ts`, `automation.route.ts`
- `aiTrustCentre.route.ts`, `ceMarking.route.ts`
- `shadowAi.route.ts`, `agentDiscovery.route.ts`, `dataset.route.ts`, `modelInventory.route.ts`
- Technical docs: `docs/technical/domains/*.md`

## Feature Gap Matrix

Scale:
- Status: `Present`, `Partial`, `Missing`
- Effort: `S`, `M`, `L`, `XL`

| Capability (VerifyWise) | FairMind Status | Evidence in FairMind | Effort | Notes |
|---|---|---|---|---|
| Multi-framework compliance data model (EU/ISO/NIST with role workflow states) | Partial | `apps/backend/api/routes/compliance_check.py`, `compliance_reporting.py` | L | FairMind has checks, but not normalized per-framework implementation workflow objects (owner/reviewer/approver lifecycle). |
| Evidence Hub with foldering/linking to controls/risks | Partial | `apps/backend/domain/compliance/services/evidence_service.py`, `api/services/india_evidence_collection_service.py` | M-L | Evidence exists, but no full evidence-hub object graph + folder/link UX parity. |
| Policy management (templates, folders, linked objects, versioning) | Missing/Doc-only | Frontend endpoints mention `/ai-governance/policies`; backend route absent | L | Need policy entities + versioning + linkage to controls/risks/evidence. |
| Approval workflows (request, step approvals, approvers, statuses) | Missing | No backend route/module in `apps/backend/api/routes` | L | Core enterprise feature; prerequisite for policy/model/compliance signoff. |
| Vendor registry and vendor risk management | Missing | No vendor domain routes in backend | M-L | Add vendor profile, assessments, periodic review, risk scoring. |
| Model inventory with model risk register and history | Partial | Model concepts across core + AIBOM; no dedicated governance inventory/risk workflow routes | M-L | FairMind tracks models but lacks governance lifecycle table/workflow parity. |
| AI incident management + incident history | Missing | Monitoring alerts exist; governance incident module absent | M | Distinct from runtime alerts; needs incident case workflow + RCA + remediation tracking. |
| Post-market monitoring cycles and reports | Missing | Generic monitoring exists; no PMM governance module | M-L | Add scheduled questionnaires, concerns, cycle reports. |
| CE marking registry and linkage | Missing | No CE-specific domain in backend | M | Niche but useful for EU high-risk systems. |
| AI Trust Center (public transparency portal) | Missing | No trust center routes/backend models | M-L | Requires public-safe projection layer and approval pipeline. |
| Dataset registry (governance metadata + change history) | Partial | Dataset upload/list routes exist | M | Need governance metadata, lineage links, audit/history parity. |
| Automation engine (trigger/action rules across governance objects) | Missing | Compliance scheduling exists, but no generic rule engine | L | Build event bus + trigger/action + execution logs. |
| Shadow AI detection/governance | Missing | No shadow AI routes/services | XL | High-complexity ingestion, identity mapping, policy enforcement. |
| Agent discovery and linking to known models | Missing | No agent discovery routes/services | XL | Requires telemetry connectors and model/tool registry matching. |
| AI detection risk scoring (governance context) | Partial | Bias/security analysis exists, but no unified governance finding engine | L | Can extend existing analytics stack into governance scoring. |
| Reporting parity (PDF/DOCX governance reports) | Partial | Report generation exists in domain reports | M | Need richer templates for governance entities and evidence references. |
| Audit/change history across entities | Partial | Some logs exist; no broad entity-level change-history modules | M-L | Add append-only history tables + API + UI timeline components. |

## Missing Items You Should Prioritize

### P0: Foundation Gaps (Block enterprise governance)
- [ ] Create canonical governance data model for: `framework_control`, `evidence_item`, `policy`, `approval_workflow`, `approval_request`, `incident`, `vendor`, `model_risk`, `dataset_registry`, `audit_event`.
- [ ] Implement actual `ai-governance` backend router modules that frontend already references in `apps/frontend/src/lib/api/endpoints.ts`.
- [ ] Clean route registration inconsistencies in `apps/backend/api/main.py` (it references modules not present under `apps/backend/api/routes`).

### P1: High-value VerifyWise parity
- [ ] Policy Manager MVP: CRUD + version + reviewer/approver statuses.
- [ ] Approval Workflow MVP: reusable step-based approval with role assignments.
- [ ] Incident Management MVP: create/update/status workflow + severity + remediation tasks.
- [ ] Vendor + Vendor Risk MVP: vendor profile, review date, risk score, linked controls.
- [ ] Evidence Hub V2: evidence folders/tags + links to controls/policies/incidents.

### P2: Compliance lifecycle depth
- [ ] Model Inventory Governance layer: risk register + lifecycle states + decision log.
- [ ] Post-Market Monitoring: recurring questionnaires + flagged concerns + archived reports.
- [ ] Trust Center: public-facing approved disclosures and compliance badges.
- [ ] Unified reporting templates (PDF + JSON) for auditors and regulators.

### P3: Advanced governance (optional/strategic)
- [ ] Automation engine: event-triggered notifications/actions.
- [ ] Shadow AI and Agent Discovery ingestion connectors.
- [ ] Governance-aware AI detection scoring and enforcement workflows.

## Can We Add VerifyWise-like Features to FairMind?

Yes, technically feasible. Constraints are architecture and sequencing, not capability.

Key integration strategy:
1. Keep FairMind's strength (bias/fairness pipelines) as the scoring engine.
2. Add a governance orchestration layer (workflows, approvals, entities, evidence links).
3. Unify data contracts so frontend `ai-governance` endpoints map to real backend implementations.
4. Deliver in vertical slices (policy + approvals first), not by building all tables first.

## Proposed Implementation Roadmap

### Phase 1 (4-6 weeks)
- [ ] Define DB schema + migrations for policy/evidence/approval core entities.
- [ ] Implement `/api/v1/ai-governance/policies`, `/compliance/frameworks`, `/evidence/*` endpoints.
- [ ] Wire frontend hooks to real endpoints and remove placeholder assumptions.

### Phase 2 (6-10 weeks)
- [ ] Add incident + vendor + model-risk domains.
- [ ] Add change-history tracking and audit timelines.
- [ ] Add report templates for compliance and incidents.

### Phase 3 (8-12 weeks)
- [ ] Add post-market monitoring and trust center.
- [ ] Add automation triggers/actions + execution logs.
- [ ] Add role-based approval gates on publish/export operations.

### Phase 4 (optional, 8+ weeks)
- [ ] Add shadow AI/agent discovery connectors and governance dashboard.

## Build-vs-Adopt Notes

- Reusing VerifyWise code directly is non-trivial because it is a separate TypeScript monolith architecture (`Servers` + custom domain models), while FairMind backend is Python/FastAPI DDD-style with different persistence patterns.
- Practical approach: borrow product patterns and data model ideas, not direct code transplant.
- Fastest value path is API and data-model parity for the top 5 domains: policy, approval, evidence, incident, vendor risk.

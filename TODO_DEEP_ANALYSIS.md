# FairMind Deep Audit TODO

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

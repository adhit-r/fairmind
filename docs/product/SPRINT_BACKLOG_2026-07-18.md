# FairMind Evidence Workbench Recovery Backlog

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this backlog story by story. Each story ends at an independently reviewable evidence gate.

**Goal:** Recover FairMind as a vendor-neutral assurance evidence workbench that turns real evaluation outputs into immutable, reviewable, reusable Evidence Passports and framework-pinned assurance packages.

**Architecture:** Integrate the existing organization-scoped assurance spine with the FairMind-E vertical slice in an isolated worktree. Evaluators emit one canonical passport through an application port; reviewers decide mappings; backend-derived readiness and reports consume only accepted, current evidence. Cleanup follows the live assurance closure instead of running ahead of it.

**Tech stack:** FastAPI, Pydantic, SQLAlchemy, PostgreSQL and SQLite test support, Next.js, TypeScript, Playwright, JSON Schema Draft 2020-12, SHA-256, RFC 8785 canonical JSON.

## Global constraints

- The user requested autonomous execution and selected the evidence-compiler approach over a generic GRC suite or proprietary test lab.
- Preserve the current and sibling worktrees' unrelated dirty state. Integrate in a separate `codex/fairmind-evidence-recovery` worktree.
- Do not claim compliance or certification. FairMind provides supporting evidence, readiness, review workflow, and assurance-package preparation.
- Respect `api -> application -> domain -> infrastructure`; domain code does not import FastAPI.
- Every tenant record and resource-by-ID query is organization-scoped.
- Evaluator capability state is one of `validated`, `metadata_only`, `external_provider`, `unavailable`, or `insufficient_data`.
- Missing credentials, missing cohorts, missing media content, provider errors, or empty evidence never produce pass, accepted evidence, "not biased," or readiness.
- Artifact bodies remain in controlled storage. Governance records contain bounded references and SHA-256 digests.
- Candidate mappings require human acceptance or rejection. Automation cannot satisfy a control.
- Failed, rejected, stale, error, superseded, and retest records remain auditable.
- UI follows `PRODUCT.md`, `DESIGN.md`, and `AGENTS.md`: no emoji, no purple gradients, no generic AI styling, and no marketing hero treatment in workflows.

---

## Sprint 1 — Trustworthy assurance spine

Sprint 1 ends when one real FairMind-E or tabular evaluation moves through an organization-scoped passport, mapping review, readiness calculation, and manifest preview without a fabricated or ambiguous state.

### S1.1 P0 — Isolated integration baseline

**Outcome:** Reconcile the assurance worktree's 27-commit line and the current branch's three post-merge-base FairMind-E commits without mutating either dirty worktree.

**Files:**

- Integrate from: `/Users/adhi/axonome/fairmind-ai-governance-assurance`
- Preserve from current: `apps/backend/src/domain/environmental/`
- Preserve from current: `apps/backend/src/application/services/environmental_service.py`
- Preserve from current: `apps/backend/src/api/routers/environmental.py`
- Preserve from current: `apps/backend/tests/test_environmental*.py`
- Record: `docs/product/integration-baseline-2026-07-18.md`

**Interfaces:**

- Consumes: Current branch at `c7845fb` and the sibling assurance branch descended from merge-base `bd1345c`.
- Produces: A clean recovery worktree with both assurance and FairMind-E tests discoverable.

**Execution:**

1. Record branch, HEAD, status, and diff stat for both source worktrees.
2. Create the recovery worktree from the agreed base with branch prefix `codex/`.
3. Apply committed assurance history and committed FairMind-E history; do not copy uncommitted files implicitly.
4. Resolve overlap by retaining organization-scoped assurance models and all post-base environmental decision/approval behaviour.
5. Record the exact commit range, conflicts, resolutions, and named baseline failures in the integration-baseline document.

**Acceptance evidence:**

```bash
git status --short
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
cd apps/backend
uv run pytest tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py tests/test_governance_assurance_routes.py tests/test_governance_evidence_runs.py tests/test_environmental.py tests/test_environmental_api.py tests/test_environmental_governance.py -q
```

Expected: the recovery worktree contains only intentional integration changes; both architecture guards exit 0; the selected assurance and environmental suites pass. Any pre-existing unrelated collection failure is named with its exact test and error rather than hidden.

### S1.2 P0 — Canonical Evidence Passport contract and ingestion port

**Outcome:** Make `docs/product/evidence-passport.schema.json` the versioned exchange contract and enforce immutable, idempotent ingestion.

**Files:**

- Use: `docs/product/evidence-passport.schema.json`
- Create: `apps/backend/src/domain/assurance/evidence_passport.py`
- Create: `apps/backend/src/application/ports/evidence_ingestion.py`
- Create: `apps/backend/src/application/services/evidence_ingestion_service.py`
- Modify: `apps/backend/src/api/routers/governance_assurance.py`
- Modify: `apps/backend/src/infrastructure/db/database/governance_models.py`
- Create from the assurance source migration: `apps/backend/migrations/011_governance_assurance.sql`
- Test: `apps/backend/tests/test_evidence_passport_schema.py`
- Test: `apps/backend/tests/test_governance_evidence_runs.py`

**Interfaces:**

- Consumes: `Evidence Passport` JSON conforming to schema version `1.0.0`.
- Produces: `ingest(passport, org_id, actor_id) -> EvidenceRun`, idempotent on organization, system, source, run ID, and immutable `runContentHash`.
- Conflict: Reusing the immutable run identity with different canonical content returns HTTP 409 and appends an audit event.

**Execution:**

1. Mirror the JSON Schema enums and required fields in domain Pydantic models; keep HTTP aliases in the API layer.
2. Calculate lowercase `runContentHash` over the immutable RFC 8785 execution envelope plus ordered artifacts. Calculate `canonicalContentHash` over the full passport snapshot after omitting that field and signatures; increment `passportRevision` and link `previousRevisionHash` when review-state snapshots change.
3. Reject raw artifact bodies, more than 50 artifact pointers, malformed hashes, absolute framework-import paths, unknown top-level properties, and mismatched client hashes.
4. Store the immutable run and artifact metadata in one transaction, then propose candidate mappings without changing control status.
5. Preserve error and unavailable executions with limitations and diagnostic artifact references.

**Acceptance evidence:**

```bash
python3 -m json.tool docs/product/evidence-passport.schema.json >/dev/null
cd apps/backend
uv run pytest tests/test_evidence_passport_schema.py tests/test_governance_evidence_runs.py -q
```

Expected tests: valid fixture accepted; unknown property rejected; uppercase or malformed digest rejected; identical replay returns the original run; changed content under the same run identity returns 409; raw output body rejected; third-party source without assessor identity rejected; `unavailable` cannot carry a passing result.

### S1.3 P0 — Organization scope, immutable framework catalog, and reviewed mappings

**Outcome:** Make system, framework assignment, control assessment, evidence, review, and readiness paths organization-safe and version-pinned.

**Files:**

- Integrate: `apps/backend/src/application/services/framework_catalog_service.py`
- Integrate: `apps/backend/src/application/services/governance_assurance_service.py`
- Modify: `apps/backend/src/api/routers/governance_assurance.py`
- Modify: `apps/backend/api/main.py`
- Modify: `apps/backend/src/infrastructure/db/database/governance_models.py`
- Modify: `apps/backend/migrations/governance_assurance_migration.py`
- Test: `apps/backend/tests/test_framework_catalog_service.py`
- Test: `apps/backend/tests/test_governance_assurance_membership.py`
- Test: `apps/backend/tests/test_governance_assurance_routes.py`
- Test: `apps/backend/tests/test_multi_org_e2e.py`

**Interfaces:**

- Produces immutable `FrameworkVersion`, `FrameworkControlDefinition`, `FrameworkAssignment`, `SystemControlAssessment`, and reviewed mapping records.
- Produces readiness with numerator, denominator, exclusions, missing accepted evidence, stale evidence, rejected assessments, and blocking findings.

**Execution:**

1. Renumber the sibling assurance migration from `009_governance_assurance.sql` to `011_governance_assurance.sql` because the product branch already contains `009_policy_versions.sql` and `010_environmental_governance.sql`; record the single resulting migration order.
2. Mount the assurance router as a required route; startup fails visibly if it cannot import.
3. Scope every resource lookup by `org_id` plus resource ID and derive actors from authentication.
4. Keep catalog definitions immutable and tenant-neutral; keep owner, applicability, status, and review on the system assessment.
5. Import managed framework sources atomically and persist source URI, source hash, version, and licensing note.
6. Preserve the historical April 2026 AIUC workbook fixture expectations of 51 requirements and 135 controls in fixture-specific tests; label them historical and do not present them as the current public count.
7. Require mapping-review rationale and optimistic `reviewVersion`; stale reviewers receive HTTP 409.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_framework_catalog_service.py tests/test_governance_assurance_membership.py tests/test_governance_assurance_routes.py tests/test_multi_org_e2e.py -q
```

Expected: cross-organization list/read/create/update/review/report requests fail closed; duplicate framework source hash is idempotent; changed source creates a new immutable version; candidate mapping does not affect readiness; accepted current mapping affects only the intended assignment; rejected and stale evidence remain blockers.

### S1.4 P0 — Remove fabricated and false-negative evaluator states

**Outcome:** No visible evaluator fabricates results or converts unavailable/insufficient input into success.

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/modern-bias/page.tsx`
- Modify: `apps/frontend/src/lib/api/hooks/useModernBias.ts`
- Modify: `apps/backend/src/domain/bias/services/llm_judge_service.py`
- Modify: `apps/frontend/src/app/(dashboard)/bias/page.tsx`
- Modify: `apps/frontend/src/lib/api/endpoints.ts`
- Modify: `apps/backend/src/api/routers/multimodal_bias_detection.py`
- Modify: `apps/backend/src/application/services/multimodal_bias_detection_service.py`
- Modify: `apps/frontend/src/lib/api/hooks/useMultimodalBias.ts`
- Modify: `apps/frontend/src/app/(dashboard)/multimodal-bias/page.tsx`
- Test: `apps/backend/tests/test_llm_judge_routes.py`
- Create: `apps/backend/tests/test_multimodal_capability_contract.py`
- Modify: `apps/frontend/tests/bias-detection.spec.ts`

**Interfaces:**

- Produces one of the five capability states and one explicit evaluation result status.
- Multimodal output remains `metadata_only` until a validated media worker exists.

**Execution:**

1. Delete the browser-generated modern-bias result path and remove its export action.
2. Replace mock `PASS` error fallbacks with `unavailable` plus a bounded diagnostic reason.
3. Route `/bias` to one tested endpoint or render an unavailable launcher with no submission action.
4. Normalize multimodal label nesting and response casing at the API boundary.
5. Return `insufficient_data` when sample labels, cohorts, or media analysis are absent; never set a negative bias conclusion from absence.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_llm_judge_routes.py tests/test_multimodal_capability_contract.py -q
cd ../frontend
npx playwright test tests/bias-detection.spec.ts --project=chromium --workers=1
npm run build
```

Expected: no mock result string is present in production source; missing provider key renders unavailable; unlabelled media renders insufficient data; no such state displays "Not Biased" or enables an assurance export.

### S1.5 P0 — FairMind-E and one real bias adapter

**Outcome:** Two heterogeneous evaluators write through the same passport contract.

**Files:**

- Create: `apps/backend/src/application/adapters/evidence/environmental_adapter.py`
- Create: `apps/backend/src/application/adapters/evidence/tabular_fairness_adapter.py`
- Modify: `apps/backend/src/application/services/environmental_service.py`
- Modify: the selected real tabular evaluator under `apps/backend/src/application/services/`
- Test: `apps/backend/tests/test_environmental_evidence_adapter.py`
- Test: `apps/backend/tests/test_tabular_evidence_adapter.py`

**Interfaces:**

- Both adapters implement the application port from S1.2 and return a schema-valid passport payload.
- Adapters propose control IDs but cannot accept mappings or approve a system.

**Execution:**

1. Map environmental assessment version, provenance confidence, measurements, thresholds, recommendation, limitations, artifacts, risks, and approval gate into the passport.
2. Map the selected fairness evaluator's dataset fingerprint, cohorts, exclusions, metric versions, thresholds, results, and plots/reports into the same contract.
3. Preserve the source system's native artifact and store its digest; do not flatten away tool-specific metrics.
4. Make repeated conversion deterministic for the same source run.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_environmental_evidence_adapter.py tests/test_tabular_evidence_adapter.py tests/test_environmental_governance.py -q
```

Expected: both fixtures validate against schema `1.0.0`; identical source run yields the same `runContentHash`; a changed threshold, subject version, dataset hash, or evaluator version changes that hash; FairMind-E `no_go` and missing evidence continue to block approval.

### S1.6 P1 — Six-task assurance navigation and review surface

**Outcome:** Users retain organization/system context while moving from evidence to mapping decision and readiness trace.

**Files:**

- Integrate: `apps/frontend/src/lib/api/hooks/useGovernanceAssurance.ts`
- Integrate: `apps/frontend/src/app/(dashboard)/evidence/components/EvaluationRunList.tsx`
- Integrate: `apps/frontend/src/app/(dashboard)/evidence/components/EvidenceMappingReview.tsx`
- Integrate: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/FrameworkCatalog.tsx`
- Integrate: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/ControlAssessmentTable.tsx`
- Integrate: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/ControlTracePanel.tsx`
- Modify: `apps/frontend/src/lib/constants/navigation.ts`
- Modify: `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/model-inventory/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/evidence/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/risks/page.tsx`
- Test: `apps/frontend/src/lib/api/hooks/useGovernanceAssurance.test.ts`
- Test: `apps/frontend/tests/governance-assurance.spec.ts`

**Interfaces:**

- Consumes org-scoped assurance APIs from S1.3.
- Produces visible passport provenance, capability state, freshness, candidate/accepted/rejected mappings, and readiness trace.

**Execution:**

1. Limit primary assurance navigation to Overview, AI Systems, Frameworks & Controls, Evidence & Evaluations, Findings, and Reports & Assurance.
2. Keep selected organization and system in a compact persistent scope strip.
3. Render subject, evaluator version, threshold, result, artifact hash, limitations, review state, and freshness before aggregate scoring.
4. Require keyboard-complete mapping acceptance/rejection with rationale and visible optimistic-conflict recovery.
5. Apply `DESIGN.md`: square geometry, 2px/4px borders, restrained teal/orange signals, hard shadows only for actionable surfaces, non-color state labels, and 44px controls.

**Acceptance evidence:**

```bash
cd apps/frontend
bun test src/lib/api/hooks/useGovernanceAssurance.test.ts
./node_modules/.bin/tsc --noEmit --pretty false
npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1
npm run build
```

Expected: six destinations are keyboard reachable; organization/system context survives navigation; candidate evidence is visibly non-accepted; unknown counts remain unknown; mobile and 200% zoom retain labels and actions.

## Sprint 2 — Portable adapters and assurance packages

Sprint 2 ends when external tool output can be imported, reviewed, remediated, retested, and exported as a deterministic, version-pinned assurance manifest with bounded AIUC-1 and EU AI Act support language.

### S2.1 P1 — External artifact adapter kit

**Outcome:** Import concrete outputs from established test tools without adding their runtime engines to FairMind.

**Files:**

- Create: `apps/backend/src/application/adapters/evidence/base.py`
- Create: `apps/backend/src/application/adapters/evidence/giskard_adapter.py`
- Create: `apps/backend/src/application/adapters/evidence/mlflow_adapter.py`
- Create: `apps/backend/src/application/adapters/evidence/fairness_adapter.py`
- Create: `apps/backend/src/application/adapters/evidence/modelscan_adapter.py`
- Create: `apps/backend/src/application/adapters/evidence/llm_redteam_adapter.py`
- Create: `apps/backend/src/api/routers/evidence_imports.py`
- Create: `apps/backend/tests/fixtures/evidence_adapters/`
- Create: `apps/backend/tests/test_external_evidence_adapters.py`

**Interfaces:**

- `detect(document_metadata) -> confidence`
- `convert(document, context) -> EvidencePassport`
- Adapter identities cover Giskard, MLflow, Fairlearn/AIF360, ModelScan, and garak/PyRIT export families.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_external_evidence_adapters.py tests/test_evidence_passport_schema.py -q
```

Expected: each golden fixture creates a schema-valid passport; source-native IDs and metrics remain traceable; unknown formats fail without partial writes; LLM-judge results retain judge identity and limitation; no adapter sets a framework mapping to accepted.

### S2.2 P1 — Finding, remediation, retest, and freshness graph

**Outcome:** Preserve the full negative-result and correction history without resetting evidence.

**Files:**

- Modify: `apps/backend/src/application/services/governance_assurance_service.py`
- Modify: `apps/backend/src/infrastructure/db/database/governance_models.py`
- Modify: `apps/backend/src/api/routers/governance_assurance.py`
- Modify: `apps/frontend/src/app/(dashboard)/risks/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/remediation/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/evidence/page.tsx`
- Create: `apps/backend/tests/test_assurance_remediation_lineage.py`
- Modify: `apps/frontend/tests/governance-assurance.spec.ts`

**Interfaces:**

- Produces immutable links from finding to remediation and from clean retest passport to failed predecessor passport.
- Freshness invalidates only evidence affected by system, subject, input, prompt, configuration, threshold, evaluator, suite, framework, scope, or time changes.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_assurance_remediation_lineage.py tests/test_governance_evidence_runs.py -q
cd ../frontend
npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1
```

Expected: closing a remediation without a verification passport cannot produce `verified`; clean retest links to rather than overwrites the failure; a dataset change stales dataset-dependent evidence but not unrelated policy evidence; every stale reason is visible.

### S2.3 P1 — Canonical assurance manifest and bounded exports

**Outcome:** Produce one deterministic server-side manifest and render AIUC-1 readiness and EU Annex IV support packets from it.

**Files:**

- Create: `apps/backend/src/domain/assurance/manifest.py`
- Create: `apps/backend/src/application/services/assurance_manifest_service.py`
- Create: `apps/backend/src/application/exporters/aiuc_readiness.py`
- Create: `apps/backend/src/application/exporters/eu_annex_iv.py`
- Modify: `apps/backend/src/api/routers/reports.py`
- Integrate: `apps/frontend/src/app/(dashboard)/reports/components/AssuranceReportStudio.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/reports/page.tsx`
- Create: `apps/backend/tests/test_assurance_manifest.py`
- Create: `apps/backend/tests/test_assurance_exports.py`
- Modify: `apps/frontend/src/app/(dashboard)/reports/components/AssuranceReportStudio.test.ts`

**Interfaces:**

- Consumes organization, system, immutable framework version, evidence cutoff, accepted mappings, findings, remediation, approvals, and limitations.
- Produces canonical JSON plus PDF/DOCX renderings whose content cites the manifest hash.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_assurance_manifest.py tests/test_assurance_exports.py -q
cd ../frontend
bun test 'src/app/(dashboard)/reports/components/AssuranceReportStudio.test.ts'
npm run build
```

Expected: identical pinned inputs yield the same manifest hash excluding rendering time; exports include framework source hash, full evidence hashes, subject/evaluator versions, thresholds, limitations, review decisions, unresolved findings, remediation, and approval status; missing sections are explicit; every export states that it is supporting evidence and not certification.

### S2.4 P2 — Route consolidation and claim correction

**Outcome:** Remove misleading product paths and preserve supported bookmarks through tested redirects.

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/audit-reports/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/compliance/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/compliance/dashboard/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/remediation-wizard/page.tsx`
- Modify: `apps/frontend/src/lib/constants/navigation.ts`
- Modify: `apps/frontend/src/lib/api/endpoints.ts`
- Modify: `README.md`
- Modify: `apps/website/src/` claim-bearing pages identified by exact-text scan
- Modify: `apps/docs/content/docs/` claim-bearing pages identified by exact-text scan
- Test: `apps/frontend/tests/navigation.spec.ts`

**Acceptance evidence:**

```bash
rg -n "production-ready|AIUC-1 compliant|EU AI Act compliant|certified|Not Biased|comprehensive LLM evaluation" README.md apps/frontend/src apps/website/src apps/docs/content/docs
cd apps/frontend
npx playwright test tests/navigation.spec.ts tests/governance-assurance.spec.ts --project=chromium --workers=1
npm run build
```

Expected: each match is either removed, explicitly bounded, or a prohibited-language test fixture; redirects preserve scope; Model DNA mock and fabricated modern-bias results are absent from production navigation; assurance routes remain six task-focused destinations.

### S2.5 P2 — Safe Ponytail cleanup pass

**Outcome:** Remove only candidates outside the final assurance/evaluator closure and report measured reduction.

**Files:**

- Governed by: `docs/product/PONYTAIL_AUDIT_2026-07-18.md`
- Modify: dependency manifests and lockfiles only within one ecosystem per change
- Delete: exact zero-inbound candidates captured in the live-closure manifest
- Record: `docs/product/ponytail-cleanup-ledger-2026-07.md`

**Execution order:** dependency manifests; frontend leaves; dead registry/health/middleware; fairness-library and legacy services; application/domain service batches; orphan routes; thin abstractions and settings; compatibility symlinks last.

**Acceptance evidence:**

```bash
git diff --check
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
python3 -c "import apps.backend.api.main"
cd apps/backend && uv run python -c "import api.main" && uv run pytest
cd ../frontend && npm run test && npm run build
cd ../website && npm run build
cd ../docs && npm run build
```

Expected: all gates pass or a named pre-existing baseline remains unchanged; cleanup ledger lists exact deletions and dependency changes; the claimed reduction equals measured committed deletions, not the audit estimate; no correctness, security, or performance claim is inferred from fewer lines.

### S2.6 P0 — Release evidence gate

**Outcome:** Demonstrate the complete assurance chain before calling the recovery releasable.

**End-to-end scenario:**

1. Select organization, workspace, and AI system.
2. Assign an immutable framework version.
3. Run or import one failing evaluation.
4. Verify immutable passport identity, artifact hashes, capability state, threshold, and limitations.
5. Review and accept one defensible control mapping; reject another with rationale.
6. Create a finding and remediation.
7. Ingest a clean retest linked to the failure.
8. Record approval without erasing unresolved blockers.
9. Export a pinned assurance manifest and render it twice.

**Acceptance evidence:**

```bash
cd apps/backend
uv run pytest tests/test_multi_org_e2e.py tests/test_assurance_remediation_lineage.py tests/test_assurance_manifest.py -q
cd ../frontend
npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1
npm run build
cd ../..
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
```

Expected: the complete scenario passes; two renderings cite the same canonical manifest hash; the failed predecessor remains visible; no candidate mapping is shown as accepted; no screen or export claims conformity or certification.

## Priority summary

| Priority | Sprint 1 | Sprint 2 |
| --- | --- | --- |
| P0 | Isolated integration; passport ingestion; tenant/catalog/review safety; capability truth; two real adapters | Release evidence gate |
| P1 | Six-task workbench | External adapters; remediation/retest/freshness; canonical manifest and bounded exports |
| P2 | Deferred until the assurance closure is stable | Route/claim consolidation; measured Ponytail cleanup |

## Definition of recovered

FairMind is recovered when the end-to-end gate is reproducible, organization-safe, fail-closed, and honest about capability. A green build without the evidence chain is not recovery. A polished readiness dashboard without immutable source artifacts and human review is not recovery. A technically valid passport without visible limitations and claim boundaries is not recovery.

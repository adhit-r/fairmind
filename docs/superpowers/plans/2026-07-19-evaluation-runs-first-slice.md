# Evaluation Runs First Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn FairMind's legacy model-only Test History page into the first honest, organization-scoped Evaluation Runs workbench for models, LLM applications, agents, code generators, image generators, audio models, video models, and multimodal systems, while preserving exact Evidence Passport revision linkage for governance review.

**Architecture:** Add a mutable evaluation-planning and run-control layer beside, never inside, the append-only Evidence Passport ledger. An Evaluation Plan records target kind, lifecycle phases, execution depth, enforcement posture, delivery mode, and versioned suite references. An Evaluation Run keeps technical execution status separate from a layered governance verdict and may link to exactly one tenant-bound Evidence Passport revision. This first slice does not pretend to execute unavailable workers: external or imported plans can create an `awaiting_evidence` run, while an unavailable FairMind worker returns an explicit preflight conflict. The frontend exposes that truth in the established FairMind shell.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL and SQLite migration fixtures, Pydantic, pytest, Next.js App Router, React, TypeScript, Tailwind CSS, Playwright, existing FairMind governance hooks and neobrutalist components.

## Global Constraints

- Keep the existing `GovernanceEvidenceRun` and Evidence Passport revision tables append-only. Do not add mutable plan or workflow state to them.
- Scope every plan, run, and linked passport lookup by `org_id`, `workspace_id`, and `system_id`; never trust an ID by itself.
- Keep technical execution status separate from governance judgment. A technically successful run is not automatically approved.
- Use the exact overall and layer verdict vocabulary: `approved`, `conditional`, `review`, `blocked`, `insufficient`.
- Use the exact technical run status vocabulary: `awaiting_evidence`, `running`, `succeeded`, `failed`, `cancelled`.
- Use the exact trigger vocabulary: `manual`, `ci`, `scheduled`, `release_gate`, `incident`, `integration_sync`.
- Use the exact plan status vocabulary: `draft`, `active`, `archived`.
- Support one target kind per plan from: `predictive_model`, `llm_application`, `agent`, `code_generator`, `image_generator`, `audio_model`, `video_model`, `multimodal_system`.
- Support one or more lifecycle phases per plan from: `pre_deploy`, `realtime`, `post_deploy`.
- Support execution depth `inline`, `deep`, or `hybrid`; default to `hybrid`.
- Support enforcement posture `advisory`, `human_approval`, or `automatic`; default to `human_approval`.
- Support delivery mode `fairmind_worker`, `external_provider`, or `imported_report`.
- `suite_refs_json` is a non-empty JSON array of immutable `namespace/name@version` strings. Do not silently invent or upgrade suite versions.
- The first slice does not implement modality workers, provider adapters, Redis queues, sandboxing, normalized findings, or automatic verdict derivation.
- A newly prepared run starts as `awaiting_evidence` with overall verdict `insufficient` and no fabricated layer results.
- Linking a valid exact Evidence Passport revision changes technical status to `succeeded` and overall verdict to `review`; it does not infer approval or populate unobserved layer verdicts.
- Expose only permitted observable evidence. Do not persist chain-of-thought, raw secrets, prohibited payloads, or unnecessary PII.
- Preserve the original white, Deep Ink, teal, orange, 4px-rule, hard-shadow FairMind product shell. No emoji, purple gradients, glass effects, or generic AI dashboards.
- Use shared framed line icons for actions and navigation, plus the illustrated profile identity treatment in both expanded and collapsed shells. Every icon-only target must have an accessible name, visible focus treatment, and at least a 44px hit area.
- Use TDD for every behavior change: add the focused test, run it and record RED, implement the minimum behavior, then record GREEN.
- Work only in `/private/tmp/fairmind-evaluation-workbench` on branch `codex/evaluation-workbench-slice`. Preserve the user's dirty primary worktree.

---

### Task 1: Tenant-bound Evaluation Plan and Evaluation Run schema

**Files:**

- Modify: `apps/backend/database/governance_models.py`
- Create: `apps/backend/migrations/012_evaluation_runs.sql`
- Create: `apps/backend/migrations/fixtures/012_evaluation_runs.sqlite.sql`
- Create: `apps/backend/migrations/evaluation_runs_migration.py`
- Create: `apps/backend/tests/test_evaluation_run_models.py`

**Interfaces:**

- Produces ORM models `GovernanceEvaluationPlan` and `GovernanceEvaluationRun`.
- Produces `apps.backend.migrations.evaluation_runs_migration.sql_for(dialect)` for explicit PostgreSQL and SQLite SQL selection.
- Later tasks consume the exact column names and constraints defined here.

`GovernanceEvaluationPlan` columns:

```text
id, org_id, workspace_id, system_id, name, target_kind,
lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
suite_refs_json, status, created_by, updated_by, created_at, updated_at
```

`GovernanceEvaluationRun` columns:

```text
id, org_id, workspace_id, system_id, plan_id, trigger,
technical_status, overall_verdict, layer_verdicts_json,
linked_evidence_run_id, linked_passport_revision_id,
linked_by, linked_at, requested_by, started_at, completed_at,
failure_code, failure_message,
created_at, updated_at
```

- [ ] **Step 1: Write failing ORM and migration tests**

Create focused tests that import both new classes, build their tables against fresh SQLite, and assert defaults and exact tenant linkage.

```python
def test_new_evaluation_run_is_insufficient_until_evidence_is_linked(db_session):
    run = GovernanceEvaluationRun(
        org_id="org-a",
        workspace_id="workspace-a",
        system_id="system-a",
        plan_id="plan-a",
        trigger="manual",
        requested_by="user-a",
    )
    db_session.add(run)
    db_session.flush()
    assert run.technical_status == "awaiting_evidence"
    assert run.overall_verdict == "insufficient"
    assert json.loads(run.layer_verdicts_json) == {}


def test_sqlite_migration_rejects_cross_tenant_plan_run_link(sqlite_connection):
    seed_governance_scope(sqlite_connection, org_id="org-a", workspace_id="ws-a", system_id="sys-a")
    seed_governance_scope(sqlite_connection, org_id="org-b", workspace_id="ws-b", system_id="sys-b")
    insert_evaluation_plan(sqlite_connection, id="plan-a", org_id="org-a", workspace_id="ws-a", system_id="sys-a")
    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(sqlite_connection, plan_id="plan-a", org_id="org-b", workspace_id="ws-b", system_id="sys-b")
```

Also assert:

- PostgreSQL SQL contains the same named check and composite foreign-key contracts as the ORM and direct SQLite fixture.
- SQLite SQL uses direct executable DDL rather than regex-transformed PostgreSQL.
- unsupported migration dialects raise `ValueError`.
- the plan has a tenant identity unique key `(id, workspace_id, system_id, org_id)`.
- the run has a tenant identity unique key `(id, workspace_id, system_id, org_id)`.
- the existing AI-system table gains the additive unique tenant key `(id, workspace_id, org_id)` required by the new composite references.
- the existing Evidence Passport run table gains the additive unique tenant key `(id, workspace_id, system_id, org_id)` required to reject cross-workspace links even when organization and system match.
- the exact passport revision FK covers `(linked_passport_revision_id, linked_evidence_run_id, system_id, org_id)`.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
cd apps/backend
/Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_run_models.py -q --disable-warnings
```

Expected: collection fails because the new ORM models and migration selector do not exist.

- [ ] **Step 3: Implement the minimum ORM models**

Add the two models next to the governance assurance models in the canonical runtime file. Use string UUIDs and ISO timestamp strings to match the existing governance tables.

Add these constraints:

```python
UniqueConstraint("id", "workspace_id", "org_id", name="uq_governance_ai_system_workspace_tenant")
UniqueConstraint("id", "workspace_id", "system_id", "org_id", name="uq_governance_evidence_run_workspace_tenant")
UniqueConstraint("id", "workspace_id", "system_id", "org_id", name="uq_governance_evaluation_plan_tenant")
ForeignKeyConstraint(
    ["workspace_id", "org_id"],
    ["governance_workspaces.id", "governance_workspaces.org_id"],
)
ForeignKeyConstraint(
    ["system_id", "workspace_id", "org_id"],
    ["governance_ai_systems.id", "governance_ai_systems.workspace_id", "governance_ai_systems.org_id"],
)
```

The run must additionally enforce:

```python
ForeignKeyConstraint(
    ["plan_id", "workspace_id", "system_id", "org_id"],
    [
        "governance_evaluation_plans.id",
        "governance_evaluation_plans.workspace_id",
        "governance_evaluation_plans.system_id",
        "governance_evaluation_plans.org_id",
    ],
)
ForeignKeyConstraint(
    ["linked_evidence_run_id", "workspace_id", "system_id", "org_id"],
    [
        "governance_evidence_runs.id",
        "governance_evidence_runs.workspace_id",
        "governance_evidence_runs.system_id",
        "governance_evidence_runs.org_id",
    ],
)
ForeignKeyConstraint(
    ["linked_passport_revision_id", "linked_evidence_run_id", "system_id", "org_id"],
    [
        "governance_evidence_passport_revisions.id",
        "governance_evidence_passport_revisions.evidence_run_id",
        "governance_evidence_passport_revisions.system_id",
        "governance_evidence_passport_revisions.org_id",
    ],
)
CheckConstraint(
    "(linked_passport_revision_id IS NULL AND linked_evidence_run_id IS NULL) OR "
    "(linked_passport_revision_id IS NOT NULL AND linked_evidence_run_id IS NOT NULL)",
    name="ck_governance_evaluation_run_complete_passport_link",
)
CheckConstraint(
    "(technical_status = 'succeeded' AND linked_passport_revision_id IS NOT NULL "
    "AND linked_evidence_run_id IS NOT NULL AND linked_by IS NOT NULL AND linked_at IS NOT NULL "
    "AND started_at IS NOT NULL AND completed_at IS NOT NULL) OR "
    "(technical_status <> 'succeeded' AND linked_passport_revision_id IS NULL "
    "AND linked_evidence_run_id IS NULL AND linked_by IS NULL AND linked_at IS NULL)",
    name="ck_governance_evaluation_run_succeeded_link",
)
CheckConstraint(
    "(technical_status = 'awaiting_evidence' AND started_at IS NULL AND completed_at IS NULL) OR "
    "(technical_status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL) OR "
    "(technical_status = 'succeeded' AND started_at IS NOT NULL AND completed_at IS NOT NULL) OR "
    "(technical_status IN ('failed', 'cancelled') AND completed_at IS NOT NULL)",
    name="ck_governance_evaluation_run_timestamps",
)
```

Add `CheckConstraint`s for the exact plan status, target kind, execution depth, enforcement mode, delivery mode, technical status, overall verdict, and trigger vocabularies. JSON array/member validation remains in the application service.

- [ ] **Step 4: Add direct PostgreSQL and SQLite migration 012 files**

Create only the two new tables and indexes, plus additive unique indexes on `governance_ai_systems(id, workspace_id, org_id)` and `governance_evidence_runs(id, workspace_id, system_id, org_id)` required by their composite references. Do not rewrite migration 011 or the Evidence Passport tables. PostgreSQL and SQLite files must both be idempotent at table/index level and preserve composite tenant FKs. Index `(org_id, system_id, status)` for plans and `(org_id, system_id, created_at)` plus `(org_id, technical_status, overall_verdict)` for runs.

- [ ] **Step 5: Run Task 1 tests and verify GREEN**

Run the Task 1 command. Expected: all Task 1 tests pass.

- [ ] **Step 6: Run schema regressions and boundary checks**

```bash
cd apps/backend
/Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_governance_assurance_models.py tests/test_evaluation_run_models.py -q --disable-warnings
cd ../..
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
```

- [ ] **Step 7: Commit**

```bash
git add apps/backend/database/governance_models.py apps/backend/migrations/012_evaluation_runs.sql apps/backend/migrations/fixtures/012_evaluation_runs.sqlite.sql apps/backend/migrations/evaluation_runs_migration.py apps/backend/tests/test_evaluation_run_models.py
git commit -m "feat(evaluations): add tenant-bound plan and run schema"
```

### Task 2: Evaluation planning, preflight, run, and Passport-link API

**Files:**

- Create: `apps/backend/src/application/services/evaluation_runs_service.py`
- Modify: `apps/backend/api/routes/governance_assurance.py`
- Create: `apps/backend/tests/test_evaluation_runs.py`

**Interfaces:**

- Produces pure validation helpers and `EvaluationRunsService`.
- Extends the existing `/api/v1/ai-governance/organizations/{org_id}` router.
- Reuses `organization_membership`, `_require_mutation`, and the existing evidence ingestion records.

Endpoints:

```text
POST /systems/{system_id}/evaluation-plans
GET  /systems/{system_id}/evaluation-plans
POST /systems/{system_id}/evaluation-plans/{plan_id}/activate
GET  /systems/{system_id}/evaluation-plans/{plan_id}/preflight
POST /systems/{system_id}/evaluation-plans/{plan_id}/runs
GET  /systems/{system_id}/evaluation-runs
GET  /systems/{system_id}/evaluation-runs/{run_id}
POST /systems/{system_id}/evaluation-runs/{run_id}/evidence-passport-link
```

- [ ] **Step 1: Write failing service and route tests**

Cover these behaviors through the FastAPI test client:

1. member reads are org-scoped; non-members receive the repository's established 403/404 behavior.
2. mutation requires the same organization role used by the existing assurance endpoints.
3. plan creation validates a 1–120 character name; target kind; one-to-three distinct lifecycle phases; execution depth; enforcement mode; delivery mode; and one-to-32 distinct immutable suite refs.
4. each suite ref is at most 160 characters and must match `^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*@[A-Za-z0-9][A-Za-z0-9._-]*$`.
5. plan creation rejects system/workspace/org scope mismatches.
6. activation changes only the selected plan; draft→active succeeds, active replay is idempotent, archived→active returns `409`, the transition and its organization audit event commit atomically, and multiple active plans for different modalities/versioned suites may coexist on one system.
7. preflight for `fairmind_worker` returns `canPrepareRun=false`, `fairmindExecutionAvailable=false`, `code=executor_unavailable`, and a human-readable next action in this slice.
8. preflight for `external_provider` and `imported_report` returns `canPrepareRun=true`, `fairmindExecutionAvailable=false`, `code=evidence_link_required`; it never calls those plans execution-ready.
9. run creation for an unavailable `fairmind_worker` plan returns `409` and does not create a run.
10. run creation for an active external/imported plan returns `201`, `technicalStatus=awaiting_evidence`, `overallVerdict=insufficient`, and `layerVerdicts={}`.
11. listing and detail retrieval never leak cross-org records.
12. linking an exact Passport revision rejects a mismatched org, workspace, system, evidence run, revision, suite identity/version, or verifiably incompatible target kind.
13. a suite is compatible only when the Passport's exact canonical `evaluation.suite.name@evaluation.suite.version` equals one of the plan's immutable `suite_refs`; no fuzzy or display-name matching is allowed.
14. Evidence Passport 1.0 can verify only `predictive_model` via `aiSystem.kind=model` and `agent` via `aiSystem.kind=agent`. For `llm_application`, `code_generator`, `image_generator`, `audio_model`, `video_model`, and `multimodal_system`, linking returns `422 target_kind_unverifiable` until a versioned Passport contract can bind that modality explicitly; the plan and `awaiting_evidence` run remain usable and insufficient.
15. linking succeeds idempotently for the same exact revision, records `linked_by` and `linked_at`, copies the Passport evaluation's `startedAt` and `endedAt` to run timestamps, sets technical status to `succeeded`, sets overall verdict to `review`, writes an organization audit event in the same transaction, and never changes the immutable Passport row.
16. linking a different revision after a link returns `409`; replacement is a later, audited workflow.
17. two concurrent link attempts use an atomic compare-and-set from unlinked `awaiting_evidence` to linked `succeeded`; only one distinct revision may win, while replaying the winner is idempotent.
18. plan creation and external/imported run preparation write minimal organization audit events in the same transaction; an injected audit failure rolls back the domain row rather than returning partial success.

- [ ] **Step 2: Run Task 2 tests and verify RED**

```bash
cd apps/backend
/Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_runs.py -q --disable-warnings
```

Expected: endpoint requests return 404 or import fails because the service is absent.

- [ ] **Step 3: Implement validation and service methods**

Use typed dataclasses or Pydantic request models at the API boundary. Store canonical JSON with deterministic separators and sorted keys. Service-internal rows use snake_case; every public request and success response uses one exact camelCase Pydantic contract. Do not rely on the frontend to guess whether a new endpoint returned snake_case or camelCase.

Required service surface:

```python
class EvaluationRunsService:
    def create_plan(self, *, org_id: str, system_id: str, actor_id: str, payload: dict) -> dict: ...
    def list_plans(self, *, org_id: str, system_id: str) -> list[dict] | None: ...
    def activate_plan(self, *, org_id: str, system_id: str, plan_id: str, actor_id: str) -> dict | None: ...
    def preflight(self, *, org_id: str, system_id: str, plan_id: str) -> dict | None: ...
    def create_run(self, *, org_id: str, system_id: str, plan_id: str, actor_id: str, trigger: str) -> dict: ...
    def list_runs(self, *, org_id: str, system_id: str) -> list[dict] | None: ...
    def get_run(self, *, org_id: str, system_id: str, run_id: str) -> dict | None: ...
    def link_passport_revision(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
        evidence_run_id: str,
        passport_revision_id: str,
        actor_id: str,
    ) -> dict | None: ...
```

Every opaque plan/run lookup must join or filter through the selected system and its workspace as well as `org_id`. Transactions must either commit the complete state change, including its audit row, or roll back. Do not catch broad exceptions and return success. Implement Passport linking with a conditional update whose predicate requires `technical_status='awaiting_evidence'` and both link columns null; inspect `rowcount`, then distinguish same-link replay from a conflicting winner.

For list methods, return `[]` only when the scoped system exists but has no records; return `None` so the router emits `404` when the `(org_id, system_id)` scope itself does not exist.

- [ ] **Step 4: Add the organization-scoped API routes**

Use explicit request and response models. Return:

- `201` for new plan/run records.
- `200` for list/detail, activation, preflight, and idempotent same-revision link.
- `404` for tenant-scoped missing plan/run/system.
- `409` for unavailable execution, inactive plan run requests, and conflicting Passport relinks.
- `422` for malformed vocabulary, suite refs, duplicate lifecycle phases, or invalid exact Passport scope.

All non-validation evaluation workflow errors use this exact FastAPI-standard nested envelope:

```json
{
  "detail": {
    "code": "executor_unavailable",
    "message": "No FairMind worker is installed for this plan.",
    "nextAction": "Select an external provider or imported report, or install a compatible worker."
  }
}
```

The API client must preserve HTTP status plus nested `code`, `message`, and `nextAction`. Plain-string legacy `detail` responses remain backward compatible.

Stable workflow codes for this slice are: `executor_unavailable`, `plan_inactive`, `plan_archived`, `passport_link_conflict`, `passport_scope_mismatch`, `suite_mismatch`, `target_kind_mismatch`, `target_kind_unverifiable`, `passport_snapshot_invalid`, and `evaluation_persistence_failed`.

Do not create an alias under legacy model-only bias routes.

- [ ] **Step 5: Run Task 2 tests and verify GREEN**

Run the Task 2 command. Expected: all tests pass.

- [ ] **Step 6: Run backend assurance regression suite**

```bash
cd apps/backend
/Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_run_models.py tests/test_evaluation_runs.py tests/test_governance_assurance_models.py tests/test_governance_assurance_routes.py -q --disable-warnings
```

- [ ] **Step 7: Commit**

```bash
git add apps/backend/src/application/services/evaluation_runs_service.py apps/backend/api/routes/governance_assurance.py apps/backend/tests/test_evaluation_runs.py
git commit -m "feat(evaluations): expose evidence-backed run workflow"
```

### Task 3: Typed frontend Evaluation Runs client

**Files:**

- Modify: `apps/frontend/src/lib/api/endpoints.ts`
- Modify: `apps/frontend/src/lib/api/api-client.ts`
- Create: `apps/frontend/src/lib/api/hooks/useEvaluationRuns.ts`
- Create: `apps/frontend/src/lib/api/hooks/useEvaluationRuns.test.ts`
- Modify: `apps/frontend/src/lib/api/hooks/index.ts`

**Interfaces:**

- Produces typed `EvaluationPlan`, `EvaluationPreflight`, `EvaluationRun`, `EvaluationTargetKind`, `LifecyclePhase`, `DeliveryMode`, `TechnicalStatus`, and `GovernanceVerdict` contracts.
- Produces endpoint builders matching Task 2.
- Produces a focused hook that loads plans and runs for the selected `(orgId, systemId)` and exposes mutation methods without optimistic green states.
- Produces a backward-compatible structured `ApiError` path preserving HTTP status, stable API `code`, `detail`, and `nextAction` for callers that need actionable preflight failures.
- Produces a dependency-free evaluation client controller used directly by the React hook, giving Bun unit tests a real stale-response seam without adding a DOM or hook-renderer package.

- [ ] **Step 1: Write failing hook tests**

Mock the existing API client and assert:

- no request is issued until both `orgId` and `systemId` exist.
- plan and run requests use organization and system IDs in their URLs.
- changing either scope invalidates generation tokens so stale list or detail responses cannot replace the current scope.
- loading, empty, and server-error states remain distinguishable.
- `createPlan`, `activatePlan`, `loadPreflight`, `createRun`, and `linkPassportRevision` call the exact Task 2 endpoints and refresh only after success.
- a `409 executor_unavailable` remains an actionable error and never inserts a fake run.
- run detail requests remain scoped to both organization and selected system and ignore stale responses after scope/run changes.
- unknown backend vocabularies are rejected by runtime schemas rather than being trusted because a TypeScript union compiled.
- nested structured and legacy string FastAPI errors both preserve a string `error`; structured workflow failures additionally preserve `status`, `code`, `detail`, and `nextAction` on `apiError`.

- [ ] **Step 2: Run hook tests and verify RED**

```bash
cd apps/frontend
bun test src/lib/api/hooks/useEvaluationRuns.test.ts
```

Expected: import failure because the hook is absent.

- [ ] **Step 3: Add endpoint builders and exact TypeScript unions**

Keep transport types separate from display labels. The exact unions must match backend vocabularies. Use strict Zod runtime schemas for raw camelCase plans, preflight, runs, lists, and structured errors. Do not call `normalizeGovernanceResponse` before validation because that would hide a snake_case regression in Task 2's exact public contract. With Zod 4, use `z.partialRecord` for partial verdict maps; `z.record` with an enum key would incorrectly require every key.

Keep the two verdict axes separate rather than conflating system components with risk dimensions:

```typescript
type EvaluationComponent =
  | 'model'
  | 'prompts_rag'
  | 'output'
  | 'tools'
  | 'trajectory'
  | 'application_controls'
  | 'deployment_context'

type EvaluationRiskDimension =
  | 'safety'
  | 'security'
  | 'fairness'
  | 'privacy'
  | 'reliability'
  | 'governance'

interface EvaluationLayerVerdicts {
  components?: Partial<Record<EvaluationComponent, GovernanceVerdict>>
  dimensions?: Partial<Record<EvaluationRiskDimension, GovernanceVerdict>>
}
```

The server may return both maps absent when linked evidence has not been normalized.

- [ ] **Step 4: Implement the minimum scoped hook**

Follow existing API client token and base URL conventions, but parse Task 2 responses before any case normalization. Extend `ApiResponse<T>` backward-compatibly with optional `apiError`; keep `error` a string for existing callers. Decode the exact nested FastAPI workflow envelope and plain-string legacy details. Tighten the browser-offline test to `navigator.onLine === false` so Bun's undefined `onLine` is not treated as offline.

Implement a small generation-token controller inside the same module and have the hook subscribe/delegate to it. Missing scope clears to empty non-loading state. Valid scope loads plan and run lists together. Mutations refresh only the affected successful list: plan creation/activation refresh plans; run creation/Passport linking refresh runs; preflight/detail do not refresh. A superseded `getRun` rejects with a named stale-result error so the detail page can suppress it.

Expose:

```typescript
useEvaluationRuns(orgId?: string, systemId?: string): {
  plans: EvaluationPlan[]
  runs: EvaluationRun[]
  loading: boolean
  error: Error | null
  refresh(): Promise<void>
  createPlan(input: CreateEvaluationPlanInput): Promise<EvaluationPlan>
  activatePlan(planId: string): Promise<EvaluationPlan>
  loadPreflight(planId: string): Promise<EvaluationPreflight>
  createRun(planId: string, trigger?: EvaluationTrigger): Promise<EvaluationRun>
  getRun(runId: string): Promise<EvaluationRun>
  linkPassportRevision(runId: string, input: PassportRevisionLinkInput): Promise<EvaluationRun>
}
```

- [ ] **Step 5: Run Task 3 tests and frontend type checks**

```bash
cd apps/frontend
bun test src/lib/api/hooks/useEvaluationRuns.test.ts
bunx tsc --noEmit --incremental false
```

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/src/lib/api/endpoints.ts apps/frontend/src/lib/api/api-client.ts apps/frontend/src/lib/api/hooks/useEvaluationRuns.ts apps/frontend/src/lib/api/hooks/useEvaluationRuns.test.ts apps/frontend/src/lib/api/hooks/index.ts
git commit -m "feat(evaluations): add typed evaluation runs client"
```

### Task 4: Original-shell Evaluation Runs workspace and icon language

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/tests/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/tests/[testId]/page.tsx`
- Modify: `apps/frontend/src/components/layout/ClientNavigation.tsx`
- Modify: `apps/frontend/src/components/layout/Header.tsx`
- Modify: `apps/frontend/src/components/layout/Sidebar.tsx`
- Modify: `apps/frontend/src/components/workflow/SystemContext.tsx`
- Modify: `apps/frontend/src/lib/constants/navigation.ts`
- Create: `apps/frontend/src/components/ui/FramedIcon.tsx`
- Create: `apps/frontend/src/components/ui/FramedIdentity.tsx`
- Create: `apps/frontend/tests/evaluation-runs.spec.ts`
- Modify: `DESIGN.md`

**Interfaces:**

- `/tests` becomes “Evaluation Runs” but stays inside the established dashboard shell.
- Reuses `useOrg`, `useSystemContext`, the layout-owned `SystemContextBar`, and Task 3's hook.
- Adds no new top-level navigation taxonomy; “Evaluation Runs” sits under the existing Assess category.
- Shared `FramedIcon` and `FramedIdentity` establish the requested icon and illustrated profile treatment across expanded and collapsed shell controls.

- [ ] **Step 1: Write failing Playwright acceptance tests**

Mock the Task 2 API responses. Cover desktop and a narrow mobile viewport.

Required assertions:

1. `/tests` renders Header, Sidebar, organization/system context, and page title “Evaluation Runs”.
2. The route is not treated as auth/shell-less; only `/test` and `/test/...` keep any legacy exception, not `/tests`.
3. the illustrated profile identity remains visible in the desktop header and collapsed/mobile shell with a labelled fallback when the image fails.
4. navigation/action icons are framed, have accessible names, 44px hit areas, visible keyboard focus, and text labels when expanded.
5. no real selected system shows an explicit “Choose an AI system” state and makes no evaluation request. Any system with `metadata.source === 'fallback'` must be treated as missing rather than queried or presented as real. The layout-owned `SystemContextBar` must return `null` for that fallback, and the rendered shell must not contain “Acme Pricing Lab”.
6. no plan shows a compact create-plan form with target kind, lifecycle phase multi-select, execution depth, enforcement mode, delivery mode, and versioned suite refs.
7. a FairMind-worker plan displays “Executor unavailable”, `canPrepareRun=false`, and disables run creation.
8. an external/imported plan displays “Evidence link required”, `canPrepareRun=true`, `fairmindExecutionAvailable=false`, and can prepare an `awaiting_evidence` run without claiming the evaluation is ready.
9. the recent-runs table shows technical status and overall verdict in separate columns; `insufficient` and `review` are never styled or labelled as passed/approved.
10. component-layer and risk-dimension verdicts are distinct, shown only when supplied, and absent axes read “Not assessed”.
11. loading, empty, server-error, and action-error states are distinct and keyboard reachable.
12. run detail links use `/tests/{runId}`, not `/dashboard/tests/{runId}`.
13. the detail page no longer renders stray import/comment source text inside JSX.
14. no emoji, purple gradient, generic AI hero, or fabricated metrics appear.

- [ ] **Step 2: Run the focused E2E test and verify RED**

```bash
cd apps/frontend
bun run test tests/evaluation-runs.spec.ts --project=chromium
```

If the Playwright config starts Bun, confirm Bun exists before changing configuration. Expected: assertions fail because `/tests` is the legacy Test History page and the route is currently shell-less.

- [ ] **Step 3: Fix routing and navigation first**

Replace the broad `pathname.startsWith("/test")` shell exception with a segment-exact check that excludes `/tests`. Correct every legacy `/dashboard/tests/...` link. Add exactly one “Evaluation Runs” child under the existing Assess category; do not rename Assess or add a competing Test History item. In collapsed navigation, reduce container padding so 44px framed controls and the identity are not clipped.

- [ ] **Step 4: Add the shared framed icon and identity components**

`FramedIcon` owns square border, hard offset shadow, high-contrast icon color, hover/pressed states, focus ring, and size variants. It accepts an actual icon component plus an accessible label; icon-only usage requires `aria-label`.

`FramedIdentity` owns the illustrated portrait, border, hard shadow, fallback initials, status/name text, and collapsed variant. Preserve the illustrated portrait character the user approved. If the current remote portrait remains the only available approved source in this slice, keep it as a centralized fallback in this component and document local asset replacement as a follow-up; do not scatter the URL.

Use the shared components in Header and Sidebar wherever they replace existing one-off profile/action icon wrappers. Do not force decorative frames around every inline status glyph.

The shared `SystemContextBar` must not render the repository's synthetic fallback system. Keep the bar layout-owned for real systems; do not duplicate it inside the page. Replace its raised gradient wrapper with the established flat canvas/border treatment while preserving its organization/system controls.

- [ ] **Step 5: Build the dense Evaluation Runs workspace**

The desktop hierarchy is:

```text
Page title and concise assurance purpose
Selected organization/system context
Plan strip or compact create-plan form
Preflight status and one primary action
Recent runs table
```

Use one flat bordered work surface, not a wall of cards. Preserve teal for active/operational states, orange for attention/action, red for blocked/error, and ink/canvas neutrals for insufficient/unassessed. Keep all controls square and task-focused.

The create form serializes one or more selected lifecycle phases and newline-separated suite refs. Validate locally for immediate feedback but treat server validation as authoritative.

For unavailable execution, show the exact blocker and next action. Never make a disabled button the sole explanation.

- [ ] **Step 6: Make the detail route truthful**

Load Task 3 run detail or use a detail-capable hook method without falling back to legacy bias-test data. Present technical state, overall verdict, layer verdicts, plan metadata, and exact linked Passport revision identifiers. If no Passport is linked, say “Awaiting evidence”; do not show synthetic artifacts.

- [ ] **Step 7: Update `DESIGN.md`**

Add sections for:

- framed functional icon anatomy and when not to use it.
- illustrated identity/avatar anatomy, expanded/collapsed behavior, and image fallback.
- evaluation-state semantics separating technical status from governance verdict.
- dense Evaluation Runs table and preflight patterns.
- accessibility rules: WCAG 2.2 AA contrast, 44px targets, labelled icon-only controls, keyboard focus, reduced-motion behavior.

Keep all existing FairMind visual foundations and explicitly prohibit purple gradients and generic AI styling.

- [ ] **Step 8: Run E2E, unit, type, and production build checks**

```bash
cd apps/frontend
bun run test tests/evaluation-runs.spec.ts --project=chromium
bunx tsc --noEmit
bun run build
```

The production build may require network access for the existing Google Raleway import. Existing Authentik and viewport warnings are baseline warnings unless this task changes their source.

- [ ] **Step 9: Commit**

```bash
git add DESIGN.md apps/frontend/src/app/'(dashboard)'/tests/page.tsx apps/frontend/src/app/'(dashboard)'/tests/'[testId]'/page.tsx apps/frontend/src/components/layout/ClientNavigation.tsx apps/frontend/src/components/layout/Header.tsx apps/frontend/src/components/layout/Sidebar.tsx apps/frontend/src/components/workflow/SystemContext.tsx apps/frontend/src/lib/constants/navigation.ts apps/frontend/src/components/ui/FramedIcon.tsx apps/frontend/src/components/ui/FramedIdentity.tsx apps/frontend/tests/evaluation-runs.spec.ts
git commit -m "feat(evaluations): launch evidence-backed runs workspace"
```

### Task 5: Integrated assurance validation and honest handoff

**Files:**

- Modify only if a test exposes a defect: files already listed in Tasks 1–4
- Create: `.superpowers/sdd/evaluation-workbench-validation.md` (working ledger, do not commit if ignored)

- [ ] **Step 1: Run the complete focused backend slice**

```bash
cd apps/backend
/Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_run_models.py tests/test_evaluation_runs.py tests/test_governance_assurance_models.py tests/test_governance_assurance_routes.py tests/test_evidence_ingestion_service.py -q --disable-warnings
```

- [ ] **Step 2: Apply migration 012 against fresh SQLite and PostgreSQL fixtures**

Use the repository's migration-test harness and the existing local PostgreSQL test instance if available. Prove:

- both tables create cleanly.
- a valid tenant-bound plan/run/passport link succeeds.
- cross-org, cross-system, and mismatched revision links fail.
- migration 011 Evidence Passport immutability triggers still reject mutation.

- [ ] **Step 3: Run the focused frontend slice at desktop and mobile widths**

```bash
cd apps/frontend
bun run test tests/evaluation-runs.spec.ts --project=chromium
bunx tsc --noEmit
bun run build
```

Capture at least one desktop and one mobile screenshot in Playwright test output or `/tmp`; do not commit generated screenshots unless the repository already tracks that artifact class.

- [ ] **Step 4: Run repository architecture guards**

```bash
cd ../..
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
git status --short
```

- [ ] **Step 5: Run final independent code review**

Use `superpowers:requesting-code-review` against the implementation base `690e587` and current HEAD. Resolve every Critical and Important issue, rerun affected tests, and request review again until clean.

- [ ] **Step 6: Run Ponytail whole-repo audit in report-only mode**

Use `ponytail:ponytail-audit` only after evaluator behavior, migrations, and UI validation are green. Report organization debt and safe consolidation candidates. Do not delete or relocate code before a parity proof and explicit follow-up scope.

- [ ] **Step 7: Verify before claiming completion**

Use `superpowers:verification-before-completion`. Record exact commands, pass counts, known baseline warnings, deferred worker/adaptor scope, and any unavailable PostgreSQL or browser dependency. Do not describe the workbench as executing modalities until a real worker is installed and tested.

- [ ] **Step 8: Finish the branch**

Use `superpowers:finishing-a-development-branch` and present the user with the verified branch/commit state. Do not merge into the dirty primary worktree without explicit direction.

# AI Governance Assurance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a company-scoped, versioned framework and evidence-assurance vertical slice to FairMind's existing AI Governance module, with AIUC-1 April 2026 as the first imported framework.

**Architecture:** Extend the existing Organization, AI System, Evidence, Risk, Remediation, Approval, and Report spine. Add immutable framework catalog records, system-scoped control assessments, provenance-rich evidence runs, and reviewed control-evidence mappings behind an org-scoped router. Reuse existing frontend routes and consolidate navigation around six governance tasks.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite/PostgreSQL, Pydantic, openpyxl, pytest, Next.js App Router, React, TypeScript, Tailwind CSS, existing FairMind UI components.

## Global Constraints

- AI Governance remains an existing FairMind module, not a standalone portal.
- Organization is the company tenant; every new tenant-owned lookup is scoped by `org_id` and authenticated membership.
- AI systems are typed as model, agent, or composite application.
- AIUC-1 is a versioned framework pack, not an AIUC-specific subsystem.
- Automation may create evidence and candidate mappings; reviewers decide mapping and control state.
- Raw model weights, unrestricted prompts, and private reasoning traces do not leave the company environment by default.
- Product language is limited to readiness, mapped evidence, supporting evidence, and review state. It must not imply certification or automatic compliance.
- Preserve the teal, orange, Deep Ink, Warm Canvas, square-cornered professional neobrutalist design. No emoji, purple gradients, glassmorphism, or marketing heroes.
- Use TDD for every behavior change. Preserve the pre-existing `api.models` test-collection failure as a recorded baseline unless a task directly touches that import path.

---

### Task 1: Governance assurance schema

**Files:**

- Modify: `apps/backend/src/infrastructure/db/database/governance_models.py`
- Create: `apps/backend/migrations/009_governance_assurance.sql`
- Test: `apps/backend/tests/test_governance_assurance_models.py`

**Interfaces:**

- Produces ORM models `GovernanceFrameworkVersion`, `GovernanceControlDefinition`, `GovernanceFrameworkAssignment`, `GovernanceControlAssessment`, `GovernanceEvidenceRun`, and `GovernanceControlEvidence`.
- Adds nullable `org_id` to `GovernanceWorkspace` for safe legacy migration, with new records requiring an organization at the API boundary.
- Later tasks consume the exact class and column names defined here.

- [ ] **Step 1: Write failing schema tests**

Create tests that build a fresh SQLite schema and assert:

```python
def test_framework_definition_state_is_separate_from_system_assessment(db_session):
    version = GovernanceFrameworkVersion(
        id="fv-1", framework_key="aiuc-1", name="AIUC-1",
        version_label="April, 2026", source_hash="abc", status="active",
    )
    definition = GovernanceControlDefinition(
        id="cd-1", framework_version_id="fv-1", external_id="A001.1",
        title="Input data policy", statement="Maintain an input data policy.",
        active=True,
    )
    assessment = GovernanceControlAssessment(
        id="ca-1", org_id="org-1", system_id="sys-1",
        framework_assignment_id="fa-1", control_definition_id="cd-1",
        applicability="applicable", status="not_started", owner="owner@example.com",
    )
    assert not hasattr(definition, "owner")
    assert assessment.owner == "owner@example.com"


def test_control_evidence_mapping_has_review_state(db_session):
    mapping = GovernanceControlEvidence(
        id="map-1", org_id="org-1", evidence_id="ev-1",
        control_assessment_id="ca-1", state="candidate",
        mapping_rationale="Evaluation tag matches control evidence kind.",
    )
    assert mapping.state == "candidate"
```

- [ ] **Step 2: Run the schema tests and verify RED**

Run:

```bash
cd apps/backend
uv run pytest tests/test_governance_assurance_models.py -q
```

Expected: collection fails because the six ORM models do not exist.

- [ ] **Step 3: Implement the minimum ORM and migration schema**

Use string UUID primary keys and ISO timestamps to match current governance tables. Enforce these uniqueness constraints:

```python
UniqueConstraint("framework_key", "version_label", "source_hash", name="uq_governance_framework_version")
UniqueConstraint("framework_version_id", "external_id", name="uq_governance_control_definition")
UniqueConstraint("org_id", "system_id", "framework_version_id", name="uq_governance_framework_assignment")
UniqueConstraint("framework_assignment_id", "control_definition_id", name="uq_governance_control_assessment")
UniqueConstraint("org_id", "source_type", "source_identifier", "run_id", "content_hash", name="uq_governance_evidence_run")
UniqueConstraint("evidence_id", "control_assessment_id", name="uq_governance_control_evidence")
```

The migration creates the six tables, indexes tenant columns, and adds `org_id` to `governance_workspaces`. Do not remove or rewrite existing tables in this migration.

- [ ] **Step 4: Run schema tests and verify GREEN**

Run the Task 1 test command. Expected: all Task 1 tests pass.

- [ ] **Step 5: Run migration and boundary checks**

```bash
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
```

- [ ] **Step 6: Commit**

```bash
git add apps/backend/src/infrastructure/db/database/governance_models.py apps/backend/migrations/009_governance_assurance.sql apps/backend/tests/test_governance_assurance_models.py
git commit -m "feat(governance): add assurance data model"
```

### Task 2: Framework-neutral AIUC workbook importer

**Files:**

- Modify: `apps/backend/pyproject.toml`
- Modify: `apps/backend/uv.lock`
- Create: `apps/backend/src/application/services/framework_catalog_service.py`
- Create: `apps/backend/tests/test_framework_catalog_service.py`

**Interfaces:**

- Produces `FrameworkCatalogService.import_workbook(path: Path, actor_id: str) -> FrameworkImportResult`.
- Produces pure parser `parse_aiuc_workbook(path: Path) -> ParsedFrameworkCatalog` for direct unit testing.
- Returns `FrameworkImportResult(version_id, framework_key, version_label, requirement_count, control_count, source_hash, created)`.

- [ ] **Step 1: Add the existing-standard XLSX dependency**

Add `openpyxl>=3.1.5` to backend dependencies and run `uv lock`. Do not introduce a custom XLSX parser.

- [ ] **Step 2: Write failing parser tests using a synthetic workbook**

Build the workbook in the test with `openpyxl.Workbook`. Include the exact three sheet names and two control rows. Assert normalized fields, hashes, and retirement preservation.

```python
catalog = parse_aiuc_workbook(workbook_path)
assert catalog.framework_key == "aiuc-1"
assert catalog.version_label == "April, 2026"
assert catalog.requirement_count == 2
assert catalog.control_count == 2
assert catalog.controls[0].external_id == "A001.1"
assert catalog.controls[1].active is False
```

Add negative tests for duplicate leaf IDs, missing parent requirements, wrong sheet names, and atomic count validation.

- [ ] **Step 3: Run importer tests and verify RED**

```bash
cd apps/backend
uv run pytest tests/test_framework_catalog_service.py -q
```

Expected: import failure because the service does not exist.

- [ ] **Step 4: Implement parsing and persistence**

Use dataclasses or Pydantic models for parsed records. Preserve source strings and add normalized arrays without discarding originals. Compute SHA-256 over workbook bytes. The AIUC adapter validates the supplied production workbook against 51 requirements and 135 leaf controls when `strict=True`; synthetic tests use `strict=False` with explicit expected counts.

Persist the framework version and controls in one transaction. A repeat import with the same `(framework_key, version_label, source_hash)` returns the existing version and `created=False`.

- [ ] **Step 5: Verify the supplied workbook without committing it**

```bash
cd apps/backend
uv run python -m src.application.services.framework_catalog_service "/Users/adhi/Downloads/AIUC-1 _ April, 2026 version.xlsx" --check
```

Expected output includes `version=April, 2026 requirements=51 controls=135` and the workbook SHA-256.

- [ ] **Step 6: Run tests and commit**

```bash
uv run pytest tests/test_framework_catalog_service.py -q
git add pyproject.toml uv.lock src/application/services/framework_catalog_service.py tests/test_framework_catalog_service.py
git commit -m "feat(governance): import versioned framework catalogs"
```

### Task 3: Organization-scoped framework and control API

**Files:**

- Create: `apps/backend/src/application/services/governance_assurance_service.py`
- Create: `apps/backend/api/routes/governance_assurance.py`
- Modify: `apps/backend/api/main.py`
- Test: `apps/backend/tests/test_governance_assurance_routes.py`

**Interfaces:**

- Produces router mounted under `/api/v1/ai-governance/organizations/{org_id}`.
- Uses `get_current_active_user`, `get_db`, and an org-membership dependency.
- Produces catalog list, import, assignment, control list, and assessment update routes.

- [ ] **Step 1: Write failing authorization and route tests**

Override `get_current_active_user` with a deterministic test user. Seed two organizations and memberships. Assert:

```python
assert client.get(f"/api/v1/ai-governance/organizations/{org_a}/frameworks").status_code == 200
assert client.get(f"/api/v1/ai-governance/organizations/{org_b}/frameworks").status_code in {403, 404}
```

Cover framework import permission, system ownership, assignment idempotency, control-assessment creation, and cross-org access by assignment or assessment ID.

- [ ] **Step 2: Run route tests and verify RED**

```bash
cd apps/backend
uv run pytest tests/test_governance_assurance_routes.py -q
```

Expected: 404 because the router is not mounted.

- [ ] **Step 3: Implement membership and service boundaries**

The router accepts `org_id` in the path but authorization never trusts the path alone. The dependency queries active `org_members` for `(org_id, current_user.user_id)`. Import requires owner/admin. Read operations require membership. Mutation requires owner/admin or a named permission already supported by the organization role model.

Implement:

```text
GET    /frameworks
POST   /frameworks/import
GET    /frameworks/{framework_key}/versions
GET    /framework-versions/{version_id}/controls
POST   /systems/{system_id}/framework-assignments
GET    /systems/{system_id}/framework-assignments
GET    /framework-assignments/{assignment_id}/controls
PATCH  /control-assessments/{assessment_id}
GET    /framework-assignments/{assignment_id}/readiness
```

Assignment creates one assessment per active control definition in a single transaction.

- [ ] **Step 4: Implement transparent readiness**

Return counts, never an unexplained score:

```json
{
  "applicable": 41,
  "accepted": 12,
  "readyForReview": 4,
  "partial": 8,
  "notStarted": 17,
  "notApplicable": 10,
  "blockingFindings": 3,
  "missingEvidence": 21,
  "staleEvidence": 2
}
```

- [ ] **Step 5: Verify GREEN and commit**

```bash
uv run pytest tests/test_governance_assurance_routes.py -q
git add src/application/services/governance_assurance_service.py api/routes/governance_assurance.py api/main.py tests/test_governance_assurance_routes.py
git commit -m "feat(governance): add org-scoped framework workflow"
```

### Task 4: Evidence runs and reviewed control mappings

**Files:**

- Modify: `apps/backend/src/application/services/governance_assurance_service.py`
- Modify: `apps/backend/api/routes/governance_assurance.py`
- Create: `apps/backend/tests/test_governance_evidence_runs.py`

**Interfaces:**

- Produces `EvidenceRunEnvelope` request schema.
- Produces idempotent evidence-run ingestion and mapping-review endpoints.
- Reuses `GovernanceEvidence` as the artifact record and links it to `GovernanceEvidenceRun`.

- [ ] **Step 1: Write failing evidence integrity tests**

Cover canonical JSON hashing, idempotent repeated ingestion, preserved failed runs, candidate mapping creation, accept/reject review history, cross-org denial, stale evidence, and rejection of caller-supplied third-party status without assessor metadata.

```python
first = service.ingest_evidence_run(org_id, system_id, envelope, actor_id)
second = service.ingest_evidence_run(org_id, system_id, envelope, actor_id)
assert first.run_id == second.run_id
assert first.content_hash == second.content_hash
```

- [ ] **Step 2: Run tests and verify RED**

```bash
cd apps/backend
uv run pytest tests/test_governance_evidence_runs.py -q
```

- [ ] **Step 3: Implement the minimum ingestion pipeline**

Canonicalize with sorted JSON keys and compact separators, hash with SHA-256, and preserve artifact references rather than copying large raw outputs. Create one GovernanceEvidence item per run summary. Candidate mappings are created only from an explicit `control_external_ids` list or declared evaluation tags configured by the service; no semantic inference engine is introduced.

Implement:

```text
POST /systems/{system_id}/evidence-runs
GET  /systems/{system_id}/evidence-runs
POST /evidence/{evidence_id}/control-mappings
POST /evidence-mappings/{mapping_id}/review
```

Mapping review records actor and time from authentication. Accepted evidence does not automatically set a control assessment to accepted.

- [ ] **Step 4: Verify GREEN and commit**

```bash
uv run pytest tests/test_governance_evidence_runs.py -q
git add src/application/services/governance_assurance_service.py api/routes/governance_assurance.py tests/test_governance_evidence_runs.py
git commit -m "feat(governance): ingest and review evaluation evidence"
```

### Task 5: Frontend API contract and consolidated governance navigation

**Files:**

- Modify: `apps/frontend/src/lib/api/endpoints.ts`
- Create: `apps/frontend/src/lib/api/hooks/useGovernanceAssurance.ts`
- Modify: `apps/frontend/src/lib/constants/navigation.ts`
- Modify: `apps/frontend/src/components/layout/Sidebar.tsx`
- Test: `apps/frontend/src/lib/api/hooks/useGovernanceAssurance.test.ts`

**Interfaces:**

- Produces typed `FrameworkVersion`, `FrameworkAssignment`, `ControlAssessment`, `ReadinessSummary`, `EvidenceRun`, and `EvidenceMapping` interfaces.
- Produces hooks for catalog, assignment controls, evidence runs, and mapping review.
- Navigation continues to use existing routes.

- [ ] **Step 1: Write failing API normalization tests**

Test snake_case and camelCase normalization, empty/error states, and org/system URL construction. Avoid network mocks beyond a minimal `apiClient` stub.

- [ ] **Step 2: Run tests and verify RED**

Use the frontend's installed test runner if configured. If there is no unit runner, add one small Node-executable TypeScript normalization test through the existing build tool rather than introducing a full test framework.

- [ ] **Step 3: Add endpoints and hooks**

Construct paths with explicit organization and system IDs:

```typescript
frameworkAssignments: (orgId: string, systemId: string) =>
  `/api/v1/ai-governance/organizations/${orgId}/systems/${systemId}/framework-assignments`
```

Expose loading, error, refresh, import, assign, updateAssessment, ingestRun, and reviewMapping operations.

- [ ] **Step 4: Consolidate navigation**

Replace the current fragmented `Govern & Prove` group with:

```typescript
[
  ["Overview", "/ai-governance"],
  ["AI Systems", "/model-inventory"],
  ["Frameworks & Controls", "/compliance-dashboard"],
  ["Evidence & Evaluations", "/evidence"],
  ["Findings", "/risks"],
  ["Reports & Assurance", "/reports"],
]
```

Keep Assess tools as execution surfaces. Completed runs appear in Evidence & Evaluations.

- [ ] **Step 5: Build and commit**

```bash
cd apps/frontend
npm run build
git add src/lib/api/endpoints.ts src/lib/api/hooks/useGovernanceAssurance.ts src/lib/constants/navigation.ts src/components/layout/Sidebar.tsx src/lib/api/hooks/useGovernanceAssurance.test.ts
git commit -m "feat(governance): consolidate assurance navigation"
```

### Task 6: Frameworks & Controls workbench

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/compliance-dashboard/page.tsx`
- Create: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/FrameworkCatalog.tsx`
- Create: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/ControlAssessmentTable.tsx`
- Create: `apps/frontend/src/app/(dashboard)/compliance-dashboard/components/ControlTracePanel.tsx`
- Test: `apps/frontend/tests/governance-assurance.spec.ts`

**Interfaces:**

- Consumes `useGovernanceAssurance` and existing OrgContext/SystemContext.
- Produces framework activation, control assessment filtering, inline trace, ownership, applicability, and state update.

- [ ] **Step 1: Write failing Playwright journey**

Cover selecting AIUC-1 April 2026, activating it for a selected system, filtering mandatory or missing-evidence controls, expanding A006.1, and updating owner/state. Assert labelled status, keyboard operation, and no certification language.

- [ ] **Step 2: Run the focused test and verify RED**

```bash
cd apps/frontend
npx playwright test tests/governance-assurance.spec.ts
```

- [ ] **Step 3: Build the workbench with existing components**

Use a toolbar, summary strip, dense table, and inline trace panel. Do not use a hero or repeated metric cards. The first empty state says `Activate a framework version for this AI system` and offers the authorized action.

Control rows show framework ID, title, mandatory or optional, Core or Supplemental, owner, assessment state, accepted evidence count, latest evaluation, freshness, and open findings.

- [ ] **Step 4: Add responsive and accessibility behavior**

At mobile widths, rows become labelled stacked records. The trace remains inline. All filters and updates work by keyboard, status has text labels, and loading uses skeleton rows.

- [ ] **Step 5: Verify and commit**

```bash
npx playwright test tests/governance-assurance.spec.ts
npm run build
git add src/app/\(dashboard\)/compliance-dashboard tests/governance-assurance.spec.ts
git commit -m "feat(governance): add frameworks and controls workbench"
```

### Task 7: Evidence & Evaluations review surface

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/evidence/page.tsx`
- Create: `apps/frontend/src/app/(dashboard)/evidence/components/EvaluationRunList.tsx`
- Create: `apps/frontend/src/app/(dashboard)/evidence/components/EvidenceMappingReview.tsx`
- Modify: `apps/frontend/tests/governance-assurance.spec.ts`

**Interfaces:**

- Reuses current Evidence Hub upload, folder, tag, search, and detail mechanics.
- Adds evaluation-run provenance and candidate mapping review.

- [ ] **Step 1: Extend the failing Playwright journey**

Assert that a completed evaluation displays source, system version, runner version, capture time, result, limitations, and content hash. Review a candidate mapping to A006.1 and verify accepted state and rationale.

- [ ] **Step 2: Verify RED**

Run the focused Playwright test.

- [ ] **Step 3: Implement evaluation and review views**

Add `gaps`, `evaluations`, and `artifacts` tabs through the `view` query parameter. Replace raw entity-ID linking for controls with a searchable control picker. Keep the existing detail drawer for artifacts; show provenance and mappings as structured sections.

- [ ] **Step 4: Verify and commit**

```bash
npx playwright test tests/governance-assurance.spec.ts
npm run build
git add src/app/\(dashboard\)/evidence tests/governance-assurance.spec.ts
git commit -m "feat(governance): review evaluation evidence mappings"
```

### Task 8: Assurance summary, redirects, and integrated verification

**Files:**

- Modify: `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`
- Modify: `apps/frontend/src/app/(dashboard)/reports/page.tsx`
- Modify: `apps/frontend/next.config.js`
- Modify: `apps/frontend/tests/governance-assurance.spec.ts`
- Create: `docs/ai-governance/assurance-module.md`

**Interfaces:**

- Overview consumes transparent readiness counts from Task 3.
- Reports & Assurance shows a version-pinned summary and read-only auditor lens.
- Legacy route redirects preserve bookmarks.

- [ ] **Step 1: Extend the failing end-to-end journey**

Assert that Overview shows scope and blockers before aggregate readiness, Reports pins framework version and evidence hashes, auditor mode removes mutation actions, and legacy paths redirect.

- [ ] **Step 2: Replace heuristic readiness**

Remove evidence-count heuristics from the touched Overview path. Show explicit accepted, partial, not started, missing, stale, and blocking counts from the backend.

- [ ] **Step 3: Consolidate Reports & Assurance**

Reuse current report preview and history. Add scope, framework version, evidence index, unresolved findings, decisions, and limitations. Auditor mode is the same route with read-only permissions, not a new portal.

- [ ] **Step 4: Add redirects**

Configure:

```text
/audit-reports -> /reports?view=builder
/compliance -> /compliance-dashboard
/compliance/dashboard -> /compliance-dashboard
/remediation-wizard -> /remediation?mode=guided
```

- [ ] **Step 5: Run integrated verification**

```bash
cd apps/backend
uv run pytest tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py tests/test_governance_assurance_routes.py tests/test_governance_evidence_runs.py -q
cd ../../
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
cd apps/frontend
npx playwright test tests/governance-assurance.spec.ts
npm run build
cd ../..
git diff --check
```

Expected: all new backend and frontend tests pass, boundary checks pass, frontend production build passes, and no whitespace errors remain. The pre-existing unrelated `api.models` collection failure remains documented if the full backend suite is run.

- [ ] **Step 6: Write operator documentation and commit**

Document workbook import, framework activation, evidence-run ingestion, mapping review, claim boundaries, and the recorded baseline issue.

```bash
git add apps/frontend/src/app/\(dashboard\)/ai-governance/page.tsx apps/frontend/src/app/\(dashboard\)/reports/page.tsx apps/frontend/next.config.js apps/frontend/tests/governance-assurance.spec.ts docs/ai-governance/assurance-module.md
git commit -m "feat(governance): complete assurance workflow"
```

## Plan Self-review

- Every MVP requirement in the design has a corresponding task.
- Framework catalog, system assessment, evidence ingestion, mapping review, IA consolidation, and assurance reporting are independently testable.
- Tenant isolation and evidence integrity are not deferred.
- The plan introduces no AIUC-specific table, duplicate tenant model, workflow engine, or integration marketplace.
- The supplied workbook remains external and is validated without being committed.
- Existing user changes in the original checkout are outside this worktree and remain untouched.

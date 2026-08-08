# Governance Decision CAS API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose a default-off, organization-scoped API for an independent reviewer to append one immutable governance decision and atomically compare-and-swap the matching v2 run projection.

**Architecture:** A new framework-free decision port and service use the existing audited 30-day mutation unit of work. The SQLAlchemy repository loads the complete decision authority and exact evidence set from persisted tenant-bound records, then inserts the immutable decision and CAS-updates the run in one PostgreSQL transaction. The HTTP route supplies only verdicts, rationale, and the expected verdict version; it cannot supply evidence identity or enable owner overrides.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 14, pytest.

## Global Constraints

- Require the exact `evaluation:decision` permission; role names and generic write permissions are insufficient.
- Require both `assurance_v2_enabled` and the independently default-off `assurance_v2_governance_decision_enabled` flag.
- Accept no client-owned evidence-set JSON, hash, envelope identity, decision identity, actor identity, or timestamp.
- Reject stale `expectedVerdictVersion` with HTTP 409 and preserve the run projection.
- Keep owner overrides unavailable; any `ownerOverrideReason` input is forbidden by the strict request schema and persistence commands always store `NULL`.
- Keep SQLite decision writes unavailable; only PostgreSQL can execute this mutation because the SQLite parity fixture deliberately rejects v2 decision insertion without trusted SHA-256.
- Do not add automatic enforcement or release gating.
- Do not change roadmap checkbox counts.

---

### Task 1: Framework-free decision contract and service

**Files:**
- Create: `apps/backend/src/application/ports/governance_decision.py`
- Create: `apps/backend/src/application/services/governance_decision_service.py`
- Create: `apps/backend/tests/test_governance_decision_service.py`

**Interfaces:**
- Consumes: `MutationCommand`, `MutationOutcome`, `MutationResult`, and `FrozenJsonObject` from `src.application.ports.evaluation_workbench`.
- Produces: `GovernanceDecisionScope`, `GovernanceDecisionAuthorityRecord`, `PersistGovernanceDecisionCommand`, `GovernanceDecisionRecord`, `GovernanceDecisionRepository`, `GovernanceDecisionUnitOfWork`, and `GovernanceDecisionService.decide(...)`.

- [ ] **Step 1: Write a failing successful-decision service test**

```python
result = service.decide(
    scope=GovernanceDecisionScope("org-a", "ws-a", "sys-a", "run-a"),
    actor_id="independent-decider",
    idempotency_key="decision-key",
    expected_verdict_version=0,
    overall_verdict="conditional",
    layer_verdicts={
        "suites": {"execution-a": "conditional"},
        "modalities": {"predictive_model": "conditional"},
        "components": {},
        "riskDimensions": {"fairness": "conditional"},
    },
    rationale="Current reviewed evidence supports conditional approval.",
)
assert result.status == 201
assert result.body["verdictVersion"] == 1
```

- [ ] **Step 2: Run the service test and verify RED**

Run: `.venv/bin/pytest -q -p no:cacheprovider tests/test_governance_decision_service.py`

Expected: collection fails because `governance_decision` does not yet exist.

- [ ] **Step 3: Implement the minimal decision contract and successful service path**

```python
class GovernanceDecisionService:
    def decide(
        self,
        *,
        scope: GovernanceDecisionScope,
        actor_id: str,
        idempotency_key: str,
        expected_verdict_version: int,
        overall_verdict: str,
        layer_verdicts: Mapping[str, object],
        rationale: str,
    ) -> MutationResult: ...
```

The service validates bounded public-safe strings and verdict structure, loads the locked authority inside `unit_of_work.mutate`, checks current version and four-eyes identities, generates the server UUID and timestamp, and passes the repository-owned evidence set and hash into `PersistGovernanceDecisionCommand`.

- [ ] **Step 4: Add failing service tests for stale CAS, scope absence, requester/submitter separation, malformed verdict layers, and persistence-record mismatch**

Each test must assert one stable error code: `governance_decision_version_conflict`, `governance_decision_scope_not_found`, `governance_decision_separation_required`, `governance_decision_request_invalid`, or `governance_decision_integrity_conflict`.

- [ ] **Step 5: Implement the minimum validation and integrity checks and verify GREEN**

Run: `.venv/bin/pytest -q -p no:cacheprovider tests/test_governance_decision_service.py`

Expected: all service tests pass.

### Task 2: Default-off strict HTTP boundary

**Files:**
- Modify: `apps/backend/config/settings.py`
- Modify: `apps/backend/api/main.py`
- Modify hard-linked pair: `apps/backend/api/routes/evaluation_workbench.py` and `apps/backend/src/api/routers/evaluation_workbench.py`
- Create: `apps/backend/api/composition/governance_decision.py`
- Modify: `apps/backend/tests/test_evaluation_workbench_routes.py`

**Interfaces:**
- Consumes: `GovernanceDecisionService.decide(...)` from Task 1.
- Produces: `governance_decision_router` and POST `/organizations/{org_id}/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/decisions`.

- [ ] **Step 1: Write failing route tests**

The tests assert: default-off returns 404 before body parsing; `model:write` without `evaluation:decision` returns 403; organization mismatch returns 404; valid scope forwards the membership actor and returns 201; `ownerOverrideReason` returns 422 because the strict model forbids it.

- [ ] **Step 2: Run the focused route tests and verify RED**

Run: `.venv/bin/pytest -q -p no:cacheprovider tests/test_evaluation_workbench_routes.py -k governance_decision`

Expected: tests fail because the router, flag, and schemas do not exist.

- [ ] **Step 3: Implement the route, permission, feature flag, and composition**

```python
class GovernanceDecisionRequest(StrictModel):
    expected_verdict_version: int = Field(alias="expectedVerdictVersion", ge=0)
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    layer_verdicts: LayerVerdictsResponse = Field(alias="layerVerdicts")
    rationale: str = Field(min_length=1, max_length=4000)
```

The route requires the feature dependency before parsing, checks the literal decision permission, derives organization and actor from membership, and calls the service with no owner-override parameter.

- [ ] **Step 4: Verify the focused route tests GREEN**

Run: `.venv/bin/pytest -q -p no:cacheprovider tests/test_evaluation_workbench_routes.py -k governance_decision`

Expected: all governance-decision route tests pass.

### Task 3: PostgreSQL server-owned authority and atomic persistence

**Files:**
- Modify: `apps/backend/src/infrastructure/db/repositories/evaluation_workbench_repository.py`
- Modify: `apps/backend/tests/test_evaluation_assurance_trust_integrity_postgres.py`

**Interfaces:**
- Consumes: decision port records and commands from Task 1 and the existing `SqlAlchemyEvaluationWorkbenchUnitOfWork`.
- Produces: `load_governance_decision_authority_for_update(...)` and `persist_governance_decision(...)` on `SqlAlchemyEvaluationWorkbenchRepository`.

- [ ] **Step 1: Write a failing native PostgreSQL adapter test**

Seed the existing accepted-review graph, create a SQLAlchemy session in that fixture schema, call the service, and assert in one committed result that decision version 1 exists, the run projects the same version/verdict/layers, the evidence-set hash matches canonical server-loaded evidence, and one audit/idempotency result is present.

- [ ] **Step 2: Run the native PostgreSQL test and verify RED**

Run: `FAIRMIND_TEST_POSTGRES_URL=<disposable-url> .venv/bin/pytest -q -p no:cacheprovider tests/test_evaluation_assurance_trust_integrity_postgres.py -k decision_service_persists`

Expected: the test fails because repository decision methods do not exist.

- [ ] **Step 3: Implement locked authority loading**

The repository locks the exact v2 run and reads the server-owned evidence set with `fairmind_expected_decision_evidence_set_013b(run_id)`. It canonicalizes the resulting object with the application’s canonical JSON function, hashes those exact bytes, and collects the run requester plus all bound evidence submitters for the service separation check.

- [ ] **Step 4: Implement immutable insert plus exact run CAS**

Insert `GovernanceEvaluationDecision` with `owner_override_reason=None`, then update the matching run only when tenant scope, envelope identity, `verdict_version=expectedVerdictVersion`, and prior verdict/layers snapshot still match. Translate PostgreSQL trigger/constraint failures into stable 409 decision errors. Force deferred decision/run-projection constraints before the callback returns.

- [ ] **Step 5: Add stale-CAS and atomic-rollback PostgreSQL tests and verify GREEN**

Run: `FAIRMIND_TEST_POSTGRES_URL=<disposable-url> .venv/bin/pytest -q -p no:cacheprovider tests/test_evaluation_assurance_trust_integrity_postgres.py -k 'decision_service_persists or decision_service_stale'`

Expected: successful decision passes; stale concurrent version leaves both decision history and run projection unchanged.

### Task 4: Regression and boundary verification

**Files:**
- Verify only; do not alter roadmap counts.

**Interfaces:**
- Consumes: completed Tasks 1–3.
- Produces: bounded verification evidence for the exact worktree state.

- [ ] **Step 1: Run focused non-PostgreSQL tests**

Run: `.venv/bin/pytest -q -p no:cacheprovider tests/test_governance_decision_service.py tests/test_evaluation_workbench_routes.py tests/test_evidence_review_repository.py tests/test_verified_evidence_review_service.py`

- [ ] **Step 2: Run native PostgreSQL decision tests**

Run the repository tests from Task 3 against a disposable PostgreSQL database.

- [ ] **Step 3: Run architecture guards**

Run from repository root: `tooling/check_backend_layer_boundaries.sh` and `tooling/check_no_archive_imports.sh`.

- [ ] **Step 4: Inspect status and diff**

Confirm only the listed files changed, the hard-linked route pair remains one inode, settings default to false, no owner override path exists, and the roadmap file is unchanged.

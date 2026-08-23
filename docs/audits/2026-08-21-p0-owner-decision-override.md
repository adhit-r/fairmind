# P0 four-eyes review and owner decision override evidence

Date: 2026-08-23

## Checkpoint identity

- Baseline commit: `98208b63c3591eb57ce57864e96bf8a6c7905eb6`
- Final implementation commit: `f6c076f7ec666bb99d6eb0a18635ec05427e9106`
- Documentation checkpoint: this audit and the prescribed roadmap prose update
  are the current commit-to-be-created. This report does not invent or claim its
  own self-referential commit hash.

This checkpoint closes one internal control-plane roadmap item: evidence review
is permanently four-eyes, and a separately gated canonical organization owner
may create one audited governance decision when requester or evidence-submitter
separation would otherwise reject that owner. It is local PostgreSQL 14,
SQLite-parity, application, and route proof. It is not staging, production,
public rollout, certification, worker execution, automatic enforcement, or a
frontend release.

## Exact implementation range

`98208b6..f6c076f` changes exactly these implementation and proof files:

- `apps/backend/api/main.py`
- `apps/backend/config/migration_integrity.py`
- `apps/backend/config/settings.py`
- `apps/backend/migrations/013j_owner_decision_override_integrity.sql`
- `apps/backend/migrations/fixtures/013j_owner_decision_override_integrity.sqlite.sql`
- `apps/backend/migrations/owner_decision_override_integrity_migration.py`
- `apps/backend/migrations/upgrade_paths/013i_to_013j_owner_decision_override_integrity.sql`
- `apps/backend/src/api/routers/evaluation_workbench.py`
- `apps/backend/src/application/evaluation_workbench_contracts.py`
- `apps/backend/src/application/ports/governance_decision.py`
- `apps/backend/src/application/services/governance_decision_service.py`
- `apps/backend/src/domain/assurance/evaluation_v2.py`
- `apps/backend/src/infrastructure/db/database/governance_models.py`
- `apps/backend/src/infrastructure/db/repositories/evaluation_workbench_repository.py`
- `apps/backend/tests/test_api_main_assurance_v2_route_gate.py`
- `apps/backend/tests/test_assurance_v2_mutation_boundary_manifest.py`
- `apps/backend/tests/test_evaluation_assurance_trust_integrity_postgres.py`
- `apps/backend/tests/test_evaluation_assurance_v2_models.py`
- `apps/backend/tests/test_evaluation_workbench_repository.py`
- `apps/backend/tests/test_evaluation_workbench_routes.py`
- `apps/backend/tests/test_governance_decision_service.py`
- `apps/backend/tests/test_migration_integrity.py`
- `apps/backend/tests/test_owner_decision_override_integrity_013j.py`
- `apps/backend/tests/test_owner_decision_override_postgres.py`

The documentation checkpoint adds or changes exactly:

- `docs/audits/2026-08-21-p0-owner-decision-override.md`
- `docs/superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md`

Frozen migrations 013 through 013i were not changed.

## Implemented control boundary

### Review remains non-overridable

Migration 013j replaces the PostgreSQL review guard so each review is checked
against the exact admission submitter, evidence linker, and run requester.
Every non-null review `separation_override_reason` is rejected. The migration
locks the review table before its provenance preflight, so an in-flight legacy
write cannot pass the scan and commit an invalid review during guard
replacement. SQLite installs the corresponding stronger review guard
atomically. No review route, service permission, or reason field was added.

### Owner override is decision-only and single-use

The new endpoint is separate from the normal decision endpoint. Its immutable
decision row is the override receipt; there is no grant, bearer token,
delegation, expiry, renewal, revocation, or transferable authority subsystem.
The exception waives only decider-versus-requester and
decider-versus-evidence-submitter identity comparisons. The owner must have a
real separation conflict; an independent owner must use the normal route.

All normal decision invariants remain mandatory: exact tenant/workspace/system/
run scope, completed run, accepted verified reviews, operationally current
evidence, issuer/key/policy authority, evidence-set hash, suite layer scope,
chronology, verdict-version CAS, idempotency, and audit-chain append.

### Canonical owner authority and provisioning

PostgreSQL proves all owner authority inside the decision transaction. The
actor must equal the exact active organization's `owner_id`, have an active
membership, use the exact system role named `owner`, and obtain both
`evaluation:decision` and the reserved
`evaluation:separation:override` permission from a bounded, canonical JSON
permission array. Role-name equality alone is insufficient.

The helper locks organization, membership, and role rows in that deterministic
order. Application preflight and the insert trigger use the same database
predicate. Tests cover owner and organization mutations, member status/role and
deletion, system-role state and deletion, both required permissions, permission
shape, and writer-first and override-first commit orderings.

The migration does not provision authority. The only approved production
provisioning boundary is a reviewed per-organization SQL/bootstrap change
executed with the trusted schema-owner identity under deployment change
control. Legacy role, invitation, membership, and normalized-permission APIs
continue to reject or omit the reserved permission.

### Default-off release gates

All three settings default to `false`:

- `assurance_v2_enabled`
- `assurance_v2_governance_decision_enabled`
- `assurance_v2_separation_override_enabled`

The main application mounts the override router only when all three are true,
and a directly mounted router independently enforces the same gates. The normal
decision route and response remain unchanged and reject override fields.

### Reason, response, idempotency, and audit handling

The bounded 1-2000 UTF-8 byte `ownerOverrideReason` is stored only in the
immutable decision row. PostgreSQL requires every non-null reason to equal its
`btrim` value and have `octet_length` from 1 through 2000; migration 013j locks
the decision table, rejects legacy-invalid values without rewriting them, and
recreates and validates the named check constraint. The ORM mirrors trimming
and its portable character-length bound. The public response exposes only
`ownerOverrideApplied: true`. Success and rejected audit material, response
material, errors, and completed idempotency responses exclude the raw reason.
The request and success audit bind its canonical SHA-256 hash.

The success audit records the canonical owner, decision/run/version, evidence
set, database decision time, reason hash, and sorted waived relationships. The
deferred PostgreSQL constraint requires the override decision, exact completed
idempotency generation, exact immutable success event, success binding,
operation, action, actor, organization, resource, reason hash, and recomputed
waived relationships to agree at commit. Raw SQL fabrication of operation,
actor, action, resource, reason hash, waived IDs, or audit-event ID fails.
Normal decisions are outside this override-only deferred constraint.

The shared SQLAlchemy mutation UoW remains the sole idempotency, decision,
audit, and commit boundary. PostgreSQL lock timeout, deadlock, serialization,
privilege, and infrastructure errors escape the owner-authority predicate
rather than becoming a domain denial. A native locked-authority-row test proves
that a bounded `lock_timeout` becomes a persistence failure, rollback leaves no
decision, success or rejected audit, or completed idempotency generation, and
the same key succeeds after the blocker releases. Expected domain rejection
persists only a sanitized rejected audit and replayable bounded response.
SQLite cannot prove canonical PostgreSQL owner authority and therefore rejects
every non-null owner override reason.

## TDD and review history

### Tasks 1-2: service and HTTP boundary

- Task 1 RED was the missing `admission_submitters` contract; GREEN was 12
  service tests. Review then found normal repository compatibility had become a
  `TypeError`; the default-preserving fix produced 13 passing service tests and
  left overrides fail-closed until the real adapter supplied provenance.
- Task 2 RED was the absent separate override router; GREEN was 100 route,
  mounting, and mutation-manifest tests. Review found the generic public-safe
  validator silently imposed a 512-byte ceiling on the advertised 2000-byte
  reason contract. Boundary tests failed at 513 and 2000 bytes before the fix;
  the repaired matrix passed 104 tests, with the service regression passing 13.
  Review was clean after one fix round.

### Tasks 3-4: database and audited repository path

- Task 3 RED was the absent 013j migration module. Initial GREEN was 28
  SQLite/ORM cases and 12 native PostgreSQL cases. Review then reproduced a
  PostgreSQL preflight race and a partial SQLite trigger installation. The
  table lock and savepoint-based loader fixes passed 29 SQLite/ORM cases and 16
  native cases; review was clean after one fix round.
- Task 4 retained the earlier RED evidence: the SQLAlchemy owner-authority
  adapter was absent and non-null reasons were rejected before persistence.
  GREEN was 3 focused repository cases, 4 native audited-UoW cases, 173 broader
  repository cases, and the native normal-decision regression. Review found no
  scoped blocker; the report records one deferred process minor because the
  interrupted partial implementation was preserved instead of discarded only
  to reproduce the same RED.

### Tasks 5-6: concurrency and frozen deployment contract

- Task 5 added authority, scope, race, replay, raw-binding, append-only, and
  cleanup proof. Review required complete authority mutation coverage,
  database-observed organization-to-membership-to-role lock order, exact review
  version 2 binding, a fully ready twenty-session barrier, exact replay status,
  and bounded executor cleanup. After two fix rounds, the focused race slice
  passed 24 cases with 6 deselected, the exact native owner matrix passed 82,
  and unchanged legacy delegation hardening passed 24. Review was clean.
- Task 6 RED was a missing operator source, missing frozen 013j ledger entry,
  and incomplete catalog manifest. The operator, startup checks, checksums, and
  PostgreSQL catalog proof passed. Review then required executable two-clean-
  install SQLite reproducibility and a current test name. The final exact
  migration matrix passed 135 tests with one explicit non-C-collation skip;
  SQLite-focused proof passed 27. Review was clean after one fix round.

### Task 7 gate blockers and remediations

The first Task 7 release attempt correctly stopped before documentation:

- the focused matrix passed 425 tests with 64 native/environment skips;
- the native matrix failed one upgraded-013b decision repository case while
  273 passed and one non-C-collation case skipped;
- the layer-boundary script rejected the router's direct domain import.

Remediation A placed the owner-reason policy behind an application-owned
exception-translating wrapper and removed the API-to-domain edge. Its focused
route/service matrix passed 109 tests; architecture, compilation, and diff
checks passed. Review was clean.

Remediation B kept frozen migration 013b unchanged and normalized only
PostgreSQL-produced layer-verdict snapshots at repository read boundaries. It
uses bounded duplicate-safe JSON parsing and semantic `jsonb` equality for the
locked run projection CAS, while SQLite and every other stored-JSON contract
remain byte-exact. The initial CAS regression could fail at decision uniqueness
before reaching the projection update; review required a unique version-2
insert plus a same-transaction hook proving the run CAS matched zero rows and
rollback removed the inserted decision. The corrected native regression passed
and review was clean after one test fix round.

### Final-review fix wave

The final-review RED slice was `6 failed, 1 passed`: PostgreSQL was converting a
transient authority-row lock failure into false, direct SQL still accepted
untrimmed and over-2000-byte multibyte reasons, migration preflight did not
reject a legacy-invalid reason, and the ORM/operator contracts lacked the exact
new checks. The already-valid exact 2000-byte application case passed at RED.

Migration 013j now lets transient database failures escape, locks decisions
against concurrent writes, preflights existing reasons, and enforces the exact
trimmed 1-2000 UTF-8-byte database contract. The operator verifies that exact
validated constraint. The focused native transient/reason/operator GREEN
matrix was `96 passed, 70 warnings in 119.90s`; it includes same-key retry after
rollback and valid `"é" * 1000` application persistence. Frozen migrations 013
through 013i and the SQLite fixture remained byte-identical.

## Fresh Task 7 release evidence

The following results were generated from implementation commit `f6c076f`; the
earlier failed release attempt is not reused as final evidence.

### Complete focused backend matrix

```bash
cd apps/backend
uv run pytest -q -p no:cacheprovider \
  tests/test_governance_decision_service.py \
  tests/test_evaluation_workbench_repository.py \
  tests/test_evaluation_workbench_routes.py \
  tests/test_api_main_assurance_v2_route_gate.py \
  tests/test_assurance_v2_mutation_boundary_manifest.py \
  tests/test_evaluation_assurance_v2_models.py \
  tests/test_legacy_role_delegation_hardening.py \
  tests/test_verified_evidence_review_service.py \
  tests/test_owner_decision_override_integrity_013j.py \
  tests/test_migration_integrity.py
```

Result: `425 passed, 68 skipped, 133 warnings in 148.11s`. The skips are
explicit native/environment cases because this focused command does not set a
PostgreSQL DSN. Warnings are existing FastAPI, Pydantic, SQLAlchemy,
`pythonjsonlogger`, HTTP-status, and `datetime.utcnow()` deprecations.

### Native PostgreSQL decision, review, and audit matrix

```bash
cd apps/backend
FAIRMIND_TEST_POSTGRES_URL='postgresql://adhi@127.0.0.1:55447/postgres' \
uv run pytest -q -p no:cacheprovider \
  tests/test_owner_decision_override_integrity_013j.py \
  tests/test_owner_decision_override_postgres.py \
  tests/test_evaluation_assurance_trust_integrity_postgres.py \
  tests/test_operational_freshness_postgres.py \
  tests/test_evaluation_rejected_mutation_audit_postgres.py \
  tests/test_migration_integrity.py
```

Result: `281 passed, 71 warnings in 244.83s` on PostgreSQL 14.18, with no
skips. Warnings are the existing deprecations.

This native matrix includes canonical owner/member/role authority, deterministic
lock order, every authority writer-first and override-first ordering, normal
versus override verdict CAS, both review/decision commit orderings with exact
review-version binding, twenty ready-session same-key calls producing one
commit and nineteen exact `201` replays, direct deferred-binding fabrication
rejection, successful shared-UoW binding, rollback/retry, append-only update and
delete denial, transient authority-lock rollback and same-key retry, direct
trimmed/UTF-8-byte reason enforcement, legacy-invalid migration preflight,
operator replay, startup verification, and catalog drift.

### Architecture, source, and compilation gates

From repository root:

```bash
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
git diff --check
git status --short
```

All exited zero. The first two reported `Backend layer boundary checks passed.`
and `No archive import violations found.`; `git diff --check` had no output;
status contained only the preserved untracked implementation plan.

```bash
cd apps/backend
uv run python -m compileall -q \
  src/application/ports/governance_decision.py \
  src/application/services/governance_decision_service.py \
  src/domain/assurance/evaluation_v2.py \
  src/api/routers/evaluation_workbench.py \
  src/infrastructure/db/repositories/evaluation_workbench_repository.py \
  migrations/owner_decision_override_integrity_migration.py
```

Result: exit zero with no output.

## Frozen sources and catalogs

- PostgreSQL 013j direct SHA-256:
  `bc5deb123981ee968061ec695821e8d00a8cc860d3c2169f9ca81ae6805846b5`
- PostgreSQL 013i-to-013j operator SHA-256:
  `3a3cab3184178958bacd67c6573dedc9b624293b3b5cb773d899b20e02eb2f53`
- SQLite 013j fixture SHA-256:
  `60e6377e21e739ab1ce845d265ed736fb50d74af47846a227a628182f6ebc746`
- PostgreSQL 14 catalog digest:
  `c181fd00d2c65009cd17a673c0462d92d557c73dc7976f800a4bcb83ae4c6fd2`
- SQLite catalog digest:
  `90e595b216e7907a92872dcfc4e0478c831298eabd5536919cb05eb85fdfc6c7`

The three source hashes were independently recomputed during the final-review
wave and match the frozen manifest. The PostgreSQL digest was re-frozen from
two independently named clean full-chain PostgreSQL 14 installations with the
same result. The unchanged SQLite source and catalog digest retain their prior
two-clean-install proof. Both remain executable startup contracts.

## Explicitly open boundaries

- The trusted schema-owner/runtime database credential can still assert actor
  text and replace schema guards. This checkpoint does not claim resistance to
  a compromised schema owner or provide an external immutable audit anchor.
- A separately authenticated, least-privilege worker/runtime identity remains
  open. Worker execution and automatic enforcement remain disabled.
- Granular/delegable separation-override authorization remains incomplete. The
  implemented reserved override permission is intentionally not delegable
  through existing human role APIs.
- Evidence submit and link operations remain service-mediated rather than
  independently invocable production surfaces.
- Capability switches, unsupported modality packs, and automatic enforcement
  remain open and must stay disabled at API and UI boundaries.
- No frontend owner-override workflow is provided.
- The owner override is implemented but default-off. Production provisioning,
  enablement, verification, rollout gates, monitoring, rollback exercises, and
  public rollout remain independent and open.
- This checkpoint creates no `FairMind Verified`, certification, compliance,
  production-safety, or public-assurance claim.

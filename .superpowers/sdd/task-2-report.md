# Task 2 Report: Evaluation planning, runs, and Passport links

## Delivered behavior

- Added explicit camelCase FastAPI request and success-response contracts for creating, listing, activating, and preflighting evaluation plans; preparing and reading evaluation runs; and linking one exact Evidence Passport revision.
- Added pure plan/trigger validation and `EvaluationRunsService` with organization, workspace, and system scoping on every opaque plan, run, evidence-run, and Passport-revision lookup.
- Plan creation validates a non-whitespace 1-120 character name, exact target/lifecycle/depth/enforcement/delivery vocabularies, distinct lifecycle phases, and one-to-32 distinct immutable suite references matching the required syntax and length.
- Plan activation is draft-to-active, idempotent for active replays, rejects archived plans, leaves other active plans unchanged, and commits the transition with its audit event.
- Preflight reports unavailable FairMind execution honestly. External-provider and imported-report plans can prepare `awaiting_evidence` / `insufficient` runs; unavailable FairMind-worker plans cannot.
- Passport 1.0.0 linkage uses relational tenant scope, exact canonical `suite.name@version`, `aiSystem.kind`, and canonical result timestamps. Only predictive-model/model and agent/agent bindings are verifiable in this slice; other target kinds remain usable but return `target_kind_unverifiable` when linked.
- Linking uses a conditional compare-and-set from an unlinked `awaiting_evidence` run to linked `succeeded`, with `review` as the governance verdict. Same-revision replay is idempotent and a different winning revision conflicts.
- Plan creation, activation, run preparation, and Passport linking write minimal `OrganizationAuditLog` records in the same transaction. Explicit UUID strings are used for plan/run IDs and valid UUID values for audit resources.
- Plan and run lists are deterministic newest-first. Missing scoped systems return `404`; valid empty systems return empty lists.
- All six evaluation list/activation/preflight/detail/link `404` paths now return the advertised nested workflow envelope with exact `code`, `message`, and `nextAction`; legacy non-evaluation endpoints retain their string details.

## TDD evidence

- RED command: `cd apps/backend && /Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_runs.py -q --disable-warnings`
- RED result: exit 2 during collection; one error, `ModuleNotFoundError: No module named 'src.application.services.evaluation_runs_service'`.
- Focused GREEN command: the same Task 2 command.
- Independent-review RED command: the focused Task 2 command with `-k all_evaluation_404_paths`.
- Independent-review RED result: six failures; every route returned a legacy string `detail` instead of the declared nested workflow object.
- Focused GREEN result after review remediation: 47 passed, 217 warnings, exit 0, in 5.43 seconds.
- Regression command: `cd apps/backend && /Users/adhi/axonome/fairmind-evidence-recovery/apps/backend/.venv/bin/python -m pytest -p no:cacheprovider tests/test_evaluation_run_models.py tests/test_evaluation_runs.py tests/test_governance_assurance_models.py tests/test_governance_assurance_routes.py -q --disable-warnings`
- Regression GREEN result after review remediation: 96 passed, 297 warnings, exit 0, in 7.43 seconds.
- `tooling/check_backend_layer_boundaries.sh`: passed.
- `tooling/check_no_archive_imports.sh`: passed.
- `git diff --check`: passed.

## Race and audit rollback evidence

- `test_two_sessions_atomically_link_only_one_distinct_passport_revision` uses a file-backed SQLite database with WAL and two independent sessions. Exactly one distinct revision links, the loser receives `passport_link_conflict`, and exactly one link audit row exists.
- Injected `_write_audit` failures prove plan creation, plan activation, external/imported run preparation, and Passport linking all roll back their domain mutation and return structured `evaluation_persistence_failed` responses.
- Exact-link tests prove same-revision replay does not add another audit row and the immutable Passport snapshot remains byte-for-byte unchanged.

## Files changed

- `apps/backend/src/application/services/evaluation_runs_service.py`
- `apps/backend/src/api/routers/governance_assurance.py` (the tracked hard-link target for `apps/backend/api/routes/governance_assurance.py`)
- `apps/backend/tests/test_evaluation_runs.py`

## Commit

- Initial commit SHA: `c0d9e0640be2e521b599ccbe8186c2b7a8eada3d`
- Review-fix commit SHA: `bbfcee746bf8cb50b3c9a7b474a94aebbf0191dd`
- Initial message: `feat(evaluations): expose evidence-backed run workflow`

## Concerns

- The race proof is SQLite-specific and intentionally file-backed; no PostgreSQL race was run in this task. The review's synchronization Minor remains bounded: pausing two SQLite WAL read transactions immediately before write promotion can produce platform-dependent `SQLITE_BUSY`, while adding a production synchronization seam solely for the test would distort the service surface. The test still verifies one durable winner, one conflict, and one audit row across two independent sessions.
- The required test commands pass with existing dependency/deprecation warning volume shown above.
- Concurrent Task 3 work modified the shared plan document; it is not part of the Task 2 commit.

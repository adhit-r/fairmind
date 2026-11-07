# P1 Typed Worker Execution Port

Date: 2026-08-30

Base: `782f715`

Scope: declaration-only P1 worker execution contract

## Result

`WorkerCapabilities` remains an immutable capability declaration covering the
worker type, supported execution depths, and supported lifecycle phases.
`EvaluationWorkerPort.execute` now accepts the domain's exact
`ExecutionEnvelopeV2` type instead of the generic `FrozenJsonObject` input.
The result remains a frozen JSON object.

This is a typed application boundary only. It mounts no worker route, creates
no concrete executor, starts no sandbox, issues no credential, and performs no
runtime work. The separately implemented PostgreSQL leased queue remains the
only concrete P1 worker adapter.

## TDD Evidence

The focused contract test was written first and failed because the port still
accepted `FrozenJsonObject`:

```text
assert <class '...FrozenJsonObject'> is ExecutionEnvelopeV2
```

After the minimal annotation change, the same test passed. The full mutation
boundary manifest and worker queue contract are part of the fresh verification
for this checkpoint.

## Security Review

Codex Security diff scan `c49c008c-16e2-4533-beba-3dd0494ede51` reviewed the
exact working-tree production change with complete inventory coverage and found
zero reportable findings.

The review retained one future integration requirement: Python Protocol
annotations are not runtime validation, while `build_execution_envelope_v2`
currently returns canonical dictionary, encoded text, and SHA-256 hash values.
Before any concrete executor is mounted, the integration must construct the
typed input without reparsing untrusted material or losing that canonical hash
binding.

## Fresh Verification

From `apps/backend`:

```bash
uv run pytest -q \
  tests/test_assurance_v2_mutation_boundary_manifest.py \
  tests/test_evaluation_worker_queue_contract.py
```

Result: `13 passed`. The run also reported existing framework and dependency
deprecation warnings; it reported no test failures.

From the repository root:

```bash
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
python3 -m compileall -q \
  apps/backend/src/application/ports/evaluation_worker.py \
  apps/backend/tests/test_assurance_v2_mutation_boundary_manifest.py
git diff --check
```

All four commands exited successfully.

## Non-claims

- No worker execution is available through this port.
- No public worker endpoint is mounted.
- No queue-to-executor handoff is implemented.
- No sandbox, broker, artifact storage, or egress policy is implemented.
- This checkpoint does not complete the pending worker job-state or signed
  Passport completion rows.

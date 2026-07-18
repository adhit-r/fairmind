# Integration baseline — 2026-07-18

## Scope and provenance

This recovery worktree integrates the committed assurance and FairMind-E work
only. It does not import uncommitted source-worktree changes.

| Source | Path | Branch | HEAD | Dirty state excluded from this integration |
| --- | --- | --- | --- | --- |
| Assurance | `/Users/adhi/axonome/fairmind-ai-governance-assurance` | `codex/ai-governance-assurance` | `b82f20cc2c78a9b7716210f28f7be04f22bda111` | 19 modified tracked files and 2 untracked files; tracked diff: 561 insertions, 83 deletions across 19 files. |
| FairMind-E | `/Users/adhi/axonome/fairmind` | `fairmind-e/p2b-paper-wedge` | `1fcdc8bee97c912dd71626f18b52acdf03d584de` | 4 modified tracked files and 9 untracked paths; tracked diff: 243 insertions, 212 deletions across 4 files. |

Merge base: `bd1345c2d2020265482396bc753d0ab1576cc38c`.

Integration branch/worktree: `codex/fairmind-evidence-recovery` at
`/Users/adhi/axonome/fairmind-evidence-recovery`. It started from the
assurance tip. The committed FairMind-E changes were cherry-picked with zero
conflicts and zero committed path overlap:

| FairMind-E original | Recovery cherry-pick |
| --- | --- |
| `e575364` | `e020d10` |
| `d11e1e9` | `c28f1a4` |
| `c7845fb` | `dab6c78` |
| `1fcdc8b` | `a078697` |

The written FairMind-E backlog listed only three commits through `c7845fb`;
the source branch contains a fourth committed change, `1fcdc8b`. This
three-versus-four-commit drift is recorded here so later slices use the actual
source tip.

## Baseline failure and resolution

The initially observed selected baseline was **119 passed, 4 failed**:

- One test used the intentionally unmounted legacy `/api/approvals` route.
- Three tests called the canonical approval API without the newly required
  authenticated organization context.

The legacy router remains unmounted. It must not be restored because it lacks
the tenant and actor guarantees of the canonical governance approval API.

The test harness now creates a fresh in-memory SQLite `StaticPool` engine for
each opt-in environmental-governance test, persists a user, organization, and
active owner membership, and overrides both `get_db` and
`get_current_active_user`. Environmental systems are created through
`/api/v1/ai-governance/organizations/{org_id}/...`, so they carry the real
organization binding before a canonical approval request is made. The tests
continue to prove the release-gate behavior: `no_go` and missing environmental
evidence return `409`; a documented `conditional_go` permits approval.

## Environment and verification

No migration was executed. Tests used the existing backend virtual environment
and an explicit isolated database URL:

```bash
# repository root
git diff --check
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh

# apps/backend
DATABASE_URL=sqlite:////private/tmp/fairmind-s1.1-verification.sqlite .venv/bin/pytest tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py tests/test_governance_assurance_routes.py tests/test_governance_evidence_runs.py tests/test_environmental.py tests/test_environmental_api.py tests/test_environmental_governance.py -q
```

Final results:

- `git diff --check`: passed.
- `tooling/check_backend_layer_boundaries.sh`: passed.
- `tooling/check_no_archive_imports.sh`: passed.
- Selected backend suite: **123 passed, 315 warnings in 5.94s**. Warnings are
  existing dependency deprecations, SQLAlchemy's SQLite foreign-key drop-order
  warning from isolated fixture teardown, and pytest cache write warnings in
  the read-only recovery worktree; no test failure was suppressed.

## Follow-on blockers

These are explicitly outside S1.1 and remain unresolved:

- The duplicate `009` migrations (`009_policy_versions.sql` and
  `009_governance_assurance.sql`) and the governance SQLite adapter's hardcoded
  `009_governance_assurance.sql` filename. The assurance migration rename is
  owned by S1.3.
- The unsafe ledgerless migration runner in `apps/backend/scripts/migrate.py`,
  which executes every SQL file without recording applied migrations.
- Unscoped environmental evidence paths, which still need tenant enforcement
  beyond the system-scoped approval gate exercised here.
- Dual database/session managers (`database/connection.py` and
  `config/database.py`, with related infrastructure copies), which make runtime
  database ownership ambiguous.

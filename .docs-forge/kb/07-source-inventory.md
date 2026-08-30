# P0 source inventory

This is a targeted inventory for the P0 release-documentation scope. Files
outside the listed areas were classified as out of scope rather than treated
as evidence for P0 claims. Archive, generated output, dependency directories,
lockfile contents, binary assets, large fixtures, and unrelated legacy routes
were skipped according to the Docs Forge ingestion rules.

| Source area | Read depth | Documentation role |
| --- | --- | --- |
| `README.md`, `CHANGELOG.md`, `docs/releases/v2.1.0-alpha.1.md`, master TODO | Full | Release identity, claims, known gaps, verification boundary |
| `AGENTS.md`, package metadata, app READMEs, CI/release workflows | Full | Commands, dependency rules, toolchain, release gates |
| `apps/backend/api/main.py`, `apps/backend/config/settings.py` | Full for P0 composition/settings sections | Default-off router composition and child gates |
| `apps/backend/src/api/evaluation_permissions.py` | Full | Human permissions, worker vocabulary, fail-closed scope |
| P0 routers under `apps/backend/src/api/routers` and compatibility composition under `apps/backend/api` | Full for Assurance V2 declarations; unrelated routes out of scope | HTTP paths, dependencies, request/response boundary |
| P0 application services for workbench, admission, linking, review, freshness, governance decisions, evaluator catalog, and trust administration | Full public methods; internal helpers sampled | Workflow, invariants, trust and decision semantics |
| P0 domain models/schemas and PostgreSQL repositories | Public contracts full; deep persistence helpers sampled | Immutable identity, state, hashes, database authority |
| Migrations `013*` and their upgrade paths | Full DDL/trigger sections related to P0; fixtures stat-only | PostgreSQL integrity and compatibility boundaries |
| Representative P0 backend tests named in the release workflow | Sample-read assertions and fixtures | Intended denial, idempotency, trust, freshness, and separation behavior |
| `apps/frontend/src/app/(dashboard)/assurance/evaluations/[runId]/page.tsx` and its evidence components/hooks | Full | Gated, read-only, scope-bound dashboard behavior |
| `apps/docs` source, content, package metadata, and validator | Full | Documentation renderer, navigation, search, validation |
| `apps/website` release-facing pages/config | Release copy full; unrelated presentation code sampled | Public alpha boundary and project links |
| `archive/`, `apps/backend/archive/`, `_external/`, generated builds, dependencies, snapshots, large fixtures | Skipped with reason | Not active P0 runtime evidence |
| P1-P5 implementation branches and unrelated application modules | Out of scope | Must not be used to expand P0 capability claims |

The generated page-to-source map is in `03-features.md`. Open intent and
publication gaps are in `99-open-questions.md`.

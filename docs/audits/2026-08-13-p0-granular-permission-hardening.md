# P0 granular permission hardening evidence

Date: 2026-08-13

## Validated defects

The pre-fix Cyber review reproduced two authorization-boundary defects against
real HTTP routes and persistence:

- `FM-EVAL-PERM-001`: a signed organization viewer whose persisted role held
  only legacy `model:write` could create target versions, create suite versions,
  and activate suites. All three operations succeeded without
  `evaluation:catalog:admin`.
- `FM-EVAL-GATE-001`: the canonical application hid Assurance V2 while its
  master flag was disabled, but a directly mounted core router did not enforce
  that flag and could reach all six base mutation workflows.

The evaluator catalog also accepted undeclared action aliases such as
`evaluation:catalog:submit`, while the architecture contract defines one
literal `evaluation:catalog:admin` authority.

## Remediation

- Centralized the live human Assurance V2 permission vocabulary in a
  fail-closed API helper.
- Required literal permissions from persisted organization membership for
  plan write, plan activation, run creation, evidence submission and linking,
  evidence review, governance decision, and catalog administration.
- Required `evaluation:catalog:admin` for target creation, suite creation,
  suite activation, and every evaluator-registration operation. Legacy
  `model:write`, owner/admin role names, token wildcards, and catalog action
  aliases do not satisfy this check.
- Added the Assurance V2 master gate as a dependency of the core router so a
  noncanonical direct mount fails with 404 before request parsing or service
  execution.
- Removed the frontend `evaluation:catalog:read` alias and prevented catalog
  rendering or fetching without the literal catalog-admin permission.
- Retained `evaluation:trust:admin`, `evaluation:worker`, and
  `evaluation:separation:override` as reserved, non-authorizing vocabulary.

## Verification

- The integrated backend authorization, catalog, evidence, review, decision,
  legacy-isolation, and PostgreSQL slice passed 256 tests.
- Frontend typecheck and production build passed; all 23 governance-assurance
  Playwright tests passed.
- The focused frontend permission/catalog tests passed 16 tests.
- An independent Cyber exploit harness passed three tests. With a real signed
  bearer and persisted `model:write` viewer membership, all three catalog
  mutations returned 403 before service entry and produced zero database,
  idempotency, or audit-chain deltas. With the master gate disabled, all six
  malformed base mutations returned 404 before authentication, database,
  parsing, or service entry. Four catalog aliases were denied while four
  literal-admin positive controls succeeded.
- The independent selected security nodes passed 11 tests and the complete
  workbench/catalog route suites passed 89 tests.
- Backend layer-boundary and no-archive-import guards passed.
- Python compilation, hardlink parity, production alias search, and
  `git diff --check` passed.
- A read-only Ponytail review found no concrete merge blocker in the final
  implementation.

## Claim boundary

This checkpoint closes the reproduced legacy-permission and direct-mount
bypasses for local source and test execution. It does not prove staging or
production configuration. The master granular-permission roadmap row remains
open: trust administration, service-principal worker authorization, an audited
separation-of-duty override, and independently invocable evidence submit/link
surfaces are not yet implemented. No certification, compliance, worker, or
automatic-enforcement claim follows from this change.

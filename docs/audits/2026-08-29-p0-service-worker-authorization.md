# P0 service-worker authorization contract

Date: 2026-08-29

## Result

FairMind now has a narrow authorization predicate for a future Assurance V2
worker. It does not mount a worker route or implement a worker runtime.

The verified JWT projection distinguishes `human` and `service` principals.
Existing access, refresh, and API-key issuers mark their tokens as human, and
the interactive-user dependency and both configured app-wide authentication
middlewares reject every explicit service principal. Signed human tokens minted
before this slice remain human through an explicit legacy-compatibility fallback
when `principal_kind` is absent. All current issuers set the claim explicitly,
and a token cannot satisfy the worker predicate without explicitly declaring
`service`. The worker predicate independently requires all of the following:

- an access-token projection with `principal_kind=service`;
- the literal `evaluation:worker` permission in a bounded, canonical array;
- no wildcard permission; and
- an exact organization claim matching the organization derived by a future
  caller from the persisted run or execution envelope.

Human roles, admin names, wildcard claims, API keys, missing permissions,
missing organization claims, and cross-tenant claims cannot satisfy the
predicate. Legacy organization-role normalization and mutation APIs continue
to strip or reject `evaluation:worker`.

## Verification

TDD began with a collection failure because `PrincipalKind` did not exist. The
final seven-file authorization verification set passed 161 tests with no
failures in 2.04 seconds. It was run from `apps/backend` as:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider \
  tests/test_evaluation_worker_authorization.py \
  tests/test_jwt_authentication_middleware.py \
  tests/test_auth_token_purpose.py \
  tests/test_legacy_role_delegation_hardening.py \
  tests/test_assurance_v2_mutation_boundary_manifest.py \
  tests/test_evaluation_workbench_service.py \
  tests/test_auth_integration.py
```

The run emitted 410 existing dependency and deprecation warnings.

The first immutable security snapshot exposed two conditional purpose-confusion
paths: a service token could enter a legacy human dependency, and a service
refresh token could be exchanged for a human access token. Both were reproduced
with failing tests and then closed by separating generic principal verification
from human authentication and enforcing human purpose at refresh exchange.
A later CodeCanopy/Ponytail review exposed a third path through the app-wide
legacy middleware. A signed service token reproduced the bypass with HTTP 200;
the middleware, its request-state helper, and a mounted governance route now
have regression coverage proving service principals receive HTTP 401.
The final CodeCanopy/Ponytail pass exposed the same conditional path in the
production-only Neon middleware. A failing regression test reproduced it before
the middleware was changed to reject explicit service principals before setting
request state; the protected route now returns HTTP 401 under Neon as well.

The mutation manifest still proves that no worker route is mounted, and plan
preflight continues to return `worker_unavailable` for FairMind-worker
delivery.

## Claim boundary

This is only a tenant-bound authorization predicate designed to follow the
existing verified token projection, but no authentication dependency composes
the two yet. It does not create a service-principal registry, worker
credential issuer, rotation or revocation workflow, worker database identity,
queue, lease, adapter, artifact broker, sandbox, or execution capability.
Those remain P1 work. The granular-permission roadmap item remains open until
delegable separation-override authorization and independently invocable
evidence submit/link surfaces are implemented and verified.

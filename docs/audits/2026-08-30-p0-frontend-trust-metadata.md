# P0 frontend trust-metadata audit

Date: 2026-08-30

Roadmap item:

> Show signer, source, admission, freshness, review, expiry, limitations, and invalidation reason.

## Result

Complete on the approved, default-off Assurance v2 run preview. Public rollout
is not implied.

The scoped `/assurance/evaluations/:runId` response projects suite evidence
source, signer identity, effective expiry, admission, operational freshness,
review, limitations, admission reasons, and bounded freshness reason codes.
The run view renders those fields in the `Suite evidence trust metadata` table.
Admission reasons and freshness/invalidation reasons are separate columns so an
admission explanation cannot be mistaken for a current trust-state cause.

The feature-on browser tracer proves the rendered path with deliberately
specific values, including an external-provider source, an Ed25519 signer,
verified admission, stale freshness, accepted review, effective expiry,
limitations, a signature-verification admission reason, and the bounded
`signing_key_revoked` invalidation code. The companion feature-off tracer still
renders no preview data and makes no v2 request.

## Evidence boundary

Freshness and invalidation reasons use the server's fixed, bounded
`freshnessReasonCodes` projection. The frontend validates the same closed set
before rendering it. The set includes both warning causes such as
`evidence_expiring` and invalidation causes such as `signing_key_revoked`; the UI
does not mislabel every code as an invalidation. The internal free-text
signing-key revocation rationale is not part of the API response and is not
rendered. This prevents privileged operator text from crossing the public
evidence boundary while still explaining the current trust state.

This checkpoint does not claim that the Assurance v2 preview is generally
enabled, that evidence is automatically decision-eligible, or that the
underlying evaluator capability is publicly available.

## Fresh verification

From `apps/frontend`:

```bash
NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED=true \
NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED=true \
NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED=true \
bunx playwright test tests/assurance-v2-run-child-gate.spec.ts \
  --project=chromium --workers=1 --timeout=60000 --reporter=line
```

Result: one feature-on test passed and the feature-off-only test skipped.

```bash
NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED=true \
NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED=true \
NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED=false \
bunx playwright test tests/assurance-v2-run-child-gate.spec.ts \
  --project=chromium --workers=1 --timeout=60000 --reporter=line
```

Result: one feature-off test passed and the feature-on-only test skipped.

Frontend verification also passed:

- `bun test src/components/evaluations/evidenceTrust.test.ts`: 13 passed.
- `bun test src/lib/api/hooks/useEvaluationWorkbenchV2.test.ts`: 10 passed,
  including rejection of a non-allowlisted reason string.
- `bun test src`: 121 passed.
- `bun run typecheck`: passed.
- `git diff --check`: passed.

From `apps/backend`:

```bash
uv run pytest tests/test_evaluation_workbench_service.py \
  tests/test_evaluation_workbench_routes.py \
  tests/test_evidence_freshness_service.py
```

Result: 195 passed. These tests cover the trust projection, route contract,
bounded operational-freshness codes, and omission of the internal revocation
rationale.

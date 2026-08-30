# P0 frontend three-axis state audit

Date: 2026-08-30

Roadmap item:

> Render execution status, evaluator evidence result, and governance verdict as separate axes.

## Result

Complete on the approved, default-off Assurance v2 run preview. Public rollout
is not implied.

The v2 run contract returns three independent fields:

- `technicalStatus`
- `evidenceOutcome`
- `overallVerdict`

`useEvaluationWorkbenchV2` validates each field independently. The scoped
`/assurance/evaluations/:runId` page passes the validated response to
`EvidenceTrustPanel`, whose presentation contains three labelled axes and
whose rendered panel preserves them as separate cells.

The feature-on Playwright tracer uses intentionally different values so that a
single collapsed status cannot satisfy the test:

- Execution status: `Leased`
- Evaluator evidence result: `Passed with limitations`
- Governance verdict: `Review`

The companion child-gate tracer proves that disabling the v2 run UI still
renders no preview data and issues no v2 request.

## Evidence boundary

This checkpoint does not claim that the Assurance v2 preview is generally
enabled or linked from the legacy Evaluation Runs workbench. Both frontend
flags and both independent backend gates remain required. The legacy v1 run
contract exposes technical status and governance verdict but no evaluator
evidence result, so the client does not invent a third value there.

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

Focused helper and scoped-controller verification also passed: 22 tests, zero
failures.

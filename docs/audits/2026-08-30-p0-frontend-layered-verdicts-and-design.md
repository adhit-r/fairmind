# P0 frontend layered-verdict and design audit

Date: 2026-08-30

Roadmap items:

> Preserve layered suite/modality verdicts plus one overall reviewer verdict.
>
> Update `DESIGN.md` with the three-axis model, admission states, capability
> truth table, worker security envelope, local identity/icon system, and binding
> model.
>
> Preserve the white/black/orange/teal neobrutalist product language; no emoji,
> purple gradients, generic AI visuals, or dashboard rewrite.

## Result

Complete for the approved, default-off Assurance v2 run preview and the P0
frontend workbench surfaces. Public rollout and a product-wide legacy-UI rewrite
are not implied.

`EvidenceTrustPanel` keeps `overallVerdict` as the one labelled run-level
governance verdict. A separate `Layered governance verdicts` region presents
the suite, modality, component, and risk-dimension maps without collapsing them
into that value. Suite keys render byte-for-byte as opaque suite-execution
identifiers; semantic keys on the other axes receive readable labels.

The browser tracer supplies deliberately different values on every layer and
asserts the exact suite-execution key, the modality result, the one overall
verdict label, and the explanatory distinction between the projections and the
reviewer verdict.

## Design truth corrections

`DESIGN.md` now states the contract and capability boundary precisely:

- The three-axis model belongs to Assurance v2; the v1 client does not invent
  an evaluator evidence result.
- Admission, review, and operational freshness remain separate decision inputs.
- Request-state, Execution Envelope, backend evidence, and governance-decision
  bindings are distinct.
- The current capability-state table describes evidence records, not a global
  authoritative product capability registry. That registry remains P5 work.
- P0 defines the worker envelope and tenant-bound service-principal predicate,
  but no worker route, credential, queue, sandbox, or artifact broker. Those
  controls remain P1 work.
- The v2 read contract does not return a Passport revision identifier, so the UI
  does not fabricate one.

The existing local identity and icon rules remain in the design contract.

## Visual-language boundary

The scoped component preserves the established white, black, orange, and teal
neobrutalist system: hard borders, flat fills, strong typography, and no emoji,
purple gradient, glow, glass, or generic AI illustration. It is responsive at
desktop and mobile widths, and long opaque suite identifiers wrap instead of
overflowing.

This checkpoint preserves the language in the P0 surfaces changed by this
roadmap. It does not claim that unrelated legacy frontend routes already comply
or authorize a dashboard rewrite.

## Evidence and capability boundary

The current governance mutation accepts suite verdicts keyed by the run's exact
suite executions. Non-empty modality, component, and risk-dimension decision
claims remain rejected until registered capability-pack authority exists. The
read surface still preserves any contract-valid stored layer values it receives;
rendering those values is not proof that FairMind can currently execute the
corresponding modality or component evaluator.

## Fresh verification

From `apps/frontend`:

- Feature-on child-gate browser tracer: two passed, one skipped, including the
  coherent reviewer-decision fixture at a 390-pixel viewport.
- Feature-off child-gate browser tracer: one passed, two skipped.
- `bunx playwright test tests/evaluation-runs.spec.ts --project=chromium
  --workers=1 --timeout=60000 --retries=0 --reporter=line`: 16 passed.
- Focused frontend unit verification: 23 passed.
- `bun test src`: 121 passed, zero failed.
- `bun run typecheck`: passed.
- Feature-on `bun run build`: passed; 54 of 54 static pages generated. The
  sandbox-only attempt could not fetch the existing Raleway font, so the same
  build was rerun with network access.
- Impeccable static design detector on `EvidenceTrustPanel.tsx`: no findings.
- `git diff --check`: passed.

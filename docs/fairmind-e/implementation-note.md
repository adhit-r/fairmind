# FairMind-E Docs and Research Implementation Note

This slice is documentation and deterministic research scaffolding only. It does not modify backend, frontend, secrets, deployment, credentials, publishing, or external communications.

## Files Added

- `docs/fairmind-e/related-work-table.md`: related-work and standards comparison for FairMind-E as an assurance layer.
- `docs/fairmind-e/refs.bib`: BibTeX entries for the standards, regulatory sources, and environmental AI governance papers used by the docs.
- `docs/fairmind-e/crosswalk.md`: ENV-1..6 mapping to NIST AI RMF functions, ISO/IEC 42001 and 42005 concepts, EU AI Act environmental hooks, and India Sutra 7.
- `docs/fairmind-e/rubric.md`: evidence confidence ladder, uncertainty guidance, gate matrix, risk-tier mapping, and exception path.
- `research/fairmind-e/`: deterministic stdlib smoke harness, configs, generated CSV outputs, SVG plots, tests, and README.

## Implementation Boundaries

- This is a draft research package. HUMAN-only items remain draft support only; no external posting or publication was performed.
- Scripts use Python stdlib only.
- The harness uses synthetic smoke data and must not be reported as production measurement.
- Offsets and RECs are disclosed only as separate fields; they are never subtracted from emissions and never improve confidence or recommendation.
- Location-based and market-based carbon outputs are both generated for every row.

## Validation

Run from the repository root:

```bash
python3 -m unittest research/fairmind-e/tests/test_smoke_harness.py
python3 research/fairmind-e/scripts/run_smoke.py --config-dir research/fairmind-e/configs --output-root research/fairmind-e
```

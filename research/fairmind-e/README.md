# FairMind-E Research Harness

This package contains deterministic research scaffolding for FairMind-E environmental evidence. It is a smoke harness, not a real emissions measurement run.

## Contents

- `configs/*.json`: synthetic workload configs for classical ML training, transformer fine-tuning, RAG inference, batch embeddings, and scenario sweeps.
- `scripts/run_smoke.py`: dependency-free Python runner that emits CSV and SVG artifacts.
- `results/*/smoke.csv`: generated deterministic CSV outputs.
- `plots/*.svg`: generated summary plots.
- `tests/test_smoke_harness.py`: stdlib unit tests for harness determinism and FairMind-E invariants.

## Run

From the repository root:

```bash
python3 research/fairmind-e/scripts/run_smoke.py --config-dir research/fairmind-e/configs --output-root research/fairmind-e
python3 -m unittest research/fairmind-e/tests/test_smoke_harness.py
```

## CSV Contract

Each result row includes:

- workload and run identifiers,
- functional unit,
- duration and `energy_kwh`,
- location-based and market-based carbon intensity,
- `carbon_intensity_basis` as `average` or `marginal`,
- `location_kg_co2e` and `market_kg_co2e`,
- `provenance_class`,
- `uncertainty_pct`,
- `confidence_score`,
- `impact_level`,
- `intensity_vs_baseline`,
- `risk_tier`,
- `recommendation`,
- disclosed offsets.

Offsets are never subtracted from emissions and never improve confidence, tier, or recommendation.

## Invariants Exercised

- Provenance stays categorical and separate from uncertainty.
- Location-based and market-based carbon are both emitted.
- Vendor-reported confidence is capped at `0.60`.
- Moderate impact plus unknown evidence returns `no_go`.
- High-impact measured evidence with documented mitigations returns `conditional_go`.
- Offsets and RECs do not improve gate results.

## Claim Boundaries

The checked-in results are synthetic smoke artifacts for reproducibility and paper-method development. They should not be presented as production measurements, benchmark results, regulatory compliance evidence, or reviewer-study data.

## Paper Gate Evaluation

The `evaluation/` folder contains a minimal hand-labeled paper fixture set that runs against the production FairMind-E domain gate.

Run from the backend environment:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/evaluation/evaluate_gate.py --output-root ../../research/fairmind-e/evaluation
uv run python ../../research/fairmind-e/tests/test_gate_evaluation.py
```

The output is a deterministic CSV, Markdown summary, and SVG plot. This validates gate-label behavior only; it is not a real emissions measurement study.

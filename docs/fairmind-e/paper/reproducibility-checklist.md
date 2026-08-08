# Reproducibility Checklist

## Artifacts

- Labeled fixture: `research/fairmind-e/evaluation/fixtures/paper_gate_cases.json`
- Evaluator: `research/fairmind-e/evaluation/evaluate_gate.py`
- CSV output: `research/fairmind-e/evaluation/results/paper_gate_eval.csv`
- Baseline CSV output: `research/fairmind-e/evaluation/results/paper_baseline_comparison.csv`
- Summary output: `research/fairmind-e/evaluation/results/paper_gate_summary.md`
- Plot output: `research/fairmind-e/evaluation/plots/paper_gate_decisions.svg`
- Baseline plot output: `research/fairmind-e/evaluation/plots/paper_baseline_accuracy.svg`
- Tests: `research/fairmind-e/tests/test_gate_evaluation.py`

## Commands

```bash
cd apps/backend
uv run python ../../research/fairmind-e/evaluation/evaluate_gate.py --output-root ../../research/fairmind-e/evaluation
uv run python ../../research/fairmind-e/tests/test_gate_evaluation.py
```

## Expected Result

- Evaluator exits `0`.
- Unit test exits `0`.
- Summary reports exact label accuracy `14/14`.
- Summary reports baseline exact matches for FairMind-E, carbon-only gate, generic sustainability score, and no environmental gate.

## Non-Goals

- No external API calls.
- No cloud credentials.
- No live workload measurement.
- No publication submission.

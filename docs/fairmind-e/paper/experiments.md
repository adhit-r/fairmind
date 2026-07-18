# Experiments

## Current Experiment

The current paper wedge evaluates 14 hand-labeled cases against the production FairMind-E domain gate.

Command:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/evaluation/evaluate_gate.py --output-root ../../research/fairmind-e/evaluation
```

Outputs:
- `research/fairmind-e/evaluation/results/paper_gate_eval.csv`
- `research/fairmind-e/evaluation/results/paper_baseline_comparison.csv`
- `research/fairmind-e/evaluation/results/paper_gate_summary.md`
- `research/fairmind-e/evaluation/plots/paper_gate_decisions.svg`
- `research/fairmind-e/evaluation/plots/paper_baseline_accuracy.svg`

Current result:
- Exact label accuracy: 14/14
- Recommendation matches: 14/14
- Approval-blocking matches: 14/14

Baseline exact matches:
- FairMind-E: 14/14
- carbon-only gate: 7/14
- generic sustainability score: 6/14
- no environmental gate: 3/14

## Fixture Ablation Table

| Gate or ablation | Exact matches | Recommendation matches | Approval-blocking matches | What the ablation removes |
| --- | ---: | ---: | ---: | --- |
| FairMind-E | 14/14 | 14/14 | 14/14 | Nothing. Full provenance, confidence, impact, mitigation, exception, and offset-aware gate. |
| No environmental gate | 3/14 | 3/14 | 6/14 | All environmental evidence checks. |
| Carbon-only gate | 7/14 | 8/14 | 10/14 | Provenance confidence, mitigation readiness, exception handling, and offset disclosure. |
| Generic sustainability score | 6/14 | 8/14 | 7/14 | Separate provenance, uncertainty, and approval-blocking state. |
| No mitigation review gate | 11/14 | 14/14 | 11/14 | Conditional approvals no longer block when mitigation is missing. |
| No exception path | 13/14 | 14/14 | 13/14 | Owned exceptions no longer unblock conditional review. |
| Offset credit gate | 13/14 | 13/14 | 13/14 | Offsets are allowed to override the release gate. |

Fixture-only interpretation:
- Environmental gating flips 11 of 14 exact decisions relative to no gate.
- Mitigation review accounts for 3 approval-blocking labels.
- Exception handling accounts for 1 approval-blocking label.
- Offset exclusion accounts for 1 recommendation and approval-blocking label.

## Cases Covered

- measured low, medium, and high impact,
- vendor confidence cap,
- tool-estimated high-impact blocking,
- manual weak-confidence blocking,
- unknown provenance no-go,
- baseline intensity bump and lowering,
- offsets that do not rescue a no-go case,
- exception path for conditional review.

## Next Experiment

Move from fixture-label evaluation to P2b workload measurements with quantified error bands. Keep the ablation table as paper-method evidence until real workload measurements are available.

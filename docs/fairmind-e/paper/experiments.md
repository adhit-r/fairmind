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
- `research/fairmind-e/evaluation/results/paper_gate_summary.md`
- `research/fairmind-e/evaluation/plots/paper_gate_decisions.svg`

Current result:
- Exact label accuracy: 14/14
- Recommendation matches: 14/14
- Approval-blocking matches: 14/14

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

Add baseline evaluators:
- no environmental gate,
- carbon-only gate,
- generic sustainability score gate.

Do this only after the fixture labels are stable.

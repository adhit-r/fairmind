# Claims And Evidence

## Claim 1

FairMind-E can encode environmental release decisions as machine-checkable governance evidence.

Evidence:
- `research/fairmind-e/evaluation/fixtures/paper_gate_cases.json`
- `research/fairmind-e/evaluation/results/paper_gate_eval.csv`
- `research/fairmind-e/evaluation/results/paper_baseline_comparison.csv`
- `research/fairmind-e/evaluation/results/paper_gate_summary.md`

Current status: supported only for the hand-labeled fixture set.

## Claim 2

Provenance-capped confidence changes release-gate outcomes compared with generic sustainability scoring.

Evidence:
- Vendor-reported high-confidence claims are capped at `0.60`.
- Unknown provenance forces `0.0` confidence and `no_go`.
- Manual evidence below the estimated band is blocked for medium impact.

Current status: demonstrated by fixtures, not yet by an external benchmark.

Baseline comparison:
- FairMind-E exact matches: 14/14.
- carbon-only gate exact matches: 7/14.
- generic sustainability-score gate exact matches: 6/14.
- no environmental gate exact matches: 3/14.
- no mitigation review gate exact matches: 11/14.
- no exception path exact matches: 13/14.
- offset credit gate exact matches: 13/14.

## Claim 3

Offsets and RECs can be disclosed without improving gate confidence, tier, or recommendation.

Evidence:
- `offsets_do_not_rescue_unknown` case remains `no_go`.
- `offset_credit_gate` changes the offset case to an incorrect `go`, showing why offsets cannot rescue weak evidence.
- Existing backend invariants verify offsets do not change confidence or recommendation.

Current status: implemented and fixture-tested.

## Claim 4

Conditional approval is separable from the environmental recommendation.

Evidence:
- High measured impact can produce `conditional_go`.
- The gate still blocks approval when mitigation is missing.
- Documented mitigation or an owned exception makes the conditional case approvable.
- `no_mitigation_review_gate` drops to 11/14 exact matches; `no_exception_path` drops to 13/14.

Current status: implemented and fixture-tested.

## Do Not Claim Yet

- FairMind-E measures real emissions.
- The provisional thresholds are calibrated.
- The fixture set represents production AI systems.
- The method proves regulatory compliance.

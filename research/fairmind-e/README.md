# FairMind-E Research Harness

This package contains deterministic research scaffolding for FairMind-E environmental evidence. It is a smoke harness, not a real emissions measurement run.

## Contents

- `configs/*.json`: synthetic workload configs for classical ML training, transformer fine-tuning, RAG inference, batch embeddings, and scenario sweeps.
- `scripts/run_smoke.py`: dependency-free Python runner that emits CSV and SVG artifacts.
- `results/*/smoke.csv`: generated deterministic CSV outputs.
- `plots/*.svg`: generated summary plots.
- `tests/`: stdlib unit tests for every package below (smoke, gate evaluation, profiles, measurement, hypotheses).
- `profiles/`: M6 expert-panel assessment profiles plus their generator and answer key.
- `panel/assignment_plan.csv`: counterbalanced rater-to-profile assignment for the panel study.
- `evaluation/`: hand-labeled paper fixture set run against the production gate, with baseline comparisons.
- `measurement/`: the real M5 measurement harness (four workloads, three provenance-mapped methods, mitigation pair-generators).
- `analysis/`: H1-H4 hypothesis statistics and measurement-accuracy analysis (MAPE, Bland-Altman).
- `paper/`: prior-art citation ledger and verified submission calendar.

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

The output is deterministic FairMind-E and baseline CSVs, a Markdown summary, and SVG plots. This validates gate-label behavior only; it is not a real emissions measurement study.

## Expert-Panel Profiles (M6)

The `profiles/` folder contains twelve synthetic assessment profiles for the expert-panel study. The set covers all nine cells of the impact x confidence decision matrix once, plus one extra profile for each conditional_go boundary cell adjacent to no_go (low+unknown and high+measured) and one extra for medium+estimated. Within each doubled cell the two profiles deliberately differ in mitigation or exception state so approval blocking varies while the recommendation does not.

- `profiles/generate_profiles.py`: deterministic stdlib generator with a `--validate` mode that replays every profile through the production domain gate.
- `profiles/profiles.json`: machine-readable profiles with engine-validated expected labels and ENV-1..6 coverage.
- `profiles/PROFILES.md`: printable rater pack (system descriptions and submissions, no answer key).
- `profiles/ANSWER_KEY.md`: expected labels, control coverage, and rationales; keep separate from the rater pack.
- `panel/assignment_plan.csv`: 15 raters (5 GRC, 5 ML_ENG, 5 ESG) x 8 profiles each via a deterministic cyclic rotation; every profile receives exactly 10 ratings with at least 3 raters from each role, and presentation order rotates per rater.

Run from the backend environment:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/profiles/generate_profiles.py --validate
uv run python ../../research/fairmind-e/tests/test_profiles.py
```

Regenerating without validation is stdlib-only and can run from the repository root: `python3 research/fairmind-e/profiles/generate_profiles.py`. The profiles are fictional panel instruments, not real system measurements.

## Expert Panel Instrument (M6)

The `panel/` folder turns the profiles into a runnable two-arm study.
`INSTRUMENT.md` is the operator document: design, the exact question wording,
the export contract, consent text, procedure, and claim boundaries.

The two-arm split is load-bearing. Each rater assesses 8 profiles, 4 under the
baseline arm (system description, boundary, raw measurements, stated source -
no confidence score, tier, matrix, or coverage table) and 4 under the module
arm (all of that plus the full FairMind-E output), on disjoint profile sets so
no rater sees a profile twice. Arms are balanced on both margins: every rater
splits 4/4 and every profile receives exactly 5 baseline and 5 module ratings.
A single-condition instrument makes H2 uncomputable after collection; see
`analysis/DESIGN_NOTES.md`.

```bash
python3 research/fairmind-e/panel/build_instrument.py --check
python3 research/fairmind-e/panel/build_instrument.py
python3 research/fairmind-e/panel/import_responses.py --responses raw_export.csv
python3 research/fairmind-e/tests/test_panel_instrument.py
```

`build_instrument.py` writes `packets/R01.md`..`packets/R15.md` (one stimulus
packet per rater, rendered per arm), `assignment_plan_arms.csv`, and
`gold_checklists.csv` (the H2 denominator: all six ENV controls apply to every
profile in the MVP control set). `import_responses.py` joins the raw survey
export to roles and arms, scores coverage against the gold checklist, drops
module-arm responses that fail the confidence-visibility manipulation check,
and emits `responses/panel_responses.csv` plus `responses/coverage_pre_post.csv`
for `analysis/hypotheses.py`. Malformed rows are reported and excluded, never
imputed.

The packets are fictional instruments, not measurements of real systems, and
the panel measures reviewer behaviour under a controlled contrast rather than
real-world release outcomes.

`RECRUITMENT.md` is the pack for assembling the panel: role definitions and
qualifying criteria, sourcing channels, per-role outreach templates, the
screening questions, the rater-identifier and linking-list protocol that keeps
the anonymity promise in the consent text, a six-week cadence, and the
pre-recruitment checklist (institutional review first). `recruitment_tracker.csv`
tracks outreach by rater identifier and deliberately holds no names; the
name-to-identifier linking list lives outside this repository and is never
committed.

## Measurement Study (M5)

The `measurement/` package is the real measurement harness, distinct from the smoke harness above: `scripts/run_smoke.py` emits deterministic synthetic numbers for package validation and is never study data, while `measurement/harness.py` executes four real workloads on real hardware (W1 sklearn logistic regression, W2 pure-torch tiny transformer fine-tune, W3 numpy embedding plus top-k retrieval, W4 numpy batch embedding) and derives energy and carbon three ways per physical run: `codecarbon` (provenance `tool_estimated`), `cloud_billing` (operator-filled `measurement/cloud_billing_template.csv`, provenance `vendor_reported`), and `manual_flop` (documented per-workload analytic FLOP formulas, provenance `manual`). The same run measured three ways yields different provenance classes, therefore different confidence, and potentially different gate decisions at identical true impact.

```bash
python3 research/fairmind-e/measurement/harness.py --workload all --dry-run
cd apps/backend
uv run python ../../research/fairmind-e/measurement/harness.py --workload all --iterations 5 --mitigations
uv run python ../../research/fairmind-e/tests/test_measurement_harness.py
```

Output contract: the smoke CSV columns plus `measurement_method`, `run_mode`, `method_available`. Honest degradation: when a dependency or billing entry is missing, the row keeps `method_available=false`, `provenance_class=unknown`, and empty measurement and gate fields; nothing is fabricated. Dry runs are labeled `run_mode=dry_run` and are never study data. Mitigation pairs (quantization, region_shift, batching, time_shift) go to a companion `*_mitigations.csv` with pre/post energy and intensity; region and time shifts recompute against the bundled PLACEHOLDER grid table in `measurement/grid_intensity.py`, which must be replaced with an authoritative source before submission. See `measurement/RUNBOOK.md` for the real-hardware protocol; `analysis/hypotheses.py` consumes both CSVs for MAPE/Bland-Altman and H4.

## Hypothesis Analysis (H1-H4)

The `analysis/` folder computes the pre-registered hypothesis statistics and the measurement-accuracy statistics from CSV inputs. It is stdlib-only and prefers scipy/sklearn when importable (the backend environment); every result records which implementation produced it, and bootstrap confidence intervals use a fixed seed so outputs are identical across environments.

Inputs (schemas are documented constants at the top of `analysis/hypotheses.py`; `#`-prefixed lines are comments):

- Panel responses: `rater_id, rater_role (GRC|ML_ENG|ESG), profile_id, recommendation (go|conditional_go|no_go), decision_confidence_1_5, decisive_controls (semicolon-joined ENV-1..ENV-6), time_to_decision_s`.
- Measurement runs: the smoke-harness CSV contract above plus `measurement_method (codecarbon|cloud_billing|manual_flop)`; the optional harness columns `run_mode` and `method_available` are validated when present, and rows with `method_available=false` keep empty fields and are excluded from statistics, never imputed.
- Coverage pre/post: `system_id, coverage_rate_pre, coverage_rate_post`.
- Mitigation pairs: `workload_id, mitigation, intensity_pre, intensity_post, unit` (one shared unit).

H1 uses the explicit ordinal go=0, conditional_go=1, no_go=2, so the expected Spearman correlation with confidence is negative. Expected labels and shown confidence join from `profiles/profiles.json` when present. See `analysis/DESIGN_NOTES.md` for what the survey instrument must capture; H2 requires a baseline condition that a ratings-only panel does not collect.

Run from the repository root:

```bash
python3 research/fairmind-e/analysis/hypotheses.py --panel panel.csv --runs runs.csv --coverage coverage.csv --mitigation mitigations.csv --out results.json
python3 -m unittest research/fairmind-e/tests/test_hypotheses.py
```

Or from the backend environment for the scipy/sklearn implementations:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/analysis/hypotheses.py --runs runs.csv
uv run python ../../research/fairmind-e/tests/test_hypotheses.py
```

Demo inputs live in `analysis/fixtures/` and are labeled SYNTHETIC in both filename and header; they are hand-constructed test vectors, not study data.

## Submission Materials

`paper/PRIOR_ART_AND_VENUES.md` holds the live-verified (2026-07-30) prior-art citation ledger with per-work differentiation lines, the regulatory-framing evidence, and the verified submission calendar (CCAI workshop 2026-08-29; FAccT 2027 full paper 2026-11-03; ICT4S 2027 estimated late January 2027).

For the CCAI paper, `paper/ccai2026/submission.tex` and
`paper/ccai2026/submission.pdf` are the source of truth. The older
`paper/ccai2026/paper.tex` and `paper/ccai2026/paper.pdf` are pre-port legacy
artifacts and should not be edited, submitted, or cited.

# Analysis Design Notes: What the Instruments Must Collect for H1-H4

Status: instrument-design constraint document for the FairMind-E paper.
Audience: whoever writes the reviewer-panel survey and the measurement-study
runbook. `analysis/hypotheses.py` computes the statistics; this document
states what data each hypothesis needs, and names the gap that a
ratings-only panel cannot close.

## The core gap: H2 needs a condition contrast the panel does not collect

H2 claims the FairMind-E module raises ENV control coverage versus a
baseline. That is a pre/post (or A/B) comparison between two CONDITIONS:

- baseline condition: reviewers assess profiles WITHOUT the FairMind-E
  confidence score and decision matrix, and
- module condition: the same assessment WITH the module output visible.

A panel instrument that only collects ratings of profiles with the module
visible produces zero baseline observations. No statistical procedure can
recover `coverage_rate_pre` from a single-condition instrument, and
`hypotheses.py` will not fabricate one: H2 is computed only when a coverage
CSV with both columns is supplied. If the study ships a ratings-only
survey, H2 must be dropped or redesigned; deciding that after data
collection is too late. This is the single most important constraint in
this document.

## H1: confidence -> conservatism (Spearman)

Statistic: Spearman rank correlation between `confidence_score` and the
recommendation ordinal, defined in `hypotheses.py` as go=0,
conditional_go=1, no_go=2, so the pre-specified expectation is a NEGATIVE
rho.

Two evidence levels exist and must not be conflated:

1. Engine-level (measurement runs CSV): the gate's own confidence and
   recommendation per run. This shows the engine is internally monotone.
   It says nothing about human raters.
2. Rater-level (panel responses joined with per-profile confidence): the
   paper's actual H1.

For the rater-level claim the instrument MUST capture, per (rater,
profile) response:

- `rater_id`, `profile_id`, `recommendation` (go|conditional_go|no_go);
- the evidence confidence value that was DISPLAYED to that rater for that
  profile at decision time (the analysis joins it from
  `profiles/profiles.json` `expected.confidence_score`; if the survey tool
  randomizes or hides confidence for any arm, it must log the shown value
  per response, not just the profile id);
- a visibility manipulation check (one item: "did the profile show an
  evidence confidence score?"), so responses where the rater did not see
  the confidence can be excluded rather than diluting the correlation;
- `decision_confidence_1_5` (the rater's own certainty, 1-5) and
  `time_to_decision_s` as secondary variables.

Without per-rater confidence visibility, H1 degrades to the engine-level
consistency check and must be reported as such.

## H2: ENV control coverage (Wilcoxon signed-rank)

Statistic: Wilcoxon signed-rank on paired `coverage_rate_pre` vs
`coverage_rate_post` per system.

Define the task concretely in the instrument:

- Coverage task: for a given system profile, the reviewer lists which of
  the six ENV controls (ENV-1..ENV-6) they would require before release.
  `coverage_rate` = (number of applicable controls the reviewer required) /
  (number of applicable controls per the gold checklist for that profile).
  The gold checklist is fixed per profile before data collection.
- Baseline arm: the reviewer sees only the raw measurement table (energy,
  carbon figures, provenance narrative). No confidence score, no risk
  tier, no decision matrix.
- Module arm: the same profile with the full FairMind-E output
  (confidence score, tier, decision matrix, mitigation status).
- Design: within-subject and counterbalanced (each reviewer does half the
  profiles baseline-first and the other half module-first, order
  randomized per reviewer), or between-subject with random arm assignment
  if contamination is a concern. Within-subject needs a washout or
  distinct profile halves so reviewers do not recall their own answers.
- Pairing unit: the system/profile. `coverage_rate_pre` and
  `coverage_rate_post` are the per-profile coverage rates (aggregated
  across the reviewers assigned to each arm).

Fields the instrument must capture per assessment: `arm`
(baseline|module), `profile_id`, `rater_id`, `controls_required`
(semicolon-joined ENV-1..ENV-6), presentation order index, and time. The
analysis-side CSV contract (`system_id, coverage_rate_pre,
coverage_rate_post`) is the aggregate of that raw capture.

## H3: inter-rater agreement (Cohen and Fleiss kappa)

Statistics: mean pairwise Cohen's kappa and Fleiss' kappa over profiles,
bootstrap 95 percent CI (deterministic seed), target kappa > 0.60.

Instrument requirements:

- At least 2 raters per profile per role (GRC, ML_ENG, ESG) for the
  by-role breakdown; at least 3 raters per profile overall for a stable
  Fleiss estimate. `hypotheses.py` marks by-role agreement as undefined
  when a role has fewer than 2 raters on fewer than 2 shared profiles.
- Ratings must be independent: no discussion between raters before
  submission, and the instrument must not show other raters' answers.
- The label set is fixed and closed (go|conditional_go|no_go); no
  free-text recommendation field.
- `rater_id` must be stable across profiles (pairwise Cohen needs to
  match the same two raters across their common profiles; a minimum
  overlap of 2 shared profiles per pair is enforced).
- Expected labels come from `profiles/profiles.json`
  (`expected.recommendation`) for the modal-vs-expected accuracy readout;
  the panel instrument itself does not collect expected labels.

## H4: mitigation reduces carbon intensity (paired t-test)

H4 is a MEASUREMENT-STUDY artifact, not a panel artifact. The reviewer
survey has no role here; do not add H4 items to it.

The measurement runbook must produce, per (workload, mitigation) pair:

- `intensity_pre` and `intensity_post`: carbon intensity per functional
  unit for the same workload, same functional unit, same hardware and
  region, before and after the mitigation. If the mitigation IS a region
  or scheduling change, hold everything else fixed and document the
  changed variable.
- one shared `unit` string for the whole CSV (the loader rejects mixed
  units because the t-test on raw intensities is meaningless across
  units);
- the `measurement_method` used, and ideally 3 or more repeated runs per
  condition so `intensity_pre`/`intensity_post` are means, not single
  observations;
- `intensity_pre` strictly positive (percent reduction is undefined at
  zero).

Report: paired t-test (pre vs post), mean percent reduction with a
deterministic bootstrap CI, and whether the CI lower bound clears the 20
percent target, which is the claim-strength distinction the paper needs.

## Measurement-accuracy statistics (threshold recalibration)

MAPE (all ordered method pairs) and Bland-Altman (mean bias, 95 percent
limits of agreement) require the same physical run measured by at least
two of codecarbon, cloud_billing, and manual_flop. The harness already
pairs rows on (workload_id, run_id); keep that invariant. MAPE is
asymmetric, so both directions are reported instead of privileging one
method as ground truth; Bland-Altman differences follow the canonical
method order (codecarbon, cloud_billing, manual_flop). Rows with
`method_available=false` are excluded and counted, never imputed.

## What `hypotheses.py` does about the gap today

- H2 runs only when a coverage CSV is supplied; there is no fallback.
- H1 labels each source (`measurement_runs` vs `panel_joined_profiles`)
  and states the interpretation limit in its output.
- H3 reports by-role agreement as undefined until the >= 2 raters per
  role per profile requirement is met.
- H4 reads only the mitigation CSV; panel files are never consulted.

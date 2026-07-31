# FairMind-E M5 Measurement Study Runbook

Operator procedure for the real 5-iteration study on real hardware: 4
workloads x 5 iterations x 3 measurement methods. Follow it start to finish;
every deviation belongs in the run log because it becomes a paper footnote.

This is the REAL harness. The smoke harness (`scripts/run_smoke.py`) emits
synthetic numbers and must never be mixed into the measurement dataset.

## 1. Environment setup

From the repository root, using the backend environment (Python 3.13):

```bash
cd apps/backend
uv add codecarbon            # or: uv pip install codecarbon
uv add torch                 # required only for W2 (transformer_finetune)
uv run python -c "import sklearn, numpy, torch, codecarbon; print('ok')"
```

Any import that fails is not fatal: the harness records the affected
workload or method as `method_available=false` and proceeds with what is
real. Do not fake availability; the honest gap is part of the study.

### 1a. Choose the measurement host deliberately

The host decides what `codecarbon` can actually observe, and therefore what
the study is entitled to claim.

- **Linux with Intel or AMD RAPL, or an NVIDIA GPU**: codecarbon reads
  hardware energy counters. This is the configuration the study wants.
- **Apple Silicon**: there are no RAPL counters, and `powermetrics` needs
  root, so codecarbon logs `No CPU tracking mode found. Falling back on CPU
  load mode` and derives power from CPU utilisation against a TDP constant.
  Confirmed on an Apple M1 Pro on 2026-07-31.

The fallback is still legitimately `tool_estimated` provenance, because it is
exactly that: a tool's estimate. But it is a load model rather than a
hardware reading, so a study run on Apple Silicon compares an estimate
against an estimate, not an estimate against a measurement. If the paper
reports MAPE or Bland-Altman agreement from such a run, it must say so in the
limitations, and the `measured` provenance class stays unclaimed because no
hardware telemetry was available. Prefer a RAPL-capable Linux host for the
study of record.

There is a useful observation here for the paper: the same tool yields
different evidence quality depending on the host, which is the module's own
thesis appearing in its instrumentation.

### 1b. Scale the workloads to the sampling window

In real mode codecarbon samples power every 15 seconds. A workload that
finishes faster than one sampling interval produces an energy figure
extrapolated from almost no samples, which is not a measurement worth
reporting.

Pilot result on an Apple M1 Pro (2026-07-31): W1 at its default config
completed in **0.93 s**, far below the sampling window. Time each workload
once before the real run:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/measurement/harness.py \
    --workload w1 --iterations 1 --output /tmp/pilot.csv
```

If `duration_seconds` is under roughly 60, raise that workload's `repeats`
(or `steps` for W2) through `--config-overrides overrides.json` until each
iteration spans several sampling intervals, and archive the override file
with the results. Every workload should clear this check before the
five-iteration run begins.

Verify the workloads and methods resolve:

```bash
uv run python ../../research/fairmind-e/measurement/harness.py --workload all --dry-run
```

The dry run must finish in under a couple of minutes and write
`research/fairmind-e/results/measurement/dryrun_runs.csv` with
`run_mode=dry_run` on every row. Dry-run CSVs are pipeline-validation
artifacts only; never hand them to the paper analysis as real data.

## 2. Region configuration

Pick the ISO-3166 alpha-3 code of the country where the machine physically
runs and pass it as `--region` (default `IND`). It is used twice:

- codecarbon's `OfflineEmissionsTracker(country_iso_code=...)`,
- the bundled grid-intensity table in `measurement/grid_intensity.py`.

The bundled table is PLACEHOLDER data (see its `DATA_SOURCE_NOTE`). Before
the paper is written, replace it with an authoritative versioned source and
record the edition. Supported placeholder regions: IND, USA, DEU, FRA, SWE.

For the `manual_flop` method also review the two hardware assumptions:

- `--gflops-per-watt` (default 4.0, PLACEHOLDER): effective sustained CPU
  efficiency of the study machine. Derive a defensible value from the CPU's
  measured sustained GFLOP/s divided by package power, and log the derivation.
- `--pue` (default 1.0 for a local machine; use the provider's published PUE
  for cloud hardware).

## 3. Thermal and idle-load protocol

Software power trackers attribute machine power to the tracked process, so
background load and thermal state contaminate measurements.

- Close every other application, browser windows included. Stop backup
  agents, sync clients (Dropbox, iCloud), and scheduled jobs for the window.
- Plug the machine into mains power; disable low-power or battery modes.
- Do not touch the machine while iterations run.
- Warmup discard: the first iteration after a cold start runs with cold
  caches, lazy library initialization, and an unstable thermal state. Run one
  throwaway iteration per workload first (`--iterations 1` to a scratch
  output) and exclude it, or mark iteration 1 for exclusion in analysis.
  Record which convention you used.
- Repeat-run variance: all 5 iterations execute identical seeded work (the
  seed is constant across iterations by design), so spread across iterations
  is measurement noise plus thermal drift, not data variation. If the machine
  visibly throttles (fan floor, rising durations), let it idle back to
  ambient temperature between workloads and note the pause.
- Keep the room conditions roughly constant; note ambient changes.

## 4. The real run

```bash
cd apps/backend
uv run python ../../research/fairmind-e/measurement/harness.py \
    --workload all \
    --iterations 5 \
    --region IND \
    --seed 1337 \
    --output ../../research/fairmind-e/results/measurement/real_runs.csv \
    --mitigations
```

This executes each workload 5 times (each iteration is one physical run
wrapped by codecarbon, with the analytic FLOP row derived from the same run),
then runs the mitigation pair suite (quantization, region_shift, batching,
time_shift) and writes `real_runs_mitigations.csv` alongside the main CSV.

Single-workload reruns use aliases: `--workload w1` (classical ML), `w2`
(transformer fine-tune), `w3` (RAG), `w4` (batch embeddings).

Expected duration per workload at the default real configs (CPU,
hardware-dependent estimates; multiply by 5 iterations):

- W1 classical_ml_training: about 1-3 min per iteration
- W2 transformer_finetune: about 5-15 min per iteration
- W3 rag_inference: about 3-8 min per iteration
- W4 batch_embeddings: about 4-10 min per iteration

Budget roughly a working day including warmups, cooldown pauses, and the
mitigation reruns. If a workload runs far shorter than a minute on your
hardware, raise its `repeats` (or `steps` for W2) via `--config-overrides
overrides.json` so codecarbon's sampling window (15 s in real mode) catches
enough samples; log the override file with the results.

## 5. Cloud billing template (vendor_reported path)

Real billing lags execution by hours to days, which is why this is a
documented manual-entry path and never an API simulation.

1. Run the same workloads on the cloud account (or identify the invoice lines
   covering the study window).
2. Wait for the invoice or the provider's carbon report to post (AWS Customer
   Carbon Footprint, GCP Carbon Footprint export, Azure Emissions Impact
   Dashboard).
3. Copy the figures into `measurement/cloud_billing_template.csv` following
   the column instructions in its comment header. One data row per
   (workload_id, iteration). Leave unknown numeric fields blank - never
   estimate in this file; estimates belong to the manual_flop method.
4. Re-run the billing method only, merging into a separate CSV:

```bash
uv run python ../../research/fairmind-e/measurement/harness.py \
    --workload all --iterations 5 \
    --methods cloud_billing \
    --billing-file ../../research/fairmind-e/measurement/cloud_billing_template.csv \
    --output ../../research/fairmind-e/results/measurement/real_runs_billing.csv
```

Iterations without a billing entry stay `method_available=false` with the
reason in `notes`. That is correct behavior, not an error.

## 6. Handing off to analysis

The analysis stage (`analysis/hypotheses.py`, built in parallel with this
harness) consumes the CSVs directly for MAPE and Bland-Altman comparisons
across methods and for the H4 mitigation deltas:

```bash
uv run python ../../research/fairmind-e/analysis/hypotheses.py \
    --runs ../../research/fairmind-e/results/measurement/real_runs.csv \
    --mitigations ../../research/fairmind-e/results/measurement/real_runs_mitigations.csv
```

(Consult `analysis/hypotheses.py --help` for the authoritative flags once it
lands.) Rules for the handoff:

- Only `run_mode=real` rows are study data; `dry_run` rows validate the
  pipeline and must be excluded.
- Rows with `method_available=false` are honest gaps: keep them in the
  archived CSV, exclude them from MAPE/Bland-Altman, and report their counts.
- Archive alongside the CSVs: the exact command lines, `--config-overrides`
  file if any, machine spec (CPU model, RAM, OS), codecarbon version, and the
  warmup-discard convention used.

# Calibration Attempt, 2026-08-01: Inconclusive

First attempt to calibrate the engine's confidence hierarchy against an
independent power reference. **It did not produce a usable result**, for two
independent reasons, and none of it should reach the paper as a finding. This
record exists so the attempt is not silently repeated the same way.

Artifacts: `m1_runs_ref.csv`, `m1_power_reference.csv`, `m1_calibration.json`,
and the raw log at `~/fairmind-power.txt` (44 MB, 10,535 samples over 2,239 s).

## What was run

Full suite, four workloads by five iterations, with `powermetrics` sampling
CPU and GPU power at 200 ms alongside it. All 20 runs matched power samples;
coverage was complete. The instrumentation worked exactly as designed.

## Why the result is unusable

**1. The host was heavily loaded.** Median background was 64 percent of each
run's observed draw. Nineteen of twenty runs exceeded the 35 percent
contamination threshold and were excluded, leaving one run per method. Three
`classical_ml_training` runs reported contamination of 1.00, meaning the
background estimate met or exceeded the run's own mean draw: the workload
signal was buried entirely.

**2. The direction of the surviving result is the untrustworthy one.** The
single-run comparison favoured the higher-confidence method (median absolute
error 145 percent versus 459 percent), which is a *confirmation* of the
hierarchy. Under contamination that is precisely the outcome that cannot be
believed: both the reference and a whole-machine load tracker include
background work, while a purely analytic estimate does not, so background
pushes the tracker toward the reference for reasons unrelated to measurement
quality. The tooling flagged this itself, recording
`trustworthy_direction: refutation` alongside a verdict that was a
confirmation. We committed in advance to discarding exactly this combination,
and we are discarding it.

Either reason alone would disqualify the run. n = 1 per method has no
statistical content regardless of contamination.

## The tooling flaw this exposed

Local background estimation was supposed to handle a drifting load by
measuring background in the gaps between runs. It only worked for half the
runs: `background_source` reads `local_gap_median` for 10 runs and falls back
to `global_idle_flag` for the other 10, because the harness executed workloads
back to back with no meaningful gaps between them. The 3,838 background samples
that were collected sit mostly before and after the suite, too far from most
runs to inform them.

Fixed: `harness.py` gained `--gap-seconds`, which idles before each run so the
sampler observes a clean stretch of background next to every one of them. A
rerun should pass `--gap-seconds 20`.

## What a valid rerun requires

1. A quiet host. Close browsers, sync clients, containers, and editors, and
   leave the machine alone for the duration. This is the binding constraint;
   the tooling cannot rescue a busy machine.
2. `--gap-seconds 20`, so local background estimation works for every run
   rather than half of them.
3. A fresh idle baseline captured under the same quiet conditions.
4. Advance agreement, again, that a confirmation is only reportable if median
   contamination is low; otherwise only a refutation carries information.

## Status of the paper

Unchanged. The submission does not claim a calibration, and its limitations
paragraph already states that confidence is not calibrated against an
independent reference. That sentence remains accurate and stays.

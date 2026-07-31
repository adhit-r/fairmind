# Independent Power Reference: Operator Protocol

Why this exists: the M5 study compared two estimates against each other with
nothing independent to anchor them, so it could not say whether the engine's
confidence ordering corresponds to anything real. This protocol adds a third,
higher-directness figure sampled from Apple's on-die power counters, which lets
us ask the question the engine cannot answer about itself.

**One step needs you.** `powermetrics` requires root. Everything else is
automated. Nothing here should be run with `sudo` except the single command in
step 3.

## What the reference is, and is not

`powermetrics` reports per-subsystem SoC power (CPU, GPU, ANE) derived from
hardware counters through Apple's own power model. Apple's own manual page says
these values "are estimated and may be inaccurate."

So this is **not ground truth**. It is an independent reference of higher
directness than a CPU-load model: a different measurement family, per
subsystem, sampled at high rate, from the vendor that designed the silicon.
Three limits travel with every number it produces, and the paper must carry
them:

1. **SoC rail, not wall power.** Display, storage, networking, and power-supply
   losses are outside the samplers, so the integrated figure is a lower bound
   on what the machine drew from the socket.
2. **Whole machine, not the process.** Background activity is included.
   Subtracting an idle baseline approximates the workload's marginal draw;
   both the total and the marginal figures are reported and neither is
   privileged.
3. **One-second timestamp resolution.** Sample headers are stamped to the
   second while run boundaries are sub-second, so a run can gain or lose one
   edge sample. At `-i 200` and runs of about 80 s this is under one percent;
   it is the reason the protocol below uses a fine sampling interval and long
   runs.

## Procedure

### 1. Prepare (no sudo)

Close other applications, plug into mains, disable low-power mode, and leave
the machine alone once sampling starts. The samplers see the whole SoC, so
anything else running is attributed to the workload.

### 2. Capture an idle baseline (needs sudo, about two minutes)

With the machine idle and untouched:

```bash
sudo powermetrics --samplers cpu_power,gpu_power -i 200 -n 600 -o ~/fairmind-idle.txt
```

Then compute the mean idle watts (no sudo):

```bash
cd apps/backend
uv run python ../../research/fairmind-e/measurement/power_reference.py \
    --log ~/fairmind-idle.txt --runs /dev/null --baseline-w 0 2>&1 | tail -2
```

Record the mean watts it prints; that value becomes `--baseline-w` in step 4.

### 3. Run the study with sampling alongside it (needs sudo)

Start sampling in one terminal:

```bash
sudo powermetrics --samplers cpu_power,gpu_power -i 200 -o ~/fairmind-power.txt
```

In a second terminal, run the suite as usual:

```bash
cd apps/backend
uv run python ../../research/fairmind-e/measurement/harness.py \
    --workload all --iterations 5 --region IND --seed 1337 \
    --config-overrides ../../research/fairmind-e/measurement/overrides_m1.json \
    --output ../../research/fairmind-e/results/measurement/m1_runs_ref.csv
```

When the harness prints its final line, stop sampling with Ctrl-C in the first
terminal. Start sampling *before* the harness and stop it *after*, so every run
window is covered.

### 4. Integrate the log over each run window (no sudo)

```bash
cd apps/backend
uv run python ../../research/fairmind-e/measurement/power_reference.py \
    --log ~/fairmind-power.txt \
    --runs ../../research/fairmind-e/results/measurement/m1_runs_ref.csv \
    --baseline-w <idle watts from step 2> \
    --out ../../research/fairmind-e/results/measurement/m1_power_reference.csv
```

Check the summary line: every run should have matched samples. Runs reported
unmatched mean the log did not cover them, which invalidates those rows rather
than being a rounding detail.

### 5. Calibrate (no sudo)

```bash
cd apps/backend
uv run python ../../research/fairmind-e/analysis/calibrate_confidence.py \
    --runs ../../research/fairmind-e/results/measurement/m1_runs_ref.csv \
    --reference ../../research/fairmind-e/results/measurement/m1_power_reference.csv \
    --out ../../research/fairmind-e/results/measurement/m1_calibration.json
```

## Reading the result

The output answers one question: does the method the policy trusts more sit
closer to the independent reference?

- **If yes**, the categorical hierarchy is consistent with observed error on
  this host, and the paper can say the ordering is empirically supported,
  bounded by the reference's own caveats.
- **If no**, the ordering is not supported by measurement here. That is the
  more valuable finding and must be reported as such: it would mean the
  confidence hierarchy is an assumption rather than a calibrated instrument,
  which is exactly the criticism the calibration was built to test.

Both outcomes are publishable. The experiment is only worth running if we
commit in advance to reporting whichever one occurs.

## Archive with the results

The idle baseline value and the raw `powermetrics` logs, the harness command
lines, the machine state (applications closed, mains power), and the
`powermetrics` sampling interval. Without the interval and the baseline the
integrated figures cannot be reinterpreted later.

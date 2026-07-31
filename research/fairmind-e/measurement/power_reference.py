"""
Independent power reference from Apple's powermetrics.

Purpose: the study's two estimation methods can only be compared against each
other unless something independent measures the same runs. On Apple Silicon
there is no RAPL and codecarbon falls back to a CPU-load model, so this module
integrates a separately sampled powermetrics log over each run's wall-clock
window to give a third, higher-directness figure.

WHAT THIS IS, PRECISELY. powermetrics reports per-subsystem SoC power (CPU,
GPU, ANE) derived from on-die counters through Apple's own power model. Apple's
manual page states plainly that these values "are estimated and may be
inaccurate". So this is NOT ground truth and must never be described as such.
It is an independent reference of higher directness than a CPU-load model: a
different measurement family, per-subsystem, sampled at high rate, from the
vendor that built the silicon. That is enough to ask the question the engine
cannot currently answer - whether the confidence ordering it assigns tracks
observed error - without claiming to have measured truth.

Three further honesty constraints, all of which the parser preserves:

* SoC rail, not wall power. Display, storage, networking, and PSU losses are
  outside the samplers, so integrated energy is a lower bound on what the
  machine drew from the socket.
* Whole-machine attribution. The samplers report the SoC, not the process, so
  background activity is included. Subtract an idle baseline (``--baseline-w``)
  to approximate the workload's marginal draw, and report both figures.
* Sampling alignment. A sample is counted when its interval midpoint falls
  inside the run window, so partially overlapping edge samples are not double
  counted across adjacent runs.

Usage (the log itself is produced by an operator-run sudo command; see
POWER_REFERENCE.md):

    cd apps/backend
    uv run python ../../research/fairmind-e/measurement/power_reference.py \\
        --log powermetrics.txt \\
        --runs ../../research/fairmind-e/results/measurement/m1_runs.csv \\
        --baseline-w 3.2 \\
        --out ../../research/fairmind-e/results/measurement/m1_power_reference.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# "*** Sampled system activity (Fri Aug  1 00:23:45 2026 +0530) (1002.35ms elapsed) ***"
SAMPLE_HEADER = re.compile(
    r"\*\*\*\s*Sampled system activity\s*\((?P<when>[^)]+?)\)\s*\((?P<elapsed>[\d.]+)ms elapsed\)"
)
POWER_LINE = re.compile(r"^(?P<label>[A-Za-z][A-Za-z0-9 +()]*?)\s+Power:\s*(?P<value>[\d.]+)\s*(?P<unit>[mu]?W)")

#: Labels we integrate. "Combined" is preferred when present because it is
#: Apple's own sum over the subsystems; otherwise CPU+GPU+ANE are added.
COMBINED_LABELS = ("Combined", "Package", "System Total")
COMPONENT_LABELS = ("CPU", "GPU", "ANE")


@dataclass
class Sample:
    epoch: float            # end of the sample interval
    elapsed_s: float
    watts: float
    source_label: str

    @property
    def midpoint(self) -> float:
        return self.epoch - self.elapsed_s / 2.0


def _to_watts(value: float, unit: str) -> float:
    return {"W": 1.0, "mW": 1e-3, "uW": 1e-6}[unit] * value


def _parse_when(text: str) -> float | None:
    """powermetrics stamps each sample with a local time and UTC offset."""
    cleaned = " ".join(text.split())
    for fmt in ("%a %b %d %H:%M:%S %Y %z", "%a %b %d %H:%M:%S %Y"):
        try:
            return datetime.strptime(cleaned, fmt).timestamp()
        except ValueError:
            continue
    return None


def parse_powermetrics(path: Path) -> list[Sample]:
    """Parse a powermetrics text log into power samples.

    Unparseable blocks are skipped rather than guessed at; a log that yields no
    samples raises, because silently returning an empty reference would let a
    calibration run report zero error.
    """
    samples: list[Sample] = []
    when: float | None = None
    elapsed_s = 0.0
    block: dict[str, float] = {}

    def flush() -> None:
        if when is None or not block:
            return
        watts = None
        label = ""
        for key in COMBINED_LABELS:
            if key in block:
                watts, label = block[key], key
                break
        if watts is None:
            present = [k for k in COMPONENT_LABELS if k in block]
            if present:
                watts = sum(block[k] for k in present)
                label = "+".join(present)
        if watts is not None:
            samples.append(Sample(epoch=when, elapsed_s=elapsed_s, watts=watts, source_label=label))

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            header = SAMPLE_HEADER.search(line)
            if header:
                flush()
                block = {}
                when = _parse_when(header.group("when"))
                elapsed_s = float(header.group("elapsed")) / 1000.0
                continue
            match = POWER_LINE.match(line.strip())
            if match:
                label = match.group("label").strip()
                watts = _to_watts(float(match.group("value")), match.group("unit"))
                # Normalise "Combined Power (CPU + GPU + ANE)" to "Combined".
                key = next((k for k in COMBINED_LABELS + COMPONENT_LABELS if label.startswith(k)), None)
                if key:
                    block[key] = watts
    flush()

    if not samples:
        raise SystemExit(
            f"no power samples parsed from {path}. Expected powermetrics text output "
            "containing '*** Sampled system activity ...' headers and 'CPU Power: N mW' lines."
        )
    return samples


def integrate(samples: list[Sample], start: float, end: float) -> tuple[float, int, float]:
    """Integrate power over [start, end].

    Returns (kWh, sample_count, mean_watts). A sample counts when its interval
    midpoint lies inside the window, so no sample is attributed to two runs.
    """
    inside = [s for s in samples if start <= s.midpoint <= end]
    if not inside:
        return 0.0, 0, 0.0
    joules = sum(s.watts * s.elapsed_s for s in inside)
    mean_w = statistics.mean(s.watts for s in inside)
    return joules / 3_600_000.0, len(inside), mean_w


def idle_baseline(samples: list[Sample], start: float, end: float) -> float:
    """Mean watts over an idle window, for marginal-energy attribution."""
    _, count, mean_w = integrate(samples, start, end)
    if count == 0:
        raise SystemExit("no samples inside the idle-baseline window")
    return mean_w


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path, help="powermetrics text log")
    parser.add_argument("--runs", required=True, type=Path, help="measurement CSV with started_at/ended_at")
    parser.add_argument(
        "--baseline-w",
        type=float,
        default=None,
        help="idle SoC watts to subtract for marginal attribution; both figures are reported",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    samples = parse_powermetrics(args.log)
    span = (min(s.midpoint for s in samples), max(s.epoch for s in samples))

    with args.runs.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    seen: set[tuple[str, str]] = set()
    out_rows: list[dict[str, object]] = []
    unmatched = 0
    for row in rows:
        if row.get("method_available") != "true":
            continue
        start_s, end_s = (row.get("started_at") or "").strip(), (row.get("ended_at") or "").strip()
        if not start_s or not end_s:
            continue
        key = (row["workload_id"], row["run_id"])
        if key in seen:  # codecarbon and manual rows share one physical run
            continue
        seen.add(key)
        start, end = float(start_s), float(end_s)
        kwh, count, mean_w = integrate(samples, start, end)
        if count == 0:
            unmatched += 1
            continue
        duration = end - start
        marginal = ""
        if args.baseline_w is not None:
            marginal_kwh = max(0.0, (mean_w - args.baseline_w) * duration / 3_600_000.0)
            marginal = f"{marginal_kwh:.6e}"
        out_rows.append(
            {
                "workload_id": row["workload_id"],
                "run_id": row["run_id"],
                "duration_seconds": f"{duration:.3f}",
                "n_power_samples": count,
                "mean_watts": f"{mean_w:.3f}",
                "reference_kwh_total": f"{kwh:.6e}",
                "reference_kwh_marginal": marginal,
                "source": f"powermetrics {samples[0].source_label} rail, SoC only, vendor power model",
            }
        )

    fieldnames = [
        "workload_id", "run_id", "duration_seconds", "n_power_samples", "mean_watts",
        "reference_kwh_total", "reference_kwh_marginal", "source",
    ]
    if args.out:
        with args.out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"wrote {args.out}")
    else:
        print(",".join(fieldnames))
        for r in out_rows:
            print(",".join(str(r[f]) for f in fieldnames))

    print(f"parsed {len(samples)} power samples spanning {span[1] - span[0]:.1f}s")
    print(f"matched {len(out_rows)} runs; {unmatched} runs had no samples in their window")
    if unmatched:
        print("unmatched runs usually mean the power log did not cover the whole study")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

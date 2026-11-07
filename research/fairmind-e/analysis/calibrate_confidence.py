"""
Does assigned confidence track observed error?

This is the experiment the engine cannot currently answer about itself. The
policy assigns a confidence score per provenance class as a constant: 0.72 for
a software tracker, 0.30 for an analytic FLOP model. Nothing so far tests
whether that ordering corresponds to anything real. If the higher-confidence
method is not in fact closer to an independent reference, the hierarchy is an
opinion encoded in Python and the paper should say so.

Given a power reference produced by measurement/power_reference.py, this
computes per-method error against it and reports whether error ordering matches
confidence ordering. Two directions are possible and both are publishable:

* Confirmation: the method the policy trusts more is measurably closer. The
  hierarchy earns its place, with the caveat that the reference is itself a
  vendor power model rather than truth.
* Refutation: the ordering is wrong or indistinguishable. Then the paper
  reports that the categorical hierarchy is not supported by measurement on
  this host, which is a more valuable finding than another agreement statistic.

The reference is NOT ground truth (see power_reference.py). Errors here are
disagreements with an independent, higher-directness estimate, and every
output label says so.

Usage:

    cd apps/backend
    uv run python ../../research/fairmind-e/analysis/calibrate_confidence.py \\
        --runs ../../research/fairmind-e/results/measurement/m1_runs.csv \\
        --reference ../../research/fairmind-e/results/measurement/m1_power_reference.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

#: Which reference column to compare against. Total SoC energy is the default
#: because marginal attribution depends on an idle baseline the operator may
#: not have captured.
REFERENCE_COLUMNS = ("reference_kwh_total", "reference_kwh_marginal")


# Below this many usable runs per method the ordering verdict is withheld.
MIN_N_PER_METHOD = 5

def load_reference(
    path: Path, column: str, max_contamination: float | None
) -> tuple[dict[tuple[str, str], float], dict[str, object]]:
    """Load reference energies, optionally dropping background-dominated runs.

    Returns (values, contamination report). Runs whose background draw is a
    large fraction of their total are excluded rather than silently averaged
    in: on a busy machine those rows describe the machine, not the workload.
    """
    out: dict[tuple[str, str], float] = {}
    ratios: list[float] = []
    excluded: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get(column) or "").strip()
            if not raw:
                continue
            key = (row["workload_id"], row["run_id"])
            ratio_raw = (row.get("contamination_ratio") or "").strip()
            ratio = float(ratio_raw) if ratio_raw else None
            if ratio is not None:
                ratios.append(ratio)
                if max_contamination is not None and ratio > max_contamination:
                    excluded.append({**{"workload_id": key[0], "run_id": key[1]},
                                     "contamination_ratio": ratio})
                    continue
            out[key] = float(raw)
    report: dict[str, object] = {
        "threshold": max_contamination,
        "n_excluded": len(excluded),
        "excluded": excluded[:20],
        "median_contamination": round(statistics.median(ratios), 4) if ratios else None,
        "max_contamination": round(max(ratios), 4) if ratios else None,
    }
    return out, report


def load_runs(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r.get("method_available") == "true"]


def spearman(xs: list[float], ys: list[float]) -> tuple[float, int]:
    """Rank correlation with average ranks for ties; stdlib only."""
    n = len(xs)
    if n < 3:
        return float("nan"), n

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        out = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return (num / den if den else float("nan")), n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--reference-column", default=REFERENCE_COLUMNS[0], choices=REFERENCE_COLUMNS)
    parser.add_argument(
        "--max-contamination",
        type=float,
        default=0.35,
        help="drop runs whose background exceeds this fraction of their draw",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    reference, contamination = load_reference(
        args.reference, args.reference_column, args.max_contamination
    )
    if not reference:
        raise SystemExit(f"no usable values in {args.reference} column {args.reference_column}")
    runs = load_runs(args.runs)

    per_method: dict[str, list[dict[str, float]]] = defaultdict(list)
    confidence_of: dict[str, float] = {}
    provenance_of: dict[str, str] = {}
    skipped = 0

    for row in runs:
        key = (row["workload_id"], row["run_id"])
        ref = reference.get(key)
        raw = (row.get("energy_kwh") or "").strip()
        if ref is None or not raw or ref <= 0:
            skipped += 1
            continue
        method = row["measurement_method"]
        estimate = float(raw)
        confidence_of[method] = float(row["confidence_score"])
        provenance_of[method] = row["provenance_class"]
        per_method[method].append(
            {
                "estimate": estimate,
                "reference": ref,
                "abs_pct_error": abs(estimate - ref) / ref * 100.0,
                "signed_pct_error": (estimate - ref) / ref * 100.0,
                # log ratio is undefined for a zero or negative estimate
                "log_ratio": math.log(estimate / ref) if estimate > 0 else None,
            }
        )

    summary: dict[str, object] = {
        "reference": {
            "file": str(args.reference),
            "column": args.reference_column,
            "caveat": (
                "powermetrics reports per-subsystem SoC power from Apple's own model; the "
                "vendor documents these values as estimated. This is an independent, "
                "higher-directness reference, not ground truth, and it excludes display, "
                "storage, networking, and PSU losses."
            ),
        },
        "n_runs_skipped": skipped,
        "contamination": contamination,
        "methods": {},
    }

    # The confound that matters when the host is busy. Both the reference and a
    # CPU-load tracker observe the whole machine, so background work inflates
    # them together while leaving a purely analytic estimate untouched. That
    # pushes the tracker to look closer to the reference for a reason unrelated
    # to measurement quality, which would manufacture a flattering confirmation.
    median_c = contamination.get("median_contamination")
    if median_c is not None and median_c > 0.15:
        summary["validity_warning"] = (
            f"background load is a median {median_c:.0%} of observed draw. Both the "
            "reference and a whole-machine load tracker include that background, while "
            "an analytic estimate does not, so this comparison is biased toward the "
            "tracker for reasons unrelated to measurement quality. A confirmation of "
            "the confidence ordering under these conditions is not trustworthy; a "
            "refutation is, since the bias runs the other way. Prefer the marginal "
            "reference column and re-run on a quiet host before publishing a positive "
            "result."
        )

    rows_for_rank: list[tuple[float, float]] = []
    for method, records in sorted(per_method.items()):
        errors = [r["abs_pct_error"] for r in records]
        signed = [r["signed_pct_error"] for r in records]
        summary["methods"][method] = {
            "provenance_class": provenance_of[method],
            "assigned_confidence": confidence_of[method],
            "n": len(records),
            "median_abs_pct_error": round(statistics.median(errors), 2),
            "mean_abs_pct_error": round(statistics.mean(errors), 2),
            "median_signed_pct_error": round(statistics.median(signed), 2),
            "direction": "over-estimates" if statistics.median(signed) > 0 else "under-estimates",
            "mean_log_ratio": (
                round(statistics.mean(logs), 4)
                if (logs := [r["log_ratio"] for r in records if r["log_ratio"] is not None])
                else None
            ),
        }
        for r in records:
            rows_for_rank.append((confidence_of[method], r["abs_pct_error"]))

    # The pre-registered question: higher confidence should mean lower error,
    # so the expected correlation is negative.
    if rows_for_rank:
        rho, n = spearman([c for c, _ in rows_for_rank], [e for _, e in rows_for_rank])
        summary["confidence_vs_error"] = {
            "spearman_rho": None if math.isnan(rho) else round(rho, 4),
            "n": n,
            "expected_sign": "negative (higher confidence should mean lower error)",
            "note": (
                "with two provenance classes this is a two-group comparison expressed as a "
                "rank correlation; it tests ordering, not a dose-response relationship"
            ),
        }

    methods = summary["methods"]
    if len(methods) >= 2 and min(m["n"] for m in methods.values()) < MIN_N_PER_METHOD:
        summary["verdict"] = {
            "ordering_holds": None,
            "n_per_method": {name: m["n"] for name, m in methods.items()},
            "min_n_per_method": MIN_N_PER_METHOD,
            "reading": (
                f"insufficient samples: at least {MIN_N_PER_METHOD} usable runs per method "
                "are required before the confidence ordering can be judged; no verdict."
            ),
        }
    elif len(methods) >= 2:
        ordered = sorted(methods.items(), key=lambda kv: -kv[1]["assigned_confidence"])
        (hi_name, hi), (lo_name, lo) = ordered[0], ordered[-1]
        hi_err, lo_err = hi["median_abs_pct_error"], lo["median_abs_pct_error"]
        summary["verdict"] = {
            "higher_confidence_method": hi_name,
            "lower_confidence_method": lo_name,
            "median_abs_pct_error_higher": hi_err,
            "median_abs_pct_error_lower": lo_err,
            "ordering_holds": hi_err < lo_err,
            "trustworthy_direction": (
                "refutation" if "validity_warning" in summary else "either"
            ),
            "reading": (
                f"the method the policy trusts more ({hi_name}, confidence "
                f"{hi['assigned_confidence']}) is {'closer to' if hi_err < lo_err else 'NOT closer to'} "
                f"the independent reference than {lo_name} (confidence {lo['assigned_confidence']}): "
                f"median absolute error {hi_err}% vs {lo_err}%. "
                + (
                    "The assigned ordering is consistent with observed error on this host."
                    if hi_err < lo_err
                    else "The assigned ordering is NOT supported by measurement on this host, "
                    "which the paper must report as a refutation of the categorical hierarchy."
                )
            ),
        }

    text = json.dumps(summary, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

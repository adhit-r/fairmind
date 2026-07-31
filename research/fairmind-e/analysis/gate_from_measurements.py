"""
Replay real measurement runs through the production decision engine.

The measurement harness records its own gate columns using the smoke module's
helper functions and its own kilogram thresholds, which are not the engine that
ships in the product. Any claim about what the gate decides therefore has to be
recomputed here, against ``src.domain.environmental``, exactly as the fixture
evaluation does. Otherwise the paper would be reporting a reimplementation.

Reads a measurement CSV, maps each available row to an engine assessment
payload, runs the production engine, and reports whether the release decision
depends on the measurement method for the same physical run.

Run from the backend environment so the engine is importable:

    cd apps/backend
    uv run python ../../research/fairmind-e/analysis/gate_from_measurements.py \
        --runs ../../research/fairmind-e/results/measurement/m1_runs.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Each workload's lifecycle phase, and how many functional units one run
# covers, so a per-unit intensity can be derived for the inference phases.
# Unit counts come from the workload REAL_CONFIG multiplied by the overrides
# actually used for the run; they are passed in rather than guessed.
WORKLOAD_PHASE = {
    "classical_ml_training": "training",
    "transformer_finetune": "fine_tune",
    "rag_inference": "inference",
    "batch_embeddings": "inference",
}


def load_engine():
    """Import the production engine, putting the backend root on the path.

    Mirrors evaluation/evaluate_gate.py so this script runs from anywhere.
    """
    repo_root = Path(__file__).resolve().parents[3]
    backend_root = repo_root / "apps" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    try:
        from src.domain.environmental import run_assessment
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            f"production engine not importable from {backend_root}; "
            "run with the backend environment (cd apps/backend && uv run python ...)"
        ) from exc
    return run_assessment


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_assessment(row: dict[str, str], units_per_run: dict[str, float]) -> dict[str, Any]:
    """Map one measurement row onto an engine assessment payload."""
    workload = row["workload_id"]
    phase = WORKLOAD_PHASE.get(workload, "inference")
    location = to_float(row.get("location_kg_co2e"))
    market = to_float(row.get("market_kg_co2e"))
    kwh = to_float(row.get("energy_kwh"))

    metrics: dict[str, Any] = {
        "total_kwh": kwh,
        "total_kg_co2e_location": location,
        "total_kg_co2e_market": market if market is not None else location,
    }

    # The inference phases are tiered per functional unit, so convert the run
    # total into the per-unit figure the engine expects.
    units = units_per_run.get(workload)
    if phase == "inference" and location is not None and units:
        metrics["kg_co2e_per_1000_requests"] = location / (units / 1000.0)

    return {
        "lifecycle_phase": phase,
        "functional_unit": row.get("functional_unit") or "run",
        "boundary": f"{workload} measured run, scope 2, single host",
        "provenance_class": row.get("provenance_class") or "unknown",
        "measurement_source": row.get("measurement_method") or "unknown",
        "uncertainty_pct": to_float(row.get("uncertainty_pct")),
        "metrics": metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument(
        "--units",
        type=Path,
        default=None,
        help="optional JSON mapping workload_id to functional units per run",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    run_assessment = load_engine()

    units_per_run: dict[str, float] = {}
    if args.units and args.units.exists():
        units_per_run = json.loads(args.units.read_text(encoding="utf-8"))

    with args.runs.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("method_available") == "true"]

    results: list[dict[str, Any]] = []
    for row in rows:
        assessment = build_assessment(row, units_per_run)
        try:
            engine = run_assessment(assessment)
        except ValueError as exc:
            results.append(
                {
                    "workload_id": row["workload_id"],
                    "run_id": row["run_id"],
                    "measurement_method": row["measurement_method"],
                    "engine_error": str(exc),
                }
            )
            continue
        results.append(
            {
                "workload_id": row["workload_id"],
                "run_id": row["run_id"],
                "measurement_method": row["measurement_method"],
                "provenance_class": engine.provenance_class,
                "confidence_score": engine.confidence_score,
                "confidence_band": engine.confidence_band,
                "impact_tier": engine.impact_tier,
                "engine_recommendation": engine.recommendation,
                "harness_recommendation": row.get("recommendation"),
                "agrees_with_harness": engine.recommendation == row.get("recommendation"),
            }
        )

    # Does the decision depend on how the same physical run was measured?
    by_run: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for r in results:
        if "engine_recommendation" in r:
            by_run[(r["workload_id"], r["run_id"])][r["measurement_method"]] = r[
                "engine_recommendation"
            ]
    paired = {k: v for k, v in by_run.items() if len(v) > 1}
    divergent = {k: v for k, v in paired.items() if len(set(v.values())) > 1}

    agree = [r for r in results if r.get("agrees_with_harness") is True]
    disagree = [r for r in results if r.get("agrees_with_harness") is False]
    errors = [r for r in results if "engine_error" in r]

    summary = {
        "rows_evaluated": len(results),
        "engine_errors": len(errors),
        "paired_runs": len(paired),
        "runs_where_method_changed_the_decision": len(divergent),
        "engine_vs_harness_agreement": {
            "agree": len(agree),
            "disagree": len(disagree),
            "note": (
                "the harness records gate columns from the smoke reimplementation "
                "with its own kilogram thresholds; the engine column is the "
                "production decision and is the one to cite"
            ),
        },
        "engine_recommendation_counts": {},
        "by_method": {},
        "results": results,
    }

    counts: dict[str, int] = defaultdict(int)
    per_method: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in results:
        if "engine_recommendation" in r:
            counts[r["engine_recommendation"]] += 1
            per_method[r["measurement_method"]][r["engine_recommendation"]] += 1
    summary["engine_recommendation_counts"] = dict(counts)
    summary["by_method"] = {k: dict(v) for k, v in per_method.items()}

    text = json.dumps(summary, indent=2, sort_keys=False)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

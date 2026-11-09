"""FairMind-E M5 measurement harness CLI.

Runs the four real workloads (W1 classical ML, W2 transformer fine-tune,
W3 RAG retrieval, W4 batch embedding) for N iterations each and derives
energy and carbon through three measurement methods per run:

- ``codecarbon``    -> provenance ``tool_estimated``
- ``cloud_billing`` -> provenance ``vendor_reported`` (operator-supplied CSV)
- ``manual_flop``   -> provenance ``manual``

Every iteration executes the workload exactly once; the codecarbon and
manual_flop rows describe that same physical run, and the cloud_billing row
joins the operator's invoice figures for the matching (workload, iteration).
This produces the paper's core dataset: the same workload measured three ways
yields different provenance classes, therefore different confidence, and
potentially different gate decisions at identical true impact.

Output CSV: the smoke-harness column contract (see ``scripts/run_smoke.py``)
plus ``measurement_method``, ``run_mode``, and ``method_available``. Rows
whose method could not produce a real figure keep ``method_available=false``,
``provenance_class=unknown``, and empty measurement and gate fields; nothing
is fabricated. ``--dry-run`` executes tiny config sizes end-to-end and labels
every row ``run_mode=dry_run``.

Usage examples (from the repository root):

    python3 research/fairmind-e/measurement/harness.py --workload w1 --dry-run
    python3 research/fairmind-e/measurement/harness.py --workload all \
        --iterations 5 --region IND --output results.csv --mitigations

See ``measurement/RUNBOOK.md`` for the real-hardware study procedure.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import pathlib
import sys
import time
from typing import Any

if __package__ in (None, ""):
    # Executed as a script: make the package importable so submodule identity
    # stays "measurement.*" for every consumer, including the test seam.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from measurement import grid_intensity, methods
from measurement.workloads import load_workloads, resolve_workload_ids

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BILLING_FILE = pathlib.Path(__file__).resolve().parent / "cloud_billing_template.csv"
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "results" / "measurement"

# Study-level impact thresholds on kg CO2e per run (market-based when present,
# otherwise location-based). Harness defaults for the paper study; documented
# in the README so analysis can restate them.
IMPACT_LOW_MAX_KG = 0.5
IMPACT_MODERATE_MAX_KG = 5.0


def _load_smoke_module():
    """Load scripts/run_smoke.py so gate and confidence rules stay single-sourced."""

    path = PACKAGE_ROOT / "scripts" / "run_smoke.py"
    spec = importlib.util.spec_from_file_location("fairmind_e_run_smoke_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load smoke harness at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SMOKE = _load_smoke_module()

MEASUREMENT_CSV_COLUMNS = list(_SMOKE.CSV_COLUMNS) + [
    "measurement_method",
    "run_mode",
    "method_available",
    # Wall-clock window of the workload itself, so an independently sampled
    # power log can be integrated over exactly the interval it occupied.
    "started_at",
    "ended_at",
]


def fmt(value: float | None, spec: str) -> str:
    """Format a numeric cell; None means 'no real figure' and stays empty."""

    if value is None:
        return ""
    return format(value, spec)


def impact_level_for_kg(kg_co2e: float) -> str:
    if kg_co2e < IMPACT_LOW_MAX_KG:
        return "low"
    if kg_co2e < IMPACT_MODERATE_MAX_KG:
        return "moderate"
    return "high"


def build_row(
    *,
    workload_id: str,
    functional_unit: str,
    run_id: str,
    run_mode: str,
    method: str,
    method_available: bool,
    duration_seconds: float | None,
    energy_kwh: float | None,
    location_intensity: float | None,
    market_intensity: float | None,
    carbon_intensity_basis: str,
    location_kg: float | None,
    market_kg: float | None,
    mitigation_readiness: str,
    notes: str,
    started_at: float | None = None,
    ended_at: float | None = None,
    degraded: bool = False,
) -> dict[str, str]:
    """Assemble one contract row. Empty strings mark absent real figures.

    ``degraded`` marks a tracker that fell back to a load x TDP model; its row
    is classed ``manual`` because that is what the figure is in kind.
    """

    if method_available:
        provenance = "manual" if degraded else methods.PROVENANCE_BY_METHOD[method]
        uncertainty = methods.UNCERTAINTY_PCT_BY_METHOD[method]
        confidence = _SMOKE.confidence_score(provenance, float(uncertainty))
        gate_kg = market_kg if market_kg is not None else location_kg
        if gate_kg is not None:
            impact = impact_level_for_kg(gate_kg)
            recommendation = _SMOKE.recommendation_for(
                impact, confidence, mitigation_readiness
            )
            risk_tier = _SMOKE.risk_tier_for(impact, recommendation)
        else:
            impact, recommendation, risk_tier = "", "", ""
    else:
        provenance = "unknown"
        uncertainty = 100
        confidence = 0.0
        impact, recommendation, risk_tier = "", "", ""

    return {
        "workload_id": workload_id,
        "run_id": run_id,
        "method": methods.INSTRUMENT_BY_METHOD[method],
        "functional_unit": functional_unit,
        "duration_seconds": fmt(duration_seconds, ".3f"),
        "energy_kwh": fmt(energy_kwh, ".6g"),
        "location_carbon_intensity_g_co2e_per_kwh": fmt(location_intensity, ".1f"),
        "market_carbon_intensity_g_co2e_per_kwh": fmt(market_intensity, ".1f"),
        "carbon_intensity_basis": carbon_intensity_basis if method_available else "",
        "location_kg_co2e": fmt(location_kg, ".6g"),
        "market_kg_co2e": fmt(market_kg, ".6g"),
        "provenance_class": provenance,
        "uncertainty_pct": str(int(uncertainty)),
        "confidence_score": f"{confidence:.2f}",
        "impact_level": impact,
        "intensity_vs_baseline": "",
        "risk_tier": risk_tier,
        "recommendation": recommendation,
        "mitigation_readiness": mitigation_readiness,
        "offsets_retired_kg_co2e": "0.000",
        "notes": notes,
        "measurement_method": method,
        "run_mode": run_mode,
        "method_available": "true" if method_available else "false",
        "started_at": "" if started_at is None else f"{started_at:.3f}",
        "ended_at": "" if ended_at is None else f"{ended_at:.3f}",
    }


def _unavailable_row(
    *,
    workload_id: str,
    functional_unit: str,
    run_id: str,
    run_mode: str,
    method: str,
    reason: str,
    duration_seconds: float | None = None,
) -> dict[str, str]:
    return build_row(
        workload_id=workload_id,
        functional_unit=functional_unit,
        run_id=run_id,
        run_mode=run_mode,
        method=method,
        method_available=False,
        duration_seconds=duration_seconds,
        energy_kwh=None,
        location_intensity=None,
        market_intensity=None,
        carbon_intensity_basis="",
        location_kg=None,
        market_kg=None,
        mitigation_readiness="none",
        notes=f"method unavailable: {reason}",
    )


def _codecarbon_row(
    *,
    module: Any,
    run_id: str,
    run_mode: str,
    region: str,
    run_result: methods.RunResult,
) -> dict[str, str]:
    if not run_result.codecarbon_available:
        return _unavailable_row(
            workload_id=module.WORKLOAD_ID,
            functional_unit=module.FUNCTIONAL_UNIT,
            run_id=run_id,
            run_mode=run_mode,
            method="codecarbon",
            reason=run_result.codecarbon_reason,
            duration_seconds=run_result.duration_seconds,
        )

    energy = run_result.codecarbon_energy_kwh
    emissions = run_result.codecarbon_emissions_kg
    implied_intensity = None
    if energy and energy > 0 and emissions is not None:
        implied_intensity = emissions / energy * 1000.0
    notes = (
        f"{run_result.codecarbon_reason}; OfflineEmissionsTracker "
        f"country={region}; market-based figures not provided by the tool"
    )
    if run_result.codecarbon_degraded:
        notes += (
            "; DEGRADED: codecarbon fell back to cpu_load mode (CPU load x TDP "
            "constant, no hardware counters); provenance downgraded to manual"
        )
    return build_row(
        degraded=run_result.codecarbon_degraded,
        workload_id=module.WORKLOAD_ID,
        functional_unit=module.FUNCTIONAL_UNIT,
        run_id=run_id,
        run_mode=run_mode,
        method="codecarbon",
        method_available=True,
        duration_seconds=run_result.duration_seconds,
        energy_kwh=energy,
        location_intensity=implied_intensity,
        market_intensity=None,
        carbon_intensity_basis="average",
        location_kg=emissions,
        market_kg=None,
        mitigation_readiness="none",
        notes=notes,
        started_at=run_result.started_at,
        ended_at=run_result.ended_at,
    )


def _manual_row(
    *,
    module: Any,
    config: dict[str, Any],
    run_id: str,
    run_mode: str,
    region: str,
    gflops_per_watt: float,
    pue: float,
    duration_seconds: float | None,
    started_at: float | None = None,
    ended_at: float | None = None,
) -> dict[str, str]:
    flops = module.flop_estimate(config)
    energy = methods.manual_energy_kwh(flops, gflops_per_watt, pue)
    intensities = grid_intensity.intensities_for(region)
    location_kg = energy * intensities["location"] / 1000.0
    market_kg = energy * intensities["market"] / 1000.0
    notes = (
        f"analytic FLOP model: {flops:.3e} FLOPs; assumed "
        f"{gflops_per_watt:g} GFLOP/s per watt, PUE {pue:g} (PLACEHOLDER "
        f"assumptions); grid table {region} {grid_intensity.DATA_SOURCE_YEAR} "
        "PLACEHOLDER"
    )
    return build_row(
        workload_id=module.WORKLOAD_ID,
        functional_unit=module.FUNCTIONAL_UNIT,
        run_id=run_id,
        run_mode=run_mode,
        method="manual_flop",
        method_available=True,
        duration_seconds=duration_seconds,
        energy_kwh=energy,
        location_intensity=intensities["location"],
        market_intensity=intensities["market"],
        carbon_intensity_basis="average",
        location_kg=location_kg,
        market_kg=market_kg,
        mitigation_readiness="none",
        notes=notes,
        started_at=started_at,
        ended_at=ended_at,
    )


def _billing_row(
    *,
    module: Any,
    run_id: str,
    run_mode: str,
    iteration: int,
    billing: methods.BillingData,
    billing_path: pathlib.Path,
) -> dict[str, str]:
    workload_id = module.WORKLOAD_ID
    if not billing.available:
        return _unavailable_row(
            workload_id=workload_id,
            functional_unit=module.FUNCTIONAL_UNIT,
            run_id=run_id,
            run_mode=run_mode,
            method="cloud_billing",
            reason=billing.reason,
        )

    entry = billing.entries.get((workload_id, iteration))
    if entry is None:
        return _unavailable_row(
            workload_id=workload_id,
            functional_unit=module.FUNCTIONAL_UNIT,
            run_id=run_id,
            run_mode=run_mode,
            method="cloud_billing",
            reason=(
                f"no operator billing entry for iteration {iteration} in "
                f"{billing_path.name}; billing lags hours to days - fill the "
                "template once invoices post and re-run with "
                "--methods cloud_billing"
            ),
        )

    energy = entry.get("energy_kwh")
    location_kg = entry.get("location_kg_co2e")
    market_kg = entry.get("market_kg_co2e")
    if energy is None and location_kg is None and market_kg is None:
        return _unavailable_row(
            workload_id=workload_id,
            functional_unit=module.FUNCTIONAL_UNIT,
            run_id=run_id,
            run_mode=run_mode,
            method="cloud_billing",
            reason=(
                "billing entry present but has neither energy_kwh nor any "
                "kg_co2e figure"
            ),
        )

    basis = entry.get("carbon_intensity_basis") or "average"
    note_parts = ["operator-supplied billing figures"]
    if entry.get("provider"):
        note_parts.append(f"provider={entry['provider']}")
    if entry.get("region"):
        note_parts.append(f"billing region={entry['region']}")
    if entry.get("invoice_reference"):
        note_parts.append(f"invoice={entry['invoice_reference']}")
    if entry.get("notes"):
        note_parts.append(str(entry["notes"]))
    return build_row(
        workload_id=workload_id,
        functional_unit=module.FUNCTIONAL_UNIT,
        run_id=run_id,
        run_mode=run_mode,
        method="cloud_billing",
        method_available=True,
        duration_seconds=entry.get("duration_seconds"),
        energy_kwh=energy,
        location_intensity=None,
        market_intensity=None,
        carbon_intensity_basis=str(basis),
        location_kg=location_kg,
        market_kg=market_kg,
        mitigation_readiness="none",
        notes="; ".join(note_parts),
    )


def build_config(
    module: Any, dry_run: bool, overrides: dict[str, Any] | None
) -> dict[str, Any]:
    config = dict(module.DRY_CONFIG if dry_run else module.REAL_CONFIG)
    if overrides:
        config.update(overrides.get(module.WORKLOAD_ID, {}))
    return config


def parse_methods(text: str) -> list[str]:
    requested = [item.strip() for item in text.split(",") if item.strip()]
    unknown = [item for item in requested if item not in methods.METHOD_ORDER]
    if unknown:
        raise ValueError(
            f"unknown methods {unknown}; expected subset of {list(methods.METHOD_ORDER)}"
        )
    if not requested:
        raise ValueError("at least one method is required")
    # Canonical order keeps the CSV deterministic regardless of CLI order.
    return [name for name in methods.METHOD_ORDER if name in requested]


def run_study(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[str]]:
    """Execute the study and return (rows, human-readable summary lines)."""

    modules = load_workloads()
    workload_ids = resolve_workload_ids(args.workload, modules)
    selected_methods = parse_methods(args.methods)
    run_mode = "dry_run" if args.dry_run else "real"
    run_label = "dryrun" if args.dry_run else "real"
    overrides = None
    if args.config_overrides:
        with args.config_overrides.open(encoding="utf-8") as handle:
            overrides = json.load(handle)

    billing = None
    if "cloud_billing" in selected_methods:
        billing = methods.load_billing_entries(args.billing_file)

    rows: list[dict[str, str]] = []
    summary: list[str] = []
    for workload_id in workload_ids:
        module = modules[workload_id]
        config = build_config(module, args.dry_run, overrides)
        available, reason = methods.workload_availability(module)
        method_states: dict[str, str] = {}

        for iteration in range(1, args.iterations + 1):
            # Idle briefly before each run so an external power sampler sees a
            # stretch of pure background next to it. Without such a gap the
            # runs abut and background can only be estimated from one global
            # constant, which is wrong whenever the load drifts.
            if args.gap_seconds > 0 and not args.dry_run:
                time.sleep(args.gap_seconds)
            run_id = f"{run_label}-i{iteration:02d}"
            run_result = None
            if available:
                # One real execution per iteration; identical seed across
                # iterations so variance isolates measurement noise, not data.
                run_result = methods.execute_workload(
                    module,
                    config,
                    args.seed,
                    args.region,
                    want_codecarbon="codecarbon" in selected_methods,
                    measure_power_secs=1 if args.dry_run else 15,
                )

            for method in selected_methods:
                if method == "cloud_billing":
                    row = _billing_row(
                        module=module,
                        run_id=run_id,
                        run_mode=run_mode,
                        iteration=iteration,
                        billing=billing,
                        billing_path=args.billing_file,
                    )
                elif not available:
                    row = _unavailable_row(
                        workload_id=workload_id,
                        functional_unit=module.FUNCTIONAL_UNIT,
                        run_id=run_id,
                        run_mode=run_mode,
                        method=method,
                        reason=f"workload unavailable: {reason}",
                    )
                elif method == "codecarbon":
                    row = _codecarbon_row(
                        module=module,
                        run_id=run_id,
                        run_mode=run_mode,
                        region=args.region,
                        run_result=run_result,
                    )
                else:
                    row = _manual_row(
                        module=module,
                        config=config,
                        run_id=run_id,
                        run_mode=run_mode,
                        region=args.region,
                        gflops_per_watt=args.gflops_per_watt,
                        pue=args.pue,
                        duration_seconds=run_result.duration_seconds,
                        started_at=run_result.started_at,
                        ended_at=run_result.ended_at,
                    )
                rows.append(row)
                state = "ok" if row["method_available"] == "true" else row["notes"]
                method_states.setdefault(method, state)

        workload_state = "available" if available else f"unavailable ({reason})"
        summary.append(f"workload {workload_id}: {workload_state}")
        for method in selected_methods:
            summary.append(f"  {method}: {method_states.get(method, 'not run')}")

    if billing is not None:
        for warning in billing.warnings:
            summary.append(f"billing warning: {warning}")
    return rows, summary


def write_rows(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=MEASUREMENT_CSV_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FairMind-E M5 measurement harness",
    )
    parser.add_argument(
        "--workload",
        default="all",
        help="workload id or alias (w1..w4, w1_classical_ml, ...) or 'all'",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="iterations per workload (default: 5 real, 1 dry-run)",
    )
    parser.add_argument(
        "--methods",
        default=",".join(methods.METHOD_ORDER),
        help="comma-separated subset of codecarbon,cloud_billing,manual_flop",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="tiny config sizes end-to-end; rows labeled run_mode=dry_run",
    )
    parser.add_argument("--output", type=pathlib.Path, default=None)
    parser.add_argument(
        "--billing-file", type=pathlib.Path, default=DEFAULT_BILLING_FILE
    )
    parser.add_argument(
        "--region",
        default=grid_intensity.DEFAULT_REGION,
        help="ISO-3166 alpha-3 country code for codecarbon and the grid table",
    )
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--gflops-per-watt",
        type=float,
        default=methods.DEFAULT_GFLOPS_PER_WATT,
        help="manual_flop hardware-efficiency assumption (PLACEHOLDER default)",
    )
    parser.add_argument(
        "--pue",
        type=float,
        default=methods.DEFAULT_PUE,
        help="power usage effectiveness multiplier for manual_flop",
    )
    parser.add_argument(
        "--mitigations",
        action="store_true",
        help="also run the mitigation pair suite (quantization, region_shift, "
        "batching, time_shift) and write a companion CSV",
    )
    parser.add_argument(
        "--mitigation-iterations",
        type=int,
        default=1,
        help="repeat the mitigation suite this many times (with --mitigations) "
        "so each physical rerun has variance, not a single execution",
    )
    parser.add_argument(
        "--gap-seconds",
        type=float,
        default=0.0,
        help=(
            "idle this long before each run so an external power sampler can "
            "observe background next to it; 20 is a reasonable value when a "
            "power reference is being captured"
        ),
    )
    parser.add_argument(
        "--config-overrides",
        type=pathlib.Path,
        default=None,
        help="optional JSON file {workload_id: {param: value}} merged over defaults",
    )
    args = parser.parse_args(argv)

    if args.iterations is None:
        args.iterations = 1 if args.dry_run else 5
    if args.iterations < 1:
        parser.error("--iterations must be >= 1")
    if args.mitigation_iterations < 1:
        parser.error("--mitigation-iterations must be >= 1")
    run_label = "dryrun" if args.dry_run else "real"
    if args.output is None:
        args.output = DEFAULT_OUTPUT_DIR / f"{run_label}_runs.csv"

    rows, summary = run_study(args)
    write_rows(args.output, rows)
    print(f"wrote {len(rows)} rows to {args.output}")
    for line in summary:
        print(line)

    if args.mitigations:
        from measurement import mitigations as mitigations_module

        mitigation_rows = []
        for iteration in range(1, args.mitigation_iterations + 1):
            mitigation_rows.extend(mitigations_module.run_mitigation_suite(
                workload=args.workload,
                dry_run=args.dry_run,
                seed=args.seed,
                region=args.region,
                gflops_per_watt=args.gflops_per_watt,
                pue=args.pue,
                config_overrides_path=args.config_overrides,
                iteration=iteration,
            ))
        mitigation_path = args.output.parent / (
            args.output.stem + "_mitigations.csv"
        )
        mitigations_module.write_mitigation_rows(mitigation_path, mitigation_rows)
        print(f"wrote {len(mitigation_rows)} mitigation pair rows to {mitigation_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

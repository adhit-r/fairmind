"""Mitigation interventions for the FairMind-E measurement study (H4).

Four reproducible transformations, each emitted as a pre/post pair row so the
H4 analysis can compare intensity before and after the intervention:

- ``quantization`` (W2, W3): a genuine reduced-precision config rerun
  (W3 numpy float64 -> float32, W2 torch float32 -> bfloat16). Durations are
  measured for both phases. When energy comes from the analytic FLOP model
  the pre/post energy is identical by construction (the model is
  precision-blind) and the row note says so; the real study relies on
  codecarbon to expose the true delta.
- ``region_shift`` (all workloads): no rerun; the measured energy of one run
  is recomputed against a different region of the bundled static
  grid-intensity table (PLACEHOLDER data, source-year labeled in
  ``grid_intensity.py``).
- ``batching`` (W4): a real batch-size sweep rerun; smallest sweep point is
  the pre phase, largest is the post phase.
- ``time_shift`` (all workloads): no rerun; the measured energy is recomputed
  against the bundled 24-hour hourly intensity profile (same PLACEHOLDER
  labeling), evening peak hour versus midday solar dip.

Honesty rules match the harness: pairs whose workload or reduced-precision
rerun is impossible in the current environment are recorded with
``method_available=false`` and the reason; nothing is fabricated. Every pair
row carries ``provenance_class=manual`` because pair carbon always flows
through the placeholder intensity table (weakest-link rule), while
``energy_method`` records whether the energy figure itself came from
codecarbon or the analytic FLOP model.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from measurement import grid_intensity, methods
from measurement.workloads import load_workloads, resolve_workload_ids

MITIGATION_CSV_COLUMNS = [
    "mitigation_id",
    "workload_id",
    "run_id",
    "run_mode",
    "energy_method",
    "method_available",
    "pre_label",
    "post_label",
    "pre_duration_seconds",
    "post_duration_seconds",
    "pre_energy_kwh",
    "post_energy_kwh",
    "pre_location_intensity_g_per_kwh",
    "post_location_intensity_g_per_kwh",
    "pre_market_intensity_g_per_kwh",
    "post_market_intensity_g_per_kwh",
    "pre_location_kg_co2e",
    "post_location_kg_co2e",
    "pre_market_kg_co2e",
    "post_market_kg_co2e",
    "delta_location_pct",
    "delta_market_pct",
    "provenance_class",
    "intensity_source",
    "notes",
]

QUANTIZATION_DTYPES: dict[str, tuple[str, str]] = {
    "transformer_finetune": ("float32", "bfloat16"),
    "rag_inference": ("float64", "float32"),
}

BATCHING_SWEEP: dict[str, dict[str, tuple[int, int]]] = {
    "batch_embeddings": {"real": (64, 4096), "dry_run": (32, 1024)},
}

REGION_SHIFT_TARGET = "SWE"
TIME_SHIFT_PRE_HOUR = 19  # evening ramp peak in the placeholder profile
TIME_SHIFT_POST_HOUR = 13  # midday solar dip in the placeholder profile

INTENSITY_SOURCE = (
    f"bundled_placeholder_table_{grid_intensity.DATA_SOURCE_YEAR}"
)


def _fmt(value: float | None, spec: str) -> str:
    if value is None:
        return ""
    return format(value, spec)


def _delta_pct(pre: float | None, post: float | None) -> float | None:
    if pre is None or post is None or pre == 0:
        return None
    return (post - pre) / pre * 100.0


class _Phase:
    """One executed (or recomputed) side of a mitigation pair."""

    def __init__(
        self,
        energy_kwh: float | None,
        duration_seconds: float | None,
        energy_method: str,
    ) -> None:
        self.energy_kwh = energy_kwh
        self.duration_seconds = duration_seconds
        self.energy_method = energy_method


def _run_phase(
    module: Any,
    config: dict[str, Any],
    seed: int,
    region: str,
    gflops_per_watt: float,
    pue: float,
    dry_run: bool,
) -> _Phase:
    """Execute one phase for real; energy from codecarbon else the FLOP model."""

    run_result = methods.execute_workload(
        module,
        config,
        seed,
        region,
        want_codecarbon=True,
        measure_power_secs=1 if dry_run else 15,
    )
    if run_result.codecarbon_available and run_result.codecarbon_energy_kwh:
        return _Phase(
            run_result.codecarbon_energy_kwh,
            run_result.duration_seconds,
            "codecarbon",
        )
    energy = methods.manual_energy_kwh(
        module.flop_estimate(config), gflops_per_watt, pue
    )
    return _Phase(energy, run_result.duration_seconds, "manual_flop")


def _pair_row(
    *,
    mitigation_id: str,
    workload_id: str,
    run_id: str,
    run_mode: str,
    energy_method: str,
    available: bool,
    pre_label: str,
    post_label: str,
    pre: _Phase | None,
    post: _Phase | None,
    pre_intensities: dict[str, float | None] | None,
    post_intensities: dict[str, float | None] | None,
    notes: str,
) -> dict[str, str]:
    def kg(phase: _Phase | None, intensities, key: str) -> float | None:
        if phase is None or phase.energy_kwh is None or not intensities:
            return None
        intensity = intensities.get(key)
        if intensity is None:
            return None
        return phase.energy_kwh * intensity / 1000.0

    pre_loc_kg = kg(pre, pre_intensities, "location")
    post_loc_kg = kg(post, post_intensities, "location")
    pre_mkt_kg = kg(pre, pre_intensities, "market")
    post_mkt_kg = kg(post, post_intensities, "market")

    return {
        "mitigation_id": mitigation_id,
        "workload_id": workload_id,
        "run_id": run_id,
        "run_mode": run_mode,
        "energy_method": energy_method,
        "method_available": "true" if available else "false",
        "pre_label": pre_label,
        "post_label": post_label,
        "pre_duration_seconds": _fmt(pre.duration_seconds if pre else None, ".3f"),
        "post_duration_seconds": _fmt(post.duration_seconds if post else None, ".3f"),
        "pre_energy_kwh": _fmt(pre.energy_kwh if pre else None, ".6g"),
        "post_energy_kwh": _fmt(post.energy_kwh if post else None, ".6g"),
        "pre_location_intensity_g_per_kwh": _fmt(
            pre_intensities.get("location") if pre_intensities else None, ".1f"
        ),
        "post_location_intensity_g_per_kwh": _fmt(
            post_intensities.get("location") if post_intensities else None, ".1f"
        ),
        "pre_market_intensity_g_per_kwh": _fmt(
            pre_intensities.get("market") if pre_intensities else None, ".1f"
        ),
        "post_market_intensity_g_per_kwh": _fmt(
            post_intensities.get("market") if post_intensities else None, ".1f"
        ),
        "pre_location_kg_co2e": _fmt(pre_loc_kg, ".6g"),
        "post_location_kg_co2e": _fmt(post_loc_kg, ".6g"),
        "pre_market_kg_co2e": _fmt(pre_mkt_kg, ".6g"),
        "post_market_kg_co2e": _fmt(post_mkt_kg, ".6g"),
        "delta_location_pct": _fmt(_delta_pct(pre_loc_kg, post_loc_kg), ".2f"),
        "delta_market_pct": _fmt(_delta_pct(pre_mkt_kg, post_mkt_kg), ".2f"),
        "provenance_class": "manual" if available else "unknown",
        "intensity_source": INTENSITY_SOURCE if available else "",
        "notes": notes,
    }


def _unavailable_pair(
    mitigation_id: str,
    workload_id: str,
    run_id: str,
    run_mode: str,
    pre_label: str,
    post_label: str,
    reason: str,
) -> dict[str, str]:
    return _pair_row(
        mitigation_id=mitigation_id,
        workload_id=workload_id,
        run_id=run_id,
        run_mode=run_mode,
        energy_method="",
        available=False,
        pre_label=pre_label,
        post_label=post_label,
        pre=None,
        post=None,
        pre_intensities=None,
        post_intensities=None,
        notes=f"mitigation unavailable: {reason}",
    )


def run_mitigation_suite(
    *,
    workload: str = "all",
    dry_run: bool = True,
    seed: int = 1337,
    region: str = grid_intensity.DEFAULT_REGION,
    gflops_per_watt: float = methods.DEFAULT_GFLOPS_PER_WATT,
    pue: float = methods.DEFAULT_PUE,
    config_overrides_path: pathlib.Path | None = None,
    target_region: str = REGION_SHIFT_TARGET,
) -> list[dict[str, str]]:
    """Run every applicable mitigation for the selected workloads."""

    modules = load_workloads()
    workload_ids = resolve_workload_ids(workload, modules)
    run_mode = "dry_run" if dry_run else "real"
    run_label = "dryrun" if dry_run else "real"
    overrides: dict[str, Any] = {}
    if config_overrides_path:
        with config_overrides_path.open(encoding="utf-8") as handle:
            overrides = json.load(handle)

    base_intensities = grid_intensity.intensities_for(region)
    shifted_intensities = grid_intensity.intensities_for(target_region)
    pre_hour_intensity = grid_intensity.hourly_location_intensity(
        region, TIME_SHIFT_PRE_HOUR
    )
    post_hour_intensity = grid_intensity.hourly_location_intensity(
        region, TIME_SHIFT_POST_HOUR
    )

    rows: list[dict[str, str]] = []
    pair_index = 0

    def next_run_id() -> str:
        nonlocal pair_index
        pair_index += 1
        return f"{run_label}-m{pair_index:02d}"

    for workload_id in workload_ids:
        module = modules[workload_id]
        config = dict(module.DRY_CONFIG if dry_run else module.REAL_CONFIG)
        config.update(overrides.get(workload_id, {}))
        available, reason = methods.workload_availability(module)

        base_phase: _Phase | None = None
        if available:
            base_phase = _run_phase(
                module, config, seed, region, gflops_per_watt, pue, dry_run
            )

        # quantization: reduced-precision rerun (W2, W3 only).
        if workload_id in QUANTIZATION_DTYPES:
            pre_dtype, post_dtype = QUANTIZATION_DTYPES[workload_id]
            run_id = next_run_id()
            if not available:
                rows.append(
                    _unavailable_pair(
                        "quantization", workload_id, run_id, run_mode,
                        f"dtype={pre_dtype}", f"dtype={post_dtype}",
                        f"workload unavailable: {reason}",
                    )
                )
            else:
                try:
                    post_phase = _run_phase(
                        module,
                        dict(config, dtype=post_dtype),
                        seed,
                        region,
                        gflops_per_watt,
                        pue,
                        dry_run,
                    )
                except Exception as exc:
                    rows.append(
                        _unavailable_pair(
                            "quantization", workload_id, run_id, run_mode,
                            f"dtype={pre_dtype}", f"dtype={post_dtype}",
                            f"reduced-precision rerun failed: {exc}",
                        )
                    )
                else:
                    note = (
                        f"reduced-precision rerun {pre_dtype} -> {post_dtype}; "
                        "durations measured per phase"
                    )
                    if base_phase.energy_method == "manual_flop":
                        note += (
                            "; manual FLOP model is precision-blind, so pre/post "
                            "energy is identical by construction - use codecarbon "
                            "for the real study delta"
                        )
                    rows.append(
                        _pair_row(
                            mitigation_id="quantization",
                            workload_id=workload_id,
                            run_id=run_id,
                            run_mode=run_mode,
                            energy_method=base_phase.energy_method,
                            available=True,
                            pre_label=f"dtype={pre_dtype}",
                            post_label=f"dtype={post_dtype}",
                            pre=base_phase,
                            post=post_phase,
                            pre_intensities=base_intensities,
                            post_intensities=base_intensities,
                            notes=note,
                        )
                    )

        # batching: batch-size sweep rerun (W4 only).
        if workload_id in BATCHING_SWEEP:
            pre_batch, post_batch = BATCHING_SWEEP[workload_id][run_mode]
            run_id = next_run_id()
            if not available:
                rows.append(
                    _unavailable_pair(
                        "batching", workload_id, run_id, run_mode,
                        f"batch_size={pre_batch}", f"batch_size={post_batch}",
                        f"workload unavailable: {reason}",
                    )
                )
            else:
                pre_phase = _run_phase(
                    module, dict(config, batch_size=pre_batch), seed, region,
                    gflops_per_watt, pue, dry_run,
                )
                post_phase = _run_phase(
                    module, dict(config, batch_size=post_batch), seed, region,
                    gflops_per_watt, pue, dry_run,
                )
                note = (
                    f"batch-size sweep {pre_batch} -> {post_batch}; durations "
                    "measured per phase"
                )
                if pre_phase.energy_method == "manual_flop":
                    note += (
                        "; manual FLOP model is batch-blind, so pre/post energy "
                        "is identical by construction - use codecarbon for the "
                        "real study delta"
                    )
                rows.append(
                    _pair_row(
                        mitigation_id="batching",
                        workload_id=workload_id,
                        run_id=run_id,
                        run_mode=run_mode,
                        energy_method=pre_phase.energy_method,
                        available=True,
                        pre_label=f"batch_size={pre_batch}",
                        post_label=f"batch_size={post_batch}",
                        pre=pre_phase,
                        post=post_phase,
                        pre_intensities=base_intensities,
                        post_intensities=base_intensities,
                        notes=note,
                    )
                )

        # region_shift: same energy, different region of the placeholder table.
        run_id = next_run_id()
        if not available:
            rows.append(
                _unavailable_pair(
                    "region_shift", workload_id, run_id, run_mode,
                    f"region={region}", f"region={target_region}",
                    f"workload unavailable: {reason}",
                )
            )
        else:
            rows.append(
                _pair_row(
                    mitigation_id="region_shift",
                    workload_id=workload_id,
                    run_id=run_id,
                    run_mode=run_mode,
                    energy_method=base_phase.energy_method,
                    available=True,
                    pre_label=f"region={region}",
                    post_label=f"region={target_region}",
                    pre=base_phase,
                    post=base_phase,
                    pre_intensities=base_intensities,
                    post_intensities=shifted_intensities,
                    notes=(
                        "recomputation of one measured run against the "
                        f"{INTENSITY_SOURCE}; no rerun performed"
                    ),
                )
            )

        # time_shift: same energy, hourly profile of the placeholder table.
        run_id = next_run_id()
        if not available:
            rows.append(
                _unavailable_pair(
                    "time_shift", workload_id, run_id, run_mode,
                    f"hour={TIME_SHIFT_PRE_HOUR:02d}",
                    f"hour={TIME_SHIFT_POST_HOUR:02d}",
                    f"workload unavailable: {reason}",
                )
            )
        else:
            rows.append(
                _pair_row(
                    mitigation_id="time_shift",
                    workload_id=workload_id,
                    run_id=run_id,
                    run_mode=run_mode,
                    energy_method=base_phase.energy_method,
                    available=True,
                    pre_label=f"hour={TIME_SHIFT_PRE_HOUR:02d}",
                    post_label=f"hour={TIME_SHIFT_POST_HOUR:02d}",
                    pre=base_phase,
                    post=base_phase,
                    pre_intensities={
                        "location": pre_hour_intensity, "market": None
                    },
                    post_intensities={
                        "location": post_hour_intensity, "market": None
                    },
                    notes=(
                        "recomputation of one measured run against the bundled "
                        "24h hourly profile (PLACEHOLDER shape); market-based "
                        "hourly figures are not modeled; no rerun performed"
                    ),
                )
            )

    return rows


def write_mitigation_rows(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=MITIGATION_CSV_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

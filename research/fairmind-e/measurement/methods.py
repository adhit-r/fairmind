"""Measurement-method primitives shared by harness.py and mitigations.py.

Three methods, three provenance classes (never mixed, never upgraded):

- ``codecarbon``    -> ``tool_estimated``: software power tracker wrapping the
  real workload execution (``OfflineEmissionsTracker`` with a configurable
  country ISO code). Used only when codecarbon is importable.
- ``cloud_billing`` -> ``vendor_reported``: figures read from an
  operator-filled CSV (``cloud_billing_template.csv``). Real billing lags
  hours to days, so this is a documented manual-entry path; the harness never
  invents or simulates a billing API response.
- ``manual_flop``   -> ``manual``: analytic FLOP estimate (per-workload
  formula, see each workload module docstring) converted to energy through a
  hardware-efficiency assumption and to carbon through the bundled
  PLACEHOLDER grid-intensity table.

Honesty rule: when a method cannot produce a real figure (missing import,
missing billing entry, tracker failure), the caller records
``method_available=false`` with the reason; nothing is fabricated.
"""

from __future__ import annotations

import csv
import dataclasses
import time
import pathlib
from typing import Any

METHOD_ORDER = ("codecarbon", "cloud_billing", "manual_flop")

PROVENANCE_BY_METHOD = {
    "codecarbon": "tool_estimated",
    "cloud_billing": "vendor_reported",
    "manual_flop": "manual",
}

# Instrument string written to the legacy "method" column of the CSV contract.
INSTRUMENT_BY_METHOD = {
    "codecarbon": "codecarbon_offline_tracker",
    "cloud_billing": "cloud_billing_import",
    "manual_flop": "analytic_flop_model",
}

# Default relative uncertainty per method. Confidence derives from these via
# the smoke-harness rules: tool_estimated -> 0.75, vendor_reported -> capped
# 0.60, manual -> clamped to its band floor 0.20.
UNCERTAINTY_PCT_BY_METHOD = {
    "codecarbon": 25,
    "cloud_billing": 30,
    "manual_flop": 75,
}

# PLACEHOLDER hardware assumptions for the manual_flop method. Effective
# sustained CPU efficiency; override per machine with --gflops-per-watt.
DEFAULT_GFLOPS_PER_WATT = 4.0
DEFAULT_PUE = 1.0

BILLING_REQUIRED_HEADERS = {"workload_id", "iteration"}
BILLING_NUMERIC_FIELDS = (
    "duration_seconds",
    "energy_kwh",
    "location_kg_co2e",
    "market_kg_co2e",
)

# Test seam: names placed here (method names or workload ids) are treated as
# unavailable so honest-degradation paths can be exercised even on machines
# where every dependency happens to be installed. Never set in production.
FORCE_UNAVAILABLE: set[str] = set()


def workload_availability(module: Any) -> tuple[bool, str]:
    """Availability probe for a workload module, honoring the test seam."""

    if module.WORKLOAD_ID in FORCE_UNAVAILABLE:
        return False, "forced unavailable (test seam)"
    return module.availability()


def probe_codecarbon() -> tuple[bool, str]:
    """Return (available, reason) for the codecarbon method. Never raises."""

    if "codecarbon" in FORCE_UNAVAILABLE:
        return False, "forced unavailable (test seam)"
    try:
        import codecarbon  # noqa: F401
    except ImportError as exc:
        return False, f"codecarbon not importable: {exc}"
    version = getattr(codecarbon, "__version__", "unknown")
    return True, f"codecarbon {version} importable"


@dataclasses.dataclass
class RunResult:
    """One real workload execution, optionally wrapped by codecarbon."""

    duration_seconds: float
    work_metrics: dict[str, Any]
    codecarbon_available: bool
    codecarbon_reason: str
    codecarbon_energy_kwh: float | None = None
    codecarbon_emissions_kg: float | None = None
    # Unix epoch seconds bracketing the workload itself, so an independently
    # sampled power log can be integrated over exactly this window.
    started_at: float | None = None
    ended_at: float | None = None


def _timed_run(module: Any, config: dict[str, Any], seed: int) -> tuple[dict[str, Any], float, float]:
    """Run the workload, returning its result and the wall-clock window."""
    started = time.time()
    result = module.run(config, seed)
    return result, started, time.time()


def execute_workload(
    module: Any,
    config: dict[str, Any],
    seed: int,
    region: str,
    want_codecarbon: bool,
    measure_power_secs: int = 15,
) -> RunResult:
    """Run the workload once; wrap with codecarbon when requested and possible.

    The workload always executes exactly once, so the codecarbon and
    manual_flop rows for an iteration describe the same physical run. If the
    tracker fails before the workload ran, the workload is re-run untracked so
    duration and the manual estimate stay real; the codecarbon method is then
    recorded unavailable with the failure reason.
    """

    if not want_codecarbon:
        result, started, ended = _timed_run(module, config, seed)
        return RunResult(
            duration_seconds=result["duration_seconds"],
            work_metrics=result["work_metrics"],
            codecarbon_available=False,
            codecarbon_reason="method not requested",
            started_at=started,
            ended_at=ended,
        )

    cc_ok, cc_reason = probe_codecarbon()
    if not cc_ok:
        result, started, ended = _timed_run(module, config, seed)
        return RunResult(
            duration_seconds=result["duration_seconds"],
            work_metrics=result["work_metrics"],
            codecarbon_available=False,
            codecarbon_reason=cc_reason,
            started_at=started,
            ended_at=ended,
        )

    result: dict[str, Any] | None = None
    started = ended = None
    try:
        from codecarbon import OfflineEmissionsTracker

        tracker = OfflineEmissionsTracker(
            country_iso_code=region,
            measure_power_secs=measure_power_secs,
            save_to_file=False,
            log_level="error",
        )
        tracker.start()
        try:
            result, started, ended = _timed_run(module, config, seed)
        finally:
            stop_emissions = tracker.stop()
        data = getattr(tracker, "final_emissions_data", None)
        energy_kwh = getattr(data, "energy_consumed", None)
        emissions_kg = getattr(data, "emissions", None)
        if emissions_kg is None:
            emissions_kg = stop_emissions
        if energy_kwh is None or emissions_kg is None:
            return RunResult(
                duration_seconds=result["duration_seconds"],
                work_metrics=result["work_metrics"],
                codecarbon_available=False,
                codecarbon_reason=(
                    "codecarbon ran but returned no energy figure; "
                    "recorded unavailable rather than fabricating one"
                ),
                started_at=started,
                ended_at=ended,
            )
        return RunResult(
            duration_seconds=result["duration_seconds"],
            work_metrics=result["work_metrics"],
            codecarbon_available=True,
            codecarbon_reason=cc_reason,
            codecarbon_energy_kwh=float(energy_kwh),
            codecarbon_emissions_kg=float(emissions_kg),
            started_at=started,
            ended_at=ended,
        )
    except Exception as exc:  # tracker fault must not lose the real run
        if result is None:
            result, started, ended = _timed_run(module, config, seed)
        return RunResult(
            duration_seconds=result["duration_seconds"],
            work_metrics=result["work_metrics"],
            codecarbon_available=False,
            codecarbon_reason=f"codecarbon failed: {exc}",
            started_at=started,
            ended_at=ended,
        )


def manual_energy_kwh(flops: float, gflops_per_watt: float, pue: float) -> float:
    """Convert analytic FLOPs to energy via the efficiency assumption.

    energy_joules = flops / (gflops_per_watt * 1e9)   [flops per joule]
    energy_kwh    = energy_joules / 3.6e6, scaled by PUE.
    """

    if flops <= 0 or gflops_per_watt <= 0 or pue <= 0:
        raise ValueError("flops, gflops_per_watt, and pue must be positive")
    joules = flops / (gflops_per_watt * 1.0e9)
    return joules / 3.6e6 * pue


@dataclasses.dataclass
class BillingData:
    """Parsed operator billing file plus its availability status."""

    available: bool
    reason: str
    entries: dict[tuple[str, int], dict[str, Any]]
    warnings: list[str]


def load_billing_entries(path: pathlib.Path) -> BillingData:
    """Read operator-supplied billing figures. Never invents entries.

    Lines starting with ``#`` and blank lines are documentation and are
    skipped. Entries are keyed by (workload_id, iteration). Numeric fields
    are parsed when present; unparseable values invalidate the entry with a
    recorded warning instead of being silently coerced.
    """

    if "cloud_billing" in FORCE_UNAVAILABLE:
        return BillingData(False, "forced unavailable (test seam)", {}, [])
    if not path.exists():
        return BillingData(False, f"billing file not found: {path}", {}, [])

    with path.open(newline="", encoding="utf-8") as handle:
        data_lines = [
            line for line in handle if line.strip() and not line.lstrip().startswith("#")
        ]
    if not data_lines:
        return BillingData(
            False, f"billing file has no header row: {path}", {}, []
        )

    reader = csv.DictReader(data_lines)
    headers = set(reader.fieldnames or [])
    missing = BILLING_REQUIRED_HEADERS - headers
    if missing:
        return BillingData(
            False,
            f"billing file missing required columns {sorted(missing)}: {path}",
            {},
            [],
        )

    entries: dict[tuple[str, int], dict[str, Any]] = {}
    warnings: list[str] = []
    for row_number, raw in enumerate(reader, start=1):
        workload_id = (raw.get("workload_id") or "").strip()
        iteration_text = (raw.get("iteration") or "").strip()
        if not workload_id or not iteration_text:
            warnings.append(
                f"data row {row_number}: missing workload_id or iteration; skipped"
            )
            continue
        try:
            iteration = int(iteration_text)
        except ValueError:
            warnings.append(
                f"data row {row_number}: iteration {iteration_text!r} is not an "
                "integer; skipped"
            )
            continue
        entry: dict[str, Any] = {
            key: (value or "").strip() for key, value in raw.items() if key
        }
        parse_failed = False
        for field in BILLING_NUMERIC_FIELDS:
            text = entry.get(field, "")
            if text == "":
                entry[field] = None
                continue
            try:
                entry[field] = float(text)
            except ValueError:
                warnings.append(
                    f"data row {row_number}: {field} {text!r} is not numeric; "
                    "entry skipped"
                )
                parse_failed = True
                break
        if parse_failed:
            continue
        entries[(workload_id, iteration)] = entry

    return BillingData(True, f"billing file loaded: {path}", entries, warnings)

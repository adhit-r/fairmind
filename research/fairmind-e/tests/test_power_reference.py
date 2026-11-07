"""
Unit tests for the independent power reference and the calibration analysis.

The parser decides which power samples belong to which run, so an error here
would silently corrupt every calibration figure. These tests pin the
integration arithmetic against hand-computed values and the attribution rule
against deliberately adjacent windows.

Run:
    python3 research/fairmind-e/tests/test_power_reference.py
"""

from __future__ import annotations

import csv
import datetime
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before execution: @dataclass resolves its module from
    # sys.modules and fails on an unregistered dynamically loaded module.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


power_reference = _load("power_reference", "measurement/power_reference.py")


def write_log(path: Path, start_epoch: float, watts_by_index: list[float], interval_ms: float = 1000.0) -> None:
    """Emit a powermetrics-shaped text log, one sample per second."""
    lines: list[str] = []
    step = interval_ms / 1000.0
    for i, watts in enumerate(watts_by_index):
        stamp = datetime.datetime.fromtimestamp(start_epoch + i * step).astimezone()
        header = stamp.strftime("%a %b %e %H:%M:%S %Y %z")
        mw = int(round(watts * 1000))
        lines += [
            f"*** Sampled system activity ({header}) ({interval_ms:.2f}ms elapsed) ***",
            "",
            "**** Processor usage ****",
            "",
            f"CPU Power: {mw} mW",
            "GPU Power: 0 mW",
            "ANE Power: 0 mW",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.start = float(int(datetime.datetime.now().timestamp()))

    def tearDown(self):
        self.tmp.cleanup()

    def test_parses_every_sample_and_converts_milliwatts(self):
        log = self.dir / "pm.txt"
        write_log(log, self.start, [1.0, 2.0, 3.0])
        samples = power_reference.parse_powermetrics(log)
        self.assertEqual(len(samples), 3)
        self.assertAlmostEqual(samples[0].watts, 1.0, places=6)
        self.assertAlmostEqual(samples[2].watts, 3.0, places=6)

    def test_sums_components_when_no_combined_line(self):
        log = self.dir / "pm.txt"
        stamp = datetime.datetime.fromtimestamp(self.start).astimezone().strftime("%a %b %e %H:%M:%S %Y %z")
        log.write_text(
            f"*** Sampled system activity ({stamp}) (1000.00ms elapsed) ***\n"
            "CPU Power: 1200 mW\nGPU Power: 300 mW\nANE Power: 100 mW\n",
            encoding="utf-8",
        )
        samples = power_reference.parse_powermetrics(log)
        self.assertAlmostEqual(samples[0].watts, 1.6, places=6)

    def test_empty_log_raises_rather_than_reporting_zero(self):
        log = self.dir / "empty.txt"
        log.write_text("no samples here\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            power_reference.parse_powermetrics(log)

    def test_integration_matches_hand_computation(self):
        log = self.dir / "pm.txt"
        # Six samples at 1.32 W, one second each -> 7.92 J -> 2.2e-6 kWh.
        write_log(log, self.start, [0.33, 0.33] + [1.32] * 6 + [0.33, 0.33])
        samples = power_reference.parse_powermetrics(log)
        # A sample stamped at T covers [T-1, T], so the busy interval is
        # [start+1, start+7] in wall-clock terms.
        kwh, count, mean_w = power_reference.integrate(samples, self.start + 1, self.start + 7)
        self.assertEqual(count, 6)
        self.assertAlmostEqual(mean_w, 1.32, places=6)
        self.assertAlmostEqual(kwh, 1.32 * 6 / 3_600_000.0, places=12)

    def test_a_sample_is_never_attributed_to_two_adjacent_runs(self):
        log = self.dir / "pm.txt"
        write_log(log, self.start, [1.0] * 10)
        samples = power_reference.parse_powermetrics(log)
        _, first, _ = power_reference.integrate(samples, self.start + 0, self.start + 4)
        _, second, _ = power_reference.integrate(samples, self.start + 4, self.start + 8)
        # Midpoint attribution keeps the boundary sample in exactly one window.
        total = len([s for s in samples if self.start <= s.midpoint <= self.start + 8])
        self.assertEqual(first + second, total)

    def test_window_with_no_samples_reports_zero_not_error(self):
        log = self.dir / "pm.txt"
        write_log(log, self.start, [1.0, 1.0])
        samples = power_reference.parse_powermetrics(log)
        kwh, count, _ = power_reference.integrate(samples, self.start + 500, self.start + 600)
        self.assertEqual(count, 0)
        self.assertEqual(kwh, 0.0)


class CalibrationTest(unittest.TestCase):
    """The calibration must report a refutation as readily as a confirmation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.calib = _load("calibrate_confidence", "analysis/calibrate_confidence.py")

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, runs, reference):
        runs_path, ref_path = self.dir / "runs.csv", self.dir / "ref.csv"
        with runs_path.open("w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=list(runs[0]))
            w.writeheader()
            w.writerows(runs)
        with ref_path.open("w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=list(reference[0]))
            w.writeheader()
            w.writerows(reference)
        return runs_path, ref_path

    N_RUNS = 5  # calibrate_confidence withholds its verdict below 5 runs per method

    def _runs(self, cc_energy: float, mf_energy: float, n: int = N_RUNS):
        rows = []
        for i in range(1, n + 1):
            base = {
                "workload_id": "w1", "run_id": f"r{i}", "method_available": "true",
                "measurement_method": "", "energy_kwh": "", "confidence_score": "",
                "provenance_class": "",
            }
            rows += [
                {**base, "measurement_method": "codecarbon", "energy_kwh": f"{cc_energy}",
                 "confidence_score": "0.72", "provenance_class": "tool_estimated"},
                {**base, "measurement_method": "manual_flop", "energy_kwh": f"{mf_energy}",
                 "confidence_score": "0.30", "provenance_class": "manual"},
            ]
        return rows

    def _reference(self, value: float, n: int = N_RUNS):
        return [{"workload_id": "w1", "run_id": f"r{i}", "reference_kwh_total": f"{value}",
                 "reference_kwh_marginal": ""} for i in range(1, n + 1)]

    def test_withholds_verdict_below_minimum_runs(self):
        runs, ref = self._write(self._runs(1.05e-4, 5.0e-4, n=1), self._reference(1.0e-4, n=1))
        out = self.dir / "out.json"
        self.calib.main(["--runs", str(runs), "--reference", str(ref), "--out", str(out)])
        import json
        summary = json.loads(out.read_text())
        self.assertIsNone(summary["verdict"]["ordering_holds"])
        self.assertIn("insufficient samples", summary["verdict"]["reading"])

    def test_zero_estimate_does_not_crash_log_ratio(self):
        runs, ref = self._write(self._runs(0.0, 5.0e-4), self._reference(1.0e-4))
        out = self.dir / "out.json"
        self.calib.main(["--runs", str(runs), "--reference", str(ref), "--out", str(out)])
        import json
        summary = json.loads(out.read_text())
        self.assertIsNone(summary["methods"]["codecarbon"]["mean_log_ratio"])

    def test_reports_ordering_holds_when_trusted_method_is_closer(self):
        runs, ref = self._write(self._runs(1.05e-4, 5.0e-4), self._reference(1.0e-4))
        out = self.dir / "out.json"
        self.calib.main(["--runs", str(runs), "--reference", str(ref), "--out", str(out)])
        import json
        summary = json.loads(out.read_text())
        self.assertTrue(summary["verdict"]["ordering_holds"])
        self.assertIn("consistent with observed error", summary["verdict"]["reading"])

    def test_reports_refutation_when_trusted_method_is_further(self):
        # codecarbon is 5x off, manual is nearly exact: the hierarchy fails.
        runs, ref = self._write(self._runs(5.0e-4, 1.02e-4), self._reference(1.0e-4))
        out = self.dir / "out.json"
        self.calib.main(["--runs", str(runs), "--reference", str(ref), "--out", str(out)])
        import json
        summary = json.loads(out.read_text())
        self.assertFalse(summary["verdict"]["ordering_holds"])
        self.assertIn("NOT supported by measurement", summary["verdict"]["reading"])

    def test_reference_caveat_is_always_carried(self):
        runs, ref = self._write(self._runs(1.0e-4, 2.0e-4), self._reference(1.0e-4))
        out = self.dir / "out.json"
        self.calib.main(["--runs", str(runs), "--reference", str(ref), "--out", str(out)])
        import json
        summary = json.loads(out.read_text())
        self.assertIn("not ground truth", summary["reference"]["caveat"])


if __name__ == "__main__":
    unittest.main(verbosity=1)

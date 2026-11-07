"""Tests for the FairMind-E M5 measurement harness.

Stdlib unittest, same run pattern as the other research tests:

    cd apps/backend
    uv run python ../../research/fairmind-e/tests/test_measurement_harness.py

or, degraded but still honest, with plain python3 from the repository root:

    python3 research/fairmind-e/tests/test_measurement_harness.py

Assertions are environment-adaptive on purpose: when numpy, sklearn, torch,
or codecarbon are missing, the harness must record the affected workloads and
methods as unavailable instead of fabricating figures, and these tests verify
exactly that behavior in whichever environment they run.
"""

from __future__ import annotations

import contextlib
import csv
import io
import math
import pathlib
import sys
import tempfile
import importlib.util
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from measurement import grid_intensity, harness, methods, mitigations  # noqa: E402
from measurement.workloads import (  # noqa: E402
    w1_classical_ml,
    w2_finetune,
    w3_rag,
    w4_batch_embed,
)

ALL_WORKLOAD_MODULES = (w1_classical_ml, w2_finetune, w3_rag, w4_batch_embed)
W1_AVAILABLE = w1_classical_ml.availability()[0]
ANY_WORKLOAD_AVAILABLE = any(
    module.availability()[0] for module in ALL_WORKLOAD_MODULES
)

BILLING_HEADER = (
    "workload_id,iteration,provider,service,region,billing_period_start,"
    "billing_period_end,duration_seconds,energy_kwh,location_kg_co2e,"
    "market_kg_co2e,carbon_intensity_basis,invoice_reference,notes"
)


def run_harness(argv: list[str]) -> tuple[int, str]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = harness.main(argv)
    return exit_code, stdout.getvalue()


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class DryRunSchemaTest(unittest.TestCase):
    def test_dry_run_produces_schema_valid_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "dryrun_runs.csv"
            exit_code, _ = run_harness(
                ["--workload", "all", "--dry-run", "--output", str(output)]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())

            with output.open(newline="", encoding="utf-8") as handle:
                header = next(csv.reader(handle))
            self.assertEqual(header, harness.MEASUREMENT_CSV_COLUMNS)
            # Contract: exactly the smoke columns plus the harness additions.
            # started_at/ended_at bracket the workload so an independently
            # sampled power log can be integrated over that exact window.
            self.assertEqual(
                harness.MEASUREMENT_CSV_COLUMNS,
                list(harness._SMOKE.CSV_COLUMNS)
                + [
                    "measurement_method",
                    "run_mode",
                    "method_available",
                    "started_at",
                    "ended_at",
                ],
            )

            rows = read_rows(output)
            # 4 workloads x 1 dry iteration x 3 methods, rows always emitted.
            self.assertEqual(len(rows), 12)
            for row in rows:
                self.assertEqual(row["run_mode"], "dry_run")
                self.assertIn(row["method_available"], {"true", "false"})
                self.assertIn(row["measurement_method"], methods.METHOD_ORDER)
                if row["method_available"] == "true":
                    self.assertGreaterEqual(float(row["energy_kwh"] or 0.0), 0.0)
                else:
                    # Honest gap: no fabricated figures, no fabricated gate.
                    self.assertEqual(row["energy_kwh"], "")
                    self.assertEqual(row["location_kg_co2e"], "")
                    self.assertEqual(row["market_kg_co2e"], "")
                    self.assertEqual(row["impact_level"], "")
                    self.assertEqual(row["recommendation"], "")
                    self.assertEqual(row["provenance_class"], "unknown")
                    self.assertEqual(row["confidence_score"], "0.00")
                    self.assertTrue(row["notes"].startswith("method unavailable:"))

            for module in ALL_WORKLOAD_MODULES:
                workload_rows = [
                    row for row in rows if row["workload_id"] == module.WORKLOAD_ID
                ]
                self.assertEqual(
                    sorted(row["measurement_method"] for row in workload_rows),
                    sorted(methods.METHOD_ORDER),
                )
                for row in workload_rows:
                    self.assertEqual(row["functional_unit"], module.FUNCTIONAL_UNIT)

            manual_rows = [
                row
                for row in rows
                if row["measurement_method"] == "manual_flop"
                and row["method_available"] == "true"
            ]
            if ANY_WORKLOAD_AVAILABLE:
                self.assertTrue(manual_rows)
            for row in manual_rows:
                self.assertGreater(float(row["energy_kwh"]), 0.0)
                self.assertGreaterEqual(float(row["duration_seconds"]), 0.0)
                self.assertEqual(row["impact_level"], "low")
                self.assertIn("PLACEHOLDER", row["notes"])


class FlopEstimatorTest(unittest.TestCase):
    # (module, config key whose doubling must double the FLOP estimate)
    LINEAR_KEYS = (
        (w1_classical_ml, "n_samples"),
        (w2_finetune, "steps"),
        (w3_rag, "n_queries"),
        (w4_batch_embed, "n_items"),
    )

    def test_flop_estimates_positive_finite_and_linear(self):
        for module, key in self.LINEAR_KEYS:
            with self.subTest(workload=module.WORKLOAD_ID, key=key):
                config = dict(module.DRY_CONFIG)
                base = module.flop_estimate(config)
                self.assertGreater(base, 0.0)
                self.assertTrue(math.isfinite(base))
                doubled = module.flop_estimate(dict(config, **{key: config[key] * 2}))
                self.assertTrue(math.isfinite(doubled))
                self.assertAlmostEqual(doubled / base, 2.0, places=9)

    def test_flop_estimates_scale_linearly_with_repeats(self):
        for module in (w1_classical_ml, w3_rag, w4_batch_embed):
            with self.subTest(workload=module.WORKLOAD_ID):
                config = dict(module.DRY_CONFIG)
                base = module.flop_estimate(config)
                tripled = module.flop_estimate(
                    dict(config, repeats=config.get("repeats", 1) * 3)
                )
                self.assertAlmostEqual(tripled / base, 3.0, places=9)

    def test_flop_estimates_need_no_optional_dependencies(self):
        # The analytic path must stay pure stdlib so the manual method and
        # these tests work on machines with no numpy, sklearn, or torch.
        for module in ALL_WORKLOAD_MODULES:
            value = module.flop_estimate(dict(module.REAL_CONFIG))
            self.assertGreater(value, 0.0)
            self.assertTrue(math.isfinite(value))


class ProvenanceMappingTest(unittest.TestCase):
    def test_method_to_provenance_mapping(self):
        self.assertEqual(
            methods.PROVENANCE_BY_METHOD,
            {
                "codecarbon": "tool_estimated",
                "cloud_billing": "vendor_reported",
                "manual_flop": "manual",
            },
        )

    def test_rows_carry_mapped_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "runs.csv"
            exit_code, _ = run_harness(
                ["--workload", "all", "--dry-run", "--output", str(output)]
            )
            self.assertEqual(exit_code, 0)
            for row in read_rows(output):
                if row["method_available"] == "true":
                    self.assertEqual(
                        row["provenance_class"],
                        methods.PROVENANCE_BY_METHOD[row["measurement_method"]],
                    )
                else:
                    self.assertEqual(row["provenance_class"], "unknown")


class CloudBillingTest(unittest.TestCase):
    def _write_billing(self, tmpdir: pathlib.Path, data_lines: list[str]) -> pathlib.Path:
        path = tmpdir / "billing.csv"
        lines = ["# operator-filled test fixture", BILLING_HEADER, *data_lines]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_operator_entry_becomes_vendor_reported_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            billing = self._write_billing(
                tmpdir,
                [
                    "classical_ml_training,1,aws,ec2,ap-south-1,2026-08-01,"
                    "2026-08-01,190,0.021,0.0089,0.0071,average,INV-42,carbon export"
                ],
            )
            output = tmpdir / "runs.csv"
            exit_code, _ = run_harness(
                [
                    "--workload", "w1_classical_ml", "--dry-run",
                    "--methods", "cloud_billing",
                    "--billing-file", str(billing),
                    "--output", str(output),
                ]
            )
            self.assertEqual(exit_code, 0)
            rows = read_rows(output)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["method_available"], "true")
            self.assertEqual(row["provenance_class"], "vendor_reported")
            self.assertEqual(row["confidence_score"], "0.60")
            self.assertEqual(float(row["energy_kwh"]), 0.021)
            self.assertEqual(float(row["market_kg_co2e"]), 0.0071)
            self.assertIn("INV-42", row["notes"])

    def test_missing_entry_is_recorded_unavailable_never_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            billing = self._write_billing(tmpdir, [])
            output = tmpdir / "runs.csv"
            exit_code, _ = run_harness(
                [
                    "--workload", "w1_classical_ml", "--dry-run",
                    "--methods", "cloud_billing",
                    "--billing-file", str(billing),
                    "--output", str(output),
                ]
            )
            self.assertEqual(exit_code, 0)
            row = read_rows(output)[0]
            self.assertEqual(row["method_available"], "false")
            self.assertEqual(row["energy_kwh"], "")
            self.assertIn("no operator billing entry", row["notes"])

    def test_entry_without_figures_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            billing = self._write_billing(
                tmpdir,
                ["classical_ml_training,1,aws,ec2,ap-south-1,,,,,,,average,INV-7,"],
            )
            output = tmpdir / "runs.csv"
            run_harness(
                [
                    "--workload", "w1_classical_ml", "--dry-run",
                    "--methods", "cloud_billing",
                    "--billing-file", str(billing),
                    "--output", str(output),
                ]
            )
            row = read_rows(output)[0]
            self.assertEqual(row["method_available"], "false")
            self.assertIn("neither energy_kwh nor any kg_co2e", row["notes"])

    def test_malformed_numeric_entries_are_skipped_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            billing = self._write_billing(
                tmpdir,
                [
                    "classical_ml_training,1,aws,ec2,ap-south-1,2026-08-01,"
                    "2026-08-01,190,not_a_number,,,average,INV-9,"
                ],
            )
            data = methods.load_billing_entries(billing)
            self.assertTrue(data.available)
            self.assertEqual(data.entries, {})
            self.assertTrue(any("not numeric" in w for w in data.warnings))

    def test_shipped_template_contains_no_data_rows(self):
        data = methods.load_billing_entries(harness.DEFAULT_BILLING_FILE)
        self.assertTrue(data.available)
        self.assertEqual(data.entries, {})
        self.assertEqual(data.warnings, [])


class UnavailableMethodHonestyTest(unittest.TestCase):
    def _forced_run(self, forced: set[str]) -> list[dict[str, str]]:
        original = set(methods.FORCE_UNAVAILABLE)
        methods.FORCE_UNAVAILABLE.clear()
        methods.FORCE_UNAVAILABLE.update(forced)
        self.addCleanup(
            lambda: (methods.FORCE_UNAVAILABLE.clear(),
                     methods.FORCE_UNAVAILABLE.update(original))
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "runs.csv"
            exit_code, _ = run_harness(
                ["--workload", "w1_classical_ml", "--dry-run", "--output", str(output)]
            )
            self.assertEqual(exit_code, 0)
            return read_rows(output)

    def test_forced_workload_unavailability_is_recorded_honestly(self):
        rows = self._forced_run({"classical_ml_training"})
        for row in rows:
            if row["measurement_method"] == "cloud_billing":
                continue  # billing availability is entry-driven, not import-driven
            self.assertEqual(row["method_available"], "false")
            self.assertIn("workload unavailable", row["notes"])
            self.assertEqual(row["energy_kwh"], "")
            self.assertEqual(row["provenance_class"], "unknown")
            self.assertEqual(row["recommendation"], "")

    def test_forced_codecarbon_unavailability_only_affects_that_method(self):
        rows = self._forced_run({"codecarbon"})
        by_method = {row["measurement_method"]: row for row in rows}
        codecarbon_row = by_method["codecarbon"]
        self.assertEqual(codecarbon_row["method_available"], "false")
        self.assertEqual(codecarbon_row["energy_kwh"], "")
        self.assertIn("unavailable", codecarbon_row["notes"])
        manual_row = by_method["manual_flop"]
        if W1_AVAILABLE:
            self.assertEqual(manual_row["method_available"], "true")
            self.assertEqual(manual_row["provenance_class"], "manual")
        else:
            self.assertEqual(manual_row["method_available"], "false")

    def test_confidence_diverges_across_methods_for_same_workload(self):
        # The paper's core mechanism: identical workload, different evidence
        # paths, different confidence. vendor_reported caps at 0.60 while the
        # manual estimate lands at 0.20.
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            billing = tmpdir / "billing.csv"
            billing.write_text(
                BILLING_HEADER + "\n"
                "classical_ml_training,1,aws,ec2,ap-south-1,2026-08-01,"
                "2026-08-01,190,0.021,0.0089,0.0071,average,INV-42,\n",
                encoding="utf-8",
            )
            output = tmpdir / "runs.csv"
            run_harness(
                [
                    "--workload", "w1_classical_ml", "--dry-run",
                    "--billing-file", str(billing),
                    "--output", str(output),
                ]
            )
            by_method = {
                row["measurement_method"]: row for row in read_rows(output)
            }
            self.assertEqual(by_method["cloud_billing"]["confidence_score"], "0.60")
            if W1_AVAILABLE:
                self.assertEqual(by_method["manual_flop"]["confidence_score"], "0.20")


class MitigationPairTest(unittest.TestCase):
    def test_mitigations_emit_valid_pre_post_pairs(self):
        rows = mitigations.run_mitigation_suite(
            workload="all", dry_run=True, seed=7
        )
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(
                list(row.keys()), mitigations.MITIGATION_CSV_COLUMNS
            )
            self.assertEqual(row["run_mode"], "dry_run")
            self.assertIn(
                row["mitigation_id"],
                {"quantization", "region_shift", "batching", "time_shift"},
            )

        by_mitigation: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_mitigation.setdefault(row["mitigation_id"], []).append(row)

        # Applicability matrix from the study design.
        self.assertEqual(
            sorted(r["workload_id"] for r in by_mitigation["quantization"]),
            ["rag_inference", "transformer_finetune"],
        )
        self.assertEqual(
            [r["workload_id"] for r in by_mitigation["batching"]],
            ["batch_embeddings"],
        )
        all_ids = sorted(m.WORKLOAD_ID for m in ALL_WORKLOAD_MODULES)
        for shared in ("region_shift", "time_shift"):
            self.assertEqual(
                sorted(r["workload_id"] for r in by_mitigation[shared]), all_ids
            )

        for row in rows:
            if row["method_available"] == "true":
                self.assertGreater(float(row["pre_energy_kwh"]), 0.0)
                self.assertGreater(float(row["post_energy_kwh"]), 0.0)
                self.assertEqual(row["provenance_class"], "manual")
                self.assertEqual(
                    row["intensity_source"], mitigations.INTENSITY_SOURCE
                )
                if row["mitigation_id"] == "region_shift":
                    self.assertEqual(row["pre_label"], "region=IND")
                    self.assertEqual(row["post_label"], "region=SWE")
                    self.assertLess(float(row["delta_location_pct"]), 0.0)
                    self.assertLess(float(row["delta_market_pct"]), 0.0)
                if row["mitigation_id"] == "time_shift":
                    self.assertLess(float(row["delta_location_pct"]), 0.0)
                    self.assertEqual(row["delta_market_pct"], "")
            else:
                self.assertEqual(row["pre_energy_kwh"], "")
                self.assertEqual(row["post_energy_kwh"], "")
                self.assertEqual(row["provenance_class"], "unknown")
                self.assertIn("unavailable", row["notes"])

    def test_mitigation_rows_write_to_schema_valid_csv(self):
        rows = mitigations.run_mitigation_suite(
            workload="w4_batch_embed", dry_run=True, seed=7
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "mitigations.csv"
            mitigations.write_mitigation_rows(path, rows)
            with path.open(newline="", encoding="utf-8") as handle:
                header = next(csv.reader(handle))
            self.assertEqual(header, mitigations.MITIGATION_CSV_COLUMNS)
            self.assertEqual(len(read_rows(path)), len(rows))


class DeterminismTest(unittest.TestCase):
    def test_manual_flop_rows_are_deterministic_for_a_fixed_seed(self):
        results = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                output = pathlib.Path(tmp) / "runs.csv"
                run_harness(
                    [
                        "--workload", "all", "--dry-run",
                        "--seed", "1337",
                        "--methods", "manual_flop",
                        "--output", str(output),
                    ]
                )
                results.append(
                    {
                        (row["workload_id"], row["run_id"]): (
                            row["energy_kwh"],
                            row["location_kg_co2e"],
                            row["market_kg_co2e"],
                            row["provenance_class"],
                            row["method_available"],
                        )
                        for row in read_rows(output)
                    }
                )
        self.assertEqual(results[0], results[1])

    @unittest.skipUnless(W1_AVAILABLE, "w1 dependencies not importable here")
    def test_workload_data_is_deterministic_for_a_fixed_seed(self):
        first = w1_classical_ml.run(dict(w1_classical_ml.DRY_CONFIG), seed=99)
        second = w1_classical_ml.run(dict(w1_classical_ml.DRY_CONFIG), seed=99)
        self.assertEqual(
            first["work_metrics"]["mean_cv_accuracy"],
            second["work_metrics"]["mean_cv_accuracy"],
        )


class GridIntensityTableTest(unittest.TestCase):
    def test_placeholder_labeling_is_explicit(self):
        self.assertIn("PLACEHOLDER", grid_intensity.DATA_SOURCE_NOTE)
        self.assertEqual(len(grid_intensity.HOURLY_SHAPE_MULTIPLIERS), 24)

    def test_unknown_region_raises_instead_of_guessing(self):
        with self.assertRaises(KeyError):
            grid_intensity.intensities_for("ATL")
        with self.assertRaises(ValueError):
            grid_intensity.hourly_location_intensity("IND", 24)



@unittest.skipUnless(
    importlib.util.find_spec("numpy"), "numpy not installed; run from the apps/backend venv"
)
class RunWindowTest(unittest.TestCase):
    """The power reference aligns on these timestamps, so they must be real."""

    def test_both_methods_of_one_iteration_share_one_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "runs.csv"
            harness.main([
                "--workload", "w1", "--iterations", "1", "--dry-run",
                "--output", str(output),
            ])
            rows = [r for r in read_rows(output) if r["method_available"] == "true"]
            self.assertTrue(rows, "expected at least one available method")
            windows = {(r["started_at"], r["ended_at"]) for r in rows}
            # codecarbon and manual_flop describe the SAME physical run, so a
            # divergent window would misattribute power samples between them.
            self.assertEqual(len(windows), 1)
            started, ended = windows.pop()
            self.assertTrue(started and ended, "timestamps must be populated")
            self.assertGreater(float(ended), float(started))

    def test_unavailable_methods_carry_no_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "runs.csv"
            harness.main([
                "--workload", "w1", "--iterations", "1", "--dry-run",
                "--output", str(output),
            ])
            for row in read_rows(output):
                if row["method_available"] == "false":
                    self.assertEqual(row["started_at"], "")
                    self.assertEqual(row["ended_at"], "")


if __name__ == "__main__":
    unittest.main()
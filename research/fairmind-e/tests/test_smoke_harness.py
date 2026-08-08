import csv
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_smoke.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("fairmind_e_run_smoke", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SmokeHarnessTest(unittest.TestCase):
    def test_runner_writes_deterministic_csv_and_svg_outputs(self):
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = pathlib.Path(tmpdir)
            exit_code = runner.main(
                [
                    "--config-dir",
                    str(ROOT / "configs"),
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(exit_code, 0)

            csv_path = output_root / "results" / "classical_ml_training" / "smoke.csv"
            svg_path = output_root / "plots" / "fairmind_e_smoke_summary.svg"
            self.assertTrue(csv_path.exists())
            self.assertTrue(svg_path.exists())

            with csv_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["workload_id"], "classical_ml_training")
            self.assertEqual(rows[0]["provenance_class"], "measured")
            self.assertEqual(rows[1]["provenance_class"], "vendor_reported")
            self.assertEqual(rows[1]["confidence_score"], "0.60")
            self.assertEqual(rows[2]["provenance_class"], "unknown")
            self.assertEqual(rows[2]["impact_level"], "moderate")
            self.assertEqual(rows[2]["recommendation"], "no_go")
            self.assertEqual(rows[2]["offsets_retired_kg_co2e"], "10.000")

            svg_text = svg_path.read_text(encoding="utf-8")
            self.assertIn("<svg", svg_text)
            self.assertIn("FairMind-E smoke summary", svg_text)

    def test_offsets_do_not_improve_confidence_or_recommendation(self):
        runner = load_runner()

        base = {
            "provenance_class": "vendor_reported",
            "uncertainty_pct": 15,
            "impact_level": "high",
            "intensity_vs_baseline": 2.5,
            "mitigation_readiness": "none",
            "location_kg_co2e": 12.0,
            "market_kg_co2e": 8.0,
        }
        with_offsets = dict(base, offsets_retired_kg_co2e=25.0)
        without_offsets = dict(base, offsets_retired_kg_co2e=0.0)

        self.assertEqual(
            runner.assess_record(with_offsets),
            runner.assess_record(without_offsets),
        )


if __name__ == "__main__":
    unittest.main()

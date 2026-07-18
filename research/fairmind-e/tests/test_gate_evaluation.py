import csv
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "evaluation" / "evaluate_gate.py"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("fairmind_e_evaluate_gate", EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GateEvaluationTest(unittest.TestCase):
    def test_evaluator_writes_deterministic_paper_outputs(self):
        evaluator = load_evaluator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = pathlib.Path(tmpdir)
            exit_code = evaluator.main(
                [
                    "--fixtures",
                    str(ROOT / "evaluation" / "fixtures" / "paper_gate_cases.json"),
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(exit_code, 0)

            csv_path = output_root / "results" / "paper_gate_eval.csv"
            baseline_path = output_root / "results" / "paper_baseline_comparison.csv"
            summary_path = output_root / "results" / "paper_gate_summary.md"
            svg_path = output_root / "plots" / "paper_gate_decisions.svg"
            baseline_svg_path = output_root / "plots" / "paper_baseline_accuracy.svg"
            self.assertTrue(csv_path.exists())
            self.assertTrue(baseline_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertTrue(baseline_svg_path.exists())

            with csv_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 14)
            self.assertTrue(all(row["match"] == "true" for row in rows))

            by_id = {row["case_id"]: row for row in rows}
            self.assertEqual(
                by_id["vendor_claimed_high_confidence_capped"]["actual_confidence_score"],
                "0.60",
            )
            self.assertEqual(
                by_id["offsets_do_not_rescue_unknown"]["actual_recommendation"],
                "no_go",
            )
            self.assertEqual(
                by_id["exception_allows_conditional_review"]["actual_approval_blocking"],
                "false",
            )

            with baseline_path.open(newline="", encoding="utf-8") as handle:
                baseline_rows = list(csv.DictReader(handle))
            self.assertEqual(len(baseline_rows), 98)
            by_baseline = {}
            for row in baseline_rows:
                by_baseline.setdefault(row["baseline"], []).append(row)
            self.assertEqual(
                sum(1 for row in by_baseline["fairmind_e"] if row["exact_match"] == "true"),
                14,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["no_environmental_gate"] if row["exact_match"] == "true"),
                3,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["carbon_only_gate"] if row["exact_match"] == "true"),
                7,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["generic_sustainability_score"] if row["exact_match"] == "true"),
                6,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["no_mitigation_review_gate"] if row["exact_match"] == "true"),
                11,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["no_exception_path"] if row["exact_match"] == "true"),
                13,
            )
            self.assertEqual(
                sum(1 for row in by_baseline["offset_credit_gate"] if row["exact_match"] == "true"),
                13,
            )

            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Exact label accuracy: 14/14 (100.0%)", summary)
            self.assertIn("| fairmind_e | 14/14 | 100.0% | 14/14 | 14/14 |", summary)
            self.assertIn("| no_environmental_gate | 3/14 | 21.4% | 3/14 | 6/14 |", summary)
            self.assertIn("| no_mitigation_review_gate | 11/14 | 78.6% | 14/14 | 11/14 |", summary)
            self.assertIn("| no_exception_path | 13/14 | 92.9% | 14/14 | 13/14 |", summary)
            self.assertIn("| offset_credit_gate | 13/14 | 92.9% | 13/14 | 13/14 |", summary)
            self.assertIn("None.", summary)


if __name__ == "__main__":
    unittest.main()

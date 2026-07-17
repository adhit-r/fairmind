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
            summary_path = output_root / "results" / "paper_gate_summary.md"
            svg_path = output_root / "plots" / "paper_gate_decisions.svg"
            self.assertTrue(csv_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(svg_path.exists())

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

            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Exact label accuracy: 14/14 (100.0%)", summary)
            self.assertIn("None.", summary)


if __name__ == "__main__":
    unittest.main()

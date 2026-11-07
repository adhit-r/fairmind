"""
Unit tests for the FairMind-E expert-panel instrument.

Covers the design invariants that the analysis depends on (balanced arms,
disjoint per-rater profile sets, arm-appropriate packet content) and the
response importer's validation and scoring behaviour.

Run:
    python3 research/fairmind-e/tests/test_panel_instrument.py
"""

from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent.parent / "panel"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, PANEL_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build_instrument = _load("build_instrument")
import_responses = _load("import_responses")


class ArmAssignmentTest(unittest.TestCase):
    def setUp(self):
        rows = build_instrument.load_assignments(PANEL_DIR / "assignment_plan.csv")
        self.assignments = build_instrument.assign_arms(rows)

    def test_every_rater_has_an_even_arm_split(self):
        by_rater: dict[str, list[str]] = {}
        for row in self.assignments:
            by_rater.setdefault(row["rater_id"], []).append(row["arm"])
        for rater_id, arms in by_rater.items():
            baseline = arms.count(build_instrument.BASELINE)
            module = arms.count(build_instrument.MODULE)
            self.assertEqual(baseline, module, f"{rater_id} split {baseline}/{module}")

    def test_every_profile_is_balanced_across_arms(self):
        counts: dict[str, dict[str, int]] = {}
        for row in self.assignments:
            entry = counts.setdefault(
                row["profile_id"],
                {build_instrument.BASELINE: 0, build_instrument.MODULE: 0},
            )
            entry[row["arm"]] += 1
        for profile_id, entry in counts.items():
            baseline = entry[build_instrument.BASELINE]
            module = entry[build_instrument.MODULE]
            self.assertGreaterEqual(baseline, 2, profile_id)
            self.assertGreaterEqual(module, 2, profile_id)
            self.assertLessEqual(abs(baseline - module), 1, f"{profile_id} imbalanced")

    def test_no_rater_sees_a_profile_twice(self):
        by_rater: dict[str, list[str]] = {}
        for row in self.assignments:
            by_rater.setdefault(row["rater_id"], []).append(row["profile_id"])
        for rater_id, profile_ids in by_rater.items():
            self.assertEqual(
                len(profile_ids), len(set(profile_ids)), f"{rater_id} repeats a profile"
            )

    def test_assignment_is_deterministic(self):
        rows = build_instrument.load_assignments(PANEL_DIR / "assignment_plan.csv")
        again = build_instrument.assign_arms(rows)
        self.assertEqual(
            [(r["rater_id"], r["profile_id"], r["arm"]) for r in self.assignments],
            [(r["rater_id"], r["profile_id"], r["arm"]) for r in again],
        )

    def test_design_check_passes(self):
        summary = build_instrument.build(check_only=True)
        self.assertEqual(summary["problems"], [])


class PacketContentTest(unittest.TestCase):
    def setUp(self):
        self.profiles = build_instrument.load_profiles(
            PANEL_DIR.parent / "profiles" / "profiles.json"
        )
        self.profile = self.profiles["P01"]

    def test_baseline_packet_hides_the_module_output(self):
        text = "\n".join(build_instrument.render_profile(self.profile, "baseline", 1))
        self.assertNotIn("FairMind-E assessment output", text)
        self.assertNotIn("Evidence confidence:", text)
        self.assertNotIn("Impact tier:", text)
        self.assertNotIn("Module recommendation:", text)
        self.assertNotIn("Decision-matrix position", text)

    def test_module_packet_shows_the_module_output(self):
        text = "\n".join(build_instrument.render_profile(self.profile, "module", 1))
        self.assertIn("FairMind-E assessment output", text)
        self.assertIn("Evidence confidence:", text)
        self.assertIn("Impact tier:", text)
        self.assertIn("Module recommendation:", text)

    def test_both_arms_share_the_raw_measurement_stimulus(self):
        baseline = "\n".join(build_instrument.render_profile(self.profile, "baseline", 1))
        module = "\n".join(build_instrument.render_profile(self.profile, "module", 1))
        for text in (baseline, module):
            self.assertIn("Reported measurements", text)
            self.assertIn("Declared boundary", text)
            self.assertIn("Measurement source as submitted", text)

    def test_manipulation_check_only_on_module_items(self):
        baseline = "\n".join(build_instrument.render_profile(self.profile, "baseline", 1))
        module = "\n".join(build_instrument.render_profile(self.profile, "module", 1))
        self.assertNotIn("Manipulation check", baseline)
        self.assertIn("Manipulation check", module)


class ImporterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.arms_path = self.tmp_path / "arms.csv"
        self.gold_path = self.tmp_path / "gold.csv"

        with self.arms_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["rater_id", "role", "position", "profile_id", "arm", "block"])
            writer.writerow(["R01", "GRC", "1", "P01", "baseline", "first"])
            writer.writerow(["R02", "ESG", "1", "P01", "module", "first"])
            writer.writerow(["R03", "ML_ENG", "1", "P01", "module", "first"])

        with self.gold_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["profile_id", "control", "applicable", "requirement"])
            for code in build_instrument.ENV_CONTROLS:
                writer.writerow(["P01", code, "yes", "x"])

    def tearDown(self):
        self.tmp.cleanup()

    def _write_responses(self, rows: list[dict[str, str]]) -> Path:
        path = self.tmp_path / "raw.csv"
        fieldnames = [
            "rater_id",
            "profile_id",
            "recommendation",
            "controls_required",
            "decision_confidence_1_5",
            "time_to_decision_s",
            "confidence_shown",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})
        return path

    def _run(self, rows):
        return import_responses.import_responses(
            self._write_responses(rows),
            self.arms_path,
            self.gold_path,
            self.tmp_path / "out",
        )

    def test_coverage_rate_is_demanded_over_applicable(self):
        summary = self._run(
            [
                {
                    "rater_id": "R01",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "controls_required": "ENV-1;ENV-2",  # 2 of 6
                    "decision_confidence_1_5": "4",
                },
                {
                    "rater_id": "R02",
                    "profile_id": "P01",
                    "recommendation": "no_go",
                    "controls_required": "ENV-1;ENV-2;ENV-3;ENV-4;ENV-5;ENV-6",  # 6 of 6
                    "decision_confidence_1_5": "5",
                    "confidence_shown": "yes",
                },
            ]
        )
        self.assertEqual(summary["problems"], [])
        with (self.tmp_path / "out" / "coverage_pre_post.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(float(rows[0]["coverage_rate_pre"]), 2 / 6, places=6)
        self.assertAlmostEqual(float(rows[0]["coverage_rate_post"]), 1.0, places=6)

    def test_failed_manipulation_check_is_excluded_and_counted(self):
        summary = self._run(
            [
                {
                    "rater_id": "R02",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "controls_required": "ENV-1",
                    "decision_confidence_1_5": "3",
                    "confidence_shown": "no",
                },
            ]
        )
        self.assertEqual(summary["manipulation_check_failures"], 1)
        self.assertEqual(summary["panel_rows"], 0)
        # The response still contributes its coverage observation.
        self.assertEqual(summary["coverage_pairs"], 0)  # no baseline partner

    def test_unknown_pair_and_bad_recommendation_are_reported_not_repaired(self):
        summary = self._run(
            [
                {
                    "rater_id": "R99",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "decision_confidence_1_5": "3",
                },
                {
                    "rater_id": "R01",
                    "profile_id": "P01",
                    "recommendation": "maybe",
                    "decision_confidence_1_5": "3",
                },
            ]
        )
        self.assertEqual(summary["panel_rows"], 0)
        self.assertEqual(len(summary["problems"]), 2)
        self.assertIn("assignment plan", summary["problems"][0])
        self.assertIn("recommendation", summary["problems"][1])

    def test_blank_manipulation_check_on_module_item_is_reported(self):
        summary = self._run(
            [
                {
                    "rater_id": "R02",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "controls_required": "ENV-1",
                    "decision_confidence_1_5": "3",
                },
            ]
        )
        self.assertEqual(summary["panel_rows"], 0)
        self.assertEqual(summary["manipulation_check_failures"], 0)
        self.assertTrue(any("confidence_shown" in p for p in summary["problems"]))

    def test_duplicate_response_keeps_first_and_reports_rest(self):
        row = {
            "rater_id": "R01",
            "profile_id": "P01",
            "recommendation": "go",
            "controls_required": "ENV-1",
            "decision_confidence_1_5": "3",
        }
        summary = self._run([row, dict(row, recommendation="no_go")])
        self.assertEqual(summary["panel_rows"], 1)
        self.assertTrue(any("duplicate" in p for p in summary["problems"]))
        with (self.tmp_path / "out" / "panel_responses.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["recommendation"], "go")

    def test_out_of_range_confidence_is_rejected(self):
        summary = self._run(
            [
                {
                    "rater_id": "R01",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "controls_required": "ENV-1",
                    "decision_confidence_1_5": "9",
                },
            ]
        )
        self.assertEqual(summary["panel_rows"], 0)
        self.assertTrue(any("outside 1-5" in p for p in summary["problems"]))

    def test_role_is_joined_from_the_assignment_plan(self):
        self._run(
            [
                {
                    "rater_id": "R01",
                    "profile_id": "P01",
                    "recommendation": "go",
                    "controls_required": "ENV-1",
                    "decision_confidence_1_5": "4",
                },
            ]
        )
        with (self.tmp_path / "out" / "panel_responses.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["rater_role"], "GRC")
        self.assertEqual(rows[0]["arm"], "baseline")

    def test_parse_controls_handles_separators_and_blanks(self):
        self.assertEqual(import_responses.parse_controls("ENV-1;ENV-3"), ["ENV-1", "ENV-3"])
        self.assertEqual(import_responses.parse_controls("env-1, env-2"), ["ENV-1", "ENV-2"])
        self.assertEqual(import_responses.parse_controls(""), [])
        self.assertEqual(import_responses.parse_controls(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)

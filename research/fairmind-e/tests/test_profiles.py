import csv
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "profiles" / "generate_profiles.py"

EXPECTED_CELL_COUNTS = {
    "low+measured": 1,
    "low+estimated": 1,
    "low+unknown": 2,
    "medium+measured": 1,
    "medium+estimated": 2,
    "medium+unknown": 1,
    "high+measured": 2,
    "high+estimated": 1,
    "high+unknown": 1,
}


def load_generator():
    spec = importlib.util.spec_from_file_location("fairmind_e_generate_profiles", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProfileMatrixDesignTest(unittest.TestCase):
    def test_twelve_profiles_cover_matrix_with_boundary_extras(self):
        generator = load_generator()
        profiles = generator.PROFILES

        self.assertEqual(len(profiles), 12)
        self.assertEqual([p["id"] for p in profiles], [f"P{i:02d}" for i in range(1, 13)])
        self.assertEqual(generator.matrix_cell_counts(profiles), EXPECTED_CELL_COUNTS)

    def test_conditional_profiles_deliberately_vary_approval_blocking(self):
        generator = load_generator()
        by_id = {p["id"]: p for p in generator.PROFILES}

        # Doubled cells flip blocking (or the unblocking path) inside the cell.
        self.assertTrue(by_id["P03"]["expected"]["approval_blocking"])
        self.assertFalse(by_id["P10"]["expected"]["approval_blocking"])
        self.assertTrue(by_id["P12"]["expected"]["approval_blocking"])
        self.assertFalse(by_id["P05"]["expected"]["approval_blocking"])
        self.assertFalse(by_id["P07"]["expected"]["approval_blocking"])
        self.assertTrue(by_id["P07"]["expected"]["has_dated_mitigation"])
        self.assertFalse(by_id["P11"]["expected"]["approval_blocking"])
        self.assertTrue(by_id["P11"]["expected"]["has_exception"])

        # Every no_go profile blocks approval.
        for profile in generator.PROFILES:
            if profile["expected"]["recommendation"] == "no_go":
                self.assertTrue(profile["expected"]["approval_blocking"], profile["id"])


class ProfileEngineAgreementTest(unittest.TestCase):
    def test_engine_agrees_with_every_expected_label(self):
        generator = load_generator()
        failures = generator.validate_profiles(generator.PROFILES)
        self.assertEqual(failures, [])


class ProfileOutputsTest(unittest.TestCase):
    def test_checked_in_outputs_match_regeneration(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generator.generate(pathlib.Path(tmpdir))
            checked_in = {
                "profiles_json": ROOT / "profiles" / "profiles.json",
                "panel_pack": ROOT / "profiles" / "PROFILES.md",
                "answer_key": ROOT / "profiles" / "ANSWER_KEY.md",
                "assignment_plan": ROOT / "panel" / "assignment_plan.csv",
            }
            for name, generated_path in paths.items():
                self.assertTrue(checked_in[name].exists(), name)
                self.assertEqual(
                    generated_path.read_bytes(),
                    checked_in[name].read_bytes(),
                    f"{name} is stale; re-run profiles/generate_profiles.py",
                )

    def test_profiles_json_contract(self):
        with (ROOT / "profiles" / "profiles.json").open(encoding="utf-8") as handle:
            document = json.load(handle)

        self.assertEqual(document["profile_count"], 12)
        self.assertEqual(document["matrix_cells"], EXPECTED_CELL_COUNTS)
        for profile in document["profiles"]:
            for key in ("id", "title", "matrix_cell", "description", "assessment", "expected", "rationale"):
                self.assertIn(key, profile, profile.get("id"))
            expected = profile["expected"]
            for key in (
                "recommendation",
                "risk_tier",
                "confidence_band",
                "approval_blocking",
                "coverage",
            ):
                self.assertIn(key, expected, profile["id"])
            self.assertEqual(
                sorted(expected["coverage"]),
                ["ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6"],
                profile["id"],
            )

    def test_panel_pack_carries_no_answer_key_and_outputs_are_ascii(self):
        generator = load_generator()
        pack = (ROOT / "profiles" / "PROFILES.md").read_text(encoding="utf-8")

        self.assertNotIn("expected_", pack)
        self.assertNotIn("Matrix cell:", pack)
        self.assertNotIn("Answer", pack)
        for profile in generator.PROFILES:
            self.assertNotIn(profile["rationale"][:60], pack, profile["id"])

        for relative in (
            "profiles/generate_profiles.py",
            "profiles/profiles.json",
            "profiles/PROFILES.md",
            "profiles/ANSWER_KEY.md",
            "panel/assignment_plan.csv",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertTrue(text.isascii(), f"{relative} must be ASCII-only (no emoji)")


class AssignmentPlanTest(unittest.TestCase):
    def test_assignment_plan_is_counterbalanced(self):
        with (ROOT / "panel" / "assignment_plan.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 120)

        raters = {}
        role_of_rater = {}
        per_profile = {}
        per_profile_role = {}
        for row in rows:
            raters.setdefault(row["rater_id"], []).append((int(row["position"]), row["profile_id"]))
            role_of_rater[row["rater_id"]] = row["role"]
            per_profile[row["profile_id"]] = per_profile.get(row["profile_id"], 0) + 1
            key = (row["profile_id"], row["role"])
            per_profile_role[key] = per_profile_role.get(key, 0) + 1

        self.assertEqual(len(raters), 15)
        roles = sorted(role_of_rater.values())
        self.assertEqual(roles.count("GRC"), 5)
        self.assertEqual(roles.count("ML_ENG"), 5)
        self.assertEqual(roles.count("ESG"), 5)

        for rater_id, assignments in raters.items():
            positions = sorted(position for position, _ in assignments)
            self.assertEqual(positions, list(range(1, 9)), rater_id)
            profile_ids = {profile_id for _, profile_id in assignments}
            self.assertEqual(len(profile_ids), 8, rater_id)

        self.assertEqual(sorted(per_profile), [f"P{i:02d}" for i in range(1, 13)])
        self.assertEqual(set(per_profile.values()), {10})
        for key, count in per_profile_role.items():
            self.assertGreaterEqual(count, 2, key)


if __name__ == "__main__":
    unittest.main()

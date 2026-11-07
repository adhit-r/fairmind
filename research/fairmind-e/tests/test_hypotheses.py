"""Known-answer tests for the FairMind-E hypothesis statistics module.

Every statistic is validated against small hand-computed fixtures. When
scipy/sklearn are importable the preferred implementations are checked
against the stdlib fallbacks to 1e-6 on statistics.
"""

import importlib.util
import json
import math
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "analysis" / "hypotheses.py"
FIXTURES = ROOT / "analysis" / "fixtures"
PANEL_FIXTURE = FIXTURES / "panel_responses_SYNTHETIC.csv"
RUNS_FIXTURE = FIXTURES / "measurement_runs_SYNTHETIC.csv"
COVERAGE_FIXTURE = FIXTURES / "coverage_pre_post_SYNTHETIC.csv"
MITIGATION_FIXTURE = FIXTURES / "mitigation_pairs_SYNTHETIC.csv"
PROFILES_JSON = ROOT / "profiles" / "profiles.json"


def load_module():
    spec = importlib.util.spec_from_file_location("fairmind_e_hypotheses", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HYP = load_module()


def panel_row(rater_id, role, profile_id, recommendation):
    return {
        "rater_id": rater_id,
        "rater_role": role,
        "profile_id": profile_id,
        "recommendation": recommendation,
        "decision_confidence_1_5": 4,
        "decisive_controls": ["ENV-1"],
        "time_to_decision_s": 30.0,
    }


def hand_panel_rows():
    """3 raters x 4 profiles; Fleiss kappa 1/3, mean pairwise Cohen 0.4."""

    ratings = {
        "R1": {"P1": "go", "P2": "go", "P3": "go", "P4": "no_go"},
        "R2": {"P1": "go", "P2": "go", "P3": "no_go", "P4": "no_go"},
        "R3": {"P1": "go", "P2": "no_go", "P3": "no_go", "P4": "no_go"},
    }
    roles = {"R1": "GRC", "R2": "ML_ENG", "R3": "ESG"}
    return [
        panel_row(rater, roles[rater], profile, label)
        for rater, per_profile in ratings.items()
        for profile, label in per_profile.items()
    ]


class RankSpearmanTest(unittest.TestCase):
    def test_midranks_handle_ties(self):
        self.assertEqual(HYP.rank_midrank([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])

    def test_perfect_negative_monotone(self):
        result = HYP.spearman_correlation([5, 4, 3, 2, 1], [1, 2, 3, 4, 5])
        self.assertAlmostEqual(result["rho"], -1.0, places=12)
        self.assertAlmostEqual(result["p_value"], 0.0, places=12)

    def test_hand_computed_tie_case(self):
        # ranks x = [1, 2.5, 2.5, 4], ranks y = [1, 3.5, 3.5, 2]
        # Pearson on ranks = 1/3; t = 0.5 with df = 2 gives p = 2/3.
        result = HYP.spearman_correlation([1, 2, 2, 4], [10, 30, 30, 20], engine="stdlib")
        self.assertEqual(result["implementation"], "stdlib")
        self.assertAlmostEqual(result["rho"], 1.0 / 3.0, places=12)
        self.assertAlmostEqual(result["p_value"], 2.0 / 3.0, places=9)

    def test_constant_input_undefined(self):
        result = HYP.spearman_correlation([1, 1, 1, 1], [1, 2, 3, 4])
        self.assertIsNone(result["rho"])
        self.assertIn("constant", result["note"])

    def test_h1_hand_case_direction(self):
        # conf ranks [5,4,3,2,1] vs ordinal ranks [1.5,1.5,3,4.5,4.5]
        # gives rho = -3/sqrt(10).
        pairs = [
            (0.9, "go"),
            (0.8, "go"),
            (0.6, "conditional_go"),
            (0.4, "no_go"),
            (0.2, "no_go"),
        ]
        entry = HYP.h1_from_pairs(pairs, "unit_test", engine="stdlib")
        self.assertAlmostEqual(entry["rho"], -3.0 / math.sqrt(10.0), places=12)
        self.assertTrue(entry["direction_consistent"])

    def test_ordinal_mapping_is_pre_specified(self):
        self.assertEqual(
            HYP.RECOMMENDATION_ORDINAL, {"go": 0, "conditional_go": 1, "no_go": 2}
        )


class KappaTest(unittest.TestCase):
    def test_cohen_hand_case(self):
        # Classic 2x2 table (20, 5, 10, 15): po = 0.7, pe = 0.5, kappa = 0.4.
        rater_a = ["yes"] * 25 + ["no"] * 25
        rater_b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
        result = HYP.cohen_kappa(rater_a, rater_b, labels=("yes", "no"), engine="stdlib")
        self.assertAlmostEqual(result["kappa"], 0.4, places=12)
        self.assertAlmostEqual(result["observed_agreement"], 0.7, places=12)
        self.assertAlmostEqual(result["expected_agreement"], 0.5, places=12)

    def test_cohen_degenerate_identical_constant(self):
        result = HYP.cohen_kappa(["go"] * 4, ["go"] * 4)
        self.assertTrue(result["degenerate"])
        self.assertEqual(result["kappa"], 1.0)

    def test_cohen_disjoint_constant_labelings(self):
        # pe = 0, po = 0: kappa = 0 without degeneracy.
        result = HYP.cohen_kappa(["go"] * 4, ["no_go"] * 4, engine="stdlib")
        self.assertFalse(result["degenerate"])
        self.assertAlmostEqual(result["kappa"], 0.0, places=12)

    def test_fleiss_hand_case(self):
        # Counts [[3,0],[2,1],[1,2],[0,3]]: P_bar = 2/3, P_e = 1/2, kappa = 1/3.
        result = HYP.fleiss_kappa_from_counts([[3, 0], [2, 1], [1, 2], [0, 3]])
        self.assertAlmostEqual(result["kappa"], 1.0 / 3.0, places=12)
        expected_agreement = [1.0, 1.0 / 3.0, 1.0 / 3.0, 1.0]
        for computed, expected in zip(result["per_item_agreement"], expected_agreement):
            self.assertAlmostEqual(computed, expected, places=12)

    def test_fleiss_varying_rater_counts(self):
        # [[2,0],[1,1]]: P_bar = 1/2, P_e = 5/8, kappa = -1/3.
        result = HYP.fleiss_kappa_from_counts([[2, 0], [1, 1]])
        self.assertAlmostEqual(result["kappa"], -1.0 / 3.0, places=12)

    def test_h3_driver_hand_values(self):
        rows = hand_panel_rows()
        result = HYP.h3_agreement(rows, {}, seed=7, n_boot=100, engine="stdlib")
        pooled = result["pooled"]
        self.assertAlmostEqual(pooled["fleiss_kappa"], 1.0 / 3.0, places=12)
        self.assertAlmostEqual(pooled["mean_pairwise_cohen_kappa"], 0.4, places=12)
        self.assertEqual(pooled["n_rater_pairs"], 3)
        self.assertFalse(pooled["target_met_fleiss"])
        self.assertIsNotNone(pooled["fleiss_ci95"])
        self.assertIsNotNone(pooled["cohen_ci95"])
        per_profile = {entry["profile_id"]: entry for entry in result["per_profile"]}
        self.assertAlmostEqual(per_profile["P1"]["observed_agreement"], 1.0, places=12)
        self.assertAlmostEqual(
            per_profile["P2"]["observed_agreement"], 1.0 / 3.0, places=12
        )
        self.assertEqual(per_profile["P2"]["modal_recommendation"], "go")
        self.assertEqual(per_profile["P3"]["modal_recommendation"], "no_go")
        # One rater per role: by-role agreement must be undefined, not invented.
        for role in HYP.RATER_ROLES:
            self.assertIsNone(result["by_role"][role]["fleiss_kappa"])

    def test_h3_bootstrap_is_deterministic(self):
        rows = hand_panel_rows()
        first = HYP.h3_agreement(rows, {}, seed=11, n_boot=150, engine="stdlib")
        second = HYP.h3_agreement(rows, {}, seed=11, n_boot=150, engine="stdlib")
        self.assertEqual(first["pooled"]["fleiss_ci95"], second["pooled"]["fleiss_ci95"])
        self.assertEqual(first["pooled"]["cohen_ci95"], second["pooled"]["cohen_ci95"])

    def test_h3_expected_label_join(self):
        rows = hand_panel_rows()
        profiles = {
            "P1": {"expected_recommendation": "go", "confidence_score": 0.9},
            "P2": {"expected_recommendation": "go", "confidence_score": 0.75},
            "P3": {"expected_recommendation": "no_go", "confidence_score": 0.4},
            "P4": {"expected_recommendation": "no_go", "confidence_score": 0.2},
        }
        result = HYP.h3_agreement(rows, profiles, seed=3, n_boot=50, engine="stdlib")
        per_profile = {entry["profile_id"]: entry for entry in result["per_profile"]}
        self.assertTrue(per_profile["P1"]["modal_matches_expected"])
        self.assertTrue(per_profile["P3"]["modal_matches_expected"])
        self.assertAlmostEqual(
            result["pooled"]["modal_matches_expected_rate"], 1.0, places=12
        )


class PairedTestsTest(unittest.TestCase):
    def test_wilcoxon_hand_statistic_and_fallback_p(self):
        # d = [2, 3, 1, -1]; ranks of |d| = [3, 4, 1.5, 1.5]; R+ = 8.5,
        # R- = 1.5, statistic = 1.5; z = 3.5/sqrt(7.375) with the tie
        # correction, two-sided normal p about 0.19747.
        result = HYP.wilcoxon_signed_rank(
            [12, 15, 10, 10], [10, 12, 9, 11], engine="stdlib"
        )
        self.assertEqual(result["statistic"], 1.5)
        self.assertAlmostEqual(result["p_value"], 0.19747, delta=5e-4)
        self.assertIn("normal approximation", result["p_method"])

    def test_wilcoxon_all_zero_differences(self):
        result = HYP.wilcoxon_signed_rank([1.0, 2.0], [1.0, 2.0])
        self.assertIsNone(result["statistic"])
        self.assertIn("zero", result["note"])

    def test_paired_ttest_hand_case(self):
        # d = [1, 2, 3]: t = 2*sqrt(3), df = 2, p = 1 - t/sqrt(t^2+2).
        result = HYP.paired_ttest([5, 6, 7], [4, 4, 4], engine="stdlib")
        self.assertAlmostEqual(result["t_statistic"], 2.0 * math.sqrt(3.0), places=12)
        self.assertAlmostEqual(result["p_value"], 0.07417990, places=8)
        self.assertEqual(result["df"], 2)

    def test_paired_ttest_zero_variance(self):
        result = HYP.paired_ttest([2, 3, 4], [1, 2, 3])
        self.assertIsNone(result["t_statistic"])
        self.assertIn("zero variance", result["note"])

    def test_h2_driver_on_fixture(self):
        rows = HYP.load_coverage(COVERAGE_FIXTURE)
        result = HYP.h2_coverage(rows, engine="stdlib")
        self.assertEqual(result["n_systems"], 8)
        self.assertEqual(result["n_nonzero"], 7)
        self.assertEqual(result["n_zero_dropped"], 1)
        self.assertEqual(result["statistic"], 0.0)
        self.assertAlmostEqual(result["median_delta"], 0.25, places=9)
        self.assertEqual(result["n_improved"], 7)
        self.assertEqual(result["n_unchanged"], 1)
        self.assertLess(result["p_value"], 0.05)

    def test_h4_driver_on_fixture(self):
        rows = HYP.load_mitigation(MITIGATION_FIXTURE)
        result = HYP.h4_mitigation(rows, seed=5, n_boot=200, engine="stdlib")
        self.assertEqual(result["n_pairs"], 6)
        self.assertAlmostEqual(result["mean_pct_reduction"], 160.0 / 6.0, places=9)
        # d = [30, 50, 24, 28, 30, 27]: mean 31.5, sum of squared deviations
        # 435.5, sample variance 87.1, so t = 31.5 * sqrt(6 / 87.1).
        self.assertAlmostEqual(
            result["t_statistic"], 31.5 * math.sqrt(6.0 / 87.1), places=9
        )
        self.assertLess(result["p_value"], 0.001)
        self.assertTrue(result["target_met_point"])
        low, high = result["pct_reduction_ci95"]
        self.assertLess(low, result["mean_pct_reduction"])
        self.assertGreater(high, result["mean_pct_reduction"])
        repeat = HYP.h4_mitigation(rows, seed=5, n_boot=200, engine="stdlib")
        self.assertEqual(result["pct_reduction_ci95"], repeat["pct_reduction_ci95"])


class AccuracyTest(unittest.TestCase):
    def test_mape_hand_case(self):
        self.assertAlmostEqual(HYP.mape_pct([100, 200], [110, 180]), 10.0, places=12)

    def test_mape_zero_reference_raises(self):
        with self.assertRaises(ValueError):
            HYP.mape_pct([0.0, 1.0], [1.0, 1.0])

    def test_bland_altman_hand_case(self):
        # diffs = [1, -1, 2, 0]: bias 0.5, sd sqrt(5/3).
        result = HYP.bland_altman([10, 12, 9, 11], [11, 11, 11, 11])
        expected_sd = math.sqrt(5.0 / 3.0)
        self.assertAlmostEqual(result["mean_bias"], 0.5, places=12)
        self.assertAlmostEqual(result["sd_diff"], expected_sd, places=12)
        self.assertAlmostEqual(result["loa95_low"], 0.5 - 1.96 * expected_sd, places=12)
        self.assertAlmostEqual(result["loa95_high"], 0.5 + 1.96 * expected_sd, places=12)

    def test_accuracy_driver_on_fixture(self):
        rows = HYP.load_measurement_runs(RUNS_FIXTURE)
        result = HYP.measurement_accuracy(rows, metric="energy_kwh")
        self.assertEqual(
            result["methods_present"], ["codecarbon", "cloud_billing", "manual_flop"]
        )
        self.assertEqual(result["n_rows_excluded"], 1)
        by_pair = {
            (row["method_ref"], row["method_alt"]): row for row in result["mape"]
        }
        # Hand: mean of 0.7/9.8, 0.7/10.2, 0.15/1.2, 0.12/1.3 = 8.934093 pct.
        row = by_pair[("codecarbon", "cloud_billing")]
        self.assertEqual(row["n_runs"], 4)
        self.assertAlmostEqual(row["mape_pct"], 8.934093, places=5)
        ba = {(row["method_a"], row["method_b"]): row for row in result["bland_altman"]}
        pooled = ba[("codecarbon", "cloud_billing")]
        # diffs = [0.7, 0.7, 0.15, 0.12]: bias 0.4175, sd sqrt(0.319675/3).
        self.assertAlmostEqual(pooled["mean_bias"], 0.4175, places=10)
        self.assertAlmostEqual(pooled["sd_diff"], math.sqrt(0.319675 / 3.0), places=10)
        per_workload = {
            entry["workload_id"]: entry for entry in pooled["per_workload"]
        }
        self.assertAlmostEqual(per_workload["w1_finetune"]["mean_bias"], 0.7, places=10)

    def test_unavailable_row_loads_with_null_fields(self):
        rows = HYP.load_measurement_runs(RUNS_FIXTURE)
        unavailable = [row for row in rows if not row["method_available"]]
        self.assertEqual(len(unavailable), 1)
        row = unavailable[0]
        self.assertIsNone(row["energy_kwh"])
        self.assertIsNone(row["recommendation"])
        self.assertIsNone(row["carbon_intensity_basis"])

    def test_h1_runs_source_on_fixture(self):
        rows = HYP.load_measurement_runs(RUNS_FIXTURE)
        section = HYP.h1_section(rows, None, {}, engine="stdlib")
        source = section["sources"][0]
        # Three confidence tiers perfectly aligned with the ordinal: rho -1.
        self.assertEqual(source["source"], "measurement_runs")
        self.assertEqual(source["n"], 12)
        self.assertEqual(source["n_excluded_method_unavailable"], 1)
        self.assertAlmostEqual(source["rho"], -1.0, places=12)
        self.assertTrue(source["direction_consistent"])


class SchemaValidationTest(unittest.TestCase):
    def write_csv(self, content):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8"
        )
        handle.write(content)
        handle.close()
        self.addCleanup(pathlib.Path(handle.name).unlink)
        return pathlib.Path(handle.name)

    def test_missing_column_raises(self):
        path = self.write_csv("system_id,coverage_rate_pre\nS1,0.5\n")
        with self.assertRaisesRegex(HYP.SchemaError, "missing required columns"):
            HYP.load_coverage(path)

    def test_bad_enum_raises(self):
        path = self.write_csv(
            "rater_id,rater_role,profile_id,recommendation,"
            "decision_confidence_1_5,decisive_controls,time_to_decision_s\n"
            "R1,GRC,P1,maybe,3,ENV-1,10\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "recommendation"):
            HYP.load_panel(path)

    def test_confidence_out_of_range_raises(self):
        path = self.write_csv(
            "rater_id,rater_role,profile_id,recommendation,"
            "decision_confidence_1_5,decisive_controls,time_to_decision_s\n"
            "R1,GRC,P1,go,6,ENV-1,10\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "above maximum"):
            HYP.load_panel(path)

    def test_bad_control_token_raises(self):
        path = self.write_csv(
            "rater_id,rater_role,profile_id,recommendation,"
            "decision_confidence_1_5,decisive_controls,time_to_decision_s\n"
            "R1,GRC,P1,go,3,ENV-9,10\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "ENV-9"):
            HYP.load_panel(path)

    def test_duplicate_control_token_raises(self):
        path = self.write_csv(
            "rater_id,rater_role,profile_id,recommendation,"
            "decision_confidence_1_5,decisive_controls,time_to_decision_s\n"
            "R1,GRC,P1,go,3,ENV-1;ENV-1,10\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "duplicate token"):
            HYP.load_panel(path)

    def test_duplicate_panel_rating_raises(self):
        path = self.write_csv(
            "rater_id,rater_role,profile_id,recommendation,"
            "decision_confidence_1_5,decisive_controls,time_to_decision_s\n"
            "R1,GRC,P1,go,3,ENV-1,10\n"
            "R1,GRC,P1,no_go,3,ENV-2,12\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "duplicate rating"):
            HYP.load_panel(path)

    def test_coverage_rate_above_one_raises(self):
        path = self.write_csv(
            "system_id,coverage_rate_pre,coverage_rate_post\nS1,0.5,1.2\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "above maximum"):
            HYP.load_coverage(path)

    def test_mixed_mitigation_units_raise(self):
        path = self.write_csv(
            "workload_id,mitigation,intensity_pre,intensity_post,unit\n"
            "w1,region_shift,100,70,g_per_unit\n"
            "w2,caching,90,60,kg_per_unit\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "mix units"):
            HYP.load_mitigation(path)

    def test_zero_intensity_pre_raises(self):
        path = self.write_csv(
            "workload_id,mitigation,intensity_pre,intensity_post,unit\n"
            "w1,region_shift,0,0,g_per_unit\n"
        )
        with self.assertRaisesRegex(HYP.SchemaError, "greater than"):
            HYP.load_mitigation(path)

    def test_duplicate_runs_key_raises(self):
        header = (
            "workload_id,run_id,method,functional_unit,duration_seconds,energy_kwh,"
            "location_carbon_intensity_g_co2e_per_kwh,"
            "market_carbon_intensity_g_co2e_per_kwh,carbon_intensity_basis,"
            "location_kg_co2e,market_kg_co2e,provenance_class,uncertainty_pct,"
            "confidence_score,impact_level,intensity_vs_baseline,risk_tier,"
            "recommendation,mitigation_readiness,offsets_retired_kg_co2e,notes,"
            "measurement_method\n"
        )
        row = (
            "w1,r1,m,fu,10,1.0,400,250,average,0.4,0.25,measured,5,0.9,low,,low,"
            "go,documented,0.0,x,codecarbon\n"
        )
        path = self.write_csv(header + row + row)
        with self.assertRaisesRegex(HYP.SchemaError, "duplicate row"):
            HYP.load_measurement_runs(path)


class ProfilesTest(unittest.TestCase):
    def test_missing_profiles_degrade_gracefully(self):
        mapping, notes = HYP.load_profiles(ROOT / "profiles" / "does_not_exist.json")
        self.assertEqual(mapping, {})
        self.assertTrue(any("not found" in note for note in notes))

    @unittest.skipUnless(PROFILES_JSON.exists(), "profiles.json not generated yet")
    def test_real_profiles_load(self):
        mapping, _ = HYP.load_profiles(PROFILES_JSON)
        self.assertEqual(len(mapping), 12)
        self.assertEqual(mapping["P01"]["expected_recommendation"], "go")
        self.assertAlmostEqual(mapping["P01"]["confidence_score"], 0.92, places=6)

    def test_tolerant_top_level_list_layout(self):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(
            [
                {"profile_id": "X1", "expected_recommendation": "no_go"},
                {"id": "X2", "expected": {"recommendation": "go", "confidence_score": 0.5}},
            ],
            handle,
        )
        handle.close()
        self.addCleanup(pathlib.Path(handle.name).unlink)
        mapping, _ = HYP.load_profiles(pathlib.Path(handle.name))
        self.assertEqual(mapping["X1"]["expected_recommendation"], "no_go")
        self.assertEqual(mapping["X2"]["expected_recommendation"], "go")
        self.assertAlmostEqual(mapping["X2"]["confidence_score"], 0.5, places=12)


@unittest.skipUnless(HYP.SCIPY_AVAILABLE, "scipy not importable in this environment")
class ScipyAgreementTest(unittest.TestCase):
    """The preferred and fallback implementations must agree to 1e-6."""

    def deterministic_vectors(self, n=30):
        import random

        rng = random.Random(42)
        x = [round(rng.uniform(0.0, 1.0), 2) for _ in range(n)]
        y = [round(0.7 * value + rng.uniform(-0.3, 0.3), 2) for value in x]
        return x, y

    def test_spearman_agreement(self):
        x, y = self.deterministic_vectors()
        preferred = HYP.spearman_correlation(x, y, engine="auto")
        fallback = HYP.spearman_correlation(x, y, engine="stdlib")
        self.assertEqual(preferred["implementation"], "scipy")
        self.assertAlmostEqual(preferred["rho"], fallback["rho"], delta=1e-6)
        self.assertAlmostEqual(preferred["p_value"], fallback["p_value"], delta=1e-6)

    def test_wilcoxon_statistic_agreement(self):
        import random

        rng = random.Random(7)
        pre = [round(rng.uniform(10.0, 20.0), 1) for _ in range(15)]
        post = [round(value + rng.uniform(-2.0, 4.0), 1) for value in pre]
        post[0] = pre[0]  # force one zero difference
        for alternative in ("two-sided", "greater"):
            preferred = HYP.wilcoxon_signed_rank(
                post, pre, alternative=alternative, engine="auto"
            )
            fallback = HYP.wilcoxon_signed_rank(
                post, pre, alternative=alternative, engine="stdlib"
            )
            self.assertEqual(preferred["implementation"], "scipy")
            self.assertAlmostEqual(
                preferred["statistic"], fallback["statistic"], delta=1e-6
            )

    def test_ttest_agreement(self):
        x, y = self.deterministic_vectors(20)
        preferred = HYP.paired_ttest(x, y, engine="auto")
        fallback = HYP.paired_ttest(x, y, engine="stdlib")
        self.assertEqual(preferred["implementation"], "scipy")
        self.assertAlmostEqual(
            preferred["t_statistic"], fallback["t_statistic"], delta=1e-6
        )
        self.assertAlmostEqual(preferred["p_value"], fallback["p_value"], delta=1e-6)

    @unittest.skipUnless(HYP.SKLEARN_AVAILABLE, "sklearn not importable")
    def test_cohen_kappa_agreement(self):
        import random

        rng = random.Random(13)
        labels = list(HYP.RECOMMENDATION_LABELS)
        rater_a = [rng.choice(labels) for _ in range(60)]
        rater_b = [
            value if rng.random() < 0.6 else rng.choice(labels) for value in rater_a
        ]
        preferred = HYP.cohen_kappa(rater_a, rater_b, engine="auto")
        fallback = HYP.cohen_kappa(rater_a, rater_b, engine="stdlib")
        self.assertEqual(preferred["implementation"], "sklearn")
        self.assertAlmostEqual(preferred["kappa"], fallback["kappa"], delta=1e-6)


class CliEndToEndTest(unittest.TestCase):
    def make_profiles_json(self, directory):
        path = directory / "profiles.json"
        payload = {
            "profiles": [
                {"id": "P1", "expected": {"recommendation": "go", "confidence_score": 0.9}},
                {"id": "P2", "expected": {"recommendation": "go", "confidence_score": 0.75}},
                {"id": "P3", "expected": {"recommendation": "no_go", "confidence_score": 0.4}},
                {"id": "P4", "expected": {"recommendation": "no_go", "confidence_score": 0.2}},
            ]
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def run_cli(self, out_path, profiles_path, engine="auto"):
        argv = [
            "--panel", str(PANEL_FIXTURE),
            "--runs", str(RUNS_FIXTURE),
            "--coverage", str(COVERAGE_FIXTURE),
            "--mitigation", str(MITIGATION_FIXTURE),
            "--profiles", str(profiles_path),
            "--bootstrap", "60",
            "--seed", "21",
            "--engine", engine,
            "--out", str(out_path),
        ]
        return HYP.main(argv)

    def test_cli_outputs_all_sections_deterministically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            profiles_path = self.make_profiles_json(tmp)
            out_path = tmp / "results.json"
            self.assertEqual(self.run_cli(out_path, profiles_path), 0)
            first = out_path.read_text(encoding="utf-8")
            results = json.loads(first)

            for section in ("meta", "h1", "h2", "h3", "h4", "measurement_accuracy"):
                self.assertIn(section, results)
            sources = {entry["source"]: entry for entry in results["h1"]["sources"]}
            self.assertAlmostEqual(sources["measurement_runs"]["rho"], -1.0, places=9)
            panel_source = sources["panel_joined_profiles"]
            self.assertEqual(panel_source["n"], 12)
            self.assertTrue(panel_source["direction_consistent"])
            self.assertAlmostEqual(
                results["h3"]["pooled"]["fleiss_kappa"], 1.0 / 3.0, places=9
            )
            self.assertEqual(results["h2"]["statistic"], 0.0)
            self.assertTrue(results["h4"]["target_met_point"])
            self.assertIn(
                results["h4"]["implementation"],
                ("scipy", "stdlib"),
            )

            self.assertEqual(self.run_cli(out_path, profiles_path), 0)
            self.assertEqual(first, out_path.read_text(encoding="utf-8"))

    def test_engine_stdlib_matches_auto_statistics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            profiles_path = self.make_profiles_json(tmp)
            auto_path = tmp / "auto.json"
            stdlib_path = tmp / "stdlib.json"
            self.assertEqual(self.run_cli(auto_path, profiles_path, engine="auto"), 0)
            self.assertEqual(
                self.run_cli(stdlib_path, profiles_path, engine="stdlib"), 0
            )
            auto = json.loads(auto_path.read_text(encoding="utf-8"))
            fallback = json.loads(stdlib_path.read_text(encoding="utf-8"))

            auto_sources = {e["source"]: e for e in auto["h1"]["sources"]}
            fallback_sources = {e["source"]: e for e in fallback["h1"]["sources"]}
            for source in auto_sources:
                self.assertAlmostEqual(
                    auto_sources[source]["rho"],
                    fallback_sources[source]["rho"],
                    delta=1e-6,
                )
            self.assertAlmostEqual(
                auto["h2"]["statistic"], fallback["h2"]["statistic"], delta=1e-6
            )
            self.assertAlmostEqual(
                auto["h4"]["t_statistic"], fallback["h4"]["t_statistic"], delta=1e-6
            )
            self.assertAlmostEqual(
                auto["h4"]["p_value"], fallback["h4"]["p_value"], delta=1e-6
            )
            self.assertAlmostEqual(
                auto["h3"]["pooled"]["mean_pairwise_cohen_kappa"],
                fallback["h3"]["pooled"]["mean_pairwise_cohen_kappa"],
                delta=1e-6,
            )
            # Bootstrap CIs are stdlib in both engines: identical, not close.
            self.assertEqual(
                auto["h3"]["pooled"]["fleiss_ci95"],
                fallback["h3"]["pooled"]["fleiss_ci95"],
            )

    def test_missing_input_returns_schema_error_code(self):
        exit_code = HYP.main(
            ["--panel", str(FIXTURES / "no_such_file.csv")]
        )
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()

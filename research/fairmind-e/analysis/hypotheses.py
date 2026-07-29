#!/usr/bin/env python3
"""Pre-registered hypothesis statistics for the FairMind-E paper (H1-H4).

This module computes, from CSV inputs, the four pre-registered hypotheses plus
the measurement-accuracy statistics that feed threshold recalibration:

- H1: lower evidence confidence leads to more conservative recommendations.
  Spearman rank correlation between ``confidence_score`` and the
  recommendation ordinal. The ordinal is defined explicitly in
  ``RECOMMENDATION_ORDINAL`` (go=0, conditional_go=1, no_go=2), so the
  pre-registered expectation is a NEGATIVE correlation.
- H2: the module raises ENV control coverage versus baseline. Wilcoxon
  signed-rank on paired ``coverage_rate_pre`` vs ``coverage_rate_post``.
- H3: the decision matrix improves inter-rater agreement. Mean pairwise
  Cohen's kappa and Fleiss' kappa with deterministic bootstrap 95 percent
  confidence intervals; target kappa > 0.60.
- H4: mitigations reduce carbon intensity by more than 20 percent. Paired
  t-test on pre/post intensity plus mean percent reduction with CI.
- Measurement accuracy: MAPE for all ordered method pairs and Bland-Altman
  statistics (mean bias, 95 percent limits of agreement) pooled and per
  workload, feeding uncertainty threshold recalibration.

Implementation policy: scipy.stats and sklearn.metrics are used when
importable (the ``apps/backend`` environment provides them); everything also
has a pure-stdlib fallback so the module runs dependency-free, matching the
research/fairmind-e convention. Every result records which implementation
produced it. Stdlib p-values use the exact Student-t distribution via the
regularized incomplete beta function, except the Wilcoxon fallback, which
uses a normal approximation and says so in its ``p_method``. Bootstrap
resampling is always pure-stdlib with a fixed seed, so confidence intervals
are identical across environments. Outputs contain no timestamps; identical
inputs yield identical outputs.

Run from the repository root:

    python3 research/fairmind-e/analysis/hypotheses.py \
        --panel panel.csv --runs runs.csv --coverage coverage.csv \
        --mitigation mitigations.csv --out results.json
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import pathlib
import random
import statistics
import sys
from typing import Any, Callable, Mapping, Sequence

try:  # Preferred implementations when available (apps/backend venv).
    from scipy import stats as _SCIPY_STATS  # type: ignore
except ImportError:  # pragma: no cover - exercised in stdlib-only environments
    _SCIPY_STATS = None

try:
    from sklearn.metrics import cohen_kappa_score as _SKLEARN_COHEN_KAPPA  # type: ignore
except ImportError:  # pragma: no cover - exercised in stdlib-only environments
    _SKLEARN_COHEN_KAPPA = None

SCIPY_AVAILABLE = _SCIPY_STATS is not None
SKLEARN_AVAILABLE = _SKLEARN_COHEN_KAPPA is not None

MODULE_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROFILES_PATH = MODULE_ROOT / "profiles" / "profiles.json"

# --------------------------------------------------------------------------
# Pre-registered constants
# --------------------------------------------------------------------------

# H1 ordinal. Higher ordinal = more conservative recommendation. Because
# higher confidence is hypothesized to license less conservative outcomes,
# the expected Spearman correlation between confidence_score and this
# ordinal is NEGATIVE.
RECOMMENDATION_ORDINAL = {"go": 0, "conditional_go": 1, "no_go": 2}
RECOMMENDATION_LABELS = ("go", "conditional_go", "no_go")

RATER_ROLES = ("GRC", "ML_ENG", "ESG")
ENV_CONTROLS = ("ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6")
MEASUREMENT_METHODS = ("codecarbon", "cloud_billing", "manual_flop")
PROVENANCE_CLASSES = (
    "measured",
    "tool_estimated",
    "vendor_reported",
    "manual",
    "unknown",
)
CARBON_INTENSITY_BASES = ("average", "marginal")
ACCURACY_METRICS = ("energy_kwh", "location_kg_co2e", "market_kg_co2e")

KAPPA_TARGET = 0.60          # H3 pre-registered agreement target (strict >).
H4_TARGET_PCT_REDUCTION = 20.0  # H4 pre-registered reduction target (strict >).
LOA_MULTIPLIER = 1.96        # Bland-Altman 95 percent limits of agreement.
MIN_PAIR_OVERLAP = 2         # Minimum common profiles for a Cohen pair.
DEFAULT_SEED = 20260730
DEFAULT_BOOTSTRAP_SAMPLES = 2000

# --------------------------------------------------------------------------
# Input contracts. Each schema maps column -> cell spec. Kinds:
#   id             non-empty string
#   str            string, may be empty
#   enum           one of "values"
#   enum_or_empty  one of "values", or empty -> None
#   int            integer within optional min/max
#   float          finite float within optional min/max
#   nullable_float finite float within optional min/max, or empty -> None
#   controls       semicolon-joined subset of ENV_CONTROLS, may be empty
# Unknown extra columns are ignored. Lines starting with "#" are treated as
# comments and skipped (used by the SYNTHETIC fixtures).
# --------------------------------------------------------------------------

# 1. Panel responses: one row per (rater, profile) release-recommendation
#    rating collected with the reviewer instrument.
PANEL_SCHEMA: dict[str, dict[str, Any]] = {
    "rater_id": {"kind": "id"},
    "rater_role": {"kind": "enum", "values": RATER_ROLES},
    "profile_id": {"kind": "id"},
    "recommendation": {"kind": "enum", "values": RECOMMENDATION_LABELS},
    "decision_confidence_1_5": {"kind": "int", "min": 1, "max": 5},
    "decisive_controls": {"kind": "controls"},
    "time_to_decision_s": {"kind": "float", "min": 0.0},
}

# 2. Measurement runs: the smoke-harness CSV contract documented in
#    research/fairmind-e/README.md and emitted by
#    research/fairmind-e/measurement/harness.py, plus measurement_method.
#    The harness leaves measurement and gate fields empty when a method
#    could not produce a real figure (method_available=false), so numeric
#    and gate columns are nullable here; nothing is imputed.
MEASUREMENT_RUNS_SCHEMA: dict[str, dict[str, Any]] = {
    "workload_id": {"kind": "id"},
    "run_id": {"kind": "id"},
    "method": {"kind": "str"},
    "functional_unit": {"kind": "id"},
    "duration_seconds": {"kind": "nullable_float", "min": 0.0},
    "energy_kwh": {"kind": "nullable_float", "min": 0.0},
    "location_carbon_intensity_g_co2e_per_kwh": {"kind": "nullable_float", "min": 0.0},
    "market_carbon_intensity_g_co2e_per_kwh": {"kind": "nullable_float", "min": 0.0},
    "carbon_intensity_basis": {"kind": "enum_or_empty", "values": CARBON_INTENSITY_BASES},
    "location_kg_co2e": {"kind": "nullable_float", "min": 0.0},
    "market_kg_co2e": {"kind": "nullable_float", "min": 0.0},
    "provenance_class": {"kind": "enum", "values": PROVENANCE_CLASSES},
    "uncertainty_pct": {"kind": "float", "min": 0.0},
    "confidence_score": {"kind": "float", "min": 0.0, "max": 1.0},
    "impact_level": {"kind": "str"},
    "intensity_vs_baseline": {"kind": "nullable_float", "min": 0.0},
    "risk_tier": {"kind": "str"},
    "recommendation": {"kind": "enum_or_empty", "values": RECOMMENDATION_LABELS},
    "mitigation_readiness": {"kind": "str"},
    "offsets_retired_kg_co2e": {"kind": "float", "min": 0.0},
    "notes": {"kind": "str"},
    "measurement_method": {"kind": "enum", "values": MEASUREMENT_METHODS},
}

# Optional harness columns, validated when present. run_mode labels the
# execution mode (for example dry_run); method_available=false marks rows
# whose method produced no real figure. Absent columns default to
# method_available=true.
MEASUREMENT_RUNS_OPTIONAL_SCHEMA: dict[str, dict[str, Any]] = {
    "run_mode": {"kind": "id"},
    "method_available": {"kind": "enum", "values": ("true", "false")},
}

# 3. Coverage pre/post: one row per system with ENV control coverage rates
#    under the baseline (pre) and module (post) conditions. See
#    analysis/DESIGN_NOTES.md: a ratings-only panel does NOT produce this.
COVERAGE_SCHEMA: dict[str, dict[str, Any]] = {
    "system_id": {"kind": "id"},
    "coverage_rate_pre": {"kind": "float", "min": 0.0, "max": 1.0},
    "coverage_rate_post": {"kind": "float", "min": 0.0, "max": 1.0},
}

# 4. Mitigation pairs: one row per (workload, mitigation) with carbon
#    intensity before and after the mitigation, in a single shared unit.
MITIGATION_SCHEMA: dict[str, dict[str, Any]] = {
    "workload_id": {"kind": "id"},
    "mitigation": {"kind": "id"},
    "intensity_pre": {"kind": "float", "min_exclusive": 0.0},
    "intensity_post": {"kind": "float", "min": 0.0},
    "unit": {"kind": "id"},
}


class SchemaError(ValueError):
    """Raised when an input file violates its documented contract."""


# --------------------------------------------------------------------------
# Small numeric helpers
# --------------------------------------------------------------------------


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _sample_sd(values: Sequence[float]) -> float | None:
    """Sample standard deviation (ddof=1); None when fewer than 2 values."""

    n = len(values)
    if n < 2:
        return None
    mean = _mean(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def _normal_sf(z: float) -> float:
    """Standard normal survival function via erfc."""

    return 0.5 * math.erfc(z / math.sqrt(2.0))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta function."""

    max_iterations = 300
    eps = 1e-15
    fpmin = 1e-300

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """I_x(a, b) via the standard continued-fraction expansion."""

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _student_t_two_sided_p(t_statistic: float, df: float) -> float:
    """Exact two-sided Student-t p-value via the incomplete beta function."""

    if df <= 0:
        raise ValueError("degrees of freedom must be positive")
    x = df / (df + t_statistic * t_statistic)
    return _regularized_incomplete_beta(df / 2.0, 0.5, x)


def _percentile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile of an ascending-sorted sequence."""

    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    position = q * (n - 1)
    low = int(math.floor(position))
    high = min(low + 1, n - 1)
    fraction = position - low
    return sorted_values[low] * (1.0 - fraction) + sorted_values[high] * fraction


# --------------------------------------------------------------------------
# Rank statistics (H1)
# --------------------------------------------------------------------------


def rank_midrank(values: Sequence[float]) -> list[float]:
    """1-based ranks with midranks for ties (matches scipy rankdata average)."""

    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        midrank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = midrank
        i = j + 1
    return ranks


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    mean_x = _mean(x)
    mean_y = _mean(y)
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    var_x = sum((a - mean_x) ** 2 for a in x)
    var_y = sum((b - mean_y) ** 2 for b in y)
    if var_x <= 0.0 or var_y <= 0.0:
        return float("nan")
    return cov / math.sqrt(var_x * var_y)


def spearman_correlation(
    x: Sequence[float], y: Sequence[float], engine: str = "auto"
) -> dict[str, Any]:
    """Spearman rho with tie handling plus a two-sided Student-t p-value.

    The stdlib path ranks with midranks and computes Pearson on ranks; its
    p-value uses the same t approximation as scipy, evaluated exactly via
    the regularized incomplete beta function.
    """

    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    n = len(x)
    if n < 3:
        return {
            "rho": None,
            "p_value": None,
            "n": n,
            "implementation": "stdlib",
            "p_method": None,
            "note": "fewer than 3 observations; Spearman correlation not reported",
        }
    if len(set(x)) < 2 or len(set(y)) < 2:
        return {
            "rho": None,
            "p_value": None,
            "n": n,
            "implementation": "stdlib",
            "p_method": None,
            "note": "constant input; Spearman correlation undefined",
        }

    if engine == "auto" and SCIPY_AVAILABLE:
        result = _SCIPY_STATS.spearmanr(list(x), list(y))
        return {
            "rho": float(result.statistic),
            "p_value": float(result.pvalue),
            "n": n,
            "implementation": "scipy",
            "p_method": "two-sided Student-t approximation (scipy)",
        }

    rho = pearson_correlation(rank_midrank(x), rank_midrank(y))
    if math.isnan(rho):
        return {
            "rho": None,
            "p_value": None,
            "n": n,
            "implementation": "stdlib",
            "p_method": None,
            "note": "rank variance is zero; Spearman correlation undefined",
        }
    if abs(rho) >= 1.0:
        p_value = 0.0
    else:
        t_statistic = rho * math.sqrt((n - 2) / (1.0 - rho * rho))
        p_value = _student_t_two_sided_p(t_statistic, n - 2)
    return {
        "rho": rho,
        "p_value": p_value,
        "n": n,
        "implementation": "stdlib",
        "p_method": (
            "two-sided Student-t approximation via regularized incomplete beta (stdlib)"
        ),
    }


# --------------------------------------------------------------------------
# Agreement statistics (H3)
# --------------------------------------------------------------------------


def cohen_kappa(
    labels_a: Sequence[str],
    labels_b: Sequence[str],
    labels: Sequence[str] = RECOMMENDATION_LABELS,
    engine: str = "auto",
) -> dict[str, Any]:
    """Cohen's kappa for two raters over the same items.

    Degenerate convention (documented, applied on every engine so the paths
    agree): when expected agreement equals 1 the ratio is 0/0; we report 1.0
    for perfect observed agreement and 0.0 otherwise, with degenerate=true.
    """

    if len(labels_a) != len(labels_b):
        raise ValueError("labels_a and labels_b must have equal length")
    n = len(labels_a)
    if n == 0:
        raise ValueError("cannot compute kappa on zero items")
    for value in itertools.chain(labels_a, labels_b):
        if value not in labels:
            raise ValueError(f"label {value!r} not in label set {tuple(labels)!r}")

    observed = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    marginal_a = {label: labels_a.count(label) / n for label in labels}
    marginal_b = {label: labels_b.count(label) / n for label in labels}
    expected = sum(marginal_a[label] * marginal_b[label] for label in labels)

    if 1.0 - expected < 1e-12:
        kappa = 1.0 if 1.0 - observed < 1e-12 else 0.0
        return {
            "kappa": kappa,
            "observed_agreement": observed,
            "expected_agreement": expected,
            "n": n,
            "implementation": "stdlib",
            "degenerate": True,
        }

    if engine == "auto" and SKLEARN_AVAILABLE:
        kappa = float(
            _SKLEARN_COHEN_KAPPA(list(labels_a), list(labels_b), labels=list(labels))
        )
        implementation = "sklearn"
    else:
        kappa = (observed - expected) / (1.0 - expected)
        implementation = "stdlib"
    return {
        "kappa": kappa,
        "observed_agreement": observed,
        "expected_agreement": expected,
        "n": n,
        "implementation": implementation,
        "degenerate": False,
    }


def fleiss_kappa_from_counts(
    counts_per_item: Sequence[Sequence[int]],
) -> dict[str, Any]:
    """Fleiss' kappa from per-item category counts.

    Accepts a varying number of ratings per item (n_i >= 2) using the
    standard generalization P_i = sum_j n_ij (n_ij - 1) / (n_i (n_i - 1)).
    There is no scipy/sklearn implementation, so this is always stdlib.
    """

    if not counts_per_item:
        raise ValueError("cannot compute Fleiss' kappa on zero items")
    item_totals = [sum(row) for row in counts_per_item]
    if any(total < 2 for total in item_totals):
        raise ValueError("every item needs at least 2 ratings for Fleiss' kappa")

    total_ratings = sum(item_totals)
    n_categories = len(counts_per_item[0])
    category_totals = [
        sum(row[j] for row in counts_per_item) for j in range(n_categories)
    ]
    p_j = [total / total_ratings for total in category_totals]
    p_e = sum(p * p for p in p_j)

    p_i = [
        sum(c * (c - 1) for c in row) / (total * (total - 1))
        for row, total in zip(counts_per_item, item_totals)
    ]
    p_bar = _mean(p_i)

    if 1.0 - p_e < 1e-12:
        kappa = 1.0 if 1.0 - p_bar < 1e-12 else 0.0
        degenerate = True
    else:
        kappa = (p_bar - p_e) / (1.0 - p_e)
        degenerate = False
    return {
        "kappa": kappa,
        "mean_observed_agreement": p_bar,
        "expected_agreement": p_e,
        "n_items": len(counts_per_item),
        "total_ratings": total_ratings,
        "per_item_agreement": p_i,
        "implementation": "stdlib",
        "degenerate": degenerate,
    }


# --------------------------------------------------------------------------
# Paired-sample tests (H2, H4)
# --------------------------------------------------------------------------


def wilcoxon_signed_rank(
    x: Sequence[float],
    y: Sequence[float],
    alternative: str = "two-sided",
    engine: str = "auto",
) -> dict[str, Any]:
    """Wilcoxon signed-rank test on paired samples (differences x - y).

    Zero differences are dropped (Wilcoxon's original procedure, matching
    the scipy default zero_method="wilcox"). The statistic follows the scipy
    convention: min(R+, R-) two-sided, otherwise R+. The stdlib fallback
    p-value uses a tie-corrected normal approximation without continuity
    correction and records that caveat in ``p_method``.
    """

    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(f"unknown alternative: {alternative}")
    if len(x) != len(y):
        raise ValueError("x and y must have equal length")

    differences = [a - b for a, b in zip(x, y)]
    nonzero = [d for d in differences if d != 0.0]
    n_pairs = len(differences)
    n_nonzero = len(nonzero)
    base = {
        "n_pairs": n_pairs,
        "n_nonzero": n_nonzero,
        "n_zero_dropped": n_pairs - n_nonzero,
        "alternative": alternative,
    }
    if n_nonzero == 0:
        base.update(
            {
                "statistic": None,
                "p_value": None,
                "implementation": "stdlib",
                "p_method": None,
                "note": "all paired differences are zero; test undefined",
            }
        )
        return base

    if engine == "auto" and SCIPY_AVAILABLE:
        result = _SCIPY_STATS.wilcoxon(list(x), list(y), alternative=alternative)
        base.update(
            {
                "statistic": float(result.statistic),
                "p_value": float(result.pvalue),
                "implementation": "scipy",
                "p_method": (
                    "scipy method=auto (exact for small tie-free samples, "
                    "else normal approximation)"
                ),
            }
        )
        return base

    absolute = [abs(d) for d in nonzero]
    ranks = rank_midrank(absolute)
    r_plus = sum(rank for rank, d in zip(ranks, nonzero) if d > 0)
    r_minus = sum(rank for rank, d in zip(ranks, nonzero) if d < 0)
    statistic = min(r_plus, r_minus) if alternative == "two-sided" else r_plus

    n = n_nonzero
    mean_r = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    tie_sizes: dict[float, int] = {}
    for value in absolute:
        tie_sizes[value] = tie_sizes.get(value, 0) + 1
    variance -= sum(t**3 - t for t in tie_sizes.values()) / 48.0
    if variance <= 0.0:
        base.update(
            {
                "statistic": statistic,
                "p_value": None,
                "implementation": "stdlib",
                "p_method": None,
                "note": "zero variance under the null; p-value undefined",
            }
        )
        return base

    z = (r_plus - mean_r) / math.sqrt(variance)
    if alternative == "two-sided":
        p_value = min(1.0, 2.0 * _normal_sf(abs(z)))
    elif alternative == "greater":
        p_value = _normal_sf(z)
    else:
        p_value = 1.0 - _normal_sf(z)
    base.update(
        {
            "statistic": statistic,
            "p_value": p_value,
            "implementation": "stdlib",
            "p_method": (
                "normal approximation with tie correction, no continuity "
                "correction (stdlib fallback); approximate for small samples"
            ),
        }
    )
    return base


def paired_ttest(
    x: Sequence[float], y: Sequence[float], engine: str = "auto"
) -> dict[str, Any]:
    """Two-sided paired t-test on differences x - y.

    The stdlib fallback p-value uses the exact Student-t distribution via
    the regularized incomplete beta function (not a normal approximation).
    """

    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    n = len(x)
    if n < 2:
        return {
            "t_statistic": None,
            "p_value": None,
            "df": None,
            "n": n,
            "mean_diff": None,
            "implementation": "stdlib",
            "p_method": None,
            "note": "fewer than 2 pairs; t-test undefined",
        }

    differences = [a - b for a, b in zip(x, y)]
    mean_diff = _mean(differences)
    sd_diff = _sample_sd(differences)
    if sd_diff == 0.0:
        return {
            "t_statistic": None,
            "p_value": None,
            "df": n - 1,
            "n": n,
            "mean_diff": mean_diff,
            "implementation": "stdlib",
            "p_method": None,
            "note": "zero variance of paired differences; t-test undefined",
        }

    if engine == "auto" and SCIPY_AVAILABLE:
        result = _SCIPY_STATS.ttest_rel(list(x), list(y))
        return {
            "t_statistic": float(result.statistic),
            "p_value": float(result.pvalue),
            "df": n - 1,
            "n": n,
            "mean_diff": mean_diff,
            "implementation": "scipy",
            "p_method": "two-sided Student-t (scipy)",
        }

    t_statistic = mean_diff / (sd_diff / math.sqrt(n))
    p_value = _student_t_two_sided_p(t_statistic, n - 1)
    return {
        "t_statistic": t_statistic,
        "p_value": p_value,
        "df": n - 1,
        "n": n,
        "mean_diff": mean_diff,
        "implementation": "stdlib",
        "p_method": (
            "two-sided Student-t via regularized incomplete beta (stdlib)"
        ),
    }


# --------------------------------------------------------------------------
# Measurement-accuracy primitives
# --------------------------------------------------------------------------


def mape_pct(reference: Sequence[float], alternative: Sequence[float]) -> float:
    """Mean absolute percentage error of alternative against reference.

    MAPE is asymmetric in its arguments; callers report both directions.
    """

    if len(reference) != len(alternative):
        raise ValueError("reference and alternative must have equal length")
    if not reference:
        raise ValueError("cannot compute MAPE on zero pairs")
    if any(r == 0.0 for r in reference):
        raise ValueError("MAPE undefined for zero reference values")
    return 100.0 * _mean(
        [abs(a - r) / abs(r) for r, a in zip(reference, alternative)]
    )


def bland_altman(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Bland-Altman statistics for paired measurements (differences b - a)."""

    if len(a) != len(b):
        raise ValueError("a and b must have equal length")
    if not a:
        raise ValueError("cannot compute Bland-Altman statistics on zero pairs")
    differences = [y - x for x, y in zip(a, b)]
    mean_bias = _mean(differences)
    sd_diff = _sample_sd(differences)
    if sd_diff is None:
        loa_low = loa_high = None
    else:
        loa_low = mean_bias - LOA_MULTIPLIER * sd_diff
        loa_high = mean_bias + LOA_MULTIPLIER * sd_diff
    return {
        "n": len(differences),
        "mean_bias": mean_bias,
        "sd_diff": sd_diff,
        "loa95_low": loa_low,
        "loa95_high": loa_high,
    }


def percent_reduction(pre: float, post: float) -> float:
    if pre <= 0.0:
        raise ValueError("percent reduction undefined for non-positive pre value")
    return 100.0 * (pre - post) / pre


def _bootstrap_percentile_ci(
    n_items: int,
    statistic_fn: Callable[[Sequence[int]], float | None],
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    """Deterministic percentile bootstrap CI over item indices (stdlib rng)."""

    rng = random.Random(seed)
    values: list[float] = []
    n_skipped = 0
    for _ in range(n_boot):
        indices = [rng.randrange(n_items) for _ in range(n_items)]
        value = statistic_fn(indices)
        if value is None or not math.isfinite(value):
            n_skipped += 1
        else:
            values.append(value)
    if not values:
        return {"low": None, "high": None, "n_boot": n_boot, "n_skipped": n_skipped}
    values.sort()
    return {
        "low": _percentile(values, 0.025),
        "high": _percentile(values, 0.975),
        "n_boot": n_boot,
        "n_skipped": n_skipped,
    }


# --------------------------------------------------------------------------
# CSV loading and validation
# --------------------------------------------------------------------------


def _parse_cell(
    column: str, spec: Mapping[str, Any], raw: str, context: str
) -> Any:
    kind = spec["kind"]
    value = raw.strip()

    if kind == "id":
        if not value:
            raise SchemaError(f"{context}: column {column!r} must be non-empty")
        return value
    if kind == "str":
        return value
    if kind == "enum":
        if value not in spec["values"]:
            raise SchemaError(
                f"{context}: column {column!r} value {value!r} not in "
                f"{tuple(spec['values'])!r}"
            )
        return value
    if kind == "enum_or_empty":
        if not value:
            return None
        if value not in spec["values"]:
            raise SchemaError(
                f"{context}: column {column!r} value {value!r} not in "
                f"{tuple(spec['values'])!r} (or empty)"
            )
        return value
    if kind == "int":
        try:
            parsed_int = int(value)
        except ValueError as exc:
            raise SchemaError(
                f"{context}: column {column!r} value {value!r} is not an integer"
            ) from exc
        if "min" in spec and parsed_int < spec["min"]:
            raise SchemaError(
                f"{context}: column {column!r} value {parsed_int} below minimum "
                f"{spec['min']}"
            )
        if "max" in spec and parsed_int > spec["max"]:
            raise SchemaError(
                f"{context}: column {column!r} value {parsed_int} above maximum "
                f"{spec['max']}"
            )
        return parsed_int
    if kind in ("float", "nullable_float"):
        if not value:
            if kind == "nullable_float":
                return None
            raise SchemaError(f"{context}: column {column!r} must be non-empty")
        try:
            parsed = float(value)
        except ValueError as exc:
            raise SchemaError(
                f"{context}: column {column!r} value {value!r} is not a number"
            ) from exc
        if not math.isfinite(parsed):
            raise SchemaError(
                f"{context}: column {column!r} value {value!r} is not finite"
            )
        if "min" in spec and parsed < spec["min"]:
            raise SchemaError(
                f"{context}: column {column!r} value {parsed} below minimum "
                f"{spec['min']}"
            )
        if "min_exclusive" in spec and parsed <= spec["min_exclusive"]:
            raise SchemaError(
                f"{context}: column {column!r} value {parsed} must be greater "
                f"than {spec['min_exclusive']}"
            )
        if "max" in spec and parsed > spec["max"]:
            raise SchemaError(
                f"{context}: column {column!r} value {parsed} above maximum "
                f"{spec['max']}"
            )
        return parsed
    if kind == "controls":
        if not value:
            return []
        tokens = [token.strip() for token in value.split(";")]
        seen: set[str] = set()
        for token in tokens:
            if token not in ENV_CONTROLS:
                raise SchemaError(
                    f"{context}: column {column!r} token {token!r} not in "
                    f"{ENV_CONTROLS!r}"
                )
            if token in seen:
                raise SchemaError(
                    f"{context}: column {column!r} has duplicate token {token!r}"
                )
            seen.add(token)
        return tokens
    raise AssertionError(f"unknown schema kind: {kind}")


def load_csv_rows(
    path: pathlib.Path,
    schema: Mapping[str, Mapping[str, Any]],
    label: str,
    optional_schema: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Load and validate a CSV against a schema.

    Lines whose first non-blank character is ``#`` are comments (used to
    label SYNTHETIC fixtures) and are skipped. Extra columns are ignored;
    ``optional_schema`` columns are validated only when present.
    """

    path = pathlib.Path(path)
    if not path.exists():
        raise SchemaError(f"{label} CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        content_lines = [
            line for line in handle if line.strip() and not line.lstrip().startswith("#")
        ]
    reader = csv.DictReader(content_lines)
    if reader.fieldnames is None:
        raise SchemaError(f"{label} CSV is empty: {path}")
    missing = [column for column in schema if column not in reader.fieldnames]
    if missing:
        raise SchemaError(
            f"{label} CSV {path} is missing required columns: {', '.join(missing)}"
        )
    present_optional = {
        column: spec
        for column, spec in (optional_schema or {}).items()
        if column in reader.fieldnames
    }

    rows: list[dict[str, Any]] = []
    for index, raw_row in enumerate(reader, start=1):
        context = f"{label} CSV {path} data row {index}"
        typed: dict[str, Any] = {}
        for column, spec in schema.items():
            raw = raw_row.get(column)
            if raw is None:
                raise SchemaError(f"{context}: missing value for column {column!r}")
            typed[column] = _parse_cell(column, spec, raw, context)
        for column, spec in present_optional.items():
            raw = raw_row.get(column)
            if raw is None:
                raise SchemaError(f"{context}: missing value for column {column!r}")
            typed[column] = _parse_cell(column, spec, raw, context)
        rows.append(typed)
    if not rows:
        raise SchemaError(f"{label} CSV has no data rows: {path}")
    return rows


def load_panel(path: pathlib.Path) -> list[dict[str, Any]]:
    rows = load_csv_rows(path, PANEL_SCHEMA, "panel responses")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["rater_id"], row["profile_id"])
        if key in seen:
            raise SchemaError(
                f"panel responses CSV {path}: duplicate rating for rater "
                f"{key[0]!r} on profile {key[1]!r}"
            )
        seen.add(key)
    return rows


def load_measurement_runs(path: pathlib.Path) -> list[dict[str, Any]]:
    rows = load_csv_rows(
        path,
        MEASUREMENT_RUNS_SCHEMA,
        "measurement runs",
        optional_schema=MEASUREMENT_RUNS_OPTIONAL_SCHEMA,
    )
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if "method_available" in row:
            row["method_available"] = row["method_available"] == "true"
        else:
            row["method_available"] = True
        key = (row["workload_id"], row["run_id"], row["measurement_method"])
        if key in seen:
            raise SchemaError(
                f"measurement runs CSV {path}: duplicate row for "
                f"(workload_id, run_id, measurement_method) = {key!r}"
            )
        seen.add(key)
    return rows


def load_coverage(path: pathlib.Path) -> list[dict[str, Any]]:
    rows = load_csv_rows(path, COVERAGE_SCHEMA, "coverage pre/post")
    seen: set[str] = set()
    for row in rows:
        if row["system_id"] in seen:
            raise SchemaError(
                f"coverage CSV {path}: duplicate system_id {row['system_id']!r}"
            )
        seen.add(row["system_id"])
    return rows


def load_mitigation(path: pathlib.Path) -> list[dict[str, Any]]:
    rows = load_csv_rows(path, MITIGATION_SCHEMA, "mitigation pairs")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["workload_id"], row["mitigation"])
        if key in seen:
            raise SchemaError(
                f"mitigation CSV {path}: duplicate (workload_id, mitigation) {key!r}"
            )
        seen.add(key)
    units = sorted({row["unit"] for row in rows})
    if len(units) > 1:
        raise SchemaError(
            f"mitigation CSV {path}: intensities mix units {units}; the paired "
            "t-test requires a single shared unit"
        )
    return rows


def load_profiles(path: pathlib.Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load optional profile metadata (expected labels, shown confidence).

    Degrades gracefully when the file is absent: returns an empty mapping
    plus an explanatory note. Tolerates the generator layouts seen in
    research/fairmind-e/profiles/profiles.json (top-level list, or an object
    with a ``profiles`` list/dict; expected labels either nested under an
    ``expected`` object or at the top level of each entry).
    """

    path = pathlib.Path(path)
    if not path.exists():
        return {}, [
            f"profiles metadata not found at {path}; expected-label and "
            "confidence-join fields are omitted"
        ]
    try:
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"profiles metadata is not valid JSON: {path}: {exc}") from exc

    if isinstance(raw, dict):
        inner = raw.get("profiles", raw)
        if isinstance(inner, dict):
            entries = [
                {"profile_id": key, **value}
                for key, value in inner.items()
                if isinstance(value, dict)
            ]
        elif isinstance(inner, list):
            entries = inner
        else:
            raise SchemaError(f"profiles metadata has unsupported layout: {path}")
    elif isinstance(raw, list):
        entries = raw
    else:
        raise SchemaError(f"profiles metadata has unsupported layout: {path}")

    def first_key(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
        for key in keys:
            if key in mapping and mapping[key] is not None:
                return mapping[key]
        return None

    mapping: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise SchemaError(f"profiles metadata entry is not an object: {path}")
        profile_id = first_key(entry, ("profile_id", "id", "name"))
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise SchemaError(f"profiles metadata entry missing id: {path}")
        profile_id = profile_id.strip()
        if profile_id in mapping:
            raise SchemaError(
                f"profiles metadata has duplicate profile id {profile_id!r}: {path}"
            )
        expected_block = entry.get("expected")
        if not isinstance(expected_block, dict):
            expected_block = {}
        expected = first_key(
            expected_block, ("recommendation", "expected_recommendation")
        )
        if expected is None:
            expected = first_key(
                entry,
                ("expected_recommendation", "expected_label", "recommendation"),
            )
        if expected is not None and expected not in RECOMMENDATION_LABELS:
            raise SchemaError(
                f"profiles metadata: profile {profile_id!r} expected "
                f"recommendation {expected!r} not in {RECOMMENDATION_LABELS!r}"
            )
        confidence = first_key(expected_block, ("confidence_score", "confidence"))
        if confidence is None:
            confidence = first_key(
                entry, ("confidence_score", "confidence", "evidence_confidence")
            )
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError) as exc:
                raise SchemaError(
                    f"profiles metadata: profile {profile_id!r} confidence is "
                    "not numeric"
                ) from exc
            if not 0.0 <= confidence <= 1.0:
                raise SchemaError(
                    f"profiles metadata: profile {profile_id!r} confidence "
                    f"{confidence} outside [0, 1]"
                )
        mapping[profile_id] = {
            "expected_recommendation": expected,
            "confidence_score": confidence,
        }
    return mapping, [f"loaded {len(mapping)} profile entries from {path}"]


# --------------------------------------------------------------------------
# H1: confidence vs recommendation conservatism
# --------------------------------------------------------------------------


def h1_from_pairs(
    pairs: Sequence[tuple[float, str]], source: str, engine: str = "auto"
) -> dict[str, Any]:
    confidences = [confidence for confidence, _ in pairs]
    ordinals = [float(RECOMMENDATION_ORDINAL[label]) for _, label in pairs]
    result = spearman_correlation(confidences, ordinals, engine=engine)
    entry: dict[str, Any] = {"source": source}
    entry.update(result)
    entry["direction_consistent"] = (
        result["rho"] < 0.0 if result.get("rho") is not None else None
    )
    return entry


def h1_section(
    runs_rows: Sequence[Mapping[str, Any]] | None,
    panel_rows: Sequence[Mapping[str, Any]] | None,
    profiles_map: Mapping[str, Mapping[str, Any]],
    engine: str = "auto",
) -> dict[str, Any] | None:
    sources: list[dict[str, Any]] = []

    if runs_rows:
        usable: list[tuple[float, str]] = []
        n_unavailable = 0
        n_missing_recommendation = 0
        for row in runs_rows:
            if not row.get("method_available", True):
                n_unavailable += 1
                continue
            if row["recommendation"] is None:
                n_missing_recommendation += 1
                continue
            usable.append((row["confidence_score"], row["recommendation"]))
        if usable:
            entry = h1_from_pairs(usable, "measurement_runs", engine=engine)
            entry["n_excluded_method_unavailable"] = n_unavailable
            entry["n_excluded_missing_recommendation"] = n_missing_recommendation
            entry["interpretation"] = (
                "engine-level consistency of confidence and gate output; not "
                "evidence about rater behavior (see analysis/DESIGN_NOTES.md)"
            )
            sources.append(entry)
        else:
            sources.append(
                {
                    "source": "measurement_runs",
                    "rho": None,
                    "p_value": None,
                    "n": 0,
                    "note": "no runs rows with both confidence and recommendation",
                }
            )

    if panel_rows:
        joined: list[tuple[float, str]] = []
        n_missing_confidence = 0
        for row in panel_rows:
            profile = profiles_map.get(row["profile_id"], {})
            confidence = profile.get("confidence_score")
            if confidence is None:
                n_missing_confidence += 1
                continue
            joined.append((confidence, row["recommendation"]))
        if joined:
            entry = h1_from_pairs(joined, "panel_joined_profiles", engine=engine)
            entry["n_excluded_missing_profile_confidence"] = n_missing_confidence
            entry["interpretation"] = (
                "rater recommendations against the evidence confidence shown "
                "for each profile (joined from profiles metadata); valid only "
                "if the instrument displayed that confidence to raters (see "
                "analysis/DESIGN_NOTES.md)"
            )
            sources.append(entry)
        else:
            sources.append(
                {
                    "source": "panel_joined_profiles",
                    "rho": None,
                    "p_value": None,
                    "n": 0,
                    "note": (
                        "no profile confidence available to join against panel "
                        "responses (profiles metadata absent or lacks "
                        "confidence_score)"
                    ),
                }
            )

    if not sources:
        return None
    return {
        "hypothesis": (
            "H1: lower evidence confidence leads to more conservative "
            "release recommendations"
        ),
        "ordinal_mapping": dict(RECOMMENDATION_ORDINAL),
        "expected_direction": (
            "negative Spearman rho (higher confidence pairs with lower, less "
            "conservative ordinal)"
        ),
        "sources": sources,
    }


# --------------------------------------------------------------------------
# H2: ENV control coverage pre/post
# --------------------------------------------------------------------------


def h2_coverage(
    rows: Sequence[Mapping[str, Any]],
    alternative: str = "two-sided",
    engine: str = "auto",
) -> dict[str, Any]:
    pre = [row["coverage_rate_pre"] for row in rows]
    post = [row["coverage_rate_post"] for row in rows]
    deltas = [b - a for a, b in zip(pre, post)]

    test = wilcoxon_signed_rank(post, pre, alternative=alternative, engine=engine)
    result = {
        "hypothesis": (
            "H2: the FairMind-E module raises ENV control coverage versus "
            "the baseline condition"
        ),
        "n_systems": len(rows),
        "statistic": test["statistic"],
        "p_value": test["p_value"],
        "alternative": test["alternative"],
        "implementation": test["implementation"],
        "p_method": test["p_method"],
        "n_nonzero": test["n_nonzero"],
        "n_zero_dropped": test["n_zero_dropped"],
        "median_delta": statistics.median(deltas),
        "mean_delta": _mean(deltas),
        "n_improved": sum(1 for d in deltas if d > 0),
        "n_worsened": sum(1 for d in deltas if d < 0),
        "n_unchanged": sum(1 for d in deltas if d == 0),
    }
    if "note" in test:
        result["note"] = test["note"]
    return result


# --------------------------------------------------------------------------
# H3: inter-rater agreement
# --------------------------------------------------------------------------


def _profile_counts(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, list[int]]:
    counts: dict[str, list[int]] = {}
    for row in rows:
        per_profile = counts.setdefault(
            row["profile_id"], [0] * len(RECOMMENDATION_LABELS)
        )
        per_profile[RECOMMENDATION_LABELS.index(row["recommendation"])] += 1
    return counts


def _mean_pairwise_cohen(
    profile_ids: Sequence[str],
    rater_ids: Sequence[str],
    labels_by_rater: Mapping[str, Mapping[str, str]],
    engine: str,
    collect_pairs: bool = False,
) -> tuple[float | None, int, list[dict[str, Any]]]:
    kappas: list[float] = []
    pair_details: list[dict[str, Any]] = []
    for rater_a, rater_b in itertools.combinations(sorted(rater_ids), 2):
        ratings_a = labels_by_rater[rater_a]
        ratings_b = labels_by_rater[rater_b]
        common = [
            profile_id
            for profile_id in profile_ids
            if profile_id in ratings_a and profile_id in ratings_b
        ]
        if len(common) < MIN_PAIR_OVERLAP:
            continue
        result = cohen_kappa(
            [ratings_a[profile_id] for profile_id in common],
            [ratings_b[profile_id] for profile_id in common],
            engine=engine,
        )
        kappas.append(result["kappa"])
        if collect_pairs:
            pair_details.append(
                {
                    "rater_a": rater_a,
                    "rater_b": rater_b,
                    "kappa": result["kappa"],
                    "n_common_profiles": result["n"],
                    "degenerate": result["degenerate"],
                    "implementation": result["implementation"],
                }
            )
    if not kappas:
        return None, 0, pair_details
    return _mean(kappas), len(kappas), pair_details


def h3_agreement(
    panel_rows: Sequence[Mapping[str, Any]],
    profiles_map: Mapping[str, Mapping[str, Any]],
    seed: int = DEFAULT_SEED,
    n_boot: int = DEFAULT_BOOTSTRAP_SAMPLES,
    engine: str = "auto",
) -> dict[str, Any]:
    notes: list[str] = []
    counts_by_profile = _profile_counts(panel_rows)
    rater_ids = sorted({row["rater_id"] for row in panel_rows})
    labels_by_rater: dict[str, dict[str, str]] = {rater: {} for rater in rater_ids}
    for row in panel_rows:
        labels_by_rater[row["rater_id"]][row["profile_id"]] = row["recommendation"]

    all_profiles = sorted(counts_by_profile)
    usable_profiles = [
        profile_id
        for profile_id in all_profiles
        if sum(counts_by_profile[profile_id]) >= 2
    ]
    excluded = [
        {
            "profile_id": profile_id,
            "n_raters": sum(counts_by_profile[profile_id]),
            "reason": "fewer than 2 ratings; agreement undefined",
        }
        for profile_id in all_profiles
        if profile_id not in usable_profiles
    ]

    per_profile: list[dict[str, Any]] = []
    have_expected = any(
        profiles_map.get(profile_id, {}).get("expected_recommendation")
        for profile_id in all_profiles
    )
    for profile_id in all_profiles:
        counts = counts_by_profile[profile_id]
        n_raters = sum(counts)
        if n_raters >= 2:
            agreement = sum(c * (c - 1) for c in counts) / (n_raters * (n_raters - 1))
        else:
            agreement = None
        # Deterministic modal label; count ties break toward the more
        # conservative (higher-ordinal) recommendation.
        modal = max(
            RECOMMENDATION_LABELS,
            key=lambda label: (
                counts[RECOMMENDATION_LABELS.index(label)],
                RECOMMENDATION_ORDINAL[label],
            ),
        )
        expected = profiles_map.get(profile_id, {}).get("expected_recommendation")
        per_profile.append(
            {
                "profile_id": profile_id,
                "n_raters": n_raters,
                "counts": dict(zip(RECOMMENDATION_LABELS, counts)),
                "observed_agreement": agreement,
                "modal_recommendation": modal,
                "expected_recommendation": expected,
                "modal_matches_expected": (
                    modal == expected if expected is not None else None
                ),
            }
        )

    pooled: dict[str, Any] = {
        "n_profiles_used": len(usable_profiles),
        "excluded_profiles": excluded,
        "n_raters": len(rater_ids),
        "min_pair_overlap": MIN_PAIR_OVERLAP,
    }

    if len(usable_profiles) == 0:
        pooled.update(
            {
                "fleiss_kappa": None,
                "mean_pairwise_cohen_kappa": None,
                "note": "no profiles with 2 or more ratings; agreement undefined",
            }
        )
        return {
            "hypothesis": (
                "H3: the decision matrix improves inter-rater agreement on "
                "release recommendations"
            ),
            "target_kappa": KAPPA_TARGET,
            "labels": list(RECOMMENDATION_LABELS),
            "n_responses": len(panel_rows),
            "pooled": pooled,
            "per_profile": per_profile,
            "by_role": {},
            "notes": notes,
        }

    fleiss = fleiss_kappa_from_counts(
        [counts_by_profile[profile_id] for profile_id in usable_profiles]
    )
    cohen_mean, n_pairs, pair_details = _mean_pairwise_cohen(
        usable_profiles, rater_ids, labels_by_rater, engine, collect_pairs=True
    )
    if cohen_mean is None:
        notes.append(
            "no rater pair shares at least "
            f"{MIN_PAIR_OVERLAP} profiles; mean pairwise Cohen kappa undefined"
        )

    # Deterministic bootstrap over profiles; one resample stream feeds both
    # statistics, and replicates always use the stdlib implementations so
    # intervals are identical with or without scipy/sklearn installed.
    rng = random.Random(seed)
    fleiss_values: list[float] = []
    cohen_values: list[float] = []
    n_skipped_fleiss = 0
    n_skipped_cohen = 0
    for _ in range(n_boot):
        sample = [
            usable_profiles[rng.randrange(len(usable_profiles))]
            for _ in range(len(usable_profiles))
        ]
        fleiss_value = fleiss_kappa_from_counts(
            [counts_by_profile[profile_id] for profile_id in sample]
        )["kappa"]
        if fleiss_value is None or not math.isfinite(fleiss_value):
            n_skipped_fleiss += 1
        else:
            fleiss_values.append(fleiss_value)
        cohen_value, _, _ = _mean_pairwise_cohen(
            sample, rater_ids, labels_by_rater, engine="stdlib"
        )
        if cohen_value is None or not math.isfinite(cohen_value):
            n_skipped_cohen += 1
        else:
            cohen_values.append(cohen_value)

    def ci_of(values: list[float]) -> list[float] | None:
        if not values:
            return None
        values = sorted(values)
        return [_percentile(values, 0.025), _percentile(values, 0.975)]

    pooled.update(
        {
            "fleiss_kappa": fleiss["kappa"],
            "fleiss_ci95": ci_of(fleiss_values),
            "fleiss_implementation": fleiss["implementation"],
            "mean_observed_agreement": fleiss["mean_observed_agreement"],
            "mean_pairwise_cohen_kappa": cohen_mean,
            "cohen_ci95": ci_of(cohen_values),
            "cohen_implementation": (
                "sklearn" if engine == "auto" and SKLEARN_AVAILABLE else "stdlib"
            ),
            "n_rater_pairs": n_pairs,
            "rater_pairs": pair_details,
            "target_met_fleiss": (
                fleiss["kappa"] > KAPPA_TARGET
                if fleiss["kappa"] is not None
                else None
            ),
            "target_met_cohen": (
                cohen_mean > KAPPA_TARGET if cohen_mean is not None else None
            ),
            "bootstrap": {
                "samples": n_boot,
                "seed": seed,
                "method": "percentile over profile resamples",
                "n_skipped_fleiss": n_skipped_fleiss,
                "n_skipped_cohen": n_skipped_cohen,
            },
        }
    )
    if have_expected:
        matched = [
            entry["modal_matches_expected"]
            for entry in per_profile
            if entry["modal_matches_expected"] is not None
        ]
        pooled["modal_matches_expected_rate"] = (
            _mean([1.0 if m else 0.0 for m in matched]) if matched else None
        )
    else:
        notes.append(
            "no expected labels available from profiles metadata; "
            "modal_matches_expected fields are null"
        )

    by_role: dict[str, Any] = {}
    for role in RATER_ROLES:
        role_rows = [row for row in panel_rows if row["rater_role"] == role]
        role_raters = sorted({row["rater_id"] for row in role_rows})
        role_counts = _profile_counts(role_rows)
        role_usable = [
            profile_id
            for profile_id in sorted(role_counts)
            if sum(role_counts[profile_id]) >= 2
        ]
        if len(role_raters) < 2 or len(role_usable) < 2:
            by_role[role] = {
                "n_raters": len(role_raters),
                "n_profiles_used": len(role_usable),
                "fleiss_kappa": None,
                "mean_pairwise_cohen_kappa": None,
                "note": (
                    f"needs at least 2 raters with role {role} rating at least "
                    "2 shared profiles (see analysis/DESIGN_NOTES.md)"
                ),
            }
            continue
        role_fleiss = fleiss_kappa_from_counts(
            [role_counts[profile_id] for profile_id in role_usable]
        )
        role_cohen, role_pairs, _ = _mean_pairwise_cohen(
            role_usable, role_raters, labels_by_rater, engine
        )
        by_role[role] = {
            "n_raters": len(role_raters),
            "n_profiles_used": len(role_usable),
            "fleiss_kappa": role_fleiss["kappa"],
            "mean_pairwise_cohen_kappa": role_cohen,
            "n_rater_pairs": role_pairs,
            "note": "point estimates only; the bootstrap CI is pooled",
        }

    return {
        "hypothesis": (
            "H3: the decision matrix improves inter-rater agreement on "
            "release recommendations"
        ),
        "target_kappa": KAPPA_TARGET,
        "labels": list(RECOMMENDATION_LABELS),
        "n_responses": len(panel_rows),
        "pooled": pooled,
        "per_profile": per_profile,
        "by_role": by_role,
        "notes": notes,
    }


# --------------------------------------------------------------------------
# H4: mitigation effect on carbon intensity
# --------------------------------------------------------------------------


def h4_mitigation(
    rows: Sequence[Mapping[str, Any]],
    seed: int = DEFAULT_SEED,
    n_boot: int = DEFAULT_BOOTSTRAP_SAMPLES,
    engine: str = "auto",
) -> dict[str, Any]:
    pre = [row["intensity_pre"] for row in rows]
    post = [row["intensity_post"] for row in rows]
    reductions = [percent_reduction(a, b) for a, b in zip(pre, post)]

    test = paired_ttest(pre, post, engine=engine)
    ci = _bootstrap_percentile_ci(
        len(reductions),
        lambda indices: _mean([reductions[i] for i in indices]),
        n_boot=n_boot,
        seed=seed,
    )
    mean_reduction = _mean(reductions)

    result = {
        "hypothesis": (
            "H4: documented mitigations reduce carbon intensity by more "
            "than 20 percent"
        ),
        "target_pct_reduction": H4_TARGET_PCT_REDUCTION,
        "unit": rows[0]["unit"],
        "n_pairs": len(rows),
        "n_workloads": len({row["workload_id"] for row in rows}),
        "t_statistic": test["t_statistic"],
        "df": test["df"],
        "p_value": test["p_value"],
        "implementation": test["implementation"],
        "p_method": test["p_method"],
        "mean_intensity_pre": _mean(pre),
        "mean_intensity_post": _mean(post),
        "mean_pct_reduction": mean_reduction,
        "median_pct_reduction": statistics.median(reductions),
        "pct_reduction_ci95": (
            [ci["low"], ci["high"]] if ci["low"] is not None else None
        ),
        "target_met_point": mean_reduction > H4_TARGET_PCT_REDUCTION,
        "target_met_ci_lower": (
            ci["low"] > H4_TARGET_PCT_REDUCTION if ci["low"] is not None else None
        ),
        "bootstrap": {
            "samples": ci["n_boot"],
            "seed": seed,
            "method": "percentile over pair resamples",
            "n_skipped": ci["n_skipped"],
        },
        "per_pair": [
            {
                "workload_id": row["workload_id"],
                "mitigation": row["mitigation"],
                "intensity_pre": row["intensity_pre"],
                "intensity_post": row["intensity_post"],
                "pct_reduction": reduction,
            }
            for row, reduction in zip(rows, reductions)
        ],
    }
    if "note" in test:
        result["note"] = test["note"]
    return result


# --------------------------------------------------------------------------
# Measurement accuracy: MAPE and Bland-Altman between methods
# --------------------------------------------------------------------------


def measurement_accuracy(
    runs_rows: Sequence[Mapping[str, Any]], metric: str = "energy_kwh"
) -> dict[str, Any]:
    """Between-method agreement statistics feeding threshold recalibration.

    Rows are paired on (workload_id, run_id): the harness emits one row per
    measurement method for the same physical run. Rows whose method was
    unavailable, or whose metric value is empty, are excluded and counted.
    """

    if metric not in ACCURACY_METRICS:
        raise ValueError(f"metric must be one of {ACCURACY_METRICS}")

    values: dict[str, dict[tuple[str, str], float]] = {}
    n_excluded = 0
    for row in runs_rows:
        if not row.get("method_available", True) or row[metric] is None:
            n_excluded += 1
            continue
        values.setdefault(row["measurement_method"], {})[
            (row["workload_id"], row["run_id"])
        ] = row[metric]

    methods_present = [m for m in MEASUREMENT_METHODS if m in values]

    def matched_keys(method_a: str, method_b: str) -> list[tuple[str, str]]:
        return sorted(set(values[method_a]) & set(values[method_b]))

    mape_rows: list[dict[str, Any]] = []
    for method_ref, method_alt in itertools.permutations(methods_present, 2):
        keys = matched_keys(method_ref, method_alt)
        usable = [key for key in keys if values[method_ref][key] != 0.0]
        n_zero_reference = len(keys) - len(usable)
        if not usable:
            mape_rows.append(
                {
                    "method_ref": method_ref,
                    "method_alt": method_alt,
                    "n_runs": 0,
                    "n_skipped_zero_reference": n_zero_reference,
                    "mape_pct": None,
                    "per_workload": [],
                }
            )
            continue
        reference = [values[method_ref][key] for key in usable]
        alternative = [values[method_alt][key] for key in usable]
        per_workload = []
        for workload_id in sorted({key[0] for key in usable}):
            workload_keys = [key for key in usable if key[0] == workload_id]
            per_workload.append(
                {
                    "workload_id": workload_id,
                    "n_runs": len(workload_keys),
                    "mape_pct": mape_pct(
                        [values[method_ref][key] for key in workload_keys],
                        [values[method_alt][key] for key in workload_keys],
                    ),
                }
            )
        mape_rows.append(
            {
                "method_ref": method_ref,
                "method_alt": method_alt,
                "n_runs": len(usable),
                "n_skipped_zero_reference": n_zero_reference,
                "mape_pct": mape_pct(reference, alternative),
                "per_workload": per_workload,
            }
        )

    bland_altman_rows: list[dict[str, Any]] = []
    for method_a, method_b in itertools.combinations(methods_present, 2):
        keys = matched_keys(method_a, method_b)
        if not keys:
            continue
        series_a = [values[method_a][key] for key in keys]
        series_b = [values[method_b][key] for key in keys]
        pooled = bland_altman(series_a, series_b)
        per_workload = []
        for workload_id in sorted({key[0] for key in keys}):
            workload_keys = [key for key in keys if key[0] == workload_id]
            workload_stats = bland_altman(
                [values[method_a][key] for key in workload_keys],
                [values[method_b][key] for key in workload_keys],
            )
            per_workload.append({"workload_id": workload_id, **workload_stats})
        bland_altman_rows.append(
            {
                "method_a": method_a,
                "method_b": method_b,
                **pooled,
                "per_workload": per_workload,
            }
        )

    return {
        "metric": metric,
        "pairing_key": "workload_id+run_id",
        "methods_present": methods_present,
        "n_rows_excluded": n_excluded,
        "implementation": "stdlib",
        "mape": mape_rows,
        "bland_altman": bland_altman_rows,
        "notes": [
            "MAPE is asymmetric; every ordered (reference, alternative) "
            "method pair is reported",
            "Bland-Altman differences are method_b minus method_a in "
            "canonical method order: " + ", ".join(MEASUREMENT_METHODS),
            "rows with method_available=false or an empty metric value are "
            "excluded and counted in n_rows_excluded",
        ],
    }


# --------------------------------------------------------------------------
# Orchestration and CLI
# --------------------------------------------------------------------------


def run_all(
    panel_path: pathlib.Path | None = None,
    runs_path: pathlib.Path | None = None,
    coverage_path: pathlib.Path | None = None,
    mitigation_path: pathlib.Path | None = None,
    profiles_path: pathlib.Path | None = None,
    metric: str = "energy_kwh",
    h2_alternative: str = "two-sided",
    seed: int = DEFAULT_SEED,
    n_boot: int = DEFAULT_BOOTSTRAP_SAMPLES,
    engine: str = "auto",
) -> dict[str, Any]:
    notes: list[str] = []
    panel_rows = load_panel(panel_path) if panel_path else None
    runs_rows = load_measurement_runs(runs_path) if runs_path else None
    coverage_rows = load_coverage(coverage_path) if coverage_path else None
    mitigation_rows = load_mitigation(mitigation_path) if mitigation_path else None

    profiles_map: dict[str, dict[str, Any]] = {}
    if panel_rows is not None:
        lookup = profiles_path if profiles_path else DEFAULT_PROFILES_PATH
        profiles_map, profile_notes = load_profiles(lookup)
        notes.extend(profile_notes)

    results: dict[str, Any] = {
        "meta": {
            "module": "research/fairmind-e/analysis/hypotheses.py",
            "seed": seed,
            "bootstrap_samples": n_boot,
            "engine_requested": engine,
            "scipy_available": SCIPY_AVAILABLE,
            "sklearn_available": SKLEARN_AVAILABLE,
            "implementation_note": (
                "scipy/sklearn are preferred when importable; pure-stdlib "
                "fallbacks otherwise; bootstrap resampling is always stdlib "
                "so intervals are identical across environments"
            ),
            "inputs": {
                "panel": str(panel_path) if panel_path else None,
                "runs": str(runs_path) if runs_path else None,
                "coverage": str(coverage_path) if coverage_path else None,
                "mitigation": str(mitigation_path) if mitigation_path else None,
                "profiles": (
                    str(profiles_path if profiles_path else DEFAULT_PROFILES_PATH)
                    if panel_rows is not None
                    else None
                ),
            },
            "notes": notes,
        }
    }

    h1 = h1_section(runs_rows, panel_rows, profiles_map, engine=engine)
    if h1 is not None:
        results["h1"] = h1
    if coverage_rows is not None:
        results["h2"] = h2_coverage(
            coverage_rows, alternative=h2_alternative, engine=engine
        )
    if panel_rows is not None:
        results["h3"] = h3_agreement(
            panel_rows, profiles_map, seed=seed, n_boot=n_boot, engine=engine
        )
    if mitigation_rows is not None:
        results["h4"] = h4_mitigation(
            mitigation_rows, seed=seed, n_boot=n_boot, engine=engine
        )
    if runs_rows is not None:
        results["measurement_accuracy"] = measurement_accuracy(
            runs_rows, metric=metric
        )
    return results


def _jsonable(value: Any) -> Any:
    """Convert to strict JSON: non-finite floats become null."""

    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _format_number(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_text(results: Mapping[str, Any]) -> str:
    lines: list[str] = []
    meta = results.get("meta", {})
    lines.append(
        "FairMind-E hypothesis statistics "
        f"(seed={meta.get('seed')}, scipy={meta.get('scipy_available')}, "
        f"sklearn={meta.get('sklearn_available')})"
    )
    h1 = results.get("h1")
    if h1:
        for source in h1["sources"]:
            lines.append(
                f"H1 [{source['source']}] rho={_format_number(source.get('rho'))} "
                f"p={_format_number(source.get('p_value'))} n={source.get('n')} "
                f"({source.get('implementation', 'n/a')})"
            )
    h2 = results.get("h2")
    if h2:
        lines.append(
            f"H2 wilcoxon statistic={_format_number(h2['statistic'])} "
            f"p={_format_number(h2['p_value'])} "
            f"median_delta={_format_number(h2['median_delta'])} "
            f"n={h2['n_systems']} ({h2['implementation']})"
        )
    h3 = results.get("h3")
    if h3:
        pooled = h3["pooled"]
        lines.append(
            f"H3 fleiss={_format_number(pooled.get('fleiss_kappa'))} "
            f"ci95={pooled.get('fleiss_ci95')} "
            f"mean_cohen={_format_number(pooled.get('mean_pairwise_cohen_kappa'))} "
            f"ci95={pooled.get('cohen_ci95')} target>{h3['target_kappa']}"
        )
    h4 = results.get("h4")
    if h4:
        lines.append(
            f"H4 t={_format_number(h4['t_statistic'])} "
            f"p={_format_number(h4['p_value'])} "
            f"mean_reduction={_format_number(h4['mean_pct_reduction'])}pct "
            f"ci95={h4.get('pct_reduction_ci95')} n={h4['n_pairs']} "
            f"({h4['implementation']})"
        )
    accuracy = results.get("measurement_accuracy")
    if accuracy:
        for row in accuracy["mape"]:
            lines.append(
                f"MAPE {row['method_ref']} -> {row['method_alt']}: "
                f"{_format_number(row['mape_pct'])}pct (n={row['n_runs']})"
            )
        for row in accuracy["bland_altman"]:
            lines.append(
                f"Bland-Altman {row['method_a']} vs {row['method_b']}: "
                f"bias={_format_number(row['mean_bias'])} "
                f"loa95=[{_format_number(row['loa95_low'])}, "
                f"{_format_number(row['loa95_high'])}] (n={row['n']})"
            )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compute the FairMind-E pre-registered hypothesis statistics "
            "(H1-H4) and measurement-accuracy statistics from CSV inputs."
        )
    )
    parser.add_argument("--panel", type=pathlib.Path, help="panel responses CSV")
    parser.add_argument("--runs", type=pathlib.Path, help="measurement runs CSV")
    parser.add_argument("--coverage", type=pathlib.Path, help="coverage pre/post CSV")
    parser.add_argument("--mitigation", type=pathlib.Path, help="mitigation pairs CSV")
    parser.add_argument(
        "--profiles",
        type=pathlib.Path,
        default=None,
        help=(
            "profiles metadata JSON (default: research/fairmind-e/profiles/"
            "profiles.json; optional, degrades gracefully when absent)"
        ),
    )
    parser.add_argument(
        "--metric",
        choices=ACCURACY_METRICS,
        default="energy_kwh",
        help="metric for MAPE and Bland-Altman (default: energy_kwh)",
    )
    parser.add_argument(
        "--h2-alternative",
        choices=("two-sided", "greater", "less"),
        default="two-sided",
        help="alternative hypothesis for the H2 Wilcoxon test",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--bootstrap", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES,
        help="bootstrap resamples for confidence intervals",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "stdlib"),
        default="auto",
        help="auto prefers scipy/sklearn when importable; stdlib forces fallbacks",
    )
    parser.add_argument(
        "--format", choices=("json", "text"), default="json", dest="output_format"
    )
    parser.add_argument("--out", type=pathlib.Path, help="write output to this path")
    args = parser.parse_args(argv)

    if not any((args.panel, args.runs, args.coverage, args.mitigation)):
        parser.error(
            "provide at least one input CSV (--panel, --runs, --coverage, "
            "--mitigation)"
        )

    try:
        results = run_all(
            panel_path=args.panel,
            runs_path=args.runs,
            coverage_path=args.coverage,
            mitigation_path=args.mitigation,
            profiles_path=args.profiles,
            metric=args.metric,
            h2_alternative=args.h2_alternative,
            seed=args.seed,
            n_boot=args.bootstrap,
            engine=args.engine,
        )
    except SchemaError as exc:
        print(f"schema error: {exc}", file=sys.stderr)
        return 2

    if args.output_format == "text":
        output = render_text(results)
    else:
        output = json.dumps(_jsonable(results), indent=2) + "\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

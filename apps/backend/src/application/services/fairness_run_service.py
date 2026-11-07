"""First verdict: a predictions CSV in, measured fairness evidence and a release gate out.

Pure functions over bytes and dicts; the router owns persistence. Metrics come
from ``fairness_library.metrics`` (bootstrap intervals and permutation tests),
which until now was never reachable from any route.
"""

from __future__ import annotations

import hashlib
import io
import itertools
import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from fairness_library.metrics import (
    _compute_calibration_diff,
    _compute_dp_diff,
    _compute_eo_diff,
    _compute_eopp_diff,
)
from src.domain.environmental.confidence import ESTIMATED_THRESHOLD, MEASURED_THRESHOLD, band_from_score, cap_confidence_for_provenance
from src.domain.environmental.decision_matrix import DECISION_MATRIX, get_recommendation

MAX_ROWS = 100_000  # ponytail: synchronous run; move to a job past this
MIN_GROUP_SIZE = 30

OUTCOME_HINTS = ("y_true", "label", "outcome", "target", "actual", "ground_truth", "truth", "repaid", "defaulted", "default", "churned", "hired", "readmitted", "fraud", "claim_paid")
PREDICTION_HINTS = ("y_pred", "prediction", "pred", "decision", "predicted", "approved", "selected")
SCORE_HINTS = ("score", "proba", "probability", "p_", "prob", "risk_score", "likelihood")
# Protected grounds FairMind looks for in a file, and the column-name hint for each ground. A hint matches
# whole tokens of a column name (camelCase split), so "statement_date", "mortgage" and "sussex" do not match.
GROUNDS = ("gender", "age", "caste or social category", "religion", "disability", "language", "marital status", "region")
ATTRIBUTE_HINTS: Dict[str, Optional[str]] = {
    "gender": "gender", "sex": "gender",
    "age": "age", "age_band": "age", "age_group": "age", "dob": "age", "date_of_birth": "age", "birth_date": "age", "birthdate": "age",
    "caste": "caste or social category", "social_category": "caste or social category",
    "religion": "religion", "disability": "disability", "language": "language", "marital": "marital status",
    "region": "region", "state": "region", "district": "region", "urban_rural": "region", "city_tier": "region",
    "race": None, "ethnicity": None, "nationality": None,
}
# A bare "tier" is a city tier; "customer_tier" and "premium_tier" are not protected. A column named "category"
# counts only through the reservation-values check, so it is not a name hint.
EXACT_ATTRIBUTE_HINTS = {"tier": "region"}
RESERVATION_VALUES = {"gen", "general", "obc", "sc", "st", "ews"}
GENDER_VALUES = {"m", "f", "male", "female", "x", "other", "transgender", "nonbinary", "non-binary"}
MAX_ATTRIBUTE_VALUES = 50  # more groups than this cannot be compared; bin first
POSSIBLE_BASIS = "Few distinct values; the name is not a protected attribute. Tick it only if it stands in for one."
REASON_MIN_CHARS = 12

DI_THRESHOLD = 0.80   # four-fifths rule
GAP_THRESHOLD = 0.05  # equal opportunity and equalized odds difference
SIGNIFICANCE = 0.05   # permutation p-value below which a disparity is not noise


def json_safe(value: Any) -> Any:
    """Round-trip through JSON with numpy scalars and arrays made plain."""
    def default(obj: Any) -> Any:
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return None if math.isnan(float(obj)) else float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    return json.loads(json.dumps(value, default=default))


class FairnessRunError(ValueError):
    """A problem with the file or the column mapping; reported as 422."""


def _read_csv(data: bytes) -> pd.DataFrame:
    try:
        frame = pd.read_csv(io.BytesIO(data))
    except Exception as exc:  # pragma: no cover - pandas message is the useful part
        raise FairnessRunError(f"Could not read the file as CSV: {exc}") from exc
    if frame.empty:
        raise FairnessRunError("The CSV has no rows")
    if len(frame) > MAX_ROWS:
        raise FairnessRunError(f"The CSV has {len(frame)} rows; the limit for a synchronous run is {MAX_ROWS}")
    return frame


def _match(columns: Iterable[str], hints: Iterable[str]) -> Optional[str]:
    lowered = {c: c.lower().strip() for c in columns}
    for hint in hints:
        for original, low in lowered.items():
            if low == hint:
                return original
    for hint in hints:
        for original, low in lowered.items():
            if hint in low:
                return original
    return None


def _tokens(name: str) -> List[str]:
    """Lower-case words of a column name: "applicantAgeBand" and "applicant_age_band" both give applicant, age, band."""
    return [t.lower() for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+", name)]


def _attribute_hint(name: str) -> Optional[str]:
    """The longest attribute hint found as whole adjacent tokens of the column name."""
    if name.strip().lower() in EXACT_ATTRIBUTE_HINTS:
        return name.strip().lower()
    tokens = _tokens(name)
    found = []
    for hint in ATTRIBUTE_HINTS:
        run = _tokens(hint)
        if any(tokens[i:i + len(run)] == run for i in range(len(tokens) - len(run) + 1)):
            found.append((len(run), hint))
    return max(found)[1] if found else None


def _attribute_column(name: str, series: pd.Series) -> Dict[str, Any]:
    """Whether one column looks like a protected attribute, why, and which ground it covers."""
    distinct = int(series.dropna().nunique())
    hint = _attribute_hint(name)
    ground = {**ATTRIBUTE_HINTS, **EXACT_ATTRIBUTE_HINTS}.get(hint) if hint else None
    basis = f'Name matches "{hint}"' if hint else None
    if hint and distinct > MAX_ATTRIBUTE_VALUES:
        return {"status": "too_many_values", "basis": basis, "ground": ground}
    values = {str(v).strip().lower() for v in series.dropna().unique()} if 2 <= distinct <= 12 else set()
    if values and values <= RESERVATION_VALUES:
        return {"status": "suggested", "basis": "The values look like reservation categories", "ground": "caste or social category"}
    if values and values <= GENDER_VALUES:
        return {"status": "suggested", "basis": f"{basis}, and the values look like gender" if basis else "The values look like gender", "ground": "gender"}
    if basis:
        return {"status": "suggested", "basis": basis, "ground": ground}
    if 2 <= distinct <= 12:
        return {"status": "possible", "basis": POSSIBLE_BASIS, "ground": None}
    return {"status": None, "basis": None, "ground": None}


def uncovered_grounds(attributes: Iterable[str], columns: List[Dict[str, Any]]) -> List[str]:
    """The grounds no chosen column covers, in GROUNDS order."""
    chosen = set(attributes)
    covered = {c["attribute"]["ground"] for c in columns if c["name"] in chosen}
    return [g for g in GROUNDS if g not in covered]


def inspect_csv(data: bytes, previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Columns, a few sample values each, and a suggested mapping to confirm.

    ``previous`` is the metadata of the system's last fairness run: its attributes that exist in this
    file are suggested instead of inferring again, so monitoring and later runs test the same columns.
    """
    frame = _read_csv(data)
    columns = [str(c) for c in frame.columns]
    binary_like = [c for c in columns if frame[c].dropna().nunique() <= 2]
    numeric_unit = [
        c for c in columns
        if pd.api.types.is_numeric_dtype(frame[c]) and frame[c].dropna().between(0, 1).all() and frame[c].dropna().nunique() > 2
    ]
    outcome = _match(binary_like, OUTCOME_HINTS) or _match(columns, OUTCOME_HINTS)
    prediction = _match([c for c in binary_like if c != outcome], PREDICTION_HINTS) or _match(columns, PREDICTION_HINTS)
    if outcome is None:
        # No recognisable name: the first 0/1 column that is not the prediction is the best guess to confirm.
        outcome = next((c for c in binary_like if c != prediction), None)
    score = _match(numeric_unit, SCORE_HINTS) or _match(columns, SCORE_HINTS)
    mapped = (outcome, prediction, score)
    assessed = {c: {"status": None, "basis": None, "ground": None} if c in mapped else _attribute_column(c, frame[c]) for c in columns}
    attributes = [c for c in columns if assessed[c]["status"] == "suggested"]
    source = "inferred" if attributes else "none"
    confirmed_by = confirmed_at = None
    previous_unconfirmed = False

    confirmation = (previous or {}).get("attribute_confirmation") or {}
    earlier = confirmation.get("attributes") or ((previous or {}).get("mapping") or {}).get("attributes") or []
    reused = [a for a in earlier if a in assessed and a not in mapped and assessed[a]["status"] != "too_many_values"]
    if reused:
        person = bool(confirmation.get("confirmed"))
        for c in columns:
            if c in reused:
                if assessed[c]["status"] != "suggested":
                    assessed[c] = {**assessed[c], "basis": "Confirmed in the last run" if person else "Used in the last run"}
                assessed[c]["status"] = "suggested"
            elif assessed[c]["status"] == "suggested":
                assessed[c] = {**assessed[c], "status": "possible", "basis": f"{assessed[c]['basis']}; not used in the last run"}
        attributes, source = reused, "confirmed"
        confirmed_by, confirmed_at = (confirmation.get("confirmedBy"), confirmation.get("confirmedAt")) if person else (None, None)
        previous_unconfirmed = not person

    described = [
        {
            "name": c,
            "dtype": str(frame[c].dtype),
            "distinct": int(frame[c].dropna().nunique()),
            "sample": [str(v) for v in frame[c].dropna().unique()[:5]],
            "attribute": assessed[c],
        }
        for c in columns
    ]
    return {
        "rows": int(len(frame)),
        "fileSha256": hashlib.sha256(data).hexdigest(),
        "columns": described,
        "suggested": {"outcome": outcome, "prediction": prediction, "score": score, "attributes": attributes},
        "attributeSource": source,
        "confirmedBy": confirmed_by,
        "confirmedAt": confirmed_at,
        "previousRunUnconfirmed": previous_unconfirmed,
        "needsBinning": [{"name": c["name"], "distinct": c["distinct"]} for c in described if c["attribute"]["status"] == "too_many_values"],
        "uncoveredGrounds": uncovered_grounds(attributes, described),
    }


def _and(items: List[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


def confirm_attributes(
    inspection: Dict[str, Any],
    attributes: List[str],
    *,
    via_ui: bool,
    actor: str,
    now: str,
    confirm_sha256: Optional[str] = None,
    removal_reason: Optional[str] = None,
    uncovered_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """The attribute confirmation stored with a run, against the suggestion recomputed from the same bytes.

    A run from the UI (``via_ui``) is a person confirming: the file must be the one they saw, and unticking a
    suggestion or leaving a ground uncovered needs a reason. API and CLI runs are recorded as not confirmed.
    """
    suggested = inspection["suggested"]["attributes"]
    removed = [a for a in suggested if a not in attributes]
    grounds = uncovered_grounds(attributes, inspection["columns"])
    removal = (removal_reason or "").strip() or None
    uncovered = (uncovered_reason or "").strip() or None
    if via_ui:
        if (confirm_sha256 or "").strip().lower() != inspection["fileSha256"]:
            raise FairnessRunError("The file changed since you confirmed it")
        if removed and len(removal or "") < REASON_MIN_CHARS:
            raise FairnessRunError(f"You unticked {_and(removed)} from the suggested protected attributes; say why")
        if grounds and len(uncovered or "") < REASON_MIN_CHARS:
            raise FairnessRunError(f"Say where {_and(grounds)} are tested, or why they don't apply")
    return {
        "via": "ui" if via_ui else "api",
        "confirmed": via_ui,
        "suggested": suggested,
        "suggestedReasons": {c["name"]: c["attribute"]["basis"] for c in inspection["columns"] if c["name"] in suggested},
        "source": inspection["attributeSource"],
        "attributes": attributes,
        "added": [a for a in attributes if a not in suggested],
        "removed": removed,
        "removalReason": removal,
        "uncoveredGrounds": grounds,
        "uncoveredReason": uncovered,
        "fileSha256": inspection["fileSha256"],
        "confirmedBy": actor if via_ui else None,
        "confirmedAt": now if via_ui else None,
    }


def _binary(series: pd.Series, favorable: Any, name: str) -> np.ndarray:
    values = series
    if favorable is None or favorable == "":
        uniques = set(values.dropna().unique().tolist())
        if uniques <= {0, 1, 0.0, 1.0, True, False}:
            return values.fillna(0).astype(int).to_numpy()
        if uniques <= {"0", "1", "true", "false", "yes", "no", "True", "False", "Yes", "No"}:
            return values.astype(str).str.lower().isin(["1", "true", "yes"]).astype(int).to_numpy()
        raise FairnessRunError(f"Column {name} is not 0/1; say which value counts as favorable")
    return (values.astype(str) == str(favorable)).astype(int).to_numpy()




N_RESAMPLES = 400  # ponytail: bootstrap and permutation draws; raise when runs move to a job


def _di_ratio(y_pred: np.ndarray, sensitive: np.ndarray) -> float:
    rates = [y_pred[sensitive == g].mean() for g in np.unique(sensitive)]
    top = max(rates)
    return float(min(rates) / top) if top > 0 else 0.0


def _attribute_stats(
    y_true: np.ndarray, y_pred: np.ndarray, proba: Optional[np.ndarray], sensitive: np.ndarray, rng: np.random.Generator, *, alpha: float = SIGNIFICANCE
) -> Dict[str, Any]:
    """Point estimate, 95% bootstrap interval and permutation p-value per metric.

    The library's own ``_bootstrap_metric_ci`` re-evaluates the statistic on the
    same rows, so its intervals collapse to the estimate; the resampling is done
    here. Bootstrap resamples rows with replacement; the permutation test shuffles
    the attribute, so the p-value is the share of shuffles at least as unequal.
    """
    n = len(y_pred)
    has_proba = proba is not None

    def all_stats(yt: np.ndarray, yp: np.ndarray, pr: Optional[np.ndarray], sa: np.ndarray) -> Dict[str, float]:
        out = {
            "disparate_impact_ratio": _di_ratio(yp, sa),
            "demographic_parity": float(_compute_dp_diff(yp, sa)),
            "equal_opportunity": float(_compute_eopp_diff(yt, yp, sa)),
            "equalized_odds": float(_compute_eo_diff(yt, yp, sa)),
        }
        if has_proba:
            out["calibration"] = float(_compute_calibration_diff(yt, pr, sa, 10))
        return out

    observed = all_stats(y_true, y_pred, proba, sensitive)
    boot: Dict[str, List[float]] = {k: [] for k in observed}
    perm: Dict[str, List[float]] = {k: [] for k in observed}
    for _ in range(N_RESAMPLES):
        idx = rng.integers(0, n, n)
        for k, v in all_stats(y_true[idx], y_pred[idx], proba[idx] if has_proba else None, sensitive[idx]).items():
            boot[k].append(v)
        shuffled = rng.permutation(sensitive)
        for k, v in all_stats(y_true, y_pred, proba, shuffled).items():
            perm[k].append(v)

    def metric(key: str, *, lower_is_fair: bool = True) -> Dict[str, Any]:
        value = observed[key]
        lo, hi = np.nanpercentile(np.array(boot[key], dtype=float), [2.5, 97.5])
        draws = np.array(perm[key], dtype=float)
        p_value = float(np.mean(draws <= value)) if not lower_is_fair else float(np.mean(draws >= value))
        crosses = value < DI_THRESHOLD if not lower_is_fair else value > GAP_THRESHOLD
        significant = p_value < alpha
        # A disparity counts only when it crosses the threshold and the shuffled-attribute
        # null rarely produces one that large; noise on small samples does not fail a check.
        is_fair = not (crosses and significant)
        return {
            "metric_name": key,
            "value": float(value),
            "confidence_interval": [float(lo), float(hi)],
            "p_value": p_value,
            "significant": bool(significant),
            "alpha": alpha,
            "crosses_threshold": bool(crosses),
            "is_fair": bool(is_fair),
            "threshold": DI_THRESHOLD if not lower_is_fair else GAP_THRESHOLD,
            "resamples": N_RESAMPLES,
        }

    return {
        "disparate_impact_ratio": metric("disparate_impact_ratio", lower_is_fair=False),
        "demographic_parity": metric("demographic_parity"),
        "equal_opportunity": metric("equal_opportunity"),
        "equalized_odds": metric("equalized_odds"),
        "calibration": metric("calibration") if has_proba else None,
    }


def run_fairness(
    data: bytes,
    *,
    outcome: str,
    attributes: List[str],
    prediction: Optional[str] = None,
    score: Optional[str] = None,
    favorable_label: Any = None,
    score_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Compute the first-verdict metric set for each protected attribute."""
    frame = _read_csv(data)
    missing = [c for c in [outcome, prediction, score, *attributes] if c and c not in frame.columns]
    if missing:
        raise FairnessRunError(f"Columns not in the file: {', '.join(missing)}")
    if not prediction and not score:
        raise FairnessRunError("Map either a prediction column or a score column")
    if not attributes:
        raise FairnessRunError("Map at least one protected attribute column")

    y_true = _binary(frame[outcome], favorable_label, outcome)
    proba = None
    if score:
        proba = pd.to_numeric(frame[score], errors="coerce").to_numpy(dtype=float)
        if np.isnan(proba).any():
            raise FairnessRunError(f"Column {score} has non-numeric values")
    y_pred = _binary(frame[prediction], favorable_label, prediction) if prediction else (proba >= score_threshold).astype(int)

    per_attribute: List[Dict[str, Any]] = []
    all_fair = True
    smallest_group = None
    rng = np.random.default_rng(20261102)
    # One run asks several questions at once (3 or 4 checks per attribute); Bonferroni keeps the
    # chance that fair data fails any of them at SIGNIFICANCE, instead of 5% per check.
    checks_per_attribute = 4 if proba is not None else 3
    alpha = SIGNIFICANCE / (len(attributes) * checks_per_attribute)
    for attribute in attributes:
        sensitive = frame[attribute].astype(str).fillna("missing").to_numpy()
        groups, counts = np.unique(sensitive, return_counts=True)
        if len(groups) < 2:
            raise FairnessRunError(f"Column {attribute} has only one value; it cannot be a protected attribute here")
        rates = {str(g): float(y_pred[sensitive == g].mean()) for g in groups}
        stats = _attribute_stats(y_true, y_pred, proba, sensitive, rng, alpha=alpha)
        checks = {
            "disparate_impact": bool(stats["disparate_impact_ratio"]["is_fair"]),
            "equal_opportunity": bool(stats["equal_opportunity"]["is_fair"]),
            "equalized_odds": bool(stats["equalized_odds"]["is_fair"]),
            **({"calibration": bool(stats["calibration"]["is_fair"])} if stats["calibration"] else {}),
        }
        group_sizes = {str(g): int(n) for g, n in zip(groups, counts)}
        smallest_here = min(group_sizes.values())
        smallest_group = smallest_here if smallest_group is None else min(smallest_group, smallest_here)
        all_fair = all_fair and all(checks.values())
        per_attribute.append(
            {
                "attribute": attribute,
                "groups": group_sizes,
                "selection_rates": rates,
                "disparate_impact_ratio": stats["disparate_impact_ratio"]["value"],
                "disparate_impact": stats["disparate_impact_ratio"],
                "demographic_parity": stats["demographic_parity"],
                "equal_opportunity": stats["equal_opportunity"],
                "equalized_odds": stats["equalized_odds"],
                "calibration": stats["calibration"],
                "checks": checks,
                "small_groups": [g for g, n in group_sizes.items() if n < MIN_GROUP_SIZE],
            }
        )

    n = int(len(frame))
    histograms = None
    if proba is not None:
        histograms = {
            "bins": SCORE_BINS.tolist(),
            "overall": score_histogram(proba),
            "by_attribute": {
                attribute: {str(g): score_histogram(proba[frame[attribute].astype(str).fillna("missing").to_numpy() == g]) for g in np.unique(frame[attribute].astype(str).fillna("missing").to_numpy())}
                for attribute in attributes
            },
        }
    payload = {
        "rows": n,
        "score_histograms": histograms,
        "positive_rate": float(y_pred.mean()),
        "base_rate": float(y_true.mean()),
        "mapping": {"outcome": outcome, "prediction": prediction, "score": score, "attributes": attributes, "favorable_label": favorable_label},
        "thresholds": {"disparate_impact_ratio": DI_THRESHOLD, "gap": GAP_THRESHOLD, "alpha": alpha, "tests": len(attributes) * checks_per_attribute},
        "attributes": per_attribute,
        "all_checks_pass": bool(all_fair),
        "smallest_group": smallest_group,
        "evidence_confidence": evidence_confidence(n, smallest_group or 0, per_attribute),
    }
    return json_safe(payload)


def evidence_confidence(rows: int, smallest_group: int, per_attribute: List[Dict[str, Any]]) -> float:
    """Measured evidence starts at the bottom of the measured band and earns the rest.

    Sample size, group coverage and interval width move it up; nothing here can
    push attested evidence into the measured band (see confidence.py).
    """
    score = 0.85
    if rows >= 1_000:
        score += 0.05
    if smallest_group >= 100:
        score += 0.05
    widths = [a["demographic_parity"]["confidence_interval"][1] - a["demographic_parity"]["confidence_interval"][0] for a in per_attribute]
    if widths and max(widths) <= 0.05:
        score += 0.05
    if smallest_group < MIN_GROUP_SIZE:
        score = 0.85  # too few rows in a group: measured, but not more than the floor
    return round(min(score, 1.0), 2)


# ---------------------------------------------------------------------------
# Monitoring runs: current scores against the last fairness run as baseline
# ---------------------------------------------------------------------------

SCORE_BINS = np.linspace(0.0, 1.0, 11)
PSI_MODERATE, PSI_SIGNIFICANT = 0.10, 0.25
RATE_DRIFT_THRESHOLD = 0.05


def score_histogram(scores: np.ndarray) -> List[int]:
    """Counts of scores per fixed decile bin on [0, 1]."""
    counts, _ = np.histogram(np.clip(scores, 0.0, 1.0), bins=SCORE_BINS)
    return [int(c) for c in counts]


def psi(expected_counts: List[int], actual_counts: List[int]) -> Optional[float]:
    """Population stability index between two histograms over the same bins.

    Empty bins are floored at 0.0001 so a single empty bin does not blow up;
    below 0.10 is stable, 0.10 to 0.25 moderate, above 0.25 significant.
    """
    e, a = np.array(expected_counts, dtype=float), np.array(actual_counts, dtype=float)
    if e.sum() == 0 or a.sum() == 0 or len(e) != len(a):
        return None
    e = np.maximum(e / e.sum(), 1e-4)
    a = np.maximum(a / a.sum(), 1e-4)
    return float(np.sum((a - e) * np.log(a / e)))


def run_monitoring(
    data: bytes,
    *,
    attributes: List[str],
    prediction: Optional[str] = None,
    score: Optional[str] = None,
    baseline: Optional[Dict[str, Any]] = None,
    favorable_label: Any = None,
    score_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Selection-rate drift, impact ratio and score PSI per attribute against the baseline run."""
    frame = _read_csv(data)
    missing = [c for c in [prediction, score, *attributes] if c and c not in frame.columns]
    if missing:
        raise FairnessRunError(f"Columns not in the file: {', '.join(missing)}")
    if not prediction and not score:
        raise FairnessRunError("Map either a prediction column or a score column")
    if not attributes:
        raise FairnessRunError("Map at least one protected attribute column")
    proba = None
    if score:
        proba = pd.to_numeric(frame[score], errors="coerce").to_numpy(dtype=float)
        if np.isnan(proba).any():
            raise FairnessRunError(f"Column {score} has non-numeric values")
    y_pred = _binary(frame[prediction], favorable_label, prediction) if prediction else (proba >= score_threshold).astype(int)

    base_attrs = {a["attribute"]: a for a in (baseline or {}).get("attributes", [])}
    base_hist = (baseline or {}).get("score_histograms") or {}
    per_attribute: List[Dict[str, Any]] = []
    all_pass = True
    for attribute in attributes:
        sensitive = frame[attribute].astype(str).fillna("missing").to_numpy()
        groups, counts = np.unique(sensitive, return_counts=True)
        rates = {str(g): float(y_pred[sensitive == g].mean()) for g in groups}
        top = max(rates.values())
        di_ratio = float(min(rates.values()) / top) if top > 0 else 0.0
        base_rates = (base_attrs.get(attribute) or {}).get("selection_rates") or {}
        drift = {g: abs(rates[g] - base_rates[g]) for g in rates if g in base_rates}
        psi_by_group: Dict[str, Optional[float]] = {}
        if proba is not None and base_hist.get("by_attribute", {}).get(attribute):
            for g in groups:
                expected = base_hist["by_attribute"][attribute].get(str(g))
                psi_by_group[str(g)] = psi(expected, score_histogram(proba[sensitive == g])) if expected else None
        worst_psi = max((v for v in psi_by_group.values() if v is not None), default=None)
        checks = {"disparate_impact": bool(di_ratio >= DI_THRESHOLD)}
        if drift:
            checks["selection_rate_stable"] = bool(max(drift.values()) <= RATE_DRIFT_THRESHOLD)
        if worst_psi is not None:
            checks["score_stable"] = bool(worst_psi < PSI_MODERATE)
        all_pass = all_pass and all(checks.values())
        per_attribute.append(
            {
                "attribute": attribute,
                "groups": {str(g): int(c) for g, c in zip(groups, counts)},
                "selection_rates": rates,
                "baseline_selection_rates": base_rates,
                "rate_drift": drift,
                "max_rate_drift": max(drift.values()) if drift else None,
                "disparate_impact_ratio": di_ratio,
                "psi_by_group": psi_by_group,
                "worst_psi": worst_psi,
                "checks": checks,
            }
        )
    overall_psi = psi(base_hist.get("overall"), score_histogram(proba)) if proba is not None and base_hist.get("overall") else None
    n = int(len(frame))
    confidence = 0.85 + (0.05 if n >= 1_000 else 0.0) + (0.05 if baseline else 0.0)
    return json_safe(
        {
            "rows": n,
            "positive_rate": float(y_pred.mean()),
            "mapping": {"prediction": prediction, "score": score, "attributes": attributes},
            "thresholds": {"disparate_impact_ratio": DI_THRESHOLD, "rate_drift": RATE_DRIFT_THRESHOLD, "psi_moderate": PSI_MODERATE, "psi_significant": PSI_SIGNIFICANT},
            "baseline": {"present": bool(baseline), "rows": (baseline or {}).get("rows")},
            "overall_psi": overall_psi,
            "attributes": per_attribute,
            "all_checks_pass": bool(all_pass),
            "evidence_confidence": round(min(confidence, 1.0), 2),
        }
    )


# ---------------------------------------------------------------------------
# Attestations: a person states that a check is satisfied; manual provenance
# ---------------------------------------------------------------------------

ATTESTABLE_CHECKS = {
    "data_governance": ("data_governance", "Data governance attested"),
    "human_oversight": ("human_oversight", "Human oversight attested"),
    "monitoring": ("monitoring", "Monitoring attested"),
    "environmental": ("environmental", "Environmental impact attested"),
}
ATTESTATION_CONFIDENCE = 0.30  # top of the manual band (confidence.py)


# ---------------------------------------------------------------------------
# Release gate: the FairMind-E matrix applied to a system's whole evidence record
# ---------------------------------------------------------------------------

GATE_CHECKS = (
    ("fairness", "Fairness measured", {"fairness_test"}),
    ("data_governance", "Data governance", {"data", "dataset", "data_governance", "data_lineage", "provenance", "training_data"}),
    ("human_oversight", "Human oversight", {"human_oversight", "policy", "oversight", "approval_policy"}),
    ("monitoring", "Monitoring in place", {"monitoring", "monitoring_snapshot", "drift"}),
    ("environmental", "Environmental impact", {"environmental", "environmental_assessment"}),
)

TIER_TO_IMPACT = {"low": "low", "medium": "medium", "high": "high", "critical": "high"}
PROVEN_CLASSES = {"measured", "tool_estimated"}


def _provenance(record: Dict[str, Any]) -> str:
    meta = record.get("metadata") or {}
    return str(meta.get("provenance_class") or meta.get("provenance") or "manual").lower()


STALE_AFTER_CADENCES = 1.5  # a snapshot older than this many cadences no longer proves monitoring


def _record_time(record: Dict[str, Any]) -> Optional[datetime]:
    raw = record.get("timestamp") or record.get("createdAt") or record.get("created_at")
    if isinstance(raw, datetime):
        parsed = raw
    else:
        try:
            parsed = datetime.fromisoformat(str(raw))
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


_NO_TIME = datetime.min.replace(tzinfo=timezone.utc)


def _span(hours: float) -> str:
    """"12 days" or "30 hours": whole days once a span passes two days."""
    if hours >= 48:
        n = int(hours // 24)
        return f"{n} day{'s' if n != 1 else ''}"
    n = int(hours)
    return f"{n} hour{'s' if n != 1 else ''}"


def release_gate(
    risk_tier: str,
    evidence: List[Dict[str, Any]],
    *,
    environmental_assessed: bool = False,
    monitoring_cadence_hours: Optional[int] = None,
    now: Optional[datetime] = None,
    approval_status: str = "not_requested",
    last_decision: Optional[str] = None,
) -> Dict[str, Any]:
    """Verdict, confidence and the state of each check from the evidence on file.

    Each check reads its newest record (the higher confidence breaks a tie): proven
    when that record is measured or tool-estimated with confidence at or above
    0.70, attested when it is anything else, open when nothing is on file. The
    verdict comes from the impact-by-confidence matrix; a measured fairness failure
    never lets a system through as a plain go. A rejected release decision makes it
    no go, and ``last_decision`` (the newest decided request) keeps a rejection
    standing while a newer request waits for a reviewer.

    With ``monitoring_cadence_hours`` the monitoring check is proven only while
    the newest qualifying snapshot is within 1.5 cadences old; past that it is open.
    """
    checks: List[Dict[str, Any]] = []
    reasons: List[str] = []
    for key, label, types in GATE_CHECKS:
        matching = [r for r in evidence if str(r.get("evidenceType") or r.get("type") or "").lower() in types]
        if key == "environmental" and environmental_assessed and not matching:
            matching = [{"evidenceType": "environmental", "confidence": 0.85, "metadata": {"provenance_class": "tool_estimated"}}]
        state, confidence, evidence_id, detail = "open", 0.0, None, None
        stale_for = None
        if key == "monitoring" and monitoring_cadence_hours:
            times = [t for r in matching if _provenance(r) in PROVEN_CLASSES and float(r.get("confidence") or 0.0) >= 0.70 for t in [_record_time(r)] if t]
            if times:
                age_hours = ((now or datetime.now(timezone.utc)) - max(times)).total_seconds() / 3600
                if age_hours > STALE_AFTER_CADENCES * monitoring_cadence_hours:
                    stale_for = age_hours
                    reasons.append(f"Latest monitoring snapshot is {_span(age_hours)} old; the cadence is {_span(monitoring_cadence_hours)}")
        if matching and stale_for is None:
            record = max(matching, key=lambda r: (_record_time(r) or _NO_TIME, float(r.get("confidence") or 0.0)))
            prov = _provenance(record)
            confidence = cap_confidence_for_provenance(float(record.get("confidence") or 0.0), prov if prov in PROVEN_CLASSES else "manual")
            state = "proven" if prov in PROVEN_CLASSES and confidence >= 0.70 else "attested"
            evidence_id = record.get("id")
            content = record.get("content") or {}
            if key in ("fairness", "monitoring") and prov in PROVEN_CLASSES and isinstance(content, dict):
                detail = {"all_checks_pass": content.get("all_checks_pass"), "rows": content.get("rows"), "attributes": [a.get("attribute") for a in content.get("attributes", [])]}
                if content.get("all_checks_pass") is False:
                    reasons.append("Measured fairness checks fail on at least one attribute" if key == "fairness" else "Latest monitoring snapshot shows drift or disparity outside thresholds")
        checks.append({"key": key, "label": label, "state": state, "confidence": round(confidence, 2), "evidenceId": evidence_id, "detail": detail, **({"stale": True} if stale_for is not None else {})})

    overall = round(sum(c["confidence"] for c in checks) / len(checks), 2) if checks else 0.0
    verdict = get_recommendation(TIER_TO_IMPACT.get(str(risk_tier).lower(), "high"), overall)
    if reasons and verdict == "go":
        verdict = "conditional_go"
    if approval_status == "rejected" or last_decision == "rejected":
        verdict = "no_go"
        reasons.insert(0, "The last release decision was rejected; it stands until a reviewer approves a new request")
    open_checks = [c["label"] for c in checks if c["state"] == "open"]
    missing = [c["label"] for c in checks if c["state"] == "open" and not c.get("stale")]
    if missing:
        reasons.append(f"Nothing on file for: {', '.join(missing)}")
    return {
        "verdict": verdict,
        "confidence": overall,
        "band": band_from_score(overall),
        "checks": checks,
        "reasons": reasons,
        "proven": sum(1 for c in checks if c["state"] == "proven"),
        "attested": sum(1 for c in checks if c["state"] == "attested"),
        "open": len(open_checks),
        "approvalStatus": approval_status,
    }


# ---------------------------------------------------------------------------
# Gate explanation: the tier the verdict used, its matrix row, and the honest path to the next verdict
# ---------------------------------------------------------------------------

TIERS = ("low", "medium", "high", "critical")
VERDICTS = ("no_go", "conditional_go", "go")
VERDICT_LABELS = {"no_go": "No go", "conditional_go": "Conditional go", "go": "Go"}
BANDS = (("measured", MEASURED_THRESHOLD, None), ("estimated", ESTIMATED_THRESHOLD, MEASURED_THRESHOLD), ("unknown", 0.0, ESTIMATED_THRESHOLD))


def effective_tier(risk_tier: str, applicability: Optional[Dict[str, Any]]) -> str:
    """The tier the verdict is computed on: the suggested tier while a lower confirmed one awaits a second
    person, else the stored tier, with anything outside the four FairMind tiers read as high (as the gate does).
    Never looser than the stored tier: system metadata is client-writable at create, so a stale or forged
    applicability record can only tighten the gate."""
    app = applicability or {}
    tier = str(risk_tier or "").strip().lower()
    tier = tier if tier in TIERS else "high"
    suggested = app.get("suggestedTier")
    if app.get("tierBelowSuggestion") and not app.get("overrideAcceptedBy") and suggested in TIERS and TIERS.index(suggested) > TIERS.index(tier):
        return suggested
    return tier


def tier_reasons(risk_tier: str, applicability: Optional[Dict[str, Any]]) -> List[str]:
    """Gate reasons about the tier itself. They explain; they never change the verdict."""
    if not applicability:
        return [f"Risk tier {risk_tier} was not confirmed by a person"]
    if not applicability.get("tierBelowSuggestion"):
        return []
    suggested, accepted = applicability.get("suggestedTier"), applicability.get("overrideAcceptedBy")
    tail = f"{accepted} accepted the change" if accepted else f"the gate uses {suggested} until another person accepts the change"
    return [f"Risk tier {risk_tier} is below the suggested {suggested}; {tail}"]


def gate_explain(risk_tier: str, applicability: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The tier, impact and decision-matrix row behind the verdict. Row bands run from ``from`` up to, not including, ``to``."""
    stored = str(risk_tier or "").strip().lower()
    tier = effective_tier(risk_tier, applicability)
    impact = TIER_TO_IMPACT[tier]
    app = applicability or {}
    notes: List[str] = []
    if app.get("tierBelowSuggestion"):
        lowered = f"Tier lowered to {stored} by {app.get('confirmedBy')}: {str(app.get('reason') or '').strip().rstrip('.')}."
        accepted = app.get("overrideAcceptedBy")
        notes.append(f"{lowered} {accepted} accepted the change." if accepted else f"{lowered} The gate keeps using the suggested {app.get('suggestedTier')} until another person accepts the change.")
    elif stored not in TIERS:
        notes.append(f"Stored tier '{risk_tier}' is not a FairMind tier, so the gate reads it as high.")
    if tier == "critical":
        notes.append("Critical is read as high by the gate.")
    source = None
    if applicability:
        source = {
            "suggestedTier": app.get("suggestedTier"), "ruleIds": [r.get("id") for r in app.get("tierRules") or []],
            "confirmedBy": app.get("confirmedBy"), "confirmedAt": app.get("confirmedAt"),
            "tierBelowSuggestion": bool(app.get("tierBelowSuggestion")), "overrideAcceptedBy": app.get("overrideAcceptedBy"),
        }
    return {
        "tier": risk_tier, "effectiveTier": tier, "impact": impact, "tierNote": " ".join(notes) or None, "tierSource": source,
        "perCheck": round(1 / len(GATE_CHECKS), 2),
        "row": [{"band": band, "from": low, "to": high, "verdict": DECISION_MATRIX[(impact, band)]} for band, low, high in BANDS],
    }


# What FairMind can record today for each check, and the confidence its route gives. Environmental is never
# attested here: an environmental attestation shadows any later assessment in release_gate.
CHECK_ACTIONS = {
    "fairness": ("fairness_run",),
    "data_governance": ("evidence_upload", "attest"),
    "human_oversight": ("evidence_upload", "attest"),
    "monitoring": ("monitoring_snapshot", "attest"),
    "environmental": ("environmental_assessment",),
}
ACTION_CLASS = {"fairness_run": "measured", "monitoring_snapshot": "measured", "environmental_assessment": "tool_estimated", "attest": "manual", "evidence_upload": "manual"}
UPLOAD_CONFIDENCE = cap_confidence_for_provenance(1.0, "manual")  # the cap release_gate puts on an uploaded document
ACTION_NOTES = {
    "environmental_assessment": "also required before anyone can approve",
    "monitoring_snapshot": "needs shadow or live decisions",
    "evidence_upload": f"an uploaded document; counts {UPLOAD_CONFIDENCE:.2f} at most",
}
_CLASS_ORDER = {"measured": 0, "tool_estimated": 1, "manual": 2}
_CHECK_ORDER = {key: i for i, (key, _, _) in enumerate(GATE_CHECKS)}


def _synthetic(check: str, action: str, now: datetime) -> Optional[Dict[str, Any]]:
    """The record an action would add, stamped now so release_gate reads it as the newest. An assessment adds none: the gate counts it through ``environmental_assessed``."""
    if action == "environmental_assessment":
        return None
    confidence, provenance = {"fairness_run": (0.85, "measured"), "monitoring_snapshot": (0.85, "measured"), "attest": (ATTESTATION_CONFIDENCE, "manual"), "evidence_upload": (1.0, "manual")}[action]
    evidence_type = "fairness_test" if check == "fairness" else check
    return {"id": None, "evidenceType": evidence_type, "confidence": confidence, "metadata": {"provenance_class": provenance}, "timestamp": now.isoformat(), "content": {}}


def path_forward(
    risk_tier: str,
    evidence: List[Dict[str, Any]],
    *,
    environmental_assessed: bool = False,
    monitoring_cadence_hours: Optional[int] = None,
    lifecycle_stage: Optional[str] = None,
    approval_blockers: Iterable[Dict[str, Any]] = (),
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """The fewest, strongest steps to the next verdict, each priced by re-running the real release_gate.

    Read on evidence alone, as the reviewer deciding a request reads it. At most one action per check, and an
    action is kept only when it alone raises its check: a proven check gets none, an attested one gets no
    attestation. ``approval_blockers`` are the approval route's other checks as {key, text, met}; an
    environmental assessment step meets ``environmental_assessment``.
    """
    now = now or datetime.now(timezone.utc)

    def run(steps: tuple) -> Dict[str, Any]:
        extra = [r for r in (_synthetic(check, action, now) for check, action in steps) if r]
        assessed = environmental_assessed or any(action == "environmental_assessment" for _, action in steps)
        return release_gate(risk_tier, evidence + extra, environmental_assessed=assessed, monitoring_cadence_hours=monitoring_cadence_hours, now=now)

    base = run(())
    current = {c["key"]: c for c in base["checks"]}
    impact = TIER_TO_IMPACT.get(str(risk_tier).lower(), "high")
    best = max(VERDICTS.index(DECISION_MATRIX[(impact, band)]) for band, _, _ in BANDS)
    rank = VERDICTS.index(base["verdict"])
    target = VERDICTS[rank + 1] if rank < best else None
    monitored = lifecycle_stage == "operate" or any(
        str(r.get("evidenceType") or r.get("type") or "").lower() == "monitoring" and _provenance(r) in PROVEN_CLASSES for r in evidence
    )

    counts: Dict[tuple, float] = {}
    choices = []
    for key, _, _ in GATE_CHECKS:
        check = current[key]
        if check["state"] == "proven":
            continue
        for action in CHECK_ACTIONS[key]:
            if (action == "attest" and check["state"] != "open") or (action == "monitoring_snapshot" and not monitored):
                continue
            after = next(c["confidence"] for c in run(((key, action),))["checks"] if c["key"] == key)
            if after > check["confidence"]:
                counts[(key, action)] = after
        actions = [step for step in counts if step[0] == key]
        if actions:
            choices.append([None, *actions])

    # ponytail: brute force over subsets (at most 2*3*3*3*2 = 108), greedy if actions grow past ~12
    results = [(steps, run(steps)) for combo in itertools.product(*choices) for steps in [tuple(s for s in combo if s)] if steps]
    top = max(results, key=lambda r: (VERDICTS.index(r[1]["verdict"]), r[1]["confidence"]), default=((), base))[1]
    blockers = [{"key": "verdict", "text": "The release gate verdict is conditional go or better", "met": base["verdict"] != "no_go"}, *approval_blockers]

    def ready(steps: tuple, gate: Dict[str, Any]) -> bool:
        assessed = any(action == "environmental_assessment" for _, action in steps)
        return all(
            gate["verdict"] != "no_go" if b["key"] == "verdict" else b["met"] or (assessed and b["key"] == "environmental_assessment")
            for b in blockers
        )

    def option(kind: str, steps: tuple, gate: Dict[str, Any]) -> Dict[str, Any]:
        ordered = sorted(steps, key=lambda s: (_CLASS_ORDER[ACTION_CLASS[s[1]]], _CHECK_ORDER[s[0]]))
        return {
            "kind": kind,
            "steps": [
                {"check": key, "action": action, "evidenceClass": ACTION_CLASS[action], "counts": counts[(key, action)],
                 "gain": round((counts[(key, action)] - current[key]["confidence"]) / len(GATE_CHECKS), 2), "note": ACTION_NOTES.get(action)}
                for key, action in ordered
            ],
            "confidenceAfter": gate["confidence"], "verdictAfter": gate["verdict"], "approvalReady": ready(steps, gate),
        }

    # Every candidate reaches the target, the next verdict up, so rank by fewest manual steps, then fewest steps,
    # then the route a reviewer could approve (an environmental assessment beats a monitoring snapshot at a tie).
    reaching = [r for r in results if target and VERDICTS.index(r[1]["verdict"]) >= VERDICTS.index(target)]
    rank_key = lambda r: (sum(ACTION_CLASS[a] == "manual" for _, a in r[0]), len(r[0]), not ready(*r), -r[1]["confidence"], sorted(_CHECK_ORDER[k] for k, _ in r[0]))  # noqa: E731
    options = []
    if reaching:
        first = min(reaching, key=rank_key)
        options.append(option("measured_first", *first))
        attested = [r for r in reaching if all(a == "attest" for _, a in r[0])]
        alt = min(attested, key=rank_key) if attested else None
        if alt and alt[0] != first[0]:
            options.append(option("attestations", *alt))

    notes: List[str] = []
    if best < VERDICTS.index("go"):
        notes.append("Medium, high and critical systems never get a plain go; the best is conditional go, approved with written conditions.")
    if impact == "low" and base["confidence"] == 0.0:
        notes.append("With nothing on file confidence is 0, which is always no go.")
    if target and not reaching:
        need = min(low for band, low, _ in BANDS if VERDICTS.index(DECISION_MATRIX[(impact, band)]) >= VERDICTS.index(target))
        if target == "go" and any((c.get("detail") or {}).get("all_checks_pass") is False for c in top["checks"]):
            notes.append("Go is not reachable while a measured check fails; it needs a passing re-run.")
        elif top["confidence"] < need:
            # Each manual-only check with the most it can count: an upload (0.40) or, for monitoring, an attestation (0.30).
            manual = [
                f"{label.lower()} ({max((v for (k, _), v in counts.items() if k == key), default=current[key]['confidence']):.2f} at most)"
                for key, label, _ in GATE_CHECKS
                if current[key]["state"] != "proven" and not any(k == key and ACTION_CLASS[a] != "manual" for k, a in counts)
            ]
            named = " and ".join([", ".join(manual[:-1]), manual[-1]] if len(manual) > 1 else manual).capitalize()
            why = f" {named} {'has' if len(manual) == 1 else 'have'} no measured route today." if manual else ""
            notes.append(f"{VERDICT_LABELS[target]} needs confidence {need:.2f}; the most FairMind can record today reaches {top['confidence']:.2f}.{why}")
    return {
        "target": target, "options": options, "ceiling": {"confidence": top["confidence"], "verdict": top["verdict"]},
        "notes": notes, "approvalBlockers": blockers,
    }

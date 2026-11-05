"""First verdict: a predictions CSV in, measured fairness evidence and a release gate out.

Pure functions over bytes and dicts; the router owns persistence. Metrics come
from ``fairness_library.metrics`` (bootstrap intervals and permutation tests),
which until now was never reachable from any route.
"""

from __future__ import annotations

import io
import json
import math
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
from src.domain.environmental.confidence import band_from_score, cap_confidence_for_provenance
from src.domain.environmental.decision_matrix import get_recommendation

MAX_ROWS = 100_000  # ponytail: synchronous run; move to a job past this
MIN_GROUP_SIZE = 30

OUTCOME_HINTS = ("y_true", "label", "outcome", "target", "actual", "ground_truth", "truth", "repaid", "defaulted", "default", "churned", "hired", "readmitted", "fraud", "claim_paid")
PREDICTION_HINTS = ("y_pred", "prediction", "pred", "decision", "predicted", "approved", "selected")
SCORE_HINTS = ("score", "proba", "probability", "p_", "prob", "risk_score", "likelihood")
ATTRIBUTE_HINTS = (
    "gender", "sex", "age", "age_band", "age_group", "caste", "religion", "region", "state", "district",
    "language", "race", "ethnicity", "disability", "nationality", "marital", "urban_rural", "tier",
)

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


def inspect_csv(data: bytes) -> Dict[str, Any]:
    """Columns, a few sample values each, and a suggested mapping to confirm."""
    frame = _read_csv(data)
    columns = [str(c) for c in frame.columns]
    binary_like = [c for c in columns if frame[c].dropna().nunique() <= 2]
    numeric_unit = [
        c for c in columns
        if pd.api.types.is_numeric_dtype(frame[c]) and frame[c].dropna().between(0, 1).all() and frame[c].dropna().nunique() > 2
    ]
    low_card = [c for c in columns if 2 <= frame[c].dropna().nunique() <= 12 and c not in binary_like]
    outcome = _match(binary_like, OUTCOME_HINTS) or _match(columns, OUTCOME_HINTS)
    prediction = _match([c for c in binary_like if c != outcome], PREDICTION_HINTS) or _match(columns, PREDICTION_HINTS)
    if outcome is None:
        # No recognisable name: the first 0/1 column that is not the prediction is the best guess to confirm.
        outcome = next((c for c in binary_like if c != prediction), None)
    score = _match(numeric_unit, SCORE_HINTS) or _match(columns, SCORE_HINTS)
    attributes = [c for c in columns if c not in (outcome, prediction, score) and _match([c], ATTRIBUTE_HINTS)]
    if not attributes:
        attributes = [c for c in low_card if c not in (outcome, prediction, score)][:3]
    return {
        "rows": int(len(frame)),
        "columns": [
            {
                "name": c,
                "dtype": str(frame[c].dtype),
                "distinct": int(frame[c].dropna().nunique()),
                "sample": [str(v) for v in frame[c].dropna().unique()[:5]],
            }
            for c in columns
        ],
        "suggested": {"outcome": outcome, "prediction": prediction, "score": score, "attributes": attributes},
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
) -> Dict[str, Any]:
    """Verdict, confidence and the state of each check from the evidence on file.

    A check is proven when measured or tool-estimated evidence with confidence
    at or above 0.70 backs it, attested when any other evidence does, open when
    nothing does; within each, the newest record counts. The verdict comes from
    the impact-by-confidence matrix; a measured fairness failure never lets a
    system through as a plain go, and a rejected release decision makes it no go.

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
        newest_first = sorted(matching, key=lambda r: (_record_time(r) or _NO_TIME, float(r.get("confidence") or 0.0)), reverse=True)
        for record in ([] if stale_for is not None else newest_first):
            prov = _provenance(record)
            conf = cap_confidence_for_provenance(float(record.get("confidence") or 0.0), prov if prov in PROVEN_CLASSES else "manual")
            if prov in PROVEN_CLASSES and conf >= 0.70:
                state, confidence, evidence_id = "proven", conf, record.get("id")
                content = record.get("content") or {}
                if key in ("fairness", "monitoring") and isinstance(content, dict):
                    detail = {"all_checks_pass": content.get("all_checks_pass"), "rows": content.get("rows"), "attributes": [a.get("attribute") for a in content.get("attributes", [])]}
                    if content.get("all_checks_pass") is False:
                        reasons.append("Measured fairness checks fail on at least one attribute" if key == "fairness" else "Latest monitoring snapshot shows drift or disparity outside thresholds")
                break
            if state == "open":
                state, confidence, evidence_id = "attested", conf, record.get("id")
        checks.append({"key": key, "label": label, "state": state, "confidence": round(confidence, 2), "evidenceId": evidence_id, "detail": detail, **({"stale": True} if stale_for is not None else {})})

    overall = round(sum(c["confidence"] for c in checks) / len(checks), 2) if checks else 0.0
    verdict = get_recommendation(TIER_TO_IMPACT.get(str(risk_tier).lower(), "high"), overall)
    if reasons and verdict == "go":
        verdict = "conditional_go"
    if approval_status == "rejected":
        verdict = "no_go"
        reasons.insert(0, "The release decision was rejected; request a new one once its reasons are addressed")
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

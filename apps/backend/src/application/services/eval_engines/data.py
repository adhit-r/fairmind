"""Engines that read datasets: drift, representativeness, completeness, duplicates, personal data, poisoning, labels."""

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse, stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, result, split

EPS = 1e-4
MIN_ROWS = 20


def _is_text(series: pd.Series) -> bool:
    values = series.dropna().astype(str)
    return series.dtype == object and len(values) > 0 and (values.str.len().mean() > 30 or values.nunique() > 0.5 * len(values) > 50)


def _psi(expected: np.ndarray, actual: np.ndarray) -> float:
    e = np.clip(expected / max(expected.sum(), 1), EPS, None)
    a = np.clip(actual / max(actual.sum(), 1), EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def _feature_drift(ref: pd.Series, cur: pd.Series) -> Dict[str, Any]:
    if pd.api.types.is_numeric_dtype(ref) and pd.api.types.is_numeric_dtype(cur):
        r, c = ref.dropna().to_numpy(float), cur.dropna().to_numpy(float)
        edges = np.unique(np.quantile(r, np.linspace(0, 1, 11)))
        edges = np.concatenate(([-np.inf], edges[1:-1], [np.inf])) if len(edges) > 2 else np.array([-np.inf, np.median(r), np.inf])
        ks = stats.ks_2samp(r, c)
        return {"type": "numeric", "psi": _psi(np.histogram(r, edges)[0], np.histogram(c, edges)[0]),
                "ks": float(ks.statistic), "pValue": float(ks.pvalue)}
    r, c = ref.astype(str).fillna(""), cur.astype(str).fillna("")
    cats = sorted(set(r) | set(c))
    return {"type": "categorical", "psi": _psi(r.value_counts().reindex(cats, fill_value=0).to_numpy(float),
                                               c.value_counts().reindex(cats, fill_value=0).to_numpy(float)), "ks": None, "pValue": None}


def _matrix(ref: pd.DataFrame, cur: pd.DataFrame, features: List[str]):
    both = pd.concat([ref[features], cur[features]], ignore_index=True)
    parts = []
    for f in features:
        col = both[f]
        if pd.api.types.is_numeric_dtype(col):
            v = col.astype(float).fillna(col.astype(float).median())
            sd = v.std() or 1.0
            parts.append(sparse.csr_matrix(((v - v.mean()) / sd).to_numpy()[:, None]))
        elif _is_text(col):
            parts.append(TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=1).fit_transform(col.fillna("").astype(str)))
        else:
            top = col.astype(str).value_counts().index[:50]
            parts.append(sparse.csr_matrix(pd.get_dummies(col.astype(str).where(col.astype(str).isin(top), "other")).to_numpy(float)))
    return sparse.hstack(parts).tocsr()


def _sample_scores(ref: pd.DataFrame, cur: pd.DataFrame, features: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """Density ratio p_ref(x) / p_cur(x) per current row, from a classifier that tells the two sets apart.

    Probabilities are out-of-fold, so no row is scored by a model that saw it. A ratio near 1 means
    the row looks like the reference; near 0 means the reference has nothing like it.
    """
    X = _matrix(ref, cur, features)
    y = np.r_[np.zeros(len(ref)), np.ones(len(cur))]
    folds = StratifiedKFold(n_splits=min(5, len(ref), len(cur)), shuffle=True, random_state=0)
    p = cross_val_predict(LogisticRegression(max_iter=2000, C=1.0), X, y, cv=folds, method="predict_proba")[len(ref):, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    ratio = (1 - p) / p * (len(cur) / len(ref))
    score = np.where(ratio >= 0.5, 1.0, np.where(ratio >= 0.1, 0.5, 0.0))
    return ratio, score


def data_drift(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    ref, cur = read_csv(files["reference"], "The reference set"), read_csv(files["current"], "The current set")
    wanted = split(params.get("features"))
    skip = set(split(params.get("ignore")))
    features = wanted or [c for c in ref.columns if c in cur.columns and c not in skip]
    columns(ref, features, "The reference set")
    columns(cur, features, "The current set")
    if not features:
        raise EngineError("The two sets share no columns to compare")
    psi_limit = number(params, "psi_limit", 0.2)
    min_share = number(params, "min_in_distribution", 0.9)

    rows, tabular = [], []
    for f in features:
        if _is_text(ref[f]):
            rows.append({"kind": "feature", "feature": f, "type": "text", "psi": None, "ks": None, "pValue": None, "drifted": None})
            continue
        d = _feature_drift(ref[f], cur[f])
        d["psi"] = round(d["psi"], 4)
        rows.append({"kind": "feature", "feature": f, **d, "drifted": d["psi"] >= psi_limit})
        tabular.append(d["psi"])

    metrics: Dict[str, Any] = {"referenceRows": len(ref), "currentRows": len(cur), "features": len(features),
                               "driftedFeatures": sum(1 for r in rows if r["drifted"]), "maxPsi": round(max(tabular), 4) if tabular else None}
    if len(ref) < MIN_ROWS or len(cur) < MIN_ROWS:
        return result("insufficient", f"Each set needs at least {MIN_ROWS} rows to measure drift; got {len(ref)} and {len(cur)}.", metrics, rows)

    ratio, score = _sample_scores(ref, cur, features)
    share = float((score == 1.0).mean())
    metrics.update({"datasetDrift": round(share, 4), "samplesInDistribution": int((score == 1.0).sum()),
                    "samplesLowDensity": int((score == 0.5).sum()), "samplesOutOfDistribution": int((score == 0.0).sum())})
    worst = np.argsort(ratio)[:50]
    shown = [c for c in features if not _is_text(cur[c])][:4] + [c for c in features if _is_text(cur[c])][:1]
    rows += [{"kind": "sample", "row": int(i) + 1, "score": float(score[i]), "densityRatio": round(float(ratio[i]), 4),
              **{c: str(cur[c].iloc[i])[:120] for c in shown}} for i in worst if score[i] < 1.0]

    failed_features = [r["feature"] for r in rows if r.get("drifted")]
    if tabular:
        ok = not failed_features
        summary = (f"No feature drifted: largest PSI {metrics['maxPsi']} (limit {psi_limit})." if ok
                   else f"{len(failed_features)} of {len(tabular)} features drifted (PSI at or above {psi_limit}): {', '.join(failed_features[:6])}.")
    else:
        ok = share >= min_share
        summary = f"Only text features; judged on the share of current samples in distribution (limit {min_share})."
    summary += f" {share:.0%} of current samples are in distribution."
    return result("passed" if ok else "failed", summary, metrics, rows)


ENGINES: List[Engine] = [
    Engine(
        id="EV-DAT-01",
        method=(
            "PSI and the Kolmogorov-Smirnov statistic per tabular feature against the reference, and a per-sample "
            "density ratio from a classifier trained to tell the reference from the current set (out-of-fold). "
            "A sample scores 1.0 when its ratio is at least 0.5, 0.5 down to 0.1, and 0.0 below."
        ),
        slots=(
            Slot("reference", "Reference set", "The data the model was trained or validated on, as CSV."),
            Slot("current", "Current set", "Production or new data with the same columns, as CSV."),
        ),
        params=(
            Param("features", "Features", "Columns to compare, comma-separated. Blank compares every shared column."),
            Param("ignore", "Ignore", "Columns to leave out, such as identifiers or timestamps."),
            Param("psi_limit", "PSI limit", "A feature drifts at or above this PSI.", "number", 0.2),
            Param("min_in_distribution", "Minimum share in distribution", "Used when every feature is text.", "number", 0.9),
        ),
        run=data_drift,
    ),
]

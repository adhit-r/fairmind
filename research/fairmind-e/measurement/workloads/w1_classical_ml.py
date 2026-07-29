"""W1: classical ML training. sklearn logistic regression on synthetic tabular data.

Workload
--------
Generates a seeded synthetic binary-classification table (default 100k rows x
40 features) with ``numpy`` and trains ``sklearn.linear_model.LogisticRegression``
under k-fold cross-validation (default 5-fold) on CPU. ``repeats`` loops the
full CV cycle to stretch wall time into a range where software power trackers
sample meaningfully.

Analytic FLOP model (manual_flop method)
----------------------------------------
Logistic regression training cost is approximated by the canonical

    FLOPs ~= 2 * n_train * d * iters

per fold (one fused forward-plus-gradient pass over ``n_train`` rows of ``d``
features costs about ``2 * n_train * d`` FLOPs, executed for ``iters``
optimizer iterations), summed over folds and repeats:

    FLOPs = repeats * folds * 2 * (n_samples * (folds - 1) / folds) * n_features * max_iter

Documented simplifications: the solver (lbfgs) may converge before
``max_iter`` and performs additional line-search evaluations; both effects are
ignored, so this is a coarse estimate. That coarseness is exactly why the
result carries ``provenance_class=manual`` with high uncertainty.
"""

from __future__ import annotations

import time
from typing import Any

WORKLOAD_ID = "classical_ml_training"
CLI_ALIASES = ("w1", "w1_classical_ml")
FUNCTIONAL_UNIT = "1000_training_rows"

REAL_CONFIG: dict[str, Any] = {
    "n_samples": 100_000,
    "n_features": 40,
    "folds": 5,
    "max_iter": 200,
    "repeats": 3,
}

DRY_CONFIG: dict[str, Any] = {
    "n_samples": 1_500,
    "n_features": 8,
    "folds": 2,
    "max_iter": 25,
    "repeats": 1,
}


def availability() -> tuple[bool, str]:
    """Probe imports without raising. Returns (available, reason)."""

    try:
        import numpy  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as exc:
        return False, f"import failed: {exc}"
    return True, "numpy and scikit-learn importable"


def flop_estimate(config: dict[str, Any]) -> float:
    """Analytic FLOPs for the configured run. Pure stdlib; see module docstring."""

    n = float(config["n_samples"])
    d = float(config["n_features"])
    folds = float(config["folds"])
    iters = float(config["max_iter"])
    repeats = float(config.get("repeats", 1))
    n_train = n * (folds - 1.0) / folds
    return repeats * folds * 2.0 * n_train * d * iters


def functional_units(config: dict[str, Any]) -> float:
    return float(config["n_samples"]) / 1000.0


def run(config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Execute the workload for real. Deterministic given (config, seed)."""

    available, reason = availability()
    if not available:
        raise RuntimeError(f"workload {WORKLOAD_ID} unavailable: {reason}")

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold

    rng = np.random.default_rng(seed)
    n = int(config["n_samples"])
    d = int(config["n_features"])
    features = rng.standard_normal((n, d))
    true_weights = rng.standard_normal(d)
    logits = features @ true_weights + 0.5 * rng.standard_normal(n)
    labels = (logits > 0.0).astype(np.int64)

    folds = int(config["folds"])
    repeats = int(config.get("repeats", 1))
    max_iter = int(config["max_iter"])

    start = time.perf_counter()
    accuracies: list[float] = []
    for _ in range(repeats):
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
        for train_idx, test_idx in splitter.split(features, labels):
            model = LogisticRegression(max_iter=max_iter, solver="lbfgs")
            model.fit(features[train_idx], labels[train_idx])
            accuracies.append(float(model.score(features[test_idx], labels[test_idx])))
    duration = time.perf_counter() - start

    return {
        "duration_seconds": duration,
        "work_metrics": {
            "rows": n,
            "features": d,
            "folds": folds,
            "repeats": repeats,
            "fits": folds * repeats,
            "mean_cv_accuracy": round(sum(accuracies) / len(accuracies), 6),
        },
    }

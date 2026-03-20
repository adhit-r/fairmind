#!/usr/bin/env python3
"""
Create an actual trained sample model artifact for pilot demos.

Outputs:
- apps/backend/uploads/models/pilot_credit_lr.pkl
- apps/backend/uploads/models/pilot_credit_lr_metrics.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "uploads" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from sklearn.datasets import make_classification
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, roc_auc_score
        import joblib
    except Exception as exc:
        raise SystemExit(
            "scikit-learn and joblib are required. "
            "Install with: uv pip install scikit-learn joblib\n"
            f"Original error: {exc}"
        )

    X, y = make_classification(
        n_samples=12000,
        n_features=14,
        n_informative=8,
        n_redundant=2,
        n_classes=2,
        class_sep=1.25,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1200, random_state=42)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "algorithm": "LogisticRegression",
        "samples_train": int(X_train.shape[0]),
        "samples_test": int(X_test.shape[0]),
        "features": int(X_train.shape[1]),
        "accuracy": float(accuracy_score(y_test, pred)),
        "roc_auc": float(roc_auc_score(y_test, prob)),
        "target_name": "default_risk",
    }

    model_path = out_dir / "pilot_credit_lr.pkl"
    metrics_path = out_dir / "pilot_credit_lr_metrics.json"

    joblib.dump(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

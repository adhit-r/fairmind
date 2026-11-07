"""Atheris fuzz target for the core fairness metric computations.

Every metric is a difference between per-group rates, so for any labels,
predictions and group assignment it must be a finite number in [0, 1].

Run (Linux, Python 3.12+):
    python fuzz/fuzz_metrics.py -max_total_time=60
"""

import importlib.util
import math
import pathlib
import sys

import atheris

with atheris.instrument_imports():
    import numpy as np

    # Load metrics.py directly so the fuzz job needs only numpy, pandas,
    # scikit-learn and scipy, not the rest of fairness_library's imports.
    _path = pathlib.Path(__file__).resolve().parent.parent / "fairness_library" / "metrics.py"
    _spec = importlib.util.spec_from_file_location("fairness_metrics", _path)
    metrics = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(metrics)


def _check(name, value):
    value = float(value)
    if not (math.isfinite(value) and 0.0 <= value <= 1.0):
        raise AssertionError(f"{name} returned {value!r}, expected a number in [0, 1]")


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    n = fdp.ConsumeIntInRange(1, 200)
    n_groups = fdp.ConsumeIntInRange(1, 6)
    y_true = np.array([fdp.ConsumeIntInRange(0, 1) for _ in range(n)])
    y_pred = np.array([fdp.ConsumeIntInRange(0, 1) for _ in range(n)])
    groups = np.array([fdp.ConsumeIntInRange(0, n_groups - 1) for _ in range(n)])
    proba = np.array([fdp.ConsumeProbability() for _ in range(n)])
    n_bins = fdp.ConsumeIntInRange(1, 20)

    _check("demographic parity", metrics._compute_dp_diff(y_pred, groups))
    _check("equalized odds", metrics._compute_eo_diff(y_true, y_pred, groups))
    _check("equal opportunity", metrics._compute_eopp_diff(y_true, y_pred, groups))
    _check("calibration", metrics._compute_calibration_diff(y_true, proba, groups, n_bins))


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

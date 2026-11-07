"""W4: batch embedding. Two-layer dense encoder over a config-scaled corpus.

Workload
--------
Generates a seeded synthetic corpus (default 500k items x 384 dims) and
pushes it through a fixed two-layer encoder (``d_in`` -> ``hidden`` with tanh
-> ``d_out``, then L2 normalization) in batches of ``batch_size``. Runs on
numpy when importable, otherwise records the workload unavailable.
``batch_size`` is the knob the batching mitigation sweeps; ``repeats`` loops
the corpus to stretch wall time.

Analytic FLOP model (manual_flop method)
----------------------------------------
Both dense layers are counted at 2 FLOPs per multiply-accumulate:

    FLOPs = repeats * (2 * n_items * d_in * hidden
                       + 2 * n_items * hidden * d_out)

Documented simplifications: the tanh activation (about ``n_items * hidden``
transcendental ops) and the final normalization are omitted as lower-order
terms. Batch size does not change the analytic FLOP count; its effect shows
up only in measured duration and metered energy, which is exactly what the
batching mitigation is designed to expose.
"""

from __future__ import annotations

import time
from typing import Any

WORKLOAD_ID = "batch_embeddings"
CLI_ALIASES = ("w4", "w4_batch_embed")
FUNCTIONAL_UNIT = "10000_embeddings"

REAL_CONFIG: dict[str, Any] = {
    "n_items": 500_000,
    "d_in": 384,
    "hidden": 512,
    "d_out": 256,
    "batch_size": 1_024,
    "repeats": 5,
    "dtype": "float64",
}

DRY_CONFIG: dict[str, Any] = {
    "n_items": 4_000,
    "d_in": 48,
    "hidden": 64,
    "d_out": 32,
    "batch_size": 256,
    "repeats": 1,
    "dtype": "float64",
}


def availability() -> tuple[bool, str]:
    """Probe imports without raising. Returns (available, reason)."""

    try:
        import numpy  # noqa: F401
    except ImportError as exc:
        return False, f"import failed: {exc}"
    return True, "numpy importable"


def flop_estimate(config: dict[str, Any]) -> float:
    """Analytic FLOPs for the configured run. Pure stdlib; see module docstring."""

    n = float(config["n_items"])
    d_in = float(config["d_in"])
    hidden = float(config["hidden"])
    d_out = float(config["d_out"])
    repeats = float(config.get("repeats", 1))
    return repeats * (2.0 * n * d_in * hidden + 2.0 * n * hidden * d_out)


def functional_units(config: dict[str, Any]) -> float:
    return float(config["n_items"]) * float(config.get("repeats", 1)) / 10_000.0


def run(config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Execute the embedding sweep for real. Deterministic given (config, seed)."""

    available, reason = availability()
    if not available:
        raise RuntimeError(f"workload {WORKLOAD_ID} unavailable: {reason}")

    import numpy as np

    dtype = getattr(np, str(config.get("dtype", "float64")))
    rng = np.random.default_rng(seed)
    n_items = int(config["n_items"])
    d_in = int(config["d_in"])
    hidden = int(config["hidden"])
    d_out = int(config["d_out"])
    batch_size = int(config["batch_size"])
    repeats = int(config.get("repeats", 1))

    corpus = rng.standard_normal((n_items, d_in)).astype(dtype)
    weight_up = rng.standard_normal((d_in, hidden)).astype(dtype)
    weight_down = rng.standard_normal((hidden, d_out)).astype(dtype)

    start = time.perf_counter()
    checksum = 0.0
    embedded_count = 0
    for _ in range(repeats):
        for offset in range(0, n_items, batch_size):
            batch = corpus[offset : offset + batch_size]
            activated = np.tanh(batch @ weight_up)
            embedded = activated @ weight_down
            embedded /= np.linalg.norm(embedded, axis=1, keepdims=True)
            checksum += float(np.abs(embedded).sum())
            embedded_count += batch.shape[0]
    duration = time.perf_counter() - start

    return {
        "duration_seconds": duration,
        "work_metrics": {
            "backend": "numpy",
            "dtype": str(config.get("dtype", "float64")),
            "items": n_items,
            "batch_size": batch_size,
            "repeats": repeats,
            "embedded": embedded_count,
            "embedding_checksum": round(checksum, 6),
        },
    }

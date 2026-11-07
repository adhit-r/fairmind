"""W3: RAG inference. Batched query embedding plus top-k retrieval, real matrix math.

Workload
--------
Builds a seeded synthetic document-embedding matrix (default 200k docs x 256
dims), then embeds query batches through a dense projection (``d_in`` ->
``d_embed``), L2-normalizes, scores every query against every document with a
real matrix multiplication, and extracts top-k document ids per query.
Runs on numpy when importable, otherwise torch, otherwise records the
workload unavailable. ``dtype`` is config-controlled (``float64`` /
``float32``) so the quantization mitigation is a genuine reduced-precision
rerun. ``repeats`` loops the full query sweep to stretch wall time.

Analytic FLOP model (manual_flop method)
----------------------------------------
Two dense stages dominate; both are counted at 2 FLOPs per multiply-accumulate:

    FLOPs = repeats * (2 * n_queries * d_in * d_embed        (query projection)
                       + 2 * n_queries * n_docs * d_embed)   (similarity scores)

Documented simplifications: normalization, softmax-free scoring, and top-k
selection (comparison ops, roughly ``n_queries * n_docs``) are omitted as
lower-order terms. The synthetic document matrix is sampled directly in
embedding space, so corpus-embedding cost is intentionally out of scope here
(that cost is what W4 measures).
"""

from __future__ import annotations

import time
from typing import Any

WORKLOAD_ID = "rag_inference"
CLI_ALIASES = ("w3", "w3_rag")
FUNCTIONAL_UNIT = "1000_queries"

REAL_CONFIG: dict[str, Any] = {
    "n_docs": 200_000,
    "d_embed": 256,
    "d_in": 512,
    "n_queries": 5_000,
    "query_batch_size": 256,
    "top_k": 10,
    "repeats": 5,
    "dtype": "float64",
}

DRY_CONFIG: dict[str, Any] = {
    "n_docs": 2_000,
    "d_embed": 32,
    "d_in": 64,
    "n_queries": 128,
    "query_batch_size": 32,
    "top_k": 5,
    "repeats": 1,
    "dtype": "float64",
}


def availability() -> tuple[bool, str]:
    """Probe imports without raising. Returns (available, reason)."""

    try:
        import numpy  # noqa: F401

        return True, "numpy importable"
    except ImportError as numpy_exc:
        try:
            import torch  # noqa: F401

            return True, "torch importable (numpy missing)"
        except ImportError as torch_exc:
            return False, f"import failed: {numpy_exc}; {torch_exc}"


def flop_estimate(config: dict[str, Any]) -> float:
    """Analytic FLOPs for the configured run. Pure stdlib; see module docstring."""

    n_q = float(config["n_queries"])
    n_docs = float(config["n_docs"])
    d_in = float(config["d_in"])
    d_embed = float(config["d_embed"])
    repeats = float(config.get("repeats", 1))
    return repeats * (2.0 * n_q * d_in * d_embed + 2.0 * n_q * n_docs * d_embed)


def functional_units(config: dict[str, Any]) -> float:
    return float(config["n_queries"]) * float(config.get("repeats", 1)) / 1000.0


def _run_numpy(config: dict[str, Any], seed: int) -> dict[str, Any]:
    import numpy as np

    dtype = getattr(np, str(config.get("dtype", "float64")))
    rng = np.random.default_rng(seed)
    n_docs = int(config["n_docs"])
    d_embed = int(config["d_embed"])
    d_in = int(config["d_in"])
    n_queries = int(config["n_queries"])
    batch_size = int(config["query_batch_size"])
    top_k = int(config["top_k"])
    repeats = int(config.get("repeats", 1))

    docs = rng.standard_normal((n_docs, d_embed)).astype(dtype)
    docs /= np.linalg.norm(docs, axis=1, keepdims=True)
    projection = rng.standard_normal((d_in, d_embed)).astype(dtype)
    queries = rng.standard_normal((n_queries, d_in)).astype(dtype)

    start = time.perf_counter()
    checksum = 0.0
    retrieved = 0
    for _ in range(repeats):
        for offset in range(0, n_queries, batch_size):
            batch = queries[offset : offset + batch_size]
            embedded = batch @ projection
            embedded /= np.linalg.norm(embedded, axis=1, keepdims=True)
            scores = embedded @ docs.T
            top_idx = np.argpartition(scores, -top_k, axis=1)[:, -top_k:]
            checksum += float(np.take_along_axis(scores, top_idx, axis=1).sum())
            retrieved += top_idx.size
    duration = time.perf_counter() - start

    return {
        "duration_seconds": duration,
        "work_metrics": {
            "backend": "numpy",
            "dtype": str(config.get("dtype", "float64")),
            "docs": n_docs,
            "queries": n_queries,
            "repeats": repeats,
            "retrieved": retrieved,
            "score_checksum": round(checksum, 6),
        },
    }


def _run_torch(config: dict[str, Any], seed: int) -> dict[str, Any]:
    import torch

    torch.manual_seed(seed)
    dtype = getattr(torch, str(config.get("dtype", "float64")))
    n_docs = int(config["n_docs"])
    d_embed = int(config["d_embed"])
    d_in = int(config["d_in"])
    n_queries = int(config["n_queries"])
    batch_size = int(config["query_batch_size"])
    top_k = int(config["top_k"])
    repeats = int(config.get("repeats", 1))

    docs = torch.randn(n_docs, d_embed, dtype=dtype)
    docs = docs / docs.norm(dim=1, keepdim=True)
    projection = torch.randn(d_in, d_embed, dtype=dtype)
    queries = torch.randn(n_queries, d_in, dtype=dtype)

    start = time.perf_counter()
    checksum = 0.0
    retrieved = 0
    for _ in range(repeats):
        for offset in range(0, n_queries, batch_size):
            batch = queries[offset : offset + batch_size]
            embedded = batch @ projection
            embedded = embedded / embedded.norm(dim=1, keepdim=True)
            scores = embedded @ docs.T
            top_scores, top_idx = torch.topk(scores, top_k, dim=1)
            checksum += float(top_scores.sum())
            retrieved += int(top_idx.numel())
    duration = time.perf_counter() - start

    return {
        "duration_seconds": duration,
        "work_metrics": {
            "backend": "torch",
            "dtype": str(config.get("dtype", "float64")),
            "docs": n_docs,
            "queries": n_queries,
            "repeats": repeats,
            "retrieved": retrieved,
            "score_checksum": round(checksum, 6),
        },
    }


def run(config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Execute the retrieval sweep for real. Deterministic given (config, seed)."""

    available, reason = availability()
    if not available:
        raise RuntimeError(f"workload {WORKLOAD_ID} unavailable: {reason}")

    try:
        import numpy  # noqa: F401

        return _run_numpy(config, seed)
    except ImportError:
        return _run_torch(config, seed)

"""Evaluation engines: catalogue evaluations FairMind computes itself from files an organisation uploads.

Each engine declares the files (slots) and parameters it takes and returns a verdict
against the catalogue threshold, the metrics behind it and per-row detail. The
evaluation-runs router stores the result as measured evidence on an AI system, and
evaluation_results reads the latest run per system back onto the evaluations page.
"""

from typing import Dict, List

from .common import Engine, EngineError, Param, Slot
from . import data, model, ops

REGISTRY: Dict[str, Engine] = {}
for _module in (data, model, ops):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            raise RuntimeError(f"two engines for {_engine.id}")
        REGISTRY[_engine.id] = _engine


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["REGISTRY", "Engine", "EngineError", "Param", "Slot", "runnable"]

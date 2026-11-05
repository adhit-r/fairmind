"""Evaluation engines: catalogue evaluations FairMind computes itself, from uploaded files or by probing the live system.

Each engine declares the files (slots) and parameters it takes and returns a verdict
against the catalogue threshold, the metrics behind it and per-row detail. The
evaluation-runs router stores the result as measured evidence on an AI system, and
evaluation_results reads the latest run per system back onto the evaluations page.
"""

from typing import Dict, List

from .common import Engine, EngineError, Param, Slot
from . import behaviour, data, model, ops

REGISTRY: Dict[str, Engine] = {}
# A behaviour test for an evaluation that also has a file engine is its second way to run (live mode).
ALTERNATES: Dict[str, Engine] = {}
for _module in (data, model, ops, behaviour):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            if not (_engine.live and not REGISTRY[_engine.id].live and _engine.id not in ALTERNATES):
                raise RuntimeError(f"two engines for {_engine.id}")
            ALTERNATES[_engine.id] = _engine
        else:
            REGISTRY[_engine.id] = _engine


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["ALTERNATES", "REGISTRY", "Engine", "EngineError", "Param", "Slot", "runnable"]

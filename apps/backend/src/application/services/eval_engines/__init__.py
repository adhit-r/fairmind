"""Evaluation engines: catalogue evaluations FairMind computes itself from files an organisation uploads.

Each engine declares the files (slots) and parameters it takes (platform engines also read an
agent platform's configuration, see platform.py) and returns a verdict
against the catalogue threshold, the metrics behind it and per-row detail. The
evaluation-runs router stores the result as measured evidence on an AI system, and
evaluation_results reads the latest run per system back onto the evaluations page.
"""

from dataclasses import replace
from typing import Dict, List

from .common import Engine, EngineError, Judge, Param, Slot
from . import data, model, ops, platform

REGISTRY: Dict[str, Engine] = {}
for _module in (data, model, ops, platform):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            raise RuntimeError(f"two engines for {_engine.id}")
        REGISTRY[_engine.id] = _engine
for _id, (_check, _method, _judged) in platform.EXTENDS.items():
    REGISTRY[_id] = replace(REGISTRY[_id], platform=_check, platform_method=_method, judge=_judged)


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["REGISTRY", "Engine", "EngineError", "Judge", "Param", "Slot", "runnable"]

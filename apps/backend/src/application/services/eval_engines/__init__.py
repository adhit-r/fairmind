"""Evaluation engines: catalogue evaluations FairMind computes itself, from uploaded files or by probing the live system.

Each engine declares the files (slots) and parameters it takes (platform engines also read an
agent platform's configuration, see platform.py) and returns a verdict
against the catalogue threshold, the metrics behind it and per-row detail. The
evaluation-runs router stores the result as measured evidence on an AI system, and
evaluation_results reads the latest run per system back onto the evaluations page.
"""

from dataclasses import replace
from typing import Dict, List

from .common import Engine, EngineError, Judge, Param, Slot
from . import assess, behaviour, data, model, ops, platform, suites

REGISTRY: Dict[str, Engine] = {}
# A behaviour test for an evaluation that also has a file engine is its second way to run (live mode).
ALTERNATES: Dict[str, Engine] = {}
for _module in (data, model, ops, platform, behaviour, suites, assess):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            if not (_engine.live and not REGISTRY[_engine.id].live and _engine.id not in ALTERNATES):
                raise RuntimeError(f"two engines for {_engine.id}")
            ALTERNATES[_engine.id] = _engine
        else:
            REGISTRY[_engine.id] = _engine
for _id, (_check, _method, _judged) in platform.EXTENDS.items():
    REGISTRY[_id] = replace(REGISTRY[_id], platform=_check, platform_method=_method, judge=_judged)


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["ALTERNATES", "REGISTRY", "Engine", "EngineError", "Judge", "Param", "Slot", "runnable"]

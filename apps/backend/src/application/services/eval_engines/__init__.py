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
from . import behaviour, data, model, ops, platform

REGISTRY: Dict[str, Engine] = {}
# A behaviour test for an evaluation that also has a file engine is its second way to run (live mode).
ALTERNATES: Dict[str, Engine] = {}
for _module in (data, model, ops, platform, behaviour):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            if not (_engine.live and not REGISTRY[_engine.id].live and _engine.id not in ALTERNATES):
                raise RuntimeError(f"two engines for {_engine.id}")
            ALTERNATES[_engine.id] = _engine
        else:
            REGISTRY[_engine.id] = _engine
for _id, (_check, _method, _judged) in platform.EXTENDS.items():
    REGISTRY[_id] = replace(REGISTRY[_id], platform=_check, platform_method=_method, judge=_judged)


# Maturity L4 (validated): evaluations, engines and older-flow result rules, whose known-answer tests reproduce a
# hand-derived value and verdict. tests/test_known_answer_coverage.py keeps this equal to the evaluations the
# @known_answer tests cover; scripts/export_pack_catalogue.py writes it into the catalogue as maturity "L4".
VALIDATED = frozenset({
    "EV-AGT-01", "EV-AGT-03", "EV-AGT-04", "EV-DAT-01", "EV-DAT-02",
    "EV-DAT-03", "EV-DAT-04", "EV-DAT-05", "EV-DAT-06", "EV-DAT-07",
    "EV-DAT-08", "EV-DEV-01", "EV-DEV-02", "EV-ENV-01", "EV-FAI-01",
    "EV-FAI-02", "EV-FAI-03", "EV-FAI-04", "EV-FAI-05", "EV-FAI-06",
    "EV-FAI-07", "EV-LEG-01", "EV-MON-01", "EV-MON-03", "EV-MON-04",
    "EV-MON-05", "EV-OFF-06", "EV-OFF-08", "EV-PRV-01", "EV-PRV-02",
    "EV-PRV-03", "EV-PRV-04", "EV-RSK-01", "EV-RSK-03", "EV-SEC-01",
    "EV-SEC-02", "EV-SEC-03", "EV-SEC-04", "EV-SEC-05", "EV-SEC-06",
    "EV-SEC-07", "EV-SEC-14", "EV-SEC-16", "EV-SEC-17", "EV-SEC-18",
    "EV-SEC-19", "EV-SEC-20", "EV-SEC-21", "EV-SEC-27", "EV-SEC-28",
    "EV-SLF-01", "EV-TST-01", "EV-TST-02", "EV-TST-03", "EV-TST-04",
    "EV-TST-07", "EV-TST-08", "EV-TST-10", "EV-TST-11", "EV-USE-03",
    "EV-USE-04",
})


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["ALTERNATES", "REGISTRY", "Engine", "EngineError", "Judge", "Param", "Slot", "runnable"]

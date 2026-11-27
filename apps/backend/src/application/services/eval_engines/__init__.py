"""Evaluation engines: catalogue evaluations FairMind computes itself, from uploaded files or by probing the live system.

Each engine declares the files (slots) and parameters it takes (platform engines also read an
agent platform's configuration, see platform.py) and returns a verdict
against the catalogue threshold, the metrics behind it and per-row detail. The
evaluation-runs router stores the result as measured evidence on an AI system, and
evaluation_results reads the latest run per system back onto the evaluations page.
"""

from dataclasses import replace
from typing import Dict, List

from .common import REVIEW_DECISIONS, Engine, EngineError, Judge, Param, Slot
from . import agentic, assess, behaviour, data, model, ops, platform, suites

REGISTRY: Dict[str, Engine] = {}
# A behaviour test for an evaluation that also has a file engine is its second way to run (live mode).
ALTERNATES: Dict[str, Engine] = {}
# behaviour last: its live engines are the alternates of file engines in every other module
for _module in (data, model, ops, platform, agentic, suites, assess, behaviour):
    for _engine in _module.ENGINES:
        if _engine.id in REGISTRY:
            if not (_engine.live and not REGISTRY[_engine.id].live and _engine.id not in ALTERNATES):
                raise RuntimeError(f"two engines for {_engine.id}")
            ALTERNATES[_engine.id] = _engine
        else:
            REGISTRY[_engine.id] = _engine
for _id, (_check, _method, _judged) in platform.EXTENDS.items():
    REGISTRY[_id] = replace(REGISTRY[_id], platform=_check, platform_method=_method, judge=_judged)


# Stored with every run beside the catalogue version; raise it when an engine's verdict on the same inputs can change.
ENGINE_VERSION = "2026.11.23"

# Evaluations whose verdict a judge model reads (behaviour tests and judged platform checks). No labelled agreement
# set measures any judge yet, so the API labels each of them "judge not validated".
JUDGED = frozenset(e.id for d in (REGISTRY, ALTERNATES) for e in d.values() if e.live or e.judge or e.file_judge)

# Paths whose code differs from the engine's main one, each earning L4 on its own known-answer test.
EXTRA_PATHS = {
    "EV-DAT-01": ("text",),  # text features are judged by an in-distribution share, not PSI
    "EV-SEC-02": ("retrieved",),  # the document as retrieved content, or the labelled user-turn fallback
    "EV-SEC-03": ("conversation",), "EV-RSK-02": ("conversation",),  # multi-turn probes, as chat messages or a transcript
    **{e: ("review",) for e in REVIEW_DECISIONS},  # a run awaiting review reaches its verdict from reviews
}


def paths(evaluation_id: str, rules=()) -> frozenset:
    """The ways one evaluation can produce a verdict: file, live, platform, rule (rules: evaluation_results.RULES), review,
    generated (probes the judge model writes) and cyberseceval (the vendored benchmark)."""
    engine, alternate = REGISTRY.get(evaluation_id), ALTERNATES.get(evaluation_id)
    out = set(EXTRA_PATHS.get(evaluation_id, ()))
    if engine:
        out.add("live" if engine.live else "platform" if engine.run is None else "file")
        if engine.run is not None and engine.platform:
            out.add("platform")
    if alternate:
        out.add("live")
    if evaluation_id in rules:
        out.add("rule")
    names = {p.name for e in (engine, alternate) if e for p in e.params}
    return frozenset(out | ({"generated"} if "probe_count" in names else set()) | ({"cyberseceval"} if "probe_source" in names else set()))


# Maturity L4 (validated): evaluations whose every path (see paths) has a known-answer test reproducing a hand-derived
# value and verdict. tests/test_known_answer_coverage.py keeps this equal to the evaluations the @known_answer tests
# cover on every path; scripts/export_pack_catalogue.py writes it into the catalogue as maturity "L4".
VALIDATED = frozenset({
    "EV-AGT-01", "EV-AGT-02", "EV-AGT-03", "EV-AGT-04", "EV-DAT-02",
    "EV-DAT-03", "EV-DAT-04", "EV-DAT-05", "EV-DAT-06", "EV-DAT-07",
    "EV-DAT-08", "EV-DAT-09", "EV-DAT-10", "EV-DEV-01", "EV-DEV-02",
    "EV-DEV-03", "EV-ENV-01", "EV-FAI-01", "EV-FAI-02", "EV-FAI-03",
    "EV-FAI-04", "EV-FAI-06", "EV-FAI-07", "EV-FAI-08", "EV-INC-01",
    "EV-LEG-01", "EV-MON-01", "EV-MON-02", "EV-MON-03", "EV-MON-04",
    "EV-MON-05", "EV-OFF-01", "EV-OFF-02", "EV-OFF-03", "EV-OFF-04",
    "EV-OFF-05", "EV-OFF-06", "EV-OFF-07", "EV-OFF-08", "EV-OVS-01",
    "EV-OVS-02", "EV-OVS-03", "EV-OVS-04", "EV-OVS-05", "EV-OVS-06",
    "EV-PRV-02", "EV-PRV-03", "EV-PRV-05", "EV-REL-01", "EV-RSK-01",
    "EV-RSK-02", "EV-RSK-03", "EV-SEC-01", "EV-SEC-02", "EV-SEC-03",
    "EV-SEC-05", "EV-SEC-06", "EV-SEC-07", "EV-SEC-08", "EV-SEC-09",
    "EV-SEC-10", "EV-SEC-11", "EV-SEC-12", "EV-SEC-13", "EV-SEC-14",
    "EV-SEC-15", "EV-SEC-16", "EV-SEC-17", "EV-SEC-18", "EV-SEC-19",
    "EV-SEC-20", "EV-SEC-21", "EV-SEC-22", "EV-SEC-23", "EV-SEC-24",
    "EV-SEC-25", "EV-SEC-26", "EV-SEC-27", "EV-SEC-28", "EV-SLF-02",
    "EV-SLF-03", "EV-TRN-01", "EV-TRN-02", "EV-TST-01", "EV-TST-03",
    "EV-TST-05", "EV-TST-06", "EV-TST-07", "EV-TST-08", "EV-TST-09",
    "EV-TST-10", "EV-TST-11", "EV-USE-01", "EV-USE-02", "EV-USE-03",
    "EV-USE-04", "EV-USE-05", "EV-USE-06", "EV-USE-07", "EV-USE-08",
    "EV-USE-09",
})


def runnable() -> List[str]:
    return sorted(REGISTRY)


__all__ = ["ALTERNATES", "ENGINE_VERSION", "JUDGED", "REGISTRY", "Engine", "EngineError", "Judge", "Param", "Slot", "runnable"]

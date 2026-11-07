"""Workload registry for the FairMind-E measurement harness.

Each workload module exposes the same interface:

- ``WORKLOAD_ID``: canonical id, matching the smoke-harness workload ids so
  downstream analysis can join measurement rows with existing artifacts.
- ``CLI_ALIASES``: short names accepted by ``harness.py --workload``.
- ``FUNCTIONAL_UNIT``: functional unit string used in the CSV contract.
- ``REAL_CONFIG`` / ``DRY_CONFIG``: config-scaled parameter dictionaries.
- ``availability() -> (bool, str)``: import-guard probe; never raises.
- ``flop_estimate(config) -> float``: pure-stdlib analytic FLOP count for the
  configured run (documented formula in each module docstring).
- ``functional_units(config) -> float``: how many functional units the
  configured run covers.
- ``run(config, seed) -> dict``: executes the workload for real and returns
  ``{"duration_seconds": float, "work_metrics": {...}}``. Raises
  ``RuntimeError`` when the workload is unavailable; callers must check
  ``availability()`` first and record unavailability honestly.
"""

from __future__ import annotations

import importlib
from typing import Any

_MODULE_NAMES = (
    "w1_classical_ml",
    "w2_finetune",
    "w3_rag",
    "w4_batch_embed",
)


def load_workloads() -> dict[str, Any]:
    """Return an ordered mapping of WORKLOAD_ID to workload module."""

    modules: dict[str, Any] = {}
    for name in _MODULE_NAMES:
        module = importlib.import_module(f"{__name__}.{name}")
        modules[module.WORKLOAD_ID] = module
    return modules


def resolve_workload_ids(requested: str, modules: dict[str, Any]) -> list[str]:
    """Resolve a --workload argument (id, alias, or 'all') to workload ids."""

    if requested == "all":
        return list(modules)
    for workload_id, module in modules.items():
        if requested == workload_id or requested in module.CLI_ALIASES:
            return [workload_id]
    known: list[str] = []
    for workload_id, module in modules.items():
        known.append(workload_id)
        known.extend(module.CLI_ALIASES)
    raise ValueError(
        f"unknown workload {requested!r}; expected 'all' or one of {sorted(known)}"
    )

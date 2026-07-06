"""
ENV-1 .. ENV-9 control set + coverage checks.

These controls define what environmental evidence a governed AI system is
expected to carry. Coverage is computed against an assessment payload: each
control is ``present`` (evidence supplied), ``missing`` (applicable but absent),
or ``not_applicable`` (explicitly waived for this system/phase).

The control codes map to rows in FairMind's ``governance_framework_controls``
table under ``framework='environmental_governance'`` (see the Phase 2 seeding).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

PRESENT = "present"
MISSING = "missing"
NOT_APPLICABLE = "not_applicable"


def _has(metrics: Mapping[str, Any], *keys: str) -> bool:
    """True if any of the given metric keys is present and non-null."""
    return any(metrics.get(k) is not None for k in keys)


@dataclass(frozen=True)
class Control:
    code: str
    name: str
    governance_test: str
    # Returns True when the assessment carries evidence for this control.
    check: Callable[[Mapping[str, Any]], bool]
    # Controls that only apply to some systems (water, embodied carbon, energy
    # source) can be waived; core controls (ENV-1..6) always apply.
    optional: bool = False


def _metrics(assessment: Mapping[str, Any]) -> Mapping[str, Any]:
    m = assessment.get("metrics")
    return m if isinstance(m, Mapping) else {}


CONTROLS: tuple[Control, ...] = (
    Control(
        "ENV-1",
        "Assessment boundary",
        "System, lifecycle phase, and functional unit of the assessment are declared.",
        lambda a: bool(a.get("boundary")) and bool(a.get("lifecycle_phase")) and bool(a.get("functional_unit")),
    ),
    Control(
        "ENV-2",
        "Energy accounting",
        "Total energy consumption (kWh) is measured for the declared boundary.",
        lambda a: _has(_metrics(a), "total_kwh"),
    ),
    Control(
        "ENV-3",
        "Carbon accounting",
        "Greenhouse-gas emissions (kgCO2e) are measured for the declared boundary.",
        lambda a: _has(_metrics(a), "total_kg_co2e"),
    ),
    Control(
        "ENV-4",
        "Efficiency metric",
        "A per-functional-unit efficiency figure is reported (per 1M tokens or per 1k requests).",
        lambda a: _has(_metrics(a), "kg_co2e_per_1m_tokens", "kg_co2e_per_1k_requests"),
    ),
    Control(
        "ENV-5",
        "Evidence confidence",
        "The measurement source is disclosed and an evidence-confidence score is derived.",
        lambda a: bool(a.get("source")) and a.get("evidence_confidence") is not None,
    ),
    Control(
        "ENV-6",
        "Mitigation & approval",
        "Where a conditional_go is recommended, a dated mitigation is documented for reviewer sign-off.",
        lambda a: (a.get("recommendation") != "conditional_go") or _has_dated_mitigation(a),
    ),
    Control(
        "ENV-7",
        "Water use (WUE)",
        "Water usage effectiveness / on-site water consumption is reported.",
        lambda a: _has(_metrics(a), "wue_litres_per_kwh", "water_litres"),
        optional=True,
    ),
    Control(
        "ENV-8",
        "Embodied carbon",
        "Embodied (manufacturing) carbon of the underlying hardware is accounted for.",
        lambda a: _has(_metrics(a), "embodied_kg_co2e"),
        optional=True,
    ),
    Control(
        "ENV-9",
        "Energy source",
        "Grid carbon intensity and/or renewable-energy share of the compute region is reported.",
        lambda a: _has(_metrics(a), "carbon_intensity_gco2e_kwh", "energy_renewable_pct"),
        optional=True,
    ),
)

_CONTROLS_BY_CODE = {c.code: c for c in CONTROLS}


def _has_dated_mitigation(assessment: Mapping[str, Any]) -> bool:
    """True if at least one mitigation has both a description and a target date."""
    mitigations = assessment.get("mitigations") or []
    for m in mitigations:
        if not isinstance(m, Mapping):
            continue
        if m.get("description") and m.get("target_date"):
            return True
    return False


def get_control(code: str) -> Control:
    return _CONTROLS_BY_CODE[code]


def coverage(assessment: Mapping[str, Any]) -> dict[str, str]:
    """Return per-control coverage: present / missing / not_applicable.

    Optional controls (ENV-7/8/9) can be waived by listing their code in
    ``assessment['not_applicable_controls']``.
    """
    waived = set(assessment.get("not_applicable_controls") or [])
    result: dict[str, str] = {}
    for control in CONTROLS:
        if control.code in waived and control.optional:
            result[control.code] = NOT_APPLICABLE
        elif control.check(assessment):
            result[control.code] = PRESENT
        else:
            result[control.code] = MISSING
    return result


def coverage_rate(assessment: Mapping[str, Any]) -> float:
    """Fraction of *applicable* controls that have evidence, in [0.0, 1.0].

    Controls marked not_applicable are excluded from the denominator. Returns
    0.0 when no controls apply.
    """
    statuses = coverage(assessment)
    applicable = [s for s in statuses.values() if s != NOT_APPLICABLE]
    if not applicable:
        return 0.0
    present = sum(1 for s in applicable if s == PRESENT)
    return round(present / len(applicable), 4)

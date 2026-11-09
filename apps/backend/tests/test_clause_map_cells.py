"""Grid cells from gate checks: one state per check, and per clause the best check unless one fails. Pure; no database."""

from datetime import datetime, timezone

from src.application.services.clause_map_service import (
    cell_state,
    clause_map,
    tracked_requirements,
)
from src.application.services.fairness_run_service import release_gate

NOW = datetime(2026, 11, 7, tzinfo=timezone.utc)


def _record(kind, confidence, provenance, *, passes=None, ts="2026-11-06T00:00:00+00:00"):
    content = {} if passes is None else {"all_checks_pass": passes, "attributes": []}
    return {"id": f"{kind}-{provenance}", "evidenceType": kind, "confidence": confidence, "metadata": {"provenance_class": provenance}, "timestamp": ts, "content": content}


def _checks(evidence, **kw):
    return {c["key"]: c for c in release_gate("medium", evidence, now=NOW, **kw)["checks"]}


def test_each_check_carries_its_evidence_class_and_cell():
    checks = _checks(
        [_record("fairness_test", 0.95, "measured", passes=True), _record("human_oversight", 0.30, "manual"), _record("data_governance", 0.80, "tool_estimated")],
        environmental_assessed={"provenance_class": "tool_estimated", "confidence": 0.85},
    )
    assert [checks[k]["evidenceClass"] for k in ("fairness", "human_oversight", "data_governance", "monitoring", "environmental")] == ["measured", "manual", "tool_estimated", None, "tool_estimated"]
    assert cell_state(checks["fairness"]) == "proven"
    assert cell_state(checks["data_governance"]) == "estimated"  # tool_estimated at 0.80 is proven in the gate, estimated in the grid
    assert cell_state(checks["human_oversight"]) == "attested"
    assert cell_state(checks["monitoring"]) == "open"
    assert "fails" not in checks["fairness"] and "stale" not in checks["monitoring"]


def test_failing_and_stale_checks():
    failing = _checks([_record("fairness_test", 0.95, "measured", passes=False)])["fairness"]
    assert failing["fails"] is True and cell_state(failing) == "fails"
    stale = _checks([_record("monitoring", 0.90, "measured", passes=True, ts="2026-10-01T00:00:00+00:00")], monitoring_cadence_hours=168)["monitoring"]
    assert stale["stale"] is True and stale["state"] == "open" and stale["evidenceClass"] is None and cell_state(stale) == "stale"
    # a measured record below 0.70 is attested in the gate, but not a person's statement
    low = _checks([_record("fairness_test", 0.50, "measured", passes=True)])["fairness"]
    assert low["state"] == "attested" and cell_state(low) == "estimated"


def test_a_clause_with_one_failing_check_fails():
    # human oversight and monitoring share clauses: a proven oversight record cannot hide a failing snapshot
    gate = release_gate("medium", [_record("human_oversight", 0.90, "measured"), _record("monitoring", 0.90, "measured", passes=False)], now=NOW)
    clauses = [c for fw in clause_map(gate)["frameworks"] for c in fw["clauses"]]
    both = [c for c in clauses if {ch["check"] for ch in c["checks"]} == {"human_oversight", "monitoring"}]
    assert both and all(c["cell"] == "fails" for c in both)
    assert all(c["state"] == "proven" for c in both)  # the clause state the panel and packs read is unchanged
    oversight_only = [c for c in clauses if {ch["check"] for ch in c["checks"]} == {"human_oversight"}]
    assert oversight_only and all(c["cell"] == "proven" for c in oversight_only)
    monitoring = next(ch for c in both for ch in c["checks"] if ch["check"] == "monitoring")
    assert monitoring["fails"] is True and monitoring["evidenceClass"] == "measured"


def test_clause_cell_is_the_best_check():
    gate = release_gate("medium", [_record("human_oversight", 0.30, "manual")], now=NOW)
    clauses = [c for fw in clause_map(gate)["frameworks"] for c in fw["clauses"]]
    for c in clauses:
        cells = {ch["cell"] for ch in c["checks"]}
        assert c["cell"] == ("attested" if "attested" in cells else "open")


def test_tracked_requirements_match_the_clause_map():
    gate = release_gate("medium", [], now=NOW)
    eu = next(fw for fw in clause_map(gate, frameworks=["EUAIA"])["frameworks"])
    assert tracked_requirements("EUAIA") == [c["key"] for c in eu["clauses"]]
    assert tracked_requirements("NOPE") == []

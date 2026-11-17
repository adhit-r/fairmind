"""Grid cells from gate checks: one state per check, and per clause the best check unless one fails. Pure; no database."""

from datetime import datetime, timezone

from src.application.services.clause_map_service import (
    cell_state,
    clause_map,
    tracked_requirements,
)
from src.application.services.fairness_run_service import path_forward, release_gate

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
    assert all(c["state"] == "partial" for c in both)  # a failing check never leaves a proven clause
    oversight_only = [c for c in clauses if {ch["check"] for ch in c["checks"]} == {"human_oversight"}]
    assert oversight_only and all(c["cell"] == ("proven" if c["checks"][0]["relation"] == "Satisfies" else "partial") for c in oversight_only)
    assert all(c["cell"] == c["state"] for c in oversight_only)  # the grid cell says what the clause state says
    monitoring = next(ch for c in both for ch in c["checks"] if ch["check"] == "monitoring")
    assert monitoring["fails"] is True and monitoring["evidenceClass"] == "measured"


def test_clause_cell_is_the_best_check():
    gate = release_gate("medium", [_record("human_oversight", 0.30, "manual")], now=NOW)
    clauses = [c for fw in clause_map(gate)["frameworks"] for c in fw["clauses"]]
    for c in clauses:
        cells = {ch["cell"] for ch in c["checks"]}
        assert c["cell"] == ("attested" if "attested" in cells else "open" if cells else "none")


def test_tracked_requirements_match_the_clause_map():
    gate = release_gate("medium", [], now=NOW)
    eu = next(fw for fw in clause_map(gate, frameworks=["EUAIA"])["frameworks"])
    assert tracked_requirements("EUAIA") == [c["key"] for c in eu["clauses"]]
    assert tracked_requirements("NOPE") == []


def _evaluation(evaluation_id, status, ts="2026-11-06T00:00:00+00:00"):
    return {"id": f"{evaluation_id}-{status}", "type": "evaluation_run", "confidence": 0.0 if status == "insufficient" else 1.0, "metadata": {"provenance_class": "measured"},
            "timestamp": ts, "content": {"evaluationId": evaluation_id, "status": status}}


def test_a_catalogue_evaluation_counts_for_the_check_its_control_maps_to():
    passed = release_gate("medium", [_evaluation("EV-FAI-05", "passed")], now=NOW)
    fairness = next(c for c in passed["checks"] if c["key"] == "fairness")
    assert (fairness["state"], fairness["evidenceClass"], fairness["confidence"]) == ("proven", "measured", 1.0) and "fails" not in fairness
    # a failing run is measured but fails: never a plain go, as a failing fairness test
    failed = release_gate("low", [_evaluation("EV-FAI-05", "failed")], environmental_assessed=True, now=NOW)
    assert next(c for c in failed["checks"] if c["key"] == "fairness")["fails"] is True
    assert failed["verdict"] != "go" and any("EV-FAI-05 failed" in r for r in failed["reasons"])
    # an insufficient run measured nothing
    assert next(c for c in release_gate("medium", [_evaluation("EV-MON-01", "insufficient")], now=NOW)["checks"] if c["key"] == "monitoring")["state"] == "open"
    # the path points at the catalogue evaluation, not only a CSV fairness run
    chat = [(s["check"], s["action"]) for o in path_forward("medium", [], now=NOW, model_target=True)["options"] for s in o["steps"]]
    assert ("fairness", "evaluation_run") in chat and ("fairness", "fairness_run") not in chat
    assert path_forward("high", [], now=NOW, model_target=True)["ceiling"]["confidence"] == 0.97  # 1.0 * 4 + 0.85, no CSV run counted


def test_the_clause_map_reads_every_active_clause_by_relation_strength():
    gate = release_gate("medium", [_evaluation("EV-FAI-05", "passed"), _evaluation("EV-TST-01", "passed")], now=NOW, include_environmental=False)
    iso = clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]
    clauses = {c["control"]: c for c in iso["clauses"]}
    assert iso["counts"]["total"] == len(tracked_requirements("ISO42001")) == 65
    assert sum(iso["counts"][s] for s in ("proven", "partial", "attested", "open")) == 65
    # fairness only supports A.5.4, so the proven check makes it partial
    assert clauses["A.5.4"]["state"] == "partial"
    # a run of a control outside the gate reaches its clauses too
    assert any(ch["check"] == "EV-TST-01" for c in iso["clauses"] for ch in c["checks"])
    # environmental is out of this gate: 4.1 stays, open, reached by nothing in the gate
    assert (clauses["4.1"]["state"], clauses["4.1"]["cell"]) == ("open", "none") and clauses["4.1"]["checks"][0]["cell"] == "not in gate"
    assert clauses["5.2"]["checks"] == [] and clauses["5.2"]["state"] == "open"


def test_a_failed_or_unmeasured_run_never_proves_its_clause():
    def iso(evidence):
        gate = release_gate("medium", evidence, now=NOW, include_environmental=False)
        return {c["control"]: c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"]}

    # a failed run measured a failure: the clause stays open, so the audit names it
    clause = iso([_evaluation("EV-TST-01", "failed")])["A.6.2.4"]
    assert (clause["state"], clause["cell"]) == ("open", "fails")
    # a failing gate check reaches its clause the same way
    clause = iso([_evaluation("EV-FAI-05", "failed")])["A.5.4"]
    assert (clause["state"], clause["cell"]) == ("open", "fails")
    # a run that is not measured is attested at most, and keeps its real class
    clause = iso([{**_evaluation("EV-TST-01", "passed"), "metadata": {"provenance_class": "manual"}}])["A.6.2.4"]
    entry = next(ch for ch in clause["checks"] if ch["check"] == "EV-TST-01")
    assert (clause["state"], entry["state"], entry["evidenceClass"], entry["cell"]) == ("attested", "attested", "manual", "attested")
    assert entry["confidence"] <= 0.30


def test_a_material_change_drops_an_older_evaluation_run():
    from src.application.services.system_lifecycle_service import drop_superseded

    run = _evaluation("EV-FAI-05", "passed")
    assert drop_superseded([run], {"fairness": datetime(2026, 11, 7, tzinfo=timezone.utc)}) == []
    # any material change makes an earlier run stale, as evaluation_results reads it; a later run still counts
    assert drop_superseded([run], {"monitoring": datetime(2026, 11, 7, tzinfo=timezone.utc)}) == []
    assert drop_superseded([run], {"fairness": datetime(2026, 11, 5, tzinfo=timezone.utc)}) == [run]
    # an attestation keeps the per-check rule
    oversight = {"evidenceType": "human_oversight", "timestamp": "2026-11-06T00:00:00+00:00"}
    assert drop_superseded([oversight], {"monitoring": datetime(2026, 11, 7, tzinfo=timezone.utc)}) == [oversight]


def test_a_partial_clause_never_draws_a_proven_cell():
    # ISO 42001 has no Satisfies link to a gate control: a proven fairness run makes its clauses partial, cell included
    gate = release_gate("medium", [_evaluation("EV-FAI-05", "passed")], now=NOW, include_environmental=False)
    iso = clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]
    partial = [c for c in iso["clauses"] if c["state"] == "partial"]
    assert partial and all(c["cell"] == "partial" for c in partial)
    assert iso["counts"]["proven"] == 0 == sum(1 for c in iso["clauses"] if c["cell"] == "proven")

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


def test_a_failing_check_is_not_counted_proven():
    gate = release_gate("medium", [_evaluation("EV-FAI-05", "failed")], now=NOW)
    assert (gate["proven"], gate["failing"]) == (0, 1)
    # a newer manual attestation is the selected record while the older failure stands: failing, not attested too
    gate = release_gate("medium", [_evaluation("EV-FAI-05", "failed"), _record("fairness_test", 0.3, "manual", ts="2026-11-06T12:00:00+00:00")], now=NOW)
    assert (gate["attested"], gate["failing"]) == (0, 1)
    assert gate["proven"] + gate["attested"] + gate["failing"] + gate["open"] == len(gate["checks"])


def test_a_failing_test_outweighs_an_attestation_of_the_same_control():
    # EV-SEC-03 fails on FMC-AGT-02 while a done workflow attests that control: A.6.2.4 stays open
    gate = {**release_gate("medium", [_evaluation("EV-SEC-03", "failed")], now=NOW, include_environmental=False),
            "attestedControls": {"FMC-AGT-02": {"statement": "Red teaming: completed", "confidence": 0.3}}}
    clause = next(c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"] if c["control"] == "A.6.2.4")
    assert clause["state"] == "open" and {ch["check"] for ch in clause["checks"]} >= {"EV-SEC-03", "FMC-AGT-02"}


def test_an_evaluation_proves_only_the_clauses_it_tests():
    # EV-FAI-08 is an accessibility scan: its control satisfies impact-assessment clauses it does not test
    gate = release_gate("medium", [_evaluation("EV-FAI-08", "passed")], now=NOW, include_environmental=False)
    clauses = {c["control"]: c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"]}
    assert clauses["6.1.4"]["state"] == "partial"
    assert next(ch for ch in clauses["6.1.4"]["checks"] if ch["check"] == "EV-FAI-08")["relation"] == "Supports"
    # a clause it does test keeps its link: EV-TST-01 tests A.6.2.4
    gate = release_gate("medium", [_evaluation("EV-TST-01", "passed")], now=NOW, include_environmental=False)
    clause = next(c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"] if c["control"] == "A.6.2.4")
    assert next(ch for ch in clause["checks"] if ch["check"] == "EV-TST-01")["relation"] == "Satisfies"


def test_attested_controls_reach_clauses_no_gate_check_does():
    gate = {**release_gate("medium", [], now=NOW, include_environmental=False),
            "attestedControls": {"FMC-GOV-02": {"statement": "AI policy approved", "confidence": 0.3}, "FMC-FAI-01": {"statement": "skipped: a gate control"}}}
    clauses = {c["control"]: c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"]}
    assert (clauses["5.2"]["state"], clauses["5.2"]["cell"]) == ("attested", "attested")
    assert not any(ch["check"] == "FMC-FAI-01" for c in clauses.values() for ch in c["checks"])


def test_a_direct_test_link_moves_its_clause_to_partial_and_a_satisfies_link_proves():
    def iso(evidence):
        gate = release_gate("medium", evidence, now=NOW, include_environmental=False)
        return {c["control"]: c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"]}

    # EV-DAT-01 names A.6.2.6 directly; its common control does not reach it
    clause = iso([_evaluation("EV-DAT-01", "passed")])["A.6.2.6"]
    assert clause["state"] == "partial" and [ch["relation"] for ch in clause["checks"] if ch["check"] == "EV-DAT-01"] == ["Tests"]
    # a Satisfies link proves only a clause the evaluation also tests: EV-TST-01 tests A.6.2.4, EV-OFF-08 does not
    assert iso([_evaluation("EV-TST-01", "passed")])["A.6.2.4"]["state"] == "proven"
    assert iso([_evaluation("EV-OFF-08", "passed")])["A.6.2.4"]["state"] == "partial"
    # a fairness evaluation counts in the gate check and also through its own links
    gate = release_gate("medium", [_evaluation("EV-FAI-05", "passed")], now=NOW, include_environmental=False)
    nist = {c["control"]: c for c in clause_map(gate, frameworks=["NISTRMF"])["frameworks"][0]["clauses"]}
    assert any(ch["check"] == "EV-FAI-05" for ch in nist["MEASURE 2.11"]["checks"])


def test_one_rule_for_the_clause_map_journeys_and_the_evaluation_catalogue():
    from src.api.routers import pack_catalogue as pc
    from src.application.services.clause_map_service import evaluation_links

    for eid in pc.EVALUATIONS:
        gate = release_gate("medium", [_evaluation(eid, "passed")], now=NOW, include_environmental=False)
        reached = {c["key"] for fw in clause_map(gate)["frameworks"] for c in fw["clauses"] if any(ch["check"] == eid for ch in c["checks"])}
        assert reached == set(evaluation_links(eid)) == set(pc.EVALUATION_LINKS[eid]) == pc._C.tests[eid], eid
        assert all(eid in [e for e, _ in pc.REQUIREMENT_EVALUATIONS[k]] for k in reached), eid


def test_a_failing_csv_fairness_run_still_counts_after_a_later_passing_evaluation():
    csv = _record("fairness_test", 0.95, "measured", passes=False, ts="2026-11-05T00:00:00+00:00")
    gate = release_gate("low", [csv, _evaluation("EV-FAI-05", "passed")], environmental_assessed=True, now=NOW)
    fairness = next(c for c in gate["checks"] if c["key"] == "fairness")
    assert fairness["fails"] is True and gate["verdict"] != "go"
    # a newer passing CSV run clears it
    fixed = _record("fairness_test", 0.95, "measured", passes=True, ts="2026-11-06T12:00:00+00:00")
    assert "fails" not in next(c for c in release_gate("low", [csv, fixed, _evaluation("EV-FAI-05", "passed")], now=NOW)["checks"] if c["key"] == "fairness")


def test_accepted_mappings_and_control_assessments_reach_their_clauses():
    def iso(**extra):
        gate = {**release_gate("medium", [], now=NOW, include_environmental=False), **extra}
        fw = clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]
        return fw, {c["control"]: c for c in fw["clauses"]}

    mapped = lambda key, ev: {"clause": key, "evaluationId": ev, "evidenceId": f"e-{ev}", "state": "proven", "evidenceClass": "measured", "confidence": 1.0, "label": ev}  # noqa: E731
    # an accepted mapping proves only a clause its evaluation tests: EV-TST-01 tests A.6.2.4, EV-DAT-01 does not
    _, clauses = iso(mappedEvidence=[mapped("ISO42001|A.6.2.4", "EV-TST-01"), mapped("ISO42001|A.6.2.3", "EV-DAT-01")])
    assert (clauses["A.6.2.4"]["state"], clauses["A.6.2.4"]["cell"]) == ("proven", "proven")
    assert clauses["A.6.2.3"]["state"] == "partial"
    row = lambda applicability, status="not_started", justification=None: {"applicability": applicability, "status": status, "justification": justification, "confidence": 0.3}  # noqa: E731
    fw, clauses = iso(controlAssessments={
        "ISO42001|A.10.4": [row("not_applicable", justification="No customers use the system.")],
        "ISO42001|A.10.3": [row("not_applicable")],  # no justification: not excluded
        "ISO42001|A.10.2": [row("applicable", "accepted")],
    })
    assert (clauses["A.10.4"]["state"], clauses["A.10.4"]["cell"], clauses["A.10.4"]["justification"]) == ("excluded", "excluded", "No customers use the system.")
    assert clauses["A.10.3"]["state"] == "open" and clauses["A.10.2"]["state"] == "attested"
    assert fw["counts"]["excluded"] == 1 and sum(fw["counts"][s] for s in ("proven", "partial", "attested", "excluded", "open")) == fw["counts"]["total"]


def test_an_accepted_mapping_is_only_as_strong_as_its_evaluation_path_and_a_failure_is_never_excluded():
    from src.application.services.clause_map_service import statement_of_applicability

    # EV-DAT-03 tests A.7.4 but its control only partially satisfies it: an accepted mapping cannot prove it
    m = {"clause": "ISO42001|A.7.4", "evaluationId": "EV-DAT-03", "evidenceId": "e1", "state": "proven", "evidenceClass": "measured", "confidence": 1.0, "label": "EV-DAT-03"}
    gate = {**release_gate("medium", [_record("monitoring", 0.90, "measured", passes=False)], now=NOW, include_environmental=False), "mappedEvidence": [m]}
    failing = next(c for c in clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]["clauses"] if c["cell"] == "fails")
    note = "=HYPERLINK(\"http://x\",\"see\")"
    gate["controlAssessments"] = {failing["key"]: [{"applicability": "not_applicable", "status": "not_started", "justification": note, "confidence": 0.3}]}
    fw = clause_map(gate, frameworks=["ISO42001"])["frameworks"][0]
    clauses = {c["key"]: c for c in fw["clauses"]}
    assert clauses["ISO42001|A.7.4"]["state"] == "partial"
    # a failing measured result outweighs a not-applicable statement
    row = clauses[failing["key"]]
    assert row["cell"] == "fails" and row["state"] != "excluded" and row["applicability"] == "not_applicable"
    # free text cannot run as a spreadsheet formula in the Statement of Applicability
    assert "'" + note.replace('"', '""') in statement_of_applicability(fw)

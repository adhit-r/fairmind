"""Which catalogue runs prove a gate check: the newest decides, a failure stands behind a run that proves nothing,
and passes on loosened thresholds or over a year old prove nothing."""

from datetime import datetime, timedelta, timezone

from src.application.services.evaluation_results import _rollup
from src.application.services.fairness_run_service import _synthetic, release_gate

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)


def _run(status, days_ago, **content):
    record = _synthetic("monitoring", "evaluation_run", NOW - timedelta(days=days_ago))
    record["content"].update(status=status, **content)
    return record


def _check(*records):
    gate = release_gate("low", list(records), now=NOW)
    return next(c for c in gate["checks"] if c["key"] == "monitoring")


def test_a_newer_insufficient_run_replaces_an_older_pass():
    assert _check(_run("passed", 2))["state"] == "proven"
    assert _check(_run("passed", 2), _run("insufficient", 1))["state"] == "open"


def test_a_failure_stands_behind_a_newer_run_that_proves_nothing():
    assert _check(_run("failed", 3), _run("insufficient", 1)).get("fails")
    loosened = {"thresholdLoosened": [{"param": "max_rate", "value": 100.0, "catalogue": None}]}
    assert _check(_run("failed", 3), _run("passed", 1, **loosened)).get("fails")
    assert _check(_run("passed", 1, **loosened))["state"] == "open"
    assert not _check(_run("failed", 3), _run("passed", 1)).get("fails")


def test_a_pass_over_a_year_old_is_stale():
    assert _check(_run("passed", 364))["state"] == "proven"
    assert _check(_run("passed", 366))["state"] == "open"


def test_the_rollup_passes_only_when_every_system_passed():
    systems = [{"status": "passed", "at": "b"}, {"status": "insufficient", "at": "a"}]
    out = _rollup(systems)
    assert out["status"] == "insufficient" and out["counts"] == {"passed": 1, "failed": 0, "insufficient": 1}
    assert _rollup(systems[:1])["status"] == "passed" and _rollup([])["status"] == "not_run"


def test_sample_size_floors_loosen_when_raised_and_baseline_direction_follows_the_engine():
    from api.routes.evaluation_runs import _engine, _loosened

    def loose(evaluation_id, **params):
        return [x["param"] for x in _loosened(_engine(evaluation_id), params)]

    assert loose("EV-TST-10", min_rows=1000) == ["min_rows"] and loose("EV-TST-10", min_rows=5) == []
    assert loose("EV-FAI-03", min_slice=1000) == ["min_slice"] and loose("EV-FAI-03", min_slice=5) == []
    assert loose("EV-FAI-05", baseline=0) == [] and loose("EV-FAI-05", baseline=5) == ["baseline"]
    assert loose("EV-TST-01", baseline=0, task="regression") == [] and loose("EV-TST-01", baseline=0) == ["baseline"]
    assert loose("EV-TST-05", baseline=0) == ["baseline"]


def test_the_system_file_counts_a_gate_check_only_where_the_gate_does():
    from api.routes.ai_governance import _missing_gate_evidence

    def _run(status, days_ago, **content):  # against the real clock, which the system file reads
        record = _synthetic("monitoring", "evaluation_run", datetime.now(timezone.utc) - timedelta(days=days_ago))
        record["content"].update(status=status, **content)
        return record

    loosened = {"thresholdLoosened": [{"param": "max_rate", "value": 100.0, "catalogue": None}]}
    assert "monitoring evidence" not in _missing_gate_evidence([_run("passed", 2)])
    assert "monitoring evidence" in _missing_gate_evidence([_run("passed", 2, **loosened)])
    assert "monitoring evidence" in _missing_gate_evidence([_run("passed", 400)])
    assert "monitoring evidence" in _missing_gate_evidence([_run("passed", 2), _run("insufficient", 1)])

"""Repository boundary tests for database-authoritative freshness rows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
)
from src.infrastructure.db.repositories import evaluation_workbench_repository as repository
from tests.test_evaluation_workbench_repository import (
    ORG,
    _create_active_plan_and_run,
    _service,
    repository_fixture,
)
from tests.test_evidence_review_repository import _admitted_scope


UTC = timezone.utc
AS_OF = datetime(2026, 8, 13, 12, tzinfo=UTC)


def _row(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "classification_status": "ok",
        "freshness_contract_version": "1.0.0",
        "recorded_freshness_status": "current",
        "effective_freshness_status": "current",
        "evaluated_at": AS_OF,
        "effective_at": datetime(2026, 8, 13, 11, tzinfo=UTC),
        "expiring_at": datetime(2026, 8, 13, 13, tzinfo=UTC),
        "reason_codes_json": "[]",
        "decision_eligible": True,
    }
    value.update(changes)
    return value


def test_repository_parses_the_exact_nine_column_classifier_contract() -> None:
    classification = repository._parse_evidence_freshness_classification(
        _row(),
        expected_recorded_status="current",
    )

    assert classification.classification_status == "ok"
    assert classification.freshness_contract_version == "1.0.0"
    assert classification.recorded_freshness_status == "current"
    assert classification.effective_freshness_status == "current"
    assert classification.evaluated_at == datetime(2026, 8, 13, 12, tzinfo=UTC)
    assert classification.effective_at == datetime(2026, 8, 13, 11, tzinfo=UTC)
    assert classification.expiring_at == datetime(2026, 8, 13, 13, tzinfo=UTC)
    assert classification.reason_codes == ()
    assert classification.decision_eligible is True


@pytest.mark.parametrize(
    "row",
    (
        {key: value for key, value in _row().items() if key != "effective_at"},
        {**_row(), "unexpected": "value"},
        _row(
            classification_status="integrity_error",
            recorded_freshness_status=None,
            effective_freshness_status=None,
            effective_at=None,
            expiring_at=None,
            reason_codes_json='["authority_integrity_error"]',
            decision_eligible=None,
        ),
        _row(recorded_freshness_status="stale"),
        _row(reason_codes_json="not-json"),
        _row(reason_codes_json="{}"),
        _row(reason_codes_json='["evidence_expiring","evidence_expiring"]'),
        _row(reason_codes_json='["unknown_reason"]'),
        _row(
            effective_freshness_status="stale",
            reason_codes_json='["issuer_revoked","recorded_stale"]',
            decision_eligible=False,
        ),
        _row(evaluated_at=datetime(2026, 8, 13, 12)),
        _row(decision_eligible=1),
    ),
)
def test_repository_rejects_malformed_or_integrity_classifier_rows(
    row: dict[str, object],
) -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        repository._parse_evidence_freshness_classification(
            row,
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


def _current_classification(
    *,
    as_of: datetime,
    recorded_freshness_status: str,
) -> EvidenceFreshnessClassification:
    return EvidenceFreshnessClassification(
        classification_status="ok",
        freshness_contract_version="1.0.0",
        recorded_freshness_status=recorded_freshness_status,
        effective_freshness_status="current",
        evaluated_at=as_of,
        effective_at=as_of - timedelta(minutes=1),
        expiring_at=as_of + timedelta(minutes=1),
        reason_codes=(),
        decision_eligible=False,
    )


def test_list_reads_all_linked_runs_at_one_database_evaluation_instant(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    first = _admitted_scope(session, run_key="freshness-list-first")
    second = _admitted_scope(
        session,
        seed_authority=False,
        run_key="freshness-list-second",
    )
    adapter = SqlAlchemyEvaluationWorkbenchRepository(session)
    clock_calls = 0
    classifications: list[dict[str, object]] = []

    def db_now() -> datetime:
        nonlocal clock_calls
        clock_calls += 1
        return AS_OF

    def classify(**kwargs: object) -> EvidenceFreshnessClassification:
        classifications.append(kwargs)
        return _current_classification(
            as_of=kwargs["as_of"],
            recorded_freshness_status=kwargs["recorded_freshness_status"],
        )

    monkeypatch.setattr(
        adapter,
        "_acquire_operational_freshness_read_lock",
        lambda *, organization_id: None,
    )
    monkeypatch.setattr(adapter, "read_fresh_utc_now", db_now)
    monkeypatch.setattr(adapter, "_classify_evidence_freshness", classify)

    records = adapter.list_run_records(org_id=ORG, system_id="system-a")

    assert records is not None
    assert clock_calls == 1
    assert {item["run_id"] for item in classifications} == {
        first.run_id,
        second.run_id,
    }
    assert {item["as_of"] for item in classifications} == {AS_OF}
    assert all(
        execution.operational_freshness is not None
        and execution.operational_freshness.evaluated_at == AS_OF
        for record in records
        for execution in record.suite_executions
    )


def test_linked_list_acquires_one_org_lock_before_clock_and_classification(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    _admitted_scope(session, run_key="freshness-locked-list-first")
    _admitted_scope(
        session,
        seed_authority=False,
        run_key="freshness-locked-list-second",
    )
    adapter = SqlAlchemyEvaluationWorkbenchRepository(session)
    events: list[str] = []

    def lock(*, organization_id: str) -> None:
        assert organization_id == ORG
        events.append("lock")

    def db_now() -> datetime:
        events.append("clock")
        return AS_OF

    def classify(**kwargs: object) -> EvidenceFreshnessClassification:
        events.append("classify")
        return _current_classification(
            as_of=kwargs["as_of"],
            recorded_freshness_status=kwargs["recorded_freshness_status"],
        )

    monkeypatch.setattr(
        adapter,
        "_acquire_operational_freshness_read_lock",
        lock,
        raising=False,
    )
    monkeypatch.setattr(adapter, "read_fresh_utc_now", db_now)
    monkeypatch.setattr(adapter, "_classify_evidence_freshness", classify)

    records = adapter.list_run_records(org_id=ORG, system_id="system-a")

    assert records is not None
    assert events == ["lock", "clock", "classify", "classify"]


def test_linked_detail_acquires_one_org_lock_before_clock_and_classification(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session, run_key="freshness-locked-detail")
    adapter = SqlAlchemyEvaluationWorkbenchRepository(session)
    events: list[str] = []

    def lock(*, organization_id: str) -> None:
        assert organization_id == ORG
        events.append("lock")

    def db_now() -> datetime:
        events.append("clock")
        return AS_OF

    def classify(**kwargs: object) -> EvidenceFreshnessClassification:
        events.append("classify")
        return _current_classification(
            as_of=kwargs["as_of"],
            recorded_freshness_status=kwargs["recorded_freshness_status"],
        )

    monkeypatch.setattr(
        adapter,
        "_acquire_operational_freshness_read_lock",
        lock,
        raising=False,
    )
    monkeypatch.setattr(adapter, "read_fresh_utc_now", db_now)
    monkeypatch.setattr(adapter, "_classify_evidence_freshness", classify)

    record = adapter.get_run_record(
        org_id=ORG,
        system_id="system-a",
        run_id=scope.run_id,
    )

    assert record is not None
    assert events == ["lock", "clock", "classify"]


def test_unlinked_list_does_not_sample_or_fabricate_operational_freshness(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    _create_active_plan_and_run(_service(session), run_key="freshness-unlinked")
    adapter = SqlAlchemyEvaluationWorkbenchRepository(session)

    def unexpected() -> datetime:
        raise AssertionError("unlinked reads must not sample the freshness clock")

    monkeypatch.setattr(adapter, "read_fresh_utc_now", unexpected)

    records = adapter.list_run_records(org_id=ORG, system_id="system-a")

    assert records is not None
    assert all(
        execution.operational_freshness is None
        for record in records
        for execution in record.suite_executions
    )


def test_linked_sqlite_read_fails_closed_when_authoritative_classifier_is_unavailable(
    repository_fixture,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session, run_key="freshness-sqlite-linked")
    adapter = SqlAlchemyEvaluationWorkbenchRepository(session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        adapter.get_run_record(
            org_id=ORG,
            system_id="system-a",
            run_id=scope.run_id,
        )

    assert caught.value.code == "operational_freshness_postgresql_required"

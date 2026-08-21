"""Repository boundary tests for unsigned imported evidence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
)
from tests.test_evidence_admission_repository import _postgres_database_error


def test_imported_evidence_authority_fails_closed_on_sqlite_before_any_scope_read() -> None:
    """Unsigned imports are not a SQLite test-harness mutation capability."""

    with Session(create_engine("sqlite://")) as session:
        repository = SqlAlchemyEvaluationWorkbenchRepository(session)
        with pytest.raises(EvaluationWorkbenchError) as caught:
            repository.load_imported_evidence_authority_for_update(
                scope=EvidenceAdmissionScope(
                    organization_id="org-a",
                    system_id="system-a",
                    run_id="run-a",
                    suite_execution_id="suite-execution-a",
                )
            )

    assert caught.value.code == "imported_evidence_postgresql_required"
    assert caught.value.status_code == 409


def test_013i_delivery_guard_is_a_bounded_integrity_conflict() -> None:
    error = _postgres_database_error(
        sqlstate="23514",
        message=(
            "unverified evidence delivery binding failed\n"
            "CONTEXT: PL/pgSQL function fairmind_unverified_import_delivery_is_valid_013i()"
        ),
        integrity=True,
    )

    with Session(create_engine("sqlite://")) as session:
        repository = SqlAlchemyEvaluationWorkbenchRepository(session)
        with pytest.raises(EvaluationWorkbenchError) as caught:
            repository._raise_evidence_database_error(error)

    assert caught.value.code == "evidence_admission_integrity_conflict"
    assert caught.value.status_code == 409

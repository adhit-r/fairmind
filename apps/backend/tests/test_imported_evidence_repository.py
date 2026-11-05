"""Repository boundary tests for unsigned imported evidence."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
)
from tests import pg
from tests.test_evidence_admission_repository import _postgres_database_error


def test_013i_delivery_guard_is_a_bounded_integrity_conflict() -> None:
    error = _postgres_database_error(
        sqlstate="23514",
        message=(
            "unverified evidence delivery binding failed\n"
            "CONTEXT: PL/pgSQL function fairmind_unverified_import_delivery_is_valid_013i()"
        ),
        integrity=True,
    )

    with Session(pg.fresh_engine()) as session:
        repository = SqlAlchemyEvaluationWorkbenchRepository(session)
        with pytest.raises(EvaluationWorkbenchError) as caught:
            repository._raise_evidence_database_error(error)

    assert caught.value.code == "evidence_admission_integrity_conflict"
    assert caught.value.status_code == 409

"""Direct database contract for owner-decision override integrity 013j."""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from threading import Event, Thread

import pytest

from migrations import owner_decision_override_integrity_migration as migration_013j
from migrations.owner_decision_override_integrity_migration import (
    apply_sqlite as apply_013j,
    sql_for,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
POSTGRES_CHAIN_THROUGH_013I = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "010_environmental_governance.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
    "013d_evaluator_catalog.sql",
    "013e_environmental_tenant_scope.sql",
    "013f_trust_authority_integrity.sql",
    "013g_operational_evidence_freshness.sql",
    "013h_idempotency_retention_integrity.sql",
    "013i_imported_evidence_delivery_integrity.sql",
)
SQLITE_REVIEW_TRIGGER = "governance_evidence_reviews_separation_guard_013j"
SQLITE_DECISION_TRIGGER = (
    "governance_evaluation_decisions_owner_override_unavailable_013j"
)


def _minimal_sqlite() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE governance_evaluation_runs (
            id TEXT PRIMARY KEY, org_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
            system_id TEXT NOT NULL, requested_by TEXT NOT NULL
        );
        CREATE TABLE governance_evidence_admissions (
            id TEXT PRIMARY KEY, contract_version TEXT NOT NULL,
            run_id TEXT NOT NULL, suite_execution_id TEXT NOT NULL,
            evidence_run_id TEXT NOT NULL, passport_revision_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL, system_id TEXT NOT NULL, org_id TEXT NOT NULL,
            submitted_by TEXT NOT NULL
        );
        CREATE TABLE governance_evaluation_suite_evidence_links (
            id TEXT PRIMARY KEY, admission_id TEXT NOT NULL,
            admission_contract_version TEXT NOT NULL, run_id TEXT NOT NULL,
            suite_execution_id TEXT NOT NULL, evidence_run_id TEXT NOT NULL,
            passport_revision_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
            system_id TEXT NOT NULL, org_id TEXT NOT NULL, linked_by TEXT NOT NULL
        );
        CREATE TABLE governance_evidence_reviews (
            id TEXT PRIMARY KEY, admission_id TEXT NOT NULL,
            admission_contract_version TEXT NOT NULL, run_id TEXT NOT NULL,
            suite_execution_id TEXT NOT NULL, evidence_run_id TEXT NOT NULL,
            passport_revision_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
            system_id TEXT NOT NULL, org_id TEXT NOT NULL, reviewed_by TEXT NOT NULL,
            separation_override_reason TEXT
        );
        CREATE TABLE governance_evaluation_decisions (
            id TEXT PRIMARY KEY, owner_override_reason TEXT
        );
        INSERT INTO governance_evaluation_runs
            VALUES ('run-a', 'org-a', 'workspace-a', 'system-a', 'requester-a');
        INSERT INTO governance_evidence_admissions VALUES (
            'admission-a', '2.0.0', 'run-a', 'execution-a', 'evidence-a',
            'revision-a', 'workspace-a', 'system-a', 'org-a', 'submitter-a'
        );
        INSERT INTO governance_evaluation_suite_evidence_links VALUES (
            'link-a', 'admission-a', '2.0.0', 'run-a', 'execution-a',
            'evidence-a', 'revision-a', 'workspace-a', 'system-a', 'org-a',
            'linker-a'
        );
        """
    )
    return connection


def _insert_review(
    connection: sqlite3.Connection,
    *,
    reviewer: str,
    separation_override_reason: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO governance_evidence_reviews VALUES (
            'review-a', 'admission-a', '2.0.0', 'run-a', 'execution-a',
            'evidence-a', 'revision-a', 'workspace-a', 'system-a', 'org-a', ?, ?
        )
        """,
        (reviewer, separation_override_reason),
    )


def test_013j_artifacts_and_loader_contract() -> None:
    assert (MIGRATIONS / "013j_owner_decision_override_integrity.sql").is_file()
    assert (
        MIGRATIONS / "fixtures" / "013j_owner_decision_override_integrity.sqlite.sql"
    ).is_file()
    assert "fairmind_owner_decision_override_authorized_013j" in sql_for("postgresql")
    assert SQLITE_REVIEW_TRIGGER in sql_for("sqlite")
    assert SQLITE_DECISION_TRIGGER in sql_for("sqlite")
    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("mysql")


def test_sqlite_013j_loader_requires_foreign_keys_and_is_idempotent() -> None:
    disabled = _minimal_sqlite()
    disabled.execute("PRAGMA foreign_keys = OFF")
    with pytest.raises(RuntimeError, match="foreign key enforcement"):
        apply_013j(disabled)

    connection = _minimal_sqlite()
    apply_013j(connection)
    apply_013j(connection)
    installed = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert {SQLITE_REVIEW_TRIGGER, SQLITE_DECISION_TRIGGER} <= installed


def test_sqlite_013j_loader_rolls_back_partial_trigger_installation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken_payload = sql_for("sqlite").replace(
        f"DROP TRIGGER IF EXISTS {SQLITE_DECISION_TRIGGER};",
        "THIS IS NOT VALID SQLITE;\n"
        f"DROP TRIGGER IF EXISTS {SQLITE_DECISION_TRIGGER};",
    )
    broken_path = tmp_path / "broken_013j.sqlite.sql"
    broken_path.write_text(broken_payload, encoding="utf-8")
    monkeypatch.setattr(migration_013j, "_SQLITE_PATH", broken_path)

    connection = _minimal_sqlite()
    with pytest.raises(sqlite3.OperationalError, match="near \"THIS\""):
        migration_013j.apply_sqlite(connection)

    installed = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert SQLITE_REVIEW_TRIGGER not in installed
    assert SQLITE_DECISION_TRIGGER not in installed


def test_sqlite_013j_rejects_every_review_override_reason() -> None:
    connection = _minimal_sqlite()
    apply_013j(connection)
    with pytest.raises(sqlite3.IntegrityError, match="review separation failed"):
        _insert_review(
            connection,
            reviewer="independent-reviewer",
            separation_override_reason="forbidden",
        )


@pytest.mark.parametrize("reviewer", ("submitter-a", "linker-a", "requester-a"))
def test_sqlite_013j_enforces_all_review_relationships(reviewer: str) -> None:
    connection = _minimal_sqlite()
    apply_013j(connection)
    with pytest.raises(sqlite3.IntegrityError, match="review separation failed"):
        _insert_review(connection, reviewer=reviewer)


def test_sqlite_013j_allows_independent_review_and_rejects_decision_override() -> None:
    connection = _minimal_sqlite()
    apply_013j(connection)
    _insert_review(connection, reviewer="independent-reviewer")
    with pytest.raises(
        sqlite3.IntegrityError,
        match="owner decision override requires PostgreSQL",
    ):
        connection.execute(
            "INSERT INTO governance_evaluation_decisions VALUES ('decision-a', 'why')"
        )


@pytest.fixture
def postgresql_013j_connection():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013j_{uuid.uuid4().hex}"
    try:
        assert connection.server_version // 10000 == 14
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cursor.execute(
                sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                    sql.Identifier(schema)
                )
            )
            for migration in POSTGRES_CHAIN_THROUGH_013I:
                cursor.execute(
                    "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                    (schema,),
                )
                cursor.execute((MIGRATIONS / migration).read_text(encoding="utf-8"))
            cursor.execute(
                (MIGRATIONS / "013j_owner_decision_override_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
        connection.commit()
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
                cursor.execute(
                    "SELECT pg_catalog.to_regnamespace(%s) IS NULL",
                    (schema,),
                )
                assert cursor.fetchone()[0] is True
        finally:
            cleanup.close()


def _seed_owner_authority(connection) -> tuple[str, str]:
    org_id = str(uuid.uuid4())
    actor_id = f"owner-{uuid.uuid4().hex}"
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, email, username, password_hash, role, permissions) "
            "VALUES (%s, %s, %s, 'test-only', 'admin', '[]'::jsonb)",
            (actor_id, f"{actor_id}@example.test", actor_id),
        )
        cursor.execute(
            "INSERT INTO organizations (id, name, slug, owner_id, is_active) "
            "VALUES (%s, 'Owner authority', %s, %s, true)",
            (org_id, org_id, actor_id),
        )
        cursor.execute(
            "INSERT INTO org_members (id, org_id, user_id, role, status) "
            "VALUES (%s, %s, %s, 'owner', 'active')",
            (str(uuid.uuid4()), org_id, actor_id),
        )
        cursor.execute(
            "INSERT INTO org_roles "
            "(id, org_id, name, permissions, is_system_role) VALUES "
            "(%s, %s, 'owner', %s::jsonb, true)",
            (
                str(uuid.uuid4()),
                org_id,
                '["evaluation:decision","evaluation:separation:override"]',
            ),
        )
    connection.commit()
    return org_id, actor_id


def _authorized(connection, org_id: str, actor_id: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT fairmind_owner_decision_override_authorized_013j(%s, %s)",
            (org_id, actor_id),
        )
        return cursor.fetchone()[0] is True


def test_postgresql14_013j_authorizes_only_exact_system_owner_role(
    postgresql_013j_connection,
) -> None:
    connection = postgresql_013j_connection
    org_id, actor_id = _seed_owner_authority(connection)
    assert _authorized(connection, org_id, actor_id)
    assert not _authorized(connection, org_id, "wrong-owner")

    mutations = (
        ("UPDATE organizations SET is_active=false WHERE id=%s", (org_id,)),
        ("UPDATE org_members SET status='inactive' WHERE org_id=%s", (org_id,)),
        ("UPDATE org_members SET role='admin' WHERE org_id=%s", (org_id,)),
        ("UPDATE org_roles SET is_system_role=false WHERE org_id=%s", (org_id,)),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            ('["evaluation:decision"]', org_id),
        ),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            ('["evaluation:separation:override"]', org_id),
        ),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            ('["evaluation:decision","evaluation:decision",'
             '"evaluation:separation:override"]', org_id),
        ),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            ('["Bad Permission","evaluation:decision",'
             '"evaluation:separation:override"]', org_id),
        ),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            (
                json.dumps(
                    ["evaluation:decision", "evaluation:separation:override"]
                    + [f"scope:item-{index}" for index in range(63)]
                ),
                org_id,
            ),
        ),
        (
            "UPDATE org_roles SET permissions=%s::jsonb WHERE org_id=%s",
            (
                json.dumps(
                    [
                        "evaluation:decision",
                        "evaluation:separation:override",
                        "scope:" + ("a" * 129),
                    ]
                ),
                org_id,
            ),
        ),
    )
    for statement, parameters in mutations:
        with connection.cursor() as cursor:
            cursor.execute("SAVEPOINT authority_case")
            cursor.execute(statement, parameters)
            assert not _authorized(connection, org_id, actor_id)
            cursor.execute("ROLLBACK TO SAVEPOINT authority_case")
    connection.rollback()


def test_postgresql14_013j_catalog_hardening(postgresql_013j_connection) -> None:
    with postgresql_013j_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT proname, proconfig, proacl IS NULL,
                   proowner = namespace.nspowner
            FROM pg_catalog.pg_proc AS procedure
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = procedure.pronamespace
            WHERE namespace.nspname = current_schema()
              AND proname LIKE '%013j'
            ORDER BY proname
            """
        )
        rows = cursor.fetchall()
    assert rows
    assert all("search_path=pg_catalog, " in next(iter(config)) for _, config, _, _ in rows)
    assert all(acl_is_null and owner_matches for _, _, acl_is_null, owner_matches in rows)


@pytest.fixture
def postgresql_013i_session_factory():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import postgres_session_factory

    chain = postgres_session_factory.__wrapped__()
    factory = next(chain)
    session = factory()
    schema = ""
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        for migration in (
            "013g_operational_evidence_freshness.sql",
            "013h_idempotency_retention_integrity.sql",
            "013i_imported_evidence_delivery_integrity.sql",
        ):
            session.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema, false)"
                ),
                {"schema": schema},
            )
            session.execute(text((MIGRATIONS / migration).read_text(encoding="utf-8")))
        session.commit()
        yield factory
    finally:
        session.close()
        try:
            next(chain)
        except StopIteration:
            pass
        _assert_schema_dropped(schema)


@pytest.fixture
def postgresql_013j_session_factory():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import postgres_session_factory

    chain = postgres_session_factory.__wrapped__()
    factory = next(chain)
    session = factory()
    schema = ""
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        for migration in (
            "013g_operational_evidence_freshness.sql",
            "013h_idempotency_retention_integrity.sql",
            "013i_imported_evidence_delivery_integrity.sql",
            "013j_owner_decision_override_integrity.sql",
        ):
            session.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema, false)"
                ),
                {"schema": schema},
            )
            session.execute(text((MIGRATIONS / migration).read_text(encoding="utf-8")))
        session.commit()
        yield factory
    finally:
        session.close()
        try:
            next(chain)
        except StopIteration:
            pass
        _assert_schema_dropped(schema)


def _assert_schema_dropped(schema: str) -> None:
    import psycopg2

    connection = psycopg2.connect(POSTGRES_URL)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_catalog.to_regnamespace(%s) IS NULL",
                (schema,),
            )
            assert cursor.fetchone()[0] is True
    finally:
        connection.close()


def _ready_graph(factory):
    from tests.test_operational_freshness_postgres import _admitted_graph, _review

    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer")
    return graph


def _insert_raw_review(
    session,
    graph,
    *,
    reviewer_sql: str,
    separation_override_reason: str | None = None,
    review_version: int = 1,
) -> None:
    from sqlalchemy import text

    session.execute(
        text(
            "INSERT INTO governance_evidence_reviews ("
            "id, org_id, system_id, evidence_run_id, passport_revision_id, "
            "admission_id, decision, rationale, reviewed_by, review_version, "
            "separation_override_reason, reviewed_at, workspace_id, run_id, "
            "suite_execution_id, admission_contract_version) "
            "SELECT :id, admission.org_id, admission.system_id, "
            "admission.evidence_run_id, admission.passport_revision_id, admission.id, "
            "'accepted', 'Direct database separation test.', "
            + reviewer_sql
            + ", :review_version, :reason, fairmind_canonical_clock_utc_013f(), "
            "admission.workspace_id, admission.run_id, admission.suite_execution_id, "
            "admission.contract_version "
            "FROM governance_evidence_admissions AS admission "
            "JOIN governance_evaluation_suite_evidence_links AS link "
            "ON link.admission_id=admission.id "
            "JOIN governance_evaluation_runs AS run ON run.id=admission.run_id "
            "WHERE admission.id=:admission_id"
        ),
        {
            "id": str(uuid.uuid4()),
            "reason": separation_override_reason,
            "review_version": review_version,
            "admission_id": graph.admission_id,
        },
    )


@pytest.mark.parametrize(
    "reviewer_sql,reason",
    (
        ("admission.submitted_by", None),
        ("link.linked_by", None),
        ("run.requested_by", None),
        ("'independent-reviewer'", "forbidden"),
    ),
)
def test_postgresql14_013j_rejects_every_review_separation_escape(
    postgresql_013j_session_factory,
    reviewer_sql: str,
    reason: str | None,
) -> None:
    from sqlalchemy.exc import IntegrityError
    from tests.test_operational_freshness_postgres import _admitted_graph

    graph = _admitted_graph(postgresql_013j_session_factory)
    session = postgresql_013j_session_factory()
    try:
        with pytest.raises(IntegrityError, match="evidence review separation failed"):
            _insert_raw_review(
                session,
                graph,
                reviewer_sql=reviewer_sql,
                separation_override_reason=reason,
            )
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize(
    "legacy_update",
    (
        "UPDATE governance_evidence_reviews AS review "
        "SET reviewed_by=admission.submitted_by "
        "FROM governance_evidence_admissions AS admission "
        "WHERE review.admission_id=admission.id "
        "AND review.admission_id=:admission_id",
        "UPDATE governance_evidence_reviews AS review "
        "SET reviewed_by=link.linked_by "
        "FROM governance_evaluation_suite_evidence_links AS link "
        "WHERE review.admission_id=link.admission_id "
        "AND review.admission_id=:admission_id",
        "UPDATE governance_evidence_reviews AS review "
        "SET reviewed_by=run.requested_by "
        "FROM governance_evaluation_runs AS run "
        "WHERE review.run_id=run.id AND review.admission_id=:admission_id",
        "UPDATE governance_evidence_reviews SET separation_override_reason='forbidden' "
        "WHERE admission_id=:admission_id",
    ),
    ids=("submitter", "linker", "requester", "reason"),
)
def test_postgresql14_013j_upgrade_preflight_rejects_legacy_conflict(
    postgresql_013j_session_factory,
    legacy_update: str,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    graph = _ready_graph(postgresql_013j_session_factory)
    session = postgresql_013j_session_factory()
    try:
        session.execute(
            text("ALTER TABLE governance_evidence_reviews DISABLE TRIGGER USER")
        )
        session.execute(
            text(
                "ALTER TABLE governance_evidence_reviews DROP CONSTRAINT "
                "ck_governance_evidence_review_no_override_013j"
            )
        )
        session.execute(
            text(legacy_update),
            {"admission_id": graph.admission_id},
        )
        session.execute(
            text("ALTER TABLE governance_evidence_reviews ENABLE TRIGGER USER")
        )
        with pytest.raises(
            DBAPIError,
            match="migration 013j found invalid review separation provenance",
        ):
            session.execute(
                text(
                    (MIGRATIONS / "013j_owner_decision_override_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
            )
    finally:
        session.rollback()
        session.close()


def test_postgresql14_013j_preflight_waits_for_inflight_legacy_review(
    postgresql_013i_session_factory,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from tests.test_operational_freshness_postgres import _admitted_graph

    factory = postgresql_013i_session_factory
    graph = _admitted_graph(factory)
    setup = factory()
    try:
        setup.execute(
            text(
                "ALTER TABLE governance_evaluation_suite_evidence_links "
                "DISABLE TRIGGER USER"
            )
        )
        setup.execute(
            text(
                "UPDATE governance_evaluation_suite_evidence_links "
                "SET linked_by='legacy-linker' WHERE admission_id=:admission_id"
            ),
            {"admission_id": graph.admission_id},
        )
        setup.execute(
            text(
                "ALTER TABLE governance_evaluation_suite_evidence_links "
                "ENABLE TRIGGER USER"
            )
        )
        setup.execute(
            text(
                "ALTER TABLE governance_evaluation_run_suite_executions "
                "DISABLE TRIGGER USER"
            )
        )
        setup.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET linked_by='legacy-linker' WHERE id=:suite_execution_id"
            ),
            {"suite_execution_id": graph.suite_execution_id},
        )
        setup.execute(
            text(
                "ALTER TABLE governance_evaluation_run_suite_executions "
                "ENABLE TRIGGER USER"
            )
        )
        setup.commit()
    finally:
        setup.close()

    writer = factory()
    migration_started = Event()
    migration_finished = Event()
    migration_pid: list[int] = []
    migration_errors: list[BaseException] = []

    def apply_migration() -> None:
        migration = factory()
        try:
            schema = migration.scalar(text("SELECT current_schema()"))
            migration.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema, false)"
                ),
                {"schema": schema},
            )
            migration.execute(text("SET application_name='013j-preflight-lock-test'"))
            migration_pid.append(migration.scalar(text("SELECT pg_backend_pid()")))
            migration_started.set()
            migration.execute(
                text(
                    (MIGRATIONS / "013j_owner_decision_override_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
            )
            migration.commit()
        except BaseException as error:
            migration_errors.append(error)
            migration.rollback()
        finally:
            migration.close()
            migration_finished.set()

    try:
        _insert_raw_review(writer, graph, reviewer_sql="link.linked_by")
        reviewed_at = writer.scalar(
            text(
                "SELECT reviewed_at FROM governance_evidence_reviews "
                "WHERE admission_id=:admission_id"
            ),
            {"admission_id": graph.admission_id},
        )
        writer.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET review_status='accepted', updated_at=:reviewed_at "
                "WHERE id=:suite_execution_id"
            ),
            {
                "reviewed_at": reviewed_at,
                "suite_execution_id": graph.suite_execution_id,
            },
        )
        thread = Thread(target=apply_migration, daemon=True)
        thread.start()
        assert migration_started.wait(timeout=5)

        observer = factory()
        try:
            deadline = time.monotonic() + 5
            waiting = False
            while time.monotonic() < deadline:
                waiting = bool(
                    observer.scalar(
                        text(
                            "SELECT wait_event_type='Lock' FROM pg_stat_activity "
                            "WHERE pid=:pid"
                        ),
                        {"pid": migration_pid[0]},
                    )
                )
                observer.rollback()
                if waiting:
                    break
            assert waiting, "013j migration did not wait on the in-flight review write"
        finally:
            observer.close()

        writer.commit()
        assert migration_finished.wait(timeout=10)
        thread.join(timeout=1)
        assert len(migration_errors) == 1
        assert isinstance(migration_errors[0], DBAPIError)
        assert "migration 013j found invalid review separation provenance" in str(
            migration_errors[0]
        )
    finally:
        writer.rollback()
        writer.close()


def test_postgresql14_013j_preserves_normal_governance_decisions(
    postgresql_013j_session_factory,
) -> None:
    from tests.test_operational_freshness_postgres import _decide

    factory = postgresql_013j_session_factory
    graph = _ready_graph(factory)
    result = _decide(factory, graph, decider_id=f"independent-decider-{uuid.uuid4()}")
    assert result["verdictVersion"] == 1


def _install_owner_role(session, graph, actor_id: str) -> None:
    from sqlalchemy import text

    session.execute(
        text(
            "UPDATE organizations SET owner_id=:actor_id, is_active=true WHERE id=:org_id"
        ),
        {"actor_id": actor_id, "org_id": graph.scenario.org_id},
    )
    session.execute(
        text(
            "UPDATE org_members SET role='owner', status='active' "
            "WHERE org_id=:org_id AND user_id=:actor_id"
        ),
        {"actor_id": actor_id, "org_id": graph.scenario.org_id},
    )
    session.execute(
        text(
            "INSERT INTO org_roles (id, org_id, name, permissions, is_system_role) "
            "VALUES (:id, :org_id, 'owner', "
            "'[\"evaluation:decision\",\"evaluation:separation:override\"]'::jsonb, true)"
        ),
        {"id": str(uuid.uuid4()), "org_id": graph.scenario.org_id},
    )


def _insert_raw_override(
    session,
    graph,
    *,
    actor_id: str,
    verdict_version: int = 1,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    system_id: str | None = None,
    run_id: str | None = None,
    admission_id: str | None = None,
) -> str:
    from sqlalchemy import text
    from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchRepository,
    )

    authority = SqlAlchemyEvaluationWorkbenchRepository(
        session
    ).load_governance_decision_authority_for_update(scope=graph.decision_scope)
    assert authority is not None
    evidence_set = authority.evidence_set.to_dict()
    if admission_id is not None:
        evidence_set["suites"][0]["admissionId"] = admission_id
    layers = {
        "suites": {graph.suite_execution_id: "conditional"},
        "modalities": {},
        "components": {},
        "riskDimensions": {},
    }
    decided_at = session.execute(
        text(
            "INSERT INTO governance_evaluation_decisions ("
            "id, org_id, workspace_id, system_id, run_id, run_contract_version, "
            "envelope_id, envelope_hash, verdict_version, overall_verdict, "
            "layer_verdicts_schema_version, layer_verdicts_json, rationale, "
            "decided_by, owner_override_reason, evidence_set_json, evidence_set_hash, "
            "decided_at) VALUES ("
            ":id, :org_id, :workspace_id, :system_id, :run_id, '2.0.0', "
            ":envelope_id, :envelope_hash, :verdict_version, 'conditional', '1.0.0', "
            ":layers, 'Documented owner conflict.', :actor_id, 'No independent owner.', "
            ":evidence_set, :evidence_set_hash, fairmind_canonical_clock_utc_013f()) "
            "RETURNING decided_at"
        ),
        {
            "id": str(uuid.uuid4()),
            "org_id": organization_id or graph.scenario.org_id,
            "workspace_id": workspace_id or graph.scenario.workspace_id,
            "system_id": system_id or graph.scenario.system_id,
            "run_id": run_id or graph.scenario.run_id,
            "envelope_id": authority.envelope_id,
            "envelope_hash": authority.envelope_hash,
            "verdict_version": verdict_version,
            "layers": canonical_json(layers),
            "actor_id": actor_id,
            "evidence_set": canonical_json(evidence_set),
            "evidence_set_hash": canonical_sha256(evidence_set),
        },
    ).scalar_one()
    session.execute(
        text(
            "UPDATE governance_evaluation_runs SET verdict_version=:verdict_version, "
            "overall_verdict='conditional', layer_verdicts_schema_version='1.0.0', "
            "layer_verdicts_json=:layers, updated_at=:decided_at "
            "WHERE id=:run_id AND verdict_version=0"
        ),
        {
            "verdict_version": verdict_version,
            "layers": canonical_json(layers),
            "decided_at": decided_at,
            "run_id": graph.scenario.run_id,
        },
    )
    return str(
        session.scalar(
            text(
                "SELECT id FROM governance_evaluation_decisions "
                "WHERE run_id=:run_id AND verdict_version=:verdict_version"
            ),
            {
                "run_id": run_id or graph.scenario.run_id,
                "verdict_version": verdict_version,
            },
        )
    )


_AUTHORITY_CASES = (
    "organization-owner",
    "organization-inactive",
    "member-inactive",
    "member-role",
    "role-non-system",
    "role-name-only",
    "permission-missing-decision",
    "permission-missing-override",
    "permissions-malformed",
    "permissions-duplicate",
    "permissions-non-string",
    "permissions-over-64",
    "organization-deleted",
    "member-deleted",
    "role-deleted",
)


def _mutate_owner_authority(session, graph, case: str) -> None:
    from sqlalchemy import text

    values = {"org_id": graph.scenario.org_id, "actor_id": graph.scenario.actor_id}
    if case == "organization-owner":
        other_actor = f"other-owner-{uuid.uuid4().hex}"
        _add_independent_member(session, graph, other_actor)
        session.execute(
            text("UPDATE organizations SET owner_id=:other WHERE id=:org_id"),
            {"other": other_actor, **values},
        )
    elif case == "organization-inactive":
        session.execute(
            text("UPDATE organizations SET is_active=false WHERE id=:org_id"),
            values,
        )
    elif case == "member-inactive":
        session.execute(
            text(
                "UPDATE org_members SET status='inactive' "
                "WHERE org_id=:org_id AND user_id=:actor_id"
            ),
            values,
        )
    elif case == "member-role":
        session.execute(
            text(
                "UPDATE org_members SET role='admin' "
                "WHERE org_id=:org_id AND user_id=:actor_id"
            ),
            values,
        )
    elif case == "role-non-system":
        session.execute(
            text(
                "UPDATE org_roles SET is_system_role=false "
                "WHERE org_id=:org_id AND name='owner'"
            ),
            values,
        )
    elif case.startswith("permission") or case == "role-name-only":
        permissions = {
            "permission-missing-decision": ["evaluation:separation:override"],
            "permission-missing-override": ["evaluation:decision"],
            "role-name-only": [],
            "permissions-malformed": {"evaluation:decision": True},
            "permissions-duplicate": [
                "evaluation:decision",
                "evaluation:decision",
                "evaluation:separation:override",
            ],
            "permissions-non-string": [
                "evaluation:decision",
                "evaluation:separation:override",
                7,
            ],
            "permissions-over-64": [
                "evaluation:decision",
                "evaluation:separation:override",
                *[f"scope:item-{index}" for index in range(63)],
            ],
        }[case]
        session.execute(
            text(
                "UPDATE org_roles SET permissions=CAST(:permissions AS jsonb) "
                "WHERE org_id=:org_id AND name='owner'"
            ),
            {"permissions": json.dumps(permissions, separators=(",", ":")), **values},
        )
    elif case == "organization-deleted":
        session.execute(text("ALTER TABLE organizations DISABLE TRIGGER ALL"))
        session.execute(text("DELETE FROM organizations WHERE id=:org_id"), values)
        session.execute(text("ALTER TABLE organizations ENABLE TRIGGER ALL"))
    elif case == "member-deleted":
        session.execute(
            text(
                "DELETE FROM org_members "
                "WHERE org_id=:org_id AND user_id=:actor_id"
            ),
            values,
        )
    elif case == "role-deleted":
        session.execute(
            text("DELETE FROM org_roles WHERE org_id=:org_id AND name='owner'"),
            values,
        )
    else:  # pragma: no cover - the parameter list is the exhaustive contract
        raise AssertionError(case)


@pytest.mark.parametrize("case", _AUTHORITY_CASES)
def test_postgresql14_013j_authority_matrix_fails_closed_for_helper_and_raw_insert(
    postgresql_013j_session_factory,
    case: str,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    factory = postgresql_013j_session_factory
    graph = _ready_graph(factory)
    setup = factory()
    try:
        _install_owner_role(setup, graph, graph.scenario.actor_id)
        setup.commit()
    finally:
        setup.close()

    session = factory()
    try:
        _mutate_owner_authority(session, graph, case)
        assert session.scalar(
            text(
                "SELECT fairmind_owner_decision_override_authorized_013j"
                "(:org_id, :actor_id)"
            ),
            {"org_id": graph.scenario.org_id, "actor_id": graph.scenario.actor_id},
        ) is False
        with pytest.raises(
            IntegrityError,
            match="owner decision override authority failed",
        ):
            _insert_raw_override(
                session,
                graph,
                actor_id=graph.scenario.actor_id,
            )
        session.rollback()
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE run_id=:run_id"
            ),
            {"run_id": graph.scenario.run_id},
        ) == 0
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND outcome='success' AND action="
                "'evaluation_v2.governance_decision.owner_override_created'"
            ),
            {"org_id": graph.scenario.org_id},
        ) == 0
    finally:
        session.rollback()
        session.close()


def test_postgresql14_013j_raw_override_requires_deferred_success_binding(
    postgresql_013j_session_factory,
) -> None:
    from sqlalchemy.exc import IntegrityError

    factory = postgresql_013j_session_factory
    graph = _ready_graph(factory)
    session = factory()
    try:
        _install_owner_role(session, graph, graph.scenario.actor_id)
        _insert_raw_override(session, graph, actor_id=graph.scenario.actor_id)
        with pytest.raises(
            IntegrityError,
            match="owner decision override audit binding failed",
        ):
            session.commit()
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize(
    ("substitution", "expected_message"),
    (
        ("organization", "evidence is not decision-eligible at database time"),
        ("workspace", "evidence is not decision-eligible at database time"),
        ("system", "evidence is not decision-eligible at database time"),
        ("run", "evidence is not decision-eligible at database time"),
        ("admission", "decision requires the exact hashed evidence set"),
    ),
)
def test_postgresql14_013j_rejects_cross_tenant_identifier_substitution(
    postgresql_013j_session_factory,
    substitution: str,
    expected_message: str,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    factory = postgresql_013j_session_factory
    first = _ready_graph(factory)
    second = _ready_graph(factory)
    setup = factory()
    try:
        _install_owner_role(setup, first, first.scenario.actor_id)
        setup.commit()
    finally:
        setup.close()

    substitutions = {
        "organization": {"organization_id": second.scenario.org_id},
        "workspace": {"workspace_id": second.scenario.workspace_id},
        "system": {"system_id": second.scenario.system_id},
        "run": {"run_id": second.scenario.run_id},
        "admission": {"admission_id": second.admission_id},
    }
    session = factory()
    try:
        with pytest.raises(DBAPIError, match=expected_message):
            _insert_raw_override(
                session,
                first,
                actor_id=first.scenario.actor_id,
                **substitutions[substitution],
            )
        session.rollback()
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE run_id IN (:first_run, :second_run)"
            ),
            {
                "first_run": first.scenario.run_id,
                "second_run": second.scenario.run_id,
            },
        ) == 0
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id IN (:first_org, :second_org) AND outcome='success' "
                "AND action="
                "'evaluation_v2.governance_decision.owner_override_created'"
            ),
            {
                "first_org": first.scenario.org_id,
                "second_org": second.scenario.org_id,
            },
        ) == 0
    finally:
        session.rollback()
        session.close()


def _insert_raw_override_binding(session, graph, *, fabrication: str | None) -> tuple[str, str]:
    from sqlalchemy import text
    from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
    from src.infrastructure.db.repositories.evaluation_audit_chain import (
        EvaluationAuditAppend,
        append_evaluation_audit_event,
    )

    actor_id = graph.scenario.actor_id
    decision_id = _insert_raw_override(session, graph, actor_id=actor_id)
    idempotency_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    bound_event_id = str(uuid.uuid4()) if fabrication == "audit-event-id" else event_id
    operation = (
        "evaluation-v2.governance-decision.fabricated"
        if fabrication == "operation"
        else "evaluation-v2.governance-decision.owner-override"
    )
    bound_actor = "fabricated-actor" if fabrication == "actor" else actor_id
    action = (
        "evaluation_v2.governance_decision.fabricated"
        if fabrication == "action"
        else "evaluation_v2.governance_decision.owner_override_created"
    )
    resource_type = (
        "fabricated_resource"
        if fabrication == "resource"
        else "evaluation_governance_decision"
    )
    resource_id = "fabricated-resource" if fabrication == "resource" else decision_id
    key_hash = "1" * 64
    request_hash = "2" * 64
    claim = (
        session.execute(
            text(
                "INSERT INTO governance_idempotency_records ("
                "id, org_id, actor_id, operation, key_hash, request_hash, status, "
                "created_at, updated_at, expires_at) VALUES ("
                ":id, :org_id, :actor_id, :operation, :key_hash, :request_hash, "
                "'in_progress', fairmind_idempotency_clock_utc_013h(), "
                "fairmind_idempotency_clock_utc_013h(), "
                "fairmind_idempotency_clock_utc_013h()) "
                "RETURNING created_at, expires_at"
            ),
            {
                "id": idempotency_id,
                "org_id": graph.scenario.org_id,
                "actor_id": bound_actor,
                "operation": operation,
                "key_hash": key_hash,
                "request_hash": request_hash,
            },
        )
        .mappings()
        .one()
    )
    relationships = [
        {
            "actorId": actor_id,
            "relationshipType": "evidence_submitter",
            "resourceIds": [
                "fabricated-admission"
                if fabrication == "waived-ids"
                else graph.admission_id
            ],
            "resourceType": "evidence_admission",
        },
        {
            "actorId": actor_id,
            "relationshipType": "run_requester",
            "resourceIds": [graph.scenario.run_id],
            "resourceType": "evaluation_run",
        },
    ]
    reason_hash = (
        "3" * 64
        if fabrication == "reason-hash"
        else canonical_sha256({"ownerOverrideReason": "No independent owner."})
    )
    details = {
        "_fairmindEvaluationSuccessBinding": {
            "schemaVersion": "1.0.0",
            "auditEventId": bound_event_id,
            "idempotencyRecordId": idempotency_id,
            "idempotencyKeyHash": key_hash,
            "operation": operation,
            "requestHash": request_hash,
            "claimedAt": claim["created_at"],
            "expiresAt": claim["expires_at"],
            "resourceType": resource_type,
            "resourceId": resource_id,
            "responseStatus": 201,
            "responseHash": "4" * 64,
            "action": action,
            "domainDetails": {
                "ownerOverride": True,
                "ownerActorId": actor_id,
                "ownerOverrideReasonHash": reason_hash,
                "waivedRelationships": relationships,
                "waivedRelationshipsHash": canonical_sha256(relationships),
            },
        }
    }
    append_evaluation_audit_event(
        session,
        event=EvaluationAuditAppend(
            organization_id=graph.scenario.org_id,
            actor_id=bound_actor,
            action=action,
            outcome="success",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            created_at=claim["created_at"],
            event_id=event_id,
        ),
    )
    response = canonical_json(
        {
            "_fairmindEvaluationMutationSucceeded": True,
            "auditEventId": bound_event_id,
            "responseBody": {
                "decisionId": decision_id,
                "ownerOverrideApplied": True,
            },
        }
    )
    session.execute(
        text(
            "UPDATE governance_idempotency_records SET status='completed', "
            "response_status=201, response_body_json=:response, "
            "resource_type=:resource_type, resource_id=:resource_id, "
            "updated_at=:updated_at WHERE id=:id"
        ),
        {
            "response": response,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "updated_at": claim["created_at"],
            "id": idempotency_id,
        },
    )
    return decision_id, event_id


@pytest.mark.parametrize(
    "fabrication",
    (
        "operation",
        "actor",
        "action",
        "resource",
        "reason-hash",
        "waived-ids",
        "audit-event-id",
    ),
)
def test_postgresql14_013j_rejects_each_fabricated_override_binding_at_commit(
    postgresql_013j_session_factory,
    fabrication: str,
) -> None:
    from sqlalchemy.exc import IntegrityError

    graph = _ready_graph(postgresql_013j_session_factory)
    session = postgresql_013j_session_factory()
    try:
        _install_owner_role(session, graph, graph.scenario.actor_id)
        _insert_raw_override_binding(session, graph, fabrication=fabrication)
        with pytest.raises(
            IntegrityError,
            match="owner decision override audit binding failed",
        ):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_postgresql14_013j_accepts_complete_binding_and_keeps_rows_append_only(
    postgresql_013j_session_factory,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    graph = _ready_graph(postgresql_013j_session_factory)
    session = postgresql_013j_session_factory()
    try:
        _install_owner_role(session, graph, graph.scenario.actor_id)
        decision_id, event_id = _insert_raw_override_binding(
            session,
            graph,
            fabrication=None,
        )
        session.commit()
        mutations = (
            (
                "UPDATE governance_evaluation_decisions SET rationale='fabricated' "
                "WHERE id=:id",
                decision_id,
            ),
            ("DELETE FROM governance_evaluation_decisions WHERE id=:id", decision_id),
            (
                "UPDATE governance_evaluation_audit_events SET action='fabricated' "
                "WHERE id=:id",
                event_id,
            ),
            ("DELETE FROM governance_evaluation_audit_events WHERE id=:id", event_id),
        )
        for statement, row_id in mutations:
            with pytest.raises(DBAPIError, match="append-only"):
                session.execute(text(statement), {"id": row_id})
            session.rollback()
    finally:
        session.rollback()
        session.close()


def test_postgresql14_013j_rejects_override_without_exact_authority_or_cas(
    postgresql_013j_session_factory,
) -> None:
    from sqlalchemy.exc import DBAPIError, IntegrityError

    factory = postgresql_013j_session_factory
    graph = _ready_graph(factory)
    session = factory()
    try:
        with pytest.raises(IntegrityError, match="owner decision override authority failed"):
            _insert_raw_override(session, graph, actor_id=graph.scenario.actor_id)
        session.rollback()
        _install_owner_role(session, graph, graph.scenario.actor_id)
        with pytest.raises(
            DBAPIError,
            match="decision does not match the current exact run graph",
        ):
            _insert_raw_override(
                session,
                graph,
                actor_id=graph.scenario.actor_id,
                verdict_version=2,
            )
    finally:
        session.rollback()
        session.close()


def _add_independent_member(session, graph, actor_id: str) -> None:
    from sqlalchemy import text

    session.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, role, permissions) "
            "VALUES (:id, :email, :id, 'test-only', 'admin', '[]'::jsonb)"
        ),
        {"id": actor_id, "email": f"{actor_id}@example.test"},
    )
    session.execute(
        text(
            "INSERT INTO org_members (id, org_id, user_id, role, status) "
            "VALUES (:id, :org_id, :actor_id, 'owner', 'active')"
        ),
        {
            "id": str(uuid.uuid4()),
            "org_id": graph.scenario.org_id,
            "actor_id": actor_id,
        },
    )


def test_postgresql14_013j_rejects_override_for_independent_owner(
    postgresql_013j_session_factory,
) -> None:
    from sqlalchemy.exc import IntegrityError

    graph = _ready_graph(postgresql_013j_session_factory)
    actor_id = f"independent-owner-{uuid.uuid4().hex}"
    session = postgresql_013j_session_factory()
    try:
        _add_independent_member(session, graph, actor_id)
        _install_owner_role(session, graph, actor_id)
        with pytest.raises(IntegrityError, match="owner decision override is not required"):
            _insert_raw_override(session, graph, actor_id=actor_id)
    finally:
        session.rollback()
        session.close()


def test_postgresql14_013j_keeps_trust_and_freshness_gates_on_override(
    postgresql_013j_session_factory,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    graph = _ready_graph(postgresql_013j_session_factory)
    session = postgresql_013j_session_factory()
    try:
        _install_owner_role(session, graph, graph.scenario.actor_id)
        session.execute(
            text(
                "UPDATE governance_evidence_trust_policy_versions AS policy "
                "SET status='retired', retired_by=:actor_id, "
                "retirement_reason='Native 013j freshness rejection test.' "
                "FROM governance_evidence_admissions AS admission "
                "WHERE admission.id=:admission_id "
                "AND policy.id=admission.trust_policy_version_id"
            ),
            {
                "actor_id": graph.scenario.actor_id,
                "admission_id": graph.admission_id,
            },
        )
        with pytest.raises(
            IntegrityError,
            match="evidence is not decision-eligible at database time",
        ):
            _insert_raw_override(
                session,
                graph,
                actor_id=graph.scenario.actor_id,
            )
    finally:
        session.rollback()
        session.close()

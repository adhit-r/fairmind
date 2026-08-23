"""Direct database contract for owner-decision override integrity 013j."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path

import pytest

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
def postgresql_013j_session_factory():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import postgres_session_factory

    chain = postgres_session_factory.__wrapped__()
    factory = next(chain)
    session = factory()
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
            + ", 1, :reason, fairmind_canonical_clock_utc_013f(), "
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


def test_postgresql14_013j_upgrade_preflight_rejects_legacy_conflict(
    postgresql_013j_session_factory,
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
                "UPDATE governance_evidence_reviews AS review "
                "SET reviewed_by=admission.submitted_by "
                "FROM governance_evidence_admissions AS admission "
                "WHERE review.admission_id=admission.id "
                "AND review.admission_id=:admission_id"
            ),
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


def _insert_raw_override(session, graph, *, actor_id: str, verdict_version: int = 1) -> None:
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
            "org_id": graph.scenario.org_id,
            "workspace_id": graph.scenario.workspace_id,
            "system_id": graph.scenario.system_id,
            "run_id": graph.scenario.run_id,
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

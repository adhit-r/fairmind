import json
import sqlite3
from collections.abc import Generator

import pytest
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    MetaData,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, registry, sessionmaker

from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationPlan,
    GovernanceEvaluationRun,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceWorkspace,
)
from migrations.evaluation_runs_migration import sql_for


PRODUCTION_TABLES = (
    GovernanceWorkspace.__table__,
    GovernanceAISystem.__table__,
    GovernanceEvidenceRun.__table__,
    GovernanceEvidencePassportRevision.__table__,
    GovernanceEvaluationPlan.__table__,
    GovernanceEvaluationRun.__table__,
)

test_metadata = MetaData()
test_tables = {table.name: table.to_metadata(test_metadata) for table in PRODUCTION_TABLES}
test_registry = registry(metadata=test_metadata)


class Workspace:
    pass


class AISystem:
    pass


class EvaluationPlan:
    pass


class EvaluationRun:
    pass


for model, table_name in (
    (Workspace, "governance_workspaces"),
    (AISystem, "governance_ai_systems"),
    (EvaluationPlan, "governance_evaluation_plans"),
    (EvaluationRun, "governance_evaluation_runs"),
):
    test_registry.map_imperatively(model, test_tables[table_name])


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    test_metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        test_metadata.drop_all(engine)


@pytest.fixture
def sqlite_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE governance_workspaces (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            UNIQUE (id, org_id)
        );
        CREATE TABLE governance_ai_systems (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            org_id TEXT NOT NULL,
            UNIQUE (id, org_id),
            FOREIGN KEY (workspace_id, org_id)
                REFERENCES governance_workspaces(id, org_id)
        );
        CREATE TABLE governance_evidence_runs (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            system_id TEXT NOT NULL,
            org_id TEXT NOT NULL,
            UNIQUE (id, system_id, org_id),
            FOREIGN KEY (workspace_id, org_id)
                REFERENCES governance_workspaces(id, org_id)
        );
        CREATE TABLE governance_evidence_passport_revisions (
            id TEXT PRIMARY KEY,
            evidence_run_id TEXT NOT NULL,
            system_id TEXT NOT NULL,
            org_id TEXT NOT NULL,
            UNIQUE (id, evidence_run_id, system_id, org_id),
            FOREIGN KEY (evidence_run_id, system_id, org_id)
                REFERENCES governance_evidence_runs(id, system_id, org_id)
        );
        """
    )
    connection.executescript(sql_for("sqlite"))
    try:
        yield connection
    finally:
        connection.close()


def seed_governance_scope(
    connection: sqlite3.Connection,
    *,
    org_id: str,
    workspace_id: str,
    system_id: str,
) -> None:
    connection.execute(
        "INSERT INTO governance_workspaces (id, org_id) VALUES (?, ?)",
        (workspace_id, org_id),
    )
    connection.execute(
        "INSERT INTO governance_ai_systems (id, workspace_id, org_id) VALUES (?, ?, ?)",
        (system_id, workspace_id, org_id),
    )


def insert_evaluation_plan(
    connection: sqlite3.Connection,
    *,
    id: str,
    org_id: str,
    workspace_id: str,
    system_id: str,
) -> None:
    connection.execute(
        """
        INSERT INTO governance_evaluation_plans (
            id, org_id, workspace_id, system_id, name, target_kind,
            lifecycle_phases_json, execution_depth, enforcement_mode,
            delivery_mode, suite_refs_json, status, created_by, updated_by,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'Plan', 'predictive_model', '["pre_deploy"]',
                  'hybrid', 'human_approval', 'external_provider',
                  '["fairmind/core@1.0.0"]', 'active', 'user-a', 'user-a', ?, ?)
        """,
        (
            id,
            org_id,
            workspace_id,
            system_id,
            "2026-07-19T00:00:00+00:00",
            "2026-07-19T00:00:00+00:00",
        ),
    )


def insert_evaluation_run(
    connection: sqlite3.Connection,
    *,
    id: str = "run-a",
    plan_id: str,
    org_id: str,
    workspace_id: str,
    system_id: str,
    technical_status: str = "awaiting_evidence",
    linked_evidence_run_id: str | None = None,
    linked_passport_revision_id: str | None = None,
    include_link_audit: bool = True,
) -> None:
    has_link_audit = linked_passport_revision_id is not None and include_link_audit
    linked_by = "reviewer-a" if has_link_audit else None
    linked_at = (
        "2026-07-19T00:00:00+00:00" if has_link_audit else None
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, trigger,
            technical_status, overall_verdict, layer_verdicts_json,
            linked_evidence_run_id, linked_passport_revision_id, linked_by, linked_at,
            requested_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'manual', ?, 'insufficient', '{}', ?, ?, ?, ?,
                  'user-a', ?, ?)
        """,
        (
            id,
            org_id,
            workspace_id,
            system_id,
            plan_id,
            technical_status,
            linked_evidence_run_id,
            linked_passport_revision_id,
            linked_by,
            linked_at,
            "2026-07-19T00:00:00+00:00",
            "2026-07-19T00:00:00+00:00",
        ),
    )


def add_plan(session: Session) -> EvaluationPlan:
    workspace = Workspace(id="workspace-a", org_id="org-a", name="Workspace A")
    system = AISystem(
        id="system-a",
        org_id="org-a",
        workspace_id=workspace.id,
        name="System A",
    )
    plan = EvaluationPlan(
        id="plan-a",
        org_id="org-a",
        workspace_id=workspace.id,
        system_id=system.id,
        name="Plan A",
        target_kind="predictive_model",
        lifecycle_phases_json='["pre_deploy"]',
        delivery_mode="external_provider",
        suite_refs_json='["fairmind/core@1.0.0"]',
        created_by="user-a",
        updated_by="user-a",
    )
    session.add(workspace)
    session.flush()
    session.add(system)
    session.flush()
    session.add(plan)
    session.flush()
    return plan


def constraint_columns(model: type, constraint_type: type) -> set[tuple[str, ...]]:
    return {
        tuple(constraint.columns.keys())
        for constraint in model.__table__.constraints
        if isinstance(constraint, constraint_type)
    }


def test_models_expose_exact_columns_and_tenant_constraints() -> None:
    assert tuple(GovernanceEvaluationPlan.__table__.columns.keys()) == (
        "id",
        "org_id",
        "workspace_id",
        "system_id",
        "name",
        "target_kind",
        "lifecycle_phases_json",
        "execution_depth",
        "enforcement_mode",
        "delivery_mode",
        "suite_refs_json",
        "status",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    assert tuple(GovernanceEvaluationRun.__table__.columns.keys()) == (
        "id",
        "org_id",
        "workspace_id",
        "system_id",
        "plan_id",
        "trigger",
        "technical_status",
        "overall_verdict",
        "layer_verdicts_json",
        "linked_evidence_run_id",
        "linked_passport_revision_id",
        "linked_by",
        "linked_at",
        "requested_by",
        "started_at",
        "completed_at",
        "failure_code",
        "failure_message",
        "created_at",
        "updated_at",
    )
    assert ("id", "workspace_id", "org_id") in constraint_columns(
        GovernanceAISystem, UniqueConstraint
    )
    assert ("id", "workspace_id", "system_id", "org_id") in constraint_columns(
        GovernanceEvidenceRun, UniqueConstraint
    )
    assert ("id", "workspace_id", "system_id", "org_id") in constraint_columns(
        GovernanceEvaluationPlan, UniqueConstraint
    )
    assert ("id", "workspace_id", "system_id", "org_id") in constraint_columns(
        GovernanceEvaluationRun, UniqueConstraint
    )
    assert (
        "linked_passport_revision_id",
        "linked_evidence_run_id",
        "system_id",
        "org_id",
    ) in constraint_columns(GovernanceEvaluationRun, ForeignKeyConstraint)
    assert (
        "linked_evidence_run_id",
        "workspace_id",
        "system_id",
        "org_id",
    ) in constraint_columns(GovernanceEvaluationRun, ForeignKeyConstraint)


def test_new_evaluation_run_is_insufficient_until_evidence_is_linked(
    db_session: Session,
) -> None:
    plan = add_plan(db_session)
    run = EvaluationRun(
        org_id=plan.org_id,
        workspace_id=plan.workspace_id,
        system_id=plan.system_id,
        plan_id=plan.id,
        trigger="manual",
        requested_by="user-a",
    )
    db_session.add(run)
    db_session.flush()

    assert run.technical_status == "awaiting_evidence"
    assert run.overall_verdict == "insufficient"
    assert json.loads(run.layer_verdicts_json) == {}
    assert plan.execution_depth == "hybrid"
    assert plan.enforcement_mode == "human_approval"
    assert plan.status == "draft"


def test_orm_rejects_succeeded_without_exact_passport_link(db_session: Session) -> None:
    plan = add_plan(db_session)
    db_session.add(
        EvaluationRun(
            org_id=plan.org_id,
            workspace_id=plan.workspace_id,
            system_id=plan.system_id,
            plan_id=plan.id,
            trigger="manual",
            requested_by="user-a",
            technical_status="succeeded",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_sqlite_migration_rejects_cross_tenant_plan_run_link(
    sqlite_connection: sqlite3.Connection,
) -> None:
    seed_governance_scope(
        sqlite_connection, org_id="org-a", workspace_id="ws-a", system_id="sys-a"
    )
    seed_governance_scope(
        sqlite_connection, org_id="org-b", workspace_id="ws-b", system_id="sys-b"
    )
    insert_evaluation_plan(
        sqlite_connection,
        id="plan-a",
        org_id="org-a",
        workspace_id="ws-a",
        system_id="sys-a",
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            plan_id="plan-a",
            org_id="org-b",
            workspace_id="ws-b",
            system_id="sys-b",
        )


def test_sqlite_migration_requires_succeeded_runs_to_have_exact_passport_link(
    sqlite_connection: sqlite3.Connection,
) -> None:
    seed_governance_scope(
        sqlite_connection, org_id="org-a", workspace_id="ws-a", system_id="sys-a"
    )
    insert_evaluation_plan(
        sqlite_connection,
        id="plan-a",
        org_id="org-a",
        workspace_id="ws-a",
        system_id="sys-a",
    )
    sqlite_connection.execute(
        """
        INSERT INTO governance_evidence_runs (id, workspace_id, system_id, org_id)
        VALUES ('evidence-a', 'ws-a', 'sys-a', 'org-a')
        """
    )
    sqlite_connection.execute(
        """
        INSERT INTO governance_evidence_passport_revisions
            (id, evidence_run_id, system_id, org_id)
        VALUES ('revision-a', 'evidence-a', 'sys-a', 'org-a')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            id="run-unlinked",
            plan_id="plan-a",
            org_id="org-a",
            workspace_id="ws-a",
            system_id="sys-a",
            technical_status="succeeded",
        )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            id="run-linked-without-audit",
            plan_id="plan-a",
            org_id="org-a",
            workspace_id="ws-a",
            system_id="sys-a",
            technical_status="succeeded",
            linked_evidence_run_id="evidence-a",
            linked_passport_revision_id="revision-a",
            include_link_audit=False,
        )

    insert_evaluation_run(
        sqlite_connection,
        id="run-linked",
        plan_id="plan-a",
        org_id="org-a",
        workspace_id="ws-a",
        system_id="sys-a",
        technical_status="succeeded",
        linked_evidence_run_id="evidence-a",
        linked_passport_revision_id="revision-a",
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            id="run-linked-but-running",
            plan_id="plan-a",
            org_id="org-a",
            workspace_id="ws-a",
            system_id="sys-a",
            technical_status="running",
            linked_evidence_run_id="evidence-a",
            linked_passport_revision_id="revision-a",
        )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            id="run-wrong-revision",
            plan_id="plan-a",
            org_id="org-a",
            workspace_id="ws-a",
            system_id="sys-a",
            technical_status="succeeded",
            linked_evidence_run_id="evidence-a",
            linked_passport_revision_id="missing-revision",
        )


def test_sqlite_migration_rejects_evidence_link_from_another_workspace(
    sqlite_connection: sqlite3.Connection,
) -> None:
    seed_governance_scope(
        sqlite_connection, org_id="org-a", workspace_id="ws-a", system_id="sys-a"
    )
    sqlite_connection.execute(
        "INSERT INTO governance_workspaces (id, org_id) VALUES ('ws-b', 'org-a')"
    )
    insert_evaluation_plan(
        sqlite_connection,
        id="plan-a",
        org_id="org-a",
        workspace_id="ws-a",
        system_id="sys-a",
    )
    sqlite_connection.execute(
        """
        INSERT INTO governance_evidence_runs (id, workspace_id, system_id, org_id)
        VALUES ('evidence-b', 'ws-b', 'sys-a', 'org-a')
        """
    )
    sqlite_connection.execute(
        """
        INSERT INTO governance_evidence_passport_revisions
            (id, evidence_run_id, system_id, org_id)
        VALUES ('revision-b', 'evidence-b', 'sys-a', 'org-a')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_evaluation_run(
            sqlite_connection,
            id="run-cross-workspace",
            plan_id="plan-a",
            org_id="org-a",
            workspace_id="ws-a",
            system_id="sys-a",
            technical_status="succeeded",
            linked_evidence_run_id="evidence-b",
            linked_passport_revision_id="revision-b",
        )


def test_migration_selector_returns_direct_dialect_sql_and_is_idempotent(
    sqlite_connection: sqlite3.Connection,
) -> None:
    postgresql_sql = sql_for("postgresql")
    sqlite_sql = sql_for("sqlite")

    assert "CREATE TABLE IF NOT EXISTS governance_evaluation_plans" in postgresql_sql
    assert "CREATE TABLE IF NOT EXISTS governance_evaluation_runs" in postgresql_sql
    assert "FOREIGN KEY (plan_id, workspace_id, system_id, org_id)" in postgresql_sql
    assert (
        "FOREIGN KEY (linked_evidence_run_id, workspace_id, system_id, org_id)"
        in postgresql_sql
    )
    assert "BOOLEAN" not in sqlite_sql
    assert "FOREIGN KEY (plan_id, workspace_id, system_id, org_id)" in sqlite_sql
    assert (
        "linked_passport_revision_id, linked_evidence_run_id, system_id, org_id"
        in sqlite_sql
    )
    assert "re.sub" not in sqlite_sql

    sqlite_connection.executescript(sqlite_sql)

    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("mysql")


def test_check_constraints_cover_exact_vocabulary() -> None:
    plan_checks = {
        str(constraint.sqltext)
        for constraint in GovernanceEvaluationPlan.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    run_checks = {
        str(constraint.sqltext)
        for constraint in GovernanceEvaluationRun.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert (
        "target_kind IN ('predictive_model', 'llm_application', 'agent', 'code_generator', "
        "'image_generator', 'audio_model', 'video_model', 'multimodal_system')"
        in plan_checks
    )
    assert "execution_depth IN ('inline', 'deep', 'hybrid')" in plan_checks
    assert "enforcement_mode IN ('advisory', 'human_approval', 'automatic')" in plan_checks
    assert (
        "delivery_mode IN ('fairmind_worker', 'external_provider', 'imported_report')"
        in plan_checks
    )
    assert "status IN ('draft', 'active', 'archived')" in plan_checks
    assert (
        "technical_status IN ('awaiting_evidence', 'running', 'succeeded', 'failed', "
        "'cancelled')" in run_checks
    )
    assert (
        "overall_verdict IN ('approved', 'conditional', 'review', 'blocked', "
        "'insufficient')" in run_checks
    )
    assert (
        "trigger IN ('manual', 'ci', 'scheduled', 'release_gate', 'incident', "
        "'integration_sync')" in run_checks
    )

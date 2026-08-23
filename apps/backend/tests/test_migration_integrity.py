from __future__ import annotations

import os
import sqlite3
import subprocess
import uuid
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import pytest
from sqlalchemy import create_engine, text

import config.migration_integrity as migration_integrity
from config.migration_integrity import (
    FROZEN_013B_OPERATOR_V2_CHECKSUM,
    FROZEN_013C_OPERATOR_CHECKSUM,
    FROZEN_013D_OPERATOR_CHECKSUM,
    FROZEN_013E_OPERATOR_CHECKSUM,
    FROZEN_013F_OPERATOR_CHECKSUM,
    FROZEN_013G_OPERATOR_CHECKSUM,
    FROZEN_013H_OPERATOR_CHECKSUM,
    FROZEN_013I_OPERATOR_CHECKSUM,
    FROZEN_ASSURANCE_MIGRATIONS,
    FROZEN_POSTGRESQL_ASSURANCE_CATALOGS,
    FROZEN_SQLITE_013C_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013D_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013E_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013F_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013G_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013H_FIXTURE_CHECKSUM,
    FROZEN_SQLITE_013I_FIXTURE_CHECKSUM,
    POSTGRESQL_ASSURANCE_CATALOG_SPEC,
    POSTGRESQL_ASSURANCE_FUNCTIONS,
    POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS,
    SQLITE_ASSURANCE_INDEXES,
    SQLITE_ASSURANCE_TABLES,
    SQLITE_ASSURANCE_TRIGGERS,
    SQLITE_ASSURANCE_VIEWS,
    FrozenMigration,
    FrozenPostgreSQLCatalog,
    MigrationIntegrityError,
    PostgreSQLCatalogSpec,
    bind_postgresql_engine_search_path,
    normalized_database_identity,
    postgresql_assurance_catalog_digest,
    postgresql_runtime_search_path,
    postgresql_server_major,
    select_frozen_postgresql_catalog,
    validate_frozen_postgresql_catalog,
    verify_assurance_migration_integrity,
    verify_bundled_migration_checksums,
    verify_database_identities,
    verify_postgresql_assurance_catalog,
    verify_postgresql_migration_ledger,
    verify_sqlite_assurance_schema,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations"
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
POSTGRES_BASE_CHAIN = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "010_environmental_governance.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
)
POSTGRES_OPERATOR_CHAIN = (
    "upgrade_paths/012_to_013_evaluation_v2.sql",
    "upgrade_paths/013_to_013a_evaluation_binding_integrity.sql",
    "upgrade_paths/013a_to_013b_evaluation_assurance_trust_integrity_v2.sql",
    "upgrade_paths/013b_to_013c_evidence_verification_receipt.sql",
    "upgrade_paths/013c_to_013d_evaluator_catalog.sql",
    "upgrade_paths/013d_to_013e_environmental_tenant_scope.sql",
    "upgrade_paths/013e_to_013f_trust_authority_integrity.sql",
    "upgrade_paths/013f_to_013g_operational_evidence_freshness.sql",
    "upgrade_paths/013g_to_013h_idempotency_retention_integrity.sql",
    "upgrade_paths/013h_to_013i_imported_evidence_delivery_integrity.sql",
)
POSTGRES_013J_OPERATOR = (
    "upgrade_paths/013i_to_013j_owner_decision_override_integrity.sql"
)
POSTGRES_OPERATOR_CHAIN_THROUGH_013J = POSTGRES_OPERATOR_CHAIN + (
    POSTGRES_013J_OPERATOR,
)
POSTGRESQL_013B_PREREQUISITE_CONSTRAINTS = frozenset(
    {
        ("governance_evaluation_plans", "uq_governance_evaluation_plan_contract_tenant"),
        ("governance_evaluation_runs", "fk_governance_evaluation_run_plan_contract"),
        (
            "governance_evaluation_target_versions",
            "uq_governance_evaluation_target_kind_tenant",
        ),
        (
            "governance_evaluation_plans",
            "fk_governance_evaluation_plan_target_version",
        ),
        (
            "governance_evaluation_suite_versions",
            "ck_governance_evaluation_suite_canonical_ref",
        ),
        (
            "governance_evaluation_runs",
            "uq_governance_evaluation_run_v2_envelope_scope",
        ),
        (
            "governance_evaluation_runs",
            "uq_governance_evaluation_run_org_envelope_nonce",
        ),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_technical_status",
        ),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_evidence_link_state",
        ),
        ("governance_evaluation_runs", "ck_governance_evaluation_run_timestamps"),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_v2_projection_freeze",
        ),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_envelope_nonce",
        ),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_timestamp_canonical",
        ),
        (
            "governance_evaluation_runs",
            "ck_governance_evaluation_run_timestamp_order",
        ),
        (
            "governance_evaluation_run_suite_executions",
            "ck_governance_evaluation_suite_execution_timestamps",
        ),
        (
            "governance_evaluation_run_suite_executions",
            "ck_governance_evaluation_suite_execution_projection_freeze",
        ),
        (
            "governance_evaluation_run_suite_executions",
            "ck_governance_evaluation_suite_execution_timestamp_canonical",
        ),
        (
            "governance_evaluation_run_suite_executions",
            "ck_governance_evaluation_suite_execution_timestamp_order",
        ),
    }
)
POSTGRESQL_013B_RETAINED_PREREQUISITE_CONSTRAINTS = POSTGRESQL_013B_PREREQUISITE_CONSTRAINTS - {
    (
        "governance_evaluation_runs",
        "ck_governance_evaluation_run_v2_projection_freeze",
    ),
    (
        "governance_evaluation_run_suite_executions",
        "ck_governance_evaluation_suite_execution_projection_freeze",
    ),
}


def _install_sqlite_assurance_chain(database_path: Path) -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite as apply_013d
    from migrations.environmental_tenant_scope_migration import apply_sqlite as apply_013e
    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_binding_integrity_migration import sql_for as sql_013a
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.evidence_verification_receipt_migration import sql_for as sql_013c
    from migrations.governance_assurance_migration import sql_for as sql_011
    from migrations.trust_authority_integrity_migration import apply_sqlite as apply_013f
    from migrations.operational_evidence_freshness_migration import (
        apply_sqlite as apply_013g,
    )
    from migrations.idempotency_retention_integrity_migration import (
        apply_sqlite as apply_013h,
    )
    from migrations.imported_evidence_delivery_integrity_migration import (
        apply_sqlite as apply_013i,
    )
    from migrations.owner_decision_override_integrity_migration import (
        apply_sqlite as apply_013j,
    )

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            (MIGRATIONS / "008_governance_canonical.sql").read_text(encoding="utf-8")
        )
        connection.executescript(sql_011("sqlite"))
        connection.executescript(sql_012("sqlite"))
        connection.executescript(sql_013("sqlite"))
        connection.executescript(sql_013a("sqlite"))
        connection.executescript(
            (
                MIGRATIONS / "fixtures/013b_evaluation_assurance_trust_integrity.sqlite.sql"
            ).read_text(encoding="utf-8")
        )
        connection.executescript(sql_013c("sqlite"))
        apply_013d(connection)
        apply_013e(connection)
        apply_013f(connection)
        apply_013g(connection)
        apply_013h(connection)
        apply_013i(connection)
        apply_013j(connection)
    finally:
        connection.close()


def _install_postgresql_base_through_012(
    postgres_url: str,
    schema_name: str,
) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(postgres_url)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(
                sql.SQL("REVOKE CREATE ON SCHEMA {} FROM PUBLIC").format(
                    sql.Identifier(schema_name)
                )
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                    sql.Identifier(schema_name)
                )
            )
            for migration_name in POSTGRES_BASE_CHAIN:
                cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))
    finally:
        connection.close()


def _run_postgresql_operator_migration(
    postgres_url: str,
    schema_name: str,
    migration_name: str,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PGOPTIONS"] = (
        f"-c search_path={schema_name},pg_catalog,pg_temp "
        f"-c fairmind.migration_schema={schema_name}"
    )
    return subprocess.run(
        [
            "psql",
            "-X",
            "-w",
            postgres_url,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            str(MIGRATIONS / migration_name),
        ],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _postgresql_013b_prerequisite_definitions(
    connection,
    *,
    schema_name: str,
    expected: frozenset[tuple[str, str]] = POSTGRESQL_013B_PREREQUISITE_CONSTRAINTS,
) -> dict[tuple[str, str], str]:
    constraint_names = [constraint_name for _table_name, constraint_name in expected]
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relation_entry.relname, constraint_entry.conname, "
            "pg_catalog.pg_get_constraintdef(constraint_entry.oid, true) "
            "FROM pg_catalog.pg_constraint AS constraint_entry "
            "JOIN pg_catalog.pg_class AS relation_entry "
            "ON relation_entry.oid = constraint_entry.conrelid "
            "JOIN pg_catalog.pg_namespace AS namespace_entry "
            "ON namespace_entry.oid = relation_entry.relnamespace "
            "WHERE namespace_entry.nspname = %s "
            "AND constraint_entry.conname = ANY(%s)",
            (schema_name, constraint_names),
        )
        installed = {
            (str(table_name), str(constraint_name)): str(definition)
            for table_name, constraint_name, definition in cursor.fetchall()
        }
    assert set(installed) == set(expected)
    return installed


def _install_minimal_postgresql_assurance_catalog(
    connection,
    *,
    schema_name: str,
) -> PostgreSQLCatalogSpec:
    """Install a real, small catalog for native fingerprint behavior tests."""
    connection.exec_driver_sql(f'CREATE SCHEMA "{schema_name}"')
    connection.exec_driver_sql(f'REVOKE CREATE ON SCHEMA "{schema_name}" FROM PUBLIC')
    connection.exec_driver_sql(
        f'CREATE TABLE "{schema_name}".guarded_events '
        "(id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
    )
    connection.exec_driver_sql(
        f'CREATE FUNCTION "{schema_name}".guard_guarded_events() '
        "RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER "
        f'SET search_path TO pg_catalog, "{schema_name}", pg_temp '
        "AS $$ BEGIN RAISE EXCEPTION 'append-only'; END $$"
    )
    connection.exec_driver_sql(
        "CREATE TRIGGER guarded_events_no_update BEFORE UPDATE "
        f'ON "{schema_name}".guarded_events FOR EACH ROW '
        f'EXECUTE FUNCTION "{schema_name}".guard_guarded_events()'
    )
    return PostgreSQLCatalogSpec(
        relations=frozenset({"guarded_events"}),
        functions=frozenset({"guard_guarded_events"}),
        required_triggers=frozenset({"guarded_events_no_update"}),
    )


def _freeze_native_postgresql_catalog(
    connection,
    *,
    schema_name: str,
    spec: PostgreSQLCatalogSpec,
) -> tuple[int, str, Mapping[int, FrozenPostgreSQLCatalog]]:
    major = postgresql_server_major(connection)
    digest = postgresql_assurance_catalog_digest(
        connection,
        trusted_schema=schema_name,
        spec=spec,
    )
    frozen = MappingProxyType(
        {
            major: FrozenPostgreSQLCatalog(
                spec=spec,
                postgresql_major=major,
                digest=digest,
            )
        }
    )
    return major, digest, frozen


def test_postgresql_ledger_requires_every_exact_frozen_checksum() -> None:
    expected = (
        FrozenMigration("migration-a", "a" * 64, Path("a.sql")),
        FrozenMigration("migration-b", "b" * 64, Path("b.sql")),
    )
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS trusted")
        connection.execute(
            text(
                "CREATE TABLE trusted.fairmind_operator_migration_ledger ("
                "migration_key TEXT PRIMARY KEY, migration_checksum TEXT NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO trusted.fairmind_operator_migration_ledger "
                "(migration_key, migration_checksum) VALUES "
                "('migration-a', :checksum_a), ('migration-b', :checksum_b)"
            ),
            {"checksum_a": "a" * 64, "checksum_b": "b" * 64},
        )
        verify_postgresql_migration_ledger(connection, trusted_schema="trusted", expected=expected)

        connection.execute(
            text(
                "UPDATE trusted.fairmind_operator_migration_ledger "
                "SET migration_checksum = :checksum WHERE migration_key = 'migration-b'"
            ),
            {"checksum": "c" * 64},
        )
        with pytest.raises(MigrationIntegrityError, match="migration-b.*checksum drift"):
            verify_postgresql_migration_ledger(
                connection, trusted_schema="trusted", expected=expected
            )

        connection.execute(
            text(
                "DELETE FROM trusted.fairmind_operator_migration_ledger "
                "WHERE migration_key = 'migration-a'"
            )
        )
        with pytest.raises(MigrationIntegrityError, match="migration-a.*missing"):
            verify_postgresql_migration_ledger(
                connection, trusted_schema="trusted", expected=expected
            )


def test_postgresql_ledger_uses_only_the_validated_trusted_schema() -> None:
    expected = (FrozenMigration("migration-a", "a" * 64, Path("a.sql")),)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS trusted")
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS shadow")
        for schema in ("trusted", "shadow"):
            connection.exec_driver_sql(
                f"CREATE TABLE {schema}.fairmind_operator_migration_ledger "
                "(migration_key TEXT PRIMARY KEY, migration_checksum TEXT NOT NULL)"
            )
        connection.execute(
            text(
                "INSERT INTO trusted.fairmind_operator_migration_ledger "
                "VALUES ('migration-a', :checksum)"
            ),
            {"checksum": "b" * 64},
        )
        connection.execute(
            text(
                "INSERT INTO shadow.fairmind_operator_migration_ledger "
                "VALUES ('migration-a', :checksum)"
            ),
            {"checksum": "a" * 64},
        )

        with pytest.raises(MigrationIntegrityError, match="migration-a.*checksum drift"):
            verify_postgresql_migration_ledger(
                connection, trusted_schema="trusted", expected=expected
            )


def test_postgresql_ledger_rejects_untrusted_or_missing_schema() -> None:
    expected = (FrozenMigration("migration-a", "a" * 64, Path("a.sql")),)
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        for schema in ("", "pg_catalog", "information_schema", "pg_temp_attack"):
            with pytest.raises(MigrationIntegrityError, match="trusted.*schema"):
                verify_postgresql_migration_ledger(
                    connection, trusted_schema=schema, expected=expected
                )
        with pytest.raises(MigrationIntegrityError, match="does not exist"):
            verify_postgresql_migration_ledger(
                connection, trusted_schema="missing", expected=expected
            )


def test_database_identity_normalizes_driver_defaults_without_exposing_secrets() -> None:
    first = normalized_database_identity(
        "postgresql+psycopg2://assurance:secret-one@LOCALHOST:5432/fairmind?ssl=true"
    )
    second = normalized_database_identity("postgresql://assurance:secret-two@localhost/fairmind")
    assert first == second

    with pytest.raises(MigrationIntegrityError) as caught:
        verify_database_identities(
            "postgresql://assurance:secret-one@localhost/fairmind",
            "postgresql://assurance:secret-two@localhost/other",
        )
    message = str(caught.value)
    assert message == "PostgreSQL runtime database identities differ"
    assert "secret-one" not in message
    assert "secret-two" not in message
    assert "fairmind" not in message


@pytest.mark.parametrize(
    ("first_url", "second_url"),
    (
        (
            "postgresql://assurance@localhost/fairmind?host=db-a.internal",
            "postgresql://assurance@localhost/fairmind?host=db-b.internal",
        ),
        (
            "postgresql://assurance@localhost:5432/fairmind?port=6432",
            "postgresql://assurance@localhost:5432/fairmind?port=7432",
        ),
        (
            "postgresql://assurance@localhost/fairmind?hostaddr=192.0.2.10",
            "postgresql://assurance@localhost/fairmind?hostaddr=192.0.2.11",
        ),
    ),
)
def test_postgresql_database_identity_rejects_libpq_endpoint_query_overrides(
    first_url: str,
    second_url: str,
) -> None:
    with pytest.raises(MigrationIntegrityError, match="ambiguous endpoint routing"):
        verify_database_identities(first_url, second_url)


def test_postgresql_database_identity_rejects_unix_socket_host_override() -> None:
    with pytest.raises(MigrationIntegrityError, match="ambiguous endpoint routing"):
        verify_database_identities(
            "postgresql://assurance@localhost/fairmind",
            "postgresql://assurance@/fairmind?host=%2Fvar%2Frun%2Fpostgresql",
        )


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql://assurance@/fairmind?host=db-a:5432&host=db-b:5432",
        "postgresql://assurance@/fairmind?host=db-a,db-b&port=5432,6432",
        "postgresql://assurance@db-a,db-b:5432/fairmind",
    ),
)
def test_postgresql_database_identity_rejects_multi_host_routing(
    database_url: str,
) -> None:
    with pytest.raises(MigrationIntegrityError, match="ambiguous endpoint routing"):
        normalized_database_identity(database_url)


def test_sqlite_database_identity_uses_one_canonical_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    expected = normalized_database_identity("sqlite:///runtime/fairmind.sqlite3")
    absolute = normalized_database_identity(
        f"sqlite:///{tmp_path / 'runtime' / 'fairmind.sqlite3'}"
    )
    assert expected == absolute

    with pytest.raises(
        MigrationIntegrityError,
        match="^SQLite runtime database identities differ$",
    ):
        verify_database_identities(
            "sqlite:///runtime/fairmind.sqlite3",
            "sqlite:///other/fairmind.sqlite3",
        )


def test_sqlite_in_memory_identity_requires_the_same_engine_instance() -> None:
    first = create_engine("sqlite:///:memory:")
    second = create_engine("sqlite:///:memory:")
    try:
        verify_database_identities(first, first)
        with pytest.raises(
            MigrationIntegrityError,
            match="^SQLite runtime database identities differ$",
        ):
            verify_database_identities(first, second)
    finally:
        first.dispose()
        second.dispose()


def test_postgresql_runtime_search_path_is_fixed_and_identifier_safe() -> None:
    assert postgresql_runtime_search_path('tenant"schema') == 'pg_catalog,"tenant""schema",pg_temp'
    for schema in (
        "",
        "pg_catalog",
        "PG_CATALOG",
        "information_schema",
        "INFORMATION_SCHEMA",
        "temp",
        "TEMP",
        "pg_temp_attack",
        "pg_attack",
        "tenant\x00attack",
    ):
        with pytest.raises(MigrationIntegrityError, match="trusted.*schema"):
            postgresql_runtime_search_path(schema)


def test_postgresql_checkout_binding_escapes_literal_metacharacters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import migration_integrity as migration_module

    callbacks = []

    class Dialect:
        name = "postgresql"

    class Engine:
        dialect = Dialect()

    class Cursor:
        statement = ""

        def execute(self, statement: str) -> None:
            self.statement = statement

        def fetchone(self):
            return (postgresql_runtime_search_path("tenant',public--"),)

        def close(self) -> None:
            pass

    class DBAPIConnection:
        cursor_instance = Cursor()

        def cursor(self):
            return self.cursor_instance

    monkeypatch.setattr(
        migration_module.event,
        "listen",
        lambda _engine, _event_name, callback: callbacks.append(callback),
    )
    engine = Engine()
    bind_postgresql_engine_search_path(engine, "tenant',public--")
    callbacks[0](DBAPIConnection(), None, None)

    statement = DBAPIConnection.cursor_instance.statement
    assert "tenant'',public--" in statement
    assert "%s" not in statement
    assert statement.count("SELECT") == 1


def test_production_postgresql_manifest_covers_audit_immutability() -> None:
    assert not hasattr(POSTGRESQL_ASSURANCE_CATALOG_SPEC, "digest")
    assert {
        "governance_evaluation_audit_events_no_update",
        "governance_evaluation_audit_events_no_delete",
        "governance_evaluation_audit_events_guard_head_insert",
        "governance_evaluation_audit_events_advance_head",
    } <= POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS
    assert "governance_evaluation_audit_events" in (POSTGRESQL_ASSURANCE_CATALOG_SPEC.relations)
    assert "guard_governance_evidence_admission_signer_013b" in (POSTGRESQL_ASSURANCE_FUNCTIONS)
    assert {
        "fairmind_verification_receipt_is_relationally_valid_013c",
        "fairmind_verification_receipt_matches_admission_013c",
        "fairmind_verification_receipt_has_exact_verified_admission_013c",
        "fairmind_verified_admission_has_exact_receipt_013c",
    } <= POSTGRESQL_ASSURANCE_FUNCTIONS
    assert "governance_evidence_admissions_guard_signer_insert" in (
        POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS
    )
    assert isinstance(FROZEN_POSTGRESQL_ASSURANCE_CATALOGS, MappingProxyType)
    assert set(FROZEN_POSTGRESQL_ASSURANCE_CATALOGS) == {14}
    frozen = FROZEN_POSTGRESQL_ASSURANCE_CATALOGS[14]
    assert frozen.spec is POSTGRESQL_ASSURANCE_CATALOG_SPEC
    assert frozen.postgresql_major == 14
    assert frozen.digest == "c4a2a891640a309a07a2421cb0951615b82e32645757e0c1469cacf501020be2"
    validate_frozen_postgresql_catalog(frozen)


def test_frozen_postgresql_catalog_rejects_placeholder_and_invalid_digests() -> None:
    spec = PostgreSQLCatalogSpec(
        relations=frozenset({"relation-a"}),
        functions=frozenset({"function-a"}),
        required_triggers=frozenset({"trigger-a"}),
    )
    valid = FrozenPostgreSQLCatalog(
        spec=spec,
        postgresql_major=14,
        digest="a" * 64,
    )
    validate_frozen_postgresql_catalog(valid)
    for digest in ("", "0" * 64, "A" * 64, "g" * 64):
        with pytest.raises(MigrationIntegrityError, match="catalog digest"):
            validate_frozen_postgresql_catalog(
                FrozenPostgreSQLCatalog(
                    spec=spec,
                    postgresql_major=14,
                    digest=digest,
                )
            )


def test_postgresql_catalog_selection_fails_closed_for_unsupported_major() -> None:
    with pytest.raises(
        MigrationIntegrityError,
        match="catalog is not frozen for server major 15",
    ):
        select_frozen_postgresql_catalog(15, {})


def test_postgresql_ledger_missing_table_fails_closed() -> None:
    engine = create_engine("sqlite:///:memory:")
    expected = (FrozenMigration("migration-a", "a" * 64, Path("a.sql")),)
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS trusted")
        with pytest.raises(MigrationIntegrityError, match="ledger is unavailable"):
            verify_postgresql_migration_ledger(
                connection, trusted_schema="trusted", expected=expected
            )


def test_bundled_checksum_manifest_detects_source_drift(tmp_path: Path) -> None:
    payload = tmp_path / "migration.sql"
    payload.write_text("SELECT 1;\n", encoding="utf-8")
    import hashlib

    expected = (
        FrozenMigration(
            "migration-a",
            hashlib.sha256(payload.read_bytes()).hexdigest(),
            payload,
        ),
    )
    verify_bundled_migration_checksums(expected=expected)

    payload.write_text("SELECT 2;\n", encoding="utf-8")
    with pytest.raises(MigrationIntegrityError, match="bundled source checksum drift"):
        verify_bundled_migration_checksums(expected=expected)


def test_013c_operator_source_checksum_is_frozen() -> None:
    import hashlib

    operator = MIGRATIONS / "upgrade_paths/013b_to_013c_evidence_verification_receipt.sql"
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == (FROZEN_013C_OPERATOR_CHECKSUM)


def test_sqlite_013c_fixture_source_checksum_is_frozen() -> None:
    import hashlib

    fixture = MIGRATIONS / "fixtures/013c_evidence_verification_receipt.sqlite.sql"
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (FROZEN_SQLITE_013C_FIXTURE_CHECKSUM)


def test_013d_operator_source_checksum_is_frozen() -> None:
    import hashlib

    operator = MIGRATIONS / "upgrade_paths/013c_to_013d_evaluator_catalog.sql"
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == (FROZEN_013D_OPERATOR_CHECKSUM)


def test_sqlite_013d_fixture_source_checksum_is_frozen() -> None:
    import hashlib

    fixture = MIGRATIONS / "fixtures/013d_evaluator_catalog.sqlite.sql"
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (FROZEN_SQLITE_013D_FIXTURE_CHECKSUM)


def test_013e_operator_source_checksum_is_frozen() -> None:
    import hashlib

    operator = MIGRATIONS / "upgrade_paths/013d_to_013e_environmental_tenant_scope.sql"
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == (FROZEN_013E_OPERATOR_CHECKSUM)


def test_013e_direct_payload_and_operator_ledger_chain_are_frozen() -> None:
    import hashlib

    frozen = next(
        item
        for item in FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key == "013d-to-013e-environmental-tenant-scope-v1"
    )
    direct = MIGRATIONS / "013e_environmental_tenant_scope.sql"
    operator = MIGRATIONS / "upgrade_paths/013d_to_013e_environmental_tenant_scope.sql"
    operator_source = operator.read_text(encoding="utf-8")

    assert frozen.ledger_key == "013d-to-013e-environmental-tenant-scope-v1"
    assert frozen.source_path == direct
    assert hashlib.sha256(direct.read_bytes()).hexdigest() == frozen.checksum
    assert "\\ir ../013e_environmental_tenant_scope.sql" in operator_source
    assert frozen.ledger_key in operator_source
    assert frozen.checksum in operator_source


def test_sqlite_013e_fixture_source_checksum_is_frozen() -> None:
    import hashlib

    fixture = MIGRATIONS / "fixtures/013e_environmental_tenant_scope.sqlite.sql"
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (FROZEN_SQLITE_013E_FIXTURE_CHECKSUM)


def test_013b_v2_operator_source_checksum_and_c_collation_are_frozen() -> None:
    import hashlib

    operator = MIGRATIONS / "upgrade_paths/013a_to_013b_evaluation_assurance_trust_integrity_v2.sql"
    payload = operator.read_text(encoding="utf-8")
    assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == (FROZEN_013B_OPERATOR_V2_CHECKSUM)
    assert payload.count("E'\\n' ORDER BY") == 4
    assert payload.count('COLLATE pg_catalog."C"') == 7


def test_013h_operator_direct_ledger_and_fixture_sources_are_frozen() -> None:
    import hashlib

    direct = MIGRATIONS / "013h_idempotency_retention_integrity.sql"
    operator = (
        MIGRATIONS
        / "upgrade_paths"
        / "013g_to_013h_idempotency_retention_integrity.sql"
    )
    fixture = (
        MIGRATIONS
        / "fixtures"
        / "013h_idempotency_retention_integrity.sqlite.sql"
    )
    frozen = next(
        item
        for item in FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key
        == "013g-to-013h-idempotency-retention-integrity-v1"
    )
    operator_source = operator.read_text(encoding="utf-8")

    assert hashlib.sha256(direct.read_bytes()).hexdigest() == frozen.checksum
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == (
        FROZEN_013H_OPERATOR_CHECKSUM
    )
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (
        FROZEN_SQLITE_013H_FIXTURE_CHECKSUM
    )
    assert "\\ir ../013h_idempotency_retention_integrity.sql" in operator_source
    assert frozen.ledger_key in operator_source
    assert frozen.checksum in operator_source


def test_013i_operator_direct_ledger_and_fixture_sources_are_frozen() -> None:
    import hashlib

    direct = MIGRATIONS / "013i_imported_evidence_delivery_integrity.sql"
    operator = (
        MIGRATIONS
        / "upgrade_paths"
        / "013h_to_013i_imported_evidence_delivery_integrity.sql"
    )
    fixture = (
        MIGRATIONS
        / "fixtures"
        / "013i_imported_evidence_delivery_integrity.sqlite.sql"
    )
    frozen = next(
        item
        for item in FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key
        == "013h-to-013i-imported-evidence-delivery-integrity-v1"
    )
    operator_source = operator.read_text(encoding="utf-8")

    assert hashlib.sha256(direct.read_bytes()).hexdigest() == frozen.checksum
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == (
        FROZEN_013I_OPERATOR_CHECKSUM
    )
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (
        FROZEN_SQLITE_013I_FIXTURE_CHECKSUM
    )
    assert "\\ir ../013i_imported_evidence_delivery_integrity.sql" in operator_source
    assert frozen.ledger_key in operator_source
    assert frozen.checksum in operator_source


def test_013j_operator_direct_ledger_and_fixture_sources_are_frozen() -> None:
    import hashlib

    direct = MIGRATIONS / "013j_owner_decision_override_integrity.sql"
    operator = MIGRATIONS / POSTGRES_013J_OPERATOR
    fixture = (
        MIGRATIONS
        / "fixtures"
        / "013j_owner_decision_override_integrity.sqlite.sql"
    )
    frozen = next(
        item
        for item in FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key
        == "013i-to-013j-owner-decision-override-integrity-v1"
    )
    operator_source = operator.read_text(encoding="utf-8")

    assert hashlib.sha256(direct.read_bytes()).hexdigest() == frozen.checksum
    assert hashlib.sha256(operator.read_bytes()).hexdigest() == getattr(
        migration_integrity,
        "FROZEN_013J_OPERATOR_CHECKSUM",
    )
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == getattr(
        migration_integrity,
        "FROZEN_SQLITE_013J_FIXTURE_CHECKSUM",
    )
    assert operator_source.count(
        "\\ir ../013j_owner_decision_override_integrity.sql"
    ) == 1
    assert frozen.ledger_key in operator_source
    assert frozen.checksum in operator_source


def test_013j_catalog_manifest_covers_owner_authority_and_guards() -> None:
    assert {"organizations", "org_members", "org_roles"} <= (
        POSTGRESQL_ASSURANCE_CATALOG_SPEC.relations
    )
    assert {
        "fairmind_owner_permission_array_is_valid_013j",
        "fairmind_owner_decision_override_authorized_013j",
        "fairmind_validate_owner_override_audit_013j",
    } <= POSTGRESQL_ASSURANCE_FUNCTIONS
    assert {
        "governance_evidence_reviews_guard_insert",
        "governance_evaluation_decisions_guard_insert",
        "governance_evaluation_decisions_owner_override_audit_013j",
    } <= POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS
    assert {
        "governance_evidence_reviews_separation_guard_013j",
        "governance_evaluation_decisions_owner_override_unavailable_013j",
    } <= SQLITE_ASSURANCE_TRIGGERS


def test_sqlite_startup_check_accepts_the_frozen_013f_catalog(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        verify_sqlite_assurance_schema(connection)


def test_sqlite_startup_check_rejects_fixture_source_checksum_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    monkeypatch.setattr(
        "config.migration_integrity.FROZEN_SQLITE_013C_FIXTURE_CHECKSUM",
        "0" * 64,
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        with pytest.raises(
            MigrationIntegrityError,
            match="bundled fixture checksum drift",
        ):
            verify_sqlite_assurance_schema(connection)


def test_sqlite_startup_check_rejects_names_with_empty_tables_and_noop_guards() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        for table_name in sorted(SQLITE_ASSURANCE_TABLES):
            connection.exec_driver_sql(f'CREATE TABLE "{table_name}" (id TEXT PRIMARY KEY)')
        anchor = sorted(SQLITE_ASSURANCE_TABLES)[0]
        for index_name in sorted(SQLITE_ASSURANCE_INDEXES):
            connection.exec_driver_sql(f'CREATE INDEX "{index_name}" ON "{anchor}" (id)')
        for trigger_name in sorted(SQLITE_ASSURANCE_TRIGGERS):
            connection.exec_driver_sql(
                f'CREATE TRIGGER "{trigger_name}" BEFORE UPDATE ON "{anchor}" '
                "BEGIN SELECT 1; END"
            )
        for view_name in sorted(SQLITE_ASSURANCE_VIEWS):
            connection.exec_driver_sql(f'CREATE VIEW "{view_name}" AS SELECT id FROM "{anchor}"')

        with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
            verify_sqlite_assurance_schema(connection)


def test_sqlite_startup_check_requires_foreign_key_enforcement(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
        with pytest.raises(MigrationIntegrityError, match="foreign_keys must be enabled"):
            verify_sqlite_assurance_schema(connection)


def test_sqlite_startup_check_rejects_noop_replacement_of_real_guard(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        connection.exec_driver_sql("DROP TRIGGER governance_evaluation_decisions_no_delete")
        connection.exec_driver_sql(
            "CREATE TRIGGER governance_evaluation_decisions_no_delete "
            "BEFORE DELETE ON governance_evaluation_decisions "
            "BEGIN SELECT 1; END"
        )
        with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
            verify_sqlite_assurance_schema(connection)


def test_sqlite_startup_check_rejects_hostile_eligibility_view_replacement(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        connection.exec_driver_sql("DROP VIEW governance_evidence_admission_v2_current_eligibility")
        connection.exec_driver_sql(
            "CREATE VIEW governance_evidence_admission_v2_current_eligibility "
            "AS SELECT id AS admission_id FROM governance_evidence_admissions"
        )
        with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
            verify_sqlite_assurance_schema(connection)


@pytest.mark.parametrize(
    "table_name",
    (
        "governance_idempotency_records",
        "governance_evidence_admission_013b_replay_state",
        "governance_evidence_admission_013b_replay_anchor",
        "governance_evidence_verification_receipts",
    ),
)
def test_sqlite_startup_check_rejects_missing_assurance_authority_table(
    tmp_path: Path,
    table_name: str,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        connection.exec_driver_sql(f'DROP TABLE "{table_name}"')
        with pytest.raises(MigrationIntegrityError, match="missing required tables"):
            verify_sqlite_assurance_schema(connection)


@pytest.mark.parametrize(
    "trigger_name",
    (
        "governance_evidence_reviews_guard_insert",
        "governance_evidence_admission_replay_state_conflict",
        "governance_evidence_admission_replay_state_no_update",
        "governance_evidence_admission_replay_state_no_delete",
        "governance_evidence_admission_replay_anchor_conflict",
        "governance_evidence_admission_replay_anchor_no_update",
        "governance_evidence_admission_replay_anchor_no_delete",
        "governance_evidence_admissions_require_receipt_013c",
        "governance_evidence_verification_receipts_guard_insert",
    ),
)
def test_sqlite_startup_check_rejects_missing_evidence_authority_guard(
    tmp_path: Path,
    trigger_name: str,
) -> None:
    database_path = tmp_path / "assurance.sqlite3"
    _install_sqlite_assurance_chain(database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        connection.exec_driver_sql(f'DROP TRIGGER "{trigger_name}"')
        with pytest.raises(MigrationIntegrityError, match="missing required triggers"):
            verify_sqlite_assurance_schema(connection)


def test_startup_verifier_is_disabled_explicitly_and_rejects_unknown_dialect() -> None:
    class UnknownDialect:
        name = "mysql"

    class UnknownEngine:
        dialect = UnknownDialect()

    verify_assurance_migration_integrity(UnknownEngine(), enabled=False)
    with pytest.raises(MigrationIntegrityError, match="unsupported database dialect"):
        verify_assurance_migration_integrity(UnknownEngine(), enabled=True)


def test_disabled_postgresql_startup_does_not_connect() -> None:
    class PostgreSQLDialect:
        name = "postgresql"

    class PostgreSQLEngine:
        dialect = PostgreSQLDialect()

        def connect(self):
            pytest.fail("disabled assurance verification must not connect")

    verify_assurance_migration_integrity(PostgreSQLEngine(), enabled=False)


def test_postgresql_startup_verifies_path_ledger_then_frozen_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import migration_integrity as migration_module

    events: list[str] = []

    class PostgreSQLDialect:
        name = "postgresql"

    class Connection:
        def __enter__(self):
            events.append("connect")
            return self

        def __exit__(self, *_args):
            events.append("disconnect")

    class PostgreSQLEngine:
        dialect = PostgreSQLDialect()

        def connect(self):
            return Connection()

    monkeypatch.setattr(
        migration_module,
        "verify_bundled_migration_checksums",
        lambda: events.append("bundled"),
    )
    monkeypatch.setattr(
        migration_module,
        "_assert_postgresql_runtime_search_path",
        lambda _connection, schema: events.append(f"path:{schema}"),
    )
    monkeypatch.setattr(
        migration_module,
        "verify_postgresql_migration_ledger",
        lambda _connection, *, trusted_schema: events.append(f"ledger:{trusted_schema}"),
    )

    def verify_catalog(
        _connection,
        *,
        trusted_schema: str,
        frozen_by_major,
    ) -> None:
        assert frozen_by_major is FROZEN_POSTGRESQL_ASSURANCE_CATALOGS
        events.append(f"catalog:{trusted_schema}")

    monkeypatch.setattr(
        migration_module,
        "verify_postgresql_assurance_catalog",
        verify_catalog,
    )

    verify_assurance_migration_integrity(
        PostgreSQLEngine(),
        enabled=True,
        postgresql_schema="trusted",
    )

    assert events == [
        "bundled",
        "connect",
        "path:trusted",
        "ledger:trusted",
        "catalog:trusted",
        "disconnect",
    ]


@pytest.mark.anyio
async def test_database_initialization_invokes_enabled_assurance_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import database as database_module

    class FakeDatabase:
        instances: list["FakeDatabase"] = []

        def __init__(self, _url: str, **_kwargs) -> None:
            self.is_connected = False
            self.statements: list[str] = []
            self.__class__.instances.append(self)

        async def connect(self) -> None:
            self.is_connected = True

        async def execute(self, statement: str) -> None:
            self.statements.append(statement)

        async def disconnect(self) -> None:
            self.is_connected = False

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module.settings, "database_url", "sqlite:///:memory:")
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", True)

    manager = database_module.DatabaseManager()
    monkeypatch.setattr(
        database_module,
        "_get_repository_database_manager",
        lambda: type("RepositoryManager", (), {"engine": manager.engine})(),
    )
    with pytest.raises(MigrationIntegrityError, match="missing required tables"):
        await manager.initialize()
    assert FakeDatabase.instances[0].statements == ["PRAGMA foreign_keys = ON"]
    assert not FakeDatabase.instances[0].is_connected
    assert manager.database is None
    assert manager.engine is None


@pytest.mark.anyio
async def test_database_initialization_failure_closes_every_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import database as database_module

    events: list[str] = []

    class FakeDatabase:
        def __init__(self, _url: str, **_kwargs) -> None:
            pass

        async def connect(self) -> None:
            events.append("database.connect")

        async def disconnect(self) -> None:
            events.append("database.disconnect")

    class FakePool:
        async def close(self) -> None:
            events.append("pool.close")

    class FakeDialect:
        name = "postgresql"

    class FakeEngine:
        dialect = FakeDialect()

        def dispose(self) -> None:
            events.append("engine.dispose")

    async def fake_create_pool(*_args, **_kwargs):
        return FakePool()

    def fail_integrity(*_args, **_kwargs) -> None:
        raise MigrationIntegrityError("forced integrity failure")

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(database_module, "create_engine", lambda *_a, **_k: FakeEngine())
    monkeypatch.setattr(database_module, "bind_postgresql_engine_search_path", lambda *_args: None)
    monkeypatch.setattr(database_module, "verify_database_identities", lambda *_args: None)
    monkeypatch.setattr(
        database_module,
        "_get_repository_database_manager",
        lambda: type("RepositoryManager", (), {"engine": FakeEngine()})(),
    )
    monkeypatch.setattr(database_module, "verify_assurance_migration_integrity", fail_integrity)
    monkeypatch.setattr(
        database_module.settings,
        "database_url",
        "postgresql://user:password@localhost/fairmind",
    )
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(database_module.settings, "assurance_migration_schema", "trusted")

    manager = database_module.DatabaseManager()
    with pytest.raises(MigrationIntegrityError, match="forced integrity failure"):
        await manager.initialize()

    assert events == [
        "database.connect",
        "engine.dispose",
        "database.disconnect",
        "pool.close",
    ]
    assert manager.database is None
    assert manager._pool is None
    assert manager.engine is None
    assert manager.SessionLocal is None


@pytest.mark.anyio
async def test_postgresql_runtime_families_receive_one_fixed_search_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import database as database_module

    database_options: dict[str, object] = {}
    pool_options: dict[str, object] = {}
    bound_engines: list[tuple[object, str]] = []
    verified_engines: list[object] = []

    class FakeDatabase:
        def __init__(self, _url: str, **options) -> None:
            database_options.update(options)

        async def connect(self) -> None:
            pass

        async def disconnect(self) -> None:
            pass

    class FakePool:
        async def close(self) -> None:
            pass

    class FakeDialect:
        name = "postgresql"

    class FakeUrl:
        def render_as_string(self, hide_password: bool = True) -> str:
            assert hide_password
            return "postgresql://assurance@db/fairmind"

    class FakeEngine:
        dialect = FakeDialect()
        url = FakeUrl()

        def dispose(self) -> None:
            pass

    primary_engine = FakeEngine()
    repository_engine = FakeEngine()

    class FakeRepositoryManager:
        engine = repository_engine

    async def fake_create_pool(*_args, **options):
        pool_options.update(options)
        return FakePool()

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(database_module, "create_engine", lambda *_a, **_k: primary_engine)
    monkeypatch.setattr(
        database_module,
        "bind_postgresql_engine_search_path",
        lambda engine, schema: bound_engines.append((engine, schema)),
    )
    monkeypatch.setattr(
        database_module,
        "verify_database_identities",
        lambda *_identities: None,
    )
    monkeypatch.setattr(
        database_module,
        "verify_assurance_migration_integrity",
        lambda engine, **_kwargs: verified_engines.append(engine),
    )
    monkeypatch.setattr(
        database_module,
        "_get_repository_database_manager",
        lambda: FakeRepositoryManager(),
    )
    monkeypatch.setattr(
        database_module.settings,
        "database_url",
        "postgresql://assurance:secret@db/fairmind",
    )
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(database_module.settings, "assurance_migration_schema", "trusted")

    manager = database_module.DatabaseManager()
    try:
        await manager.initialize()
    finally:
        await manager.disconnect()

    expected_path = 'pg_catalog,"trusted",pg_temp'
    assert database_options["server_settings"] == {"search_path": expected_path}
    assert pool_options["server_settings"] == {"search_path": expected_path}
    assert bound_engines == [
        (primary_engine, "trusted"),
        (repository_engine, "trusted"),
    ]
    assert verified_engines == [primary_engine, repository_engine]


@pytest.mark.anyio
async def test_disabled_v2_preserves_legacy_postgresql_startup_without_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config import database as database_module

    database_options: dict[str, object] = {}
    pool_options: dict[str, object] = {}

    class FakeDatabase:
        def __init__(self, _url: str, **options) -> None:
            database_options.update(options)

        async def connect(self) -> None:
            pass

        async def disconnect(self) -> None:
            pass

    class FakePool:
        async def close(self) -> None:
            pass

    class FakeDialect:
        name = "postgresql"

    class FakeEngine:
        dialect = FakeDialect()

        def dispose(self) -> None:
            pass

    async def fake_create_pool(*_args, **options):
        pool_options.update(options)
        return FakePool()

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(database_module, "create_engine", lambda *_args, **_kwargs: FakeEngine())
    monkeypatch.setattr(
        database_module,
        "bind_postgresql_engine_search_path",
        lambda *_args: pytest.fail("disabled v2 must not bind a trusted schema"),
    )
    monkeypatch.setattr(
        database_module,
        "_get_repository_database_manager",
        lambda: pytest.fail("disabled v2 must not resolve the v2 repository engine"),
    )
    monkeypatch.setattr(
        database_module.settings,
        "database_url",
        "postgresql://legacy:secret@localhost/fairmind",
    )
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(database_module.settings, "assurance_migration_schema", None)

    manager = database_module.DatabaseManager()
    try:
        await manager.initialize()
    finally:
        await manager.disconnect()

    assert "server_settings" not in database_options
    assert "server_settings" not in pool_options


def test_repository_postgresql_binding_tracks_the_v2_feature_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from database import connection as repository_database_module

    class FakeEngine:
        pass

    created_engines: list[FakeEngine] = []
    bound: list[tuple[FakeEngine, str]] = []

    def fake_create_engine(*_args, **_kwargs) -> FakeEngine:
        engine = FakeEngine()
        created_engines.append(engine)
        return engine

    monkeypatch.setattr(repository_database_module, "create_engine", fake_create_engine)
    monkeypatch.setattr(
        repository_database_module,
        "bind_postgresql_engine_search_path",
        lambda engine, schema: bound.append((engine, schema)),
    )
    monkeypatch.setattr(repository_database_module.settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(repository_database_module.settings, "assurance_migration_schema", None)
    repository_database_module.DatabaseManager(
        database_url="postgresql://legacy:secret@localhost/fairmind"
    )
    assert bound == []

    monkeypatch.setattr(repository_database_module.settings, "assurance_v2_enabled", True)
    repository_database_module.DatabaseManager(
        database_url="postgresql://assurance:secret@localhost/fairmind",
        trusted_schema="trusted",
    )
    assert bound == [(created_engines[-1], "trusted")]


@pytest.mark.anyio
async def test_database_initialization_sanitizes_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from config import database as database_module

    secret = "postgresql://runtime-user:do-not-log@db.internal/fairmind"

    class FakeDatabase:
        def __init__(self, _url: str, **_options) -> None:
            pass

        async def connect(self) -> None:
            raise RuntimeError(secret)

        async def disconnect(self) -> None:
            pass

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module.settings, "database_url", "sqlite:///:memory:")
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", False)

    manager = database_module.DatabaseManager()
    with pytest.raises(RuntimeError) as caught:
        await manager.initialize()

    assert str(caught.value) == "Database initialization failed"
    assert secret not in str(caught.value)
    assert secret not in caplog.text


@pytest.mark.anyio
async def test_sqlite_v2_startup_rejects_a_different_repository_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from config import database as database_module

    primary_path = tmp_path / "primary.sqlite3"
    repository_path = tmp_path / "repository.sqlite3"

    class FakeDatabase:
        def __init__(self, _url: str, **_options) -> None:
            self.is_connected = False

        async def connect(self) -> None:
            self.is_connected = True

        async def execute(self, _statement: str) -> None:
            pass

        async def disconnect(self) -> None:
            self.is_connected = False

    class FakeDialect:
        name = "sqlite"

    class FakeEngine:
        dialect = FakeDialect()

        def __init__(self, url: str) -> None:
            self.url = url

        def dispose(self) -> None:
            pass

    primary_engine = FakeEngine(f"sqlite:///{primary_path}")
    repository_engine = FakeEngine(f"sqlite:///{repository_path}")

    class FakeRepositoryManager:
        engine = repository_engine

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.setattr(database_module, "create_engine", lambda *_args, **_kwargs: primary_engine)
    monkeypatch.setattr(database_module.event, "listen", lambda *_args: None)
    monkeypatch.setattr(
        database_module, "_get_repository_database_manager", lambda: FakeRepositoryManager()
    )
    monkeypatch.setattr(
        database_module, "verify_assurance_migration_integrity", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(database_module.settings, "database_url", f"sqlite:///{primary_path}")
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", True)

    manager = database_module.DatabaseManager()
    with pytest.raises(
        MigrationIntegrityError,
        match="^SQLite runtime database identities differ$",
    ):
        await manager.initialize()
    assert not FakeDatabase.__dict__.get("is_connected", False)
    assert manager.database is None
    assert manager.engine is None


@pytest.mark.anyio
async def test_async_sqlite_enforces_foreign_keys_on_every_acquired_connection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The databases SQLite backend opens and closes a connection per query."""
    from config import database as database_module

    database_path = tmp_path / "async-foreign-keys.sqlite3"
    monkeypatch.setattr(
        database_module.settings,
        "database_url",
        f"sqlite:///{database_path}",
    )
    monkeypatch.setattr(database_module.settings, "assurance_v2_enabled", False)

    manager = database_module.DatabaseManager()
    try:
        await manager.initialize()
        assert manager.database is not None
        await manager.database.execute("CREATE TABLE async_fk_parent (id TEXT PRIMARY KEY)")
        await manager.database.execute(
            "CREATE TABLE async_fk_child ("
            "id TEXT PRIMARY KEY, parent_id TEXT NOT NULL, "
            "FOREIGN KEY (parent_id) REFERENCES async_fk_parent(id))"
        )
        with pytest.raises(Exception, match="FOREIGN KEY constraint failed"):
            await manager.database.execute(
                "INSERT INTO async_fk_child (id, parent_id) " "VALUES ('child-a', 'missing-parent')"
            )
    finally:
        await manager.disconnect()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_non_c_locale_013b_v2_uses_exact_frozen_prerequisites() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013b_v2_{uuid.uuid4().hex[:12]}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT datcollate FROM pg_catalog.pg_database "
                "WHERE datname = pg_catalog.current_database()"
            )
            database_collation = str(cursor.fetchone()[0])
        if database_collation in {"C", "POSIX"}:
            pytest.skip("requires a native PostgreSQL database with non-C collation")

        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN[:2]:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr

        before = _postgresql_013b_prerequisite_definitions(
            connection,
            schema_name=schema_name,
        )
        first = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_OPERATOR_CHAIN[2],
        )
        assert first.returncode == 0, first.stderr
        replay = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_OPERATOR_CHAIN[2],
        )
        assert replay.returncode == 0, replay.stderr
        after = _postgresql_013b_prerequisite_definitions(
            connection,
            schema_name=schema_name,
            expected=POSTGRESQL_013B_RETAINED_PREREQUISITE_CONSTRAINTS,
        )

        assert after == {
            key: before[key] for key in POSTGRESQL_013B_RETAINED_PREREQUISITE_CONSTRAINTS
        }
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT migration_checksum FROM {}."
                    "fairmind_operator_migration_ledger "
                    "WHERE migration_key = "
                    "'013a-to-013b-evaluation-assurance-trust-integrity-v1'"
                ).format(sql.Identifier(schema_name))
            )
            assert cursor.fetchone() == (
                "d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f",
            )
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_production_catalog_freeze_matches_two_operator_installs_and_tamper_fails() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schemas = [f"fm_freeze_{uuid.uuid4().hex[:12]}" for _ in range(2)]
    engines = []
    digests: list[str] = []
    try:
        for ordinal, schema_name in enumerate(schemas):
            _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
            for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
                result = _run_postgresql_operator_migration(
                    POSTGRES_URL,
                    schema_name,
                    migration_name,
                )
                assert result.returncode == 0, result.stderr
            if ordinal == 0:
                replay = _run_postgresql_operator_migration(
                    POSTGRES_URL,
                    schema_name,
                    POSTGRES_013J_OPERATOR,
                )
                assert replay.returncode == 0, replay.stderr

            engine = create_engine(POSTGRES_URL)
            bind_postgresql_engine_search_path(engine, schema_name)
            engines.append(engine)
            verify_assurance_migration_integrity(
                engine,
                enabled=True,
                postgresql_schema=schema_name,
            )
            with engine.connect() as connection:
                digests.append(
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=schema_name,
                        spec=POSTGRESQL_ASSURANCE_CATALOG_SPEC,
                    )
                )

        frozen = FROZEN_POSTGRESQL_ASSURANCE_CATALOGS[14]
        assert digests == [frozen.digest, frozen.digest]

        with engines[0].begin() as connection:
            connection.exec_driver_sql(
                f'CREATE OR REPLACE FUNCTION "{schemas[0]}".'
                "reject_governance_evaluation_013b_mutation() "
                "RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER "
                f'SET search_path TO pg_catalog, "{schemas[0]}", pg_temp '
                "AS $$ BEGIN RETURN NEW; END $$"
            )
        with pytest.raises(
            MigrationIntegrityError,
            match="catalog definition drift",
        ):
            verify_assurance_migration_integrity(
                engines[0],
                enabled=True,
                postgresql_schema=schemas[0],
            )
    finally:
        for engine in engines:
            engine.dispose()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                for schema_name in schemas:
                    cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema_name)
                        )
                    )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013j_operator_accepts_exact_replay_and_rejects_ledger_tamper() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013j_ledger_{uuid.uuid4().hex[:12]}"
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr

        replay = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_013J_OPERATOR,
        )
        assert replay.returncode == 0, replay.stderr

        connection = psycopg2.connect(POSTGRES_URL)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "UPDATE {}.fairmind_operator_migration_ledger "
                        "SET migration_checksum = %s WHERE migration_key = %s"
                    ).format(sql.Identifier(schema_name)),
                    (
                        "0" * 64,
                        "013i-to-013j-owner-decision-override-integrity-v1",
                    ),
                )
        finally:
            connection.close()

        tampered = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_013J_OPERATOR,
        )
        assert tampered.returncode != 0
        assert "checksum drift for 013i-to-013j" in tampered.stderr
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013j_operator_requires_the_exact_frozen_013i_prerequisite() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    missing_schema = f"fm_013j_missing_{uuid.uuid4().hex[:12]}"
    drift_schema = f"fm_013j_prereq_{uuid.uuid4().hex[:12]}"
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, missing_schema)
        for migration_name in POSTGRES_OPERATOR_CHAIN[:-1]:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                missing_schema,
                migration_name,
            )
            assert result.returncode == 0, result.stderr
        missing = _run_postgresql_operator_migration(
            POSTGRES_URL,
            missing_schema,
            POSTGRES_013J_OPERATOR,
        )
        assert missing.returncode != 0
        assert "prerequisite ledger row 013h-to-013i" in missing.stderr

        _install_postgresql_base_through_012(POSTGRES_URL, drift_schema)
        for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                drift_schema,
                migration_name,
            )
            assert result.returncode == 0, result.stderr
        connection = psycopg2.connect(POSTGRES_URL)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "UPDATE {}.fairmind_operator_migration_ledger "
                        "SET migration_checksum = %s WHERE migration_key = %s"
                    ).format(sql.Identifier(drift_schema)),
                    (
                        "0" * 64,
                        "013h-to-013i-imported-evidence-delivery-integrity-v1",
                    ),
                )
        finally:
            connection.close()
        drift = _run_postgresql_operator_migration(
            POSTGRES_URL,
            drift_schema,
            POSTGRES_013J_OPERATOR,
        )
        assert drift.returncode != 0
        assert "prerequisite checksum drift for migration 013i" in drift.stderr
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                for schema_name in (missing_schema, drift_schema):
                    cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema_name)
                        )
                    )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013j_operator_orphan_rejection_is_schema_scoped() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    orphan_schema = f"fm_013j_orphan_{uuid.uuid4().hex[:12]}"
    clean_schema = f"fm_013j_clean_{uuid.uuid4().hex[:12]}"
    try:
        for schema_name in (orphan_schema, clean_schema):
            _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
            for migration_name in POSTGRES_OPERATOR_CHAIN:
                result = _run_postgresql_operator_migration(
                    POSTGRES_URL,
                    schema_name,
                    migration_name,
                )
                assert result.returncode == 0, result.stderr

        connection = psycopg2.connect(POSTGRES_URL)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "CREATE FUNCTION {}.fairmind_owner_permission_array_is_valid_013j(jsonb) "
                        "RETURNS boolean LANGUAGE sql IMMUTABLE AS 'SELECT false'"
                    ).format(sql.Identifier(orphan_schema))
                )
        finally:
            connection.close()

        rejected = _run_postgresql_operator_migration(
            POSTGRES_URL,
            orphan_schema,
            POSTGRES_013J_OPERATOR,
        )
        assert rejected.returncode != 0
        assert "preexisting 013j catalog exists without its immutable ledger row" in (
            rejected.stderr
        )

        installed = _run_postgresql_operator_migration(
            POSTGRES_URL,
            clean_schema,
            POSTGRES_013J_OPERATOR,
        )
        assert installed.returncode == 0, installed.stderr
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                for schema_name in (orphan_schema, clean_schema):
                    cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema_name)
                        )
                    )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013j_startup_rejects_every_missing_or_disabled_guard() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013j_startup_{uuid.uuid4().hex[:12]}"
    engine = None
    guards = (
        ("governance_evidence_reviews", "governance_evidence_reviews_guard_insert"),
        (
            "governance_evaluation_decisions",
            "governance_evaluation_decisions_guard_insert",
        ),
        (
            "governance_evaluation_decisions",
            "governance_evaluation_decisions_owner_override_audit_013j",
        ),
    )
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr

        engine = create_engine(POSTGRES_URL)
        bind_postgresql_engine_search_path(engine, schema_name)
        verify_assurance_migration_integrity(
            engine,
            enabled=True,
            postgresql_schema=schema_name,
        )
        for relation_name, trigger_name in guards:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    f'ALTER TABLE "{relation_name}" DISABLE TRIGGER "{trigger_name}"'
                )
            with pytest.raises(
                MigrationIntegrityError,
                match="disabled required triggers",
            ):
                verify_assurance_migration_integrity(
                    engine,
                    enabled=True,
                    postgresql_schema=schema_name,
                )
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    f'ALTER TABLE "{relation_name}" ENABLE ALWAYS TRIGGER "{trigger_name}"'
                )

            with engine.begin() as connection:
                connection.exec_driver_sql(
                    f'DROP TRIGGER "{trigger_name}" ON "{relation_name}"'
                )
            with pytest.raises(
                MigrationIntegrityError,
                match="missing required triggers",
            ):
                verify_assurance_migration_integrity(
                    engine,
                    enabled=True,
                    postgresql_schema=schema_name,
                )
            replay = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                POSTGRES_013J_OPERATOR,
            )
            assert replay.returncode == 0, replay.stderr
    finally:
        if engine is not None:
            engine.dispose()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013j_catalog_rejects_function_acl_relation_and_trigger_drift() -> None:
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013j_drift_{uuid.uuid4().hex[:12]}"
    owner_role = f"fm_013j_owner_{uuid.uuid4().hex[:12]}"
    engine = None
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr

        engine = create_engine(POSTGRES_URL)
        bind_postgresql_engine_search_path(engine, schema_name)
        cases = (
            (
                "function body",
                (
                    "CREATE OR REPLACE FUNCTION "
                    f'"{schema_name}".fairmind_owner_permission_array_is_valid_013j('
                    "p_permissions JSONB) RETURNS BOOLEAN LANGUAGE plpgsql IMMUTABLE "
                    "SECURITY INVOKER "
                    f'SET search_path TO pg_catalog, "{schema_name}", pg_temp '
                    "AS 'BEGIN RETURN false; END;'"
                ),
                "catalog definition drift",
            ),
            (
                "function search path",
                "ALTER FUNCTION fairmind_owner_permission_array_is_valid_013j(JSONB) "
                "SET search_path TO pg_catalog",
                "fixed search_path",
            ),
            (
                "function owner",
                f'CREATE ROLE "{owner_role}" NOLOGIN; '
                "ALTER FUNCTION fairmind_owner_permission_array_is_valid_013j(JSONB) "
                f'OWNER TO "{owner_role}"',
                "function ownership invariant",
            ),
            (
                "function ACL",
                "REVOKE EXECUTE ON FUNCTION "
                "fairmind_owner_permission_array_is_valid_013j(JSONB) FROM PUBLIC",
                "catalog definition drift",
            ),
            (
                "relation ACL",
                "GRANT SELECT ON TABLE org_roles TO PUBLIC",
                "catalog definition drift",
            ),
            (
                "trigger state",
                "ALTER TABLE governance_evidence_reviews DISABLE TRIGGER "
                "governance_evidence_reviews_guard_insert",
                "disabled required triggers",
            ),
        )
        with engine.connect() as connection:
            baseline = postgresql_assurance_catalog_digest(
                connection,
                trusted_schema=schema_name,
            )
            assert baseline == FROZEN_POSTGRESQL_ASSURANCE_CATALOGS[14].digest
            connection.commit()
            for case_name, statement, message in cases:
                transaction = connection.begin()
                try:
                    connection.exec_driver_sql(statement)
                    try:
                        verify_postgresql_assurance_catalog(
                            connection,
                            trusted_schema=schema_name,
                            frozen_by_major=FROZEN_POSTGRESQL_ASSURANCE_CATALOGS,
                        )
                    except MigrationIntegrityError as error:
                        assert message in str(error), case_name
                    else:
                        pytest.fail(f"{case_name} drift was accepted")
                finally:
                    transaction.rollback()
                assert postgresql_assurance_catalog_digest(
                    connection,
                    trusted_schema=schema_name,
                ) == baseline
                connection.commit()
    finally:
        if engine is not None:
            engine.dispose()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
                cursor.execute(
                    sql.SQL("DROP ROLE IF EXISTS {}").format(
                        sql.Identifier(owner_role)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013g_operator_orphan_check_is_schema_scoped() -> None:
    """A recorded 013g catalog in one schema cannot block another schema's install."""
    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    first_schema, second_schema = (
        f"fm_013g_scope_{uuid.uuid4().hex[:12]}",
        f"fm_013g_scope_{uuid.uuid4().hex[:12]}",
    )
    try:
        for schema_name in (first_schema, second_schema):
            _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
            for migration_name in POSTGRES_OPERATOR_CHAIN[:-1]:
                result = _run_postgresql_operator_migration(
                    POSTGRES_URL, schema_name, migration_name
                )
                assert result.returncode == 0, result.stderr

        first = _run_postgresql_operator_migration(
            POSTGRES_URL, first_schema, POSTGRES_OPERATOR_CHAIN[-1]
        )
        assert first.returncode == 0, first.stderr
        second = _run_postgresql_operator_migration(
            POSTGRES_URL, second_schema, POSTGRES_OPERATOR_CHAIN[-1]
        )
        assert second.returncode == 0, second.stderr
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                for schema_name in (first_schema, second_schema):
                    cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema_name)
                        )
                    )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013i_operator_rejects_ledger_tamper() -> None:
    """An exact replay succeeds, but a changed 013i ledger row cannot be adopted."""

    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013i_ledger_{uuid.uuid4().hex[:12]}"
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr
        replay = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_OPERATOR_CHAIN[-1],
        )
        assert replay.returncode == 0, replay.stderr

        connection = psycopg2.connect(POSTGRES_URL)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "UPDATE {}.fairmind_operator_migration_ledger "
                        "SET migration_checksum = %s WHERE migration_key = %s"
                    ).format(sql.Identifier(schema_name)),
                    (
                        "0" * 64,
                        "013h-to-013i-imported-evidence-delivery-integrity-v1",
                    ),
                )
        finally:
            connection.close()
        tampered = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_OPERATOR_CHAIN[-1],
        )
        assert tampered.returncode != 0
        assert "checksum drift for 013h-to-013i" in tampered.stderr
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013h_failed_operator_upgrade_rolls_back_catalog_and_ledger() -> None:
    """Invalid legacy state cannot leave a partly adopted 013h authority."""

    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013h_rollback_{uuid.uuid4().hex[:12]}"
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN[:-2]:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr
        connection = psycopg2.connect(POSTGRES_URL)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                        sql.Identifier(schema_name)
                    )
                )
                cursor.execute(
                    """
                    INSERT INTO governance_idempotency_records (
                        id, org_id, actor_id, operation, key_hash, request_hash,
                        status, created_at, updated_at, expires_at
                    ) VALUES (
                        'bad-operator-row', 'org-bad', 'actor-bad',
                        'evaluation.run.create', %s, %s, 'in_progress',
                        '2000-01-01T24:00:00+00:00',
                        '2000-01-01T24:00:00+00:00',
                        '2000-01-31T24:00:00+00:00'
                    )
                    """,
                    ("a" * 64, "b" * 64),
                )
        finally:
            connection.close()

        failed = _run_postgresql_operator_migration(
            POSTGRES_URL,
            schema_name,
            POSTGRES_OPERATOR_CHAIN[-2],
        )
        assert failed.returncode != 0
        assert "migration 013h found invalid idempotency records" in failed.stderr

        inspection = psycopg2.connect(POSTGRES_URL)
        inspection.autocommit = True
        try:
            with inspection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        (SELECT count(*) FROM pg_catalog.pg_proc AS p
                         JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
                         WHERE n.nspname = %s AND p.proname LIKE '%%_013h'),
                        (SELECT count(*) FROM pg_catalog.pg_trigger AS t
                         JOIN pg_catalog.pg_class AS c ON c.oid = t.tgrelid
                         JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
                         WHERE n.nspname = %s AND t.tgname =
                           'governance_idempotency_records_integrity_013h'),
                        (SELECT count(*) FROM {}.fairmind_operator_migration_ledger
                         WHERE migration_key =
                           '013g-to-013h-idempotency-retention-integrity-v1')
                    """.format(sql.Identifier(schema_name).as_string(inspection)),
                    (schema_name, schema_name),
                )
                assert cursor.fetchone() == (0, 0, 0)
        finally:
            inspection.close()
    finally:
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_013i_startup_rejects_disabled_and_missing_trigger() -> None:
    """Startup detects both live disablement and removal of the 013i authority."""

    import psycopg2
    from psycopg2 import sql

    assert POSTGRES_URL is not None
    schema_name = f"fm_013i_startup_{uuid.uuid4().hex[:12]}"
    engine = None
    try:
        _install_postgresql_base_through_012(POSTGRES_URL, schema_name)
        for migration_name in POSTGRES_OPERATOR_CHAIN_THROUGH_013J:
            result = _run_postgresql_operator_migration(
                POSTGRES_URL,
                schema_name,
                migration_name,
            )
            assert result.returncode == 0, result.stderr
        engine = create_engine(POSTGRES_URL)
        bind_postgresql_engine_search_path(engine, schema_name)
        verify_assurance_migration_integrity(
            engine,
            enabled=True,
            postgresql_schema=schema_name,
        )
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
                '"000_013i_unverified_import_delivery_guard"'
            )
        with pytest.raises(MigrationIntegrityError, match="disabled required triggers"):
            verify_assurance_migration_integrity(
                engine,
                enabled=True,
                postgresql_schema=schema_name,
            )
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE governance_evidence_admissions ENABLE ALWAYS TRIGGER "
                '"000_013i_unverified_import_delivery_guard"'
            )
        verify_assurance_migration_integrity(
            engine,
            enabled=True,
            postgresql_schema=schema_name,
        )
        with engine.begin() as connection:
            connection.exec_driver_sql(
                'DROP TRIGGER "000_013i_unverified_import_delivery_guard" '
                "ON governance_evidence_admissions"
            )
        with pytest.raises(MigrationIntegrityError, match="missing required triggers"):
            verify_assurance_migration_integrity(
                engine,
                enabled=True,
                postgresql_schema=schema_name,
            )
    finally:
        if engine is not None:
            engine.dispose()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_trusted_schema_cannot_be_shadowed() -> None:
    trusted_schema = f"fm_mi_trusted_{uuid.uuid4().hex[:12]}"
    shadow_schema = f"fm_mi_shadow_{uuid.uuid4().hex[:12]}"
    expected = (FrozenMigration("migration-a", "a" * 64, Path("a.sql")),)
    engine = create_engine(POSTGRES_URL)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{trusted_schema}"')
            connection.exec_driver_sql(f'CREATE SCHEMA "{shadow_schema}"')
            for schema in (trusted_schema, shadow_schema):
                connection.exec_driver_sql(
                    f'CREATE TABLE "{schema}".fairmind_operator_migration_ledger '
                    "(migration_key TEXT PRIMARY KEY, migration_checksum TEXT NOT NULL)"
                )
            connection.execute(
                text(
                    f'INSERT INTO "{trusted_schema}".'
                    "fairmind_operator_migration_ledger VALUES "
                    "('migration-a', :checksum)"
                ),
                {"checksum": "b" * 64},
            )
            connection.execute(
                text(
                    f'INSERT INTO "{shadow_schema}".'
                    "fairmind_operator_migration_ledger VALUES "
                    "('migration-a', :checksum)"
                ),
                {"checksum": "a" * 64},
            )
            connection.exec_driver_sql(
                f'SET LOCAL search_path TO "{shadow_schema}", "{trusted_schema}"'
            )
            with pytest.raises(MigrationIntegrityError, match="migration-a.*checksum drift"):
                verify_postgresql_migration_ledger(
                    connection,
                    trusted_schema=trusted_schema,
                    expected=expected,
                )
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{shadow_schema}" CASCADE')
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_rejects_missing_trigger_and_noop_function() -> None:
    trusted_schema = f"fm_catalog_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    spec = PostgreSQLCatalogSpec(
        relations=frozenset({"guarded_events"}),
        functions=frozenset({"guard_guarded_events"}),
        required_triggers=frozenset({"guarded_events_no_update", "guarded_events_no_delete"}),
    )
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{trusted_schema}"')
            connection.exec_driver_sql(
                f'CREATE TABLE "{trusted_schema}".guarded_events '
                "(id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            connection.exec_driver_sql(
                f'CREATE FUNCTION "{trusted_schema}".guard_guarded_events() '
                "RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER "
                f'SET search_path TO pg_catalog, "{trusted_schema}", pg_temp '
                "AS $$ BEGIN RAISE EXCEPTION 'append-only'; END $$"
            )
            for operation in ("UPDATE", "DELETE"):
                trigger = f"guarded_events_no_{operation.lower()}"
                connection.exec_driver_sql(
                    f'CREATE TRIGGER "{trigger}" BEFORE {operation} '
                    f'ON "{trusted_schema}".guarded_events FOR EACH ROW '
                    f'EXECUTE FUNCTION "{trusted_schema}".guard_guarded_events()'
                )
            digest = postgresql_assurance_catalog_digest(
                connection,
                trusted_schema=trusted_schema,
                spec=spec,
            )
            major = postgresql_server_major(connection)
            frozen = FrozenPostgreSQLCatalog(
                spec=spec,
                postgresql_major=major,
                digest=digest,
            )
            verify_postgresql_assurance_catalog(
                connection,
                trusted_schema=trusted_schema,
                frozen_by_major={major: frozen},
            )

            connection.exec_driver_sql(
                f"DROP TRIGGER guarded_events_no_delete " f'ON "{trusted_schema}".guarded_events'
            )
            with pytest.raises(MigrationIntegrityError, match="required triggers"):
                verify_postgresql_assurance_catalog(
                    connection,
                    trusted_schema=trusted_schema,
                    frozen_by_major={major: frozen},
                )
            connection.exec_driver_sql(
                f"CREATE TRIGGER guarded_events_no_delete BEFORE DELETE "
                f'ON "{trusted_schema}".guarded_events FOR EACH ROW '
                f'EXECUTE FUNCTION "{trusted_schema}".guard_guarded_events()'
            )

            connection.exec_driver_sql(
                f'CREATE OR REPLACE FUNCTION "{trusted_schema}".'
                "guard_guarded_events() RETURNS trigger LANGUAGE plpgsql "
                "VOLATILE SECURITY INVOKER "
                f'SET search_path TO pg_catalog, "{trusted_schema}", pg_temp '
                "AS $$ BEGIN RETURN NEW; END $$"
            )
            with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
                verify_postgresql_assurance_catalog(
                    connection,
                    trusted_schema=trusted_schema,
                    frozen_by_major={major: frozen},
                )
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_requires_fixed_function_search_path() -> None:
    trusted_schema = f"fm_function_path_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    spec = PostgreSQLCatalogSpec(
        relations=frozenset({"guarded_events"}),
        functions=frozenset({"guard_guarded_events"}),
        required_triggers=frozenset({"guarded_events_no_update"}),
    )
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{trusted_schema}"')
            connection.exec_driver_sql(
                f'CREATE TABLE "{trusted_schema}".guarded_events (id TEXT PRIMARY KEY)'
            )
            connection.exec_driver_sql(
                f'CREATE FUNCTION "{trusted_schema}".guard_guarded_events() '
                "RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$"
            )
            connection.exec_driver_sql(
                f"CREATE TRIGGER guarded_events_no_update BEFORE UPDATE "
                f'ON "{trusted_schema}".guarded_events FOR EACH ROW '
                f'EXECUTE FUNCTION "{trusted_schema}".guard_guarded_events()'
            )
            with pytest.raises(MigrationIntegrityError, match="fixed search_path"):
                postgresql_assurance_catalog_digest(
                    connection,
                    trusted_schema=trusted_schema,
                    spec=spec,
                )
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_normalizes_schema_and_rejects_public_create() -> None:
    schemas = [f"fm_catalog_norm_{uuid.uuid4().hex[:12]}" for _ in range(2)]
    engines = [create_engine(POSTGRES_URL) for _ in schemas]
    spec = PostgreSQLCatalogSpec(
        relations=frozenset({"guarded_events"}),
        functions=frozenset({"guard_guarded_events"}),
        required_triggers=frozenset({"guarded_events_no_update"}),
    )
    try:
        digests: list[str] = []
        for schema, engine in zip(schemas, engines, strict=True):
            bind_postgresql_engine_search_path(engine, schema)
            with engine.begin() as connection:
                connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                connection.exec_driver_sql(
                    f'CREATE TABLE "{schema}".guarded_events (id TEXT PRIMARY KEY)'
                )
                connection.exec_driver_sql(
                    f'CREATE FUNCTION "{schema}".guard_guarded_events() '
                    "RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER "
                    f'SET search_path TO pg_catalog, "{schema}", pg_temp '
                    "AS $$ BEGIN RAISE EXCEPTION 'append-only'; END $$"
                )
                connection.exec_driver_sql(
                    f"CREATE TRIGGER guarded_events_no_update BEFORE UPDATE "
                    f'ON "{schema}".guarded_events FOR EACH ROW '
                    f'EXECUTE FUNCTION "{schema}".guard_guarded_events()'
                )
                digests.append(
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=schema,
                        spec=spec,
                    )
                )

                connection.exec_driver_sql(f'GRANT CREATE ON SCHEMA "{schema}" TO PUBLIC')
                with pytest.raises(MigrationIntegrityError, match="PUBLIC CREATE"):
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=schema,
                        spec=spec,
                    )
                connection.exec_driver_sql(f'REVOKE CREATE ON SCHEMA "{schema}" FROM PUBLIC')

        assert digests[0] == digests[1]
    finally:
        cleanup_engine = create_engine(POSTGRES_URL)
        with cleanup_engine.begin() as connection:
            for schema in schemas:
                connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        cleanup_engine.dispose()
        for engine in engines:
            engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_detects_user_rewrite_rule_drift() -> None:
    trusted_schema = f"fm_rule_catalog_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    try:
        with engine.begin() as connection:
            spec = _install_minimal_postgresql_assurance_catalog(
                connection,
                schema_name=trusted_schema,
            )
            _major, baseline_digest, frozen = _freeze_native_postgresql_catalog(
                connection,
                schema_name=trusted_schema,
                spec=spec,
            )

            connection.exec_driver_sql(
                "CREATE RULE guarded_events_audit AS ON INSERT TO "
                f'"{trusted_schema}".guarded_events DO ALSO NOTHING'
            )
            added_digest = postgresql_assurance_catalog_digest(
                connection,
                trusted_schema=trusted_schema,
                spec=spec,
            )
            assert added_digest != baseline_digest
            with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
                verify_postgresql_assurance_catalog(
                    connection,
                    trusted_schema=trusted_schema,
                    frozen_by_major=frozen,
                )

            connection.exec_driver_sql(
                "DROP RULE guarded_events_audit ON " f'"{trusted_schema}".guarded_events'
            )
            connection.exec_driver_sql(
                "CREATE RULE guarded_events_audit AS ON UPDATE TO "
                f'"{trusted_schema}".guarded_events DO INSTEAD NOTHING'
            )
            changed_digest = postgresql_assurance_catalog_digest(
                connection,
                trusted_schema=trusted_schema,
                spec=spec,
            )
            assert changed_digest not in {baseline_digest, added_digest}
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_detects_schema_relation_and_function_acl_drift() -> None:
    trusted_schema = f"fm_acl_catalog_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    try:
        with engine.begin() as connection:
            spec = _install_minimal_postgresql_assurance_catalog(
                connection,
                schema_name=trusted_schema,
            )
            _major, baseline_digest, frozen = _freeze_native_postgresql_catalog(
                connection,
                schema_name=trusted_schema,
                spec=spec,
            )

            mutations = (
                f'GRANT USAGE ON SCHEMA "{trusted_schema}" TO PUBLIC',
                f'GRANT SELECT ON TABLE "{trusted_schema}".guarded_events TO PUBLIC',
                (
                    f'REVOKE EXECUTE ON FUNCTION "{trusted_schema}".'
                    "guard_guarded_events() FROM PUBLIC"
                ),
            )
            restorations = (
                f'REVOKE USAGE ON SCHEMA "{trusted_schema}" FROM PUBLIC',
                f'REVOKE SELECT ON TABLE "{trusted_schema}".guarded_events FROM PUBLIC',
                (
                    f'GRANT EXECUTE ON FUNCTION "{trusted_schema}".'
                    "guard_guarded_events() TO PUBLIC"
                ),
            )
            for mutation, restoration in zip(mutations, restorations, strict=True):
                connection.exec_driver_sql(mutation)
                assert (
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=trusted_schema,
                        spec=spec,
                    )
                    != baseline_digest
                )
                with pytest.raises(
                    MigrationIntegrityError,
                    match="catalog definition drift",
                ):
                    verify_postgresql_assurance_catalog(
                        connection,
                        trusted_schema=trusted_schema,
                        frozen_by_major=frozen,
                    )
                connection.exec_driver_sql(restoration)
                assert (
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=trusted_schema,
                        spec=spec,
                    )
                    == baseline_digest
                )
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_detects_owner_and_role_membership_authority_drift() -> None:
    trusted_schema = f"fm_owner_catalog_{uuid.uuid4().hex[:12]}"
    owner_role = f"fm_owner_{uuid.uuid4().hex[:12]}"
    member_role = f"fm_member_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE ROLE "{owner_role}" NOLOGIN')
            connection.exec_driver_sql(f'CREATE ROLE "{member_role}" NOLOGIN')
            spec = _install_minimal_postgresql_assurance_catalog(
                connection,
                schema_name=trusted_schema,
            )
            _major, original_owner_digest, _original_frozen = _freeze_native_postgresql_catalog(
                connection,
                schema_name=trusted_schema,
                spec=spec,
            )

            connection.exec_driver_sql(
                f'ALTER TABLE "{trusted_schema}".guarded_events OWNER TO "{owner_role}"'
            )
            connection.exec_driver_sql(
                f'ALTER FUNCTION "{trusted_schema}".guard_guarded_events() '
                f'OWNER TO "{owner_role}"'
            )
            connection.exec_driver_sql(f'ALTER SCHEMA "{trusted_schema}" OWNER TO "{owner_role}"')
            _major, transferred_owner_digest, transferred_frozen = (
                _freeze_native_postgresql_catalog(
                    connection,
                    schema_name=trusted_schema,
                    spec=spec,
                )
            )
            assert transferred_owner_digest != original_owner_digest

            connection.exec_driver_sql(f'GRANT "{owner_role}" TO "{member_role}"')
            assert (
                postgresql_assurance_catalog_digest(
                    connection,
                    trusted_schema=trusted_schema,
                    spec=spec,
                )
                != transferred_owner_digest
            )
            with pytest.raises(MigrationIntegrityError, match="catalog definition drift"):
                verify_postgresql_assurance_catalog(
                    connection,
                    trusted_schema=trusted_schema,
                    frozen_by_major=transferred_frozen,
                )
    finally:
        cleanup_engine = create_engine(POSTGRES_URL)
        try:
            with cleanup_engine.begin() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
                connection.exec_driver_sql(f'DROP ROLE IF EXISTS "{member_role}"')
                connection.exec_driver_sql(f'DROP ROLE IF EXISTS "{owner_role}"')
        finally:
            cleanup_engine.dispose()
            engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_catalog_normalizes_rules_and_acls_across_schema_names() -> None:
    schemas = [f"fm_authority_norm_{uuid.uuid4().hex[:12]}" for _ in range(2)]
    engines = [create_engine(POSTGRES_URL) for _ in schemas]
    try:
        digests: list[str] = []
        for schema, engine in zip(schemas, engines, strict=True):
            bind_postgresql_engine_search_path(engine, schema)
            with engine.begin() as connection:
                spec = _install_minimal_postgresql_assurance_catalog(
                    connection,
                    schema_name=schema,
                )
                connection.exec_driver_sql(f'GRANT USAGE ON SCHEMA "{schema}" TO PUBLIC')
                connection.exec_driver_sql(
                    f'GRANT SELECT ON TABLE "{schema}".guarded_events TO PUBLIC'
                )
                connection.exec_driver_sql(
                    "CREATE RULE guarded_events_audit AS ON INSERT TO "
                    f'"{schema}".guarded_events DO ALSO NOTHING'
                )
                digests.append(
                    postgresql_assurance_catalog_digest(
                        connection,
                        trusted_schema=schema,
                        spec=spec,
                    )
                )
        assert digests[0] == digests[1]
    finally:
        cleanup_engine = create_engine(POSTGRES_URL)
        with cleanup_engine.begin() as connection:
            for schema in schemas:
                connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        cleanup_engine.dispose()
        for engine in engines:
            engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)
def test_native_postgresql_checkout_blocks_default_user_and_temp_shadowing() -> None:
    trusted_schema = f"fm_runtime_{uuid.uuid4().hex[:12]}"
    hostile_schema = f"fm_hostile_{uuid.uuid4().hex[:12]}"
    engine = create_engine(POSTGRES_URL, pool_size=1, max_overflow=0)
    bind_postgresql_engine_search_path(engine, trusted_schema)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{trusted_schema}"')
            connection.exec_driver_sql(f'CREATE SCHEMA "{hostile_schema}"')
            connection.exec_driver_sql(
                f'CREATE TABLE "{trusted_schema}".critical_relation ' "(source TEXT NOT NULL)"
            )
            connection.exec_driver_sql(
                f'CREATE TABLE "{hostile_schema}".critical_relation ' "(source TEXT NOT NULL)"
            )
            connection.exec_driver_sql(
                f"INSERT INTO \"{trusted_schema}\".critical_relation VALUES ('trusted')"
            )
            connection.exec_driver_sql(
                f"INSERT INTO \"{hostile_schema}\".critical_relation VALUES ('hostile')"
            )
            connection.exec_driver_sql("CREATE TEMP TABLE critical_relation (source TEXT NOT NULL)")
            connection.exec_driver_sql("INSERT INTO pg_temp.critical_relation VALUES ('temporary')")
            connection.exec_driver_sql(f'SET search_path TO "$user", "{hostile_schema}", pg_temp')

        with engine.connect() as connection:
            assert connection.scalar(text("SELECT current_setting('search_path')")) == (
                postgresql_runtime_search_path(trusted_schema)
            )
            assert connection.scalar(text("SELECT source FROM critical_relation")) == ("trusted")
            assert connection.scalar(
                text(
                    "SELECT 'critical_relation'::regclass::oid = "
                    f"'\"{trusted_schema}\".critical_relation'::regclass::oid"
                )
            )
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{trusted_schema}" CASCADE')
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{hostile_schema}" CASCADE')
        engine.dispose()

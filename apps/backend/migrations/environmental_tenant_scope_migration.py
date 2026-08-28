"""Dialect-aware application of environmental tenant scope migration 013e."""

from __future__ import annotations

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013e_environmental_tenant_scope.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR / "fixtures" / "013e_environmental_tenant_scope.sqlite.sql"
)


def sql_for(dialect: str) -> str:
    """Return the direct 013e migration payload for a supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def _foreign_key_column_sets(connection: object) -> set[tuple[str, ...]]:
    execute = getattr(connection, "execute")
    grouped: dict[int, list[tuple[int, str]]] = {}
    for row in execute(
        "PRAGMA foreign_key_list(governance_environmental_assessments)"
    ).fetchall():
        grouped.setdefault(row[0], []).append((row[1], row[3]))
    return {
        tuple(column for _, column in sorted(columns))
        for columns in grouped.values()
    }


def _has_unique_index(
    connection: object,
    table_name: str,
    columns: tuple[str, ...],
    *,
    required_name: str | None = None,
) -> bool:
    execute = getattr(connection, "execute")
    for row in execute(f"PRAGMA index_list({table_name})").fetchall():
        index_name = row[1]
        is_unique = bool(row[2])
        if not is_unique or (required_name is not None and index_name != required_name):
            continue
        indexed_columns = tuple(
            item[2]
            for item in execute(f'PRAGMA index_info("{index_name}")').fetchall()
        )
        if indexed_columns == columns:
            return True
    return False


def _assert_sqlite_contract(connection: object) -> None:
    execute = getattr(connection, "execute")
    columns = {
        row[1]: row
        for row in execute(
            "PRAGMA table_info(governance_environmental_assessments)"
        ).fetchall()
    }
    org_column = columns.get("org_id")
    if org_column is None or org_column[3] != 1:
        raise RuntimeError("013e SQLite environmental org_id contract drifted")

    required_foreign_keys = {
        ("system_id", "org_id"),
        ("evidence_id", "system_id", "org_id"),
    }
    if not required_foreign_keys.issubset(_foreign_key_column_sets(connection)):
        raise RuntimeError("013e SQLite environmental tenant foreign keys drifted")
    if not _has_unique_index(
        connection,
        "governance_environmental_assessments",
        ("org_id", "system_id", "version"),
        required_name="idx_governance_env_assessments_org_system_version",
    ):
        raise RuntimeError("013e SQLite environmental version index drifted")
    if not _has_unique_index(
        connection,
        "governance_evidence",
        ("id", "system_id", "org_id"),
    ):
        raise RuntimeError("013e SQLite evidence tenant key drifted")

    violations = execute(
        "PRAGMA foreign_key_check(governance_environmental_assessments)"
    ).fetchall()
    if violations:
        raise RuntimeError("013e SQLite environmental foreign key check failed")


def apply_sqlite(connection: object) -> None:
    """Atomically rebuild the legacy SQLite table with enforceable tenant keys.

    A table rebuild is required because SQLite cannot add a non-null column or
    composite foreign keys to an existing table.  Existing scope is derived
    only from ``governance_ai_systems``.  Any unresolved system or linked
    evidence tuple aborts before the legacy table is replaced.
    """

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")

    foreign_keys = execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys is None or foreign_keys[0] != 1:
        raise RuntimeError("013e SQLite migration requires foreign key enforcement")

    columns = {
        row[1]
        for row in execute(
            "PRAGMA table_info(governance_environmental_assessments)"
        ).fetchall()
    }
    if "org_id" in columns:
        _assert_sqlite_contract(connection)
        return

    try:
        executescript(sql_for("sqlite"))
    except Exception:
        try:
            rollback = getattr(connection, "rollback", None)
            if callable(rollback):
                rollback()
        finally:
            execute("PRAGMA legacy_alter_table = OFF")
            execute("PRAGMA foreign_keys = ON")
        raise

    execute("PRAGMA legacy_alter_table = OFF")
    foreign_keys = execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys is None or foreign_keys[0] != 1:
        raise RuntimeError("013e SQLite migration did not restore foreign key enforcement")
    _assert_sqlite_contract(connection)

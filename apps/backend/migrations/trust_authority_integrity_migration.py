"""Dialect-aware application of forward-only trust authority migration 013f."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013f_trust_authority_integrity.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR / "fixtures" / "013f_trust_authority_integrity.sqlite.sql"
)
_CANONICAL_UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{6})?\+00:00$"
)
_BOUNDED_SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]{0,9})\."
    r"(?:0|[1-9][0-9]{0,9})\."
    r"(?:0|[1-9][0-9]{0,9})$"
)


def _is_canonical_utc_timestamp(value: object) -> int:
    if value is None:
        return 1
    if not isinstance(value, str) or _CANONICAL_UTC_TIMESTAMP.fullmatch(value) is None:
        return 0
    timestamp_format = (
        "%Y-%m-%dT%H:%M:%S.%f%z" if "." in value else "%Y-%m-%dT%H:%M:%S%z"
    )
    try:
        datetime.strptime(value, timestamp_format)
    except ValueError:
        return 0
    return 1


def _is_bounded_semver(value: object) -> int:
    return int(isinstance(value, str) and _BOUNDED_SEMVER.fullmatch(value) is not None)


def sql_for(dialect: str) -> str:
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def _columns(connection: object, table_name: str) -> set[str]:
    execute = getattr(connection, "execute")
    return {
        str(row[1])
        for row in execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def _assert_sqlite_contract(connection: object) -> None:
    issuer_columns = _columns(connection, "governance_evidence_issuers")
    key_columns = _columns(connection, "governance_evidence_signing_keys")
    policy_columns = _columns(
        connection, "governance_evidence_trust_policy_versions"
    )
    if not {"revoked_by", "revoked_at", "revocation_reason"} <= issuer_columns:
        raise RuntimeError("013f SQLite issuer chronology contract drifted")
    if not {"public_key_fingerprint", "revoked_by"} <= key_columns:
        raise RuntimeError("013f SQLite signing-key contract drifted")
    if not {
        "policy_schema_version",
        "supersedes_id",
        "activated_by",
        "activated_at",
        "retired_by",
        "retired_at",
        "retirement_reason",
    } <= policy_columns:
        raise RuntimeError("013f SQLite trust-policy contract drifted")


def apply_sqlite(connection: object) -> None:
    """Install the SQLite parity fixture after failing closed on legacy authority.

    SQLite cannot truthfully recover lifecycle actors or timestamps. Existing
    revoked issuer/key rows or non-draft policies therefore abort instead of
    receiving fabricated provenance.
    """

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")
    create_function = getattr(connection, "create_function", None)
    if not callable(create_function):
        raise TypeError("sqlite connection with deterministic functions is required")
    create_function(
        "fairmind_sha256",
        1,
        lambda value: hashlib.sha256(str(value).encode("utf-8")).hexdigest(),
        deterministic=True,
    )
    create_function(
        "fairmind_is_canonical_utc",
        1,
        _is_canonical_utc_timestamp,
        deterministic=True,
    )
    create_function(
        "fairmind_is_bounded_semver",
        1,
        _is_bounded_semver,
        deterministic=True,
    )
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013f SQLite migration requires foreign key enforcement")
    if "public_key_fingerprint" in _columns(
        connection, "governance_evidence_signing_keys"
    ):
        _assert_sqlite_contract(connection)
        return
    try:
        executescript(sql_for("sqlite"))
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        execute("PRAGMA legacy_alter_table = OFF")
        execute("PRAGMA foreign_keys = ON")
        raise
    _assert_sqlite_contract(connection)


__all__ = ["apply_sqlite", "sql_for"]

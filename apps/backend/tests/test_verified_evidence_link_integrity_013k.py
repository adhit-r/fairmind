"""Packaging contract for verified-evidence link integrity 013k."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

import config.migration_integrity as migration_integrity
from migrations.verified_evidence_link_integrity_migration import apply_sqlite


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"


def test_013k_registers_a_fail_closed_verified_link_guard() -> None:
    migration = MIGRATIONS / "013k_verified_evidence_link_integrity.sql"
    fixture = MIGRATIONS / "fixtures" / "013k_verified_evidence_link_integrity.sqlite.sql"
    operator = (
        MIGRATIONS
        / "upgrade_paths"
        / "013j_to_013k_verified_evidence_link_integrity.sql"
    )

    assert migration.is_file()
    assert fixture.is_file()
    assert operator.is_file()
    assert "fairmind_guard_verified_evidence_link_013k" in migration.read_text(
        encoding="utf-8"
    )
    source = migration.read_text(encoding="utf-8")
    assert "governance_evaluation_suite_evidence_links_verified_guard_013k" in source
    assert "guard_governance_evaluation_evidence_link_013b()" in source
    assert "admission.admission_status = 'verified'" in source
    submitter_marker = source.index("$needle$    IF v_admission_ids IS NOT NULL THEN$needle$")
    linker_injection = source.index("$replacement$    SELECT", submitter_marker)
    assert linker_injection < source.index('"relationshipType":"evidence_linker"')
    assert "link.linked_by = NEW.decided_by" in source
    assert '"relationshipType":"evidence_linker"' in source
    assert "013j-to-013k-verified-evidence-link-integrity-v1" in operator.read_text(
        encoding="utf-8"
    )
    assert any(
        item.ledger_key == "013j-to-013k-verified-evidence-link-integrity-v1"
        for item in migration_integrity.FROZEN_ASSURANCE_MIGRATIONS
    )
    assert "fairmind_guard_verified_evidence_link_013k" in (
        migration_integrity.POSTGRESQL_ASSURANCE_FUNCTIONS
    )
    assert "governance_evaluation_suite_evidence_links_verified_unavailable_013k" in (
        migration_integrity.SQLITE_ASSURANCE_TRIGGERS
    )


def test_013k_sqlite_fixture_fails_closed_for_verified_links() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        "CREATE TABLE governance_evaluation_suite_evidence_links (id TEXT PRIMARY KEY)"
    )

    apply_sqlite(connection)
    apply_sqlite(connection)

    with pytest.raises(sqlite3.IntegrityError, match="requires PostgreSQL"):
        connection.execute(
            "INSERT INTO governance_evaluation_suite_evidence_links(id) VALUES ('link-a')"
        )

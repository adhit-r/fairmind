"""Packaging contract for verified-evidence link integrity 013k."""

from __future__ import annotations

from pathlib import Path

import pytest

import config.migration_integrity as migration_integrity
from migrations.verified_evidence_link_integrity_migration import sql_for


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"


def test_013k_registers_a_fail_closed_verified_link_guard() -> None:
    migration = MIGRATIONS / "013k_verified_evidence_link_integrity.sql"
    operator = (
        MIGRATIONS
        / "upgrade_paths"
        / "013j_to_013k_verified_evidence_link_integrity.sql"
    )

    assert migration.is_file()
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
    assert "governance_evaluation_suite_evidence_links_verified_guard_013k" in (
        migration_integrity.POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS
    )


def test_013k_loader_returns_postgresql_payload_only() -> None:
    assert "fairmind_guard_verified_evidence_link_013k" in sql_for("postgresql")
    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("sqlite")

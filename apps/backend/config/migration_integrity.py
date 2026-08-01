"""Fail-closed startup verification for the assurance migration chain.

PostgreSQL is the release authority and therefore verifies the operator ledger
against a frozen source manifest. SQLite is a development/parity fixture and
verifies only the installed schema and foreign-key enforcement.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError


class MigrationIntegrityError(RuntimeError):
    """Raised when the installed assurance schema cannot be trusted."""


@dataclass(frozen=True)
class FrozenMigration:
    ledger_key: str
    checksum: str
    source_path: Path


@dataclass(frozen=True)
class PostgreSQLCatalogSpec:
    """Digest-free inventory used only to measure a trusted catalog."""

    relations: frozenset[str]
    functions: frozenset[str]
    required_triggers: frozenset[str]


@dataclass(frozen=True)
class FrozenPostgreSQLCatalog:
    """Reviewed catalog digest bound to one PostgreSQL major version."""

    spec: PostgreSQLCatalogSpec
    postgresql_major: int
    digest: str


@dataclass(frozen=True)
class DatabaseIdentity:
    """Credential-free identity for one physical runtime database."""

    backend: str
    username: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_MIGRATIONS = _BACKEND_ROOT / "migrations"

# This checksum is frozen from the reviewed direct PostgreSQL payload. Never
# derive it from the bundled file during verification: doing so would bless
# source drift instead of detecting it.
_FROZEN_013B_CHECKSUM = (
    "d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f"
)
_FROZEN_013C_CHECKSUM = (
    "e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87"
)

FROZEN_ASSURANCE_MIGRATIONS = (
    FrozenMigration(
        "012-to-013-evaluation-v2-v1",
        "3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd",
        _MIGRATIONS / "013_evaluation_assurance_contract_v2.sql",
    ),
    FrozenMigration(
        "013-to-013a-evaluation-binding-integrity-v1",
        "92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8",
        _MIGRATIONS / "013a_evaluation_binding_integrity.sql",
    ),
    FrozenMigration(
        "013a-to-013b-evaluation-assurance-trust-integrity-v1",
        _FROZEN_013B_CHECKSUM,
        _MIGRATIONS / "013b_evaluation_assurance_trust_integrity.sql",
    ),
    FrozenMigration(
        "013b-to-013c-evidence-verification-receipt-v1",
        _FROZEN_013C_CHECKSUM,
        _MIGRATIONS / "013c_evidence_verification_receipt.sql",
    ),
)

POSTGRESQL_ASSURANCE_RELATIONS = frozenset(
    {
        "fairmind_operator_migration_ledger",
        "governance_workspaces",
        "governance_ai_systems",
        "governance_evaluation_target_versions",
        "governance_evaluation_suite_versions",
        "governance_evaluation_plans",
        "governance_evaluation_plan_suites",
        "governance_evaluation_runs",
        "governance_evaluation_run_suite_executions",
        "governance_evidence_issuers",
        "governance_evidence_signing_keys",
        "governance_evidence_trust_policy_versions",
        "governance_evidence_runs",
        "governance_evidence_artifacts",
        "governance_evidence_passport_revisions",
        "governance_evidence_admissions",
        "governance_evidence_verification_receipts",
        "governance_evidence_reviews",
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
        "governance_idempotency_records",
        "governance_evaluation_audit_events",
        "governance_evaluation_audit_chain_heads",
    }
)

POSTGRESQL_ASSURANCE_FUNCTIONS = frozenset(
    {
        "advance_governance_evaluation_audit_head_013b",
        "fairmind_assert_decision_projection_013b",
        "fairmind_assert_evaluation_plan_graph",
        "fairmind_assert_evaluation_run_graph",
        "fairmind_extract_canonical_envelope_nonce",
        "fairmind_evidence_admission_is_eligible_013b",
        "fairmind_expected_decision_evidence_set_013b",
        "fairmind_is_exact_decision_evidence_set_shape_013b",
        "fairmind_jsonb_object_member_count_013c",
        "fairmind_freshness_transition_allowed",
        "fairmind_initial_layer_verdicts_v1_for_run",
        "fairmind_is_canonical_utc_timestamp",
        "fairmind_is_initial_layer_verdicts",
        "fairmind_is_layer_verdicts_v1",
        "fairmind_layer_suite_scope_matches",
        "fairmind_run_state_transition_allowed",
        "fairmind_suite_result_coherent",
        "guard_governance_evaluation_audit_event_head_013b",
        "guard_governance_evaluation_audit_head_013b",
        "guard_governance_evaluation_decision_013b",
        "guard_governance_evaluation_decision_graph_013b",
        "guard_governance_evaluation_evidence_link_013b",
        "guard_governance_evaluation_plan_suite",
        "guard_governance_evaluation_plan_v2",
        "guard_governance_evaluation_run_graph_deferred",
        "guard_governance_evaluation_run_v2",
        "guard_governance_evaluation_suite_execution",
        "guard_governance_evaluation_suite_version",
        "guard_governance_evaluation_target_version",
        "guard_governance_evidence_admission_signer_013b",
        "guard_governance_evidence_admission_receipt_013c",
        "guard_governance_evidence_issuer_013b",
        "guard_governance_evidence_nonce_claim_013b",
        "guard_governance_evidence_review_013b",
        "guard_governance_evidence_run_namespace_013b",
        "guard_governance_evidence_signing_key_013b",
        "guard_governance_evidence_trust_policy_013b",
        "guard_governance_evidence_verification_receipt_013c",
        "reject_governance_evaluation_013b_mutation",
        "reject_governance_evaluation_audit_mutation",
    }
)

POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS = frozenset(
    {
        "governance_evaluation_audit_chain_heads_guard_delete",
        "governance_evaluation_audit_chain_heads_guard_insert",
        "governance_evaluation_audit_chain_heads_guard_update",
        "governance_evaluation_audit_events_advance_head",
        "governance_evaluation_audit_events_guard_head_insert",
        "governance_evaluation_audit_events_no_delete",
        "governance_evaluation_audit_events_no_update",
        "governance_evaluation_decisions_guard_insert",
        "governance_evaluation_decisions_no_delete",
        "governance_evaluation_decisions_no_update",
        "governance_evaluation_plan_suites_guard_delete",
        "governance_evaluation_plan_suites_guard_insert",
        "governance_evaluation_plan_suites_guard_update",
        "governance_evaluation_plans_v2_guard_delete",
        "governance_evaluation_plans_v2_guard_update",
        "governance_evaluation_runs_v2_guard_delete",
        "governance_evaluation_runs_v2_guard_insert",
        "governance_evaluation_runs_v2_guard_update",
        "governance_evaluation_suite_evidence_links_guard_insert",
        "governance_evaluation_suite_evidence_links_no_delete",
        "governance_evaluation_suite_evidence_links_no_update",
        "governance_evaluation_suite_executions_guard_delete",
        "governance_evaluation_suite_executions_guard_insert",
        "governance_evaluation_suite_executions_guard_update",
        "governance_evaluation_suite_versions_guard_delete",
        "governance_evaluation_suite_versions_guard_update",
        "governance_evaluation_target_versions_guard_delete",
        "governance_evaluation_target_versions_guard_update",
        "governance_evidence_admissions_no_delete",
        "governance_evidence_admissions_no_update",
        "governance_evidence_admissions_guard_signer_insert",
        "governance_evidence_admissions_require_receipt_013c",
        "governance_evidence_issuers_guard_delete",
        "governance_evidence_issuers_guard_insert",
        "governance_evidence_issuers_guard_update",
        "governance_evidence_nonce_claims_guard_insert",
        "governance_evidence_nonce_claims_no_delete",
        "governance_evidence_nonce_claims_no_update",
        "governance_evidence_reviews_no_delete",
        "governance_evidence_reviews_guard_insert",
        "governance_evidence_reviews_no_update",
        "governance_evidence_runs_guard_v2_namespace",
        "governance_evidence_signing_keys_guard_delete",
        "governance_evidence_signing_keys_guard_insert",
        "governance_evidence_signing_keys_guard_update",
        "governance_evidence_trust_policies_guard_delete",
        "governance_evidence_trust_policies_guard_insert",
        "governance_evidence_trust_policies_guard_update",
        "governance_evidence_verification_receipts_guard_insert",
        "governance_evidence_verification_receipts_no_delete",
        "governance_evidence_verification_receipts_no_update",
    }
)

POSTGRESQL_ASSURANCE_CATALOG_SPEC = PostgreSQLCatalogSpec(
    relations=POSTGRESQL_ASSURANCE_RELATIONS,
    functions=POSTGRESQL_ASSURANCE_FUNCTIONS,
    required_triggers=POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS,
)

# Measured from two independent full operator-chain installations on
# PostgreSQL 14 and cross-checked against a direct-payload installation. The
# PostgreSQL major is part of the canonical catalog payload because PostgreSQL
# deparser output can change across major versions.
FROZEN_POSTGRESQL_ASSURANCE_CATALOGS: Mapping[
    int, FrozenPostgreSQLCatalog
] = MappingProxyType(
    {
        14: FrozenPostgreSQLCatalog(
            spec=POSTGRESQL_ASSURANCE_CATALOG_SPEC,
            postgresql_major=14,
            digest=(
                "47739c29a794d0e20bc3b5178551d92d1ab11656d202f755dc47bfe736124d3d"
            ),
        )
    }
)

SQLITE_ASSURANCE_TABLES = frozenset(
    {
        "governance_workspaces",
        "governance_ai_systems",
        "governance_evaluation_target_versions",
        "governance_evaluation_suite_versions",
        "governance_evaluation_plans",
        "governance_evaluation_plan_suites",
        "governance_evaluation_runs",
        "governance_evaluation_run_suite_executions",
        "governance_evidence_issuers",
        "governance_evidence_signing_keys",
        "governance_evidence_trust_policy_versions",
        "governance_evidence_runs",
        "governance_evidence_artifacts",
        "governance_evidence_passport_revisions",
        "governance_evidence_admissions",
        "governance_evidence_verification_receipts",
        "governance_evidence_reviews",
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
        "governance_idempotency_records",
        "governance_evaluation_audit_events",
        "governance_evaluation_audit_chain_heads",
        "governance_evidence_admission_013b_replay_state",
        "governance_evidence_admission_013b_replay_anchor",
    }
)

SQLITE_ASSURANCE_INDEXES = frozenset(
    {
        "uq_governance_workspace_org",
        "uq_governance_ai_system_tenant",
        "uq_governance_ai_system_workspace_tenant",
        "idx_governance_evaluation_targets_scope_created_keyset",
        "uq_governance_evaluation_target_kind_tenant",
        "idx_governance_evaluation_targets_scope_status",
        "idx_governance_evaluation_suites_owner_identity_keyset",
        "idx_governance_evaluation_plans_scope_contract_created_keyset",
        "idx_governance_evaluation_runs_scope_created",
        "idx_governance_evaluation_runs_status_verdict",
        "idx_governance_evaluation_runs_scope_contract_created_keyset",
        "uq_governance_evaluation_run_v2_envelope_scope",
        "uq_governance_evaluation_run_v2_envelope_nonce_scope",
        "uq_governance_evaluation_run_org_envelope_nonce",
        "idx_governance_evidence_issuers_org_status",
        "idx_governance_evidence_signing_keys_org_issuer_key_revoked",
        "idx_governance_evidence_trust_policies_org_status_version",
        "idx_governance_evidence_runs_org_system_schema_created",
        "uq_governance_evidence_run_workspace_tenant",
        "idx_evidence_passport_revisions_tenant_run",
        "idx_governance_evidence_admissions_scope_execution_created",
        "idx_governance_evidence_verification_receipts_scope",
        "idx_governance_evidence_reviews_admission_version",
        "idx_governance_evidence_nonce_claims_scope_admission",
        "idx_governance_evaluation_suite_evidence_links_scope",
        "idx_governance_evaluation_decisions_scope_version",
    }
)

SQLITE_ASSURANCE_TRIGGERS = frozenset(
    {
        "governance_ai_systems_org_insert",
        "governance_ai_systems_org_update",
        "governance_evaluation_target_versions_guard_update",
        "governance_evaluation_target_versions_guard_delete",
        "governance_evaluation_suite_versions_guard_insert",
        "governance_evaluation_suite_versions_guard_update",
        "governance_evaluation_suite_versions_guard_delete",
        "governance_evaluation_plans_v2_guard_update",
        "governance_evaluation_plans_v2_guard_delete",
        "governance_evaluation_plan_suites_guard_insert",
        "governance_evaluation_plan_suites_guard_update",
        "governance_evaluation_plan_suites_guard_delete",
        "governance_evaluation_runs_v2_guard_insert",
        "governance_evaluation_runs_v2_guard_update",
        "governance_evaluation_runs_v2_guard_delete",
        "governance_evaluation_suite_executions_guard_insert",
        "governance_evaluation_suite_executions_guard_layer_graph",
        "governance_evaluation_suite_executions_guard_update",
        "governance_evaluation_suite_executions_guard_delete",
        "governance_evaluation_suite_executions_timestamps_insert",
        "governance_evaluation_suite_executions_timestamps_update_013b",
        "governance_evidence_admissions_capture_013b_replay_insert",
        "governance_evidence_admissions_verified_signer_guard",
        "governance_evidence_admission_replay_state_conflict",
        "governance_evidence_admission_replay_state_no_update",
        "governance_evidence_admission_replay_state_no_delete",
        "governance_evidence_admission_replay_anchor_conflict",
        "governance_evidence_admission_replay_anchor_no_update",
        "governance_evidence_admission_replay_anchor_no_delete",
        "governance_evidence_admissions_no_update",
        "governance_evidence_admissions_no_delete",
        "governance_evidence_admissions_require_receipt_013c",
        "governance_evidence_admissions_require_receipt_update_013c",
        "governance_evidence_verification_receipts_guard_insert",
        "governance_evidence_verification_receipts_no_update",
        "governance_evidence_verification_receipts_no_delete",
        "governance_evidence_reviews_guard_insert",
        "governance_evidence_reviews_no_update",
        "governance_evidence_reviews_no_delete",
        "governance_evidence_nonce_claims_guard_insert",
        "governance_evidence_nonce_claims_no_update",
        "governance_evidence_nonce_claims_no_delete",
        "governance_evaluation_suite_evidence_links_guard_insert",
        "governance_evaluation_suite_evidence_links_no_update",
        "governance_evaluation_suite_evidence_links_no_delete",
        "governance_evaluation_decisions_guard_insert",
        "governance_evaluation_decisions_no_update",
        "governance_evaluation_decisions_no_delete",
        "governance_evidence_trust_policies_guard_insert",
        "governance_evidence_trust_policies_guard_update",
        "governance_evidence_trust_policies_guard_delete",
        "governance_evidence_issuers_guard_insert",
        "governance_evidence_issuers_guard_update",
        "governance_evidence_issuers_guard_delete",
        "governance_evidence_signing_keys_guard_insert",
        "governance_evidence_signing_keys_guard_update",
        "governance_evidence_signing_keys_guard_delete",
        "governance_evidence_runs_schema_source_guard_insert",
        "governance_evidence_runs_immutable_update",
        "governance_evidence_runs_immutable_delete",
        "governance_evidence_source_run_insert",
        "governance_evidence_source_run_update",
        "governance_evidence_passport_revisions_immutable_update",
        "governance_evidence_passport_revisions_immutable_delete",
        "governance_evidence_artifacts_immutable_update",
        "governance_evidence_artifacts_immutable_delete",
        "governance_evidence_org_insert",
        "governance_evidence_org_update",
        "governance_evaluation_audit_events_no_update",
        "governance_evaluation_audit_events_no_delete",
        "governance_evaluation_audit_events_guard_insert_head",
        "governance_evaluation_audit_events_advance_head",
        "governance_evaluation_audit_chain_heads_guard_insert",
        "governance_evaluation_audit_chain_heads_guard_update",
        "governance_evaluation_audit_chain_heads_guard_delete",
    }
)

SQLITE_ASSURANCE_VIEWS = frozenset(
    {
        "governance_evidence_admission_v2_current_eligibility",
    }
)

# SHA-256 over the whitespace-normalized sqlite_master SQL for every object
# named above, sorted by object type and name.  Unlike a name-only inventory,
# this freezes table columns/checks/FKs, explicit indexes, trigger bodies, and
# security-critical view definitions.
# Replace only after the complete 013c SQLite fixture has passed review.
SQLITE_ASSURANCE_CATALOG_DIGEST = (
    "a0812fa421ab7a172045d8f9845389cc5876bc1388ed9ef4cef8793fde2697d1"
)

_SQLITE_ASSURANCE_OBJECTS = {
    "table": SQLITE_ASSURANCE_TABLES,
    "index": SQLITE_ASSURANCE_INDEXES,
    "trigger": SQLITE_ASSURANCE_TRIGGERS,
    "view": SQLITE_ASSURANCE_VIEWS,
}

_TRUSTED_SCHEMA_SENTINEL = "__fairmind_trusted_schema__"


def _validate_trusted_schema_name(trusted_schema: str) -> str:
    if not isinstance(trusted_schema, str) or not trusted_schema:
        raise MigrationIntegrityError(
            "a trusted PostgreSQL migration schema is required"
        )
    lowered = trusted_schema.lower()
    if (
        "\x00" in trusted_schema
        or lowered in {"information_schema", "temp"}
        or lowered.startswith("pg_")
    ):
        raise MigrationIntegrityError(
            "a trusted PostgreSQL migration schema is required"
        )
    return trusted_schema


def _quoted_postgresql_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def postgresql_runtime_search_path(trusted_schema: str) -> str:
    """Return the only allowed PostgreSQL runtime namespace order."""
    schema = _validate_trusted_schema_name(trusted_schema)
    return f"pg_catalog,{_quoted_postgresql_identifier(schema)},pg_temp"


def _parse_postgresql_search_path(value: str) -> tuple[str, ...]:
    try:
        parsed = next(
            csv.reader(
                [value],
                delimiter=",",
                quotechar='"',
                doublequote=True,
                skipinitialspace=True,
                strict=True,
            )
        )
    except (csv.Error, StopIteration) as error:
        raise MigrationIntegrityError(
            "PostgreSQL search_path cannot be validated"
        ) from error
    return tuple(part.strip() for part in parsed)


def _assert_postgresql_runtime_search_path(connection, trusted_schema: str) -> None:
    spec = ("pg_catalog", trusted_schema, "pg_temp")
    try:
        actual = connection.execute(
            text("SELECT pg_catalog.current_setting('search_path')")
        ).scalar_one()
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "PostgreSQL search_path cannot be validated"
        ) from error
    if _parse_postgresql_search_path(str(actual)) != spec:
        raise MigrationIntegrityError("PostgreSQL runtime search_path is not fixed")


def bind_postgresql_engine_search_path(engine, trusted_schema: str) -> None:
    """Reset a SQLAlchemy pool to the trusted namespace on every checkout."""
    if getattr(getattr(engine, "dialect", None), "name", None) != "postgresql":
        raise MigrationIntegrityError(
            "cannot bind PostgreSQL search_path to a non-PostgreSQL engine"
        )
    schema = _validate_trusted_schema_name(trusted_schema)
    runtime_path = postgresql_runtime_search_path(schema)
    runtime_path_literal = runtime_path.replace("'", "''")
    prior = getattr(engine, "_fairmind_assurance_search_path", None)
    if prior is not None:
        if prior != runtime_path:
            raise MigrationIntegrityError(
                "PostgreSQL engine search_path is already bound"
            )
        return

    def _reset_search_path(dbapi_connection, _connection_record, _connection_proxy):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(
                "SELECT pg_catalog.set_config("
                f"'search_path', '{runtime_path_literal}', false)"
            )
            configured = cursor.fetchone()
            if configured is None or str(configured[0]) != runtime_path:
                raise MigrationIntegrityError(
                    "PostgreSQL runtime search_path could not be fixed"
                )
        finally:
            cursor.close()

    event.listen(engine, "checkout", _reset_search_path)
    setattr(engine, "_fairmind_assurance_search_path", runtime_path)


def _coerce_database_url(source):
    candidate = getattr(source, "url", source)
    if hasattr(candidate, "get_backend_name"):
        return candidate
    if hasattr(candidate, "render_as_string"):
        candidate = candidate.render_as_string(hide_password=True)
    try:
        return make_url(str(candidate))
    except Exception as error:
        raise MigrationIntegrityError(
            "runtime database identity cannot be parsed"
        ) from error


def _assert_unambiguous_postgresql_endpoint(url) -> None:
    query_keys = {str(key).lower() for key in url.query}
    authority_host = str(url.host or "")
    if (
        query_keys.intersection({"host", "hostaddr", "port"})
        or "," in authority_host
    ):
        raise MigrationIntegrityError(
            "PostgreSQL runtime database identity has ambiguous endpoint routing"
        )


def normalized_database_identity(source) -> DatabaseIdentity:
    """Normalize one URL without retaining credentials or routing overrides."""
    url = _coerce_database_url(source)
    backend = str(url.get_backend_name()).lower()
    if backend in {"postgres", "postgresql"}:
        _assert_unambiguous_postgresql_endpoint(url)
        return DatabaseIdentity(
            backend="postgresql",
            username=url.username,
            host=(url.host or "localhost").lower(),
            port=int(url.port or 5432),
            database=url.database,
        )
    if backend == "sqlite":
        database = url.database
        if database not in {None, "", ":memory:"}:
            database = str(Path(database).expanduser().resolve(strict=False))
        return DatabaseIdentity(backend="sqlite", database=database)
    return DatabaseIdentity(backend=backend, database=url.database)


def verify_database_identities(*sources) -> None:
    """Fail closed unless every runtime family targets one physical database."""
    identities = tuple(normalized_database_identity(source) for source in sources)
    if len(identities) < 2:
        raise MigrationIntegrityError(
            "at least two runtime database identities are required"
        )
    if (
        identities[0].backend == "sqlite"
        and identities[0].database in {None, "", ":memory:"}
    ):
        if all(source is sources[0] for source in sources[1:]):
            return
        raise MigrationIntegrityError("SQLite runtime database identities differ")
    if all(identity == identities[0] for identity in identities[1:]):
        return
    if all(identity.backend == "postgresql" for identity in identities):
        raise MigrationIntegrityError("PostgreSQL runtime database identities differ")
    if all(identity.backend == "sqlite" for identity in identities):
        raise MigrationIntegrityError("SQLite runtime database identities differ")
    raise MigrationIntegrityError("runtime database families differ")


def _normalize_postgresql_definition(
    definition: str | None,
    *,
    trusted_schema: str,
) -> str | None:
    if definition is None:
        return None
    normalized = str(definition)
    quoted_schema = _quoted_postgresql_identifier(trusted_schema)
    quoted_sentinel = _quoted_postgresql_identifier(_TRUSTED_SCHEMA_SENTINEL)
    normalized = normalized.replace(quoted_schema, quoted_sentinel)
    normalized = re.sub(
        rf"(?<![A-Za-z0-9_$]){re.escape(trusted_schema)}(?![A-Za-z0-9_$])",
        _TRUSTED_SCHEMA_SENTINEL,
        normalized,
    )
    return " ".join(normalized.split())


def _validate_postgresql_catalog_spec(
    spec: PostgreSQLCatalogSpec,
) -> None:
    if not spec.relations:
        raise MigrationIntegrityError("PostgreSQL assurance relation manifest is empty")
    if not spec.functions:
        raise MigrationIntegrityError("PostgreSQL assurance function manifest is empty")
    if not spec.required_triggers:
        raise MigrationIntegrityError("PostgreSQL assurance trigger manifest is empty")


def _mapping_rows(result) -> list[Mapping[str, object]]:
    return [dict(row) for row in result.mappings().all()]


def _postgresql_assurance_catalog_payload(
    connection,
    *,
    trusted_schema: str,
    spec: PostgreSQLCatalogSpec,
) -> dict[str, object]:
    schema = _validate_trusted_schema_name(trusted_schema)
    _validate_postgresql_catalog_spec(spec)
    if getattr(connection.dialect, "name", None) != "postgresql":
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog requires PostgreSQL"
        )
    _assert_postgresql_runtime_search_path(connection, schema)

    try:
        schema_row = connection.execute(
            text(
                "SELECT n.oid AS schema_oid, n.nspowner AS schema_owner_oid, "
                "(SESSION_USER::pg_catalog.regrole)::oid AS session_user_oid, "
                "(CURRENT_USER::pg_catalog.regrole)::oid AS current_user_oid, "
                "(n.nspowner = (SESSION_USER::pg_catalog.regrole)::oid) "
                "AS owner_is_session_user, "
                "(n.nspowner = (CURRENT_USER::pg_catalog.regrole)::oid) "
                "AS owner_is_current_user, "
                "pg_catalog.has_schema_privilege('public', n.oid, 'CREATE') "
                "AS public_create "
                "FROM pg_catalog.pg_namespace AS n WHERE n.nspname = :schema"
            ),
            {"schema": schema},
        ).mappings().one_or_none()
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "trusted PostgreSQL migration schema cannot be validated"
        ) from error
    if schema_row is None:
        raise MigrationIntegrityError(
            f"trusted PostgreSQL migration schema {schema!r} does not exist"
        )
    if bool(schema_row["public_create"]):
        raise MigrationIntegrityError(
            "trusted PostgreSQL migration schema grants PUBLIC CREATE"
        )

    try:
        relation_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.oid AS relation_oid, c.relname, c.relkind, "
                    "c.relpersistence, c.relrowsecurity, c.relforcerowsecurity, "
                    "c.relowner AS owner_oid, "
                    "(c.relowner = n.nspowner) AS owner_matches_schema "
                    "FROM pg_catalog.pg_class AS c "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = :schema AND c.relkind IN ('r', 'p') "
                    "ORDER BY c.relname"
                ),
                {"schema": schema},
            )
        )
        column_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.relname, a.attnum, a.attname, "
                    "pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type, "
                    "a.attnotnull, a.attidentity, a.attgenerated, "
                    "pg_catalog.pg_get_expr(d.adbin, d.adrelid, true) AS default_expr, "
                    "CASE WHEN coll.oid IS NULL THEN NULL "
                    "ELSE coll_ns.nspname || '.' || coll.collname END AS collation "
                    "FROM pg_catalog.pg_attribute AS a "
                    "JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "LEFT JOIN pg_catalog.pg_attrdef AS d "
                    "ON d.adrelid = a.attrelid AND d.adnum = a.attnum "
                    "LEFT JOIN pg_catalog.pg_collation AS coll ON coll.oid = a.attcollation "
                    "LEFT JOIN pg_catalog.pg_namespace AS coll_ns "
                    "ON coll_ns.oid = coll.collnamespace "
                    "WHERE n.nspname = :schema AND c.relkind IN ('r', 'p') "
                    "AND a.attnum > 0 AND NOT a.attisdropped "
                    "ORDER BY c.relname, a.attnum"
                ),
                {"schema": schema},
            )
        )
        constraint_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.relname, con.conname, con.contype, con.condeferrable, "
                    "con.condeferred, con.convalidated, "
                    "pg_catalog.pg_get_constraintdef(con.oid, true) AS definition "
                    "FROM pg_catalog.pg_constraint AS con "
                    "JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = :schema "
                    "ORDER BY c.relname, con.conname"
                ),
                {"schema": schema},
            )
        )
        index_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT table_class.relname, index_class.relname AS index_name, "
                    "idx.indisunique, idx.indisprimary, idx.indisvalid, "
                    "idx.indisready, idx.indislive, "
                    "index_class.relowner AS owner_oid, "
                    "(index_class.relowner = n.nspowner) AS owner_matches_schema, "
                    "pg_catalog.pg_get_indexdef(index_class.oid, 0, true) AS definition "
                    "FROM pg_catalog.pg_index AS idx "
                    "JOIN pg_catalog.pg_class AS table_class "
                    "ON table_class.oid = idx.indrelid "
                    "JOIN pg_catalog.pg_class AS index_class "
                    "ON index_class.oid = idx.indexrelid "
                    "JOIN pg_catalog.pg_namespace AS n "
                    "ON n.oid = table_class.relnamespace "
                    "WHERE n.nspname = :schema "
                    "ORDER BY table_class.relname, index_class.relname"
                ),
                {"schema": schema},
            )
        )
        trigger_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.relname, t.tgname, t.tgenabled, p.proname AS function_name, "
                    "pg_catalog.pg_get_triggerdef(t.oid, true) AS definition "
                    "FROM pg_catalog.pg_trigger AS t "
                    "JOIN pg_catalog.pg_class AS c ON c.oid = t.tgrelid "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "JOIN pg_catalog.pg_proc AS p ON p.oid = t.tgfoid "
                    "WHERE n.nspname = :schema AND NOT t.tgisinternal "
                    "ORDER BY c.relname, t.tgname"
                ),
                {"schema": schema},
            )
        )
        rewrite_rule_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.relname, r.rulename, r.ev_type, r.ev_enabled, "
                    "r.is_instead, "
                    "pg_catalog.pg_get_ruledef(r.oid, true) AS definition "
                    "FROM pg_catalog.pg_rewrite AS r "
                    "JOIN pg_catalog.pg_class AS c ON c.oid = r.ev_class "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = :schema "
                    "ORDER BY c.relname, r.rulename"
                ),
                {"schema": schema},
            )
        )
        function_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT p.proname, p.prokind, "
                    "pg_catalog.pg_get_function_identity_arguments(p.oid) "
                    "AS identity_arguments, "
                    "pg_catalog.pg_get_function_result(p.oid) AS result_type, "
                    "lang.lanname AS language, p.prosecdef, p.proleakproof, "
                    "p.provolatile, p.proparallel, p.proconfig, "
                    "p.proowner AS owner_oid, "
                    "(p.proowner = n.nspowner) AS owner_matches_schema, "
                    "pg_catalog.pg_get_functiondef(p.oid) AS definition "
                    "FROM pg_catalog.pg_proc AS p "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace "
                    "JOIN pg_catalog.pg_language AS lang ON lang.oid = p.prolang "
                    "WHERE n.nspname = :schema "
                    "ORDER BY p.proname, identity_arguments"
                ),
                {"schema": schema},
            )
        )
        schema_acl_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT acl.grantor AS grantor_oid, "
                    "acl.grantee AS grantee_oid, acl.privilege_type, "
                    "acl.is_grantable "
                    "FROM pg_catalog.pg_namespace AS n "
                    "CROSS JOIN LATERAL pg_catalog.aclexplode("
                    "COALESCE(n.nspacl, pg_catalog.acldefault('n', n.nspowner))"
                    ") AS acl "
                    "WHERE n.nspname = :schema "
                    "ORDER BY acl.grantor, acl.grantee, acl.privilege_type"
                ),
                {"schema": schema},
            )
        )
        relation_acl_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT c.relname, acl.grantor AS grantor_oid, "
                    "acl.grantee AS grantee_oid, acl.privilege_type, "
                    "acl.is_grantable "
                    "FROM pg_catalog.pg_class AS c "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                    "CROSS JOIN LATERAL pg_catalog.aclexplode("
                    "COALESCE(c.relacl, pg_catalog.acldefault('r', c.relowner))"
                    ") AS acl "
                    "WHERE n.nspname = :schema AND c.relkind IN ('r', 'p') "
                    "ORDER BY c.relname, acl.grantor, acl.grantee, "
                    "acl.privilege_type"
                ),
                {"schema": schema},
            )
        )
        function_acl_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT p.proname, "
                    "pg_catalog.pg_get_function_identity_arguments(p.oid) "
                    "AS identity_arguments, acl.grantor AS grantor_oid, "
                    "acl.grantee AS grantee_oid, acl.privilege_type, "
                    "acl.is_grantable "
                    "FROM pg_catalog.pg_proc AS p "
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace "
                    "CROSS JOIN LATERAL pg_catalog.aclexplode("
                    "COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))"
                    ") AS acl "
                    "WHERE n.nspname = :schema "
                    "ORDER BY p.proname, identity_arguments, acl.grantor, "
                    "acl.grantee, acl.privilege_type"
                ),
                {"schema": schema},
            )
        )
        role_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT r.oid AS role_oid, r.rolsuper, "
                    "r.rolinherit, r.rolcreaterole, r.rolcreatedb, "
                    "r.rolcanlogin, r.rolreplication, r.rolbypassrls "
                    "FROM pg_catalog.pg_roles AS r ORDER BY r.oid"
                )
            )
        )
        role_membership_rows = _mapping_rows(
            connection.execute(
                text(
                    "SELECT m.roleid AS granted_role_oid, "
                    "m.member AS member_role_oid, m.grantor AS grantor_role_oid, "
                    "m.admin_option "
                    "FROM pg_catalog.pg_auth_members AS m "
                    "ORDER BY m.roleid, m.member, m.grantor"
                )
            )
        )
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog cannot be inspected"
        ) from error

    expected_relations = set(spec.relations)
    selected_relations = [
        row for row in relation_rows if str(row["relname"]) in expected_relations
    ]
    installed_relations = {str(row["relname"]) for row in selected_relations}
    missing_relations = sorted(expected_relations - installed_relations)
    if missing_relations:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required relations: "
            + ", ".join(missing_relations)
        )
    if any(not bool(row["owner_matches_schema"]) for row in selected_relations):
        raise MigrationIntegrityError(
            "PostgreSQL assurance relation ownership invariant failed"
        )

    selected_columns = [
        row for row in column_rows if str(row["relname"]) in expected_relations
    ]
    selected_constraints = [
        row for row in constraint_rows if str(row["relname"]) in expected_relations
    ]
    selected_indexes = [
        row for row in index_rows if str(row["relname"]) in expected_relations
    ]
    if any(not bool(row["owner_matches_schema"]) for row in selected_indexes):
        raise MigrationIntegrityError(
            "PostgreSQL assurance index ownership invariant failed"
        )
    selected_triggers = [
        row for row in trigger_rows if str(row["relname"]) in expected_relations
    ]
    selected_rewrite_rules = [
        row
        for row in rewrite_rule_rows
        if str(row["relname"]) in expected_relations
    ]
    installed_triggers = {str(row["tgname"]) for row in selected_triggers}
    missing_triggers = sorted(set(spec.required_triggers) - installed_triggers)
    if missing_triggers:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required triggers: "
            + ", ".join(missing_triggers)
        )
    disabled_triggers = sorted(
        str(row["tgname"])
        for row in selected_triggers
        if str(row["tgenabled"]) not in {"O", "A"}
    )
    if disabled_triggers:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog has disabled required triggers: "
            + ", ".join(disabled_triggers)
        )

    expected_functions = set(spec.functions)
    selected_functions = [
        row for row in function_rows if str(row["proname"]) in expected_functions
    ]
    installed_functions = {str(row["proname"]) for row in selected_functions}
    missing_functions = sorted(expected_functions - installed_functions)
    if missing_functions:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required functions: "
            + ", ".join(missing_functions)
        )
    if any(not bool(row["owner_matches_schema"]) for row in selected_functions):
        raise MigrationIntegrityError(
            "PostgreSQL assurance function ownership invariant failed"
        )

    selected_relation_acls = [
        row
        for row in relation_acl_rows
        if str(row["relname"]) in expected_relations
    ]
    selected_function_acls = [
        row
        for row in function_acl_rows
        if str(row["proname"]) in expected_functions
    ]

    schema_owner_oid = int(schema_row["schema_owner_oid"])
    session_user_oid = int(schema_row["session_user_oid"])
    current_user_oid = int(schema_row["current_user_oid"])
    roles_by_oid = {int(row["role_oid"]): row for row in role_rows}
    if schema_owner_oid not in roles_by_oid:
        raise MigrationIntegrityError(
            "PostgreSQL assurance schema owner identity cannot be validated"
        )

    authority_role_oids = {schema_owner_oid}
    for row in (
        *selected_relations,
        *selected_indexes,
        *selected_functions,
        *schema_acl_rows,
        *selected_relation_acls,
        *selected_function_acls,
    ):
        for key in ("owner_oid", "grantor_oid", "grantee_oid"):
            value = row.get(key)
            if value is not None and int(value) != 0:
                authority_role_oids.add(int(value))

    # Membership can confer the authority represented by an owner or ACL
    # principal. Capture the complete connected component without persisting
    # environment-specific role OIDs or names in the release fingerprint.
    while True:
        prior_count = len(authority_role_oids)
        for row in role_membership_rows:
            granted_role_oid = int(row["granted_role_oid"])
            member_role_oid = int(row["member_role_oid"])
            if (
                granted_role_oid in authority_role_oids
                or member_role_oid in authority_role_oids
            ):
                authority_role_oids.update((granted_role_oid, member_role_oid))
        if len(authority_role_oids) == prior_count:
            break

    selected_role_memberships = [
        row
        for row in role_membership_rows
        if int(row["granted_role_oid"]) in authority_role_oids
        and int(row["member_role_oid"]) in authority_role_oids
    ]
    authority_role_oids.update(
        int(row["grantor_role_oid"])
        for row in selected_role_memberships
        if int(row["grantor_role_oid"]) != 0
    )
    missing_authority_roles = sorted(authority_role_oids - roles_by_oid.keys())
    if missing_authority_roles:
        raise MigrationIntegrityError(
            "PostgreSQL assurance role authority cannot be validated"
        )

    def canonical_role_identity(role_oid: int) -> str:
        if role_oid == 0:
            return "public"
        if role_oid == schema_owner_oid:
            return "schema_owner"
        if role_oid == session_user_oid:
            return "session_user"
        if role_oid == current_user_oid:
            return "current_user"
        return "external_role"

    def normalized_acl_rows(
        rows: Iterable[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for row in rows:
            item = {
                key: value
                for key, value in row.items()
                if key not in {"grantor_oid", "grantee_oid"}
            }
            item["grantor_identity"] = canonical_role_identity(
                int(row["grantor_oid"])
            )
            item["grantee_identity"] = canonical_role_identity(
                int(row["grantee_oid"])
            )
            normalized.append(item)
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )

    normalized_role_authorities: list[dict[str, object]] = []
    for role_oid in sorted(authority_role_oids):
        row = roles_by_oid[role_oid]
        identity = canonical_role_identity(role_oid)
        # The schema-owner token deliberately omits deployment-specific role
        # attributes. Ownership itself already conveys full object authority;
        # external principals retain the flags that determine their reach.
        if identity == "schema_owner":
            normalized_role_authorities.append({"identity": identity})
            continue
        normalized_role_authorities.append(
            {
                "identity": identity,
                "superuser": bool(row["rolsuper"]),
                "inherits": bool(row["rolinherit"]),
                "can_create_roles": bool(row["rolcreaterole"]),
                "can_create_databases": bool(row["rolcreatedb"]),
                "can_login": bool(row["rolcanlogin"]),
                "can_replicate": bool(row["rolreplication"]),
                "bypasses_row_security": bool(row["rolbypassrls"]),
            }
        )
    normalized_role_authorities.sort(
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )

    normalized_role_memberships = sorted(
        (
            {
                "granted_role_identity": canonical_role_identity(
                    int(row["granted_role_oid"])
                ),
                "member_role_identity": canonical_role_identity(
                    int(row["member_role_oid"])
                ),
                "grantor_role_identity": canonical_role_identity(
                    int(row["grantor_role_oid"])
                ),
                "admin_option": bool(row["admin_option"]),
            }
            for row in selected_role_memberships
        ),
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    )

    expected_function_path = ("pg_catalog", schema, "pg_temp")
    for row in selected_functions:
        configs = tuple(str(value) for value in (row["proconfig"] or ()))
        search_paths = [
            value.partition("=")[2]
            for value in configs
            if value.partition("=")[0].strip().lower() == "search_path"
        ]
        if len(search_paths) != 1 or (
            _parse_postgresql_search_path(search_paths[0]) != expected_function_path
        ):
            raise MigrationIntegrityError(
                "PostgreSQL assurance function lacks a fixed search_path"
            )

    def normalized_rows(
        rows: Iterable[Mapping[str, object]],
        *,
        excluded: frozenset[str] = frozenset(),
    ) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for row in rows:
            item: dict[str, object] = {}
            for key, value in row.items():
                if key in excluded:
                    continue
                if key == "owner_oid":
                    item["owner_identity"] = canonical_role_identity(int(value))
                    continue
                if key in {"definition", "default_expr", "data_type", "collation"}:
                    item[key] = _normalize_postgresql_definition(
                        None if value is None else str(value),
                        trusted_schema=schema,
                    )
                elif key == "proconfig":
                    item[key] = sorted(
                        _normalize_postgresql_definition(
                            str(config), trusted_schema=schema
                        )
                        for config in (value or ())
                    )
                else:
                    item[key] = value
            normalized.append(item)
        return normalized

    return {
        "postgresqlMajor": postgresql_server_major(connection),
        "schema": {
            "name": _TRUSTED_SCHEMA_SENTINEL,
            "public_create": False,
            "owner_identity": canonical_role_identity(schema_owner_oid),
            "owner_is_session_user": bool(schema_row["owner_is_session_user"]),
            "owner_is_current_user": bool(schema_row["owner_is_current_user"]),
        },
        "schemaAcls": normalized_acl_rows(schema_acl_rows),
        "relations": normalized_rows(
            selected_relations,
            excluded=frozenset({"relation_oid"}),
        ),
        "relationAcls": normalized_acl_rows(selected_relation_acls),
        "columns": normalized_rows(selected_columns),
        "constraints": normalized_rows(selected_constraints),
        "indexes": normalized_rows(selected_indexes),
        "triggers": normalized_rows(selected_triggers),
        "rewriteRules": normalized_rows(selected_rewrite_rules),
        "functions": normalized_rows(selected_functions),
        "functionAcls": normalized_acl_rows(selected_function_acls),
        "roleAuthorities": normalized_role_authorities,
        "roleMemberships": normalized_role_memberships,
    }


def postgresql_assurance_catalog_digest(
    connection,
    *,
    trusted_schema: str,
    spec: PostgreSQLCatalogSpec = POSTGRESQL_ASSURANCE_CATALOG_SPEC,
) -> str:
    """Return the canonical trusted-schema digest after semantic checks."""
    payload = _postgresql_assurance_catalog_payload(
        connection,
        trusted_schema=trusted_schema,
        spec=spec,
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def postgresql_server_major(connection) -> int:
    """Return the server major used by PostgreSQL catalog deparsers."""
    try:
        version_number = connection.execute(
            text("SELECT pg_catalog.current_setting('server_version_num')")
        ).scalar_one()
        major = int(str(version_number)) // 10000
    except (SQLAlchemyError, TypeError, ValueError) as error:
        raise MigrationIntegrityError(
            "PostgreSQL server major cannot be validated"
        ) from error
    if major <= 0:
        raise MigrationIntegrityError(
            "PostgreSQL server major cannot be validated"
        )
    return major


def validate_frozen_postgresql_catalog(
    frozen: FrozenPostgreSQLCatalog,
) -> None:
    """Reject malformed, placeholder, or cross-version catalog manifests."""
    _validate_postgresql_catalog_spec(frozen.spec)
    if (
        isinstance(frozen.postgresql_major, bool)
        or not isinstance(frozen.postgresql_major, int)
        or frozen.postgresql_major <= 0
    ):
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog major is invalid"
        )
    if (
        len(frozen.digest) != 64
        or frozen.digest == "0" * 64
        or any(
            character not in "0123456789abcdef"
            for character in frozen.digest
        )
    ):
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog digest is invalid"
        )


def select_frozen_postgresql_catalog(
    postgresql_major: int,
    frozen_by_major: Mapping[int, FrozenPostgreSQLCatalog],
) -> FrozenPostgreSQLCatalog:
    """Select one reviewed manifest without trusting the live catalog."""
    try:
        frozen = frozen_by_major[postgresql_major]
    except KeyError as error:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is not frozen for server major "
            f"{postgresql_major}"
        ) from error
    validate_frozen_postgresql_catalog(frozen)
    if frozen.postgresql_major != postgresql_major:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog major does not match its release key"
        )
    return frozen


def verify_postgresql_assurance_catalog(
    connection,
    *,
    trusted_schema: str,
    frozen_by_major: Mapping[int, FrozenPostgreSQLCatalog],
) -> None:
    """Require exact reviewed definitions for the connected server major."""
    major = postgresql_server_major(connection)
    frozen = select_frozen_postgresql_catalog(major, frozen_by_major)
    actual = postgresql_assurance_catalog_digest(
        connection,
        trusted_schema=trusted_schema,
        spec=frozen.spec,
    )
    if actual != frozen.digest:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog definition drift"
        )


def _as_tuple(expected: Iterable[FrozenMigration]) -> tuple[FrozenMigration, ...]:
    frozen = tuple(expected)
    if not frozen:
        raise MigrationIntegrityError("assurance migration manifest is empty")
    keys = [item.ledger_key for item in frozen]
    if len(keys) != len(set(keys)):
        raise MigrationIntegrityError("assurance migration manifest has duplicate keys")
    for item in frozen:
        if len(item.checksum) != 64 or any(
            character not in "0123456789abcdef" for character in item.checksum
        ):
            raise MigrationIntegrityError(
                f"{item.ledger_key} has an invalid frozen checksum"
            )
    return frozen


def verify_bundled_migration_checksums(
    *, expected: Iterable[FrozenMigration] = FROZEN_ASSURANCE_MIGRATIONS
) -> None:
    """Prove that bundled SQL still matches the reviewed frozen manifest."""
    for item in _as_tuple(expected):
        try:
            actual = hashlib.sha256(item.source_path.read_bytes()).hexdigest()
        except OSError as error:
            raise MigrationIntegrityError(
                f"{item.ledger_key} bundled source is unavailable"
            ) from error
        if actual != item.checksum:
            raise MigrationIntegrityError(
                f"{item.ledger_key} bundled source checksum drift"
            )


def verify_postgresql_migration_ledger(
    connection,
    *,
    trusted_schema: str,
    expected: Iterable[FrozenMigration] = FROZEN_ASSURANCE_MIGRATIONS,
) -> None:
    """Require every frozen migration key and checksum in the release ledger."""
    frozen = _as_tuple(expected)
    trusted_schema = _validate_trusted_schema_name(trusted_schema)
    try:
        available_schemas = set(inspect(connection).get_schema_names())
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "trusted PostgreSQL migration schema cannot be validated"
        ) from error
    if trusted_schema not in available_schemas:
        raise MigrationIntegrityError(
            f"trusted PostgreSQL migration schema {trusted_schema!r} does not exist"
        )
    quoted_schema = connection.dialect.identifier_preparer.quote_schema(
        trusted_schema
    )
    try:
        rows = connection.execute(
            text(
                "SELECT migration_key, migration_checksum "
                f"FROM {quoted_schema}.fairmind_operator_migration_ledger"
            )
        ).all()
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "assurance migration ledger is unavailable"
        ) from error

    installed = {str(key): str(checksum) for key, checksum in rows}
    for item in frozen:
        actual = installed.get(item.ledger_key)
        if actual is None:
            raise MigrationIntegrityError(f"{item.ledger_key} is missing")
        if actual != item.checksum:
            raise MigrationIntegrityError(f"{item.ledger_key} checksum drift")


def _normalize_sqlite_schema_sql(sql: str) -> str:
    return " ".join(sql.split())


def _sqlite_catalog_digest(
    rows: Iterable[tuple[str, str, str]],
) -> str:
    payload = "\n".join(
        f"{object_type}\0{name}\0{_normalize_sqlite_schema_sql(sql)}"
        for object_type, name, sql in sorted(rows)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_sqlite_assurance_schema(connection) -> None:
    """Validate the parity fixture without inventing a PostgreSQL ledger."""
    foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
    if foreign_keys != 1:
        raise MigrationIntegrityError("SQLite foreign_keys must be enabled")

    rows = connection.exec_driver_sql(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE type IN ('table', 'index', 'trigger', 'view') AND sql IS NOT NULL"
    ).all()
    installed = {(object_type, name): sql for object_type, name, sql in rows}
    selected: list[tuple[str, str, str]] = []
    for object_type, required_names in _SQLITE_ASSURANCE_OBJECTS.items():
        missing = sorted(
            name for name in required_names if (object_type, name) not in installed
        )
        if missing:
            raise MigrationIntegrityError(
                f"SQLite assurance schema is missing required {object_type}s: "
                + ", ".join(missing)
            )
        selected.extend(
            (object_type, name, installed[(object_type, name)])
            for name in required_names
        )
    if _sqlite_catalog_digest(selected) != SQLITE_ASSURANCE_CATALOG_DIGEST:
        raise MigrationIntegrityError(
            "SQLite assurance catalog definition drift"
        )
    violations = connection.exec_driver_sql("PRAGMA foreign_key_check").first()
    if violations is not None:
        raise MigrationIntegrityError("SQLite assurance foreign-key check failed")


def verify_assurance_migration_integrity(
    engine,
    *,
    enabled: bool,
    postgresql_schema: str | None = None,
) -> None:
    """Verify the installed assurance schema before the API serves requests."""
    if not enabled:
        return
    dialect = engine.dialect.name
    if dialect == "postgresql":
        trusted_schema = _validate_trusted_schema_name(postgresql_schema or "")
        verify_bundled_migration_checksums()
        with engine.connect() as connection:
            _assert_postgresql_runtime_search_path(connection, trusted_schema)
            verify_postgresql_migration_ledger(
                connection,
                trusted_schema=trusted_schema,
            )
            verify_postgresql_assurance_catalog(
                connection,
                trusted_schema=trusted_schema,
                frozen_by_major=FROZEN_POSTGRESQL_ASSURANCE_CATALOGS,
            )
        return
    if dialect == "sqlite":
        with engine.connect() as connection:
            verify_sqlite_assurance_schema(connection)
        return
    raise MigrationIntegrityError(
        f"unsupported database dialect for assurance v2: {dialect}"
    )

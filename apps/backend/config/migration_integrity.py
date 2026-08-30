"""Fail-closed startup verification for the assurance migration chain.

PostgreSQL is the release authority and therefore verifies the operator ledger
against a frozen source manifest. Any other dialect fails closed.
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
_FROZEN_013B_CHECKSUM = "d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f"
FROZEN_013B_OPERATOR_V2_CHECKSUM = (
    "1ad3a12f814f537c130ffbbc326bee3c7408ec90795d31925b459b9a05486fe0"
)
_FROZEN_013C_CHECKSUM = "b121f3d1d8723da5b932231e234270cf037dfa239151ec5a518184915032dbae"
FROZEN_013C_OPERATOR_CHECKSUM = "8f7ec1bda9041f16a03ace75202e590fc8a92947495a792f1b886a55fe621040"
_FROZEN_013D_CHECKSUM = "d5d167dabc3d2458aa5aab6d2cb120ae9c90f798bf4ace6b193b58d4660c6cb9"
FROZEN_013D_OPERATOR_CHECKSUM = "7a1d368fc1556e6286e047bf73c47878ab69fb31d2b25e7cf139b6919a00d77d"
_FROZEN_013E_CHECKSUM = "95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32"
FROZEN_013E_OPERATOR_CHECKSUM = "6397810191ab919a0bf3246a17d04284344afa96acfd291b9485e361c4fcb1e6"
_FROZEN_013F_CHECKSUM = "c6cd4b77875b3fe3cc9c2140d9ca1f619e17adbefbedc37a31cea342dbc64fb6"
FROZEN_013F_OPERATOR_CHECKSUM = (
    "55cae25a29e05bcb538b049dbe743994d8e19f759dd0c19992ed494405f1120d"
)
_FROZEN_013G_CHECKSUM = "ec8c29cabc98906d43c44aaf138e0d5e6a4458e86702298170b3b5964849ebf8"
FROZEN_013G_OPERATOR_CHECKSUM = (
    "4d7e1db2453832b409b9dcc8dcf9f8027e589a0f081dd1a64a4d0806cf2541f3"
)
_FROZEN_013H_CHECKSUM = "9798cca6bae5e66036ff08caf3eeebcb9d8ed78e5ea669ec403a4bf06e4df84b"
FROZEN_013H_OPERATOR_CHECKSUM = (
    "71c58297d218c9da7c54d0f13887eec1250d11e463c02bbca2f3981b2b13e180"
)
_FROZEN_013I_CHECKSUM = "83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94"
FROZEN_013I_OPERATOR_CHECKSUM = "69c4bda5b5485da32f522d8dffd690f3875c05fe3bba576a21338cd814159c8d"
_FROZEN_013J_CHECKSUM = "bc5deb123981ee968061ec695821e8d00a8cc860d3c2169f9ca81ae6805846b5"
FROZEN_013J_OPERATOR_CHECKSUM = "3a3cab3184178958bacd67c6573dedc9b624293b3b5cb773d899b20e02eb2f53"
_FROZEN_013K_CHECKSUM = "f81a4b888d5b86a9e9675561b319c19e0470d61d2cb486442b8e4e6bf6022acf"
FROZEN_013K_OPERATOR_CHECKSUM = "8bdbf13e15452949b7a4e002fe152f0a90c7cb8c1c343a126271f6a6b8d9d322"
_FROZEN_013L_CHECKSUM = "2dd029773f4dbe7b79cbc8db69ebe2bcdf444d82d8c9316a7f23b900ceabc4f9"
FROZEN_013L_OPERATOR_CHECKSUM = "b8942f7baf21bc21cfabea04f33ab020c1aa55f531be3effee571e1eb2a7eda1"
_FROZEN_014_CHECKSUM = "c2c1260f5c60e9494e6d2ca558840dfe362a6dec6e60320fe92e6d7b8f8a83e3"
FROZEN_014_OPERATOR_CHECKSUM = "3d2b1c20451aeef918db459d49504193e82c2eae497beffcfb02d0cb080a9252"

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
    FrozenMigration(
        "013c-to-013d-evaluator-catalog-v1",
        _FROZEN_013D_CHECKSUM,
        _MIGRATIONS / "013d_evaluator_catalog.sql",
    ),
    FrozenMigration(
        "013d-to-013e-environmental-tenant-scope-v1",
        _FROZEN_013E_CHECKSUM,
        _MIGRATIONS / "013e_environmental_tenant_scope.sql",
    ),
    FrozenMigration(
        "013e-to-013f-trust-authority-integrity-v1",
        _FROZEN_013F_CHECKSUM,
        _MIGRATIONS / "013f_trust_authority_integrity.sql",
    ),
    FrozenMigration(
        "013f-to-013g-operational-evidence-freshness-v1",
        _FROZEN_013G_CHECKSUM,
        _MIGRATIONS / "013g_operational_evidence_freshness.sql",
    ),
    FrozenMigration(
        "013g-to-013h-idempotency-retention-integrity-v1",
        _FROZEN_013H_CHECKSUM,
        _MIGRATIONS / "013h_idempotency_retention_integrity.sql",
    ),
    FrozenMigration(
        "013h-to-013i-imported-evidence-delivery-integrity-v1",
        _FROZEN_013I_CHECKSUM,
        _MIGRATIONS / "013i_imported_evidence_delivery_integrity.sql",
    ),
    FrozenMigration(
        "013i-to-013j-owner-decision-override-integrity-v1",
        _FROZEN_013J_CHECKSUM,
        _MIGRATIONS / "013j_owner_decision_override_integrity.sql",
    ),
    FrozenMigration(
        "013j-to-013k-verified-evidence-link-integrity-v1",
        _FROZEN_013K_CHECKSUM,
        _MIGRATIONS / "013k_verified_evidence_link_integrity.sql",
    ),
    FrozenMigration(
        "013k-to-013l-delegated-separation-override-grant-integrity-v1",
        _FROZEN_013L_CHECKSUM,
        _MIGRATIONS / "013l_delegated_separation_override_grant_integrity.sql",
    ),
    FrozenMigration(
        "013l-to-014-worker-execution-foundation-v1",
        _FROZEN_014_CHECKSUM,
        _MIGRATIONS / "014_worker_execution_foundation.sql",
    ),
)

POSTGRESQL_ASSURANCE_RELATIONS = frozenset(
    {
        "fairmind_operator_migration_ledger",
        "organizations",
        "org_members",
        "org_roles",
        "governance_workspaces",
        "governance_ai_systems",
        "governance_evidence",
        "governance_environmental_assessments",
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
        "governance_evaluator_registrations",
        "governance_evidence_reviews",
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
        "governance_idempotency_records",
        "governance_evaluation_audit_events",
        "governance_evaluation_audit_chain_heads",
        "governance_separation_override_grants",
        "governance_evaluation_worker_identities",
        "governance_evaluation_suite_attempts",
        "governance_evaluation_artifacts",
        "governance_evaluation_attempt_artifacts",
        "governance_evaluation_cancellations",
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
        "fairmind_evaluator_registration_binding_hash_013d",
        "fairmind_verification_receipt_has_exact_verified_admission_013c",
        "fairmind_verification_receipt_is_relationally_valid_013c",
        "fairmind_verification_receipt_matches_admission_013c",
        "fairmind_verified_admission_has_exact_receipt_013c",
        "fairmind_freshness_transition_allowed",
        "fairmind_canonical_clock_utc_013f",
        "fairmind_is_canonical_ed25519_jwk_013f",
        "fairmind_is_canonical_text_array_013f",
        "fairmind_is_exact_trust_policy_013f",
        "fairmind_is_semver_013f",
        "fairmind_semver_gt_013f",
        "fairmind_sha256_text_013f",
        "fairmind_classify_evidence_freshness_013g",
        "fairmind_lock_evidence_authority_org_013g",
        "fairmind_gate_evidence_review_013g",
        "fairmind_stamp_evaluator_registration_revocation_013g",
        "fairmind_gate_evaluation_decision_013g",
        "fairmind_idempotency_format_utc_013h",
        "fairmind_idempotency_clock_utc_013h",
        "fairmind_idempotency_row_is_valid_013h",
        "fairmind_guard_idempotency_record_013h",
        "fairmind_unverified_import_delivery_is_valid_013i",
        "fairmind_unverified_import_projection_is_valid_013i",
        "fairmind_guard_unverified_import_delivery_013i",
        "fairmind_guard_unverified_import_projection_013i",
        "fairmind_owner_permission_array_is_valid_013j",
        "fairmind_owner_decision_override_authorized_013j",
        "fairmind_validate_owner_override_audit_013j",
        "fairmind_verified_evidence_link_is_valid_013k",
        "fairmind_guard_verified_evidence_link_013k",
        "fairmind_governance_decision_actor_authorized_013l",
        "fairmind_separation_override_relationships_013l",
        "fairmind_delegated_separation_override_authorized_013l",
        "guard_governance_separation_override_grant_013l",
        "guard_governance_evaluation_suite_queue_metadata_014",
        "guard_governance_evaluation_worker_identity_014",
        "guard_governance_evaluation_suite_attempt_014",
        "guard_governance_evaluation_artifact_014",
        "fairmind_validate_separation_override_grant_audit_013l",
        "fairmind_validate_delegated_decision_audit_013l",
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
        "guard_governance_evidence_issuer_013f",
        "guard_governance_evidence_nonce_claim_013b",
        "guard_governance_evidence_review_013b",
        "guard_governance_evidence_run_namespace_013b",
        "guard_governance_evidence_signing_key_013b",
        "guard_governance_evidence_signing_key_013f",
        "guard_governance_evidence_trust_policy_013b",
        "guard_governance_evidence_trust_policy_013f",
        "guard_governance_evidence_verification_receipt_013c",
        "guard_governance_evidence_verification_receipt_parent_013c",
        "guard_governance_evaluator_registration_insert_013d",
        "guard_governance_evaluator_registration_update_013d",
        "guard_governance_evaluator_registration_delete_013d",
        "guard_governance_evidence_receipt_catalog_013d",
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
        "governance_evaluation_suite_evidence_links_verified_guard_013k",
        "governance_separation_override_grants_guard_insert",
        "governance_separation_override_grants_immutable_update",
        "governance_separation_override_grants_immutable_delete",
        "governance_separation_override_grants_audit_013l",
        "governance_evaluation_decisions_delegated_override_audit_013l",
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
        "governance_evidence_receipts_require_verified_admission_013c",
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
        "governance_evaluator_registrations_guard_insert",
        "governance_evaluator_registrations_guard_update",
        "governance_evaluator_registrations_no_delete",
        "governance_evidence_verification_receipts_catalog_guard_013d",
        "governance_evidence_verification_receipts_no_update",
        "000_013g_evidence_issuers_common_lock",
        "000_013g_evidence_signing_keys_common_lock",
        "000_013g_evidence_trust_policies_common_lock",
        "000_013g_evaluator_registrations_common_lock",
        "001_013g_evaluator_registration_revocation_clock",
        "000_013g_evidence_reviews_freshness_gate",
        "000_013g_evaluation_decisions_freshness_gate",
        "governance_idempotency_records_integrity_013h",
        "000_013i_unverified_import_delivery_guard",
        "000_013i_unverified_import_projection_guard",
        "governance_evaluation_decisions_owner_override_audit_013j",
        "000_014_governance_evaluation_suite_queue_metadata_guard",
        "governance_evaluation_worker_identities_guard_update_014",
        "governance_evaluation_worker_identities_no_delete_014",
        "governance_evaluation_suite_attempts_guard_update_014",
        "governance_evaluation_suite_attempts_no_delete_014",
        "governance_evaluation_artifacts_guard_update_014",
        "governance_evaluation_artifacts_no_delete_014",
        "governance_evaluation_attempt_artifacts_no_update_014",
        "governance_evaluation_attempt_artifacts_no_delete_014",
        "governance_evaluation_cancellations_no_update_014",
        "governance_evaluation_cancellations_no_delete_014",
    }
)

POSTGRESQL_ASSURANCE_CATALOG_SPEC = PostgreSQLCatalogSpec(
    relations=POSTGRESQL_ASSURANCE_RELATIONS,
    functions=POSTGRESQL_ASSURANCE_FUNCTIONS,
    required_triggers=POSTGRESQL_ASSURANCE_REQUIRED_TRIGGERS,
)

# Measured from two independent full operator-chain installations through 014 on
# PostgreSQL 14 and cross-checked against a direct-payload installation. The
# PostgreSQL major is part of the canonical catalog payload because PostgreSQL
# deparser output can change across major versions.
#
# PostgreSQL 18 (Neon) was measured from two clean installs that ran
# upgrade_paths/010_to_011_drift_reconciliation.sql between 010 and 011, and
# matches the ORM-provisioned Neon production schema after that same script.
# The reconciliation appends organizations.plan and organizations.settings, so
# a PostgreSQL 18 install that skips it does not match. The payload includes
# the role authority graph around the schema owner, and on Neon every project
# role is a member of neon_superuser: adding or removing a project role changes
# this digest, and startup then fails closed until it is re-measured.
#
# The PostgreSQL 18 digest below is still the 013j measurement. It includes the
# Neon role graph, so it cannot be reproduced on a local PostgreSQL 18. After
# 013k and 013l are applied to Neon, re-measure it there before setting
# assurance_v2_enabled; until then startup with assurance on fails closed.
FROZEN_POSTGRESQL_ASSURANCE_CATALOGS: Mapping[int, FrozenPostgreSQLCatalog] = MappingProxyType(
    {
        14: FrozenPostgreSQLCatalog(
            spec=POSTGRESQL_ASSURANCE_CATALOG_SPEC,
            postgresql_major=14,
            digest=("18acdb1569c601bf99c45b22d5de45fe3b749acaf4bb7bb5644a7eba265e2f3a"),
        ),
        18: FrozenPostgreSQLCatalog(
            spec=POSTGRESQL_ASSURANCE_CATALOG_SPEC,
            postgresql_major=18,
            digest=("ca00ef6d75a35294ac915de43d8f1a188a77a784060065d3947f982e8e6920a4"),
        ),
    }
)

_TRUSTED_SCHEMA_SENTINEL = "__fairmind_trusted_schema__"


def _validate_trusted_schema_name(trusted_schema: str) -> str:
    if not isinstance(trusted_schema, str) or not trusted_schema:
        raise MigrationIntegrityError("a trusted PostgreSQL migration schema is required")
    lowered = trusted_schema.lower()
    if (
        "\x00" in trusted_schema
        or lowered in {"information_schema", "temp"}
        or lowered.startswith("pg_")
    ):
        raise MigrationIntegrityError("a trusted PostgreSQL migration schema is required")
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
        raise MigrationIntegrityError("PostgreSQL search_path cannot be validated") from error
    return tuple(part.strip() for part in parsed)


def _assert_postgresql_runtime_search_path(connection, trusted_schema: str) -> None:
    spec = ("pg_catalog", trusted_schema, "pg_temp")
    try:
        actual = connection.execute(
            text("SELECT pg_catalog.current_setting('search_path')")
        ).scalar_one()
    except SQLAlchemyError as error:
        raise MigrationIntegrityError("PostgreSQL search_path cannot be validated") from error
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
            raise MigrationIntegrityError("PostgreSQL engine search_path is already bound")
        return

    def _reset_search_path(dbapi_connection, _connection_record, _connection_proxy):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(
                "SELECT pg_catalog.set_config(" f"'search_path', '{runtime_path_literal}', false)"
            )
            configured = cursor.fetchone()
            if configured is None or str(configured[0]) != runtime_path:
                raise MigrationIntegrityError("PostgreSQL runtime search_path could not be fixed")
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
        raise MigrationIntegrityError("runtime database identity cannot be parsed") from error


def _assert_unambiguous_postgresql_endpoint(url) -> None:
    query_keys = {str(key).lower() for key in url.query}
    authority_host = str(url.host or "")
    if query_keys.intersection({"host", "hostaddr", "port"}) or "," in authority_host:
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
    raise MigrationIntegrityError(f"unsupported database backend: {backend}")


def verify_database_identities(*sources) -> None:
    """Fail closed unless every runtime family targets one physical database."""
    identities = tuple(normalized_database_identity(source) for source in sources)
    if len(identities) < 2:
        raise MigrationIntegrityError("at least two runtime database identities are required")
    if all(identity == identities[0] for identity in identities[1:]):
        return
    raise MigrationIntegrityError("PostgreSQL runtime database identities differ")


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
        raise MigrationIntegrityError("PostgreSQL assurance catalog requires PostgreSQL")
    _assert_postgresql_runtime_search_path(connection, schema)

    try:
        schema_row = (
            connection.execute(
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
            )
            .mappings()
            .one_or_none()
        )
    except SQLAlchemyError as error:
        raise MigrationIntegrityError(
            "trusted PostgreSQL migration schema cannot be validated"
        ) from error
    if schema_row is None:
        raise MigrationIntegrityError(
            f"trusted PostgreSQL migration schema {schema!r} does not exist"
        )
    if bool(schema_row["public_create"]):
        raise MigrationIntegrityError("trusted PostgreSQL migration schema grants PUBLIC CREATE")

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
        raise MigrationIntegrityError("PostgreSQL assurance catalog cannot be inspected") from error

    expected_relations = set(spec.relations)
    selected_relations = [row for row in relation_rows if str(row["relname"]) in expected_relations]
    installed_relations = {str(row["relname"]) for row in selected_relations}
    missing_relations = sorted(expected_relations - installed_relations)
    if missing_relations:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required relations: "
            + ", ".join(missing_relations)
        )
    if any(not bool(row["owner_matches_schema"]) for row in selected_relations):
        raise MigrationIntegrityError("PostgreSQL assurance relation ownership invariant failed")

    selected_columns = [row for row in column_rows if str(row["relname"]) in expected_relations]
    selected_constraints = [
        row for row in constraint_rows if str(row["relname"]) in expected_relations
    ]
    selected_indexes = [row for row in index_rows if str(row["relname"]) in expected_relations]
    if any(not bool(row["owner_matches_schema"]) for row in selected_indexes):
        raise MigrationIntegrityError("PostgreSQL assurance index ownership invariant failed")
    selected_triggers = [row for row in trigger_rows if str(row["relname"]) in expected_relations]
    selected_rewrite_rules = [
        row for row in rewrite_rule_rows if str(row["relname"]) in expected_relations
    ]
    installed_triggers = {str(row["tgname"]) for row in selected_triggers}
    missing_triggers = sorted(set(spec.required_triggers) - installed_triggers)
    if missing_triggers:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required triggers: "
            + ", ".join(missing_triggers)
        )
    disabled_triggers = sorted(
        str(row["tgname"]) for row in selected_triggers if str(row["tgenabled"]) not in {"O", "A"}
    )
    if disabled_triggers:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog has disabled required triggers: "
            + ", ".join(disabled_triggers)
        )

    expected_functions = set(spec.functions)
    selected_functions = [row for row in function_rows if str(row["proname"]) in expected_functions]
    installed_functions = {str(row["proname"]) for row in selected_functions}
    missing_functions = sorted(expected_functions - installed_functions)
    if missing_functions:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is missing required functions: "
            + ", ".join(missing_functions)
        )
    if any(not bool(row["owner_matches_schema"]) for row in selected_functions):
        raise MigrationIntegrityError("PostgreSQL assurance function ownership invariant failed")

    selected_relation_acls = [
        row for row in relation_acl_rows if str(row["relname"]) in expected_relations
    ]
    selected_function_acls = [
        row for row in function_acl_rows if str(row["proname"]) in expected_functions
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
            if granted_role_oid in authority_role_oids or member_role_oid in authority_role_oids:
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
        raise MigrationIntegrityError("PostgreSQL assurance role authority cannot be validated")

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
            item["grantor_identity"] = canonical_role_identity(int(row["grantor_oid"]))
            item["grantee_identity"] = canonical_role_identity(int(row["grantee_oid"]))
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
                "granted_role_identity": canonical_role_identity(int(row["granted_role_oid"])),
                "member_role_identity": canonical_role_identity(int(row["member_role_oid"])),
                "grantor_role_identity": canonical_role_identity(int(row["grantor_role_oid"])),
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
            raise MigrationIntegrityError("PostgreSQL assurance function lacks a fixed search_path")

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
                        _normalize_postgresql_definition(str(config), trusted_schema=schema)
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
        raise MigrationIntegrityError("PostgreSQL server major cannot be validated") from error
    if major <= 0:
        raise MigrationIntegrityError("PostgreSQL server major cannot be validated")
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
        raise MigrationIntegrityError("PostgreSQL assurance catalog major is invalid")
    if (
        len(frozen.digest) != 64
        or frozen.digest == "0" * 64
        or any(character not in "0123456789abcdef" for character in frozen.digest)
    ):
        raise MigrationIntegrityError("PostgreSQL assurance catalog digest is invalid")


def select_frozen_postgresql_catalog(
    postgresql_major: int,
    frozen_by_major: Mapping[int, FrozenPostgreSQLCatalog],
) -> FrozenPostgreSQLCatalog:
    """Select one reviewed manifest without trusting the live catalog."""
    try:
        frozen = frozen_by_major[postgresql_major]
    except KeyError as error:
        raise MigrationIntegrityError(
            "PostgreSQL assurance catalog is not frozen for server major " f"{postgresql_major}"
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
        raise MigrationIntegrityError("PostgreSQL assurance catalog definition drift")


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
            raise MigrationIntegrityError(f"{item.ledger_key} has an invalid frozen checksum")
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
            raise MigrationIntegrityError(f"{item.ledger_key} bundled source checksum drift")


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
    quoted_schema = connection.dialect.identifier_preparer.quote_schema(trusted_schema)
    try:
        rows = connection.execute(
            text(
                "SELECT migration_key, migration_checksum "
                f"FROM {quoted_schema}.fairmind_operator_migration_ledger"
            )
        ).all()
    except SQLAlchemyError as error:
        raise MigrationIntegrityError("assurance migration ledger is unavailable") from error

    installed = {str(key): str(checksum) for key, checksum in rows}
    for item in frozen:
        actual = installed.get(item.ledger_key)
        if actual is None:
            raise MigrationIntegrityError(f"{item.ledger_key} is missing")
        if actual != item.checksum:
            raise MigrationIntegrityError(f"{item.ledger_key} checksum drift")


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
    raise MigrationIntegrityError(f"unsupported database dialect for assurance v2: {dialect}")

from pathlib import Path

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

from database import governance_models


REPO_ROOT = Path(__file__).parents[3]


def _named_constraints(model, constraint_type):
    return {
        constraint.name: tuple(constraint.columns.keys())
        for constraint in model.__table__.constraints
        if isinstance(constraint, constraint_type) and constraint.name
    }


def _named_checks(model):
    return {
        constraint.name: str(constraint.sqltext)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }


def _named_indexes(model):
    def column_name(expression):
        return getattr(expression, "name", None) or expression.element.name

    return {
        index.name: tuple(column_name(expression) for expression in index.expressions)
        for index in model.__table__.indexes
        if isinstance(index, Index) and index.name
    }


def test_trust_integrity_model_mirrors_are_byte_identical():
    canonical = REPO_ROOT / "apps/backend/database/governance_models.py"
    layered = (
        REPO_ROOT
        / "apps/backend/src/infrastructure/db/database/governance_models.py"
    )
    assert canonical.read_bytes() == layered.read_bytes()


def test_admission_and_review_expose_complete_013b_scope():
    admission = governance_models.GovernanceEvidenceAdmission
    assert tuple(admission.__table__.columns.keys()) == (
        "id",
        "org_id",
        "workspace_id",
        "system_id",
        "evidence_run_id",
        "passport_revision_id",
        "trust_policy_version_id",
        "suite_execution_id",
        "envelope_hash",
        "admission_status",
        "freshness_status",
        "issuer_id",
        "signing_key_id",
        "signer_key_id",
        "signer_algorithm",
        "reasons_json",
        "checked_by",
        "checked_at",
        "created_at",
        "contract_version",
        "run_id",
        "envelope_id",
        "envelope_nonce",
        "submitted_by",
        "captured_at",
        "signed_at",
        "effective_expires_at",
    )
    assert admission.__table__.c.contract_version.default.arg == "1.0.0"
    admission_uniques = _named_constraints(admission, UniqueConstraint)
    assert admission_uniques["uq_governance_evidence_admission_v2_scope"] == (
        "id",
        "contract_version",
        "run_id",
        "suite_execution_id",
        "evidence_run_id",
        "passport_revision_id",
        "workspace_id",
        "system_id",
        "org_id",
    )
    assert admission_uniques[
        "uq_governance_evidence_admission_v2_nonce_binding"
    ] == (
        "id",
        "contract_version",
        "run_id",
        "suite_execution_id",
        "envelope_id",
        "envelope_hash",
        "envelope_nonce",
        "evidence_run_id",
        "passport_revision_id",
        "workspace_id",
        "system_id",
        "org_id",
    )
    admission_fks = _named_constraints(admission, ForeignKeyConstraint)
    assert admission_fks[
        "fk_governance_evidence_admission_suite_execution_run_scope"
    ] == ("suite_execution_id", "run_id", "workspace_id", "system_id", "org_id")
    assert admission_fks[
        "fk_governance_evidence_admission_run_envelope_scope"
    ] == (
        "run_id",
        "contract_version",
        "envelope_id",
        "envelope_hash",
        "workspace_id",
        "system_id",
        "org_id",
    )
    assert (
        "fk_governance_evidence_admission_signer_key_identity"
        not in admission_fks
    )
    admission_checks = _named_checks(admission)
    assert "contract_version IN ('1.0.0', '2.0.0')" in admission_checks[
        "ck_governance_evidence_admission_contract_version"
    ]
    assert "length(envelope_nonce) = 43" in admission_checks[
        "ck_governance_evidence_admission_envelope_nonce"
    ]
    assert "submitted_by IS NOT NULL" in admission_checks[
        "ck_governance_evidence_admission_v2_binding"
    ]
    assert "contract_version = '1.0.0' OR" in admission_checks[
        "ck_governance_evidence_admission_v2_binding"
    ]
    assert "contract_version = '1.0.0' OR" in admission_checks[
        "ck_governance_evidence_admission_envelope_nonce"
    ]
    assert "contract_version = '1.0.0' OR" in admission_checks[
        "ck_governance_evidence_admission_v2_signer"
    ]
    assert "signed_at IS NOT NULL" in admission_checks[
        "ck_governance_evidence_admission_v2_signer"
    ]
    timestamp_check = admission_checks[
        "ck_governance_evidence_admission_v2_timestamps"
    ]
    assert "contract_version = '1.0.0' OR" in timestamp_check
    for column_name in ("captured_at", "signed_at", "effective_expires_at"):
        assert f"length({column_name}) IN (25, 32)" in timestamp_check
        assert f"substr({column_name}, 21, 6)" in timestamp_check
    timestamp_order = admission_checks[
        "ck_governance_evidence_admission_v2_timestamp_order"
    ]
    assert "captured_at <= effective_expires_at" in timestamp_order
    assert "captured_at <= signed_at" in timestamp_order
    assert "signed_at <= effective_expires_at" in timestamp_order

    review = governance_models.GovernanceEvidenceReview
    for column_name in (
        "workspace_id",
        "run_id",
        "suite_execution_id",
        "admission_contract_version",
    ):
        assert column_name in review.__table__.c
    review_uniques = _named_constraints(review, UniqueConstraint)
    assert review_uniques["uq_governance_evidence_review_admission_version"] == (
        "admission_id",
        "review_version",
    )
    review_fks = _named_constraints(review, ForeignKeyConstraint)
    assert review_fks["fk_governance_evidence_review_admission_v2_scope"] == (
        "admission_id",
        "admission_contract_version",
        "run_id",
        "suite_execution_id",
        "evidence_run_id",
        "passport_revision_id",
        "workspace_id",
        "system_id",
        "org_id",
    )


def test_013b_models_expose_exact_columns_and_structural_keys():
    expected_columns = {
        "GovernanceEvidenceNonceClaim": (
            "id", "org_id", "workspace_id", "system_id", "run_id",
            "run_contract_version", "suite_execution_id", "admission_id",
            "admission_contract_version", "evidence_run_id", "passport_revision_id",
            "envelope_id", "envelope_hash", "envelope_nonce", "claimed_by",
            "claimed_at",
        ),
        "GovernanceEvaluationSuiteEvidenceLink": (
            "id", "org_id", "workspace_id", "system_id", "run_id",
            "suite_execution_id", "admission_id", "admission_contract_version",
            "evidence_run_id", "passport_revision_id", "nonce_claim_id", "linked_by",
            "linked_at",
        ),
        "GovernanceEvaluationDecision": (
            "id", "org_id", "workspace_id", "system_id", "run_id",
            "run_contract_version", "envelope_id", "envelope_hash", "verdict_version",
            "overall_verdict", "layer_verdicts_schema_version", "layer_verdicts_json",
            "rationale", "decided_by", "owner_override_reason", "evidence_set_json",
            "evidence_set_hash", "decided_at",
        ),
        "GovernanceEvaluationAuditChainHead": (
            "org_id", "last_sequence_number", "last_event_hash", "updated_at",
        ),
    }
    for model_name, columns in expected_columns.items():
        model = getattr(governance_models, model_name, None)
        assert model is not None, f"missing {model_name}"
        assert tuple(model.__table__.columns.keys()) == columns

    run_columns = governance_models.GovernanceEvaluationRun.__table__.c
    assert run_columns.layer_verdicts_schema_version.nullable is True

    nonce_claim = governance_models.GovernanceEvidenceNonceClaim
    assert _named_constraints(nonce_claim, UniqueConstraint)[
        "uq_governance_evidence_nonce_claim_replay"
    ] == ("suite_execution_id", "envelope_id", "envelope_nonce")
    nonce_checks = _named_checks(nonce_claim)
    assert "run_contract_version = '2.0.0'" in nonce_checks[
        "ck_governance_evidence_nonce_claim_contract_versions"
    ]
    assert "admission_contract_version = '2.0.0'" in nonce_checks[
        "ck_governance_evidence_nonce_claim_contract_versions"
    ]
    assert "length(envelope_nonce) = 43" in nonce_checks[
        "ck_governance_evidence_nonce_claim_envelope_nonce"
    ]

    link = governance_models.GovernanceEvaluationSuiteEvidenceLink
    link_uniques = _named_constraints(link, UniqueConstraint)
    assert link_uniques[
        "uq_governance_evaluation_suite_evidence_link_tenant"
    ] == (
        "id",
        "run_id",
        "suite_execution_id",
        "admission_id",
        "admission_contract_version",
        "evidence_run_id",
        "passport_revision_id",
        "nonce_claim_id",
        "workspace_id",
        "system_id",
        "org_id",
    )
    assert link_uniques[
        "uq_governance_evaluation_suite_evidence_link_suite_execution"
    ] == ("suite_execution_id",)
    assert link_uniques[
        "uq_governance_evaluation_suite_evidence_link_admission"
    ] == ("admission_id",)
    assert link_uniques[
        "uq_governance_evaluation_suite_evidence_link_nonce_claim"
    ] == ("nonce_claim_id",)

    decision = governance_models.GovernanceEvaluationDecision
    assert (
        decision.__table__.c.layer_verdicts_schema_version.default is None
    )
    assert _named_constraints(decision, UniqueConstraint)[
        "uq_governance_evaluation_decision_tenant"
    ] == (
        "id",
        "run_id",
        "verdict_version",
        "workspace_id",
        "system_id",
        "org_id",
    )
    decision_checks = _named_checks(decision)
    assert "verdict_version >= 1" in decision_checks[
        "ck_governance_evaluation_decision_verdict_version"
    ]
    assert "approved" in decision_checks[
        "ck_governance_evaluation_decision_overall_verdict"
    ]
    assert "length(evidence_set_hash) = 64" in decision_checks[
        "ck_governance_evaluation_decision_evidence_set_hash"
    ]
    evidence_set_object = decision_checks[
        "ck_governance_evaluation_decision_evidence_set_object"
    ]
    assert "substr(trim(evidence_set_json), 1, 1) = '{'" in evidence_set_object
    assert "substr(trim(evidence_set_json), -1, 1) = '}'" in evidence_set_object

    head = governance_models.GovernanceEvaluationAuditChainHead
    assert _named_constraints(head, ForeignKeyConstraint)[
        "fk_governance_evaluation_audit_chain_head_tail"
    ] == ("org_id", "last_sequence_number")


def test_013b_query_indexes_are_explicit_and_match_the_release_contract():
    expected = {
        "GovernanceEvidenceAdmission": {
            "idx_governance_evidence_admissions_scope_execution_created": (
                "org_id", "system_id", "suite_execution_id", "created_at"
            )
        },
        "GovernanceEvidenceReview": {
            "idx_governance_evidence_reviews_admission_version": (
                "admission_id", "review_version"
            )
        },
        "GovernanceEvaluationSuiteEvidenceLink": {
            "idx_governance_evaluation_suite_evidence_links_scope": (
                "org_id", "system_id", "run_id", "suite_execution_id"
            )
        },
        "GovernanceEvidenceNonceClaim": {
            "idx_governance_evidence_nonce_claims_scope_admission": (
                "org_id", "system_id", "admission_id"
            )
        },
        "GovernanceEvaluationDecision": {
            "idx_governance_evaluation_decisions_scope_version": (
                "org_id", "system_id", "run_id", "verdict_version"
            )
        },
        "GovernanceEvidenceIssuer": {
            "idx_governance_evidence_issuers_org_status": ("org_id", "status")
        },
        "GovernanceEvidenceSigningKey": {
            "idx_governance_evidence_signing_keys_org_issuer_key_revoked": (
                "org_id", "issuer_id", "key_id", "revoked_at"
            )
        },
        "GovernanceEvidenceTrustPolicyVersion": {
            "idx_governance_evidence_trust_policies_org_status_version": (
                "org_id", "status", "version"
            )
        },
        "GovernanceEvidenceRun": {
            "idx_governance_evidence_runs_org_system_schema_created": (
                "org_id", "system_id", "schema_version", "created_at"
            )
        },
    }
    for model_name, required in expected.items():
        indexes = _named_indexes(getattr(governance_models, model_name))
        for index_name, columns in required.items():
            assert indexes[index_name] == columns


def test_013b_named_constraints_are_exact_and_postgresql_safe():
    expected = {
        "GovernanceEvidenceAdmission": {
            "uq_governance_evidence_admission_v2_scope",
            "uq_governance_evidence_admission_v2_nonce_binding",
            "fk_governance_evidence_admission_suite_execution_run_scope",
            "fk_governance_evidence_admission_run_envelope_scope",
            "ck_governance_evidence_admission_contract_version",
            "ck_governance_evidence_admission_envelope_nonce",
            "ck_governance_evidence_admission_v2_binding",
            "ck_governance_evidence_admission_v2_signer",
            "ck_governance_evidence_admission_v2_timestamps",
            "ck_governance_evidence_admission_v2_timestamp_order",
        },
        "GovernanceEvidenceReview": {
            "uq_governance_evidence_review_admission_version",
            "fk_governance_evidence_review_admission_v2_scope",
        },
        "GovernanceEvidenceNonceClaim": {
            "uq_governance_evidence_nonce_claim_admission",
            "uq_governance_evidence_nonce_claim_replay",
            "uq_governance_evidence_nonce_claim_tenant",
            "fk_governance_evidence_nonce_claim_admission",
            "fk_governance_evidence_nonce_claim_run_envelope",
            "fk_governance_evidence_nonce_claim_suite_execution",
            "ck_governance_evidence_nonce_claim_contract_versions",
            "ck_governance_evidence_nonce_claim_envelope_hash",
            "ck_governance_evidence_nonce_claim_envelope_nonce",
        },
        "GovernanceEvaluationSuiteEvidenceLink": {
            "uq_governance_evaluation_suite_evidence_link_tenant",
            "uq_governance_evaluation_suite_evidence_link_suite_execution",
            "uq_governance_evaluation_suite_evidence_link_admission",
            "uq_governance_evaluation_suite_evidence_link_nonce_claim",
            "fk_governance_evaluation_suite_evidence_link_execution",
            "fk_governance_evaluation_suite_evidence_link_admission",
            "fk_governance_evaluation_suite_evidence_link_nonce_claim",
            "ck_governance_evaluation_suite_evidence_link_contract",
        },
        "GovernanceEvaluationDecision": {
            "uq_governance_evaluation_decision_tenant",
            "uq_governance_evaluation_decision_run_version",
            "fk_governance_evaluation_decision_run_envelope",
            "ck_governance_evaluation_decision_contract",
            "ck_governance_evaluation_decision_verdict_version",
            "ck_governance_evaluation_decision_overall_verdict",
            "ck_governance_evaluation_decision_layer_schema",
            "ck_governance_evaluation_decision_layer_verdicts",
            "ck_governance_evaluation_decision_rationale",
            "ck_governance_evaluation_decision_owner_override",
            "ck_governance_evaluation_decision_evidence_set_hash",
            "ck_governance_evaluation_decision_evidence_set_size",
        },
        "GovernanceEvaluationAuditChainHead": {
            "fk_governance_evaluation_audit_chain_head_tail",
            "ck_governance_evaluation_audit_chain_head_sequence",
            "ck_governance_evaluation_audit_chain_head_hash",
        },
    }
    for model_name, required_names in expected.items():
        table = getattr(governance_models, model_name).__table__
        actual_names = {
            constraint.name
            for constraint in table.constraints
            if constraint.name
        }
        assert required_names <= actual_names
        for name in actual_names | {index.name for index in table.indexes}:
            assert len(name) <= 63, f"PostgreSQL identifier too long: {name}"

    audit_head_checks = _named_checks(
        governance_models.GovernanceEvaluationAuditChainHead
    )
    assert set(audit_head_checks) == {
        "ck_governance_evaluation_audit_chain_head_sequence",
        "ck_governance_evaluation_audit_chain_head_hash",
    }
    assert all("1 = 0" not in expression for expression in audit_head_checks.values())

    nonce_scope = _named_constraints(
        governance_models.GovernanceEvidenceNonceClaim, UniqueConstraint
    )["uq_governance_evidence_nonce_claim_tenant"]
    assert "admission_contract_version" in nonce_scope
    nonce_fk = _named_constraints(
        governance_models.GovernanceEvaluationSuiteEvidenceLink,
        ForeignKeyConstraint,
    )["fk_governance_evaluation_suite_evidence_link_nonce_claim"]
    assert "admission_contract_version" in nonce_fk


def test_013b_replaces_task7_projection_freezes_with_coherence_checks():
    run_checks = _named_checks(governance_models.GovernanceEvaluationRun)
    assert "ck_governance_evaluation_run_v2_projection_freeze" not in run_checks
    run_coherence = run_checks[
        "ck_governance_evaluation_run_v2_projection_coherence"
    ]
    assert "contract_version = '1.0.0'" in run_coherence
    assert "contract_version = '2.0.0'" in run_coherence
    assert "verdict_version = 0" in run_coherence
    assert "overall_verdict IN ('review', 'insufficient')" in run_coherence
    assert "verdict_version >= 1" in run_coherence
    for forbidden in ('approved', 'conditional', 'blocked'):
        assert forbidden in run_coherence
    assert "layer_verdicts_schema_version IS NULL" in run_coherence
    assert "layer_verdicts_schema_version = '1.0.0'" in run_coherence
    for key in ("suites", "modalities", "components", "riskDimensions"):
        assert key in run_coherence

    execution_checks = _named_checks(
        governance_models.GovernanceEvaluationRunSuiteExecution
    )
    assert (
        "ck_governance_evaluation_suite_execution_projection_freeze"
        not in execution_checks
    )
    projection = execution_checks[
        "ck_governance_evaluation_suite_execution_projection_coherence"
    ]
    assert "admission_status = 'pending'" in projection
    assert "evidence_run_id IS NULL" in projection
    assert "evidence_run_id IS NOT NULL" in projection
    assert (
        "admission_status IN ('verified', 'unverified', 'expired', 'superseded')"
        in projection
    )
    assert "result_summary_json IS NOT NULL" in projection
    assert "limitations_json IS NOT NULL" in projection

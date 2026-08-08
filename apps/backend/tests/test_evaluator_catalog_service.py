"""Application contract for the persistent, organization-scoped evaluator catalog."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.ports.evaluation_workbench import MutationResult
from src.application.services.evaluator_catalog_service import (
    EvaluatorCatalogError,
    EvaluatorCatalogService,
)
from src.application.services.evaluator_registration import EvaluatorIdentityBinding


NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


class _CatalogRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], object] = {}
        self.authorities = {("org-a", "issuer-a", "key-a")}

    def find_by_binding(self, *, organization_id: str, binding: EvaluatorIdentityBinding):
        for (org_id, _registration_id), record in self.records.items():
            if org_id == organization_id and record.binding == binding:
                return record
        return None

    def get_registration(
        self,
        *,
        organization_id: str,
        registration_id: str,
        lock: bool = False,
    ):
        del lock
        return self.records.get((organization_id, registration_id))

    def signing_authority_is_live(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        key_id: str,
        source_type: str,
        at: datetime,
        lock: bool,
    ) -> bool:
        del source_type, at, lock
        return (organization_id, issuer_id, key_id) in self.authorities

    def insert_registration(self, record):
        self.records[(record.organization_id, record.registration_id)] = record
        return record

    def replace_registration(self, record, *, expected_status: str):
        existing = self.records.get((record.organization_id, record.registration_id))
        if existing is None or existing.status != expected_status:
            return None
        self.records[(record.organization_id, record.registration_id)] = record
        return record


class _CatalogUnitOfWork:
    def __init__(self, repository: _CatalogRepository) -> None:
        self.repository = repository
        self.commands = []
        self.outcomes = []
        self._replays: dict[tuple[str, str, str, str], MutationResult] = {}

    def mutate(self, command, callback) -> MutationResult:
        key = (
            command.organization_id,
            command.actor_id,
            command.operation,
            command.idempotency_key,
        )
        prior = self._replays.get(key)
        if prior is not None:
            assert command.request_hash == self.commands[-1].request_hash
            return MutationResult.create(body=prior.body, status=prior.status, replayed=True)
        outcome = callback(NOW)
        result = MutationResult.create(body=outcome.body.to_dict(), status=outcome.status)
        self._replays[key] = result
        self.commands.append(command)
        self.outcomes.append(outcome)
        return result


def _binding(*, issuer_id: str = "issuer-a", key_id: str = "key-a") -> EvaluatorIdentityBinding:
    return EvaluatorIdentityBinding(
        evaluator_id="inspect-agent-safety",
        source_type="external_provider",
        adapter_name="inspect",
        adapter_version="0.3.0",
        result_contract_version="1.0.0",
        issuer_id=issuer_id,
        key_id=key_id,
    )


def _service() -> tuple[EvaluatorCatalogService, _CatalogUnitOfWork]:
    repository = _CatalogRepository()
    unit_of_work = _CatalogUnitOfWork(repository)
    return (
        EvaluatorCatalogService(
            unit_of_work,
            uuid_factory=lambda: "11111111-1111-4111-8111-111111111111",
        ),
        unit_of_work,
    )


def test_submit_is_org_scoped_idempotent_and_audited() -> None:
    service, unit_of_work = _service()

    created = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-a",
        binding=_binding(),
    )
    replay = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-a",
        binding=_binding(),
    )

    assert created.status == 201
    assert created.body["status"] == "pending"
    assert created.body["organizationId"] == "org-a"
    assert replay.replayed is True
    assert len(unit_of_work.repository.records) == 1
    assert unit_of_work.commands[0].operation == "evaluation-v2.evaluator-catalog.submit"
    assert unit_of_work.outcomes[0].audit_action == "evaluation_v2.evaluator_catalog.submitted"
    assert unit_of_work.outcomes[0].audit_details.to_dict()["bindingHash"] == created.body[
        "bindingHash"
    ]


def test_review_enforces_four_eyes_and_exact_tenant_scope() -> None:
    service, _unit_of_work = _service()
    created = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-a",
        binding=_binding(),
    )
    registration_id = created.body["id"]

    with pytest.raises(EvaluatorCatalogError) as same_actor:
        service.approve(
            organization_id="org-a",
            registration_id=registration_id,
            actor_id="submitter-a",
            idempotency_key="catalog-approve-same",
            rationale="The designated reviewer checked the evaluator binding.",
        )
    assert same_actor.value.code == "evaluator_registration_four_eyes_required"

    with pytest.raises(EvaluatorCatalogError) as foreign_tenant:
        service.approve(
            organization_id="org-b",
            registration_id=registration_id,
            actor_id="reviewer-b",
            idempotency_key="catalog-approve-foreign",
            rationale="This must not leak a foreign tenant registration.",
        )
    assert foreign_tenant.value.code == "evaluator_registration_not_found"

    approved = service.approve(
        organization_id="org-a",
        registration_id=registration_id,
        actor_id="reviewer-a",
        idempotency_key="catalog-approve-a",
        rationale="The designated reviewer checked the evaluator binding.",
    )
    assert approved.body["status"] == "approved"
    assert approved.body["reviewedBy"] == "reviewer-a"


def test_submission_fails_closed_when_issuer_key_is_not_live_for_that_org() -> None:
    service, _unit_of_work = _service()

    with pytest.raises(EvaluatorCatalogError) as caught:
        service.submit(
            organization_id="org-b",
            actor_id="submitter-b",
            idempotency_key="catalog-submit-foreign-authority",
            binding=_binding(),
        )

    assert caught.value.code == "evaluator_registration_signing_authority_untrusted"


def test_lifecycle_audit_actions_use_explicit_past_tense_names() -> None:
    service, unit_of_work = _service()

    approved = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-approved",
        binding=_binding(),
    )
    service.approve(
        organization_id="org-a",
        registration_id=approved.body["id"],
        actor_id="reviewer-a",
        idempotency_key="catalog-approve-audit",
        rationale="Independent approval has been recorded.",
    )
    service.revoke(
        organization_id="org-a",
        registration_id=approved.body["id"],
        actor_id="revoker-a",
        idempotency_key="catalog-revoke-audit",
        rationale="The approved evaluator is no longer authorized.",
    )

    rejected = service.submit(
        organization_id="org-a",
        actor_id="submitter-b",
        idempotency_key="catalog-submit-rejected",
        binding=EvaluatorIdentityBinding(
            evaluator_id="inspect-agent-security",
            source_type="external_provider",
            adapter_name="inspect",
            adapter_version="0.3.0",
            result_contract_version="1.0.0",
            issuer_id="issuer-a",
            key_id="key-a",
        ),
    )
    service.reject(
        organization_id="org-a",
        registration_id=rejected.body["id"],
        actor_id="reviewer-b",
        idempotency_key="catalog-reject-audit",
        rationale="The evaluator does not meet the approval criteria.",
    )

    assert [outcome.audit_action for outcome in unit_of_work.outcomes] == [
        "evaluation_v2.evaluator_catalog.submitted",
        "evaluation_v2.evaluator_catalog.approved",
        "evaluation_v2.evaluator_catalog.revoked",
        "evaluation_v2.evaluator_catalog.submitted",
        "evaluation_v2.evaluator_catalog.rejected",
    ]

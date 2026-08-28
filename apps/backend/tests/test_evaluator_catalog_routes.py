"""HTTP contracts for the default-off evaluator catalog administration API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.composition.evaluator_catalog import build_evaluator_catalog_service
from api.routes.evaluator_catalog import (
    evaluator_catalog_router,
    get_evaluator_catalog_service,
)
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from config.jwt_exceptions import JWT_EXCEPTION_HANDLERS
from config.settings import settings
from database.connection import Base, get_db
from database.models import Organization, OrganizationMember, OrganizationRole, User
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    MutationResult,
)
from src.application.ports.evaluator_catalog import EvaluatorCatalogRecord
from src.application.services.evaluator_catalog_service import (
    EvaluatorCatalogError,
    EvaluatorCatalogService,
)
from src.application.services.evaluator_registration import EvaluatorIdentityBinding
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluatorCatalogRepository,
    SqlAlchemyEvaluatorCatalogUnitOfWork,
)

app = FastAPI()
app.include_router(evaluator_catalog_router, prefix="/api/v1/ai-governance")

ORG = str(uuid.uuid4())
FOREIGN_ORG = str(uuid.uuid4())
USER = str(uuid.uuid4())
OWNER = str(uuid.uuid4())
REVIEWER = str(uuid.uuid4())
INACTIVE_USER = str(uuid.uuid4())
BASE = f"/api/v1/ai-governance/organizations/{ORG}/evaluation-v2/evaluator-catalog"
FOREIGN_BASE = f"/api/v1/ai-governance/organizations/{FOREIGN_ORG}/evaluation-v2/evaluator-catalog"
CATALOG_PERMISSION = "evaluation:catalog:admin"
NOW = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)


def _token(user_id: str) -> TokenData:
    return TokenData(
        user_id=user_id,
        email=f"{user_id}@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=NOW,
        exp=NOW,
    )


class _CatalogRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], EvaluatorCatalogRecord] = {}
        self.authorities = {
            (ORG, "issuer-a", "key-a", "external_provider"),
            (FOREIGN_ORG, "issuer-a", "key-a", "external_provider"),
        }

    def find_by_binding(
        self,
        *,
        organization_id: str,
        binding: EvaluatorIdentityBinding,
    ) -> EvaluatorCatalogRecord | None:
        return next(
            (
                record
                for (record_org_id, _), record in self.records.items()
                if record_org_id == organization_id and record.binding == binding
            ),
            None,
        )

    def get_registration(
        self,
        *,
        organization_id: str,
        registration_id: str,
        lock: bool,
    ) -> EvaluatorCatalogRecord | None:
        del lock
        return self.records.get((organization_id, registration_id))

    def list_registrations(
        self,
        *,
        organization_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[EvaluatorCatalogRecord]:
        registrations = sorted(
            (
                record
                for (record_org_id, _), record in self.records.items()
                if record_org_id == organization_id
            ),
            key=lambda record: record.registration_id,
        )
        if limit is None:
            return registrations[offset:]
        return registrations[offset : offset + limit]

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
        del at, lock
        return (organization_id, issuer_id, key_id, source_type) in self.authorities

    def insert_registration(self, record: EvaluatorCatalogRecord) -> EvaluatorCatalogRecord:
        self.records[(record.organization_id, record.registration_id)] = record
        return record

    def replace_registration(
        self,
        record: EvaluatorCatalogRecord,
        *,
        expected_status: str,
    ) -> EvaluatorCatalogRecord | None:
        current = self.records.get((record.organization_id, record.registration_id))
        if current is None or current.status != expected_status:
            return None
        self.records[(record.organization_id, record.registration_id)] = record
        return record


class _CatalogUnitOfWork:
    def __init__(self) -> None:
        self.repository = _CatalogRepository()
        self._idempotency: dict[
            tuple[str, str, str, str], tuple[str, MutationResult | EvaluationWorkbenchError]
        ] = {}

    def mutate(self, command, callback) -> MutationResult:
        identity = (
            command.organization_id,
            command.actor_id,
            command.operation,
            command.idempotency_key,
        )
        replay = self._idempotency.get(identity)
        if replay is not None:
            request_hash, outcome = replay
            if request_hash != command.request_hash:
                raise EvaluatorCatalogError(
                    "idempotency_conflict",
                    "This Idempotency-Key is already bound to a different request.",
                    status_code=409,
                )
            if isinstance(outcome, EvaluationWorkbenchError):
                raise outcome
            return MutationResult.create(
                body=outcome.body,
                status=outcome.status,
                replayed=True,
            )
        try:
            outcome = callback(NOW)
        except EvaluationWorkbenchError as error:
            self._idempotency[identity] = (command.request_hash, error)
            raise
        result = MutationResult.create(body=outcome.body.to_dict(), status=outcome.status)
        self._idempotency[identity] = (command.request_hash, result)
        return result


def _catalog_service() -> EvaluatorCatalogService:
    return EvaluatorCatalogService(_CatalogUnitOfWork())


@pytest.fixture
def catalog_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record) -> None:
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        for user_id in (USER, OWNER, REVIEWER, INACTIVE_USER):
            session.execute(
                User.__table__.insert().values(
                    id=uuid.UUID(user_id),
                    email=f"{user_id}@example.test",
                    username=user_id,
                )
            )
        for org_id, name in ((ORG, "Catalog Org"), (FOREIGN_ORG, "Foreign Catalog Org")):
            session.execute(
                Organization.__table__.insert().values(
                    id=uuid.UUID(org_id),
                    name=name,
                    slug=org_id,
                    owner_id=uuid.UUID(USER),
                )
            )
        for role in ("admin", "reviewer"):
            session.execute(
                OrganizationRole.__table__.insert().values(
                    id=uuid.uuid4(),
                    org_id=uuid.UUID(ORG),
                    name=role,
                    permissions=[],
                )
            )
        for user_id, role, status in (
            (USER, "admin", "active"),
            (OWNER, "owner", "active"),
            (REVIEWER, "reviewer", "active"),
            (INACTIVE_USER, "admin", "disabled"),
        ):
            session.execute(
                OrganizationMember.__table__.insert().values(
                    id=uuid.uuid4(),
                    org_id=uuid.UUID(ORG),
                    user_id=uuid.UUID(user_id),
                    role=role,
                    status=status,
                )
            )
        session.commit()
    finally:
        session.close()

    active = {"token": _token(USER)}
    service = _catalog_service()

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    async def override_user() -> TokenData:
        return active["token"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    app.dependency_overrides[get_evaluator_catalog_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, active, factory, service
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _enable_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_evaluator_catalog_enabled", True)


def _grant_catalog_permission(factory, role: str, permissions: list[str] | None = None) -> None:
    session = factory()
    try:
        session.execute(
            update(OrganizationRole)
            .where(
                OrganizationRole.__table__.c.org_id == uuid.UUID(ORG),
                OrganizationRole.__table__.c.name == role,
            )
            .values(permissions=permissions or [CATALOG_PERMISSION])
        )
        session.commit()
    finally:
        session.close()


def _binding_payload(*, evaluator_id: str = "inspect-agent-safety") -> dict[str, str]:
    return {
        "evaluatorId": evaluator_id,
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "resultContractVersion": "1.0.0",
        "issuerId": "issuer-a",
        "signingKeyId": "key-a",
    }


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _registrations_url(base: str = BASE) -> str:
    return f"{base}/registrations"


def test_catalog_route_is_hidden_until_both_feature_flags_are_enabled(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _active, _factory, service = catalog_client
    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_evaluator_catalog_enabled", False)

    disabled = client.post(
        _registrations_url(),
        headers=_headers("catalog-hidden"),
        json=_binding_payload(),
    )
    assert disabled.status_code == 404
    assert disabled.json()["detail"]["code"] == "assurance_feature_disabled"
    assert service._unit_of_work.repository.records == {}

    monkeypatch.setattr(settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(settings, "assurance_v2_evaluator_catalog_enabled", True)
    parent_disabled = client.get(_registrations_url())
    assert parent_disabled.status_code == 404
    assert parent_disabled.json()["detail"]["code"] == "assurance_feature_disabled"


def test_catalog_requires_authentication_active_membership_and_exact_permission(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    unauthenticated_app = FastAPI()
    for exception_class, handler in JWT_EXCEPTION_HANDLERS.items():
        unauthenticated_app.add_exception_handler(exception_class, handler)
    unauthenticated_app.include_router(
        evaluator_catalog_router,
        prefix="/api/v1/ai-governance",
    )
    with TestClient(unauthenticated_app) as unauthenticated_client:
        unauthenticated = unauthenticated_client.get(_registrations_url())
    assert unauthenticated.status_code == 401

    client, active, factory, _service = catalog_client
    owner_without_permission = client.get(_registrations_url())
    assert owner_without_permission.status_code == 403
    assert owner_without_permission.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }

    active["token"] = _token(OWNER)
    owner_without_permission = client.get(_registrations_url())
    assert owner_without_permission.status_code == 403
    assert owner_without_permission.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }

    active["token"] = _token(INACTIVE_USER)
    inactive_member = client.get(_registrations_url())
    assert inactive_member.status_code == 403
    assert inactive_member.json()["detail"] == "Organization membership required"

    active["token"] = _token(USER)
    _grant_catalog_permission(factory, "admin")
    allowed = client.get(_registrations_url())
    assert allowed.status_code == 200
    assert allowed.json() == {"items": [], "limit": 100, "offset": 0, "hasMore": False}


def test_undeclared_catalog_action_aliases_cannot_authorize_any_catalog_route(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    client, active, factory, _service = catalog_client

    _grant_catalog_permission(factory, "admin", ["evaluation:catalog:submit"])
    submit_denied = client.post(
        _registrations_url(),
        headers=_headers("catalog-submit-denied"),
        json=_binding_payload(),
    )
    assert submit_denied.status_code == 403
    assert submit_denied.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }

    _grant_catalog_permission(factory, "admin")
    submitted = client.post(
        _registrations_url(),
        headers=_headers("catalog-submit-allowed"),
        json=_binding_payload(),
    )
    assert submitted.status_code == 201
    registration_id = submitted.json()["id"]

    _grant_catalog_permission(factory, "admin", ["evaluation:catalog:read"])
    read_denied = client.get(_registrations_url())
    assert read_denied.status_code == 403
    assert read_denied.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }

    _grant_catalog_permission(factory, "reviewer", ["evaluation:catalog:review"])
    active["token"] = _token(REVIEWER)
    review_denied = client.post(
        f"{_registrations_url()}/{registration_id}/approve",
        headers=_headers("catalog-review-denied"),
        json={"rationale": "Independent review."},
    )
    assert review_denied.status_code == 403
    assert review_denied.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }

    _grant_catalog_permission(factory, "reviewer")
    approved = client.post(
        f"{_registrations_url()}/{registration_id}/approve",
        headers=_headers("catalog-review-allowed"),
        json={"rationale": "Independent review."},
    )
    assert approved.status_code == 200

    _grant_catalog_permission(factory, "reviewer", ["evaluation:catalog:revoke"])
    revoke_denied = client.post(
        f"{_registrations_url()}/{registration_id}/revoke",
        headers=_headers("catalog-revoke-denied"),
        json={"rationale": "Revoke requires a separate permission."},
    )
    assert revoke_denied.status_code == 403
    assert revoke_denied.json()["detail"] == {
        "code": "evaluation_catalog_admin_forbidden",
        "message": "The evaluation:catalog:admin permission is required.",
    }


def test_catalog_submit_is_strict_scope_bound_and_idempotent(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    client, _active, factory, service = catalog_client
    _grant_catalog_permission(factory, "admin")

    missing_key = client.post(_registrations_url(), json=_binding_payload())
    assert missing_key.status_code == 422
    assert service._unit_of_work.repository.records == {}

    body_with_server_owned_fields = {
        **_binding_payload(),
        "organizationId": FOREIGN_ORG,
        "status": "approved",
        "id": "caller-registration-id",
        "bindingHash": "a" * 64,
        "reviewedBy": REVIEWER,
        "authorityId": "internal-authority-id",
    }
    rejected_body = client.post(
        _registrations_url(),
        headers=_headers("catalog-strict"),
        json=body_with_server_owned_fields,
    )
    assert rejected_body.status_code == 422
    assert rejected_body.json()["detail"]["code"] == "invalid_request"
    assert service._unit_of_work.repository.records == {}

    first = client.post(
        f"{_registrations_url()}?organizationId={FOREIGN_ORG}",
        headers=_headers("catalog-submit"),
        json=_binding_payload(),
    )
    assert first.status_code == 201, first.text
    assert first.json()["organizationId"] == ORG
    assert first.json()["submittedBy"] == USER
    registration_id = first.json()["id"]

    replay = client.post(
        _registrations_url(),
        headers=_headers("catalog-submit"),
        json=_binding_payload(),
    )
    assert replay.status_code == 201
    assert replay.content == first.content
    assert replay.headers["Idempotency-Replayed"] == "true"

    conflict = client.post(
        _registrations_url(),
        headers=_headers("catalog-submit"),
        json=_binding_payload(evaluator_id="inspect-agent-security"),
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "idempotency_conflict"
    assert list(service._unit_of_work.repository.records) == [(ORG, registration_id)]


def test_catalog_transitions_preserve_membership_identity_four_eyes_and_stale_state(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    client, active, factory, _service = catalog_client
    _grant_catalog_permission(factory, "admin")
    _grant_catalog_permission(factory, "reviewer")

    submitted = client.post(
        _registrations_url(),
        headers=_headers("catalog-transition-submit"),
        json=_binding_payload(),
    )
    assert submitted.status_code == 201, submitted.text
    registration_id = submitted.json()["id"]

    self_review = client.post(
        f"{_registrations_url()}/{registration_id}/approve",
        headers=_headers("catalog-self-review"),
        json={"rationale": "The submitter cannot approve this registration."},
    )
    assert self_review.status_code == 409
    assert self_review.json()["detail"]["code"] == "evaluator_registration_four_eyes_required"

    active["token"] = _token(REVIEWER)
    approved = client.post(
        f"{_registrations_url()}/{registration_id}/approve",
        headers=_headers("catalog-approve"),
        json={"rationale": "An independent reviewer checked the binding."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["reviewedBy"] == REVIEWER
    assert approved.json()["status"] == "approved"

    stale = client.post(
        f"{_registrations_url()}/{registration_id}/approve",
        headers=_headers("catalog-stale-approve"),
        json={"rationale": "This transition is no longer pending."},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "evaluator_registration_transition_invalid"

    revoked = client.post(
        f"{_registrations_url()}/{registration_id}/revoke",
        headers=_headers("catalog-revoke"),
        json={"rationale": "The approved evaluator is no longer authorized."},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["revokedBy"] == REVIEWER

    active["token"] = _token(USER)
    rejected_submission = client.post(
        _registrations_url(),
        headers=_headers("catalog-reject-submit"),
        json=_binding_payload(evaluator_id="inspect-agent-security"),
    )
    assert rejected_submission.status_code == 201, rejected_submission.text
    active["token"] = _token(REVIEWER)
    rejected = client.post(
        f"{_registrations_url()}/{rejected_submission.json()['id']}/reject",
        headers=_headers("catalog-reject"),
        json={"rationale": "The independent review rejected this evaluator binding."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"


def test_catalog_list_is_explicitly_bounded_and_stably_paged(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    client, _active, factory, service = catalog_client
    _grant_catalog_permission(factory, "admin")
    registration_ids = [
        str(
            service.submit(
                organization_id=ORG,
                actor_id=USER,
                idempotency_key=f"catalog-page-{ordinal}",
                binding=EvaluatorIdentityBinding(
                    evaluator_id=f"inspect-page-{ordinal}",
                    source_type="external_provider",
                    adapter_name="inspect",
                    adapter_version="0.3.0",
                    result_contract_version="1.0.0",
                    issuer_id="issuer-a",
                    key_id="key-a",
                ),
            ).body["id"]
        )
        for ordinal in range(3)
    ]

    first_page = client.get(f"{_registrations_url()}?limit=2&offset=0")
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert isinstance(first_payload, dict)
    assert first_payload["limit"] == 2
    assert first_payload["offset"] == 0
    assert first_payload["hasMore"] is True
    assert [item["id"] for item in first_payload["items"]] == sorted(registration_ids)[:2]

    second_page = client.get(f"{_registrations_url()}?limit=2&offset=2")
    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert second_payload["limit"] == 2
    assert second_payload["offset"] == 2
    assert second_payload["hasMore"] is False
    assert [item["id"] for item in second_payload["items"]] == sorted(registration_ids)[2:]

    invalid_limit = client.get(f"{_registrations_url()}?limit=0")
    invalid_offset = client.get(f"{_registrations_url()}?offset=-1")
    invalid_large_offset = client.get(f"{_registrations_url()}?offset=10001")
    assert invalid_limit.status_code == invalid_offset.status_code == 422
    assert invalid_large_offset.status_code == 422


def test_catalog_get_list_and_transitions_do_not_disclose_foreign_registrations(
    catalog_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_catalog(monkeypatch)
    client, _active, factory, service = catalog_client
    _grant_catalog_permission(factory, "admin")

    foreign = service.submit(
        organization_id=FOREIGN_ORG,
        actor_id="foreign-submitter",
        idempotency_key="foreign-registration",
        binding=EvaluatorIdentityBinding(
            evaluator_id="foreign-inspect-agent",
            source_type="external_provider",
            adapter_name="inspect",
            adapter_version="0.3.0",
            result_contract_version="1.0.0",
            issuer_id="issuer-a",
            key_id="key-a",
        ),
    )
    foreign_id = str(foreign.body["id"])

    local_get = client.get(f"{_registrations_url()}/{foreign_id}")
    local_transition = client.post(
        f"{_registrations_url()}/{foreign_id}/reject",
        headers=_headers("foreign-transition"),
        json={"rationale": "Foreign registrations are not visible here."},
    )
    local_list = client.get(_registrations_url())
    foreign_path = client.get(f"{_registrations_url(FOREIGN_BASE)}/{foreign_id}")

    for response in (local_get, local_transition):
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "evaluator_registration_not_found"
    assert local_list.status_code == 200
    assert local_list.json() == {"items": [], "limit": 100, "offset": 0, "hasMore": False}
    assert foreign_path.status_code == 403
    assert foreign_path.json()["detail"] == "Organization membership required"


def test_catalog_composition_uses_the_audited_catalog_unit_of_work() -> None:
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)()
    try:
        service = build_evaluator_catalog_service(session)

        assert isinstance(service, EvaluatorCatalogService)
        assert isinstance(service._unit_of_work, SqlAlchemyEvaluatorCatalogUnitOfWork)
        assert isinstance(service._repository, SqlAlchemyEvaluatorCatalogRepository)
    finally:
        session.close()
        engine.dispose()

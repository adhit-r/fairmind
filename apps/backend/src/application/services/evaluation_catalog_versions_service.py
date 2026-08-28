"""Independent immutable target and suite version use cases for Assurance V2."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Mapping

from src.application.ports.evaluation_catalog_versions import (
    EvaluationCatalogVersionsUnitOfWork,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationOutcome,
    MutationResult,
    PersistSuiteCommand,
    PersistTargetCommand,
)
from src.application.services.evaluation_service_support import EvaluationServiceSupport
from src.application.evaluation_workbench_contracts import (
    _iso,
    _suite_view,
    _target_view,
    _translate,
    _verify_suite,
    _verify_target,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    normalize_suite_create,
    normalize_target_create,
)


class EvaluationCatalogVersionsService(EvaluationServiceSupport):
    """Create, read, and activate immutable V2 target and suite versions."""

    def __init__(self, unit_of_work: EvaluationCatalogVersionsUnitOfWork) -> None:
        super().__init__(unit_of_work)

    def create_target_version(
        self,
        *,
        org_id: str,
        system_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            target = normalize_target_create(payload)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.target.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "systemId": system_id},
            body=payload,
        )

        def create(now: datetime) -> MutationOutcome:
            scope = self.repository.load_system_scope(
                org_id=org_id,
                system_id=system_id,
                lock=True,
            )
            if scope is None:
                raise EvaluationWorkbenchError(
                    "binding_scope_mismatch",
                    "AI system is outside this organization scope.",
                    status_code=404,
                )
            if self.repository.target_identity_exists(
                scope=scope,
                target_key=str(target["targetKey"]),
                version=str(target["version"]),
            ):
                raise EvaluationWorkbenchError(
                    "immutable_version_conflict",
                    "This target key and version already exist in the system scope.",
                    status_code=409,
                )
            supersedes_id = target.get("supersedesId")
            if supersedes_id is not None:
                prior = self.repository.load_target_binding(
                    scope=scope,
                    target_version_id=str(supersedes_id),
                    lock=True,
                )
                if prior is None:
                    raise EvaluationWorkbenchError(
                        "binding_scope_mismatch",
                        "supersedesId is outside the target scope.",
                        status_code=422,
                    )
                _verify_target(prior)
                requested_lineage = (
                    target["targetKey"],
                    target["targetKind"],
                    target["subjectKind"],
                    target["subjectId"],
                )
                prior_lineage = (
                    prior.target_key,
                    prior.target_kind,
                    prior.subject_kind,
                    prior.subject_id,
                )
                if requested_lineage != prior_lineage:
                    raise EvaluationWorkbenchError(
                        "supersedes_lineage_mismatch",
                        "supersedesId must identify the same logical target and subject lineage.",
                        status_code=422,
                    )
                self.repository.cas_supersede_target(prior)
            target_id = str(uuid.uuid4())
            record = self.repository.persist_target(
                PersistTargetCommand(
                    target_id=target_id,
                    actor_id=actor_id,
                    requested=FrozenJsonObject.from_mapping(target),
                    scope=scope,
                    created_at=_iso(now),
                )
            )
            _verify_target(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_target_view(record)),
                status=201,
                resource_type="evaluation_target_version",
                resource_id=target_id,
                audit_action="evaluation_v2.target.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {"systemId": system_id, "manifestDigest": record.manifest_digest}
                ),
            )

        return self.unit_of_work.mutate(command, create)

    def list_target_versions(
        self, *, org_id: str, system_id: str
    ) -> list[Mapping[str, object]] | None:
        records = self.repository.list_target_bindings(org_id=org_id, system_id=system_id)
        if records is None:
            return None
        for record in records:
            _verify_target(record)
        return [_target_view(record) for record in records]

    def get_target_version(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
    ) -> Mapping[str, object] | None:
        scope = self.repository.load_system_scope(org_id=org_id, system_id=system_id, lock=False)
        if scope is None:
            return None
        record = self.repository.load_target_binding(
            scope=scope,
            target_version_id=target_version_id,
            lock=False,
        )
        if record is None:
            return None
        _verify_target(record)
        return _target_view(record)

    def create_suite_version(
        self,
        *,
        org_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            suite = normalize_suite_create(payload, owner_scope=org_id)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.suite.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id},
            body=payload,
        )

        def create(now: datetime) -> MutationOutcome:
            if self.repository.suite_identity_exists(
                org_id=org_id,
                namespace=str(suite["namespace"]),
                name=str(suite["name"]),
                version=str(suite["version"]),
            ):
                raise EvaluationWorkbenchError(
                    "immutable_version_conflict",
                    "This suite namespace, name, and version already exist in the owner scope.",
                    status_code=409,
                )
            suite_id = str(uuid.uuid4())
            record = self.repository.persist_suite(
                PersistSuiteCommand(
                    suite_id=suite_id,
                    actor_id=actor_id,
                    organization_id=org_id,
                    requested=FrozenJsonObject.from_mapping(suite),
                    created_at=_iso(now),
                )
            )
            _verify_suite(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_suite_view(record)),
                status=201,
                resource_type="evaluation_suite_version",
                resource_id=suite_id,
                audit_action="evaluation_v2.suite.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {"suiteRef": record.suite_ref, "manifestDigest": record.manifest_digest}
                ),
            )

        return self.unit_of_work.mutate(command, create)

    def list_suite_versions(self, *, org_id: str) -> list[Mapping[str, object]]:
        records = self.repository.list_suite_bindings(org_id=org_id)
        for record in records:
            _verify_suite(record)
        return [_suite_view(record) for record in records]

    def get_suite_version(
        self, *, org_id: str, suite_version_id: str
    ) -> Mapping[str, object] | None:
        record = self.repository.load_suite_binding(
            org_id=org_id,
            suite_version_id=suite_version_id,
            lock=False,
        )
        if record is None:
            return None
        _verify_suite(record)
        return _suite_view(record)

    def activate_suite_version(
        self,
        *,
        org_id: str,
        suite_version_id: str,
        actor_id: str,
        idempotency_key: str,
    ) -> MutationResult | None:
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.suite.activate",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "suiteVersionId": suite_version_id},
            body={},
        )

        def activate(_now: datetime) -> MutationOutcome:
            suite = self.repository.load_suite_binding(
                org_id=org_id,
                suite_version_id=suite_version_id,
                lock=True,
            )
            if suite is None:
                raise EvaluationWorkbenchError(
                    "suite_not_found", "Suite version was not found.", status_code=404
                )
            _verify_suite(suite)
            if suite.owner_scope != org_id:
                raise EvaluationWorkbenchError(
                    "suite_not_mutable",
                    "Platform suites cannot be mutated through a tenant route.",
                    status_code=403,
                )
            if suite.status not in {"draft", "active"}:
                raise EvaluationWorkbenchError(
                    "suite_not_activatable", "Suite cannot be activated.", status_code=409
                )
            action = "evaluation_v2.suite.activated" if suite.status == "draft" else None
            updated = self.repository.cas_activate_suite(suite=suite)
            _verify_suite(updated)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_suite_view(updated)),
                status=200,
                resource_type="evaluation_suite_version",
                resource_id=suite_version_id,
                audit_action=action,
                audit_details=FrozenJsonObject.from_mapping({"status": "active"}),
            )

        return self.unit_of_work.mutate(command, activate)


__all__ = ["EvaluationCatalogVersionsService"]

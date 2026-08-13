"""Pure evaluator-registration identity projections shared with persistence."""

from __future__ import annotations

from src.application.evaluator_registration import EvaluatorIdentityBinding
from src.domain.assurance.evaluation_v2 import canonical_sha256


def evaluator_binding_projection(binding: EvaluatorIdentityBinding) -> dict[str, str]:
    """Return the exact immutable tuple that a registration approves."""

    return {
        "evaluatorId": binding.evaluator_id,
        "sourceType": binding.source_type,
        "adapterName": binding.adapter_name,
        "adapterVersion": binding.adapter_version,
        "resultContractVersion": binding.result_contract_version,
        "issuerId": binding.issuer_id,
        "signingKeyId": binding.key_id,
    }


def evaluator_binding_hash(binding: EvaluatorIdentityBinding) -> str:
    """Return the immutable evaluator identity digest used by the repository."""

    return canonical_sha256(evaluator_binding_projection(binding))


__all__ = ["evaluator_binding_hash", "evaluator_binding_projection"]

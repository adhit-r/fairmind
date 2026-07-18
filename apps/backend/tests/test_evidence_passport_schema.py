"""Contract, domain, and canonical-hash tests for Evidence Passport 1.0.0."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import rfc8785
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError

from src.application.ports.evidence_ingestion import EvidenceScopeMismatch
from src.application.services.evidence_ingestion_service import EvidenceIngestionService
from src.domain.assurance.evidence_passport import (
    EvidencePassport,
    EvidencePassportValidationError,
    calculate_canonical_content_hash,
    calculate_run_content_hash,
    canonical_snapshot_projection,
    rfc8785_sha256,
    run_content_projection,
    validate_public_ingestion,
    with_server_hashes,
)

SCHEMA_PATH = Path(__file__).parents[3] / "docs/product/evidence-passport.schema.json"
PACKAGED_SCHEMA_PATH = (
    Path(__file__).parents[1] / "src/domain/assurance/evidence-passport.schema.json"
)


def golden_passport() -> dict:
    """Return a complete revision-1 exchange document with client hash slots."""
    return {
        "schemaVersion": "1.0.0",
        "passportId": "passport-001",
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": "org-001",
        "workspaceId": "workspace-001",
        "aiSystem": {
            "systemId": "system-001",
            "name": "Underwriting model",
            "kind": "model",
            "version": "2026.07",
            "identityHash": "1" * 64,
            "deploymentId": "deployment-001",
            "ownerId": "owner-001",
            "intendedUse": "Support bounded underwriting decisions.",
        },
        "evaluation": {
            "sourceType": "fairmind_evaluation",
            "sourceIdentifier": "fairmind-bias-suite",
            "runId": "run-001",
            "capabilityState": "validated",
            "assuranceSource": "fairmind_internal",
            "evaluator": {
                "name": "FairMind evaluator",
                "version": "2.0.0",
                "adapterName": "passport-adapter",
                "adapterVersion": "1.0.0",
                "runnerVersion": "3.0.0",
                "runnerDigest": "2" * 64,
                "codeCommit": "abcdef1",
            },
            "suite": {
                "name": "Bias and subgroup parity",
                "version": "2026.07",
                "taxonomy": "fairness",
                "trigger": "release_gate",
            },
            "subject": {
                "kind": "model",
                "subjectId": "subject-001",
                "name": "Underwriting model",
                "version": "2026.07",
                "digest": "3" * 64,
                "provider": "FairMind test fixture",
                "endpoint": "https://models.example.test/underwriting",
            },
            "scope": {
                "intendedUse": "Evaluate parity on a bounded synthetic set.",
                "inputFingerprint": "4" * 64,
                "datasetName": "Synthetic applicants",
                "datasetVersion": "1.0",
                "datasetHash": "5" * 64,
                "sampleCount": 100,
                "protectedGroups": ["age", "gender"],
                "locales": ["en-IN"],
                "exclusions": ["No production applicant records."],
            },
            "configurationHash": "6" * 64,
            "seed": 42,
            "thresholds": [
                {
                    "metric": "demographic_parity_difference",
                    "operator": "lte",
                    "value": 0.1,
                    "unit": "ratio",
                    "preRegisteredAt": "2026-07-17T23:59:59Z",
                    "rationale": "Release threshold chosen before the run.",
                }
            ],
            "environment": {
                "operatingSystem": "linux",
                "architecture": "arm64",
                "runtime": "python-3.13",
                "containerDigest": "7" * 64,
                "region": "ap-south-1",
                "hardware": "cpu",
            },
            "result": {
                "status": "failed",
                "summary": "The preregistered parity threshold was not met.",
                "metrics": [
                    {
                        "name": "demographic_parity_difference",
                        "value": 0.2,
                        "unit": "ratio",
                        "slice": "gender",
                        "thresholdMet": False,
                        "confidenceInterval": {"lower": 0.15, "upper": 0.25, "level": 0.95},
                    }
                ],
                "confidence": 0.9,
                "startedAt": "2026-07-18T00:00:00Z",
                "endedAt": "2026-07-18T00:05:00Z",
            },
            "runContentHash": "0" * 64,
            "capturedAt": "2026-07-18T00:05:00Z",
            "expiresAt": "2026-10-18T00:05:00Z",
            "limitations": ["Synthetic test set only."],
        },
        "artifacts": [
            {
                "artifactId": "artifact-report",
                "role": "report",
                "uri": "s3://evidence/run-001/report.json",
                "sha256": "8" * 64,
                "mediaType": "application/json",
                "sizeBytes": 1024,
                "containsSensitiveData": False,
                "retentionPolicy": "retain-365-days",
            },
            {
                "artifactId": "artifact-log",
                "role": "log",
                "uri": "https://evidence.example.test/run-001/log.txt",
                "sha256": "9" * 64,
                "mediaType": "text/plain",
                "sizeBytes": 512,
                "containsSensitiveData": False,
                "redactionNote": "Fixture identifiers only.",
            },
        ],
        "frameworkMappings": [
            {
                "mappingId": "mapping-001",
                "framework": {
                    "key": "generic",
                    "versionLabel": "1",
                    "sourceHash": "a" * 64,
                    "sourceUri": "https://frameworks.example.test/generic/1",
                },
                "control": {"externalId": "CTRL-1", "assessmentId": "assessment-001"},
                "state": "candidate",
                "relation": "supports",
                "rationale": "The bounded result may support a human review.",
                "suggestedBy": {
                    "actorType": "adapter",
                    "actorId": "adapter-001",
                    "displayName": "FairMind adapter",
                },
                "createdAt": "2026-07-18T00:05:00Z",
            }
        ],
        "review": {"status": "pending", "reviewVersion": 0},
        "findings": [
            {
                "findingId": "finding-001",
                "severity": "high",
                "status": "open",
                "title": "Parity threshold missed",
                "description": "Observed value exceeded the preregistered threshold.",
                "artifactIds": ["artifact-report"],
                "createdAt": "2026-07-18T00:05:00Z",
            }
        ],
        "remediation": [
            {
                "remediationId": "remediation-001",
                "findingIds": ["finding-001"],
                "status": "planned",
                "ownerId": "owner-001",
                "action": "Investigate the failed slice before release.",
                "dueAt": "2026-07-25T00:00:00Z",
            }
        ],
        "freshness": {
            "status": "current",
            "policy": "Re-evaluate on system, subject, or data change.",
            "assessedAt": "2026-07-18T00:05:00Z",
            "expiresAt": "2026-10-18T00:05:00Z",
            "staleReasons": [],
            "invalidationKeys": ["system_version", "subject_digest", "dataset_hash"],
        },
        "lineage": {"predecessorPassportIds": [], "retestOfPassportIds": []},
        "createdAt": "2026-07-18T00:05:00Z",
        "canonicalContentHash": "0" * 64,
    }


def server_hashed_passport(**updates: object) -> dict:
    payload = golden_passport()
    payload.update(updates)
    return with_server_hashes(EvidencePassport.model_validate(payload)).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_checked_in_schema_is_draft_2020_12_and_golden_round_trips(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    passport = server_hashed_passport()
    validator.validate(passport)
    model = EvidencePassport.model_validate(passport)
    protocol = model.model_dump(by_alias=True, mode="json", exclude_none=True)
    validator.validate(protocol)
    assert protocol == passport


def test_packaged_runtime_schema_is_byte_identical_to_published_contract() -> None:
    assert PACKAGED_SCHEMA_PATH.read_bytes() == SCHEMA_PATH.read_bytes()


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ((), {"unknownProperty": True}),
        (("aiSystem",), {"unknownProperty": True}),
        (("evaluation", "result"), {"prompt": "do not retain"}),
        (("artifacts", 0), {"body": "raw output"}),
    ],
)
def test_unknown_and_raw_body_properties_are_rejected(path: tuple, value: dict) -> None:
    payload = golden_passport()
    target: object = payload
    for part in path:
        target = target[part]  # type: ignore[index]
    assert isinstance(target, dict)
    target.update(value)
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    "path",
    [
        ("aiSystem", "identityHash"),
        ("evaluation", "configurationHash"),
        ("evaluation", "evaluator", "runnerDigest"),
        ("evaluation", "subject", "digest"),
        ("evaluation", "scope", "inputFingerprint"),
        ("evaluation", "scope", "datasetHash"),
        ("evaluation", "environment", "containerDigest"),
        ("artifacts", 0, "sha256"),
        ("frameworkMappings", 0, "framework", "sourceHash"),
        ("evaluation", "runContentHash"),
        ("canonicalContentHash",),
    ],
)
@pytest.mark.parametrize("bad", ["A" * 64, "a" * 63, "g" * 64])
def test_every_digest_field_requires_64_lowercase_hex(path: tuple, bad: str) -> None:
    payload = golden_passport()
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = bad
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("artifacts", 0, "uri"), "not a uri"),
        (("artifacts", 0, "uri"), "data:text/plain,inline"),
        (("artifacts", 0, "uri"), "file:///tmp/raw.json"),
        (("artifacts", 0, "mediaType"), "application"),
        (("frameworkMappings", 0, "framework", "sourceUri"), "/tmp/framework.json"),
        (("frameworkMappings", 0, "framework", "sourceUri"), "file:///tmp/framework.json"),
    ],
)
def test_uri_and_media_type_policy_fails_closed(path: tuple, value: str) -> None:
    payload = golden_passport()
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("evaluation", "subject", "endpoint"), "data:text/plain,inline"),
        (("evaluation", "subject", "endpoint"), "file:///tmp/model.bin"),
        (("evaluation", "subject", "endpoint"), "/tmp/model.bin"),
        (("frameworkMappings", 0, "framework", "sourceUri"), "data:text/plain,inline"),
    ],
)
def test_every_uri_field_rejects_inline_and_local_locations(path: tuple, value: str) -> None:
    payload = golden_passport()
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-18 00:00:00Z",
        "2026-07-18T00:00:00",
        "20260718T000000Z",
        "2026-07-18T00:00:00,123Z",
    ],
)
def test_non_rfc3339_datetime_lexemes_fail_at_ingestion_before_storage(value: str) -> None:
    payload = server_hashed_passport()
    payload["createdAt"] = value
    store = _HashMismatchStore()
    with pytest.raises(EvidencePassportValidationError):
        EvidenceIngestionService(store).ingest(payload, org_id="org-001", actor_id="user-001")
    assert store.calls == 0


def test_schema_valid_lowercase_rfc3339_datetime_is_accepted_by_domain_model() -> None:
    payload = golden_passport()
    payload["createdAt"] = "2026-07-18t00:05:00z"
    assert EvidencePassport.model_validate(payload).created_at == payload["createdAt"]


@pytest.mark.parametrize("count", [0, 51])
def test_artifact_count_is_bounded(count: int) -> None:
    payload = golden_passport()
    payload["artifacts"] = [deepcopy(payload["artifacts"][0]) for _ in range(count)]
    for index, artifact in enumerate(payload["artifacts"]):
        artifact["artifactId"] = f"artifact-{index:03d}"
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


def test_artifact_ids_and_local_references_are_unique_and_resolved() -> None:
    duplicate = golden_passport()
    duplicate["artifacts"][1]["artifactId"] = duplicate["artifacts"][0]["artifactId"]
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(duplicate)

    dangling_finding = golden_passport()
    dangling_finding["findings"][0]["artifactIds"] = ["missing-artifact"]
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(dangling_finding)

    dangling_remediation = golden_passport()
    dangling_remediation["remediation"][0]["findingIds"] = ["missing-finding"]
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(dangling_remediation)


@pytest.mark.parametrize(
    "mutation",
    [
        {"sourceType": "third_party_assessment", "assuranceSource": "third_party"},
        {"sourceType": "fairmind_evaluation", "assuranceSource": "third_party"},
    ],
)
def test_third_party_sources_require_independent_assessor(mutation: dict) -> None:
    payload = golden_passport()
    payload["evaluation"].update(mutation)
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)
    payload["evaluation"]["thirdPartyAssessor"] = {
        "identity": "Independent Assurance Co.",
        "independenceAssertion": False,
    }
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    ("capability", "status"),
    [("unavailable", "passed"), ("insufficient_data", "failed")],
)
def test_capability_state_requires_matching_result(capability: str, status: str) -> None:
    payload = golden_passport()
    payload["evaluation"]["capabilityState"] = capability
    payload["evaluation"]["result"]["status"] = status
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize("status", ["unavailable", "error"])
def test_unavailable_and_error_require_limitations_and_diagnostic_log(status: str) -> None:
    payload = golden_passport()
    payload["evaluation"]["capabilityState"] = (
        "unavailable" if status == "unavailable" else "validated"
    )
    payload["evaluation"]["result"]["status"] = status
    payload["evaluation"]["limitations"] = []
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)
    payload["evaluation"]["limitations"] = ["Evaluator dependency unavailable."]
    payload["artifacts"] = [payload["artifacts"][0]]
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        "accepted_mapping_without_review",
        "mapping_review_mismatch",
        "candidate_with_review",
        "reviewed_passport_without_fields",
        "pending_passport_with_fields",
        "revision_two_without_previous",
        "revision_one_with_previous",
        "completed_without_time",
        "verified_without_passport",
        "superseded_without_passport",
    ],
)
def test_review_revision_remediation_and_freshness_conditionals(mutate: str) -> None:
    payload = golden_passport()
    mapping = payload["frameworkMappings"][0]
    if mutate == "accepted_mapping_without_review":
        mapping["state"] = "accepted"
    elif mutate == "mapping_review_mismatch":
        mapping["state"] = "accepted"
        mapping["review"] = {
            "decision": "rejected",
            "reviewer": {"actorType": "user", "actorId": "reviewer-001"},
            "reviewedAt": "2026-07-18T01:00:00Z",
            "rationale": "Mismatch",
            "reviewVersion": 1,
        }
    elif mutate == "candidate_with_review":
        mapping["review"] = {
            "decision": "accepted",
            "reviewer": {"actorType": "user", "actorId": "reviewer-001"},
            "reviewedAt": "2026-07-18T01:00:00Z",
            "rationale": "Premature",
            "reviewVersion": 1,
        }
    elif mutate == "reviewed_passport_without_fields":
        payload["review"] = {"status": "accepted", "reviewVersion": 1}
    elif mutate == "pending_passport_with_fields":
        payload["review"].update(
            {
                "reviewer": {"actorType": "user", "actorId": "reviewer-001"},
                "reviewedAt": "2026-07-18T01:00:00Z",
                "rationale": "Ambiguous pending decision",
            }
        )
    elif mutate == "revision_two_without_previous":
        payload["passportRevision"] = 2
    elif mutate == "revision_one_with_previous":
        payload["previousRevisionHash"] = "b" * 64
    elif mutate == "completed_without_time":
        payload["remediation"][0]["status"] = "completed"
    elif mutate == "verified_without_passport":
        payload["remediation"][0].update(
            {"status": "verified", "completedAt": "2026-07-18T02:00:00Z"}
        )
    elif mutate == "superseded_without_passport":
        payload["freshness"]["status"] = "superseded"
    with pytest.raises(ValidationError):
        EvidencePassport.model_validate(payload)


@pytest.mark.parametrize(
    "mutation",
    ["revision", "previous", "accepted_review", "accepted_mapping", "mapping_review", "signature"],
)
def test_public_ingestion_is_revision_one_pending_candidate_only_and_unsigned(
    mutation: str,
) -> None:
    payload = golden_passport()
    if mutation == "revision":
        payload["passportRevision"] = 2
        payload["previousRevisionHash"] = "b" * 64
    elif mutation == "previous":
        payload["previousRevisionHash"] = "b" * 64
    elif mutation == "accepted_review":
        payload["review"] = {
            "status": "accepted",
            "reviewVersion": 1,
            "reviewer": {"actorType": "user", "actorId": "reviewer-001"},
            "reviewedAt": "2026-07-18T01:00:00Z",
            "rationale": "Server-only decision",
        }
    elif mutation in {"accepted_mapping", "mapping_review"}:
        payload["frameworkMappings"][0].update(
            {
                "state": "accepted" if mutation == "accepted_mapping" else "candidate",
                "review": {
                    "decision": "accepted",
                    "reviewer": {"actorType": "user", "actorId": "reviewer-001"},
                    "reviewedAt": "2026-07-18T01:00:00Z",
                    "rationale": "Server-only decision",
                    "reviewVersion": 1,
                },
            }
        )
    else:
        payload["signatures"] = [
            {
                "algorithm": "Ed25519",
                "keyId": "key-001",
                "signedAt": "2026-07-18T01:00:00Z",
                "value": "AAAAAAAAAAAAAAAA",
            }
        ]
    try:
        passport = EvidencePassport.model_validate(payload)
    except ValidationError:
        return
    with pytest.raises(EvidencePassportValidationError):
        validate_public_ingestion(passport)


def test_rfc8785_official_style_number_and_unicode_vectors() -> None:
    assert rfc8785.dumps([333333333.33333329, 1e30, 4.50, 2e-3, 1e-27]) == (
        b"[333333333.3333333,1e+30,4.5,0.002,1e-27]"
    )
    assert rfc8785.dumps({"z": "\u00e9", "a": "\u20ac"}) == (
        '{"a":"\u20ac","z":"\u00e9"}'.encode("utf-8")
    )
    assert rfc8785_sha256({"b": 2, "a": 1}) == rfc8785_sha256({"a": 1, "b": 2})


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("evaluation", "thresholds", 0, "value"), 0.2),
        (("aiSystem", "version"), "2026.08"),
        (("evaluation", "subject", "version"), "2026.08"),
        (("evaluation", "subject", "digest"), "b" * 64),
        (("evaluation", "scope", "datasetHash"), "b" * 64),
        (("evaluation", "scope", "inputFingerprint"), "b" * 64),
        (("evaluation", "evaluator", "version"), "2.0.1"),
        (("evaluation", "evaluator", "adapterVersion"), "1.0.1"),
        (("evaluation", "evaluator", "runnerVersion"), "3.0.1"),
        (("evaluation", "suite", "version"), "2026.08"),
        (("evaluation", "scope", "sampleCount"), 101),
        (("evaluation", "result", "summary"), "Changed bounded result."),
        (("evaluation", "limitations", 0), "Changed limitation."),
        (("artifacts", 0, "sizeBytes"), 2048),
    ],
)
def test_run_hash_changes_for_every_immutable_execution_family(path: tuple, value: object) -> None:
    before = EvidencePassport.model_validate(golden_passport())
    mutated = golden_passport()
    target = mutated
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    after = EvidencePassport.model_validate(mutated)
    assert calculate_run_content_hash(before) != calculate_run_content_hash(after)


def test_run_hash_includes_artifact_order_but_excludes_mutable_snapshot_state() -> None:
    before = EvidencePassport.model_validate(golden_passport())
    reordered = golden_passport()
    reordered["artifacts"].reverse()
    assert calculate_run_content_hash(before) != calculate_run_content_hash(
        EvidencePassport.model_validate(reordered)
    )

    mutable = golden_passport()
    mutable["passportId"] = "passport-999"
    mutable["passportRevision"] = 2
    mutable["previousRevisionHash"] = "b" * 64
    mutable["frameworkMappings"] = []
    mutable["review"] = {"status": "pending", "reviewVersion": 4}
    mutable["findings"] = []
    mutable["remediation"] = []
    mutable["freshness"]["policy"] = "Changed policy."
    mutable["lineage"]["predecessorPassportIds"] = ["passport-previous"]
    mutable["signatures"] = [
        {
            "algorithm": "Ed25519",
            "keyId": "key-001",
            "signedAt": "2026-07-18T01:00:00Z",
            "value": "AAAAAAAAAAAAAAAA",
        }
    ]
    assert calculate_run_content_hash(before) == calculate_run_content_hash(
        EvidencePassport.model_validate(mutable)
    )


@pytest.mark.parametrize(
    "field", ["frameworkMappings", "review", "remediation", "freshness", "lineage"]
)
def test_canonical_hash_changes_for_mutable_snapshot_state(field: str) -> None:
    before = EvidencePassport.model_validate(golden_passport())
    mutated = golden_passport()
    if field == "frameworkMappings":
        mutated[field] = []
    elif field == "review":
        mutated[field]["reviewVersion"] = 1
    elif field == "remediation":
        mutated[field][0]["action"] = "Changed action."
    elif field == "freshness":
        mutated[field]["policy"] = "Changed freshness policy."
    else:
        mutated[field]["predecessorPassportIds"] = ["passport-previous"]
    after = EvidencePassport.model_validate(mutated)
    assert calculate_canonical_content_hash(before) != calculate_canonical_content_hash(after)


def test_hash_projections_are_exact_and_canonical_omits_only_self_and_signatures() -> None:
    passport = EvidencePassport.model_validate(golden_passport())
    run_projection = run_content_projection(passport)
    assert list(run_projection) == ["schemaVersion", "aiSystem", "evaluation", "artifacts"]
    assert "runContentHash" not in run_projection["evaluation"]
    assert "organizationId" not in run_projection

    canonical = canonical_snapshot_projection(passport)
    assert "canonicalContentHash" not in canonical
    assert "signatures" not in canonical
    assert canonical["evaluation"]["runContentHash"] == "0" * 64
    assert canonical["passportRevision"] == 1


class _HashMismatchStore:
    def __init__(self) -> None:
        self.calls = 0

    def scoped_system(self, *_args: object, **_kwargs: object) -> object:
        self.calls += 1
        raise AssertionError("hash mismatch must fail before store access")


@pytest.mark.parametrize(
    "path",
    [
        ("aiSystem", "ownerId"),
        ("evaluation", "evaluator", "runnerDigest"),
        ("evaluation", "subject", "endpoint"),
        ("evaluation", "result", "confidence"),
        ("artifacts", 0, "sizeBytes"),
        ("frameworkMappings", 0, "framework", "sourceUri"),
        ("remediation", 0, "completedAt"),
        ("freshness", "expiresAt"),
    ],
)
def test_explicit_null_is_rejected_by_raw_schema_before_store_access(path: tuple) -> None:
    payload = server_hashed_passport()
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = None
    store = _HashMismatchStore()

    with pytest.raises(EvidencePassportValidationError):
        EvidenceIngestionService(store).ingest(payload, org_id="org-001", actor_id="user-001")

    assert store.calls == 0


@pytest.mark.parametrize("field", ["run", "canonical"])
def test_client_hash_mismatch_fails_before_storage(field: str) -> None:
    payload = server_hashed_passport()
    if field == "run":
        payload["evaluation"]["runContentHash"] = "f" * 64
    else:
        payload["canonicalContentHash"] = "f" * 64
    store = _HashMismatchStore()
    with pytest.raises(EvidencePassportValidationError):
        EvidenceIngestionService(store).ingest(payload, org_id="org-001", actor_id="user-001")
    assert store.calls == 0


def test_service_scope_validation_is_explicit() -> None:
    payload = server_hashed_passport(organizationId="org-002")
    with pytest.raises(EvidenceScopeMismatch):
        EvidenceIngestionService(_HashMismatchStore()).ingest(
            payload, org_id="org-001", actor_id="user-001"
        )

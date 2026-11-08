"""Evaluation input artifact store: moto S3, PostgreSQL 013n guards, and the upload route."""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

from botocore.exceptions import ClientError

import boto3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from api.routes.evaluation_artifacts import (
    evaluation_artifacts_router,
    get_evaluation_artifact_service_builder,
)
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from config.settings import settings
from database.connection import get_db
from database.models import Organization, OrganizationMember, OrganizationRole, User
from src.application.ports.evaluation_artifacts import ArtifactStoreError
from src.application.services.evaluation_artifact_service import (
    ArtifactUploadError,
    EvaluationArtifactService,
    scan_input,
)
from src.infrastructure.db.repositories.evaluation_artifact_repository import (
    SqlAlchemyEvaluationArtifactRepository,
)
from src.infrastructure.storage.s3_artifact_store import S3ArtifactStore

BUCKET = "fairmind-artifact-test"
PREFIX = "inputs/"
MAX_BYTES = 1 << 20
PERMISSION = "evaluation:artifact:upload"
CLEAN_CSV = b"id,label,prediction\n1,0,0\n2,1,1\n"


@pytest.fixture(scope="module")
def factory():
    engine = create_engine(os.environ["DATABASE_URL"])
    yield sessionmaker(bind=engine)
    engine.dispose()


@pytest.fixture
def s3():
    with mock_aws():
        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="moto",
            aws_secret_access_key="moto",
        )
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture
def store(s3):
    return S3ArtifactStore(s3, bucket=BUCKET, prefix=PREFIX, max_bytes=MAX_BYTES)


def _service(session, store) -> EvaluationArtifactService:
    return EvaluationArtifactService(
        SqlAlchemyEvaluationArtifactRepository(session), store, max_bytes=MAX_BYTES
    )


def _upload(factory, store, org_id: str, data: bytes, media_type: str = "text/csv"):
    with factory() as session:
        return _service(session, store).upload(
            organization_id=org_id, actor_id=str(uuid.uuid4()), media_type=media_type, data=data
        )


def _rows(factory, org_id: str) -> list[dict]:
    with factory() as session:
        return [
            dict(row)
            for row in session.execute(
                text("SELECT * FROM governance_evaluation_artifacts WHERE org_id = :o"),
                {"o": org_id},
            ).mappings()
        ]


def _audit(factory, org_id: str) -> list[dict]:
    with factory() as session:
        return [
            dict(row)
            for row in session.execute(
                text(
                    "SELECT action, outcome, details_json FROM governance_evaluation_audit_events "
                    "WHERE org_id = :o ORDER BY sequence_number"
                ),
                {"o": org_id},
            ).mappings()
        ]


def _objects(s3) -> list[str]:
    return [item["Key"] for item in s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])]


CSV, JSON = "text/csv", "application/json"


def test_scan_input_uses_fixed_reason_codes() -> None:
    assert scan_input(CLEAN_CSV, CSV) is None
    assert scan_input(b'{"rows": [{"id": 1, "label": "a", "prompt_tokens": 12}]}', JSON) is None
    assert scan_input(b"id,key\n1,AKIAABCDEFGHIJKLMNOP\n", CSV) == "credential_detected"
    assert scan_input(b'{"api_key": "abcd1234efgh5678"}', JSON) == "credential_detected"
    assert scan_input(b"-----BEGIN PRIVATE KEY-----\nMIIE\n", CSV) == "private_key_detected"
    assert scan_input(b"-----BEGIN EC PRIVATE KEY-----\n", CSV) == "private_key_detected"
    assert scan_input(b"id,text\n1,<think>step one</think>\n", CSV) == "chain_of_thought_detected"
    assert scan_input(b'{"reasoning_content": "x"}', JSON) == "chain_of_thought_detected"
    assert scan_input(b"\xff\xfe", CSV) == "undecodable_content"
    assert scan_input(b"a\x00b", CSV) == "undecodable_content"
    assert scan_input(b'{"id": 1', JSON) == "undecodable_content"


@pytest.mark.parametrize(
    ("data", "media_type", "reason"),
    [
        # JSON string escapes are decoded before the patterns run.
        (
            b'{"k": "\\u002d\\u002d\\u002d\\u002d\\u002dBEGIN RSA PRIVATE KEY-----\\nMIIE"}',
            JSON,
            "private_key_detected",
        ),
        (b'{"k": "\\u0041KIAABCDEFGHIJKLMNOP"}', JSON, "credential_detected"),
        (b'{"password": "hunter2hunter2"}', JSON, "credential_detected"),
        (b'{"pass\\u0077ord": "hunter2"}', JSON, "credential_detected"),
        (
            b'{"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}',
            JSON,
            "credential_detected",
        ),
        (b'{"clientConfig": {"apiKey": "abc"}}', JSON, "credential_detected"),
        (b'[{"id": 1}, {"id": 2, "access_token": "abc"}]', JSON, "credential_detected"),
        # A duplicate key cannot hide the first value.
        (b'{"secret": "abc", "secret": ""}', JSON, "credential_detected"),
        # A credential-named CSV column with values, in any position.
        (b"user,password\nalice,Tr0ub4dor&3xyz\n", CSV, "credential_detected"),
        (b"id,AWS Secret Access Key,label\n1,abc,0\n", CSV, "credential_detected"),
        (b'id,note\n1,"-----BEGIN OPENSSH PRIVATE KEY-----"\n', CSV, "private_key_detected"),
    ],
)
def test_scan_input_decodes_before_matching(data: bytes, media_type: str, reason: str) -> None:
    assert scan_input(data, media_type) == reason


def test_scan_input_allows_empty_credential_columns_and_plain_names() -> None:
    assert scan_input(b"user,password\nalice,\nbob, \n", CSV) is None
    assert scan_input(b'{"password": "", "tokens": ["a", "b"], "label": 1}', JSON) is None
    assert scan_input(b"id,keyword,label\n1,secretary,0\n", CSV) is None


def test_moto_round_trip_promotes_and_replays(factory, store, s3) -> None:
    org = str(uuid.uuid4())
    digest = hashlib.sha256(CLEAN_CSV).hexdigest()

    first = _upload(factory, store, org, CLEAN_CSV)
    assert first.created is True
    assert first.record.state == "available"
    assert first.record.sha256 == digest
    assert first.record.scan_policy == "fairmind-input-scan-v1"
    assert _objects(s3) == [f"{PREFIX}sha256/{digest}"]
    assert store.get_verified(digest) == CLEAN_CSV

    replay = _upload(factory, store, org, CLEAN_CSV)
    assert replay.created is False
    assert replay.record == first.record
    rows = _rows(factory, org)
    assert len(rows) == 1 and rows[0]["storage_key"] == f"sha256/{digest}"
    assert [(e["action"], e["outcome"]) for e in _audit(factory, org)] == [
        ("evaluation_artifact.uploaded", "success"),
        ("evaluation_artifact.promoted", "success"),
    ]


def test_store_refuses_overwrite_and_checksum_mismatch_on_read_fails(store, s3) -> None:
    digest = hashlib.sha256(CLEAN_CSV).hexdigest()
    assert store.put_if_absent(digest, CLEAN_CSV, "text/csv") is True
    assert store.put_if_absent(digest, CLEAN_CSV, "text/csv") is False
    with pytest.raises(ArtifactStoreError) as wrong_digest:
        store.put_if_absent("0" * 64, CLEAN_CSV, "text/csv")
    assert wrong_digest.value.code == "stored_digest_mismatch"

    # Tamper with the stored object out of band (the adapter itself cannot overwrite).
    s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}sha256/{digest}", Body=b"id\n9\n")
    with pytest.raises(ArtifactStoreError) as mismatch:
        store.get_verified(digest)
    assert mismatch.value.code == "stored_digest_mismatch"
    with pytest.raises(ArtifactStoreError) as missing:
        store.get_verified("a" * 64)
    assert missing.value.code == "stored_object_missing"
    assert not hasattr(store, "delete") and not hasattr(store, "list")


class _LeastPrivilegeClient:
    """moto does not enforce IAM. Without s3:ListBucket, real S3 answers GetObject
    on an absent key with 403 AccessDenied, and a conditional write can see 409."""

    def __init__(self, inner, put_error: str | None = None) -> None:
        self._inner = inner
        self.put_error = put_error

    def put_object(self, **kwargs):
        if self.put_error is not None:
            raise ClientError({"Error": {"Code": self.put_error}}, "PutObject")
        return self._inner.put_object(**kwargs)

    def get_object(self, **kwargs):
        try:
            return self._inner.get_object(**kwargs)
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                raise ClientError(
                    {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GetObject"
                ) from None
            raise


def test_conditional_write_conflict_is_unavailable_not_existing(factory, s3) -> None:
    client = _LeastPrivilegeClient(s3, put_error="ConditionalRequestConflict")
    store = S3ArtifactStore(client, bucket=BUCKET, prefix=PREFIX, max_bytes=MAX_BYTES)
    digest = hashlib.sha256(CLEAN_CSV).hexdigest()
    with pytest.raises(ArtifactStoreError) as conflict:
        store.put_if_absent(digest, CLEAN_CSV, "text/csv")
    assert conflict.value.code == "store_unavailable"

    org = str(uuid.uuid4())
    with pytest.raises(ArtifactUploadError) as unavailable:
        _upload(factory, store, org, CLEAN_CSV)
    assert unavailable.value.code == "artifact_store_unavailable"
    assert _rows(factory, org) == [] and _objects(s3) == []

    # Once the conflicting operation is over, the same bytes upload normally.
    client.put_error = None
    assert _upload(factory, store, org, CLEAN_CSV).record.state == "available"


def test_missing_object_under_least_privilege_stays_quarantined_until_replay(
    factory, s3
) -> None:
    store = S3ArtifactStore(
        _LeastPrivilegeClient(s3), bucket=BUCKET, prefix=PREFIX, max_bytes=MAX_BYTES
    )
    org = str(uuid.uuid4())
    data = b"id,score\n1,0.25\n"
    digest = hashlib.sha256(data).hexdigest()
    with pytest.raises(ArtifactStoreError) as denied:
        store.get_verified(digest)
    assert denied.value.code == "store_unavailable"

    with factory() as session:
        row = SqlAlchemyEvaluationArtifactRepository(session).insert_quarantined(
            organization_id=org, sha256=digest, media_type="text/csv",
            size_bytes=len(data), scan_policy="fairmind-input-scan-v1",
        )
        session.commit()
    with factory() as session, pytest.raises(ArtifactUploadError) as unavailable:
        _service(session, store).promote(
            organization_id=org, artifact_id=row.artifact_id, actor_id=str(uuid.uuid4())
        )
    assert unavailable.value.code == "artifact_store_unavailable"
    assert [r["state"] for r in _rows(factory, org)] == ["quarantined"]

    replay = _upload(factory, store, org, data)
    assert replay.created is False
    assert replay.record.artifact_id == row.artifact_id
    assert replay.record.state == "available"
    assert _objects(s3) == [f"{PREFIX}sha256/{digest}"]


def test_promotion_re_verifies_the_stored_object(factory, store, s3) -> None:
    org = str(uuid.uuid4())
    digest = hashlib.sha256(CLEAN_CSV).hexdigest()
    # The object under this digest holds different bytes: promotion must reject.
    s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}sha256/{digest}", Body=b"id\n9\n")

    result = _upload(factory, store, org, CLEAN_CSV)
    assert result.record.state == "rejected"
    assert result.record.rejection_reason == "stored_digest_mismatch"
    events = _audit(factory, org)
    assert events[-1]["action"] == "evaluation_artifact.promotion_rejected"
    assert json.loads(events[-1]["details_json"])["reasonCode"] == "stored_digest_mismatch"

    # A row stuck in quarantine whose object never landed: the replay re-writes it.
    other_org = str(uuid.uuid4())
    other = b"id,score\n1,0.5\n"
    with factory() as session:
        repository = SqlAlchemyEvaluationArtifactRepository(session)
        repository.insert_quarantined(
            organization_id=other_org,
            sha256=hashlib.sha256(other).hexdigest(),
            media_type="text/csv",
            size_bytes=len(other),
            scan_policy="fairmind-input-scan-v1",
        )
        session.commit()
    replay = _upload(factory, store, other_org, other)
    assert replay.created is False
    assert replay.record.state == "available"
    assert store.get_verified(hashlib.sha256(other).hexdigest()) == other


def test_concurrent_uploads_of_one_digest_yield_one_row_and_one_object(
    factory, store, s3
) -> None:
    org = str(uuid.uuid4())
    workers = 6
    barrier = Barrier(workers)

    def upload(_):
        barrier.wait()
        return _upload(factory, store, org, CLEAN_CSV)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(upload, range(workers)))

    assert sum(result.created for result in results) == 1
    assert {result.record.artifact_id for result in results} == {results[0].record.artifact_id}
    assert {result.record.state for result in results} == {"available"}
    assert len(_rows(factory, org)) == 1
    assert _objects(s3) == [f"{PREFIX}sha256/{hashlib.sha256(CLEAN_CSV).hexdigest()}"]


def test_promotion_serializes_on_the_quarantined_row_lock(factory, store, s3) -> None:
    """A second promoter blocks on the row lock and, once the first commits,
    sees no quarantined row: no second transition and no second audit event."""

    org = str(uuid.uuid4())
    digest = hashlib.sha256(CLEAN_CSV).hexdigest()
    assert store.put_if_absent(digest, CLEAN_CSV, "text/csv") is True
    with factory() as session:
        row = SqlAlchemyEvaluationArtifactRepository(session).insert_quarantined(
            organization_id=org, sha256=digest, media_type="text/csv",
            size_bytes=len(CLEAN_CSV), scan_policy="fairmind-input-scan-v1",
        )
        session.commit()

    def promote_in_other_session():
        with factory() as session:
            return _service(session, store).promote(
                organization_id=org, artifact_id=row.artifact_id, actor_id=str(uuid.uuid4())
            )

    with factory() as holder, ThreadPoolExecutor(max_workers=1) as pool:
        repository = SqlAlchemyEvaluationArtifactRepository(holder)
        assert repository.lock_quarantined(
            organization_id=org, artifact_id=row.artifact_id
        ) is not None
        pending = pool.submit(promote_in_other_session)
        time.sleep(0.5)
        repository.mark_available(organization_id=org, artifact_id=row.artifact_id)
        repository.commit()
        result = pending.result(timeout=30)

    assert result.artifact_id == row.artifact_id and result.state == "available"
    assert [r["state"] for r in _rows(factory, org)] == ["available"]
    assert [e["action"] for e in _audit(factory, org)] == []


def test_csv_with_a_secret_leaves_no_object_and_no_row(factory, store, s3) -> None:
    org = str(uuid.uuid4())
    secret_csv = b"id,note\n1,password=hunter2hunter2\n"
    with pytest.raises(ArtifactUploadError) as rejected:
        _upload(factory, store, org, secret_csv)
    assert rejected.value.code == "artifact_rejected"
    assert rejected.value.reason_code == "credential_detected"
    assert _objects(s3) == []
    assert _rows(factory, org) == []
    events = _audit(factory, org)
    assert [(e["action"], e["outcome"]) for e in events] == [
        ("evaluation_artifact.upload_rejected", "rejected")
    ]
    details = json.loads(events[0]["details_json"])
    assert details["reasonCode"] == "credential_detected"
    assert "sha256" not in details


def test_013n_guards_reject_unsafe_rows(factory) -> None:
    org = str(uuid.uuid4())
    digest = hashlib.sha256(b"x").hexdigest()
    base = (
        "INSERT INTO governance_evaluation_artifacts (id, org_id, sha256, media_type, "
        "size_bytes, storage_key, state, scan_policy, created_at, available_at, "
        "rejected_at, rejection_reason) VALUES (:id, :org, :sha, :media, 1, :key, :state, "
        ":policy, fairmind_canonical_clock_utc_013f(), :available_at, :rejected_at, :reason)"
    )
    good = {
        "org": org, "sha": digest, "media": "text/csv", "key": f"sha256/{digest}",
        "state": "quarantined", "policy": "fairmind-input-scan-v1",
        "available_at": None, "rejected_at": None, "reason": None,
    }
    # available_at from the canonical clock satisfies the 013m state CHECK, so
    # only the 013n BEFORE INSERT trigger can refuse this row.
    available = base.replace(":available_at", "fairmind_canonical_clock_utc_013f()")
    with factory() as session, pytest.raises(
        DBAPIError, match="artifact must be inserted quarantined"
    ):
        session.execute(text(available), {**good, "state": "available", "id": str(uuid.uuid4())})
    for bad in (
        {"key": "sha256/other"},
        {"policy": "none"},
        {"media": "application/octet-stream"},
    ):
        with factory() as session, pytest.raises(DBAPIError):
            session.execute(text(base), {**good, **bad, "id": str(uuid.uuid4())})
    artifact_id = str(uuid.uuid4())
    with factory() as session:
        session.execute(text(base), {**good, "id": artifact_id})
        session.commit()
    for statement, message in (
        (
            "UPDATE governance_evaluation_artifacts SET state='rejected', "
            "rejected_at=fairmind_canonical_clock_utc_013f(), rejection_reason='free text' "
            "WHERE id=:id",
            None,
        ),
        # BEFORE triggers run ahead of CHECK constraints, so the message names the trigger.
        (
            "UPDATE governance_evaluation_artifacts SET scan_policy='other' WHERE id=:id",
            "artifact scan policy is immutable",
        ),
        ("DELETE FROM governance_evaluation_artifacts WHERE id=:id", None),
    ):
        with factory() as session, pytest.raises(DBAPIError, match=message):
            session.execute(text(statement), {"id": artifact_id})


# --- HTTP route --------------------------------------------------------------

app = FastAPI()
app.include_router(evaluation_artifacts_router, prefix="/api/v1/ai-governance")


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=f"{user_id}@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


@pytest.fixture
def route(factory, store, monkeypatch: pytest.MonkeyPatch):
    org, foreign_org = str(uuid.uuid4()), str(uuid.uuid4())
    uploader, viewer, foreign_uploader = (str(uuid.uuid4()) for _ in range(3))
    with factory() as session:
        for user_id in (uploader, viewer, foreign_uploader):
            session.execute(
                User.__table__.insert().values(
                    id=uuid.UUID(user_id), password_hash="",
                    email=f"{user_id}@example.test", username=user_id,
                )
            )
        for org_id in (org, foreign_org):
            session.execute(
                Organization.__table__.insert().values(
                    id=uuid.UUID(org_id), name=org_id, slug=org_id, owner_id=uploader,
                )
            )
        for org_id, role, permissions in (
            (org, "uploader", [PERMISSION]),
            (org, "viewer", []),
            (foreign_org, "uploader", [PERMISSION]),
        ):
            session.execute(
                OrganizationRole.__table__.insert().values(
                    id=uuid.uuid4(), org_id=uuid.UUID(org_id), name=role, permissions=permissions,
                )
            )
        for org_id, user_id, role in (
            (org, uploader, "uploader"),
            (org, viewer, "viewer"),
            (foreign_org, foreign_uploader, "uploader"),
        ):
            session.execute(
                OrganizationMember.__table__.insert().values(
                    id=uuid.uuid4(), org_id=uuid.UUID(org_id), user_id=user_id,
                    role=role, status="active",
                )
            )
        session.commit()

    active = {"token": _token(uploader)}

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    def override_builder():
        db = factory()
        try:
            yield lambda: _service(db, store)
        finally:
            db.close()

    async def override_user() -> TokenData:
        return active["token"]

    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_artifact_upload_enabled", True)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    app.dependency_overrides[get_evaluation_artifact_service_builder] = override_builder
    try:
        with TestClient(app) as client:
            yield client, active, {
                "org": org, "foreign_org": foreign_org, "uploader": uploader,
                "viewer": viewer, "foreign_uploader": foreign_uploader,
            }
    finally:
        app.dependency_overrides.clear()


def _url(org_id: str) -> str:
    return f"/api/v1/ai-governance/organizations/{org_id}/evaluation-v2/artifacts"


def _post(client, org_id: str, data: bytes = CLEAN_CSV, media_type: str = "text/csv"):
    return client.post(_url(org_id), content=data, headers={"Content-Type": media_type})


def test_route_is_hidden_until_both_flags_are_on(route, monkeypatch) -> None:
    client, _active, ids = route
    monkeypatch.setattr(settings, "assurance_v2_artifact_upload_enabled", False)
    assert _post(client, ids["org"]).status_code == 404
    monkeypatch.setattr(settings, "assurance_v2_artifact_upload_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_enabled", False)
    response = _post(client, ids["org"])
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "assurance_feature_disabled"


def test_route_uploads_idempotently_and_refuses_without_permission_or_tenant(
    route, factory, s3
) -> None:
    client, active, ids = route
    created = _post(client, ids["org"])
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["state"] == "available"
    assert body["sha256"] == hashlib.sha256(CLEAN_CSV).hexdigest()
    replay = _post(client, ids["org"])
    assert replay.status_code == 200 and replay.json() == body

    assert _post(client, ids["org"], media_type="application/octet-stream").status_code == 415
    rejected = _post(client, ids["org"], data=b"-----BEGIN RSA PRIVATE KEY-----\n")
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["reasonCode"] == "private_key_detected"

    active["token"] = _token(ids["viewer"])
    forbidden = _post(client, ids["org"], data=b"id\n2\n")
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "evaluation_artifact_upload_forbidden"

    # A member of another organization cannot upload into this one.
    active["token"] = _token(ids["foreign_uploader"])
    cross = _post(client, ids["org"], data=b"id\n3\n")
    assert cross.status_code == 403
    assert len(_rows(factory, ids["org"])) == 1

    # The same bytes in the other tenant get that tenant's own row.
    foreign = _post(client, ids["foreign_org"])
    assert foreign.status_code == 201
    assert foreign.json()["artifactId"] != body["artifactId"]
    assert len(_objects(s3)) == 1


def test_route_fails_closed_when_the_store_is_not_configured(route, monkeypatch) -> None:
    client, _active, ids = route
    del app.dependency_overrides[get_evaluation_artifact_service_builder]
    monkeypatch.setattr(settings, "evaluation_artifact_s3_bucket", None)
    response = _post(client, ids["org"])
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "artifact_store_unavailable"


def test_route_refuses_oversized_and_empty_bodies(route, factory, s3, monkeypatch) -> None:
    client, _active, ids = route
    monkeypatch.setattr(settings, "evaluation_artifact_max_bytes", 16)
    too_large = b"id\n" + b"1\n" * 7  # 17 bytes
    declared = _post(client, ids["org"], data=too_large)
    assert declared.status_code == 413
    assert declared.json()["detail"]["code"] == "artifact_too_large"
    # No Content-Length: the streaming cap must stop the read.
    streamed = client.post(
        _url(ids["org"]), content=iter([too_large[:8], too_large[8:]]),
        headers={"Content-Type": "text/csv"},
    )
    assert streamed.status_code == 413
    empty = _post(client, ids["org"], data=b"")
    assert empty.status_code == 400
    assert empty.json()["detail"]["code"] == "artifact_empty"
    assert _rows(factory, ids["org"]) == [] and _objects(s3) == []
    assert _post(client, ids["org"], data=too_large[:16]).status_code == 201


def test_service_refuses_oversized_input_before_any_write(factory, store, s3) -> None:
    org = str(uuid.uuid4())
    with factory() as session, pytest.raises(ArtifactUploadError) as too_large:
        EvaluationArtifactService(
            SqlAlchemyEvaluationArtifactRepository(session), store, max_bytes=4
        ).upload(
            organization_id=org, actor_id=str(uuid.uuid4()), media_type="text/csv",
            data=b"id\n12\n",
        )
    assert too_large.value.code == "artifact_too_large"
    assert _rows(factory, org) == [] and _objects(s3) == []

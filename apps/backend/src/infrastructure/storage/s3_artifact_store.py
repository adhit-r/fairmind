"""Write-once S3 adapter for the content-addressed evaluation artifact store.

Only PutObject (conditional, with a SHA-256 checksum) and GetObject are used,
so the dedicated IAM user needs s3:PutObject and s3:GetObject on the prefix and
nothing else. There is no delete and no list.

Without s3:ListBucket, S3 answers GetObject on an absent key with 403
AccessDenied rather than 404, so a missing object surfaces here as
store_unavailable. The service treats both the same way: the row stays
quarantined and a replay re-writes the object before promoting.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, FlexibleChecksumError

from src.application.ports.evaluation_artifacts import (
    ArtifactStoreError,
    artifact_storage_key,
)


# Only 412 means the key exists. 409 ConditionalRequestConflict means another
# operation on the key is in flight; the object may never exist, so it is an
# unavailable store and the caller retries.
_ALREADY_EXISTS = frozenset({"PreconditionFailed"})
_MISSING = frozenset({"NoSuchKey", "404", "NotFound"})


class S3ArtifactStore:
    def __init__(self, client, *, bucket: str, prefix: str, max_bytes: int) -> None:
        if not bucket or bucket != bucket.strip():
            raise ArtifactStoreError("store_not_configured")
        if (
            not prefix
            or not prefix.endswith("/")
            or prefix.startswith("/")
            or ".." in prefix
            or "//" in prefix
        ):
            raise ArtifactStoreError("store_not_configured")
        self._client = client
        self._bucket = bucket
        self._prefix = prefix
        self._max_bytes = max_bytes

    def _key(self, digest: str) -> str:
        return self._prefix + artifact_storage_key(digest)

    def put_if_absent(self, digest: str, data: bytes, content_type: str) -> bool:
        raw = hashlib.sha256(data).digest()
        if not hmac.compare_digest(raw.hex(), digest):
            raise ArtifactStoreError("stored_digest_mismatch")
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=self._key(digest),
                Body=data,
                ContentType=content_type,
                ChecksumSHA256=base64.b64encode(raw).decode("ascii"),
                IfNoneMatch="*",
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in _ALREADY_EXISTS:
                return False
            raise ArtifactStoreError("store_unavailable") from None
        except BotoCoreError:
            raise ArtifactStoreError("store_unavailable") from None
        return True

    def get_verified(self, digest: str) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket, Key=self._key(digest), ChecksumMode="ENABLED"
            )
            data = response["Body"].read(self._max_bytes + 1)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in _MISSING:
                raise ArtifactStoreError("stored_object_missing") from None
            raise ArtifactStoreError("store_unavailable") from None
        except FlexibleChecksumError:
            # botocore's own validation of the stored ChecksumSHA256 failed.
            raise ArtifactStoreError("stored_digest_mismatch") from None
        except BotoCoreError:
            raise ArtifactStoreError("store_unavailable") from None
        if len(data) > self._max_bytes:
            raise ArtifactStoreError("stored_size_mismatch")
        if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), digest):
            raise ArtifactStoreError("stored_digest_mismatch")
        return data


def build_s3_artifact_store(settings) -> S3ArtifactStore:
    """Build from the dedicated artifact settings; fail closed when any is unset."""

    secret = settings.evaluation_artifact_aws_secret_access_key
    secret_value = secret.get_secret_value() if secret is not None else ""
    if not (
        settings.evaluation_artifact_s3_bucket
        and settings.evaluation_artifact_s3_prefix
        and settings.evaluation_artifact_s3_region
        and settings.evaluation_artifact_aws_access_key_id
        and secret_value
    ):
        raise ArtifactStoreError("store_not_configured")
    client = boto3.client(
        "s3",
        region_name=settings.evaluation_artifact_s3_region,
        aws_access_key_id=settings.evaluation_artifact_aws_access_key_id,
        aws_secret_access_key=secret_value,
        endpoint_url=settings.evaluation_artifact_s3_endpoint_url or None,
        config=Config(
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )
    return S3ArtifactStore(
        client,
        bucket=settings.evaluation_artifact_s3_bucket,
        prefix=settings.evaluation_artifact_s3_prefix,
        max_bytes=settings.evaluation_artifact_max_bytes,
    )


__all__ = ["S3ArtifactStore", "build_s3_artifact_store"]

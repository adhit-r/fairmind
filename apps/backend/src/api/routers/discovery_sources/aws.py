"""AWS: Bedrock models in use, custom and imported models, provisioned throughput, Bedrock
agents, AgentCore runtimes, and SageMaker endpoints and model registries, per region.

config: access_key_id, regions (comma separated, default us-east-1), role_arn and external_id
(optional, to assume a read-only role). token: the secret access key.
Read-only IAM: bedrock:List*, bedrock-agentcore:ListAgentRuntimes, cloudwatch:ListMetrics,
sagemaker:ListEndpoints, sagemaker:ListModelPackageGroups, sts:AssumeRole if role_arn is set.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException

from . import asset, need, need_token

logger = logging.getLogger(__name__)
MAX_PER_CALL = 200


def _iso(v: Any) -> Optional[str]:
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def _session(config: Dict[str, Any], secret: str):
    import boto3  # deferred: only this connector needs it

    key_id = need(config, "access_key_id", "AWS access key ID")
    session = boto3.Session(aws_access_key_id=key_id, aws_secret_access_key=secret)
    role = str(config.get("role_arn") or "").strip()
    if not role:
        return session
    kwargs: Dict[str, Any] = {"RoleArn": role, "RoleSessionName": "fairmind-discovery"}
    if config.get("external_id"):
        kwargs["ExternalId"] = str(config["external_id"])
    c = session.client("sts").assume_role(**kwargs)["Credentials"]
    return boto3.Session(aws_access_key_id=c["AccessKeyId"], aws_secret_access_key=c["SecretAccessKey"], aws_session_token=c["SessionToken"])


def _pages(client: Any, op: str, key: str, **kwargs: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if client.can_paginate(op):
        for page in client.get_paginator(op).paginate(**kwargs):
            out.extend(page.get(key, []))
            if len(out) >= MAX_PER_CALL:
                break
    else:
        out = getattr(client, op)(**kwargs).get(key, [])
    return out[:MAX_PER_CALL]


def _scan(config: Dict[str, Any], secret: str) -> List[Dict[str, Any]]:
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

    try:
        session = _session(config, secret)
    except ClientError as exc:
        raise HTTPException(status_code=401, detail=f"AWS rejected the credentials ({exc.response['Error'].get('Code')})") from None
    regions = [r.strip() for r in str(config.get("regions") or "us-east-1").split(",") if r.strip()]
    found: List[Dict[str, Any]] = []
    denied: List[str] = []
    readable = 0

    def read(region: str, service: str, label: str, fn: Callable[[Any], None]) -> None:
        nonlocal readable
        try:
            fn(session.client(service, region_name=region))
            readable += 1
        except ClientError as exc:
            code = exc.response["Error"].get("Code", "")
            if code in ("UnrecognizedClientException", "InvalidClientTokenId", "SignatureDoesNotMatch", "ExpiredTokenException"):
                raise HTTPException(status_code=401, detail=f"AWS rejected the credentials ({code})") from None
            denied.append(f"{label} in {region} ({code})")
        except (BotoCoreError, NoCredentialsError) as exc:  # service not offered in the region, or not in this botocore
            denied.append(f"{label} in {region} ({type(exc).__name__})")

    for region in regions:
        meta = {"cloud": "aws", "region": region, "signal": "cloud inventory"}

        def invoked_models(c: Any, region: str = region, meta: Dict[str, Any] = meta) -> None:
            # CloudWatch lists a metric when it had data in the last two weeks: the foundation models in use.
            for m in _pages(c, "list_metrics", "Metrics", Namespace="AWS/Bedrock", MetricName="Invocations"):
                model_id = next((d["Value"] for d in m.get("Dimensions", []) if d["Name"] == "ModelId"), None)
                if model_id:
                    found.append(asset(f"aws:{region}:bedrock-model:{model_id}", model_id, "llm_app",
                                       {**meta, "service": "Amazon Bedrock", "model_id": model_id, "usage": "invoked in the last 14 days"}))

        def custom_models(c: Any, region: str = region, meta: Dict[str, Any] = meta) -> None:
            for m in _pages(c, "list_custom_models", "modelSummaries"):
                found.append(asset(m["modelArn"], m.get("modelName"), "llm_app",
                                   {**meta, "service": "Amazon Bedrock", "type": "custom model", "base_model": m.get("baseModelName") or m.get("baseModelArn"),
                                    "customization": m.get("customizationType"), "created_at": _iso(m.get("creationTime"))}))
            for m in _pages(c, "list_imported_models", "modelSummaries"):
                found.append(asset(m["modelArn"], m.get("modelName"), "llm_app",
                                   {**meta, "service": "Amazon Bedrock", "type": "imported model", "created_at": _iso(m.get("creationTime"))}))
            for p in _pages(c, "list_provisioned_model_throughputs", "provisionedModelSummaries"):
                found.append(asset(p["provisionedModelArn"], p.get("provisionedModelName"), "llm_app",
                                   {**meta, "service": "Amazon Bedrock", "type": "provisioned throughput", "model": p.get("foundationModelArn") or p.get("modelArn"),
                                    "status": p.get("status"), "created_at": _iso(p.get("creationTime"))}))

        def agents(c: Any, region: str = region, meta: Dict[str, Any] = meta) -> None:
            for a in _pages(c, "list_agents", "agentSummaries"):
                found.append(asset(f"aws:{region}:bedrock-agent:{a['agentId']}", a.get("agentName"), "agent",
                                   {**meta, "service": "Bedrock Agents", "description": a.get("description") or "", "status": a.get("agentStatus"),
                                    "updated_at": _iso(a.get("updatedAt"))}))

        def runtimes(c: Any, region: str = region, meta: Dict[str, Any] = meta) -> None:
            for r in _pages(c, "list_agent_runtimes", "agentRuntimes"):
                found.append(asset(r.get("agentRuntimeArn") or r["agentRuntimeId"], r.get("agentRuntimeName"), "agent",
                                   {**meta, "service": "Bedrock AgentCore", "status": r.get("status"), "updated_at": _iso(r.get("lastUpdatedAt"))}))

        def sagemaker(c: Any, region: str = region, meta: Dict[str, Any] = meta) -> None:
            for e in _pages(c, "list_endpoints", "Endpoints"):
                found.append(asset(e["EndpointArn"], e.get("EndpointName"), "ml_model",
                                   {**meta, "service": "SageMaker endpoint", "status": e.get("EndpointStatus"), "created_at": _iso(e.get("CreationTime"))},
                                   stage="operate" if e.get("EndpointStatus") == "InService" else "onboard"))
            for g in _pages(c, "list_model_package_groups", "ModelPackageGroupSummaryList"):
                found.append(asset(g["ModelPackageGroupArn"], g.get("ModelPackageGroupName"), "ml_model",
                                   {**meta, "service": "SageMaker model registry", "description": g.get("ModelPackageGroupDescription") or "",
                                    "created_at": _iso(g.get("CreationTime"))}))

        read(region, "cloudwatch", "Bedrock invocation metrics", invoked_models)
        read(region, "bedrock", "Bedrock models", custom_models)
        read(region, "bedrock-agent", "Bedrock agents", agents)
        read(region, "bedrock-agentcore-control", "AgentCore runtimes", runtimes)
        read(region, "sagemaker", "SageMaker", sagemaker)

    if denied:
        logger.warning("AWS discovery skipped: %s", "; ".join(denied))
    if not readable:
        raise HTTPException(status_code=403, detail="AWS allowed none of the reads: " + "; ".join(denied[:5]))
    for a in found:
        a["metadata"]["skipped_reads"] = denied[:20]
    return found


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    secret = need_token(token, "AWS secret access key")
    return await asyncio.to_thread(_scan, config, secret)

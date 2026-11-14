"""The steps each source's read is made of: what it fetches and with which call. A run records
counts and examples per step, and a person can turn a step off (config disabled_steps) on a
source that has more than one, which stops that part of the read.
"""

from __future__ import annotations

from typing import Any, Dict, List

# kind -> [(key, title, call)]
STEPS: Dict[str, List[tuple]] = {
    "github": [("repos", "Repos with AI", "GET /orgs/{owner}/repos + manifests"), ("mcp", "MCP server configs", ".mcp.json, .cursor/mcp.json, .vscode/mcp.json")],
    "mlflow": [("models", "Registered models", "GET /api/2.0/mlflow/registered-models/search")],
    "huggingface": [("models", "Models", "GET /api/models?author={owner}")],
    "anthropic": [("keys", "API keys and usage", "GET /v1/organizations/api_keys + usage_report/messages"), ("claude_code", "Claude Code, 7 days", "GET /v1/organizations/usage_report/claude_code")],
    "claude_enterprise": [("orgs", "Organisations and people", "GET /v1/compliance/organizations/{id}/users"), ("projects", "Shared projects", "GET /v1/compliance/apps/projects")],
    "openai": [("keys", "Project API keys and usage", "GET /organization/projects/{id}/api_keys + usage/completions")],
    "aws": [
        ("bedrock", "Bedrock models", "cloudwatch:ListMetrics, bedrock:ListCustomModels"),
        ("agents", "Agents", "bedrock-agent:ListAgents, bedrock-agentcore:ListAgentRuntimes"),
        ("sagemaker", "SageMaker", "sagemaker:ListEndpoints, ListModelPackageGroups"),
    ],
    "azure": [("deployments", "Model deployments", "Microsoft.CognitiveServices/accounts/deployments"), ("workspaces", "ML workspaces", "Microsoft.MachineLearningServices/workspaces")],
    "gcp": [("endpoints", "Endpoints", "aiplatform endpoints.list"), ("models", "Model registry", "aiplatform models.list"), ("agents", "Agent Engine", "aiplatform reasoningEngines.list")],
    "okta": [("sso", "AI apps in single sign-on", "GET /api/v1/apps + /api/v1/logs")],
    "entra": [("apps", "AI enterprise apps and consents", "GET /servicePrincipals + /oauth2PermissionGrants")],
    "m365_copilot": [("usage", "Licences and usage", "GET /subscribedSkus + copilot/reports"), ("agents", "Copilot agents", "GET /copilot/admin/catalog/packages")],
    "litellm": [("keys", "Virtual keys", "GET /key/list + /v1/models")],
    "proxy_logs": [("traffic", "AI traffic in the log", "Uploaded export")],
    "mcp_registry": [("servers", "Approved MCP servers", "GET /v0.1/servers")],
}

SAMPLES = 3


def step_of(kind: str, item: Dict[str, Any]) -> str:
    """Which step produced a discovered item."""
    meta = item.get("metadata") or {}
    service = str(meta.get("service") or "")
    if kind == "github":
        return "mcp" if item["kind"] == "mcp_server" else "repos"
    if kind == "anthropic":
        return "claude_code" if item["external_id"] == "anthropic:claude-code" else "keys"
    if kind == "claude_enterprise":
        return "projects" if item["external_id"].startswith("claude-project:") else "orgs"
    if kind == "aws":
        return "sagemaker" if service.startswith("SageMaker") else "agents" if item["kind"] == "agent" else "bedrock"
    if kind == "azure":
        return "deployments" if item["kind"] == "llm_app" else "workspaces"
    if kind == "gcp":
        return "agents" if item["kind"] == "agent" else "endpoints" if service == "Vertex AI endpoint" else "models"
    if kind == "m365_copilot":
        return "agents" if item["kind"] == "agent" else "usage"
    return STEPS.get(kind, [("items", "", "")])[0][0]


def disabled(config: Dict[str, Any], key: str) -> bool:
    return key in (config.get("disabled_steps") or [])


def summarise(kind: str, found: List[Dict[str, Any]], new_ids: set, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Per step: how many items, how many new, and a few examples (new ones first)."""
    out = []
    for key, title, call in STEPS.get(kind, []):
        items = [i for i in found if step_of(kind, i) == key]
        items.sort(key=lambda i: i["external_id"] not in new_ids)
        out.append(
            {
                "key": key,
                "found": len(items),
                "created": sum(1 for i in items if i["external_id"] in new_ids),
                "off": disabled(config, key),
                "samples": [{"id": i["external_id"], "name": i["name"], "new": i["external_id"] in new_ids} for i in items[:SAMPLES]],
            }
        )
    return out


def definitions(kind: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = STEPS.get(kind, [])
    return [{"key": k, "title": t, "call": c, "on": not disabled(config, k), "toggleable": len(steps) > 1} for k, t, c in steps]

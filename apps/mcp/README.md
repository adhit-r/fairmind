# fairmind-mcp

<!-- mcp-name: io.github.adhit-r/fairmind -->

An MCP server that lets a coding agent ask FairMind whether an AI system may ship, and run fairness tests on CSVs from your machine, record findings and remediation tasks, and build inspection packs. It is a thin layer over the [`fairmind` Python SDK](../sdk/README.md) and talks to the server over stdio.

## Tools

| Tool | What it does |
| --- | --- |
| `list_systems` | AI systems your key can see, with id, risk tier and lifecycle stage |
| `get_system` | One AI system: name, owner, risk tier, lifecycle stage and metadata |
| `register_system` | Registers an AI system (optionally in a given workspace) with the risk tier the user states |
| `release_gate` | Verdict (`go`, `conditional_go`, `no_go`), confidence, the five checks and the reasons |
| `clause_map` | The gate read per regulatory clause; optional `frameworks` such as `EUAIA`, `ISO42001` |
| `run_fairness_test` | Uploads a local CSV, stores the measured result as evidence, returns metrics and the new gate |
| `record_monitoring_snapshot` | Compares recent decisions in a local CSV with the latest fairness run (drift, impact ratio, PSI) |
| `attest_check` | Records a person's statement that `data_governance`, `human_oversight`, `monitoring` or `environmental` is satisfied |
| `list_evaluations` | Searches the evaluation catalogue (drift, leakage, prompt injection, jailbreaks, counterfactual flip rate, agent configuration and more) and says which FairMind can run |
| `describe_evaluation` | The files and params an evaluation takes, and whether it also runs as a behaviour test against the live system |
| `run_evaluation` | Runs an evaluation on local files, against the live system (`live`) or on the connected agent platform (`use_connection`); stores the result as measured evidence |
| `create_evidence_pack` | Builds a hashed inspection pack of chosen systems' evidence and clause maps; `share` also mints a read-only auditor token |
| `verify_evidence_pack` | Recomputes a pack's manifest hash and each system's evidence chain head, from a local `pack.json`, an auditor link or a pack id |
| `record_finding` | Records a risk finding (type, severity, description) against a system |
| `list_findings` | Recorded findings with counts by severity, and a system's remediation tasks |
| `create_remediation_task` | Opens a remediation task for a system, optionally tied to a finding |
| `update_remediation_task` | Moves a remediation task to a new status and/or adds notes |
| `request_release_approval` | Asks for a release decision, or reads where the latest request stands; a person approves or rejects it in FairMind, not this server |
| `generate_report` | Generates and stores a compliance, bias or governance report snapshot for a system and lists earlier ones |

Each tool returns a compact text summary and the full API response as structured content. `run_evaluation` waits for behaviour tests, which run as background jobs and can take minutes. The evaluation tools act in the key's first organisation; set `FAIRMIND_ORG_ID` to pick another. API failures come back as tool errors carrying the HTTP status and the server's message. `attest_check` writes manual evidence, and `record_finding` writes a finding, so the tools tell the agent to use only statements and observations that are real.

## Install

```bash
pip install fairmind-mcp        # or run it without installing: uvx fairmind-mcp
```

It is listed in the official MCP Registry as `io.github.adhit-r/fairmind`. To work on it from a checkout, run `uv sync` in `apps/mcp` (the SDK is resolved from `../sdk`).

The server targets the `mcp` 1.x `FastMCP` API (`mcp>=1.10,<2`); in `mcp` 2.x it was renamed `MCPServer`.

## Configure

Create a key once with `POST /api/v1/auth/api-keys`, export it, and let the client pass it through. The config below never contains the key itself.

```bash
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...
```

### Claude Code

```bash
claude mcp add fairmind -- uvx fairmind-mcp
```

The server inherits `FAIRMIND_API_URL` and `FAIRMIND_API_KEY` from the shell that starts Claude Code. To scope it to a repository, commit a `.mcp.json` that expands the variables from each developer's environment:

```json
{
  "mcpServers": {
    "fairmind": {
      "command": "uvx",
      "args": ["fairmind-mcp"],
      "env": {
        "FAIRMIND_API_URL": "${FAIRMIND_API_URL}",
        "FAIRMIND_API_KEY": "${FAIRMIND_API_KEY}"
      }
    }
  }
}
```

### Claude Desktop

Desktop does not expand variables, so launch through a shell that reads them from your environment. In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fairmind": {
      "command": "/bin/sh",
      "args": ["-c", "exec uvx fairmind-mcp"]
    }
  }
}
```

Set `FAIRMIND_API_URL` and `FAIRMIND_API_KEY` in the environment that starts Claude Desktop (for example with `launchctl setenv` on macOS), or keep them in a file outside the repository that you source in the `-c` command.

## Try it

Ask the agent: "May the credit-scoring system ship?" It calls `list_systems`, then `release_gate`. Ask it to "run a fairness test on `holdout.csv` for gender and region, outcome `repaid`, prediction `approved`" and it calls `run_fairness_test` with the file path on your machine.

## Tests

```bash
cd apps/mcp && uv run --with pytest pytest -q -p no:cacheprovider tests
```

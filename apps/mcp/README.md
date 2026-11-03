# fairmind-mcp

An MCP server that lets a coding agent ask FairMind whether an AI system may ship, and run fairness tests on CSVs from your machine. It is a thin layer over the [`fairmind` Python SDK](../sdk/README.md) and talks to the server over stdio.

## Tools

| Tool | What it does |
| --- | --- |
| `list_systems` | AI systems your key can see, with id, risk tier and lifecycle stage |
| `release_gate` | Verdict (`go`, `conditional_go`, `no_go`), confidence, the five checks and the reasons |
| `clause_map` | The gate read per regulatory clause; optional `frameworks` such as `EUAIA`, `ISO42001` |
| `run_fairness_test` | Uploads a local CSV, stores the measured result as evidence, returns metrics and the new gate |
| `record_monitoring_snapshot` | Compares recent decisions in a local CSV with the latest fairness run (drift, impact ratio, PSI) |
| `attest_check` | Records a person's statement that `data_governance`, `human_oversight`, `monitoring` or `environmental` is satisfied |

Each tool returns a compact text summary and the full API response as structured content. API failures come back as tool errors carrying the HTTP status and the server's message. `attest_check` writes manual evidence, so the tool tells the agent to use only statements the user gave or confirmed.

## Install

```bash
# from a checkout, with uv (the SDK is resolved from ../sdk)
cd apps/mcp && uv sync

# or with pip: SDK first, then this package
pip install -e apps/sdk -e apps/mcp
```

The server targets the `mcp` 1.x `FastMCP` API (`mcp>=1.10,<2`); in `mcp` 2.x it was renamed `MCPServer`.

## Configure

Create a key once with `POST /api/v1/auth/api-keys`, export it, and let the client pass it through. The config below never contains the key itself.

```bash
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...
```

### Claude Code

```bash
claude mcp add fairmind -- uv run --project /path/to/fairmind/apps/mcp fairmind-mcp
```

The server inherits `FAIRMIND_API_URL` and `FAIRMIND_API_KEY` from the shell that starts Claude Code. To scope it to a repository, commit a `.mcp.json` that expands the variables from each developer's environment:

```json
{
  "mcpServers": {
    "fairmind": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/fairmind/apps/mcp", "fairmind-mcp"],
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
      "args": ["-c", "exec uv run --project /path/to/fairmind/apps/mcp fairmind-mcp"]
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

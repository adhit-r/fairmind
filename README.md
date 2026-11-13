<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind: open-source agentic AI governance platform" width="800">
</div>

<br>

<div align="center">

# FairMind

**Open-source agentic AI governance. Agents do the governance work; a person decides at every gate.**

[![License: AGPL-3.0 / Apache-2.0](https://img.shields.io/badge/license-AGPL--3.0%20%2F%20Apache--2.0-blue.svg)](LICENSING.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23982915.svg)](https://doi.org/10.5281/zenodo.23982915)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/16369/badge)](https://www.bestpractices.dev/projects/16369)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/adhit-r/fairmind/badge)](https://scorecard.dev/viewer/?uri=github.com/adhit-r/fairmind)
[![PyPI](https://img.shields.io/pypi/v/fairmind-mcp?label=PyPI)](https://pypi.org/project/fairmind-mcp/)
[![Software Heritage](https://archive.softwareheritage.org/badge/origin/https://github.com/adhit-r/fairmind/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/adhit-r/fairmind)
[![OECD.AI Catalogue](https://img.shields.io/badge/OECD.AI-Catalogue%20of%20Tools%20%26%20Metrics-1f4e79)](https://oecd.ai/en/catalogue/tools/adhit-rfairmind)
[![Mentioned in Awesome AI Regulation, Principles & Guidelines](https://awesome.re/mentioned-badge.svg)](https://github.com/EthicalML/awesome-artificial-intelligence-regulation#interactive-and-practical-tools)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange)](#current-status)
[![Good first issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

[Website](https://fairmind.xyz) | [Docs](https://docs.fairmind.xyz) | [Status](#current-status) | [Quickstart](#quickstart) | [Contributing](CONTRIBUTING.md) | [Discussions](https://github.com/adhit-r/fairmind/discussions)

</div>

---

## What FairMind does

FairMind governs AI systems, including LLM applications and AI agents, by running governance as **workflows**. Each workflow is a chain of steps: collect, check, suggest, ask a person, act, verify, file evidence. An agent drafts the work steps, FairMind runs the evaluations, and a person approves or rejects at each gate. Every step lands on a hash-chained ledger, so the record of who decided what, and on which evidence, can be checked later.

One workflow run counts toward every framework it maps to. Run an AI risk assessment once and it is evidence for ISO/IEC 42001, NIST AI RMF, the EU AI Act and the other frameworks whose requirements it meets.

| | |
|---|---|
| **90** agentic workflows | in **21 packs** across four pillars: Govern, Evaluate, Secure, Comply |
| **109** evaluations | **61** produce a result inside FairMind today |
| **51** frameworks | **539** requirements, linked through **29** common controls and **922** crosswalk entries |

FairMind helps a team get ready for review and shows an auditor the evidence. It does not certify compliance, and it never approves a release on its own.

---

## Current status

**Alpha, November 2026.** The main path works end to end: discover systems, run workflows and evaluations, gate a release, hand an auditor a verifiable pack. 86 of the 90 catalogue workflows are still marked *proposed* until organisations run them in practice.

### Works today

| Area | What you can do |
|---|---|
| **AI systems** | Register a system, or discover it from MLflow, GitHub or the Hugging Face Hub and promote it from a review queue. Each system has one page that walks it through Onboard, Assess, Govern, Remediate and Operate. |
| **Packs and workflows** | Install packs, start workflow runs, record step outputs, decide at gates. Draft and publish your own version of any workflow. |
| **Evaluations** | Run all 109 evaluations: on uploaded files, against your live AI system, on your agent platform's configuration, or on results from your own sandbox, drills and detectors. Results are stored as measured evidence. |
| **Release gate** | Five checks (fairness, data governance, human oversight, monitoring, environmental) give `go`, `conditional_go` or `no_go`. Failing blocking policy rules force `no_go`. Approval is refused while critical findings are open. |
| **Policies** | Write rules mapped to framework controls. Results are evaluated live and count as evidence for those controls. |
| **Evidence for auditors** | Read the gate per framework clause, export inspection packs, share a read-only auditor link, and verify a pack offline with `fairmind verify`. |
| **CI and agents** | CLI, GitHub Action, Python SDK and MCP server read the gate and push test results with an API key. |

### Partly done

| Area | Where it stands |
|---|---|
| **Agent steps** | The agent drafts a work step when someone presses *Let the agent do this step* or *Run to the next decision*. It uses your own model (19 providers, key encrypted at rest) or, without one, built-in rules that list what is on file and what is missing. It writes text to the ledger; it does not change anything outside FairMind. |
| **Agent, attack and detector evaluations** | 21 evaluations judge a results file from your own sandbox, drill, attack run or detector. FairMind computes the metric from the raw rows but does not run the scenario or attack itself until sandboxed workers exist. |
| **Monitoring** | You push snapshots on your schedule (for example `fairmind monitor` in a cron job). FairMind tracks cadence, flags stale snapshots and opens a finding on sustained drift. It does not pull data itself. |
| **Older pages** | Bias detection, LLM judge, multimodal bias and similar pages from earlier versions remain outside the main navigation. They are not validated. |

### Not built yet

- **Automatic workflow starts.** The catalogue lists schedules and triggers, but a person starts every run.
- **Sandboxed evaluation workers.** Engines run inside the backend process. Uploaded model files are inspected, never loaded or executed.
- **Signed-evidence control plane (Assurance V2).** Signed evidence, issuer keys, trust policies and four-eyes review are built and tested but **off by default**. See [docs/STATUS.md](docs/STATUS.md).
- **Runtime guardrails.** FairMind assesses systems; it does not sit in the request path.
- **Certification.** No compliance certificate, automatic approval or "FairMind Verified" claim.

---

## How a workflow runs

| Step kind | Who does it |
|---|---|
| `trigger`, `escalate`, `file` | **FairMind**, on its own. Filing evidence seals the ledger. |
| `collect`, `check`, `suggest`, `act`, `preflight`, `verify` | **A person** records the output, or **the agent** drafts it on request. |
| `ask`, `exception`, `decide` | **A person** approves, requests changes or rejects. The run follows the branch that matches. |

- Requested changes go through a revise step; the fourth round escalates.
- When someone decides on their own proposal, the run warns and the ledger records `selfReview: true`.
- Every run reports `chainValid`, so tampering with the ledger shows.

---

## The four pillars

| Pillar | Packs |
|---|---|
| **Govern** | AI governance foundation; Inventory and lifecycle; Risk and impact; Data and privacy; Third parties, IP and liability |
| **Evaluate** | Quality evaluation; Fairness and bias; Explainability and oversight; Production monitoring; Use-case evaluation suites |
| **Secure** | Secure LLM applications; Secure agentic AI; AI supply chain; Adversarial ML and red teaming; Offensive AI and deepfake defence; Content safety; Incident response; FairMind agent self-assurance |
| **Comply** | Regulatory obligations; Audit and certification readiness; Rights of affected people |

---

## Evaluations

Each evaluation has a metric and a pass rule from the catalogue. A run returns `passed`, `failed` or `insufficient` (the inputs cannot support a verdict), the metrics behind it and the detail per row or probe.

**On uploaded files.** Data drift, data poisoning, train-test leakage, personal data, RAG knowledge-base poisoning, label quality, task accuracy, calibration, out-of-distribution detection, multilingual parity, counterfactual flip rate, membership inference, verbatim reproduction, secrets in prompts and config, tool poisoning, model file and dependency scanning, runaway agent loops, cost against budget and more. No file engine makes a network call.

**Against your live AI system.** Connect an OpenAI-compatible endpoint or any HTTP endpoint. FairMind sends probes and judges the answers with your own model: prompt injection, jailbreaks, system prompt leakage, harmful content, PII leakage, RAG faithfulness, robustness to typos and distractors, and uneven treatment between groups. Probes come from your CSV, or your model writes them from the system's intended use. Behaviour tests run as background jobs.

**On your agent platform's configuration.** Connect Claude Managed Agents read-only, or upload an exported config or an MCP config. FairMind checks for high-risk tools that do not ask first, unrestricted network egress, poisoned agent memory, shadow MCP servers, MCP servers without credentials, and secrets in agent fields. A section the export leaves out counts as *not read*, so a check never passes on missing data.

**From stored runs.** Fairness runs (disparate impact, demographic parity, equal opportunity, equalized odds, calibration, each with a bootstrap interval and a permutation p-value), monitoring snapshots and environmental assessments feed five more evaluations.

---

## Frameworks

51 frameworks are in the catalogue. Among them:

- **AI management and risk:** ISO/IEC 42001, ISO/IEC 42005, ISO/IEC 23894, NIST AI RMF, NIST AI 600-1
- **Agents and LLM security:** AIUC-1, OWASP Top 10 for LLM Applications, OWASP Top 10 for Agentic Applications, OWASP MCP Top 10, CSA AI Controls Matrix, CSA MAESTRO, MITRE ATLAS, Google SAIF
- **Law and regulation:** EU AI Act, Council of Europe AI Convention, Korea AI Basic Act, Colorado and Texas AI acts, NYC Local Law 144, California SB 53
- **Guidelines:** OECD AI Principles, G7 Hiroshima Process, Singapore's frameworks for agentic and generative AI, Japan's AI Guidelines for Business, sector guidance for finance and health

A framework mapping organises evidence. It is not legal advice or a conformity decision. The full catalogue lives in [`pack_catalogue_data/catalogue.json`](apps/backend/src/api/routers/pack_catalogue_data/catalogue.json).

---

## Release gate in CI and coding agents

Mint an API key at `POST /api/v1/auth/api-keys`.

```bash
pipx install fairmind-cli
export FAIRMIND_API_URL=https://your-fairmind-host
export FAIRMIND_API_KEY=...

fairmind gate --system <id>      # exit 0 go, 2 conditional go, 1 no go
fairmind test --system <id> --file predictions.csv --outcome repaid --prediction approved --attributes gender,region
fairmind monitor --system <id> --file recent.csv --attributes gender,region
fairmind verify pack.json        # offline, no network
```

```yaml
- uses: adhit-r/fairmind/.github/actions/fairmind-gate@main
  with:
    system: ${{ vars.FAIRMIND_SYSTEM_ID }}
    api-url: ${{ vars.FAIRMIND_API_URL }}
    api-key: ${{ secrets.FAIRMIND_API_KEY }}
```

The [Python SDK](apps/sdk/README.md) (`pip install fairmind`) wraps the same calls, and the [MCP server](apps/mcp/README.md) (`pip install fairmind-mcp`, listed in the official MCP Registry as `io.github.adhit-r/fairmind`) gives Claude Code and other MCP clients nine tools: `list_systems`, `release_gate`, `clause_map`, `run_fairness_test`, `record_monitoring_snapshot`, `attest_check`, `list_evaluations`, `describe_evaluation` and `run_evaluation`. Guides: [release gate in CI](apps/docs/content/docs/workflows/release-gate-in-ci.mdx), [SDK and MCP](apps/docs/content/docs/workflows/sdk-and-mcp.mdx), [inspection packs](apps/docs/content/docs/workflows/inspection-packs.mdx).

---

## Quickstart

You need Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 20+, npm, and an empty PostgreSQL 14+ database (local, Docker or Neon).

```bash
git clone https://github.com/adhit-r/fairmind.git
cd fairmind
```

Backend, in one terminal:

```bash
cd apps/backend
cp config/env.example .env           # set DATABASE_URL and SECRET_KEY
uv sync
uv run python scripts/setup_db.py    # schema plus reference data; safe to re-run
uv run uvicorn api.main:app --reload --port 8000
```

Frontend, in another:

```bash
cd apps/frontend
echo "BACKEND_INTERNAL_URL=http://localhost:8000" > .env.local
npm install
npm run dev
```

Open http://localhost:1111, register, and sign in. API docs are at http://localhost:8000/docs. `uv run python scripts/setup_db.py verify` checks a database without changing it.

`SECRET_KEY` also derives the key that encrypts stored model-provider and platform keys, so rotating it means entering those keys again.

---

## Repository layout

| Path | What it is |
|---|---|
| `apps/backend/` | FastAPI backend (Python, uv, PostgreSQL only) |
| `apps/frontend/` | Next.js app (TypeScript, Tailwind) |
| `apps/cli/`, `apps/sdk/`, `apps/mcp/` | `fairmind` CLI, Python SDK and MCP server |
| `apps/docs/` | Docs site at docs.fairmind.xyz |
| `apps/website/` | Marketing site (Astro) |
| `.github/actions/fairmind-gate/` | GitHub Action for the release gate |
| `docs/` | Status, architecture notes, ADRs and audits |

## Tests

```bash
cd apps/backend && FAIRMIND_TEST_POSTGRES_URL=postgresql://... uv run pytest
cd apps/frontend && npm run test
```

Backend tests need a throwaway PostgreSQL 14 server; each test gets its own temporary database. CI runs the backend suite, the frontend type-check and unit tests, and the CLI, SDK and MCP tests.

---

## Listings

FairMind is listed in the [OECD.AI Catalogue of Tools & Metrics for Trustworthy AI](https://oecd.ai/en/catalogue/tools/adhit-rfairmind) as an open-source technical toolkit for governance, compliance and risk management, covering design, validation, deployment and monitoring. The catalogue lists tools from their authors; the OECD does not vet or endorse them.

It is also listed in [Awesome AI Regulation, Principles & Guidelines](https://github.com/EthicalML/awesome-artificial-intelligence-regulation#interactive-and-practical-tools), the Institute for Ethical AI & Machine Learning's curated list of AI guidelines, principles and tools, under "Interactive and Practical Tools".

## Contributing

Contributions are welcome, from typo fixes to new evaluation engines. Start with [CONTRIBUTING.md](CONTRIBUTING.md), then pick a [good first issue](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22). Running the agent-scenario and attack evaluations in a sandboxed worker is a good place to start. Questions go to [Discussions](https://github.com/adhit-r/fairmind/discussions). Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Do not report vulnerabilities in public issues. See [SECURITY.md](SECURITY.md).

## Citing FairMind

Metadata is in [CITATION.cff](CITATION.cff). Concept DOI: [10.5281/zenodo.23982915](https://doi.org/10.5281/zenodo.23982915).

## License

Created and maintained by [Axonome](https://www.fairmind.xyz/about). The platform is under the [AGPL-3.0](LICENSE); the Python SDK, CLI and MCP server are under [Apache-2.0](apps/sdk/LICENSE). A commercial license is available. See [LICENSING.md](LICENSING.md). Releases up to `v0.3.1-alpha` were MIT.

<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind: open-source AI governance and assurance platform for models and LLM agents" width="800">
</div>

<br>

<div align="center">

# FairMind

**Open-source AI governance and assurance platform for models and LLM agents**

*Bring your tests. Produce evidence you can defend.*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23982915.svg)](https://doi.org/10.5281/zenodo.23982915)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/adhit-r/fairmind/badge)](https://scorecard.dev/viewer/?uri=github.com/adhit-r/fairmind)
[![Status](https://img.shields.io/badge/status-internal%20alpha-orange)](docs/STATUS.md)
[![Backend](https://img.shields.io/badge/backend-FastAPI-green)](apps/backend)
[![Frontend](https://img.shields.io/badge/frontend-Next.js-black)](apps/frontend)
[![Good first issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Contributors](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Website](https://fairmind.xyz) | [Docs](https://docs.fairmind.xyz) | [Status](docs/STATUS.md) | [Contributing](CONTRIBUTING.md) | [Discussions](https://github.com/adhit-r/fairmind/discussions) | [Leer en español](README.es-ES.md)

</div>

---

## Table of contents

- [What FairMind is](#what-fairmind-is)
- [Who it is for](#who-it-is-for)
- [How it works](#how-it-works)
- [Key features](#key-features)
- [Supported frameworks](#supported-frameworks)
- [Quickstart](#quickstart)
- [Release gate in CI: CLI, GitHub Action, SDK and MCP](#release-gate-in-ci-cli-github-action-sdk-and-mcp)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository layout](#repository-layout)
- [API overview](#api-overview)
- [Development and tests](#development-and-tests)
- [Deployment](#deployment)
- [Project status](#project-status)
- [Contributing](#contributing)
- [Security](#security)
- [Citing FairMind](#citing-fairmind)
- [License](#license)

---

## What FairMind is

FairMind is an open-source **AI governance, AI assurance and AI compliance platform** for machine learning models, LLM applications and agentic AI systems. A team registers an AI system, plugs in governance frameworks such as **ISO/IEC 42001, the EU AI Act, NIST AI RMF, AIUC-1, RBI FREE-AI, India's DPDP Act and the OECD AI Principles**, and then works through the controls that apply:

1. **Discover** AI systems from MLflow, GitHub and the Hugging Face Hub.
2. **Evaluate** them: fairness and bias tests, data drift, behaviour tests against the live system (prompt injection, jailbreaks, RAG faithfulness, PII leakage) and configuration audits of agent platforms.
3. **Collect evidence** from FairMind's own runs, your own tools and signed attestations.
4. **Review and decide** in guided, hash-chained workflows with human approval gates.
5. **Ship or block** with a release gate your CI pipeline can call.
6. **Hand auditors** a verifiable inspection pack that maps every requirement down to the evidence behind it.

The output is a version-pinned, tamper-evident evidence trail that an internal reviewer or an external auditor can follow from a framework clause to the measurement behind it.

FairMind supports readiness and review. **It does not certify compliance, approve systems automatically or enforce policy on its own.** Every gate decision waits for a person.

## Who it is for

- **Compliance and risk teams** preparing for EU AI Act, ISO/IEC 42001, NIST AI RMF, DPDP or RBI FREE-AI reviews.
- **ML and platform engineers** who want a release gate in CI instead of a spreadsheet.
- **Teams running LLM agents** (including Claude Managed Agents and MCP-based agents) who need to audit tool permissions, egress, memory and secrets.
- **Auditors** who need evidence they can verify offline, without trusting the vendor.
- **Regulated lenders and fintechs in India** working to RBI FREE-AI and DPDP.

---

## How it works

<div align="center">
  <img src="assets/diagrams/user_features_workflow.png" alt="FairMind workflow: discover AI systems, evaluate, collect evidence, review, gate releases and export audit packs" width="900">
</div>

Every AI system has a **system file** (`/systems/[id]`) that walks it through six lifecycle stages:

| Stage | What happens there |
|---|---|
| **Onboard** | Register the system or promote it from an integration's review queue |
| **Assess** | Run fairness tests, catalogue evaluations and behaviour tests; connect the system under test |
| **Govern** | Read the release gate per framework clause; install packs and run their workflows |
| **Remediate** | Track findings and remediation tasks, then retest |
| **Decision** | Request a release decision; approvers see every check and its reasons |
| **Operate** | Scheduled monitoring snapshots, drift trends and stale-evidence warnings |

Evidence has a **provenance class**: *measured* (FairMind ran it), *imported* (your tool ran it, unverified until reviewed) or *attested* (a person's statement). Attested evidence never counts as proof; it is capped at a manual confidence band.

---

## Key features

### 1. Agentic packs, journeys and workflows

- **51 frameworks, 539 requirements and 90 workflows** ship as a static, validated catalogue. Nothing is seeded into your database.
- A **pack** bundles workflows; a **journey** orders them by framework clause; one workflow run counts toward every framework it maps to through a common-control crosswalk.
- **Guided run engine**: steps such as collect, check, suggest and verify wait for input; ask, exception and decide steps open approval gates; revisions escalate after three rounds.
- **Workflow builder**: each organisation can draft and publish its own immutable versions of a workflow, validated for reachability, termination and approval branches.
- **Hash-chained run ledger** with a `chainValid` check on every run. Tamper-evident.
- **Separation of duties**: when someone decides on their own proposal, the run warns and the ledger records `selfReview: true`.
- **Bring your own AI provider** for the packs agent, with 19 providers: Anthropic, OpenAI, Azure OpenAI, Google Gemini, Amazon Bedrock, Mistral, Cohere, Groq, Together AI, Fireworks, DeepSeek, xAI, Perplexity, Cerebras, OpenRouter, Sarvam AI, Krutrim, Ollama and any OpenAI-compatible server. Keys are encrypted at rest and never returned. Without a provider, deterministic rules write the step and say what is missing.

### 2. Evaluation engines: 31 catalogue evaluations on uploaded files

Each engine declares the files it reads and its settings, and returns a verdict (`passed`, `failed` or `insufficient`), the metrics behind it and per-row detail. Results are stored as measured evidence on the AI system. No engine makes a network call, and uploaded model files are never loaded or executed (pickle files are read opcode by opcode).

| Group | Evaluations |
|---|---|
| **Datasets** | Data drift (PSI, Kolmogorov-Smirnov, classifier-based density ratio, TF-IDF for text), data poisoning, representativeness, completeness and accuracy, duplicates and train-test leakage, personal data, RAG knowledge-base poisoning, label quality |
| **Model outputs** | Task accuracy, answer consistency, calibration, out-of-distribution detection, multilingual parity, selective accuracy, intersectional slices, counterfactual flip rate, production degradation, membership inference, verbatim reproduction |
| **Prompts, config and logs** | System prompt safety, secrets in prompts and config, secrets in agent context, model file and dependency scan, tool poisoning, tool least privilege, MCP permission audit, browser-agent allowlist, cost vs budget, log completeness, runaway loops, processing location |

Personal-data detectors cover India-specific identifiers (Aadhaar with its Verhoeff check, PAN, IFSC) and payment cards (Luhn check). Values are masked in all output.

### 3. Behaviour tests: 20 evaluations against the live AI system

Connect the system under test (an OpenAI-compatible chat endpoint or any HTTP endpoint with a JSON template) and FairMind sends probes and judges the answers with **your own model**.

- **Security**: prompt injection, jailbreaks, system prompt leakage (checked in code), harmful content by hazard category.
- **Privacy**: canary extraction and personal-data echo, checked in code.
- **Quality**: RAG faithfulness (claims supported by the source), robustness under typos and distractors, paraphrase consistency.
- **Fairness**: counterfactual prompt pairs that differ only in group, with a baseline run.
- **Self-test**: planted instructions in evidence are given to FairMind's own packs agent to check it does not follow them.

Probes come from your CSV, or the judge model writes them from the system's intended use. No third-party benchmark data is bundled. Runs execute as background jobs with progress, and a run with more than 10% unanswered probes is marked insufficient.

### 4. Configuration audits of agent platforms

Audit how an LLM agent platform is configured, either through a read-only **Claude Managed Agents** connection (official `anthropic` SDK, list calls only) or by uploading an exported configuration or MCP config (`{"mcpServers": {...}}`).

| Check | What it looks for |
|---|---|
| Excessive agency | High-risk tools (`bash`, `write`, `edit`, `mcp:*`) not set to always ask |
| Data exfiltration | Unrestricted networking, wildcard hosts, hosts off an approved list |
| Memory and context poisoning | Planted instructions and secrets in agent memory |
| Sandbox escape | Memory stores writable by more than one agent |
| Shadow MCP servers and agents | Anything off the approved register |
| MCP authentication | Each MCP server has a vault credential for its URL |
| Credential hygiene | Inline secrets, credentials in MCP URLs, static bearer tokens |
| Tool least privilege | Enabled tools judged against the agent's stated purpose |

A collection the export leaves out counts as *not read*, not *read and empty*, so a check never passes on missing data.

### 5. Fairness testing and bias detection

- **First verdict from a predictions CSV**: upload a file, confirm the suggested column mapping, and get disparate impact (four-fifths rule), demographic parity, equal opportunity, equalized odds and calibration by group, each with a **95% bootstrap interval and a permutation p-value**. Up to 100k rows.
- **India-specific bias** on caste, religion, region, state, district and language attributes.
- **Fairness drift**: monitoring snapshots compare selection rates, impact ratio and score PSI per group against the latest fairness run.
- Legacy predictive, LLM and multimodal bias routes remain for compatibility; see [docs/STATUS.md](docs/STATUS.md) for what is validated.

### 6. Release gate and per-clause framework coverage

- **Five checks**: bias and fairness, data governance, human oversight, monitoring, environmental impact. Each is *proven*, *attested* or *open*, with a confidence and reasons.
- **Impact-by-confidence matrix** produces `go`, `conditional_go` or `no_go`. A measured fairness failure can never produce a plain go; a rejected release decision forces no go.
- **Clause map**: the gate read per framework clause (for example "EU AI Act: 5 of 11 clauses evidenced, 4 attested"), so auditors read the record by article and control.
- **Approvals** are refused while high or critical findings, active critical tasks or a no-go gate are open.

### 7. Monitoring and watch

- Push monitoring snapshots on a schedule (`fairmind monitor` in a cron job or GitHub Actions).
- **Cadence per system**: the monitoring check is proven only while the newest snapshot is fresh; stale monitoring turns the check open with a reason.
- **Sustained drift** across the last N snapshots opens one high-severity finding automatically.

### 8. Inspection packs with an auditor link and offline verification

- A manifest per system: gate verdict and checks, clause map, every evidence entry with its hash, the chain head and the latest seals.
- **Read-only auditor link**: a 30-day, revocable token; only its SHA-256 hash is stored.
- **Offline verify**: `fairmind verify pack.json` recomputes the manifest hash and every chain head with no network, so an auditor does not have to trust FairMind.
- Audit report PDFs include a "Release Gate and Framework Coverage" section.

### 9. Policy center

- Policies with versioned rules mapped to framework controls (AIUC-1, OECD AI Principles and others).
- **Coverage per control** from the latest enforcement result: failing, passing, not checked or no policy. Only published, enforced versions count.

### 10. Integrations-first onboarding

- **MLflow, GitHub and Hugging Face Hub connectors** sync models and AI code into a review queue; promote what matters into the estate.
- Hugging Face sync maps pipeline tag, library, licence, downloads, datasets, languages and base model, and suggests a risk tier.
- An **estate board** groups systems by business line with readiness at a glance.

### 11. Trust and evidence foundation (Assurance V2, default off)

- Immutable target and suite identity, execution envelopes and Passport v2 binding.
- Ed25519 issuer and key administration, trust policies, signature, replay, scope and expiry checks.
- Database-time operational freshness, four-eyes review and governance decisions.
- Transactional idempotency and an append-only per-organisation audit chain.
- Imported evidence from your own tools is stored as unverified and human-review-only until reviewed.

### 12. Security and access control

- Organisation-scoped data with membership checks on every governance route.
- Granular, database-backed permissions; human and service principals are kept apart.
- API keys stored as SHA-256 hashes, revocable on the next request.
- Password reset with single-use, 30-minute links; optional Authentik SSO.
- Request audit trail that records route templates, never raw paths, bodies or tokens.
- GitHub Actions pinned to commit SHAs, CodeQL, Dependabot and OpenSSF Scorecard.

---

## Supported frameworks

The pack catalogue covers **51 frameworks and 539 requirements**, crosswalked through common controls. Highlights:

| Area | Frameworks |
|---|---|
| **AI management and risk** | ISO/IEC 42001, ISO/IEC 42005, ISO/IEC 23894, ISO/IEC 38507, NIST AI RMF 1.0, NIST AI 600-1 Generative AI Profile, IEEE 7000-series |
| **Agents and LLM security** | AIUC-1, OWASP Top 10 for LLM Applications 2025, OWASP Top 10 for Agentic Applications 2026, OWASP MCP Top 10, OWASP Agentic Skills, CSA AI Controls Matrix, CSA MAESTRO, MITRE ATLAS, Google SAIF, NIST AI 100-2 adversarial ML, NIST SP 800-218A |
| **European Union and UK** | EU AI Act (as amended by the Digital Omnibus), Council of Europe Framework Convention on AI, ENISA, UK AI Cyber Security Code of Practice |
| **India** | India AI Governance Guidelines, RBI FREE-AI (7 sutras, 26 recommendations) |
| **Asia-Pacific** | Singapore IMDA agentic and generative AI frameworks, AI Verify, MAS FEAT, Japan AI Guidelines for Business, Korea AI Basic Act, China GenAI measures, TC260 AI Safety Governance Framework, Australia Guidance for AI Adoption |
| **United States** | Colorado SB 26-189, NYC Local Law 144, Texas TRAIGA, Illinois HB 3773, California SB 53, OMB M-25-21 |
| **International** | OECD AI Principles, G7 Hiroshima AI Process, WHO AI for health, FINMA AI guidance, MIT AI Risk Repository, MLCommons AILuminate |

AIUC-1 (135 controls) and the OECD AI Principles are also loaded into the policy center by `setup_db.py`. Legacy compliance pages additionally reference GDPR and India's DPDP Act.

Framework mapping is evidence organisation, not legal compliance or a conformity decision.

---

## Quickstart

You need Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 20+ and npm. You also need **PostgreSQL 14+** (local, Docker, or a Neon branch) with an empty database. The backend runs on PostgreSQL only.

```bash
git clone https://github.com/adhit-r/fairmind.git
cd fairmind
```

**Backend** (first terminal):

```bash
cd apps/backend
cp config/env.example .env        # set DATABASE_URL to your empty PostgreSQL database
uv sync
uv run python scripts/setup_db.py # schema + AIUC-1 and OECD reference data; safe to re-run
uv run uvicorn api.main:app --reload --port 8000
```

`uv run python scripts/setup_db.py verify` checks an existing database without changing it. When the server is ready, the API docs are at http://localhost:8000/docs.

**Frontend** (second terminal):

```bash
cd apps/frontend
echo "BACKEND_INTERNAL_URL=http://localhost:8000" > .env.local
npm install
npm run dev
```

Open http://localhost:1111, create an account on the register page, and sign in.

### Environment configuration

The backend reads `apps/backend/.env`. The essentials:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fairmind   # required, PostgreSQL only
SECRET_KEY=change-me          # signs tokens and derives the key that encrypts stored provider keys
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
# SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD   # for password-reset emails
```

See [`config/env.example`](apps/backend/config/env.example) and the [configuration reference](apps/docs/content/docs/reference/configuration.mdx) for every option. Setup problems are worth reporting: open an issue with the command you ran and the error you got.

---

## Release gate in CI: CLI, GitHub Action, SDK and MCP

Engineers and coding agents can reach FairMind without forms. Mint an API key at `POST /api/v1/auth/api-keys`, then:

**CLI** ([`apps/cli`](apps/cli/README.md), one dependency):

```bash
pipx install ./apps/cli
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...
fairmind gate --system <id>        # exit 0 go, 2 conditional go, 1 no go
fairmind test --system <id> --file predictions.csv --outcome repaid --prediction approved --attributes gender,region
fairmind monitor --system <id> --file recent.csv --attributes gender,region
fairmind verify pack.json          # offline inspection-pack check
```

**GitHub Action**:

```yaml
- uses: adhit-r/fairmind/.github/actions/fairmind-gate@main
  with:
    system: ${{ vars.FAIRMIND_SYSTEM_ID }}
    api-url: ${{ vars.FAIRMIND_API_URL }}
    api-key: ${{ secrets.FAIRMIND_API_KEY }}
    predictions: artifacts/predictions.csv   # optional: run the fairness test first
    outcome: repaid
    prediction: approved
    attributes: gender,region
```

**Python SDK** ([`apps/sdk`](apps/sdk/README.md)):

```python
from fairmind import FairMind

fm = FairMind()  # reads FAIRMIND_API_URL and FAIRMIND_API_KEY
gate = fm.gate(fm.systems()[0]["id"])
print(gate["verdict"], gate["confidence"])
```

**MCP server** ([`apps/mcp`](apps/mcp/README.md)) for Claude Code and other MCP clients, with six tools: `list_systems`, `release_gate`, `clause_map`, `run_fairness_test`, `record_monitoring_snapshot` and `attest_check`.

Guides: [release gate in CI](apps/docs/content/docs/workflows/release-gate-in-ci.mdx), [SDK and MCP](apps/docs/content/docs/workflows/sdk-and-mcp.mdx), [scheduled monitoring](apps/docs/content/docs/workflows/scheduled-monitoring.mdx), [inspection packs](apps/docs/content/docs/workflows/inspection-packs.mdx).

---

## Architecture

<div align="center">
  <img src="assets/diagrams/fairmind_system_architecture.png" alt="FairMind system architecture: Next.js dashboard, FastAPI backend, PostgreSQL, evaluation engines and integrations" width="800">
</div>

- **Frontend**: Next.js dashboard organised around the lifecycle shell (Onboard, Assess, Govern, Remediate, Decision, Operate) plus a library of cross-cutting pages.
- **Backend**: FastAPI with domain-driven routes and services for governance, packs, evaluations, evidence, policies, integrations and trust administration.
- **Evaluation engines**: a registry of file-based, behaviour and platform-audit engines sharing one run and evidence model; behaviour tests run as background jobs.
- **Data**: PostgreSQL is authoritative for users, organisations, governance, evidence and audit chains. DuckDB serves dataset analytics; Redis is an optional cache.
- **Clients**: CLI, Python SDK, MCP server and a composite GitHub Action, all over the same API-key auth.

---

## Technology stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2, uv |
| Data | PostgreSQL 14+ (Neon in production), DuckDB, Redis (optional) |
| ML and statistics | scikit-learn, pandas, NumPy, SciPy |
| LLM | BYOK across 19 providers, official `anthropic` SDK for platform audits |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Radix UI and shadcn/ui, React Flow, Recharts |
| Docs | Fumadocs, with `llms.txt` |
| Website | Astro |
| Testing | pytest (on PostgreSQL 14), Playwright, mocked-transport tests for CLI, SDK and MCP |
| CI and security | GitHub Actions, CodeQL, Dependabot, OpenSSF Scorecard |

---

## Repository layout

| Path | What it is |
|---|---|
| `apps/backend/` | FastAPI backend (Python, uv): governance, packs, evaluation, evidence, policy and trust APIs |
| `apps/frontend/` | Next.js dashboard (TypeScript, Tailwind, Playwright tests) |
| `apps/cli/` | `fairmind` CLI: gate, test, monitor, verify |
| `apps/sdk/` | `fairmind` Python SDK |
| `apps/mcp/` | `fairmind-mcp` MCP server |
| `apps/docs/` | Documentation site published at docs.fairmind.xyz |
| `apps/website/` | Marketing site (Astro) |
| `apps/ml/` | ML models and visualization utilities |
| `.github/actions/fairmind-gate/` | Composite GitHub Action for the release gate |
| `docs/` | Status, architecture notes, ADRs, audits and plans |

---

## API overview

Interactive docs run at `http://localhost:8000/docs`. Main route groups:

| Area | Routes |
|---|---|
| AI systems and gate | `/api/v1/ai-governance/systems`, `/systems/{id}/gate`, `/systems/{id}/clause-map` |
| Fairness and monitoring | `/systems/{id}/fairness-runs`, `/systems/{id}/monitoring-runs`, `/systems/{id}/monitoring-policy`, `/systems/{id}/attestations` |
| Packs and workflows | `/api/v1/packs`, `/packs/workflows/{id}/draft`, `/packs/runs/{id}/steps/{step}/output` |
| Evaluations | `/packs/evaluations/{id}/engine`, `/packs/evaluations/{id}/runs`, `/packs/evaluation-jobs/{id}` |
| System under test | `/packs/ai-systems/{id}/target`, `/target/test` |
| Inspection packs | `/api/v1/ai-governance/packs`, `/packs/{id}/share`, `/api/v1/public/packs/{id}` |
| Policies | `/policies`, `/policies/coverage` |
| Auth | `/api/v1/auth`, `/auth/api-keys`, password reset |
| Audit | `/api/v1/audit-logs` |

The catalogue includes legacy endpoints kept for compatibility. An endpoint's presence does not mean it is bound to the v2 evidence contract or independently validated. Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

---

## Development and tests

```bash
cd apps/backend && FAIRMIND_TEST_POSTGRES_URL=postgresql://... uv run pytest
cd apps/frontend && npm run test
```

Backend tests need `FAIRMIND_TEST_POSTGRES_URL` pointing at a throwaway PostgreSQL 14 server; each test gets its own temporary database. The frontend tests use Playwright; run `npx playwright install` once first. CI runs the backend suite on `postgres:14`, the frontend type-check and unit tests, and the CLI, SDK and MCP tests. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

---

## Deployment

- **Backend**: Docker image from `apps/backend`; run `setup_db.py` against the target database on each release (it adds only what is missing).
- **Frontend**: Docker image from `apps/frontend`, or any Next.js host.
- **Database**: any PostgreSQL 14+; Neon works well.

See the [deployment reference](apps/docs/content/docs/reference/deployment.mdx) and [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).

---

## Project status

**Internal alpha.** The packs, evaluation engines, behaviour tests, platform audits, release gate, inspection packs and the evidence, trust and review foundations are built and tested. Sandboxed evaluation workers, independently validated LLM, agent and multimodal packs, and realtime assurance are not shipped yet. The Assurance V2 control plane stays off by default.

No compliance certification, automatic approval, automatic enforcement or "FairMind Verified" claim is made. See [docs/STATUS.md](docs/STATUS.md) for exactly what can and cannot be claimed today, and [ROADMAP.md](ROADMAP.md) for what comes next.

---

## Contributing

Contributions are welcome, from typo fixes to evaluation engines and framework catalogues. Start with [CONTRIBUTING.md](CONTRIBUTING.md), then pick an issue labelled [good first issue](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [help wanted](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22). Questions and ideas go to [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions).

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Please do not report vulnerabilities in public issues. See [SECURITY.md](SECURITY.md) for how to report them privately.

## Citing FairMind

If you use FairMind in research, please cite it. Metadata is in [CITATION.cff](CITATION.cff) and [codemeta.json](codemeta.json); the concept DOI is [10.5281/zenodo.23982915](https://doi.org/10.5281/zenodo.23982915).

## License

FairMind is created and maintained by [Axonome](https://www.fairmind.xyz/about). It is released under the MIT licence; see [LICENSE](LICENSE).

---

<sub>Keywords: AI governance, AI assurance, AI compliance, responsible AI, AI audit, agentic AI governance, LLM evaluation, LLM red teaming, prompt injection testing, MCP security, AI fairness, bias detection, EU AI Act compliance, ISO 42001, NIST AI RMF, AIUC-1, DPDP Act, RBI FREE-AI, model risk management, AI release gate.</sub>

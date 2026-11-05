<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind" width="800">
</div>

<br>

<div align="center">

**Open-source AI assurance workbench for models and agents**

*Bring your tests. Produce evidence you can defend.*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Good first issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Contributors](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23982915.svg)](https://doi.org/10.5281/zenodo.23982915)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/adhit-r/fairmind/badge)](https://scorecard.dev/viewer/?uri=github.com/adhit-r/fairmind)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Website](https://fairmind.xyz) | [Docs](https://docs.fairmind.xyz) | [Contributing](CONTRIBUTING.md) | [Discussions](https://github.com/adhit-r/fairmind/discussions) | [Leer en español](README.es-ES.md)

</div>

---

## What FairMind is

FairMind is a governance and assurance platform for AI systems, including LLM agents. A team registers an AI system, activates a governance framework such as AIUC-1, NIST AI RMF, the EU AI Act or India's DPDP Act, and then works through the controls that apply: running evaluations, attaching evidence from its own tools, reviewing findings, fixing failures and retesting. The output is a version-pinned evidence trail that an internal reviewer or an external auditor can follow from a requirement down to the evidence behind it.

FairMind supports readiness and review. It does not certify compliance, approve systems automatically or enforce policy on its own.

**Status: internal alpha.** The evidence contract, trust and review foundations are built and tested; sandboxed evaluation workers and validated LLM, agent and multimodal evaluation packs are not shipped yet. See [docs/STATUS.md](docs/STATUS.md) for exactly what can and cannot be claimed today.

## Quickstart

You need Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 20+ and npm. You also need PostgreSQL 14+ (local, Docker, or a Neon branch) with an empty database.

```bash
git clone https://github.com/adhit-r/fairmind.git
cd fairmind
```

**Backend** (first terminal):

```bash
cd apps/backend
cp config/env.example .env        # set DATABASE_URL to your empty PostgreSQL database
uv sync
uv run python scripts/setup_db.py # schema + AIUC-1 reference data; safe to re-run
uv run uvicorn api.main:app --reload --port 8000
```

When it is ready, the API docs are at http://localhost:8000/docs.

**Frontend** (second terminal):

```bash
cd apps/frontend
echo "BACKEND_INTERNAL_URL=http://localhost:8000" > .env.local
npm install
npm run dev
```

Open http://localhost:1111, create an account on the register page, and sign in.

Setup problems are worth reporting: open an issue with the command you ran and the error you got.

## Repository layout

| Path | What it is |
|---|---|
| `apps/backend/` | FastAPI backend (Python, uv): governance, evaluation, evidence and compliance APIs |
| `apps/frontend/` | Next.js dashboard (TypeScript, Tailwind, Playwright tests) |
| `apps/docs/` | Documentation site published at docs.fairmind.xyz |
| `apps/website/` | Marketing site (Astro) |
| `apps/ml/` | ML models and visualization utilities |
| `docs/` | Architecture notes, ADRs, audits and plans |

## Running tests

```bash
cd apps/backend && uv run pytest
cd apps/frontend && npm run test
```

The frontend tests use Playwright; run `npx playwright install` once before the first run. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Contributing

Contributions are welcome, from typo fixes to evaluation packs. Start with [CONTRIBUTING.md](CONTRIBUTING.md), then pick an issue labelled [good first issue](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [help wanted](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22). Questions and ideas go to [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions).

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Please do not report vulnerabilities in public issues. See [SECURITY.md](SECURITY.md) for how to report them privately.

## License

FairMind is created and maintained by [Axonome](https://www.fairmind.xyz/about). It is released under the MIT licence; see [LICENSE](LICENSE).

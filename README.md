<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind" width="800">
</div>

# FairMind

**Evidence-grade AI assurance control plane.**

FairMind is building the foundations for reproducible, scoped, reviewable AI
assurance evidence. The current release line is an **internal, default-off
alpha**. It is not a generally available evaluation service, certification
service, automatic approval system, or automatic enforcement product.

[![Release](https://img.shields.io/badge/release-v2.1.0--alpha.1-orange)](docs/releases/v2.1.0-alpha.1.md)
[![Assurance status](https://img.shields.io/badge/assurance-internal%20alpha-orange)](docs/superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## P0 trustworthy control plane

`v2.1.0-alpha.1` packages the completed P0 control-plane and frontend/design
checklists at an alpha boundary. It provides:

- Immutable v2 target, suite, execution-envelope, and evidence bindings.
- Passport v2 signature, scope, expiry, replay, admission, and trust-policy
  checks behind separately gated routes.
- PostgreSQL-authoritative trust administration, operational freshness,
  idempotency, audit chains, review/decision separation, and guarded owner
  overrides.
- A dashboard that makes trust, freshness, evidence, and governance-decision
  state visible without representing unavailable packs as executable.
- Explicit unavailable states for LLM judge, LLM testing, explainability,
  modern-bias, and multimodal packs.

The release does **not** include sandboxed worker execution, calibrated
predictive/LLM/agent/code/vision/audio/video evaluation packs, realtime or
post-deployment assurance, a completed retention/export lifecycle, or any
compliance, conformity, or certification determination.

| Roadmap area | Complete | Status |
| --- | ---: | ---: |
| P0 trustworthy control plane | 19/19 | 100% |
| P0 frontend/design corrections | 10/10 | 100% |
| P1 isolated workers | 0/9 | 0% |
| P2 real evaluation engines | 0/7 | 0% |
| P3 modality packs | 0/9 | 0% |
| P4 pre/realtime/post assurance | 0/7 | 0% |
| P5 research and product assets | 0/8 | 0% |
| Public contracts | 9/10 | 90% |
| Verification and rollout gates | 0/13 | 0% |
| **P0 release branch total** | **38/92** | **41.3%** |

The separate development branch has isolated-worker work in progress; it is
not part of this P0 alpha release.

## Before you use it

Treat P0 outputs as supporting engineering evidence only. An organization and
its counsel remain responsible for deciding whether a law, framework, control,
or conformity obligation applies. FairMind does not establish EU AI Act, GDPR,
DPDPA, ISO, NIST, or other compliance by itself.

The default-off gates are intentional. Do not enable evidence-admission,
trust-administration, review, or governance-decision routes outside a
controlled internal environment until their operational prerequisites and
release gates are satisfied.

## Run locally

Requirements:

- Python 3.11 or later and [uv](https://docs.astral.sh/uv/)
- Node.js 20 or later for the dashboard and docs site
- Node.js 22.12 or later for the Astro public website
- [Bun](https://bun.sh/) for frontend unit tests

Start the backend:

```bash
git clone https://github.com/adhit-r/fairmind.git
cd fairmind/apps/backend
uv sync --extra test
cp config/env.example .env
uv run python scripts/create_dev_user.py
uv run python -m uvicorn api.main:app --reload --port 8000
```

In a second terminal, start the dashboard:

```bash
cd fairmind/apps/frontend
npm ci
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Optional documentation site:

```bash
cd fairmind/apps/docs
npm ci
npm run dev
```

Local URLs:

- Dashboard: `http://localhost:1111`
- Backend API: `http://localhost:8000`
- Backend API reference: `http://localhost:8000/docs`
- Documentation site: `http://localhost:3333`

These local services are development surfaces, not production deployment
evidence.

## Verify the P0 release surface

Run the focused checks from the repository root:

```bash
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh

cd apps/backend
uv run pytest -q \
  tests/test_api_main_assurance_v2_route_gate.py \
  tests/test_evaluation_worker_authorization.py \
  tests/test_verified_evidence_admission_service.py \
  tests/test_verified_evidence_link_service.py \
  tests/test_governance_decision_service.py

cd ../frontend
bun test src
npm run typecheck
npm run build

cd ../docs
npm run build
```

Native PostgreSQL 14 controls are exercised by the release workflow against a
disposable database. See the committed [release notes](docs/releases/v2.1.0-alpha.1.md)
for the exact CI matrix and known limits.

## Architecture boundary

Active backend code follows:

```text
api -> application -> domain -> infrastructure
```

Older compatibility modules remain in the repository. Their existence or a
legacy endpoint name does not establish that the capability is bound to the v2
evidence contract or independently validated.

## Documentation and support

- [P0 release boundary](apps/docs/content/docs/release-boundary.mdx)
- [Getting started](apps/docs/content/docs/getting-started.mdx)
- [Assurance workflow](apps/docs/content/docs/assurance-workflow.mdx)
- [Operator runbook](apps/docs/content/docs/operator-runbook.mdx)
- [EU AI Act evidence crosswalk](apps/docs/content/docs/eu-ai-act-crosswalk.mdx)
- [Release notes](docs/releases/v2.1.0-alpha.1.md)
- [2027 assurance roadmap](docs/superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md)
- [P0 evidence-admission architecture](docs/architecture/verified-evidence-admission-task12b.md)
- [GitHub issues](https://github.com/adhit-r/fairmind/issues)
- [GitHub discussions](https://github.com/adhit-r/fairmind/discussions)

The hosted docs and GitHub Wiki are being aligned with this alpha. Until that
work is published, this README and the committed release notes are the
canonical public release description.

## Security and contribution

Report vulnerabilities privately to `security@fairmind.xyz`; do not include
them in public issues. Contributions should preserve the default-off gates,
tenant scope, evidence bindings, and the backend dependency direction. See
[CONTRIBUTING.md](CONTRIBUTING.md) if present in your checkout.

## License

FairMind is licensed under the [MIT License](LICENSE).

# FairMind assurance roadmap

> Status at the P0-only `v2.1.0-alpha.1` release candidate. Checklist completion is not production readiness.

FairMind is building an evidence-grade AI assurance control plane. Each public execution capability must pass its own contract, benchmark, sandbox, and rollout gates before it is described as available.

## Current release boundary

P0 establishes internal, default-off foundations for exact evaluation scope, evidence integrity, trust administration, operational freshness, reviewer separation, and append-only governance decisions.

P0 does **not** ship evaluator workers, automatic enforcement, validated modality packs, realtime assurance, certification, automatic compliance decisions, or a “FairMind Verified” designation.

| Roadmap area | Complete | Status |
|---|---:|---:|
| P0 trustworthy control plane | 19/19 | 100% |
| P0 frontend/design corrections | 10/10 | 100% |
| P1 isolated workers | 0/9 | 0% |
| P2 real evaluation engines | 0/7 | 0% |
| P3 modality packs | 0/9 | 0% |
| P4 pre/realtime/post assurance | 0/7 | 0% |
| P5 research and product assets | 0/8 | 0% |
| Public contracts | 9/10 | 90% |
| Verification and rollout gates | 0/13 | 0% |
| **Total checklist** | **38/92** | **41.3%** |

The P1 development lane contains separate, incomplete worker-foundation work. It is intentionally excluded from this release.

## P0 trustworthy control plane

Complete in the release candidate:

- Immutable target and suite versions.
- Versioned plans and one suite-execution record per selected suite.
- RFC 8785-hashed Execution Envelope V2 bindings.
- Evidence Passport V2 scope, chronology, and signature bindings.
- Evidence issuer, Ed25519 key, and immutable trust-policy administration.
- Separately gated evidence submission, linking, review, and governance decisions.
- Database-time operational freshness and invalidation checks.
- Four-eyes review plus audited, decision-only owner and delegated separation overrides.
- Transactional idempotency and an append-only per-organization audit hash chain.
- Literal permissions, including a service-principal-only worker permission.
- Legacy V1 records remain readable but cannot be used to fabricate V2 authority.
- Unsupported execution surfaces fail closed in both API and UI.

See the [P0 release boundary](apps/docs/content/docs/release-boundary.mdx) and [master engineering checklist](docs/superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md).

## Next engineering stages

### P1 — isolated workers

- PostgreSQL-authoritative leased jobs and attempt state.
- Signed completion bound to a live lease and exact Passport.
- Cancellation arbitration and recovery.
- Opaque target and artifact brokers.
- Non-root, read-only, resource-bounded evaluator sandboxes.
- Deny-default egress, kill switches, and operational security metrics.

P1 does not become available when queue rows exist. A real signed suite must complete end to end inside the sandbox and pass Gate B.

### P2 — real evaluation engines

- Independently validate predictive fairness kernels.
- Add a common LLM and agent evaluation harness.
- Add security and CI/red-team adapters.
- Quarantine fixed, simulated, mislabeled, and fail-open evaluators.
- Preserve failing or unavailable evaluator outcomes without translating them into success.
- Treat LLM judges as calibrated supporting signals, never sole verdicts.

### P3 — modality packs

Planned packs cover predictive models, LLM/text, agents, code generation, vision input, image generation, audio, video, and cross-modal systems. Each pack remains unavailable until its own frozen manifest, benchmark report, sandbox report, limitations, and release gate are complete.

### P4 — lifecycle assurance

Planned work includes pre-deployment evaluation, synchronous deterministic realtime checks, queued deep checks, post-output and side-effect review, scheduled post-deployment evaluation, drift and incident replay, and hybrid human review. Enforcement remains advisory until separate safety gates pass.

### P5 — evidence and product assets

Planned work includes evidence-laundering and realtime-latency research corpora, cross-modal provenance research, immutable manifests and calibration reports, one authoritative capability registry, and product media based only on validated screens and claims.

## Public contract still open

The remaining contract item is the public route family for target and suite catalogs, suite evidence links and reviews, cancellation, worker leases, and realtime pre/post evaluation. It will be completed incrementally and exposed only as each child capability passes its independent gate.

## Rollout gates

- **Gate A — private control-plane pilot:** two organizations, 100 workflows, 14 days, zero isolation or integrity failures, automatic enforcement off.
- **Gate B — worker alpha:** one real signed sandboxed suite end to end with failure injection and human approval only.
- **Gate C — modality beta:** every exposed capability independently passes benchmark and sandbox gates with visible limitations.
- **Gate D — public execution:** GA adapter and reports, independent red team, 30-day soak, and zero unresolved integrity, isolation, Critical, or High defects.

No gate is complete in this release candidate.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [master engineering checklist](docs/superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md). Work should preserve capability gates, exact scope, evidence provenance, and explicit unavailable states.

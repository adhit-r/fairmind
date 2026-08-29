# FairMind 2027 AI Assurance Platform — Master TODO

**Goal:** Evolve FairMind from a model-focused governance control plane into an evidence-grade assurance platform for predictive models, LLM applications, agents, code generation, vision input, image generation, audio, video, and multimodal systems.

**Implementation base:** `29eaba4` in the isolated evaluation-workbench worktree. The primary `fairmind-e/p2b-paper-wedge` checkout is intentionally out of scope.

**Non-negotiable sequence:** evidence integrity → isolated execution → real adapters → independently calibrated modality packs → pre/realtime/post lifecycle assurance → capability-scoped public claims.

## P0 — Trustworthy control plane

- [x] Capture fresh backend, frontend, browser, build, PostgreSQL, boundary, and archive-import baselines.
- [x] Split evaluation planning, runs, evidence admission, decisions, and worker ports while preserving `api -> application -> domain -> infrastructure`.
  - Checkpoint: catalog/version, planning, and run use cases now have narrow application services and ports composed over one request-scoped transactional UoW; evidence admission, review, governance decision, catalog, and trust retain their independently composed boundaries. Pure binding, freshness, evaluator-registration, and JWK policies live in neutral application modules, so infrastructure imports no application services. The worker port is declaration-only: no route, adapter, queue, lease, credential, persistence, or execution was added. See `docs/audits/2026-08-14-p0-assurance-service-port-split.md`.
- [x] Add immutable target versions containing exact subject, version, digest, deployment, connector, and manifest identity.
- [x] Preserve the current target kinds and add `vision_model`.
- [x] Add immutable suite versions with compatible target kinds, phases, depths, delivery modes, configuration schema, budgets, runner digest, adapter version, and result contract.
- [x] Replace authoritative free-text suite references and bare target kinds with version IDs and configured suite selections.
- [x] Generate and RFC 8785-hash an immutable Execution Envelope v2 for every run.
- [x] Create one suite-execution record per selected suite.
- [x] Bind Passport v2 to exact tenant, system, target, suite, plan, configuration, lifecycle, delivery, evaluator, nonce, and chronology.
- [x] Keep Passport v1 readable but ineligible for v2 runs.
- [x] Add evidence issuers, Ed25519 keys, immutable trust policies, admissions, freshness, and append-only reviews.
  - Checkpoint: migration 013g derives current operational freshness from the exact admission, receipt, evaluator registration, issuer, signing key, policy, review, and chronology graph. PostgreSQL owns gate time and serializes authority changes with review/decision mutations; SQLite remains a fail-closed parity fixture. See `docs/audits/2026-08-13-p0-operational-evidence-freshness.md` for proof and remaining public-release gaps.
- [x] Require verified evidence from FairMind workers and external adapters; imports may remain unsigned only as visibly unverified human-review material.
  - Checkpoint: signed Passport V2 evidence still requires its exact approved evaluator registration, issuer, and key. A separate default-off import route can persist only terminal `imported_report` material as claimed, unverified, human-review-only, and decision-ineligible. Migration 013i binds the immutable import snapshot, evidence row, admission, link, suite projection, active authority graph, provenance, chronology, and policy-derived expiry; PostgreSQL rejects mismatches and the UI never presents the material as verified. See `docs/audits/2026-08-21-p0-evidence-source-import.md`.
- [x] Keep linking separate from governance decision-making; a link yields `review` or `insufficient`, never automatic approval/blocking.
- [ ] Add granular plan, run, evidence, decision, catalog, trust, worker, and separation-override permissions.
  - Checkpoint: live human plan, run, evidence, decision, catalog, and trust-administration routes now require literal persisted permissions, and direct-mounted v2 routers fail closed. The decision-only audited canonical-owner override is implemented and default-off; granular/delegable separation-override authorization, service-only worker authorization, and independent submit/link surfaces remain open.
- [x] Enforce four-eyes review and audited owner overrides.
  - Checkpoint: migration 013j makes evidence review permanently non-overridable and binds decision-only canonical-owner exceptions to exact persisted authority, one immutable decision, completed idempotency, and the per-organization success-audit chain. The route is separately default-off and PostgreSQL-authoritative. See `docs/audits/2026-08-21-p0-owner-decision-override.md`.
- [x] Add 30-day transactional idempotency and an append-only per-organization audit hash chain.
  - Checkpoint: migration 013h makes PostgreSQL the database-clock authority for exact 2,592,000-second idempotency generations, immutable completion bindings, expired-only atomic rollover, and non-deletable identity anchors. Every enabled Assurance V2 mutation reaches the shared transactional UoW, and successful plus expected/domain-rejected outcomes bind to the per-organization audit chain. This is a minimum anti-reexecution window, not bounded data retention or production-runtime proof. See `docs/audits/2026-08-13-p0-idempotency-audit-integrity.md`.
- [x] Feature-disable automatic enforcement, untrusted external linking, workers, and unsupported modality packs at both API and UI boundaries.
  - Checkpoint: automatic enforcement and FairMind-worker delivery are unconditionally unavailable for new legacy and Assurance V2 plans, and retired switches cannot re-enable them. New generic Evidence Hub external URLs and direct entity links are default-off at API and UI boundaries; the explicit reviewed-linking lane does not restore legacy Passport linking. Unsupported LLM-judge, LLM-testing, modern-bias, multimodal, and explainability evaluator surfaces are represented by inert dashboard availability states with no evaluator hooks, forms, fake results, exports, or endpoint requests; their dedicated routers are unmounted and removed from development-public path families. Assurance V2 target-kind vocabulary, including `vision_model`, is preserved.
- [x] Add forward migration 013 without rewriting migration 012; extend checksum-ledger drift detection.
- [x] Mark existing plans/runs contract v1 without fabricating registry identities; keep them readable but prevent new execution until upgraded.

Task 12B milestone: Passport v2 binding, trust authority, verified admission,
append-only review, operational freshness, and link separation are implemented
as an internal, default-off PostgreSQL-authoritative control-plane kernel. They
do not imply generally available evaluator execution, compliance,
certification, automatic approval, worker execution, or runtime enforcement.
The canonical-owner decision override is implemented but default-off;
production provisioning, enablement, and rollout remain an independent gate.
Worker execution identity, independently invocable submit/link surfaces, and
validated public execution routes remain independent release gates. Imported
reports are inspection material only and cannot enter formal
evidence review or governance decision authority.

## P0 — Frontend and design

- [ ] Add one shared session provider above the dashboard shell and bind identity to `/auth/me`.
- [ ] Connect both logout controls; clear local tokens, authenticated caches, and cross-tab state even when revocation fails.
- [ ] Self-host the profile portrait and eliminate authenticated third-party portrait requests.
- [ ] Key state by organization/system/plan/run and mask prior-scope state synchronously during route changes.
- [ ] Reject parsed responses whose scope differs from the request and remove `selected_org_id` as secondary path authority.
- [ ] Render execution status, evaluator evidence result, and governance verdict as separate axes.
- [ ] Show signer, source, admission, freshness, review, expiry, limitations, and invalidation reason.
- [ ] Preserve layered suite/modality verdicts plus one overall reviewer verdict.
- [ ] Update `DESIGN.md` with the three-axis model, admission states, capability truth table, worker security envelope, local identity/icon system, and binding model.
- [ ] Preserve the white/black/orange/teal neobrutalist product language; no emoji, purple gradients, generic AI visuals, or dashboard rewrite.

## P1 — Isolated execution foundation

- [ ] Add migration 014 for worker identities, leased jobs, suite attempts, artifacts, and cancellation.
- [ ] Implement a PostgreSQL `FOR UPDATE SKIP LOCKED` queue with 60-second leases, 20-second heartbeats, expiry recovery, and manifest-controlled retries capped at three.
- [ ] Implement `queued`, `leased`, `running`, `awaiting_evidence`, `succeeded`, `failed`, `timed_out`, and `cancelled` job states.
- [ ] Require the live lease token and matching signed Passport v2 for completion; cancellation wins races.
- [ ] Add `WorkerCapabilities` and `EvaluationWorker.execute(ExecutionEnvelopeV2)` ports.
- [ ] Store artifacts by immutable SHA-256 in S3/MinIO-compatible storage; exclude credentials, secrets, and chain-of-thought.
- [ ] Resolve opaque target/artifact bindings through short-lived brokers.
- [ ] Run evaluators non-root with read-only roots, ephemeral scratch, no host socket, dropped capabilities, restrictive syscalls, bounded resources, quarantined inputs, and deny-default network.
- [ ] Add scoped egress credentials, kill switches, and operational/security metrics.

## P2 — Real evaluation engines

- [ ] Build a validated predictive fairness pack covering parity, opportunity, odds, calibration, subgroups, robustness, drift, privacy, and intersections; fix bootstrap resampling and cross-check AIF360/Fairlearn.
- [ ] Add an Inspect adapter as the common LLM/agent harness.
- [ ] Add garak for LLM security and Promptfoo for CI/red-team/agent/multimodal scenarios.
- [ ] Add Giskard later as an external/imported adapter.
- [ ] Quarantine fixed, simulated, mislabeled, and fail-open legacy evaluators; retain only independently validated kernels.
- [ ] Never translate evaluator failure or unavailable input into passing evidence.
- [ ] Treat LLM judges as calibrated supporting signals, never sole verdicts.

## P3 — Modality packs

- [ ] LLM/text: injection, jailbreak, unsafe output, privacy, hallucination, bias, multilingual consistency, robustness.
- [ ] Agents: indirect injection, tool/memory poisoning, permission misuse, excessive agency, exfiltration, irreversible actions, trajectory compliance.
- [ ] Code generation: compile/test, insecure code, dependencies, secrets, command injection, licenses, tool behavior.
- [ ] Vision input: OCR/typographic and low-visibility instructions, metadata carriers, hidden instructions, perturbations, transform survival.
- [ ] Image generation: unsafe content, demographic/stereotype bias, adherence, provenance, watermarking, transformation history.
- [ ] Audio: ASR-mediated and obfuscated instructions, transcoding survival, privacy, accent disparities, generated-voice misuse.
- [ ] Video: sparse-frame, subtitle/audio-track, temporal injection, unsafe content, representation, frame-sampling sensitivity.
- [ ] Multimodal: cross-modal conflict and attack transfer, retrieval/context contamination, tool effects, end-to-end transformation DAG.
- [ ] Map findings to versioned governance controls as candidate evidence; require reviewer acceptance and generate reproducible hash-bound audit packs without automatic compliance claims.

## P4 — Pre, realtime pre/post, and post-deployment assurance

- [ ] Add `lifecyclePhase` to run creation; each run executes one selected phase.
- [ ] Support pre-deployment deep/CI/release-gate evaluation with verified current reviewed evidence.
- [ ] Add synchronous realtime pre-input/tool-action evaluation for deterministic low-latency suites and queue deep checks under the same interaction ID.
- [ ] Add realtime post-output/tool/side-effect/media evaluation with an advisory result and evidence-pending state.
- [ ] Support scheduled post-deployment evaluation, drift, incident replay, provider changes, and evidence expiry.
- [ ] Implement hybrid inline deterministic plus asynchronous stochastic/human review.
- [ ] Keep enforcement advisory until accuracy, rollback, circuit-breaker, latency, and independent safety gates pass.

## P5 — Research, documentation, and product evidence

- [ ] EvalAttest: evidence-laundering corpus across bindings, signers, phase, and chronology.
- [ ] GateTrace: realtime detection, latency, utility, and asynchronous follow-up.
- [ ] X-Provenance: cross-modal transformations and causal-stage attribution.
- [ ] Publish immutable manifests, calibration reports, limitations, confidence intervals, and reproducibility guidance.
- [ ] Make the capability registry authoritative for product, docs, website, and sales claims.
- [ ] Use “AI assurance control plane” until execution capabilities independently pass their gates.
- [ ] After worker alpha, produce the product deck, audit examples, NotebookLM-style podcast, Remotion video, and HyperFrames video from validated screens and claims.
- [ ] Run whole-repository quality and organization audits at each release gate.

## Public contracts

- [x] `EvaluationPlanV2Create`: contract version, target version, phases, depth, enforcement, delivery, configured suite versions.
- [x] `EvaluationRunV2Create`: trigger, lifecycle phase, required `Idempotency-Key`.
- [x] `ExecutionEnvelopeV2`: server-generated IDs/hashes, target and suite bindings, lifecycle/enforcement/delivery, nonce, budgets, inputs, trust policy.
- [x] `EvidencePassportV2.executionBinding`: envelope ID/hash, suite execution, target/suite versions and digests, nonce.
- [x] `EvaluationRunResponse`: technical status, evidence outcome, governance verdict, layer verdicts, suite executions, envelope hash, verdict version.
- [x] Evidence result: `pending | passed | passed_with_limitations | failed | informational | error | unavailable | insufficient_data | unknown`.
- [x] Admission: `pending | verified | unverified | expired | superseded | rejected | trust_error`.
- [x] Review: `pending | accepted | rejected`; freshness: `current | expiring | stale | superseded`.
- [x] Preserve `technicalStatus=succeeded` with `evidenceResultStatus=failed` when the evaluator ran correctly and found a failing target.
- [ ] Add target/suite catalogs, suite-specific evidence links, reviews, CAS decisions, cancellation, worker leases, and realtime pre/post endpoints under the existing AI-governance route family.

## Verification and rollout gates

- [ ] Mutate every envelope field independently; no mismatch may yield decision-grade evidence.
- [ ] Test valid/tampered/unknown/revoked/expired/replayed/wrong-tenant/wrong-suite signatures and timestamp policy.
- [ ] Test cross-tenant isolation, 20-request idempotency/concurrency, link races, lost responses, cancellation, lease recovery, and audit-chain integrity.
- [ ] Fuzz canonical JSON and adversarially test sandbox/file/network/resource/media boundaries.
- [ ] Complete 1,000 adversarial sandbox jobs with zero escape, unauthorized egress, host access, secret exposure, or orphaning.
- [ ] Preserve the focused backend/frontend/browser/build/PostgreSQL/boundary baseline and add continuous CI security lanes.
- [ ] Require zero unresolved or unaccepted Critical/High findings.
- [ ] Per public modality: freeze manifests; use at least 100 benign and 100 adversarial independently labelled cases across at least two target families; repeat stochastic cases three times; require kappa >= 0.70, macro-F1 >= 0.80, per-class recall >= 0.70, and benign false-positive rate <= 5%.
- [ ] Gate A private control-plane pilot: two organizations, 100 workflows, 14 days, zero isolation/integrity failures, automatic enforcement off.
- [ ] Gate B worker alpha: one real signed sandboxed suite end to end with failure injection and human approval only.
- [ ] Gate C modality beta: each exposed capability independently passes benchmark and sandbox gates with visible limits.
- [ ] Gate D public execution: GA adapter, reports, independent red team, 30-day soak, zero open integrity/isolation/Critical/High defect.
- [ ] Keep “FairMind Verified,” certification, automatic compliance, and automatic enforcement prohibited pending a separate independent safety program.

## Defaults

- PostgreSQL is release authority; SQLite is a parity fixture.
- PostgreSQL leasing is the first worker queue; no Redis/Celery until capacity evidence requires it.
- FairMind owns orchestration, scope, trust, evidence, findings, review, and decisions; specialist engines execute tests.
- All three delivery paths and all three lifecycle phases remain supported.
- Layered results and one overall verdict are both required.
- Unsupported capability combinations fail preflight.

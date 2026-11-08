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
  - Checkpoint: signed Passport V2 evidence still requires its exact approved evaluator registration, issuer, and key. The existing default-off submission endpoint is submit-only: it authenticates and persists the evidence run, canonical Passport revision, verification receipt, verified admission, and nonce claim, but does not create a link or suite/run projection. The separately default-off exact link endpoint requires `evaluation:evidence:link`, audits and idempotently links only stored canonical Passport material, revalidates live authority, and atomically creates the link and derived projections. PostgreSQL migration 013k backstops the link's exact current authority chain. A separate default-off import route can persist only terminal `imported_report` material as claimed, unverified, human-review-only, and decision-ineligible. Migration 013i binds the immutable import snapshot, evidence row, admission, link, suite projection, active authority graph, provenance, chronology, and policy-derived expiry; PostgreSQL rejects mismatches and the UI never presents the material as verified. See `docs/audits/2026-08-29-p0-verified-evidence-submit-link.md` and `docs/audits/2026-08-21-p0-evidence-source-import.md`.
- [x] Keep linking separate from governance decision-making; a link yields `review` or `insufficient`, never automatic approval/blocking.
  - Checkpoint: review and normal governance decisions treat the requester, evidence submitter, and evidence linker as separated actors. The exact default-off canonical-owner waiver audit records waived submitter/linker relationships; it remains decision-only and non-delegable.
- [x] Add granular plan, run, evidence, decision, catalog, trust, worker, and separation-override permissions.
  - Checkpoint: live human plan, run, evidence, decision, catalog, trust-administration, submit, and link routes require literal persisted permissions, and direct-mounted v2 routers fail closed. Submit and link are independently invocable, separately permissioned, and separately default-off. The unmounted worker predicate accepts only a tenant-bound service access principal with the literal `evaluation:worker` permission and a canonical permission array; human, admin, wildcard, API-key, missing-tenant, and cross-tenant principals fail closed. Worker authentication, credential issuance, mounted routes, and execution remain P1. Canonical-owner override authority requires both `evaluation:decision` and the reserved `evaluation:separation:override` permission in PostgreSQL. Migration 013l adds a default-off, immutable, 30-minute, exact-run grant through which that owner can delegate one separation exception to one named actor who retains `evaluation:decision`; wrong actors, permission loss, graph/version drift, expiry, reuse, and non-atomic audit fabrication fail closed. See `docs/audits/2026-08-30-p0-delegated-separation-override.md`.
- [x] Enforce four-eyes review and audited owner overrides.
  - Checkpoint: migration 013j makes evidence review permanently non-overridable and binds decision-only canonical-owner exceptions to exact persisted authority, one immutable decision, completed idempotency, and the per-organization success-audit chain. The route is separately default-off and PostgreSQL-authoritative. See `docs/audits/2026-08-21-p0-owner-decision-override.md`.
- [x] Add 30-day transactional idempotency and an append-only per-organization audit hash chain.
  - Checkpoint: migration 013h makes PostgreSQL the database-clock authority for exact 2,592,000-second idempotency generations, immutable completion bindings, expired-only atomic rollover, and non-deletable identity anchors. Every enabled Assurance V2 mutation reaches the shared transactional UoW, and successful plus expected/domain-rejected outcomes bind to the per-organization audit chain. This is a minimum anti-reexecution window, not bounded data retention or production-runtime proof. See `docs/audits/2026-08-13-p0-idempotency-audit-integrity.md`.
- [x] Feature-disable automatic enforcement, untrusted external linking, workers, and unsupported modality packs at both API and UI boundaries.
  - Open gap: an evidence PATCH that omits URL fields skips the untrusted-URL gate on stored URL items; PR 336 closes it.
  - Checkpoint: automatic enforcement and FairMind-worker delivery are unconditionally unavailable for new legacy and Assurance V2 plans, and retired switches cannot re-enable them. New generic Evidence Hub external URLs and direct entity links are default-off at API and UI boundaries; the explicit reviewed-linking lane does not restore legacy Passport linking. Unsupported modern-bias, multimodal, and explainability evaluator surfaces are represented by inert dashboard availability states with no evaluator hooks, forms, fake results, exports, or endpoint requests; their dedicated routers are unmounted. The LLM judge stays available as a supporting signal and reports an insufficient result, never a default score, when a judge call fails. Assurance V2 target-kind vocabulary, including `vision_model`, is preserved.
- [x] Add forward migration 013 without rewriting migration 012; extend checksum-ledger drift detection.
- [x] Mark existing plans/runs contract v1 without fabricating registry identities; keep them readable but prevent new execution until upgraded.

Task 12B milestone: Passport v2 binding, trust authority, verified submission,
append-only review, operational freshness, and separately permissioned linking
are implemented as an internal, default-off PostgreSQL-authoritative
control-plane kernel. Submission authenticates and stores the evidence graph;
linking revalidates live authority and derives projections from the stored
canonical Passport. They do not imply generally available evaluator execution,
compliance, certification, automatic approval, worker execution, or runtime
enforcement. Canonical-owner and named exact-run delegated decision overrides
are implemented but default-off; production provisioning, enablement, and
rollout remain independent gates. Worker credentials, runtime execution, and
validated public execution routes remain P1 and release gates. Imported reports are inspection material only and
cannot enter formal evidence review or governance decision authority.

## P0 — Frontend and design

- [ ] Add one shared session provider above the dashboard shell and bind identity to `/auth/me`.
  - Re-scored 2026-11-08, partial: one SessionProvider in the (dashboard) layout wraps AuthGuard and AppShell and loads identity once from /api/v1/auth/me, with Playwright session-shell.spec.ts and session-state unit tests covering it. One leftover remains: compliance/runs/[runId]/page.tsx:39-42 still makes its own /auth/me call through useAuth().getCurrentUser instead of reading useSession(), so it is worth moving onto the shared session later.
- [x] Connect both logout controls; clear local tokens, authenticated caches, and cross-tab state even when revocation fails.
  - Re-scored 2026-11-08, done: The lifecycle shell now has one Sign out control, and it goes through the shared SessionContext logout. Logout clears tokens, the API and LLM-judge caches, org and PKCE state, and sibling tabs (BroadcastChannel, with a storage-event fallback) before revocation settles. Playwright specs cover failed and slow revocation. Caveats: the node:test unit files (session-state.test.ts, api-client.test.ts) are not wired into any package or CI script, and the unused legacy useAuth.logout still exists.
- [x] Self-host the profile portrait and eliminate authenticated third-party portrait requests.
  - Re-scored 2026-11-08, done: The third-party shadcn portrait was replaced with a self-hosted asset (0a1b75d5). The lifecycle shell now shows a local initials badge from the verified session (AppShell.tsx Me()), so the browser makes no third-party portrait requests. No test or CSP rule guards against a regression.
- [ ] Key state by organization/system/plan/run and mask prior-scope state synchronously during route changes.
  - Re-scored 2026-11-08, partial: evaluation-scope-state.ts keys state by org/workspace/system/plan/run and masks the previous scope in the same render on the tests, run-detail and assurance-run pages, covered by unit tests in CI (useEvaluationRuns.test.ts:360). The /systems/[id] system file (useSystemFile) and the compliance pack run pages still show the previous scope's data during route changes.
- [ ] Reject parsed responses whose scope differs from the request and remove `selected_org_id` as secondary path authority.
  - Re-scored 2026-11-08, partial: The API client no longer treats `selected_org_id` as request authority (5521aaf1, with api-client tests). Evaluation plan, run, workbench and catalog responses are rejected when their scope does not match the request (15b97fd7, with tests). Governance assurance and evidence hooks still accept parsed responses without checking scope.
- [x] Render execution status, evaluator evidence result, and governance verdict as separate axes.
  - Re-scored 2026-11-08, done: the V2 run detail page (`/assurance/evaluations/[runId]`, behind the assurance V2 run preview flags) shows Execution status, Evaluator evidence result, and Governance verdict as three separately labelled axes through `EvidenceTrustPanel`. Claimed or mixed-authority evaluator material is qualified and never shown as approval. `evidenceTrust.test.ts` (run in CI) and the flag-gated Playwright spec `assurance-v2-run-child-gate.spec.ts` cover this. Legacy runs have no evaluator-evidence field and keep technical status and verdict in separate cards.
- [x] Show signer, source, admission, freshness, review, expiry, limitations, and invalidation reason.
  - Re-scored 2026-11-08, done: The run detail page's EvidenceTrustPanel shows, for each suite, signer (key id and algorithm), source, admission state and reasons, freshness with evaluated and effective times, review state and reviewer, effective expiry, limitations, and invalidation reasons as bounded freshness reason codes. Fields the response does not return are shown as unavailable rather than inferred. Unit tests in evidenceTrust.test.ts and the env-gated Playwright check in assurance-v2-run-child-gate.spec.ts cover this.
- [x] Preserve layered suite/modality verdicts plus one overall reviewer verdict.
  - Re-scored 2026-11-08, done: V2 evaluation runs keep separate suite, modality, component and risk-dimension verdicts next to one overallVerdict, enforced in the backend contract and the database. The run detail EvidenceTrustPanel shows each layer separately and labels the run-level verdict as the single overall reviewer verdict once a decision version exists. Playwright and backend repository and Postgres tests cover this. The roadmap checkbox is still unticked.
- [ ] Update `DESIGN.md` with the three-axis model, admission states, capability truth table, worker security envelope, local identity/icon system, and binding model.
  - Re-scored 2026-11-08, partial: DESIGN.md on main documents five of the six parts: the three-axis model, the admission/review/freshness states, the capability truth table, the worker Execution Envelope, and the self-hosted framed identity and icon system. Two things are still missing: a binding-model section, and updating the identity/icon and token sections to the lifecycle-shell design.
- [ ] Preserve the white/black/orange/teal neobrutalist product language; no emoji, purple gradients, generic AI visuals, or dashboard rewrite.
  - Re-scored 2026-11-08, partial: main has moved the product UI onto the lifecycle-shell tokens (var(--fm-*)) and dropped almost all of the neobrutalist hard-shadow and black-border styling. Emoji remain in five UI files and gradients in llm-judge and model-inventory, DESIGN.md still describes the old style, and no automated guard enforces the rule.

## P1 — Isolated execution foundation

- [x] Add migration 013m for worker identities, leased jobs, suite attempts, artifacts, and cancellation.
  - Checkpoint: migration 013m extends the existing suite-execution job rather than creating a competing state machine, and adds tenant-bound worker identities, lease-token-hash-only attempts, content-addressed artifact metadata, exact attempt-artifact links, and run/suite cancellation requests. PostgreSQL 14 is release authority with a frozen operator ledger/catalog and controlled or append-only mutations; SQLite installs exact fail-closed parity objects but rejects worker writes. This schema foundation does not claim queue, heartbeat, completion, object-storage, broker, sandbox, or worker-route behavior. See `docs/audits/2026-08-30-p1-worker-execution-foundation.md`.
- [x] Implement a PostgreSQL `FOR UPDATE SKIP LOCKED` queue with 60-second leases, 20-second heartbeats, expiry recovery, and manifest-controlled retries capped at three.
  - Checkpoint: the application exposes only tenant/service-principal-bound claim and heartbeat operations over one PostgreSQL-authoritative adapter. Claim uses database time, bounded private expiry recovery, suite worker-type matching, and `FOR UPDATE SKIP LOCKED`; it creates exactly one attempt with a 60-second lease and persists only the SHA-256 of the 43-character opaque token. Heartbeat requires the same tenant, service subject, active worker identity, live attempt, and token, then renews the lease for 60 seconds and returns the 20-second heartbeat hint. Run materialization freezes `min(manifest maxAttempts or 1, 3)` onto each suite execution. SQLite fails closed. Concrete execution, completion, Passport verification, cancellation arbitration, and public worker routes remain later P1 rows. See `docs/audits/2026-08-30-p1-leased-worker-queue.md`.
- [ ] Implement `queued`, `leased`, `running`, `awaiting_evidence`, `succeeded`, `failed`, `timed_out`, and `cancelled` job states.
  - Re-scored 2026-11-08, partial: All eight job states and their legal transitions are enforced in PostgreSQL (migrations 013/013a/013m). The leased queue drives queued->leased and expiry to timed_out or back to queued. The running, succeeded, failed and cancelled transitions for worker jobs have no application operation or test yet; they are specified only in docs/superpowers/specs/2026-08-31-p1-worker-job-state-completion-design.md.
- [ ] Require the live lease token and matching signed Passport v2 for completion; cancellation wins races.
- [x] Add `WorkerCapabilities` and `EvaluationWorker.execute(ExecutionEnvelopeV2)` ports.
  - Checkpoint: the immutable `WorkerCapabilities` declaration exposes the worker
    type and supported execution depths and lifecycle phases. The declaration-only
    `EvaluationWorkerPort.execute` boundary now requires the domain's exact
    `ExecutionEnvelopeV2` object rather than an untyped JSON mapping and returns a
    frozen JSON result. No concrete executor, route, sandbox, credential handoff,
    or runtime validation is implied. A later integration must preserve the
    canonical builder output and envelope hash when constructing the typed input.
    See `docs/audits/2026-08-30-p1-typed-worker-execution-port.md`.
- [ ] Store artifacts by immutable SHA-256 in S3/MinIO-compatible storage; exclude credentials, secrets, and chain-of-thought.
  - Re-scored 2026-11-08, partial: Migration 013m adds a tenant-scoped, append-guarded artifact metadata ledger keyed by unique SHA-256 with quarantine states.
  - Re-scored 2026-11-08 (P1 S2), partial for inputs: migration 013n binds every row to the `fairmind-input-scan-v1` policy, fixes rejection reasons to stable codes, pins `storage_key` to `sha256/<digest>` and requires rows to enter quarantined. `src/infrastructure/storage/s3_artifact_store.py` writes once to S3 (conditional `IfNoneMatch`, SHA-256 checksum, PutObject and GetObject only), and `evaluation_artifact_service.py` scans CSV and JSON inputs (raw text plus decoded JSON members and CSV cells) for private keys, credentials and chain-of-thought markers before any write, then re-verifies and re-scans the stored bytes before promotion. The upload route sits behind `ASSURANCE_V2_ARTIFACT_UPLOAD_ENABLED` and `evaluation:artifact:upload`. Still open: output and result artifacts, the lease-bound input broker (S3), and a production bucket and IAM user, so this row stays open.
- [ ] Resolve opaque target/artifact bindings through short-lived brokers.
- [ ] Run evaluators non-root with read-only roots, ephemeral scratch, no host socket, dropped capabilities, restrictive syscalls, bounded resources, quarantined inputs, and deny-default network.
- [ ] Add scoped egress credentials, kill switches, and operational/security metrics.

## P2 — Real evaluation engines

- [ ] Build a validated predictive fairness pack covering parity, opportunity, odds, calibration, subgroups, robustness, drift, privacy, and intersections; fix bootstrap resampling and cross-check AIF360/Fairlearn.
  - Re-scored 2026-11-08, partial: the fairness run on main measures parity, disparate impact, equal opportunity, equalized odds and calibration per attribute, with a real row-resampling bootstrap, permutation p-values and baseline drift (PSI, rate drift), and tests cover them. Intersections, robustness, privacy and an AIF360/Fairlearn cross-check are still missing, and the library bootstrap helper is worked around rather than fixed.
- [ ] Add an Inspect adapter as the common LLM/agent harness.
- [ ] Add garak for LLM security and Promptfoo for CI/red-team/agent/multimodal scenarios.
- [ ] Add Giskard later as an external/imported adapter.
- [ ] Quarantine fixed, simulated, mislabeled, and fail-open legacy evaluators; retain only independently validated kernels.
  - Re-scored 2026-11-08, partial: Partial. PR #340 (ec79119f) unmounted the modern-bias and multimodal-bias routers and turned their pages into an inert notice, with 404 and main.py-source tests, and WEAT/SEAT moved to EV-FAI-05. The legacy /bias-detection and /advanced-bias-detection routers are still mounted, and they still return placeholder results from bias_testing_library and simulated image analysis.
- [ ] Never translate evaluator failure or unavailable input into passing evidence.
  - Re-scored 2026-11-08, partial: Partial. The Assurance V2/Passport path is fail-closed and tested: error, unavailable, insufficient_data and unknown map to failed/insufficient, and a missing executor returns 409. Legacy evaluators that are still mounted still fail open: India bias detection returns disparate impact 1.0 on error or missing data (india_bias_detection_service.py:849-869), and the bias testing library falls back to a p-value of 0.05.
- [ ] Treat LLM judges as calibrated supporting signals, never sole verdicts.
  - Re-scored 2026-11-08, partial: on main, a judge failure gives 'insufficient' and never 'passed', each run records the judge provider and model, and the leak and PII checks do not use the judge. But the behaviour suites still set pass or fail from the uncalibrated LLM judge's verdicts alone. Judge calibration and a rule that the judge never gives the sole verdict, with tests, are still to do.

## P3 — Modality packs

- [ ] LLM/text: injection, jailbreak, unsafe output, privacy, hallucination, bias, multilingual consistency, robustness.
  - Re-scored 2026-11-08, partial: live, tested behaviour engines cover LLM/text injection (EV-SEC-01/02), jailbreak (EV-SEC-03), unsafe output (EV-SEC-07, EV-OFF-06, EV-RSK-01), privacy (EV-PRV-01/04, EV-SEC-04), hallucination (EV-SEC-28, EV-TST-03), bias (EV-FAI-05) and robustness (EV-TST-04). Multilingual consistency only exists as an offline per-language accuracy gap (EV-TST-10, marked Partial), and these engines are not grouped into one LLM/text modality pack.
- [ ] Agents: indirect injection, tool/memory poisoning, permission misuse, excessive agency, exfiltration, irreversible actions, trajectory compliance.
  - Re-scored 2026-11-08, partial: Agent pack partial: indirect injection (EV-SEC-02, EV-SLF-01), tool poisoning (EV-SEC-17), memory poisoning (EV-SEC-21/20), permission misuse (EV-AGT-01/03, EV-SEC-18/19), excessive agency (EV-SEC-06, runaway) and exfiltration (EV-AGT-04, EV-SEC-27) have tested engines on main. Trajectory compliance and a behavioural irreversible-action test (EV-AGT-02) are still open.
- [ ] Code generation: compile/test, insecure code, dependencies, secrets, command injection, licenses, tool behavior.
- [ ] Vision input: OCR/typographic and low-visibility instructions, metadata carriers, hidden instructions, perturbations, transform survival.
- [ ] Image generation: unsafe content, demographic/stereotype bias, adherence, provenance, watermarking, transformation history.
- [ ] Audio: ASR-mediated and obfuscated instructions, transcoding survival, privacy, accent disparities, generated-voice misuse.
- [ ] Video: sparse-frame, subtitle/audio-track, temporal injection, unsafe content, representation, frame-sampling sensitivity.
- [ ] Multimodal: cross-modal conflict and attack transfer, retrieval/context contamination, tool effects, end-to-end transformation DAG.
- [ ] Map findings to versioned governance controls as candidate evidence; require reviewer acceptance and generate reproducible hash-bound audit packs without automatic compliance claims.
  - Re-scored 2026-11-08, partial: Partial. Evidence is mapped to versioned framework controls as candidate evidence, readiness counts only reviewer-accepted mappings, and both are tested. SHA-256 inspection packs with offline verification also exist and are tested. However, the packs are built from release gate and clause map data rather than from accepted control mappings, they are not reproducible by rebuilding (createdAt is in the hash), and the clause map marks clauses "proven" with no reviewer step.

## P4 — Pre, realtime pre/post, and post-deployment assurance

- [ ] Add `lifecyclePhase` to run creation; each run executes one selected phase.
  - Re-scored 2026-11-08, partial: Evaluation v2 run creation now requires one `lifecyclePhase`. It is checked against the plan and each suite, bound into the hash-checked envelope and evidence receipt, and stored with a DB CHECK constraint. Tests cover this. The legacy plan-runs route and the /tests UI still create runs without a phase.
- [ ] Support pre-deployment deep/CI/release-gate evaluation with verified current reviewed evidence.
  - Re-scored 2026-11-08, partial: Partial. V2 runs accept lifecyclePhase pre_deploy, executionDepth deep and the ci and release_gate triggers. V2 decisions require verified, current and reviewed evidence (governance_decision_service.py:196-205). The CI action and the CLI gate still read the older per-system release_gate, which does not check signatures, reviews or expiry. Deep execution waits on the P1 worker and P2 engine rows.
- [ ] Add synchronous realtime pre-input/tool-action evaluation for deterministic low-latency suites and queue deep checks under the same interaction ID.
- [ ] Add realtime post-output/tool/side-effect/media evaluation with an advisory result and evidence-pending state.
- [ ] Support scheduled post-deployment evaluation, drift, incident replay, provider changes, and evidence expiry.
  - Re-scored 2026-11-08, partial: evidence expiry is implemented and tested (013g freshness SQL plus evidence_freshness.py), and post_deploy and the scheduled and incident triggers are accepted as run metadata. There is still no post-deploy scheduler, drift-triggered evaluation, incident replay or provider-change detection.
- [ ] Implement hybrid inline deterministic plus asynchronous stochastic/human review.
  - Re-scored 2026-11-08, partial: 'hybrid' exists as an executionDepth value in the run schema, DB constraint, passport contract and suite preflight compatibility check, and reviewers can manually accept evidence. Nothing yet runs inline deterministic suites synchronously while queuing stochastic or human review under the same interaction.
- [ ] Keep enforcement advisory until accuracy, rollback, circuit-breaker, latency, and independent safety gates pass.

## P5 — Research, documentation, and product evidence

- [ ] EvalAttest: evidence-laundering corpus across bindings, signers, phase, and chronology.
  - Re-scored 2026-11-08, partial: origin/main has adversarial tests that reject binding, attribution, actor, signer-identity and chronology (capture, expiry) laundering in the 013i and trust-integrity suites. The EvalAttest corpus itself is not there: no labelled case set grouped by binding, signer, phase and chronology, no manifest and no results. Laundering across lifecycle phases is not covered.
- [ ] GateTrace: realtime detection, latency, utility, and asynchronous follow-up.
- [ ] X-Provenance: cross-modal transformations and causal-stage attribution.
- [ ] Publish immutable manifests, calibration reports, limitations, confidence intervals, and reproducibility guidance.
  - Re-scored 2026-11-08, partial: FairMind-E publishes a limitations doc and a reproducibility checklist with a tested evaluator and checked-in outputs. No research artifact has an immutable manifest, a calibration report or confidence intervals (thresholds are marked provisional), and the EvalAttest, GateTrace and X-Provenance corpora have no artifacts yet.
- [ ] Make the capability registry authoritative for product, docs, website, and sales claims.
  - Re-scored 2026-11-08, partial: DESIGN.md defines the capability truth table, and the docs app publishes a hand-maintained capability register (concepts/capability-truth.mdx). There is still no machine-readable registry that product, docs, website and sales all read from, and no test checks claims against it.
- [ ] Use “AI assurance control plane” until execution capabilities independently pass their gates.
  - Re-scored 2026-11-08, partial: the frontend app's metadata calls the product an "assurance control plane" (apps/frontend/src/app/layout.tsx:14,48), but the README and the website still say "agentic AI governance platform", and no test keeps the wording tied to the execution gates.
- [ ] After worker alpha, produce the product deck, audit examples, NotebookLM-style podcast, Remotion video, and HyperFrames video from validated screens and claims.
- [ ] Run whole-repository quality and organization audits at each release gate.
  - Re-scored 2026-11-08, partial: One report-only Ponytail whole-repository audit was recorded at the Task 12B release gate (docs/audits/2026-08-08-ponytail-whole-repository-audit.md). The organization audits date from March 2026. No release checklist step or CI job makes either audit recur at each gate, and the planned Ponytail re-run with measured reduction has not been done.

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
  - Re-scored 2026-11-08, partial: target and suite version catalogs, the evaluator catalog, suite-execution evidence admission and links, evidence review, and decisions guarded by expectedVerdictVersion (CAS) are live under /organizations/{org_id}/.../evaluation-v2, with route and service tests, and the review and decision routes are behind feature flags. Cancellation, worker-lease and realtime pre/post endpoints do not exist yet.

## Verification and rollout gates

- [ ] Mutate every envelope field independently; no mismatch may yield decision-grade evidence.
  - Re-scored 2026-11-08, partial: Tests show each envelope field changes the envelope hash, and each signed Passport V2 binding and evaluator field mutation is rejected at verified admission on PostgreSQL. A per-field matrix running from envelope through admission, link and decision is still missing, so the gate rests on the hash comparison and is not yet demonstrated end to end.
- [x] Test valid/tampered/unknown/revoked/expired/replayed/wrong-tenant/wrong-suite signatures and timestamp policy.
  - Re-scored 2026-11-08, done: tests cover valid, tampered, unknown, revoked, expired, replayed, wrong-tenant and wrong-suite signatures and the timestamp policy. They span the authenticity service, the trusted-authority resolver, the verified admission service and the 013b PostgreSQL guards (nonce replay uniqueness, trust-window, skew and max-age checks). These tests were not run for this review.
- [ ] Test cross-tenant isolation, 20-request idempotency/concurrency, link races, lost responses, cancellation, lease recovery, and audit-chain integrity.
  - Re-scored 2026-11-08, partial: PostgreSQL tests now cover cross-tenant isolation, 20-session idempotency and concurrency, two-session link races, idempotent replay of stored responses, and audit-chain tamper and gap detection. Lease recovery and end-to-end cancellation are still untested because worker leases and a cancellation endpoint don't exist yet.
- [ ] Fuzz canonical JSON and adversarially test sandbox/file/network/resource/media boundaries.
- [ ] Complete 1,000 adversarial sandbox jobs with zero escape, unauthorized egress, host access, secret exposure, or orphaning.
- [ ] Preserve the focused backend/frontend/browser/build/PostgreSQL/boundary baseline and add continuous CI security lanes.
  - Re-scored 2026-11-08, partial: CI on main keeps the focused baseline on every PR and push to main: backend pytest against PostgreSQL 14 including the boundary and isolation suites, frontend tsc and unit tests, and the Playwright browser lane with a production build. Continuous security covers supply chain only: Trivy fs scan (reports without failing), dependency review on PRs (fails on moderate), weekly Scorecard and Dependabot. Static analysis, secret scanning and Critical/High gating are still to do.
- [ ] Require zero unresolved or unaccepted Critical/High findings.
  - Re-scored 2026-11-08, partial: Partial. Dependency review blocks pull requests that add moderate-or-worse vulnerable dependencies, and Trivy uploads its scan results to the Security tab. But nothing fails a build or release on an unresolved Critical/High finding, and there is no record of accepted risks.
- [ ] Per public modality: freeze manifests; use at least 100 benign and 100 adversarial independently labelled cases across at least two target families; repeat stochastic cases three times; require kappa >= 0.70, macro-F1 >= 0.80, per-class recall >= 0.70, and benign false-positive rate <= 5%.
- [ ] Gate A private control-plane pilot: two organizations, 100 workflows, 14 days, zero isolation/integrity failures, automatic enforcement off.
- [ ] Gate B worker alpha: one real signed sandboxed suite end to end with failure injection and human approval only.
- [ ] Gate C modality beta: each exposed capability independently passes benchmark and sandbox gates with visible limits.
- [ ] Gate D public execution: GA adapter, reports, independent red team, 30-day soak, zero open integrity/isolation/Critical/High defect.
- [ ] Keep “FairMind Verified,” certification, automatic compliance, and automatic enforcement prohibited pending a separate independent safety program.
  - Re-scored 2026-11-08, partial: on the new assurance path, automatic enforcement is blocked in code and tests, docs and the website disclaim certification and 'FairMind Verified', and the governance UI tests ban certification wording. But the old compliance automation scheduler and endpoint still create 'Certificate of Compliance' PDFs with self-filled Pass and Compliant statuses, so the certification and automatic-compliance ban is not yet enforced.

## Defaults

- PostgreSQL is release authority; SQLite is a parity fixture.
- PostgreSQL leasing is the first worker queue; no Redis/Celery until capacity evidence requires it.
- FairMind owns orchestration, scope, trust, evidence, findings, review, and decisions; specialist engines execute tests.
- All three delivery paths and all three lifecycle phases remain supported.
- Layered results and one overall verdict are both required.
- Unsupported capability combinations fail preflight.

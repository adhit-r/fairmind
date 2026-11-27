# FairMind roadmap

Recalibrated on **24 November 2026** against [`main` at `dc2e730e`](https://github.com/adhit-r/fairmind/commit/dc2e730e1ef0650dfcf3cc1b5177d86b3ee8b961) and the live GitHub milestones. Merged changes, work verified in the dashboard branch, and remaining work have separate evidence below. The November 8 [feature audit](docs/FEATURE_STATUS.md) and [Assurance V2 scorecard](docs/STATUS.md#current-phase-2027-assurance-foundation) are dated snapshots. Milestone issue counts track the backlog.

FairMind helps teams register AI systems, gather and test evidence, and record human decisions. The roadmap prioritises the path from a failed check to its source evidence, a fix, a release decision and a versioned record.

## Merged product baseline

- The lifecycle dashboard covers inventory, candidate discovery, framework applicability, evaluations, findings, release decisions, and pushed monitoring snapshots. The system record retains the scope for review. [Product status](README.md#current-status)
- The catalogue contains **21 packs, 90 workflows and 109 evaluations**. There are 104 registered engines and five evaluators that read stored runs. Valid inputs and execution modes vary. Some checks score evidence produced by an external sandbox, drill or detector. Independent benchmarking and managed sandbox execution remain open. [Evaluation coverage](README.md#evaluations) · [Evaluation depth changes](https://github.com/adhit-r/fairmind/pull/552)
- The Reports hub has audience views at organisation and system scope, with sealed downloads. Inspection packs support read-only auditor links and offline verification. [Reports hub](https://github.com/adhit-r/fairmind/pull/550) · [Report correctness fixes](https://github.com/adhit-r/fairmind/pull/555) · [Evidence for auditors](README.md#works-today)
- Assurance V2 signed evidence, trust policies and decision routes remain an internal alpha behind default-off gates. Wider availability depends on the pilot, sandbox, and capability-specific verification. [Assurance release gates](docs/STATUS.md#assurance-v2-claim-boundary)

## Now · Q4 2026

| Order | Work | Completion evidence |
|---|---|---|
| **1. Release the verified dashboard and Reports work** | Integrate the dashboard UX changes and the one-system report workflow. The candidate release has local browser and database verification for the evidence handoff, Home and Discovery priority flows, the system review trail, report approval/export, saved setups, recurring preparation and assigned review. Rollout requires migrations 033–035. | In the target workspace, trace a failed check on a test system to its exact evidence and retest. Exercise one authorised, versioned report assignment through scheduled preparation, review, approval and export. Check owner and reviewer access on desktop and mobile, and show a clear missing-assignment state where applicable. |
| **2. Close account and organisation blockers** | Surface invitation delivery results, verify the enabled SSO callback, and consolidate old admin entry points into Settings. [#362](https://github.com/adhit-r/fairmind/issues/362) · [#368](https://github.com/adhit-r/fairmind/issues/368) · [#369](https://github.com/adhit-r/fairmind/issues/369) | A member can join from an invite, recover access, and reach the right organisation. An administrator can see a delivery failure and retry it without creating a second invitation. |
| **3. Make results and status reliable** | Replace obsolete evaluation preflight messaging. Reconcile estate monitoring with legacy endpoints, scope automation counts to one organisation, and remove remaining unsupported bias and compliance stubs. [#360](https://github.com/adhit-r/fairmind/issues/360) · [#361](https://github.com/adhit-r/fairmind/issues/361) · [#365](https://github.com/adhit-r/fairmind/issues/365) · [#366](https://github.com/adhit-r/fairmind/issues/366) · [#367](https://github.com/adhit-r/fairmind/issues/367) | Unavailable, empty, stale and failing states are distinguishable. Status shows the relevant tenant’s real records. Legacy links have a working destination or a specific unsupported-state explanation. |
| **4. Bring claims and routes into line with the product** | Reconcile public copy and setup docs, then remove verified-unused surfaces. Review the current security alert queue with an authorised maintainer. [#135](https://github.com/adhit-r/fairmind/issues/135) · [#152](https://github.com/adhit-r/fairmind/issues/152) · [#370–375](https://github.com/adhit-r/fairmind/milestone/7) | Published capability claims name their scope and inputs. Remaining routes have identified callers or a removal decision. Current security status comes from the alert queue rather than the original issue counts. |

### Q4 issue reconciliation

GitHub states below were read on 24 November. The assessment reflects merged code and the cited changes. Deployment acceptance remains a separate check.

| Issue | Assessment against `main` and remaining work |
|---|---|
| [#359](https://github.com/adhit-r/fairmind/issues/359) · Bias page | **Superseded.** The old address redirects to Evaluations, and the system file has the fairness run flow. Check old entry links and close the obsolete contract after verifying the replacement. [Redirect](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/frontend/next.config.js#L56-L59) |
| [#360](https://github.com/adhit-r/fairmind/issues/360) · Evaluation preparation | **Partial.** The system action reaches Evaluations. Legacy preflight still points users to an unavailable trusted-evidence workflow. [Preflight](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/application/services/evaluation_runs_service.py#L620) |
| [#361](https://github.com/adhit-r/fairmind/issues/361) · Monitoring | **Partial.** Estate Monitoring reads real system snapshots. Resolve or retire the legacy country-metrics stub and verify its callers. [Monitoring page](<https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/frontend/src/app/(dashboard)/monitoring/page.tsx#L58>) |
| [#362](https://github.com/adhit-r/fairmind/issues/362) · Invitations | **Partial.** Creation, acceptance and an email sender exist. Surface a send failure to the inviter and verify delivery and retry. [Invite dispatch](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/api/routers/org_management.py#L616-L633) |
| [#363](https://github.com/adhit-r/fairmind/issues/363) · Organisation settings | **Superseded.** The unsupported form was removed and its address redirects to Settings. Verify the supported organisation controls. [Redirect](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/frontend/next.config.js#L53) |
| [#364](https://github.com/adhit-r/fairmind/issues/364) · Password and preferences | **Superseded in scope.** Preferences persist and sign-in offers password reset. The misleading password form was removed. Decide separately whether a signed-in reset shortcut is needed. [Settings service](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/application/services/settings_service.py#L29-L57) |
| [#365](https://github.com/adhit-r/fairmind/issues/365) · Fabricated compliance results | **Partial.** Certificate generation uses recorded evidence. Compliance status still counts scheduler jobs across the process. Scope that count and verify the remaining empty and failed states. [Job count](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/domain/compliance/services/compliance_automation_service.py#L319) |
| [#366](https://github.com/adhit-r/fairmind/issues/366) · Bias stubs | **Partial.** Unsupported image and text routes return 501. Review the legacy template stubs and consumers. [Bias router](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/api/routers/bias_detection.py#L341-L362) |
| [#367](https://github.com/adhit-r/fairmind/issues/367) · Legacy monitoring and alerts | **Partial.** Durable metrics and alerts exist. Reconcile the separate health and streaming interfaces with supported snapshot monitoring. [Monitoring router](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/api/routers/monitoring.py#L395) |
| [#368](https://github.com/adhit-r/fairmind/issues/368) · Organisation admin | **Partial.** Team and Audit log are in Settings. Migrate or redirect the remaining duplicate admin routes. |
| [#369](https://github.com/adhit-r/fairmind/issues/369) · Auth links | **Partial.** The approval email points to sign-in. Verify and correct the enabled SSO callback. [SSO configuration](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/frontend/src/lib/api/hooks/useAuthentik.ts#L91) |
| [#370](https://github.com/adhit-r/fairmind/issues/370) · Website claims | **Partial.** The timeline shipped. Feature and comparison claims still need review against reachable workflows and evidence modes. [Timeline PR](https://github.com/adhit-r/fairmind/pull/553) |
| [#371](https://github.com/adhit-r/fairmind/issues/371) · Docs and OpenAPI | **Partial.** Several docs changed. Reconcile the remaining setup, route, and realtime claims with the supported contract. [Setup instructions](CONTRIBUTING.md) |
| [#372](https://github.com/adhit-r/fairmind/issues/372) · Legacy pages | **Partial.** Many older tool URLs redirect and the legacy navigation constant is gone. Check remaining standalone views and bookmarks. [Redirects](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/frontend/next.config.js#L38-L59) |
| [#373](https://github.com/adhit-r/fairmind/issues/373) · Frontend dead code | **Merged and closed.** [Cleanup PR](https://github.com/adhit-r/fairmind/pull/399) |
| [#374](https://github.com/adhit-r/fairmind/issues/374) · Unused backend modules | **Open.** Check dependencies before removing the named routers, services and middleware. |
| [#375](https://github.com/adhit-r/fairmind/issues/375) · Mounted routes | **Open.** Older compliance, dataset and provenance routes remain mounted. Identify consumers and choose canonical routes. [Mounted routes](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/api/main.py#L671-L693) |
| [#152](https://github.com/adhit-r/fairmind/issues/152) · Frontend reliability | **Open.** Finish API-base consolidation, route-level error boundaries and noisy logging fixes. |
| [#135](https://github.com/adhit-r/fairmind/issues/135) · Security alerts | **Unverified.** The current alert list requires repository security access. Use the live queue to confirm outstanding findings. |

## Next · Q1 2027

| Workstream | Remaining scope and completion evidence |
|---|---|
| **Audit reporting and auditor handoff** | Confirm the organisation audit export’s required dataset and CSV/PDF/JSON contract in [#381](https://github.com/adhit-r/fairmind/issues/381). Existing audience snapshots and the local one-system report cover different scopes. Build from the approved-version contract. Validate explicit auditor-pack scope, expiry and revocation. For recurring delivery, record preparation, approval and each recipient outcome separately and retry failures without changing the approved artifact. |
| **Legacy compliance automation** | Scheduling and Run now have handlers. Finish truthful dispatch and violations, persisted report history and tenant-scoped status. The history endpoint still returns 501. Keep the legacy certificate job distinct from System Assurance Report preparation. [#382](https://github.com/adhit-r/fairmind/issues/382) · [History endpoint](https://github.com/adhit-r/fairmind/blob/dc2e730e/apps/backend/src/api/routers/compliance_automation.py#L612-L615) |
| **Requirements and evidence** | Prove requirement → named check → accepted evidence in one system context. Evidence Passport intake remains open alongside existing inspection-pack exports. Define the app path for India checks and the scope of DPDP/GDPR catalogue additions. [#378](https://github.com/adhit-r/fairmind/issues/378) · [#379](https://github.com/adhit-r/fairmind/issues/379) |
| **System lifecycle and decisions** | Finish environmental approval from the existing assessment history. Material edits and signed retirement exist. Recheck workspace reuse and lifecycle permissions. Define the remaining approval editor and workflow version history around existing decisions and version APIs. [#376](https://github.com/adhit-r/fairmind/issues/376) · [#380](https://github.com/adhit-r/fairmind/issues/380) · [#383](https://github.com/adhit-r/fairmind/issues/383) · [#388](https://github.com/adhit-r/fairmind/issues/388) |
| **Evaluation and risk quality** | Finish the LLM judge’s reachable workflow, comparison and evidence handoff. Validate supported evaluator modes with benchmarks. Expand guided risk assessment only where the taxonomy and scoring are defined. [#377](https://github.com/adhit-r/fairmind/issues/377) · [#149](https://github.com/adhit-r/fairmind/issues/149) |
| **Assurance V2 pilot** | Complete the default-off workbench and evaluator/trust administration around existing backend contracts. A private pilot must exercise exact scope, permission boundaries, evidence admission, reviewer decisions and failure recovery before rollout. [#385](https://github.com/adhit-r/fairmind/issues/385) · [#386](https://github.com/adhit-r/fairmind/issues/386) · [Gate A](docs/STATUS.md#current-phase-2027-assurance-foundation) |
| **Product quality gates** | Complete representative keyboard and accessibility checks, establish a measured bundle budget, and cover the main journeys and failure states in CI. [#103](https://github.com/adhit-r/fairmind/issues/103) · [#101](https://github.com/adhit-r/fairmind/issues/101) · [#154](https://github.com/adhit-r/fairmind/issues/154) |

Three open Q1 tickets have superseding implementation to accept and reconcile with the tracker. The access-request form and API-key controls exist ([#384](https://github.com/adhit-r/fairmind/issues/384)). The system file shows policy failures in the release workflow and blocking policies can force `no_go` ([#387](https://github.com/adhit-r/fairmind/issues/387)). All 109 catalogue checks now have a registered engine or stored-run evaluator ([#389](https://github.com/adhit-r/fairmind/issues/389) · [evaluation changes](https://github.com/adhit-r/fairmind/pull/552)). Each still needs confirmation against its original acceptance scope before tracker closure.

## Later · Dependency-based

- **Isolated workers and sandbox.** Prove worker identity, execution isolation, leases, recovery and measured evaluator integrity before enabling managed execution. [#390](https://github.com/adhit-r/fairmind/issues/390) · [Assurance gates](docs/STATUS.md#current-phase-2027-assurance-foundation)
- **Automatic workflow starts.** Add trigger identity, idempotent runs and observability around workflow starts. Report preparation has its own schedule and human review path. [#391](https://github.com/adhit-r/fairmind/issues/391)
- **Ask and explained decisions.** Live decision explanations have merged. Complete the remaining measured checks and extend system and finding questions with source citation and access checks. [#392](https://github.com/adhit-r/fairmind/issues/392) · [PR #547](https://github.com/adhit-r/fairmind/pull/547)
- **Scoped follow-ons.** Define the maintained ML pipeline scope after the old DVC configuration’s removal. Start internationalisation after the priority workflows stabilise and evaluate an optional content-safety evaluator. [#393](https://github.com/adhit-r/fairmind/issues/393) · [#104](https://github.com/adhit-r/fairmind/issues/104) · [#143](https://github.com/adhit-r/fairmind/issues/143)

The numeric distribution robustness item was merged and closed. [#147](https://github.com/adhit-r/fairmind/issues/147) · [PR #408](https://github.com/adhit-r/fairmind/pull/408)

### GitHub issue snapshot

Counts include issues only. Open issues can contain work already merged or superseded. The evidence above determines what remains.

| Milestone | Open | Closed |
|---|---:|---:|
| [Q4 2026 · Close gaps](https://github.com/adhit-r/fairmind/milestone/7) | 18 | 1 |
| [Q1 2027](https://github.com/adhit-r/fairmind/milestone/8) | 18 | 0 |
| [Later](https://github.com/adhit-r/fairmind/milestone/9) | 6 | 1 |

### Research backlog

Causal DAGs, bias propagation across agents, regulatory change ingestion, fairness/performance trade-offs, SEBI disclosure mapping, FRIA/DPIA generation, multi-jurisdiction simulation, model bias lineage, privacy-preserving and federated auditing, bounds under missing demographics, synthetic-data fairness and community red teaming remain research topics. Propose a scope and evaluation method in [Discussions](https://github.com/adhit-r/fairmind/discussions) before assigning a delivery milestone.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and [good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) for bounded contributions.

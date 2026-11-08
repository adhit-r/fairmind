# FairMind Roadmap

> Last updated: November 2026. Checked against the code on `main`. For what works today, see [docs/FEATURE_STATUS.md](docs/FEATURE_STATUS.md), the [README status section](README.md#current-status) and [docs/STATUS.md](docs/STATUS.md).

FairMind is open-source agentic AI governance: agents draft the governance work, FairMind runs the evaluations, and a person decides at every gate. This roadmap lists only what has been verified in the code as shipped, and puts everything else in Now, Next or Later with a linked issue.

---

## Shipped

Verified end to end on `main`.

- **AI system inventory**: register a system, or discover it from MLflow, GitHub or the Hugging Face Hub and promote it from a review queue. Each system has one page that walks it through Onboard, Assess, Govern, Remediate and Operate.
- **Applicability**: suggested frameworks per system, with confirm and override.
- **Packs and workflows**: 21 packs and 90 workflows. Install packs, start runs, record step outputs, decide at gates, and draft and publish your own workflow version.
- **Agent step drafting**: the agent drafts a work step on request, using the organization's own model or built-in rules. It writes to the ledger only.
- **Evaluations**: 61 of the 109 catalogue evaluations produce a result inside FairMind, on uploaded files, against a live system, or on agent platform configuration.
- **Fairness runs and release gate**: disparate impact, demographic parity, equal opportunity, equalized odds and calibration, each with a bootstrap interval and a permutation p-value. The gate returns `go`, `conditional_go` or `no_go`, with seals, a clause map and attestations.
- **Policies** mapped to framework controls and evaluated live.
- **Evidence for auditors**: evidence hub, evidence-to-control mapping with four-eyes review, inspection packs, a read-only auditor link, and offline verification with `fairmind verify`.
- **Assurance report studio** on `/reports`.
- **Monitoring snapshots**: pushed from the CLI or SDK, with cadence tracking, stale-snapshot flags and drift findings.
- **Remediation task tracker** on `/remediation`.
- **CI and agent surfaces**: CLI, GitHub Action, Python SDK and MCP server.
- **Accounts**: sign-up, sign-in, password reset, organization switcher, member list and removal.
- **Assurance V2 signed-evidence control plane**: built and tested, off by default, internal alpha only (see [docs/STATUS.md](docs/STATUS.md)).

Removed from this list because the code does not support them: multimodal bias detection, AI BOM, explainability studio, remediation wizard with code generation, real-time WebSocket monitoring, a model marketplace, Comet, DeepEval, Arize Phoenix and AWS Clarify integrations, GDPR and DPDP as catalogue frameworks, and automated compliance reports with email distribution. Each one is either tracked below or listed as unscoped.

---

## Now: Q4 2026 (close gaps)

Milestone: **Q4 2026 - Close gaps**. Fix the user-facing breakage on reachable pages first, then remove what misleads.

### Broken or misleading on reachable pages (p0)

- Wire the Bias Detection page `/bias` to a real fairness endpoint, and fix its links to `/models` and `/datasets`. #359
- Stop the Evaluation Runs page `/tests` from promising run preparation it cannot do. #360
- Replace the `/monitoring` placeholder with the system's real monitoring snapshots, and delete the placeholder routes that hide the honest 501. #361
- Fix the invitation accept flow and send invitation emails. #362
- Build the organization settings API, or remove the org-info form. #363
- Make Settings "Update Password" change the password, and persist user preferences. #364

### Trust and correctness (p1)

- Remove fabricated compliance results: hardcoded Pass rows in certificates, the sample stakeholder dashboard, and the placeholder gap-remediation plan. #365
- Remove the placeholder 0.0 bias scores and no-op stubs from the bias-detection router. #366
- Decide the fate of the in-memory per-model monitoring API, alerts and WebSocket. #367
- Organization admin: fix the broken calls, add it to the sidebar, and remove the `/admin` duplicates. #368
- Fix the SSO callback path and the access-approved email link. #369
- Bring the website roadmap, features and comparison pages in line with the code. #370
- Correct the repository docs, the docs site and the OpenAPI text. #371
- Close the remaining OpenSSF Scorecard findings. #135

### Cleanup (p2)

- Remove orphan legacy frontend pages and the unused `navigation.ts`. #372
- Remove dead API endpoint keys, hooks and service modules in the frontend. #373
- Delete unmounted routers, unimported services and unused middleware in the backend. #374
- Remove or consolidate mounted backend routes that nothing calls. #375
- Frontend code quality: one API base, a route-level error boundary, and fewer `any` and `console.error` calls. #152

---

## Next: Q1 2027

Milestone: **Q1 2027**. Give working backend features a frontend, and finish the half-built ones.

- Environmental assessment and approval flow on the system page. #376
- LLM judge: use the organization's own model key, add it to the navigation, add judge comparison, and save results as evidence. #377
- India compliance: expose the DPDP, NITI Aayog and RBI checks, and add DPDP and GDPR to the framework catalogue. #378
- Evidence Passport upload and inspection-pack export from the UI, SDK and CLI. #379
- Edit, re-tier and archive an AI system; reuse workspaces. #380
- Org audit-report export from `/reports`. #381
- Wire the compliance automation page: schedules, Run now, violations, and persisted reports. #382
- Approval workflow editor and decision history. #383
- Access-request form and API key management. #384
- Assurance V2 evaluation workbench UI, behind its existing flags. #385
- Assurance V2 admin UI: evaluator catalog and trust administration. #386
- Show the policy gate next to the release gate on the system page. #387
- Workflow version history on the workflow page. #388
- Build engines for the catalogue evaluations marked Partial. #389
- Risk taxonomy API and the `/risks` page extension (IBM, MIT and OECD taxonomies). #149
- Accessibility audit and keyboard navigation on the lifecycle-shell pages. #103
- Bundle size baseline and budgets. #101
- Dashboard end-to-end test hardening. #154

---

## Later: 2027 and beyond

Milestone: **Later**. Scoped, but after the gaps above are closed.

- Sandboxed evaluation workers (Assurance Gate B). #390
- Automatic workflow starts from schedules and triggers. #391
- Ask about any system or finding, and measured VerdictExplainer checks (both labelled Coming soon today). #392
- Decide the scope of `apps/ml` and fix or archive `dvc.yaml`. #393
- Make the numeric distribution plot robust to bad input. #147
- Internationalization, phase 1 (next-intl, nav shell and one page). #104
- Optional ShieldGemma content-safety evaluator. #143

### Unscoped research ideas

These ideas carried over from the earlier roadmap have no issue yet. Propose them in [Discussions](https://github.com/adhit-r/fairmind/discussions) with a scope before they get a milestone: a causal DAG builder, bias propagation across agent chains, ingesting regulatory changes, a fairness-performance Pareto explorer, SEBI disclosure mapping, FRIA and DPIA generation, a multi-jurisdiction what-if simulator, bias lineage across model components, privacy-preserving fairness auditing, fairness bounds under missing demographics, synthetic-data fairness, federated fairness, and a community red-team module.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup. The [good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are a good place to start.

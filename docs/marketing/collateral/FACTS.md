# FairMind marketing facts (single source for all collateral)

Every claim in a poster, banner, sheet or video must come from this file. If it is not here, leave it out.
Sources: `apps/docs/content/docs/index.mdx`, `apps/docs/content/docs/get-started/status-and-limits.mdx`,
`apps/backend/src/api/routers/pack_catalogue_data/catalogue.json` (counted 2026-11-15), the demo tour recordings.

## Identity
- Name: FairMind. Mark: `apps/website/public/logo-mark.svg`.
- One line: An open-source AI assurance workbench for models and agents.
- Longer: It turns governance frameworks into controls, collects evaluation evidence, and gates releases. It keeps an AI system, its tests, evidence, risks, remediation and approvals in one reviewable record.
- The question it answers for a release: May this system ship, and what is the evidence?
- The rule: An evaluation result is evidence for a decision, never the decision itself. A person decides.
- Separation: a pending release request is decided by someone other than the person who asked.
- Licence: AGPL-3.0. Code: github.com/adhit-r/fairmind
- Status: Alpha, November 2026. The main path works end to end. (Always show "Alpha" on sheets.)
- Links: fairmind.xyz (site), app.fairmind.xyz (app; "Try the demo" on the login page is a read-only demo with public data), docs.fairmind.xyz (docs).

## Numbers you may use (catalogue counts)
- 109 evaluations in the catalogue, in 4 pillars: Govern, Evaluate, Secure, Comply.
- In the demo app header: "109 evaluations. 104 can run today." (use this pairing when showing the app)
- 51 frameworks, standards and risk lists. 539 requirements. 922 crosswalk links. 29 common controls.
- 90 catalogue workflows (86 marked proposed until organisations run them). 21 packs. 8 bundles.
- Agent steps can use your own model: 19 providers, key encrypted at rest, or built-in rules.
- Release gate: five checks give go, conditional_go or no_go. Failing blocking policy rules force no_go. Approval is refused while critical findings are open.

## Frameworks to name (lead set)
EU AI Act, ISO/IEC 42001, NIST AI RMF, RBI FREE-AI. Also with guides: OWASP LLM Top 10, OWASP Agentic Top 10, OWASP MCP Top 10, MITRE ATLAS, AIUC-1, NIST AI 600-1, ISO/IEC 42005, CSA MAESTRO. Catalogue evaluations map to AIUC-1 requirements.

## What works today (the lifecycle)
- Onboard: register a system, or discover it from MLflow, GitHub or the Hugging Face Hub and promote it from a review queue.
- Assess: evaluations run on uploaded files, as behaviour tests against your live system, as configuration audits of your agent platform, or on results from your own sandbox, drills and detectors. Results are stored as measured evidence.
- Govern: policies mapped to framework controls, evaluated live, counted as evidence. Evidence shows where it came from and how much it counts.
- Remediate: findings, owners, retests.
- Operate: you push monitoring snapshots on your schedule (e.g. `fairmind monitor` in cron); stale snapshots are flagged and sustained drift opens a finding.
- Auditors: the gate per framework clause, inspection packs, a read-only auditor link, offline verification with `fairmind verify`.
- Build: CLI, GitHub Action (`fairmind gate` in CI), Python SDK, MCP server, all with an API key.
- Bring your own evaluator: an Evidence Passport carries subject, evaluator and metric versions, threshold, artifact digest, result and limitations, and enters the same review, mapping and gate.
- Tamper-evident: hash-chained run ledger; chain state shown on the run page.

## What FairMind is not (say this plainly on the spec sheet)
- Not a certification: no compliance certificate, automatic approval or "verified" badge.
- Not a runtime guardrail: it assesses systems; it does not sit in the request path.
- Not a sandbox: engines run inside the backend; uploaded model files are inspected, never executed.
- A person starts every workflow run (no automatic starts yet).
- 21 agent, attack and detector evaluations judge a results file you produce in your own sandbox; FairMind computes the metric but does not run the scenario.

## Comparison (from fairmind.xyz/comparison, generalised by category, never name competitors)
Headline: Evaluators test. GRC suites file. FairMind decides, with people.
| Need | Evaluation tools | GRC suites | FairMind |
|---|---|---|---|
| Run a fairness or safety test | Yes, deeply | No | 109 catalogue evaluations; or bring results as an Evidence Passport |
| Map evidence to framework requirements | No | Yes, by questionnaire | Yes: 51 frameworks, standards and risk lists, 922 crosswalk links, human-accepted mappings |
| Human approval before anything changes | Not in scope | Sign-off on documents | A gate step in workflows; decided by someone other than the requester |
| Tamper-evident record | Logs | Audit log | Hash-chained run ledger, chain state on the run page |
| A verdict your pipeline can read | Thresholds in code | No | `fairmind gate` in the CLI and GitHub Actions: go, conditional_go, no_go |
| Govern agents, tools and MCP servers | Some red-teaming | Rarely | OWASP Agentic and MCP Top 10, AIUC-1 coverage |
| Certification | No | No | No. Readiness and evidence only |
Footnote always: "Generalised across categories. Your tools may differ."

## Banned
- Emoji, gamification (badges, stamps, scores-as-rewards), invented numbers, customer logos, testimonials, "compliant", "certified", "approves releases", "FairMind evaluates models" (unqualified), "trusted by", "enterprise-grade", "leading", any competitor name.

# FairMind product audit: does it fully serve its purpose?

Date: 2026-11-12. Branch audited: `task/ga-small-fixes` (Astryx shell merged).

Evidence base:
- A live walk of the local app (port 1111 against the local Postgres copy), signed in as the e2e admin.
- Code reads of `apps/frontend` and `apps/backend`. Two read-only audits; claims cited with file:line where it matters.
- The pack catalogue (`pack_catalogue_data/catalogue.json`).
- Web research on competitors and regulation. Vendor details come mostly from secondary sources; where something is unverified it is marked.

---

## 0. What FairMind exists to do

FairMind's stated purpose is agentic AI governance: "agents prepare, people decide". Its sources are `docs/product/SYSTEM_JOURNEY.md`, the website positioning and the catalogue.

| Job type | The job users hire FairMind for |
|---|---|
| Functional (core) | When I am accountable for the AI my organisation runs, help me (1) **know every AI system that exists**, (2) **know what each one needs** under the rules that apply, (3) **get the proof produced** with as little manual work as possible, (4) **make a release decision I can defend**, (5) **keep that decision true after release**, and (6) **hand an auditor proof they can verify** without a scramble. |
| Emotional | "I will not be blindsided by an AI system I did not know about, or by an audit I cannot answer." |
| Social | Be seen by the board, regulators and customers as an organisation that is in control of its AI, for example as ISO 42001 or EU AI Act ready. |
| Secondary: ML engineer | "Get my model through the gate inside my normal workflow (CI), without a bureaucratic detour." |
| Secondary: reviewer | "Tell me when a decision needs me, show me what is proven and what is only claimed, and let me decide in one place." |
| Secondary: auditor | "Let me verify the record independently, in a format I recognise." |

---

## 1. Purpose and JTBD verdict

**FairMind delivers about half of the job, and it does that half better than most of the market.** Its core (the release gate, measured-versus-attested evidence classes, hash-chained decision seals, and auditor packs that can be verified offline) is real, distinctive and correct. The jobs either side of that core are thin or not real, and the positioning ("agentic") claims more than the product does.

| Job step | Delivered? | Evidence |
|---|---|---|
| 1. Know every AI system | **Partly (weak)** | Discovery reads only MLflow, GitHub and Hugging Face (`integrations.py:337`). There are no Bedrock, SageMaker, Azure AI Foundry, Vertex, Databricks or OpenAI-org connectors, and no SaaS or shadow-AI detection. There is no agent inventory: agents are not a first-class kind. There is no CSV import. The only manual form, `/onboard`, cannot be reached from the navigation or from `/systems`. |
| 2. Know what each needs | **Mostly** | There are 51 frameworks, 539 requirements and a hand-authored crosswalk of 922 rows. Applicability tiering and the org plan (`/api/v1/plan`) work. The plan is org-level, and its link to a single system's gate path is unclear. |
| 3. Get proof produced | **Partly** | There are 79 engines. 22 probe a live system; about 57 compute from uploaded files. About 30 of the 109 catalogue evaluations have no engine. Workflows mostly record states that a person advances. Only `trigger`, `escalate` and `file` steps run themselves, and `escalate` sends nothing (`packs.py:967`, `notificationSent: False`). The agent drafts a step only when someone clicks, needs a BYO-key LLM, and makes no tool calls and runs no evaluations. 86 of 90 workflows are "Proposed". |
| 4. Defensible decision | **Yes (strong)** | The gate has five checks, confidence and `path_forward`. The decision endpoint refuses approval with a 409 while a critical item is open. A conditional go requires written conditions. SHA-256 seals are created at `ai_governance.py:1911`. |
| 5. Keep it true after release | **Weak** | Monitoring is an hourly in-process loop that pulls a snapshot from an https data URL (`main.py:49-73`, `autopilot.py:258`). There is no production telemetry intake, no incident register and no EU AI Act Art. 73 serious-incident flow. Staleness does lower the gate, which is good. |
| 6. Hand auditors proof | **Yes (strong), with a format gap** | The pack is a JSON manifest with a hash, a 30-day share link, a public `/verify/[packId]` page and `fairmind verify` offline. Missing are human-readable, regulator-shaped documents: EU AI Act Annex IV technical documentation, a FRIA, an ISO 42001 Statement of Applicability, EU-database registration fields. PDF and DOCX reports exist only on the legacy `/reports` page. |
| Secondary: engineer in CI | **Built but invisible** | `.github/actions/fairmind-gate` fails a job unless the gate is green. Nothing in the app tells anyone it exists, apart from the API-keys section in Settings. |
| Secondary: reviewer notified | **No** | Release approval requests notify nobody. The only approval email is for access requests (`registration.py:238`). A reviewer has to happen to open Needs you. |

**Gaps between the stated purpose and the actual job:**
1. "Agentic" is the headline, but agents draft only on demand and never act; the workflow engine is a human checklist with a ledger. The real differentiator is **proof-grade release decisions**, and the positioning undersells it.
2. The home page promises "Find unregistered AI". For most enterprises their AI lives in Azure OpenAI, Bedrock, Copilot Studio and SaaS tools, none of which FairMind can see.
3. Environmental impact is one of only five release-gate checks. No regulation gates a release on energy use, so a user will not connect "assess energy" with "can I ship" (see walkthrough J2).

---

## 2. Feature suitability

| Feature | Verdict | Rationale tied to the job |
|---|---|---|
| Release gate, confidence, path forward | **Keep** | This is the core of job 4 and is unique: it weights measured, tool-estimated and attested evidence separately. Make it the product's name for itself. |
| Decision seals, auditor packs, `/verify`, CLI `verify` | **Keep** | This is the moat for job 6; incumbents are thin here. Add a human-readable report inside the pack. |
| GitHub Action gate, SDK, CLI, MCP server | **Keep, make visible** | This serves the engineer's job. It needs an in-app "Add the gate to CI" page with a generated snippet. |
| Home live board (systems by checks) | **Keep, improve** | The right picture. Its empty state must become a guided first-run, not a link to Discovery alone. |
| Needs you (single inbox) | **Keep as the one decision surface** | Release approval is decided in four places today (`/decisions`, `/needs-you`, the system-file Decide panel, legacy `systemApproval`). Keep decisions here; turn `/decisions` into a read-only register. |
| AI systems board and Discovery | **Rebuild (breadth)** | Job 1 fails for most buyers. Add cloud and agent-registry connectors, CSV import and in-shell manual registration. |
| Org governance plan (`/plan`) | **Improve** | The LLM questionnaire is useful. It renders a blank main area for a user with no organisation (seen live). Its tasks should flow into each system's "What it needs". |
| Frameworks | **Keep, consolidate** | Six surfaces exist (`/frameworks`, `/frameworks/[key]`, `/compliance`, `/compliance/journeys/[key]`, `/compliance-dashboard`, the system Requirements tab). Keep two: the framework page and the system Requirements tab. |
| Policies (LLM draft, enforce, acknowledge) | **Keep** | Supports job 2. Drafting is blocked without a provider; say so before the user clicks. |
| Evaluations catalogue | **Rebuild** | It is read-only. "Open to run" leaves the Astryx shell for the legacy `/compliance/evaluations/[id]`. Make it runnable in place, recommend evaluations per system, and hide "Not built yet" items by default. |
| Workflows and runs | **Rebuild or re-label** | Either make steps execute (run evaluations, call tools, send escalations, all written to the ledger), or present them honestly as guided checklists. Showing 86 "Proposed" workflows as product capability is not acceptable. |
| Agent audits | **Improve** | Supports only Claude Managed Agents. Add generic MCP and agent-config upload, plus AgentCore, Foundry and Agent 365, OpenAI Agents and Copilot Studio. |
| Monitoring | **Rebuild** | Snapshot pulls do not constitute operating oversight. Add a push API (OpenTelemetry GenAI conventions), an incident register and Art. 73 timers. |
| Findings and remediation with retest | **Keep** | Closes the loop between a failed check and a decision. |
| Environment (FairMind-E) | **Keep, demote** | It is a research asset and has a CSRD export. Make it a policy-optional gate check, off by default. It is not a headline feature. |
| Autopilot (Off, Ask first, Run) | **Improve** | It is gated on an https data-source URL that few systems will have; explain this in the selector. |
| Ask FairMind | **Keep** | Useful once a provider is set. |
| Settings | **Improve** | The organisation section cannot be edited. There is no notification destination, no residency setting, and the audit log fails with a generic error. |
| Legacy bias tools (`/bias`, `/advanced-bias`, `/llm-judge`, `/llm-testing`, `/tests`) | **Cut** | These are the retired "bias tool" product and dilute the governance job. |
| Stubs (`/benchmarks`, `/explainability-studio`, `/multimodal-bias`, `/fairness-documentation`, `/ai-bom`, `/provenance`) | **Cut** | They are ComingSoon pages or 501s. |
| Legacy `/compliance` tree, `/compliance-dashboard`, `/compliance-automation`, `/reports` | **Cut after porting** | First port the run page and the report builder into the shell. |
| Placeholder endpoints | **Cut** | `/reports` returns `[]`. `/monitoring-metrics` returns a fixed "healthy". The gap plan returns a "Placeholder gap description" (`compliance_automation.py:~600`). `/evidence/manual` stores nothing. `compliance_reporting.py` lists EU AI Act as "Proposed". These break the repo's own no-mock-data rule. |

---

## 3. Critical gaps and anti-patterns

**Blocks the job:**
1. **First run is broken for a user without an organisation (seen live).** Every page says "Select an organisation to see its packs." on Home, AI systems and Evaluations. There is no organisation selector, "Try again" cannot fix the problem, and `/plan` renders an empty main area. The copy names "packs" on pages that have nothing to do with packs (`usePacks.ts:353`).
2. **Your first system cannot get in.** The home empty state says "Register a system, or connect a source", but its only button goes to Discovery. Discovery covers three sources. The manual form `/onboard` is reachable only from legacy pages or an empty state on Evidence, and it lands on another legacy page (`/systems/[id]/plan`, which has a disabled "Coming soon" save).
3. **Decisions wait on someone who is never told.** Release requests send no email, Slack or Teams message and create no ticket. The `escalate` step is recorded as done but sent nothing, so the product states something about itself that is not true.
4. **The journey leaves the product mid-task.** The system file links to `/tests`, `/compliance`, `/compliance/runs` and `/audit-reports`. These are legacy pages in a different visual frame (`fm-legacy`) with a different navigation model. More than 40 legacy routes are still live.

**Anti-patterns and AI slop:**
- **Catalogue as feature list.** The 109 evaluations, 90 workflows and 51 frameworks are presented as capability, but about 30 evaluations have no engine and 86 workflows are "Proposed". Breadth is shown without saying what is real; this is the biggest credibility risk in an audit-facing product.
- **Stale identity.** The browser tab reads "FairMind - Build Fair & Trustworthy AI" (`app/layout.tsx:15`), which is the old bias-tool positioning. The login page's "Example" panel (`components/stageshow/AuthDemo.tsx`) shows an older navigation (Inventory, Plan, Run, Decide) that the app no longer has.
- **Leaky internal vocabulary.** "packs", "journeys", "common controls", "evidence class", "tool estimate" and "Proposed v2" reach the screen.
- **Design churn instead of capability.** More than 27 IA and visual iterations were made between 8 and 11 November. The shell is now good enough. The remaining gaps (connectors, notifications, execution, documents) are capability gaps that no layout can close.
- **Silent success.** Astryx pages mostly refresh data after a mutation without confirming it. No toasts are used in the shell, and there are no `error.tsx` or `loading.tsx` route boundaries.

**Wasted real estate:**
- The Environment page has top-level nav weight equal to Decisions and Findings.
- Agent audits is a top-level page for a single vendor.
- The Records group splits Evidence and Auditor packs, although both serve one job (job 6).

---

## 4. IA, UX, journeys, Nielsen heuristics and cognitive walkthrough

### Nielsen heuristics: violations that block the job

| # | Heuristic | Violation | Job blocked | Fix |
|---|---|---|---|---|
| 1 | Visibility of system status | `escalate` reports done without sending. Mutations give no confirmation. LLM calls run 60-90 s with no progress. `/plan` is blank with no state. | 3, 4 | Record `escalate` as "not sent" until a destination exists. Add toasts and progress for long calls. |
| 2 | Match with the real world | "Select an organisation to see its packs" appears on the systems page. Words like "packs", "journeys" and "tool estimate" are shown. The tab title is a bias-tool slogan. | 1, 2 | Rewrite copy per page. Use the words "requirement", "check", "proof", "measured" and "claimed". |
| 3 | User control and freedom | Running an evaluation or building a report drops the user into the legacy frame with a different navigation; the way back is unclear. | 3, 6 | Port these into the shell; until then, give legacy pages a "Back to system" bar. |
| 4 | Consistency and standards | There are four places to decide, six framework views, three audit logs, four evaluation surfaces and two visual systems. | 4 | Keep one place per job (table in section 2). |
| 5 | Error prevention | **Strength.** The gate blocks approval while critical items are open, and a conditional go requires conditions. **Gap:** the Discovery token field has no scope guidance. | none | Keep the gate guards. Add guidance on token scope. |
| 6 | Recognition rather than recall | `/onboard`, the CI gate, the CLI and the MCP server can be found only by knowing their URL or reading docs. | 1, engineer | Add "Register a system" on `/systems` and Home, and a "Connect your pipeline" page. |
| 7 | Flexibility and efficiency | There are no bulk actions, saved views or CSV import, which matters at the 100+ system scale the product targets. Search or ask, the CLI and the SDK are good. | 1 | Add bulk register, assign and request, plus CSV import. |
| 8 | Aesthetic and minimalist design | Astryx pages are calm. Legacy pages are long (`/compliance` is 428 lines), and the catalogue shows unbuilt items. | 3 | Cut legacy pages and filter unbuilt items. |
| 9 | Recognise, diagnose and recover from errors | "Try again" is offered on a state that retrying cannot fix. The Settings audit log fails with a generic "This could not load". | 1 | Write errors that name the cause and the fix ("You are not in an organisation yet. Ask your admin, or create one."). |
| 10 | Help and documentation | Help lives on the separate docs site. The only in-context help is "How to verify a pack", which is good. | all | Add per-page "What is this for", linked to the docs. |

### Cognitive walkthrough (new user, step by step)

Each step was scored against the four walkthrough questions: does the user know what to do, notice the action, link it to the result they want, and get feedback.

**J1. Governance lead, first day: get the estate in**
1. They request access and an admin approves, or they accept an invite. Know: yes. Feedback: an email on approval.
2. They sign in and land on Home. Without an organisation **they fail**: wrong copy, no selector. With an organisation they see the empty board and the copy is good.
3. They add their first system. Notice: only "Find unregistered AI" is offered. **They fail if their AI is not in MLflow, GitHub or Hugging Face**, which describes most enterprises. A manual route exists but cannot be noticed.
4. They see the estate fill in. With discovery the feedback is good: the systems board has Found, Registered and Approved columns.
- **Drop-off:** step 3. **Fix:** "Register a system" plus CSV import on Home and `/systems`; cloud connectors next.

**J2. System owner: get one system to a release decision**
1. They open the system file. Know: yes, because `path_forward` names the next step.
2. They run a fairness test by uploading a predictions CSV. Link to result: yes. Feedback: the gate moves.
3. They record a monitoring snapshot before the system is released. **Linking the action to the goal is weak**: "monitor before release" is not obvious.
4. They run the environmental assessment. **They fail to make the link**: nobody expects energy use to block a release.
5. They attest and add evidence. Some actions open legacy pages (`/tests`, `/compliance`). **Noticing the way back fails.**
6. They request the decision. Feedback: none beyond a status change, and the reviewer is not told.
- **Drop-off:** steps 3 to 5. **Fix:** a policy-optional environmental check, in-shell actions, and a "why this check matters" line on each gate check.

**J3. Reviewer: decide**
1. They learn a decision waits on them. **They fail**: no notification goes out.
2. They open Needs you and see the checks and conditions. Know: yes.
3. They approve, approve with conditions, or reject. Feedback: a banner ("Release approved.") and a seal.
- **Drop-off:** step 1. **Fix:** email plus Slack/Teams destinations, with a deep link to the item.

**J4. Auditor: verify**
1. They open the share link to `/verify`. Good.
2. They verify offline with `fairmind verify`. Good, and unique in this market.
3. They read evidence against a framework clause. **Partial**: the JSON manifest is not the document an auditor is used to.
- **Fix:** a rendered PDF in the pack, plus regulator-shaped documents.

**J5. ML engineer: gate in CI**
- The Action exists, but **nobody can notice it from the app**. Fix: a "Connect your pipeline" page that creates an API key and YAML in one step.

**J6. Agent owner: assess an agent**
- Works only with a Claude Managed Agents key. **Other agent stacks fail at step 1.** Fix: upload any MCP or agent config file, and add registry connectors.

**J7. Run a governance workflow**
1. They start a workflow from a framework (they have to know to go there). Notice: weak.
2. Steps wait for a person. The agent drafts only when someone clicks, and only with a provider set.
3. `escalate` shows done but sent nothing, so **the feedback is false**.
- **Fix:** see "Workflows and runs" in section 2.

---

## 5. Current and future problems

| Problem | Today | How well FairMind solves it |
|---|---|---|
| "What AI do we even have?" (shadow AI, agents) | The top buyer pain | **Poorly**: three dev-tool sources and no agents. |
| Proving a model is fit before release | Core | **Well**: the gate plus measured evidence. |
| EU AI Act readiness | Omnibus in force since 27 Jul 2026. GPAI duties since Aug 2025. Art. 50 transparency since 2 Aug 2026. Annex III high-risk moves to 2 Dec 2027; Annex I to 2 Aug 2028. EU-database registration reinstated. | **Partly**: catalogue mapping is current; Annex IV, FRIA and registration outputs are missing. Legacy `compliance_reporting.py` still lists the Act as "Proposed". |
| ISO 42001 certification | Rising procurement signal | **Partly**: the requirements are mapped, but there is no SoA or internal-audit pack. |
| India (DPDP Rules Nov 2025; MeitY guidelines Nov 2025; RBI FREE-AI) | Consent-manager rules from about Nov 2026; main duties from about May 2027 | **Partly**: frameworks are present; no data residency. |
| US (Colorado SB 26-189, effective 1 Jan 2027, disclosure-based) | Emerging | **No**: no notices for automated decision-making. |
| Agent accountability (OWASP Agentic Top 10, MCP Top 10) | Every hyperscaler shipped an agent registry in 2026, so inventory is becoming a commodity; the open problem is who approved what scope | **Partly**: config audits exist; no inventory, scope approvals or runtime link. |
| Continuous assurance after a model or provider swap | Growing | **Partly**: staleness lowers the gate, but no change triggers a re-check. |
| Third-party and vendor AI risk | Table stakes in RFPs | **No**. |
| Incident reporting (Art. 73) | Draft guidance; the date likely follows the high-risk delay (unverified) | **No**. |

**Future-proofing:**
1. **Be the cross-vendor decision and proof layer, not another registry.** Ingest from Agent 365, Foundry, AgentCore, Gemini Enterprise, ServiceNow and Databricks rather than competing with them on discovery. Then own the thing none of them sell: an independent, evidence-weighted, sealed release decision across all of them.
2. **Trigger re-checks on change.** A new MLflow version, a provider or model swap seen through GitHub, or expiring staleness should reopen the gate automatically. This turns point-in-time assurance into continuous assurance.
3. **Generate regulator-format documents from the same evidence**: Annex IV, FRIA, an EU-database record, an ISO 42001 SoA, Art. 73 reports, Colorado notices. The crosswalk already holds the mapping.
4. **Make the agent claim true, narrowly.** Agents that run evaluations, chase evidence owners and assemble packs, each action written to the ledger and each gate kept human, are defensible. Unscoped "autonomous governance" is not.
5. **Data residency** (India and EU regions) before regulated pilots in those markets.

---

## 6. Competitive differentiation and new features

Market context: Gartner published its first Magic Quadrant for AI governance platforms in mid-2026, per vendor posts; the report itself was not read. Leaders: IBM, ServiceNow, Truyo. Visionaries: OneTrust, Credo AI, ModelOp, Monitaur, Airia. Holistic AI is a Challenger. The market is consolidating: AuditBoard bought FairNow, Collibra bought trail ML, ServiceNow bought Armis and Veza, Check Point bought Lakera, SentinelOne bought Prompt Security (2025, unverified), and Cisco announced it will buy Astrix.

| Competitor | Serves the job better at | FairMind's answer |
|---|---|---|
| ServiceNow AI Control Tower | Discovery through Armis, CMDB, workflow and ticketing; agent identity through Veza; Agent 365 link | Integrate (tickets, CMDB import); do not out-build. |
| Microsoft Agent 365 (GA 1 May 2026, $15 per user per month) | Agent identity and policy across Entra, Purview and Defender inside the Microsoft estate | Ingest its registry; be the cross-vendor proof layer. |
| OneTrust | DPIA and privacy workflow, vendor risk, regulation content | Add vendor AI intake and DPIA/FRIA outputs. |
| Credo AI | Policy packs, board reporting, US government channel | FairMind's packs are deeper; it lacks a board view. |
| IBM watsonx.governance | Lifecycle factsheets and GRC integration | Equivalent evidence, and better verifiability. |
| Holistic AI | Testing breadth and red-teaming | Comparable engines; FairMind ties them to a decision. |
| Palo Alto, Cisco, Zenity, Noma | Runtime guardrails, agent discovery, prompt-injection defence | Do not compete. Consume their findings as evidence. |
| Hyperscaler registries (AWS, Google) | Free, native, but single-estate | Cross-estate is FairMind's opening. |

**Where FairMind is ahead:**
- Verifiable sealed decisions with public and offline verification.
- Evidence classes (measured, tool-estimated, attested) that change the confidence score.
- A CI release gate.
- India frameworks.
- BYO-key LLM across 19 providers.
- Open SDK, CLI and MCP.

No competitor researched markets cryptographic, auditor-verifiable decision records. This was not verified against every vendor.

**New capabilities that strengthen ownership of the job:**
1. Connector framework plus the top five sources: Azure AI Foundry and Agent 365, Bedrock and AgentCore, Vertex and Gemini Enterprise, Databricks, OpenAI org.
2. Agents as a first-class system kind, with approved tool scope as a sealed decision.
3. Approval routing to email, Slack, Teams, Jira and ServiceNow.
4. Change-triggered re-evaluation.
5. Regulator documents generated from evidence.
6. An incident register with Art. 73 clocks.
7. Vendor AI intake mapped to the same gate checks.
8. A customer-facing trust page built on `/verify`.

**Dilutes the purpose; avoid:**
- Building runtime guardrails or an AI firewall.
- Building SaaS shadow-AI discovery from scratch.
- Adding more catalogue workflows before existing ones execute.
- Leading with FairMind-E.
- Further visual "wow" iterations before the capability gaps close.

---

## 7. Prioritised roadmap

**Now (next 4-6 weeks): make the existing half honest and unbroken**
1. First run: an organisation picker or "create organisation" when there is none; per-page empty and error copy; fix the blank `/plan`.
2. "Register a system" in the shell (port `/onboard`) and CSV import, reachable from Home and `/systems`.
3. Notifications: email, plus a Slack/Teams webhook destination in Settings, for approval requests, run gates and `escalate`. `escalate` must say "not sent" when no destination exists.
4. Honesty pass: hide "Proposed" workflows and "Not built yet" evaluations by default and label them clearly where shown. Remove the placeholder endpoints. Cut stub and legacy-bias routes.
5. One decision surface (Needs you); `/decisions` becomes a register.
6. Port the evaluation run page and the PDF report builder into the shell, then cut `/compliance*` and `/reports`.
7. Make the environmental check optional per policy (off by default).
8. Fix the tab title and the login example panel; add a "Connect your pipeline" page for the GitHub Action.

**Next (1-2 quarters): close jobs 1, 3 and 5**
1. Cloud and agent-registry connectors (top five); agents as a system kind; bulk actions for 100+ systems.
2. Workflow steps that execute: run evaluations, request evidence from owners, assemble packs. Every action written to the ledger; gates stay human.
3. Re-checks triggered by change (MLflow version, GitHub release, provider swap).
4. Telemetry push API (OpenTelemetry GenAI) and an incident register with Art. 73 timing.
5. Regulator documents: Annex IV, FRIA, EU-database record, ISO 42001 SoA.
6. Jira and ServiceNow ticket sync.

**Later (2-4 quarters): durable advantage**
1. Vendor and third-party AI intake.
2. Data residency (India and EU).
3. ISO 42001 certification mode (internal audit, management review).
4. Colorado and US disclosure notices.
5. A customer-facing trust page on verified packs.
6. Ingest runtime-security findings (Prisma AIRS, Cisco, Zenity) as evidence.

---

## 8. Final verdict

**Ship with conditions**: to design-partner pilots now. **Do not ship yet** as a generally available "agentic AI governance platform".

Fit for pilots: regulated teams whose models live in MLflow, GitHub or Hugging Face and who need a defensible, verifiable release decision. That job FairMind already does better than most of the market.

Conditions before a general launch:
1. A new user can get from invitation to a first registered system without knowing a URL, whatever their organisation state.
2. A reviewer is told when a decision waits on them, and nothing in the product reports an action (such as `escalate`) that did not happen.
3. Every capability shown is real: no Proposed workflows or engineless evaluations presented as features, no placeholder endpoints, no stub routes.
4. Each job happens in one place, inside one shell. No mid-task trips into the legacy frame.
5. An auditor receives a human-readable, framework-shaped report alongside the verifiable manifest.
6. Discovery covers at least one major cloud AI platform and treats agents as systems.
7. The positioning matches the product: lead with proof-grade release decisions, and claim "agentic" only for steps agents actually perform.

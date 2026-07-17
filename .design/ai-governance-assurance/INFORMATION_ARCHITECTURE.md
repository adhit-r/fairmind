# Information Architecture: FairMind AI Governance Assurance

## Site Map

- AI Governance Overview `/ai-governance?system=:systemId`
  - Portfolio or selected-system readiness
  - Assigned work and blockers
  - Framework coverage and recent decisions
- AI Systems `/model-inventory?type=all|model|agent|composite`
  - System detail `?asset=:systemId&tab=overview|evaluations|controls|evidence|findings|activity`
- Frameworks & Controls `/compliance-dashboard?system=:systemId&framework=:frameworkKey&view=coverage|controls`
  - Framework activation
  - Version-pinned control assessment
  - Shared-control and evidence mappings
- Evidence & Evaluations `/evidence?system=:systemId&view=gaps|evaluations|artifacts`
  - Evidence detail `?evidence=:evidenceId`
  - Evaluation run detail `?run=:runId`
- Findings `/risks?system=:systemId&status=open|accepted|resolved`
  - Contextual remediation `/remediation?system=:systemId&finding=:findingId`
- Reports & Assurance `/reports?system=:systemId&view=summary|builder|history|auditor`
- Company Administration `/org-admin/*`
  - Members `/org-admin/members`
  - Roles `/org-admin/roles`
  - Settings `/org-admin/settings`
  - Audit Log `/org-admin/audit-log`

Legacy paths remain as redirects during migration:

- `/audit-reports` to `/reports?view=builder`
- `/compliance` and `/compliance/dashboard` to `/compliance-dashboard`
- `/remediation-wizard` to `/remediation?mode=guided`
- `/lifecycle` to the selected AI-system activity tab
- `/policies` to the policy view within Frameworks & Controls

## Navigation Model

- **Primary navigation:** retain the current application sidebar. Replace the fragmented `Govern & Prove` group with one `AI Governance` category containing six destinations: Overview, AI Systems, Frameworks & Controls, Evidence & Evaluations, Findings, Reports & Assurance.
- **Secondary navigation:** use view tabs within Frameworks & Controls, Evidence & Evaluations, and Reports & Assurance. Use query parameters rather than a new route for every framework, asset type, or detail tab.
- **Utility navigation:** company switcher, compact AI-system selector, account, organization administration, settings, and help remain outside the module hierarchy.
- **Mobile navigation:** reuse the existing sidebar sheet. Dense tables switch to labelled stacked rows while retaining control ID, state, owner, and evidence status.

Navigation depth is limited to two levels inside AI Governance. Detail opens inline, in a split panel, or through query-driven tabs before a new page is introduced.

## Content Hierarchy

### Overview

1. Company and AI-system scope, framework versions, and review period.
2. Current decision state and approval blockers.
3. Assigned work: missing evidence, failed evaluations, stale evidence, and overdue remediation.
4. Framework coverage and control-state distribution.
5. Recent evaluation runs, evidence reviews, findings, and decisions.

### AI Systems

1. Search and filters for model, agent, composite application, owner, risk, and lifecycle.
2. System table with readiness, failed evaluations, evidence gaps, and current decision.
3. Register AI system action and instructive empty state.
4. Quick detail with overview, evaluations, controls, evidence, findings, and activity.

### Frameworks & Controls

1. Framework version selector and activation state.
2. Coverage summary based on explicit control assessments, not artifact counts alone.
3. Shared-control table: framework ID, requirement, assessment state, owner, evidence, evaluations, freshness, and findings.
4. Expanded trace with mappings, guidance, rationale, reviewer disposition, and history.
5. Bulk owner and applicability actions, subject to permission checks.

### Evidence & Evaluations

1. Approval-blocking gaps and failed or stale evidence.
2. Evaluation runs from FairMind and configured integrations.
3. Evidence artifact library with source, assurance level, subject version, capture time, and freshness.
4. Candidate mappings requiring review.
5. Chronological provenance and supersession history.

### Findings

1. Critical and high findings that block approval.
2. Owner, due date, affected systems and controls, and remediation state.
3. Evidence and evaluation context that produced the finding.
4. Retest and verification evidence.

### Reports & Assurance

1. Version-pinned scope and readiness summary.
2. Report builder and preview.
3. Evidence index, control matrix, unresolved findings, decisions, and limitations.
4. Historical immutable report snapshots.
5. Read-only auditor view filtered to the assigned organization, systems, framework, and period.

## User Flows

### Company Provisioning

1. Administrator selects or creates the Organization.
2. Administrator invites members and assigns roles.
3. Administrator registers an AI system as model, agent, or composite application.
4. Administrator selects owner, use case, lifecycle, risk tier, and deployment context.
5. Administrator activates a framework version.
6. System control assessments are created in `not_started` state.

### Evaluation to Evidence

1. System owner opens the system and selects an evaluation suite.
2. FairMind runs in the configured environment.
3. The runner produces an immutable evidence envelope with system version, dataset or prompt-set hash, thresholds, metrics, findings, limitations, runner version, and artifact hashes.
4. The platform stores the run as framework-neutral evidence.
5. Declarative tags produce candidate control mappings.
6. A reviewer accepts or rejects each mapping with rationale.
7. Failed evaluation findings enter the Findings queue and may block approval.

### Control Review

1. Compliance owner filters Frameworks & Controls by framework, system, owner, or state.
2. Reviewer opens a control trace row.
3. Reviewer inspects requirement guidance, evidence, evaluation history, findings, and freshness.
4. Reviewer records applicability and control assessment state.
5. Missing or rejected evidence creates an assignable finding or evidence request.

### Auditor Review

1. Auditor enters Reports & Assurance in read-only mode.
2. Auditor confirms organization, system, framework version, review period, and report snapshot.
3. Auditor follows requirement to control assessment to evidence to finding to remediation to decision.
4. Auditor downloads the evidence index, control matrix, report, and audit log.

## Naming Conventions

| Concept | Label in UI | Notes |
|---|---|---|
| Tenant | Company | Backed by the existing Organization record. |
| Governed object | AI System | Model, agent, or composite application. |
| Catalog selection | Framework | A named standard or regulatory framework. |
| Immutable catalog release | Framework Version | Always shown in assessment and report scope. |
| Reusable implementation statement | Shared Control | Can map to multiple framework requirements. |
| System-specific control state | Control Assessment | Holds applicability, owner, status, and review. |
| Collected proof | Evidence | Framework-neutral artifact with provenance. |
| FairMind test execution | Evaluation Run | Produces evidence and findings, not compliance conclusions. |
| Evidence-to-control relationship | Evidence Mapping | Candidate, accepted, or rejected with rationale. |
| Control or evaluation problem | Finding | May lead to remediation and approval blocking. |
| Audit output | Assurance Package | Avoids implying certification. |

## Component Reuse Map

| Component | Used on | Behavior differences |
|---|---|---|
| Existing application sidebar | All dashboard routes | AI Governance receives six consolidated destinations. |
| Organization context | All governance routes | Displayed in one compact scope strip. |
| System context and detail drawer | Overview, AI Systems, all scoped views | Extended to model, agent, and composite types. |
| Evidence Hub filters and detail drawer | Evidence & Evaluations, control trace | Entity IDs replaced by searchable system and control pickers. |
| Risk and remediation tables | Findings, control trace | Finding context includes framework and control assessment. |
| Report preview and history | Reports & Assurance | Combined with auditor read-only view. |
| Existing FairMind evaluation result panels | Evidence & Evaluations | Wrapped in provenance, source, and mapping review metadata. |

## Content Growth Plan

- AI systems, controls, evidence, runs, and findings use server-side pagination and stable filters.
- Framework versions are immutable and archived, never overwritten.
- Evidence and evaluation history remains append-only and supports supersession links.
- Control rows use virtualization only when observed framework size or combined system scope requires it.
- Cross-framework views reuse shared controls rather than duplicating evidence per framework.

## URL Strategy

- Pattern: keep the current top-level route vocabulary during MVP to limit churn.
- Dynamic selection: use `system`, `framework`, `asset`, `evidence`, `run`, and `finding` query parameters.
- View state: use `view`, `tab`, `type`, and `status` query parameters.
- Shareability: meaningful review state belongs in the URL; transient drawer animation and unsaved form state do not.
- Security: URL identifiers never establish authorization. Every resource lookup is scoped to the authenticated organization.

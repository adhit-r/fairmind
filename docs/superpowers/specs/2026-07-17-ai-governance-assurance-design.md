# FairMind AI Governance Assurance Design

## Summary

FairMind will enhance its existing AI Governance module into a company-scoped, AI-system-first assurance workspace. The module will support immutable framework versions, shared controls, system-specific control assessments, evidence produced by company integrations and FairMind evaluations, reviewed evidence mappings, findings, remediation, decisions, and auditor-ready reports.

AIUC-1 April 2026 is the first framework version implemented through this architecture. It is not a separate application, data model, or visual system.

## Goals

- Use the existing Organization as the company tenant.
- Govern models, agents, and composite applications through the existing AI-system concept.
- Import and validate versioned framework catalogs without hard-coded route constants.
- Separate global control definitions from company and system implementation state.
- Turn real FairMind evaluation runs and integration snapshots into provenance-rich evidence.
- Require human review for evidence mappings and control conclusions.
- Consolidate the fragmented governance UX into six task-oriented destinations.
- Produce a version-pinned assurance package with a trace from requirement to decision.

## Non-goals

- Replacing FairMind evaluators.
- Building a second tenant, identity, risk, remediation, evidence, policy, or reporting subsystem.
- Building an AIUC-specific workflow or copying the reference mapping microsite.
- Creating a general integration marketplace or workflow engine.
- Automatically declaring a control satisfied, a framework compliant, or a system certified.
- Transferring raw model weights, unrestricted prompts, or private reasoning traces by default.

## Existing Foundation

The implementation reuses:

- Organization membership, invitations, roles, and audit records.
- Governance workspaces and AI systems.
- Governance evidence, evidence links, risks, remediation tasks, policies, approvals, decisions, and report snapshots.
- Evidence Hub CRUD and linking interactions.
- Existing FairMind bias, fairness, LLM, environmental, and other evaluation services.
- The FairMind-E pattern that versions an assessment, mirrors evidence, creates risks and remediation, and gates approval.
- Existing report preview, history, and PDF generation.

The implementation must correct these structural problems in the touched workflow:

- Governance resources are not consistently scoped to Organization.
- Frameworks are hard-coded and unversioned.
- Global framework definitions incorrectly contain tenant state such as owner and status.
- Evidence links lack reviewer disposition and mapping rationale.
- Evidence lacks a canonical source-run identity and content hash.
- Governance UX is fragmented across overlapping routes.

## Domain Model

### Existing records retained

- `Organization`: canonical company tenant.
- `GovernanceWorkspace`: optional grouping under an Organization.
- `GovernanceAISystem`: model, agent, or composite application.
- `GovernanceEvidence`: framework-neutral evidence artifact.
- `GovernanceRisk` and `GovernanceRemediationTask`: finding and resolution loop.
- Approval, decision, policy, and audit-report records.

### New or extended records

#### FrameworkVersion

Immutable catalog release with:

- `id`, `framework_key`, `name`, `version_label`, `status`.
- `source_filename`, `source_uri`, `source_hash`, `imported_at`, `imported_by`.
- `effective_date` or `published_date` when available.
- `licensing_note` and provenance metadata.

Unique key: `(framework_key, version_label, source_hash)`.

#### FrameworkControlDefinition

Immutable leaf definition attached to a FrameworkVersion:

- `external_id`, title, statement, principle, parent requirement ID and title.
- Mandatory or optional obligation.
- Core or Supplemental application.
- Frequency and capabilities.
- Evidence kind, title, guidance, category, and typical locations.
- Active or retired status and source-cell reference.

Unique key: `(framework_version_id, external_id)`.

#### FrameworkAssignment

Connects an Organization and AI system to a FrameworkVersion:

- `org_id`, `system_id`, `framework_version_id`.
- Assignment status, assigned by, assigned time, review period, and scope note.

Unique active key: `(org_id, system_id, framework_version_id)`.

#### SystemControlAssessment

The company and system-specific state for one control definition:

- `org_id`, `system_id`, `framework_assignment_id`, `control_definition_id`.
- `applicability`: applicable, not applicable, or pending.
- `status`: not started, partial, ready for review, accepted, or rejected.
- Owner, due date, applicability rationale, reviewer, review rationale, reviewed time, and next review date.

Global framework definitions never hold owner, applicability, or completion state.

#### EvidenceRun

Immutable source execution for a FairMind evaluation or integration collection:

- `org_id`, `system_id`, source type and source identifier.
- Run ID, suite or connector name and version, trigger, start and end times.
- Subject versions, dataset or test-set hashes, configuration hash, thresholds, seed, runner commit or image digest.
- Summary result, limitations, artifact references, content hash, capture time, retention, and expiry.

Idempotency key: `(org_id, source_type, source_identifier, run_id, content_hash)`.

#### Reviewed Evidence Mapping

Extends the evidence-to-entity relationship for control assessments:

- Evidence ID and control-assessment ID.
- Relation type and mapping rationale.
- State: candidate, accepted, or rejected.
- Suggested by, mapped by, reviewed by, and review timestamps.

One artifact may support multiple controls. Each mapping receives an independent rationale and disposition.

## Tenant Isolation

All new tenant-owned records contain `org_id`. Every new route obtains the authenticated user and organization context, verifies membership or permission, and scopes resource lookup by both `id` and `org_id`.

`GovernanceWorkspace` gains `org_id`. AI systems inherit tenant scope through workspace, and touched evidence, assignment, assessment, run, finding, remediation, and report paths verify the same organization chain.

Cross-organization denial tests are required for list, create, read, update, delete, review, sync, and report operations. Caller-supplied actor fields are replaced by authenticated identities.

SQLite remains supported for local tests through application filters and composite constraints. PostgreSQL deployment adds row-level security after migration and backfill. Ambiguous legacy rows are not assigned to a guessed organization.

## AIUC-1 Import

Authoritative input: `/Users/adhi/Downloads/AIUC-1 _ April, 2026 version.xlsx`.

The importer reads:

- `Instructions`: version, update cadence, source, audit, testing, and claim restrictions.
- `AIUC-1 requirements`: 51 requirements across six principles.
- `AIUC-1 Controls & Evidence`: 135 unique leaf control and evidence rows.

Acceptance checks:

- Workbook hash is recorded.
- Version label is exactly `April, 2026` after normalized parsing.
- Requirement count is 51.
- Leaf control count is 135.
- Leaf control IDs are unique.
- Every leaf joins to a parent requirement.
- Retired requirements and controls remain present with retired status.
- Current and historical columns are not silently merged.

The importer is framework-neutral. A small adapter maps workbook columns into the catalog contract. Tests use a synthetic workbook fixture; the supplied workbook and its full wording are not committed unless licensing is confirmed.

The AIUC1-Mapping-Tool is used only as an interaction and deterministic-mapping reference. Its checked-out version is stale relative to the workbook and has no explicit license. No source code or mapper-authored enrichment is copied.

## Evaluation and Evidence Pipeline

At evaluation completion, an adapter emits one immutable evidence envelope:

- Organization, AI system, model or agent version, provider or endpoint, and deployment.
- Evaluation suite, run type, trigger, runner version, and timestamps.
- Dataset or prompt-set identity, version, hash, sample counts, protected groups, and exclusions.
- Configuration, thresholds, seed, and code or image digest.
- Metrics, findings, pass or fail result, and explicit limitations.
- Raw artifact references and hashes.
- Assurance source. FairMind internal runs are never marked third-party.
- Retention, expiry, capture time, and content hash.

The ingestion service:

1. Validates tenant, system, source, and envelope.
2. Computes canonical JSON and content hash.
3. Applies the idempotency key.
4. Stores the EvidenceRun and GovernanceEvidence record.
5. Uses declarative test tags and evidence kinds to suggest candidate control mappings.
6. Creates findings for failed tests where a configured policy requires them.
7. Preserves all failed, superseded, and rerun evidence.

Reviewers accept or reject candidate mappings. Control assessment state is derived from explicit reviewer decisions and required evidence coverage, not from artifact count alone.

Raw model weights remain in the customer environment by default. Open-weight models may be evaluated by a customer-side runner that sends hashes, metrics, and artifact references. Closed models use black-box endpoint evaluation. Prompt and tool traces are minimized and redacted according to retention policy.

## Services

- `FrameworkCatalogService`: validate and import immutable framework versions and definitions.
- `FrameworkAssignmentService`: assign versions to systems and initialize control assessments.
- `ControlAssessmentService`: applicability, ownership, reviewer disposition, evidence coverage, and readiness.
- `EvidenceIngestionService`: one idempotent path for FairMind evaluation and integration evidence.
- `IntegrationSyncService`: orchestrate configured provider adapters without connector-specific tables.

Existing remediation, approval, policy, audit-log, and report services are extended rather than replaced.

## API Surface

All routes are under the existing AI Governance API and require authenticated organization context.

- `GET /frameworks`
- `POST /frameworks/import` for authorized administrators
- `GET /frameworks/{framework_key}/versions`
- `GET /framework-versions/{version_id}/controls`
- `POST /systems/{system_id}/framework-assignments`
- `GET /systems/{system_id}/framework-assignments`
- `GET /framework-assignments/{assignment_id}/controls`
- `PATCH /control-assessments/{assessment_id}`
- `POST /systems/{system_id}/evidence-runs`
- `GET /systems/{system_id}/evidence-runs`
- `POST /evidence/{evidence_id}/control-mappings`
- `POST /evidence-mappings/{mapping_id}/review`
- `GET /framework-assignments/{assignment_id}/readiness`
- `POST /framework-assignments/{assignment_id}/reports`

Existing system evidence endpoints remain compatibility paths and are routed through EvidenceIngestionService when provenance data is present.

## Frontend Architecture

AI Governance remains inside the current dashboard shell. The sidebar exposes:

1. Overview
2. AI Systems
3. Frameworks & Controls
4. Evidence & Evaluations
5. Findings
6. Reports & Assurance

Current routes are reused during MVP:

- `/ai-governance`
- `/model-inventory`
- `/compliance-dashboard`
- `/evidence`
- `/risks` and contextual `/remediation`
- `/reports`

Overlapping routes become redirects. The Organization switcher and AI-system context become one compact scope strip. Model Inventory is relabelled AI Systems and supports model, agent, and composite types.

Frameworks & Controls uses a dense shared-control table. Evidence & Evaluations combines existing evidence mechanics with evaluation-run provenance and mapping review. Reports & Assurance combines the current Reports and Audit Reports experiences and adds read-only auditor mode.

## Readiness Semantics

Readiness is a transparent aggregation of explicit state:

- Applicable control assessments.
- Required evidence mappings accepted by reviewers.
- Evidence freshness and expiry.
- Failed evaluations and unresolved findings.
- Required policies and approvals.
- Blocking remediation.

The UI shows the numerator, denominator, exclusions, blockers, and limitations. It does not present one unexplained compliance percentage.

Permitted language:

- `AIUC-1 readiness`
- `Evidence mapped to AIUC-1 April 2026 controls`
- `FairMind-collected supporting evidence`
- `Ready for reviewer or auditor review`

Prohibited language without official certification:

- `AIUC-1 compliant`
- `follows AIUC-1`
- `has met AIUC-1`
- `certified`

## Error Handling

- Invalid framework imports fail atomically and return count, join, duplicate-ID, or version errors without partial writes.
- Repeated evidence runs with the same idempotency key return the existing run.
- Hash mismatch or attempted mutation of immutable evidence returns a conflict response and records an audit event.
- Missing integration credentials never create candidate evidence.
- Evaluation failure records an error run with limitations; it does not create a passing or accepted artifact.
- Unauthorized and cross-organization resource lookups return a non-disclosing not-found or forbidden response according to the existing security policy.
- Frontend empty states explain the next action; loading uses skeletons; recoverable errors preserve filters and unsaved review rationale.

## Testing Strategy

Backend tests are written before implementation and cover:

- Framework workbook parsing, count validation, parent joins, retirement, and atomic failure.
- Framework-version immutability and duplicate import idempotency.
- Cross-organization denial for every new resource-by-ID route.
- Framework assignment and system-control creation.
- Evidence canonicalization, hashing, source-run idempotency, and tamper rejection.
- Candidate mapping and reviewer acceptance or rejection history.
- Readiness with missing, stale, rejected, failed, and accepted evidence.
- Reproducible report snapshots pinned to framework and evidence versions.

Frontend tests cover:

- Six-destination governance navigation.
- Company and AI-system scope preservation.
- AIUC-1 framework activation.
- Control filters, expanded trace, evidence review, and accessible state labels.
- Evaluation-run provenance and mapping review.
- Auditor read-only restrictions.
- Desktop and mobile task completion.

Baseline note: the frontend production build passes. The backend test collection currently has a pre-existing package-root failure in `test_fairness_evidence_profile_route.py` because `api.models` is unavailable from the backend package context. Feature tests will run independently, and the baseline failure remains separately recorded unless the feature touches that import path.

## Migration and Rollout

1. Add versioned catalog, assignment, assessment, evidence-run, and reviewed-mapping tables.
2. Add Organization linkage to governance workspace and touched tenant records.
3. Import the AIUC-1 workbook into a development database and verify counts and hashes.
4. Expose org-scoped APIs behind a feature flag.
5. Add the consolidated navigation and Frameworks & Controls experience.
6. Adapt one real FairMind evaluation path into EvidenceIngestionService.
7. Add reviewer mapping, findings, and readiness.
8. Add assurance export and auditor read-only mode.
9. Redirect overlapping legacy routes after parity checks.

Migration is additive until the new route path and UI are verified. Hard-coded framework constants and global control state are removed only after backfill and parity validation.

## Security and Privacy

- Organization membership and permission checks are mandatory at every route and service boundary.
- Credentials are referenced through the existing secret-management pattern and never returned by APIs.
- Evidence payloads are minimized, hashed, access-controlled, and retained according to policy.
- Raw model weights stay in the customer environment by default.
- Chain-of-thought and private reasoning traces are not collected.
- Audit, evidence, mapping-review, and report history is append-only.
- Background jobs carry explicit organization context and cannot bypass tenant filters.

## Decision Record

The approved product direction is system-first with a framework lens. Organization is the company. AIUC-1 is an immutable framework pack. FairMind evaluations and company integrations create framework-neutral evidence. Automation may suggest mappings, while reviewers decide evidence acceptance and control state. Existing governance entities and routes are consolidated and extended rather than replaced.

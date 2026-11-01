# FairMind Evidence Workbench Recovery Design

## Status and decision

Date: 18 July 2026

The user requested autonomous execution of the FairMind recovery. The selected product is a vendor-neutral assurance evidence compiler. FairMind will not become another generic GRC suite organized around questionnaires and readiness percentages, and it will not become a proprietary laboratory that must own every evaluator.

The product compiles outputs from real model, data, LLM, agent, security, provenance, and environmental evaluations into portable Evidence Passports. A passport preserves subject identity, evaluator and configuration versions, pre-registered thresholds, artifact integrity, result, limitations, reviewer decisions, remediation, reruns, and versioned framework mappings. FairMind supports review and assurance-package preparation; it does not automatically determine legal compliance or issue certification.

## Context

The current repository contains a wide dashboard and API surface but only a few evidence-grade paths. FairMind-E is the strongest working vertical slice. The current Evidence Hub stores metadata without immutable run provenance or artifact digests. The main tabular-bias route is broken, the modern-bias screen fabricates exportable results, current multimodal analysis is metadata-only, compliance checks are declared-field presence checks, reports lack one canonical manifest, and Model DNA is mock data.

A sibling worktree at `/Users/adhi/axonome/fairmind-ai-governance-assurance` already implements organization-scoped systems and framework assignments, immutable framework versions, source hashes, evidence-run identities and content hashes, bounded artifact references, candidate/accepted/rejected mapping review, backend readiness, freshness, and an assurance report studio. It diverges from the current FairMind-E branch and both worktrees are dirty. The recovery integrates their committed histories in an isolated worktree; it does not merge either dirty worktree in place.

The detailed current-state, market, framework, and gap evidence is recorded in `docs/product/FAIRMIND_RECOVERY_AUDIT_2026-07-18.md`. The implementation sequence is `docs/product/SPRINT_BACKLOG_2026-07-18.md`.

## Users and jobs

### AI assurance lead

- Select an organization and AI system.
- See which evidence is current, stale, limited, rejected, or missing.
- Understand blockers without reverse-engineering a readiness score.
- Produce a version-pinned evidence package for an internal or external review.

### ML engineer or evaluator operator

- Run a FairMind evaluator or import a native tool report.
- Preserve model, dataset, prompt, configuration, threshold, environment, and tool identities.
- Compare failed and clean reruns without losing the first result.
- Resolve a finding and show exactly which retest verifies the remediation.

### Model-risk, compliance, or security reviewer

- Inspect source artifacts and limitations before accepting a mapping.
- Accept or reject each evidence-to-control mapping independently with rationale.
- Mark applicability and assess control state without changing the immutable framework definition.
- See conflicts when another reviewer has already changed the decision.

### Auditor or independent reviewer

- Navigate a read-only evidence index from framework requirement to control, passport, artifact hash, finding, remediation, retest, approval, and report.
- Reproduce the manifest hash for a pinned evidence cutoff.
- Distinguish FairMind-internal, company-integration, manually registered, and third-party evidence.
- See missing or insufficient evidence explicitly.

## Goals

- Establish one organization-scoped assurance graph for models, agents, and composite applications.
- Establish Evidence Passport schema version `1.0.0` as the portable evidence contract.
- Ingest FairMind-E, one real fairness evaluator, and external tool outputs through one application port.
- Preserve immutable source-run identity, `runContentHash`, passport snapshot hashes, and bounded artifact references.
- Require accountable human review for every accepted control mapping.
- Derive transparent readiness from explicit control and evidence state.
- Preserve findings, remediation, retest, approvals, and negative history.
- Render AIUC-1 readiness and EU Annex IV support packets from one canonical manifest.
- Consolidate the dashboard into six task-focused destinations while preserving organization/system context.
- Correct unsupported claims and expose capability truth everywhere.

## Non-goals

- Issuing a certificate, legal opinion, conformity assessment, or automatic compliance decision.
- Replacing certification bodies, legal counsel, auditors, or accountable system owners.
- Rebuilding Giskard, MLflow, Fairlearn, AIF360, ModelScan, garak, PyRIT, or observability platforms.
- Building another tenant, risk, remediation, policy, approval, or report subsystem alongside the existing governance records.
- Collecting raw model weights, unrestricted prompt histories, private reasoning traces, secrets, or artifact bodies by default.
- Claiming actual image, audio, or video analysis before a separately deployed media worker passes a validated gold-set evaluation.
- Treating field presence, artifact count, provider availability, or missing data as evidence of success.
- Deleting candidate services before the final assurance/evaluator runtime closure is known.

## Official evidence-design anchors

The framework mappings are versioned product aids, not a substitute for the authoritative source or professional interpretation.

- The [EU AI Act](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689) connects lifecycle risk management, data governance, predefined testing, technical documentation, logging, accuracy/robustness/cybersecurity, quality management, and post-market monitoring. FairMind exports traceable contributions to those records. The [Council timeline](https://www.consilium.europa.eu/en/policies/artificial-intelligence-act/timeline-artificial-intelligence/) is stored with product guidance because application dates have changed.
- [ISO/IEC 42001](https://www.iso.org/standard/42001) defines an AI management-system approach. FairMind passports support its records; they are not certification.
- [ISO/IEC 23894](https://www.iso.org/standard/77304.html) provides AI risk-management guidance. FairMind links evidence to risk assessment, treatment, monitoring, and reassessment without copying proprietary clauses.
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), the [AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/), and [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) motivate versioned GOVERN/MAP/MEASURE/MANAGE mappings, TEVV provenance, lineage, limitations, incident, and change records. The Playbook remains optional guidance.
- [AIUC-1 scope](https://www.aiuc-1.com/scoping), [current changelog](https://www.aiuc-1.com/changelog), [third-party evidence guidance](https://www.aiuc-1.com/evidence/third-party), and [certificate process](https://www.aiuc-1.com/learn/certificate) motivate versioned control catalogs, Statements of Applicability, quarterly technical evidence, and evaluation reports containing scope, methodology, findings, assessor context, and remediation. FairMind prepares evidence for review and is not the certifier.

## Canonical domain graph

The graph has a governance chain and an evidence chain:

`Organization → Workspace → AI System → Framework Assignment → Control Assessment`

`Evaluation Run → Evidence Artifact → Candidate Mapping → Reviewer Decision → Finding/Risk → Remediation → Retest → Approval → Assurance Package`

### Organization

The existing `Organization` is the company tenant. Every workspace, system, assignment, assessment, run, artifact metadata record, mapping, finding, remediation, approval, and report is resolved through an organization-scoped repository query. Caller-supplied organization IDs never grant access.

### Workspace

`GovernanceWorkspace` is the required grouping between one organization and its governed AI systems in the recovered graph. Legacy rows without an unambiguous organization or workspace are quarantined for explicit migration review; the migration does not guess.

### AI System

`GovernanceAISystem` represents a model, agent, or composite application. It has a stable identity, explicit version, identity hash, intended use, owner, and optional deployment reference. Test results are never attached only to a display name.

### Framework Version and Control Definition

Framework catalogs are immutable and tenant-neutral. Each `FrameworkVersion` records framework key, version label, source URI, source filename, source SHA-256, effective/published date where known, imported actor, imported time, and licensing note. Each leaf `FrameworkControlDefinition` retains its external ID, parent hierarchy, statement metadata, evidence guidance, applicability class, status, and source location.

Owner, applicability, due date, status, evidence coverage, and reviewer conclusion do not live on the global definition.

### Framework Assignment and Control Assessment

A `FrameworkAssignment` pins one immutable framework version to one organization and AI system. It records scope, review period, state, actor, and assignment time. A `SystemControlAssessment` records applicability, rationale, owner, due date, state, reviewer, review rationale, and next review for one assigned control.

### Evaluation Run and Evidence Artifact

An `EvaluationRun` is the immutable execution identity. It records source, run ID, capability state, assurance source, evaluator/suite/runner versions, subject and input identities, configuration hash, thresholds, environment, result, limitations, capture/expiry, and `runContentHash`. `EvidenceArtifact` stores a bounded URI, digest, media type, role, size, sensitivity flag, retention policy, and redaction note; it does not store unrestricted raw bodies in the governance row.

### Mapping and reviewer decision

A mapping links one passport to one system control assessment. Its state is `candidate`, `accepted`, or `rejected`. Automation may create a candidate with rationale. Only an authenticated reviewer may accept or reject it. Review uses optimistic concurrency and retains actor, timestamp, rationale, version, and history.

### Finding, remediation, retest, and approval

Configured failed or limited runs may create findings. Findings link to the artifacts that support them. Remediation records owner, action, due/completion state, and linked findings. A remediation becomes verified only when a new passport identifies the predecessor under `retestOfPassportIds`. A clean retest does not mutate or delete the failed passport. Approval reads blockers but remains a separate authenticated decision.

### Assurance package

The package is a server-generated canonical JSON manifest pinned to organization, AI system, framework version and source hash, evidence cutoff, accepted mapping set, unresolved finding set, remediation/retest state, approval state, and limitations. PDF and DOCX are renderings that cite the manifest hash.

## Evidence Passport contract

The normative exchange schema is `docs/product/evidence-passport.schema.json`.

### Required identity and scope

- Schema version and immutable passport ID.
- `supporting_evidence_only` claim boundary.
- Organization, workspace, AI system, system version, and system identity hash.
- Subject kind, stable ID, version, and SHA-256 digest.
- Intended use, input fingerprint, sample count, protected groups/locales where relevant, and explicit exclusions.

### Required execution provenance

- Source type and identifier, run ID, assurance source, and capability state.
- Evaluator, adapter, runner, and suite names and versions.
- Configuration hash, optional seed, environment identity, and pre-registered thresholds with rationale.
- Start, end, and capture times.
- Explicit result status, measured metrics, limitations, and diagnostic error context where applicable.

### Artifact integrity

- At least one bounded artifact reference, including a diagnostic log for unavailable/error executions.
- Maximum 50 references per passport.
- URI, lowercase SHA-256, MIME type, role, sensitivity flag, optional size, retention policy, and redaction note.
- No inline unrestricted artifact body.

### Review and reuse

- Candidate, accepted, or rejected versioned framework mappings.
- Framework source hash and control-assessment ID on every mapping.
- Reviewer actor, decision, timestamp, rationale, and optimistic review version for accepted/rejected mappings.
- Passport-level pending, accepted, or rejected review.
- Findings, remediation, freshness, invalidation keys, predecessors, and retest links.

### Canonicalization and signatures

The server calculates two hashes. `evaluation.runContentHash` is the lowercase SHA-256 of the immutable RFC 8785 execution envelope and ordered artifact-reference set; mapping, review, remediation, and freshness state are excluded. `canonicalContentHash` covers the complete exported passport snapshot after omitting `canonicalContentHash` and `signatures`. The client may send either hash for integrity comparison but cannot choose the stored value.

`passportId` remains stable while `passportRevision` increases when review, mapping, remediation, freshness, or lineage changes. Revision 2 and later include `previousRevisionHash`, creating a tamper-evident snapshot chain without changing the immutable evaluation-run hash. Optional Ed25519, ES256, or RS256 signatures cover the snapshot canonical hash and identify the signing key and time.

Idempotency is scoped to organization, system, source type, source identifier, and run ID. Replaying identical canonical content returns the existing record. Reusing that immutable identity with changed content returns HTTP 409 and writes an audit event.

## Evidence ingestion architecture

### Application port

`apps/backend/src/application/ports/evidence_ingestion.py` defines the sole write boundary for evaluator evidence. The port accepts a validated passport plus authenticated organization/system context and returns the immutable run, evidence record, and candidate mappings.

The application service performs:

1. Membership, permission, system, and source validation.
2. JSON Schema/domain-model validation.
3. Canonicalization and server-side content hashing.
4. Immutable identity and conflict check.
5. Transactional run and artifact-metadata persistence.
6. Candidate mapping suggestions from declarative tags and framework adapters.
7. Configured finding creation for failed or limited results.
8. Audit event creation.

It never accepts a mapping, changes a control assessment, approves a release, or declares compliance.

### Adapter contract

Adapters convert native output to a passport; they do not hide the source artifact. Each adapter supplies:

- Stable adapter name and version.
- Supported source family and format versions.
- Format detection with confidence.
- Deterministic conversion for the same native document and context.
- Native run IDs, tool versions, metrics, thresholds, and limitations.
- One or more hashed native artifact references.
- Candidate framework/control tags, never accepted mappings.

Initial internal adapters:

- FairMind environmental assessment.
- One validated tabular fairness evaluation.
- Provider-backed LLM evaluation after prompt-set/evaluator provenance is persisted.
- Multimodal metadata assessment explicitly labelled `metadata_only`.
- Compliance declared-context audit explicitly labelled as gap review.
- AI BOM fairness-profile transformation.

Initial external-import adapters:

- Giskard JSON/JUnit results.
- MLflow evaluation run artifacts.
- Fairlearn/AIF360 metric and mitigation output.
- ModelScan JSON reports.
- garak JSONL or PyRIT conversation/score exports.

External adapters ingest reports; they do not add those tools as FairMind runtime dependencies.

## Capability truth and fail-closed semantics

Each evaluator publishes one state:

| State | Meaning | Permitted result behaviour |
| --- | --- | --- |
| `validated` | Evaluator and contract have passed the defined validation suite for the stated scope | May report pass/fail/informational with thresholds and limitations |
| `metadata_only` | Evaluates declared labels or metadata, not underlying content | Must say which content was not inspected; cannot claim media analysis |
| `external_provider` | Result depends on an identified provider or endpoint | Missing credentials or provider failure becomes `unavailable` |
| `unavailable` | Evaluator cannot run or source cannot be reached | Result status is `unavailable`; no pass, accepted mapping, or exportable assurance conclusion |
| `insufficient_data` | Available inputs do not support a conclusion | Result status is `insufficient_data`; no negative bias conclusion or readiness credit |

An error is preserved as a run with limitations and diagnostic evidence. It is not silently omitted and is never converted to a default pass.

## Framework mapping model

Framework adapters map an immutable source catalog into FairMind's shared definition model. Mappings always carry framework key, exact version label, and source hash. They remain suggestions until a reviewer accepts them for a specific system control assessment.

### AIUC-1

The current public source describes 50 requirements and a quarterly update cycle as of 15 July 2026. The sibling branch contains a historical April 2026 workbook adapter validated against 51 requirements and 135 controls. The importer preserves that historical source and hash but the UI never presents its count as the current standard. A refreshed source creates a new immutable version and does not rewrite existing assignments.

FairMind export language is limited to `AIUC-1 readiness`, `evidence mapped to [version] AIUC-1 controls`, `supporting evidence`, and `ready for reviewer or auditor review`.

### EU AI Act

The first export is a technical-documentation contribution index, not an Annex IV conformity declaration. It groups system description, design/dependencies, data scope/governance, test thresholds/results, accuracy/robustness/security evidence, risk records, logging references, lifecycle changes, and post-market evidence. Missing sections remain visible.

### ISO and NIST

ISO mappings identify supporting management-system and risk records without reproducing proprietary clause text. NIST mappings identify AI RMF/GenAI Profile outcomes and profile version. Neither mapping is a checklist score or certification claim.

## Readiness semantics

Readiness is calculated by the backend from explicit state:

- Applicable and not-applicable control assessments.
- Accepted, rejected, and candidate evidence mappings.
- Required evidence kinds and current evidence coverage.
- Passport freshness and invalidation.
- Failed evaluations and unresolved findings.
- Required policies, remediation, and approvals.
- Capability state and material limitations.

The API returns numerator, denominator, exclusions, missing evidence, stale evidence, rejected assessments, unresolved blockers, and limitations. A candidate mapping, expired passport, unavailable evaluator, or insufficient dataset contributes no accepted coverage. The UI does not replace missing counts with zero or collapse them into an unexplained percentage.

## Information architecture

The dashboard keeps one selected organization and AI system across six destinations:

| Task | Route | Primary content |
| --- | --- | --- |
| Overview | `/ai-governance` | Scope, capability state, blockers, bounded readiness, decisions, and environmental governance |
| AI Systems | `/model-inventory` | Models, agents, composites, versions, intended use, owners, and deployments |
| Frameworks & Controls | `/compliance-dashboard` | Catalog versions, assignments, applicability, control state, evidence coverage, and trace |
| Evidence & Evaluations | `/evidence` | Runs, passports, artifacts, thresholds, metrics, limitations, freshness, mappings, and rerun comparison |
| Findings | `/risks` | Findings, risks, remediation, retests, exceptions, and approval dependencies |
| Reports & Assurance | `/reports` | Pinned manifest, evidence index, limitations, decisions, history, read-only auditor mode, and renderings |

Temporary redirects preserve `/audit-reports`, `/compliance`, `/compliance/dashboard`, and guided-remediation bookmarks until parity and telemetry checks justify removal.

### Core workflow

1. Select organization and AI system.
2. Assign an immutable framework version.
3. Run or import an evaluation.
4. Inspect the passport's subject, evaluator, threshold, artifacts, result, and limitations.
5. Accept or reject candidate mappings with rationale.
6. Inspect backend readiness and blockers.
7. Create or follow a finding, remediation, and retest.
8. Record an approval decision separately.
9. Pin an evidence cutoff and export the canonical assurance package.

## API surface

All routes require authenticated organization context and live under the AI Governance API:

- `GET /organizations/{org_id}/frameworks`
- `POST /organizations/{org_id}/frameworks/import`
- `GET /organizations/{org_id}/frameworks/{framework_key}/versions`
- `GET /organizations/{org_id}/framework-versions/{version_id}/controls`
- `POST /organizations/{org_id}/workspaces`
- `POST /organizations/{org_id}/systems`
- `POST /organizations/{org_id}/systems/{system_id}/framework-assignments`
- `GET /organizations/{org_id}/systems/{system_id}/framework-assignments`
- `GET /organizations/{org_id}/framework-assignments/{assignment_id}/controls`
- `PATCH /organizations/{org_id}/control-assessments/{assessment_id}`
- `GET /organizations/{org_id}/framework-assignments/{assignment_id}/readiness`
- `POST /organizations/{org_id}/systems/{system_id}/evidence-runs`
- `GET /organizations/{org_id}/systems/{system_id}/evidence-runs`
- `POST /organizations/{org_id}/systems/{system_id}/evidence-imports`
- `POST /organizations/{org_id}/evidence/{evidence_id}/control-mappings`
- `POST /organizations/{org_id}/evidence-mappings/{mapping_id}/review`
- `POST /organizations/{org_id}/framework-assignments/{assignment_id}/assurance-manifests`
- `GET /organizations/{org_id}/assurance-manifests/{manifest_id}`

Compatibility evidence endpoints route through the ingestion service when complete provenance exists. Metadata-only legacy registration remains visibly separate and receives no control credit.

## Persistence and migrations

- Use one SQLAlchemy/session lifecycle for touched governance APIs.
- Use managed migrations for schema evolution. Renumber the assurance worktree's `009_governance_assurance.sql` to `011_governance_assurance.sql` because the product branch already has `009_policy_versions.sql` and `010_environmental_governance.sql`. Request handlers do not call `create_all`, `ALTER TABLE`, or `CREATE TABLE IF NOT EXISTS`.
- Retain SQLite for focused local tests and PostgreSQL for deployment tests.
- Add composite organization/resource indexes and constraints.
- Apply PostgreSQL row-level security only after organization backfill and application-level negative tests are green.
- Backfill unambiguous legacy relationships; quarantine ambiguous rows with a migration report.
- Keep catalog definitions, runs, artifacts, mapping decisions, findings, retests, approvals, and manifest history append-only where mutation would break auditability.

## Security and privacy

- Resolve actor identity from authentication, not request fields.
- Verify organization membership and permission at route and service boundaries.
- Scope background jobs and connector syncs with explicit organization/system context.
- Keep credentials in existing secret-management paths and never return them.
- Reject absolute or escaping framework-import paths; accept managed relative `.xlsx` sources within size bounds.
- Limit artifact reference count, URI length, hash form, metadata size, and accepted media types.
- Keep model weights and sensitive evaluation data in customer-controlled storage by default.
- Do not collect chain-of-thought or private reasoning traces.
- Record sensitivity and redaction metadata on artifact references.
- Use retention policies appropriate to the organization and applicable obligation; do not apply one universal 90-day freshness rule.
- Log rejected mutations, cross-organization access attempts, hash conflicts, and mapping-review conflicts without exposing another tenant's resource existence.

## Report and export contract

The server generates one canonical manifest containing:

- Organization, workspace, AI system, version, intended use, and identity hash.
- Framework key, immutable version, source URI, and source hash.
- Evidence period and cutoff.
- Control applicability and assessment state.
- Accepted, rejected, and candidate mapping decisions.
- Passport IDs, revisions, immutable run hashes, and full snapshot hashes.
- Subject, evaluator, suite, input, configuration, threshold, and artifact identities.
- Results, capability states, freshness, and limitations.
- Findings, remediation, retests, approvals, and unresolved blockers.
- Explicit missing sections and claim-boundary disclaimer.

PDF and DOCX renderers consume this manifest and do not query live governance tables independently. Presentation timestamps are excluded from the canonical hash. Two renders from the same manifest cite the same hash.

## Interface design

The Evidence Workbench follows `DESIGN.md` and the Assurance Ledger north star.

- Evidence detail leads with subject, evaluator, result, review state, and freshness.
- Threshold, versions, scope, limitations, and artifact hash are visible before framework mappings.
- Candidate mappings use action-oriented orange; accepted context uses restrained teal/green; failures and blockers use text plus semantic color.
- Full 2px/4px borders, square geometry, and hard shadows indicate interactive or consequential surfaces.
- No gradients, purple, glassmorphism, soft card clouds, ornamental motion, sparkle icons, chat-first copilot, or dashboard hero.
- Tables are keyboard navigable and retain headers/labels at 200% zoom.
- All actions have 44px minimum targets and visible focus.
- Mobile preserves the selected organization/system scope and review order.
- Reduced motion removes physical hover translation without hiding state change.

## Claim policy

Permitted:

- `AI assurance evidence workbench`
- `Evidence Passport`
- `Supporting evidence`
- `AIUC-1 readiness`
- `Evidence mapped to [exact framework version] controls`
- `Technical-documentation contribution`
- `Ready for reviewer or auditor review`
- `FairMind-internal evaluation`, `company-integration evidence`, or `third-party evidence` when accurately sourced

Prohibited without an external determination:

- `Certified`
- `Compliant`
- `Meets the EU AI Act`
- `Follows AIUC-1`
- `Passed governance`
- `Not biased` when evidence is missing, insufficient, metadata-only, or unavailable
- `Third-party` for a FairMind-internal run
- `Image analysis` for the metadata-only multimodal path

## Error handling

- Invalid framework imports fail atomically and report version, count, parent-join, duplicate-ID, source, or path errors without partial writes.
- Invalid passports identify the rejected field and create no run or mapping.
- Identical evidence replay returns the existing immutable run.
- Hash mismatch or changed content under an existing run identity returns HTTP 409 and records an audit event.
- Missing provider credentials and provider errors return `unavailable` with limitations.
- Insufficient labels, cohorts, media content, or sample size return `insufficient_data`.
- Mapping review with a stale `reviewVersion` returns HTTP 409 and the current decision metadata.
- Unauthorized and cross-organization lookups fail closed without disclosing the other tenant's resource.
- Frontend recoverable errors preserve scope, filters, and unsaved rationale.
- A report request with missing framework version or evidence cutoff fails rather than silently exporting current live data.

## Testing strategy

### Contract tests

- Parse the JSON Schema under Draft 2020-12.
- Validate one golden passport per internal and external adapter.
- Reject unknown properties, malformed hashes, inline raw artifacts, and contradictory capability/result states.
- Verify `runContentHash` stability and sensitivity to subject, input, configuration, threshold, evaluator, suite, and scope changes.
- Verify passport snapshot hashes and revision links change with framework mapping, review, remediation, freshness, or lineage changes while retaining the same run hash.

### Tenant and authorization tests

- Deny cross-organization list, create, read, update, review, approve, import, and report access.
- Verify authenticated actor attribution and mutation roles.
- Run both SQLite and PostgreSQL migration/authorization paths.

### Framework and review tests

- Verify immutable version import, source hash, parent joins, retirement, duplicate import idempotency, and atomic failure.
- Preserve fixture-specific historical AIUC counts without presenting them as current.
- Verify candidate, accepted, rejected, stale-review conflict, and history behaviour.
- Verify readiness with missing, stale, rejected, failed, unavailable, insufficient, and accepted evidence.

### Evaluator tests

- Use deterministic golden fixtures for environmental, tabular fairness, Giskard, MLflow, Fairlearn/AIF360, ModelScan, and garak/PyRIT adapters.
- Verify provider failures fail closed.
- Verify unlabelled media never returns `Not Biased`.
- Verify FairMind-E `no_go` and missing environmental evidence continue to block approval.

### Manifest tests

- Pin organization, system, framework source hash, evidence cutoff, mappings, findings, and decisions.
- Verify identical inputs yield the same manifest hash.
- Verify missing sections remain explicit.
- Verify renderings cite the manifest hash and retain limitations and the non-certification disclaimer.

### Frontend and accessibility tests

- Exercise all six assurance routes with preserved organization/system scope.
- Run evaluation/import → passport → mapping review → finding → remediation → retest → approval → export.
- Verify keyboard-only review, focus, conflict recovery, mobile layout, 200% zoom, and reduced motion.
- Verify capability state and mapping state never rely on color alone.

## Migration and release sequence

1. Create the isolated recovery worktree and record both dirty source states.
2. Integrate the assurance spine and post-base FairMind-E commits.
3. Run migrations and cross-organization tests on SQLite and PostgreSQL.
4. Make the assurance router required.
5. Move the passport contract into the domain and application ingestion port.
6. Remove fabricated modern-bias results and fail-open evaluator states.
7. Connect FairMind-E and one real tabular evaluator.
8. Ship the six-task review flow behind an organization-scoped feature flag.
9. Add external artifact adapters.
10. Add remediation/retest freshness and canonical manifests.
11. Correct repository, website, docs, and UI claims.
12. Redirect overlapping routes after parity.
13. Run the safe Ponytail sequence only against the final live closure.

Rollback is additive through the first release: legacy read paths remain available until passport ingestion, review, and report parity pass. Hard-coded framework constants and duplicate reporting paths are removed only after migration and redirect evidence exists.

## Release acceptance

The recovery release requires this evidence chain:

1. One failing real evaluation or native tool import creates a schema-valid passport.
2. The same source replay returns the existing run with the same `runContentHash` and creates no duplicate run.
3. Changed content under the same run identity returns 409.
4. A reviewer accepts one candidate mapping and rejects another with rationale.
5. Only the accepted current mapping affects the correct organization/system/framework readiness.
6. A finding links to remediation and a clean retest without deleting the failed predecessor.
7. An approval decision preserves unresolved blockers.
8. Two renders from the same pinned manifest cite the same manifest hash.
9. Missing provider, cohort, media, or evidence states never appear as pass, "not biased," accepted, compliant, or certified.
10. Architecture guards, focused backend suites, frontend unit tests, Playwright E2E, production build, and JSON Schema validation pass.

## Decision record

FairMind is system-first with a framework lens and evidence-first with a human review boundary. Organization is the tenant. Framework catalogs are immutable and versioned. Evaluator outputs are framework-neutral Evidence Passports. Automation proposes mappings; reviewers decide. Readiness is transparent and backend-derived. Reports are renderings of a canonical manifest. Existing environmental, risk, remediation, approval, and reporting assets are extended or adapted where they preserve this graph; duplicated and unreachable surfaces are removed only after the recovery closure is verified.

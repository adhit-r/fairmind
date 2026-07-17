# AI Governance Assurance module

FairMind's AI Governance Assurance module is an organization-scoped workbench for governing models, agents, and composite AI systems. It maps versioned framework controls to system assessments, evidence runs, reviewer decisions, findings, and assurance summaries. It supports readiness and review; it does not issue certification or automatically determine legal compliance.

## Product routes

The dashboard keeps one company and AI-system context across six tasks:

| Task | Route | Purpose |
| --- | --- | --- |
| Overview | `/ai-governance` | Shows pinned scope and backend-derived blockers before readiness counts, then persisted approval and environmental governance. |
| AI Systems | `/model-inventory` | Registers models, agents, and composite applications. |
| Frameworks & Controls | `/compliance-dashboard` | Activates an immutable framework version and reviews system control assessments. |
| Evidence & Evaluations | `/evidence` | Inspects artifacts, evaluation provenance, and candidate evidence mappings. |
| Findings | `/risks` | Tracks findings, risks, and linked remediation work. |
| Reports & Assurance | `/reports` | Presents a version-pinned evidence index, decisions, unresolved findings, limitations, report generation, exports, and saved history. |

Users without mutation permission see the same `/reports` route in read-only auditor mode. Authorized users can also request it explicitly with `/reports?mode=auditor`. Auditor mode is a lens on the same tenant-scoped data, not a separate portal or copy.

Legacy bookmarks are temporary redirects:

- `/audit-reports` to `/reports?view=builder`
- `/compliance` and `/compliance/dashboard` to `/compliance-dashboard`
- `/remediation-wizard` to `/remediation?mode=guided`

## Import a framework workbook

Framework imports are administrative operations. Place the `.xlsx` file below the managed import directory configured by `GOVERNANCE_FRAMEWORK_IMPORT_ROOT`. The API accepts a relative path only, confines resolution to that directory, rejects non-Excel files and files larger than 50 MiB, and uses strict validation unless `GOVERNANCE_FRAMEWORK_IMPORT_STRICT=false` is set deliberately.

```bash
export GOVERNANCE_FRAMEWORK_IMPORT_ROOT=/var/lib/fairmind/framework-imports
cp 'AIUC-1 _ April, 2026 version.xlsx' "$GOVERNANCE_FRAMEWORK_IMPORT_ROOT/aiuc-1-april-2026.xlsx"

curl --fail-with-body \
  -H "Authorization: Bearer $FAIRMIND_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"workbookPath":"aiuc-1-april-2026.xlsx"}' \
  "$FAIRMIND_API_URL/api/v1/ai-governance/organizations/$FAIRMIND_ORG_ID/frameworks/import"
```

The importer records the source hash, imported actor, source fields, requirements, controls, and hierarchy. A previously imported workbook hash resolves to the same immutable version rather than silently replacing it. Keep the source workbook outside the repository.

## Activate a framework version

Activation is system-specific and requires an organization owner, administrator, or member with `model:write`. Select the company and AI system, open Frameworks & Controls, choose the required immutable version, and activate it. FairMind creates one assessment for every active control definition in a transaction.

If a system has multiple assigned frameworks, Overview and Reports & Assurance load every catalog's versions, resolve each assignment by its `frameworkVersionId`, and expose a framework-scope selector. Readiness and evidence mapping detail always follow the selected assignment; the UI never pairs an assignment with a framework merely because both occupy the first position in separate API responses.

The Overview and Reports pages do not infer a score from artifact counts. They read the assignment's transparent readiness contract:

- applicable and not-applicable controls;
- accepted, ready-for-review, partial, and not-started states;
- controls missing accepted evidence;
- controls with stale evidence; and
- rejected control assessments (returned by the current API field `blockingFindings`).

If assignment, readiness, or a control-level finding count is absent, the UI says that it is unknown or incomplete. It does not substitute zero.

## Record approval and environmental governance

Overview retains the system approval workflow beside transparent readiness. Users with organization mutation permission can submit a persisted approval request and approve or reject a pending request. Read-only users see the recorded request and latest decision without mutation actions. Rejected-assessment and evidence-gap counts inform the review but are not silently converted into an approval decision.

The Environmental Governance panel continues to read the selected system's environmental-impact packet. It shows energy, carbon, recommendation, provenance, and linked environmental evidence when recorded, and an explicit pending or unavailable state otherwise. Environmental values are not included in the framework readiness numerator unless the active framework's controls and reviewed mappings explicitly cover them.

## Ingest an evidence run

Use the organization- and system-scoped evidence-run endpoint for FairMind evaluations, company integration snapshots, manual evidence envelopes, or third-party results. Send compact metrics, hashes, limitations, and bounded artifact references. Do not send raw model weights, unrestricted prompts, private reasoning traces, or artifact bodies.

```bash
curl --fail-with-body \
  -H "Authorization: Bearer $FAIRMIND_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "sourceType": "fairmind_evaluation",
    "sourceIdentifier": "FairMind Bias Suite",
    "runId": "bias-418",
    "result": "passed_with_limitations",
    "capturedAt": "2026-07-15T10:30:00Z",
    "suiteName": "Bias and subgroup parity",
    "suiteVersion": "2026.07",
    "subjectVersion": "2.4.1",
    "runnerVersion": "fairmind-runner 1.8.0",
    "assuranceSource": "fairmind_internal",
    "limitations": ["Sparse intersectional cohorts were excluded below n=30."],
    "artifactReferences": [{
      "uri": "s3://acme-assurance/bias-418/report.json",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }],
    "controlExternalIds": ["A006.1"]
  }' \
  "$FAIRMIND_API_URL/api/v1/ai-governance/organizations/$FAIRMIND_ORG_ID/systems/$FAIRMIND_SYSTEM_ID/evidence-runs"
```

Run identity is immutable within the selected AI system. Repeating the same envelope is idempotent. Reusing the same run identity with different canonical content returns HTTP 409. The content hash shown in Reports & Assurance is derived from the canonical envelope; it is not a user-entered display value.

Artifact references are limited to 50 pointers, require a 64-character hexadecimal SHA-256 hash, and are size bounded. For third-party evidence, include the assessor identity and an explicit independence assertion. Configure evidence retention outside the envelope according to the organization's retention policy.

## Review evidence mappings

Automation may propose candidate mappings from an evidence artifact to a control assessment, but a candidate does not satisfy a control. A reviewer must accept or reject it in Evidence & Evaluations and record a rationale when appropriate.

Mapping review uses optimistic concurrency through `reviewVersion`. A stale review receives HTTP 409; reload the mapping, inspect the newer decision, and decide again. FairMind retains review actor, timestamp, state, rationale, and prior review history. Accepted mappings may contribute to readiness only while the evidence is current and the control's other requirements are met.

## Read an assurance summary

Reports & Assurance pins the company, AI system, framework name, immutable version, catalog source hash, and evidence period before presenting any aggregate. Its evidence index includes the complete evidence content hash and evaluation versions. It separates:

- backend readiness counts;
- unresolved and incompletely reported findings;
- accepted or rejected reviewer decisions;
- candidate suggestions, which are not decisions;
- evaluation limitations; and
- evidence-run history retained for the scoped system.

Below the assurance summary, the Report Studio keeps the existing operational-report workflow reachable on `/reports`: authorized builders can generate a stored governance snapshot, preview it, revisit saved report history, and export JSON or PDF. Auditor mode can preview and export saved reports but cannot generate a new snapshot. The operational preview is kept separate because its legacy system-readiness field is not the framework readiness calculation above.

The assurance summary is a live review surface, not a signed assurance opinion. Preserve exported evidence, saved reports, and decision records under the organization's records policy if an immutable review package is required.

## Claim boundaries

Permitted language includes:

- `AIUC-1 readiness`;
- `evidence mapped to AIUC-1 April 2026 controls`;
- `FairMind-collected supporting evidence`; and
- `ready for reviewer or auditor review`.

Do not state that an organization, system, or model is certified, automatically compliant, or has met a framework solely because the module contains mappings or shows accepted controls. Official certification remains a decision of the applicable certification body, under its own scope and process.

## Operational checks

Run the focused assurance regression suites before deployment:

```bash
cd apps/backend
uv run pytest \
  tests/test_governance_assurance_models.py \
  tests/test_framework_catalog_service.py \
  tests/test_governance_assurance_routes.py \
  tests/test_governance_evidence_runs.py -q

cd ../..
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh

cd apps/frontend
bun test src/lib/api/hooks/useGovernanceAssurance.test.ts
./node_modules/.bin/tsc --noEmit --pretty false
npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1
npm run build
```

The repository's recorded baseline includes an unrelated backend collection failure in `test_fairness_evidence_profile_route.py`: `ModuleNotFoundError: No module named 'api.models'` when run in the backend package context. The focused assurance suites do not import that compatibility path. Treat a change to that baseline as separate work; do not suppress feature-test failures under the baseline note.

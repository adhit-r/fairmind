# FairMind Recovery Audit — 18 July 2026

## Decision

The user requested autonomous execution of the recovery work. The selected direction is a vendor-neutral assurance evidence compiler, not another generic GRC suite and not a proprietary test laboratory.

FairMind should let an engineer bring the output of a real model, data, LLM, agent, security, provenance, or environmental test; bind it to the tested subject and run configuration; route proposed framework mappings through accountable review; and export a reproducible evidence packet. A technical result may support a governance conclusion. It does not itself prove legal compliance or certification.

This audit is a current-state and recovery decision record. It is based on the active repository, the sibling `fairmind-ai-governance-assurance` worktree, official framework sources, and current vendor documentation. Vendor capability statements below are vendor claims, not independent product-test results.

## Executive finding

FairMind has broad surface area but few evidence-grade vertical slices. Environmental governance is the strongest implemented slice. The current Evidence Hub stores searchable metadata but lacks an immutable evaluation-run envelope, artifact digests, evaluator versions, reviewed control mappings, and framework-version provenance. Several visible product claims exceed the live implementation: the principal tabular-bias route has no backend endpoint, the modern LLM-bias screen fabricates exportable results, multimodal analysis uses caller-supplied labels rather than media content, and Model DNA returns static mock provenance.

The recovery should integrate the already-built assurance spine from `/Users/adhi/axonome/fairmind-ai-governance-assurance` with the post-divergence FairMind-E work. Both worktrees are dirty and divergent, so integration must happen in a new recovery worktree after their state is recorded. This audit does not authorize a merge of either dirty worktree.

## Product job

FairMind's primary job is to answer five defensible questions:

1. What exactly was tested?
2. Which model, agent, dataset, prompt set, configuration, and version were in scope?
3. Which evaluator, metric, threshold, environment, and artifact produced the result?
4. Who reviewed the evidence and its proposed control mappings?
5. Which versioned governance obligations may reuse the accepted evidence, with what limitations?

The unit of value is an Evidence Passport with a visible chain of custody, not a readiness percentage.

## Current capability truth

| Capability | Current truth | Primary paths | Recovery disposition |
| --- | --- | --- | --- |
| Environmental governance | Working, bounded vertical slice with provenance-capped confidence, ENV-1–ENV-6 coverage, versioned assessments, mirrored evidence, risk/remediation creation, approval gates, connectors, and a CSRD/ESRS E1-shaped export. Thresholds remain provisional and the paper comparison uses fixtures. | `apps/backend/src/domain/environmental/`; `apps/backend/src/application/services/environmental_service.py`; `apps/backend/src/api/routers/environmental.py`; `apps/backend/src/api/routers/approvals.py`; `apps/backend/src/infrastructure/db/database/governance_models.py`; `apps/backend/tests/test_environmental*.py`; `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`; `apps/frontend/src/lib/api/hooks/useAIGovernance.ts` | Preserve as the reference adapter and connect its assessment versions and artifacts to the canonical evidence-ingestion port. Keep environmental claims bounded to recorded provenance and provisional thresholds. |
| Governance systems and workspaces | CRUD, lifecycle, risks, policy, approvals, remediation, and evidence exist, but current records are not consistently organization-scoped and overlap older inventory models. | `apps/backend/src/api/routers/ai_governance.py`; `apps/backend/src/infrastructure/db/database/governance_models.py`; `apps/frontend/src/app/(dashboard)/ai-governance/page.tsx`; `apps/frontend/src/app/(dashboard)/model-inventory/page.tsx` | Adopt the organization-scoped system, framework, assessment, evidence-run, and mapping foundation from the assurance worktree. |
| Evidence Hub | Searchable evidence, tags, folders, links, and metadata collection exist. "Upload" is JSON metadata collection; there is no persisted file body, artifact digest, immutable run, evaluator version, or reviewed mapping. Freshness is a universal 90-day rule. | `apps/backend/src/api/routers/ai_governance.py`; `apps/frontend/src/app/(dashboard)/evidence/page.tsx`; `apps/frontend/src/lib/api/hooks/useEvidence.ts` | Reframe as Evidence & Evaluations. Ingest bounded artifact references plus hashes, calculate evidence-specific freshness, and expose review history. |
| Tabular and classic bias | Statistical and fairness services exist, including causal, counterfactual, intersectional, and temporal methods. The main `/bias` screen calls `/api/v1/bias/analyze/dataset`, which is not mounted by the backend. Results from other engines are not evidence runs. | `apps/frontend/src/app/(dashboard)/bias/page.tsx`; `apps/frontend/src/lib/api/endpoints.ts`; `apps/backend/src/application/services/comprehensive_bias_detection_service.py`; `apps/backend/src/application/services/advanced_bias_detection_service.py`; `apps/backend/src/api/routers/advanced_bias_detection.py`; `apps/backend/src/application/services/bias_testing_library.py` | Wire one real, tested evaluator to the canonical contract or mark the launcher `unavailable`. Do not leave a visible broken action. |
| LLM bias | A provider-backed judge and deterministic/statistical services exist, but outputs are transient. `/modern-bias` creates a hard-coded "mock comprehensive evaluation" in the browser and can export it. An unused domain judge can return mock `PASS` on provider failure. | `apps/backend/src/api/routers/llm_judge.py`; `apps/backend/src/application/services/llm_as_judge_service.py`; `apps/backend/src/domain/bias/services/llm_judge_service.py`; `apps/frontend/src/app/(dashboard)/llm-judge/page.tsx`; `apps/frontend/src/app/(dashboard)/modern-bias/page.tsx` | Remove fabricated results and fail closed. Persist prompt-set hash, evaluator/prompt version, provider/endpoint, thresholds, limitations, and bounded output artifacts. Missing credentials produce `unavailable`, never pass. |
| Image and multimodal bias | Metadata-only prototype. It does not fetch or decode image, audio, or video content. Request labels and response casing are inconsistent; insufficient data can be rendered as "Not Biased". | `apps/backend/src/api/routers/multimodal_bias_detection.py`; `apps/backend/src/application/services/multimodal_bias_detection_service.py`; `apps/frontend/src/app/(dashboard)/multimodal-bias/page.tsx`; `apps/frontend/src/lib/api/hooks/useMultimodalBias.ts` | Correct the contract and label it `metadata_only`. Return `insufficient_data` when media or labels cannot support a result. Add actual media analysis only behind a separately validated worker and gold-set evaluation. |
| Compliance checks | One active engine performs 24 presence checks over caller-declared EU AI Act, GDPR, DPDP, ISO 42001, and NIST fields. This is gap prompting, not evidence-backed compliance assessment. Multiple overlapping compliance routers also exist. | `apps/backend/src/api/routers/compliance_audit.py`; `apps/backend/src/domain/compliance/services/compliance_audit_engine.py`; `apps/backend/src/api/routers/compliance_check.py`; `apps/backend/src/api/routers/compliance_reporting.py`; `apps/backend/src/api/routers/india_compliance.py`; `apps/frontend/src/app/(dashboard)/compliance-dashboard/page.tsx` | Rename the capability as declared-context gap review. Feed accepted evidence mappings into control assessments; never convert field presence into compliance. |
| Frameworks and controls | EU AI Act, ISO 42001, and NIST AI RMF are hard-coded in the governance router. The current branch has no immutable catalog versions or current AIUC catalog. | `apps/backend/src/api/routers/ai_governance.py` | Integrate immutable framework versions, source hashes, system assignments, control assessments, and human-reviewed evidence mappings from the assurance worktree. Revalidate AIUC source counts and version at integration time. |
| Reports and exports | Three disconnected paths produce persisted governance snapshots, server PDFs/DOCX from caller-supplied results, and client PDFs/JSON. None emits one canonical evidence manifest. Requested framework/date/section filters do not reliably determine snapshot contents. | `apps/backend/src/api/routers/ai_governance.py`; `apps/backend/src/api/routers/reports.py`; `apps/frontend/src/app/(dashboard)/audit-reports/page.tsx`; `apps/frontend/src/app/(dashboard)/reports/page.tsx`; `apps/frontend/src/lib/export/backend-report-generator.ts`; `apps/frontend/src/services/reports-service.ts` | Build one server-side canonical assurance manifest pinned to organization, system, framework source hash, evidence cutoff, and evidence content hashes. PDF and DOCX are renderings, not independent truth. |
| AI BOM fairness profile | Useful reviewer-facing transformation of BOM metadata, bias results, evidence, remediation, and unknowns. It does not independently evaluate a system and is disconnected from central controls. | `apps/backend/src/api/routers/real_ai_bom.py`; `apps/backend/src/application/services/fairness_evidence_profile_service.py`; `apps/frontend/src/lib/api/hooks/useAIBOM.ts`; `research/aibom-fairness-evidence/` | Add an adapter that records the input BOM hash, transformation version, limitations, and profile artifact in the same evidence graph. |
| Model DNA and provenance | Static mock response containing a fixed training run, architecture, and parameter count. | `apps/backend/src/api/routers/provenance.py`; `apps/frontend/src/app/(dashboard)/model-dna/page.tsx`; `apps/frontend/src/app/(dashboard)/provenance/page.tsx` | Remove from production navigation or mark `unavailable` until backed by a real provenance source. Do not admit the mock response as evidence. |
| ML application | Thin sample package; it is not a deployed evaluation worker. Most algorithms live in backend services. | `apps/ml/pipelines/data_processing.py`; `apps/ml/pipelines/model_training.py`; `apps/ml/visualizations/data_distribution.py`; `apps/ml/mlflow_config.py` | Do not describe `apps/ml` as a complete test lab. Use tool-output adapters before creating another runtime subsystem. |

The frontend currently contains 54 dashboard `page.tsx` routes while `apps/frontend/src/lib/constants/navigation.ts` exposes a smaller, inconsistent subset. Consolidation must preserve useful deep links through redirects while reducing the product to six assurance tasks.

## Market and tool evidence matrix

Actual-test evidence is no longer a unique claim. The opening is the portable chain of custody between concrete evaluator output, accountable review, remediation, and reusable framework evidence.

| Product or tool | Current job-to-be-done and evidence claim | FairMind gap or integration opportunity | Primary source |
| --- | --- | --- | --- |
| Credo AI | Inventory, policy workflow, approvals, runtime governance, risk scores, red-team/drift results, traces, and audit-ready documentation | Compete on open portability and replayability across external test tools and governance platforms | [Credo AI product](https://www.credo.ai/product) |
| Holistic AI | Inventory, bias/robustness/efficacy/privacy testing, red-teaming, enforcement, audit trails, version history, assurance reports, and remediation | Closest broad competitor; differentiate with an open evidence contract, bring-your-own evaluators, and multi-framework reuse | [Holistic AI governance platform](https://www.holisticai.com/ai-governance-platform) |
| IBM watsonx.governance | Model and prompt lifecycle governance with AI Factsheets, lineage, versions, evaluation metrics, monitoring, and downloadable reports | Compile evidence across IBM and non-IBM subjects, tools, and environments | [IBM model governance](https://www.ibm.com/products/watsonx-governance/model-governance) |
| Microsoft Purview and Azure Responsible AI | Prompt/response audit metadata, referenced-file sensitivity, model performance/fairness analysis, and PDF scorecards | Join operational, data-governance, and evaluation evidence across clouds; do not depend on an Azure-only dossier | [Purview for AI](https://learn.microsoft.com/en-us/purview/ai-microsoft-purview), [Responsible AI scorecard](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-responsible-ai-scorecard?view=azureml-api-2) |
| Fiddler | Runtime monitoring, guardrails, fairness, drift, PII/toxicity signals, audit trails, and reports | Convert monitoring events into durable, reviewable evidence rather than control-plane-only records | [Fiddler AI GRC](https://www.fiddler.ai/ai-governance-risk-compliance) |
| Arthur | Agent discovery/governance, traces, continuous evaluations, guardrails, benchmarks, fairness, and drift | Broaden agent-first runtime evidence into portable model/data/security evidence and framework packets | [Arthur Discover and Govern](https://www.arthur.ai/discover-and-govern-agents), [Arthur Bench](https://www.arthur.ai/product/bench) |
| WhyLabs | Privacy-preserving statistical profiles, monitoring configuration, anomalies, security events, and audit trails | Add intended-use scope, versions, thresholds, review, remediation, and framework semantics | [WhyLabs documentation](https://docs.whylabs.ai/docs/) |
| Giskard | Agent/model vulnerability scans with failure conversations, verdicts, reusable JSON suites, JUnit output, and exact reruns | High-value adapter input; add judge provenance, reviewer confirmation, remediation, and control mappings | [Giskard vulnerability scans](https://docs.giskard.ai/oss/solutions/scan-vulnerabilities) |
| ModelScan | Serialized-model supply-chain scanning with severity findings, JSON reports, report files, and CI exit codes | Bind narrow security findings to subject lineage, ownership, remediation, rerun, and assurance controls | [Protect AI ModelScan](https://github.com/protectai/modelscan) |
| MLflow, Fairlearn, AIF360, and Evidently | Run tracking, metrics, plots, thresholds, subgroup analyses, mitigations, snapshots, and monitoring history | Normalize existing artifacts instead of rebuilding their evaluators | [MLflow evaluation](https://mlflow.org/docs/latest/ml/evaluation/), [Fairlearn](https://fairlearn.org/), [AIF360](https://github.com/Trusted-AI/AIF360), [Evidently](https://docs.evidentlyai.com/docs/library/overview) |
| garak and PyRIT | LLM probes, attack conversations, scores, logs, and run histories | Preserve attack scope, target version, configuration, review, exceptions, remediation, and clean reruns | [garak](https://github.com/NVIDIA/garak), [PyRIT](https://github.com/microsoft/PyRIT) |

## Framework evidence expectations

These are product-design inputs, not legal advice or certification determinations.

| Framework | Evidence expectation relevant to FairMind | Product boundary and source |
| --- | --- | --- |
| EU AI Act | High-risk providers need lifecycle risk-management records, data-governance documentation, predefined test metrics and thresholds, up-to-date technical documentation, automatic logs, accuracy/robustness/cybersecurity evidence, quality-management records, and documented post-market monitoring. Annex IV ties system description, design, data, performance, risk, lifecycle change, and monitoring information together. | FairMind may produce traceable technical-documentation contributions and evidence indexes. It does not determine conformity. Use the consolidated [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689) and the [current Council implementation timeline](https://www.consilium.europa.eu/en/policies/artificial-intelligence-act/timeline-artificial-intelligence/). The timeline lists 2 December 2027 for stand-alone high-risk systems and 2 August 2028 for high-risk systems embedded in regulated products. |
| ISO/IEC 42001 | An AI management system establishes, implements, maintains, and continually improves policies and processes. Supporting records concern responsibility, risk and opportunity management, operational control, monitoring, internal audit, corrective action, and improvement. | A passport supports management-system records; it is not ISO certification. Public source: [ISO/IEC 42001](https://www.iso.org/standard/42001). |
| ISO/IEC 23894 | Organizations integrate AI-specific risk management into activities and functions, including context, risk criteria, assessment, treatment, monitoring, and review. | Link technical evidence to risk and treatment records without reproducing proprietary standard text. Public source: [ISO/IEC 23894](https://www.iso.org/standard/77304.html). |
| NIST AI RMF 1.0 and GenAI Profile | GOVERN, MAP, MEASURE, and MANAGE outcomes call for documented context, provenance, TEVV, metrics, limitations, incidents, dependencies, changes, and follow-up. The GenAI Profile adds lineage, test/evaluation content flow, ground-truth comparison, incident, and change-management emphasis. | Store the framework/profile version with each mapping because AI RMF 1.0 is being revised. The Playbook is optional guidance, not a compliance checklist. Sources: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), [AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/), [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1). |
| AIUC-1 | The current private certification standard describes 50 requirements across six principles, with Core and Supplemental controls and a Statement of Applicability. Its evidence guidance covers legal policies, technical implementation, operational practices, and third-party evaluations. Third-party reports should record scope/taxonomy, methodology, findings, assessor qualifications where relevant, remediation timing, and improvement tracking; technical testing is expected quarterly. | Position FairMind as audit-readiness and evidence preparation, not the certifier. Store the catalog source and version because AIUC-1 changes quarterly. The current release was published 15 July 2026. Sources: [AIUC-1 scope](https://www.aiuc-1.com/scoping), [changelog](https://www.aiuc-1.com/changelog), [third-party evidence](https://www.aiuc-1.com/evidence/third-party), [certificate process](https://www.aiuc-1.com/learn/certificate). The sibling branch's April 2026 workbook importer expected 51 requirements and 135 controls; those historical workbook counts must not be presented as the current public standard count. |

## Canonical assurance graph

The recovery architecture has two connected chains:

`Organization → Workspace → AI System → Framework Assignment → Control Assessment`

`Evaluation Run → Evidence Artifact → Candidate Mapping → Reviewer Decision → Finding/Risk → Remediation → Retest → Approval → Assurance Package`

Rules:

- Every tenant-owned identifier is scoped by `organization_id` at repository and authorization boundaries.
- Framework definitions and source hashes are immutable; applicability, owner, status, and review belong to the system-specific control assessment.
- Every evaluator writes through one evidence-ingestion application port. Evaluators never mutate readiness, approvals, or reports directly.
- Candidate mappings do not satisfy controls. Only an accepted reviewer decision may contribute evidence coverage.
- Failed, rejected, stale, superseded, and error runs remain in history.
- Artifact metadata lives in the governance database; artifact bodies remain in controlled storage and are referenced by bounded URI plus SHA-256 digest.
- The immutable evaluation-run hash remains stable across review. Each exported passport review snapshot has a monotonic revision and previous-revision hash.
- A canonical server-side JSON manifest is the report truth. PDF and DOCX are deterministic renderings of that manifest.

The normative Evidence Passport exchange contract is `docs/product/evidence-passport.schema.json`.

## Information architecture

Consolidate the dashboard around the selected organization and AI system:

1. **Overview** — `/ai-governance`: blockers, capability truth, current decisions, and bounded readiness.
2. **AI Systems** — `/model-inventory`: models, agents, and composite applications.
3. **Frameworks & Controls** — `/compliance-dashboard`: immutable versions, assignments, control assessments, and reviewed evidence coverage.
4. **Evidence & Evaluations** — `/evidence`: runs, passports, artifacts, provenance, limitations, mapping review, and rerun comparison.
5. **Findings** — `/risks`: finding, risk, remediation, retest, and approval chain.
6. **Reports & Assurance** — `/reports`: pinned manifest, evidence index, limitations, unresolved findings, decisions, history, and exports.

Overlapping routes should redirect only after parity and browser checks. The selected organization/system scope must survive every route and export.

## Claim corrections

Replace or prohibit these claims until the stated evidence exists:

| Current or risky claim | Required bounded wording |
| --- | --- |
| "Production-ready AI governance" | "AI assurance evidence workbench under active recovery; capability state shown per evaluator." |
| "AIUC-1 compliant", "meets AIUC-1", or "certified" | "Evidence mapped to [version] AIUC-1 controls" or "AIUC-1 readiness for reviewer assessment." |
| "EU AI Act compliant" | "Technical evidence and documentation support for selected EU AI Act obligations; legal applicability and conformity remain external decisions." |
| "Image bias analysis" for the current multimodal route | "Metadata-based group distribution analysis; media content is not evaluated." |
| "Not Biased" when labels, cohorts, providers, or thresholds are missing | `insufficient_data` or `unavailable`, with the missing input stated. |
| "Comprehensive LLM evaluation" from `/modern-bias` | Remove the fabricated path. Show only persisted results from a named, versioned evaluator. |
| "Upload evidence" when only JSON metadata is collected | "Register evidence metadata" until controlled artifact storage exists. |
| Model DNA training lineage from static mock data | Remove from production navigation or label `unavailable`. |
| A readiness percentage without numerator, denominator, exclusions, freshness, and blockers | Show those components and call the result `readiness`, never conformity. |

Every evaluator exposes exactly one capability state: `validated`, `metadata_only`, `external_provider`, `unavailable`, or `insufficient_data`.

## Prioritized recovery gaps

### P0 — trust and safety of the product claim

1. Enforce organization scope for systems, evidence, mappings, approvals, and reports.
2. Integrate immutable framework versions, source hashes, evidence-run identities, content hashes, and reviewed mappings from the assurance worktree.
3. Remove the browser-generated `/modern-bias` result and the mock-pass fallback.
4. Repair `/bias` with one real contract or mark it unavailable.
5. Normalize multimodal contracts and prevent insufficient evidence from appearing as "Not Biased".
6. Make evidence immutable and artifact-integrity-aware.
7. Produce reports from a pinned canonical manifest.

### P1 — reliable recovery foundation

1. Reconcile the assurance worktree's 27-commit line with the current branch's three post-merge-base FairMind-E commits in an isolated worktree, preserving both dirty states.
2. Make the assurance router required rather than silently optional.
3. Consolidate the touched governance path onto one SQLAlchemy/session lifecycle and migrations; remove request-time `create_all`, `ALTER TABLE`, and `CREATE TABLE IF NOT EXISTS`.
4. Add environmental and one real tabular or LLM adapter to the evidence-ingestion port.
5. Derive readiness on the backend from applicability, accepted mappings, freshness, unresolved findings, policies, and approvals.
6. Preserve package-root and repository-root validation until compatibility symlinks are deliberately retired.

### P2 — coherence and maintainability

1. Consolidate 54 dashboard routes into the six task destinations with tested redirects.
2. Remove stale endpoint constants and duplicate policy, approval, evidence, compliance, remediation, and report families after closure tests.
3. Add artifact-import adapters for Giskard, MLflow, Fairlearn/AIF360, ModelScan, and garak/PyRIT before building new evaluator engines.
4. Connect the AIBOM transformation and environmental exporter to the canonical manifest.
5. Retire mock provenance and placeholder services.
6. Execute the deletion sequence in `docs/product/PONYTAIL_AUDIT_2026-07-18.md` only after the new assurance closure is green.

## Recovery acceptance boundary

The recovery is credible when one real evaluation can be run or imported, produces the same immutable run hash when replayed unchanged, rejects changed content under the same run identity, displays its limitations and capability state, receives an independent mapping decision, creates a finding and remediation when configured, links a clean retest without erasing the failure, and exports the same framework-pinned manifest for the same evidence cutoff.

No missing provider key, missing cohort, absent media content, request error, or empty evidence set may produce a pass, "not biased," accepted control, compliance claim, or certificate.


# FairMind feature status

Checked against `main` on 2026-11-08. Status values:

- **Working**: reachable in the UI (or on a supported surface) and backed by a mounted, real endpoint.
- **Partial**: some of it works, but part is stubbed, placeholder, unreachable or misleading.
- **BE only**: the backend works, but no reachable frontend uses it.
- **FE only**: the frontend calls an endpoint that does not exist, is not mounted, or has a different path or shape.
- **Planned**: not built, quarantined, or labelled Coming soon.

The live navigation is the AppShell LIBRARY list plus the system-file stage spine (`apps/frontend/src/components/layout/AppShell.tsx:21-29`). `apps/frontend/src/lib/constants/navigation.ts` is imported only by tests, so pages listed only there cannot be reached.

## Inventory and lifecycle

| Feature | Status | Evidence |
|---|---|---|
| Register a system (onboarding, applicability) | Working | `apps/frontend/src/app/(dashboard)/onboard/page.tsx`, `apps/frontend/src/components/workflow/SystemContext.tsx:213-227`, `apps/backend/api/routes/applicability.py` |
| Discover systems from MLflow, GitHub, Hugging Face and promote them | Working | `apps/backend/api/routes/integrations.py:315` |
| System file `/systems/[id]` (Onboard to Operate stages) | Working | `apps/frontend/src/app/(dashboard)/systems/[id]/page.tsx`, `apps/frontend/src/lib/api/hooks/useSystemFile.ts` |
| Live target connection (TargetPanel, platform connections) | Working | `apps/backend/api/routes/packs.py`, `apps/backend/api/routes/platform_connections.py` |
| Findings / risk register `/risks` | Working | `apps/frontend/src/lib/api/hooks/useRisks.ts:58-67` |
| Dashboard estate | Working | `apps/frontend/src/app/(dashboard)/dashboard/page.tsx` |
| Edit, re-tier or archive a system | Planned | no PATCH/DELETE on `/systems/{id}` in `apps/backend/api/routes/ai_governance.py` |
| Risk taxonomy (IBM, MIT, OECD) | Partial (data model only, no API or UI) | `apps/backend/src/infrastructure/db/database/risk_taxonomy_models.py:40` |
| AI BOM | Planned (quarantined) | `apps/backend/api/routes/real_ai_bom.py:20-38`, `apps/frontend/src/app/(dashboard)/ai-bom/page.tsx` |
| Provenance | Planned (routes return 501) | `apps/backend/api/routes/provenance.py:12-21` |
| `/model-inventory` | Partial (works, unreachable, duplicates dashboard) | `apps/frontend/src/app/(dashboard)/model-inventory/page.tsx` |
| Ask about a system (dashboard input), measured VerdictExplainer checks | Planned (labelled Coming soon) | `apps/frontend/src/app/(dashboard)/dashboard/page.tsx:132-137`, `apps/frontend/src/app/(dashboard)/systems/[id]/VerdictExplainer.tsx:268-271` |

## Bias and fairness

| Feature | Status | Evidence |
|---|---|---|
| System fairness runs, release gate, seals, clause map, attestations | Working | `apps/backend/api/routes/fairness_runs.py`, `apps/frontend/src/lib/api/hooks/useSystemFile.ts:414-519` |
| Bias Detection page `/bias` (Assess nav, "Bias test" action) | FE only (posts to missing `/api/v1/bias/analyze/dataset`) | `apps/frontend/src/lib/api/endpoints.ts:56`, `apps/frontend/src/lib/api/hooks/useBiasDetection.ts:19-22` |
| bias-detection `/test/fairness`, `/test/weat`, templates, libraries | BE only | `apps/backend/api/routes/bias_detection.py:223,273,444,473` |
| bias-detection `/test/image`, `/test/text` | Partial (placeholder 0.0 scores) | `apps/backend/src/application/services/bias_testing_library.py:368-385,429-445` |
| LLM-as-Judge batch evaluation `/llm-judge` | Partial (works, not in live nav, uses server env keys) | `apps/backend/api/routes/llm_judge.py:226`, `apps/backend/src/application/services/llm_as_judge_service.py:255-290` |
| LLM judge single and multi-judge | BE only | `apps/backend/api/routes/llm_judge.py:158,308`, `apps/frontend/src/lib/api/hooks/useLLMJudge.ts:162,312` |
| `/llm-testing` | FE only (orphan; calls template scorer and missing v2 route) | `apps/frontend/src/app/(dashboard)/llm-testing/page.tsx:108-165` |
| Advanced bias (causal, counterfactual, intersectional, adversarial) | BE only (FE request shape mismatch) | `apps/backend/api/routes/advanced_bias_detection.py:33-58`, `apps/frontend/src/lib/api/hooks/useAdvancedBias.ts:20-25` |
| `/benchmarks`, `/realtime` | FE only (no backend) | `apps/frontend/src/lib/api/endpoints.ts:269-286` |
| Multimodal bias, modern LLM bias, explainability studio | Planned (routers unmounted) | `apps/backend/api/main.py:548-551` |
| Remediation tasks `/remediation` | Working | `apps/backend/api/routes/ai_governance.py:2639,2663,2743` |
| Remediation wizard | Planned (ComingSoon; nav redirects to task list) | `apps/frontend/next.config.js:15-19`, `apps/frontend/src/app/(dashboard)/remediation-wizard/page.tsx` |
| Environmental impact snapshot (read) | Working | `apps/backend/api/routes/environmental.py:172` |
| Environmental assessment, approval, export | BE only (UI tells users to run one) | `apps/backend/api/routes/environmental.py:147-459`, `apps/frontend/src/app/(dashboard)/systems/[id]/VerdictExplainer.tsx:39,131` |
| Fairness documentation generator | BE only (page is ComingSoon) | `apps/backend/api/routes/compliance_reporting.py:212-230` |

## Compliance and frameworks

| Feature | Status | Evidence |
|---|---|---|
| Frameworks library, packs, bundles, journeys `/compliance` | Working | `apps/backend/api/routes/packs.py` |
| Workflow runs, decisions, step output, agent drafting | Working | `apps/frontend/src/app/(dashboard)/compliance/runs/[runId]/page.tsx:226`, `apps/backend/api/routes/packs.py:1148` |
| Workflow drafts and publish | Working | `apps/frontend/src/lib/api/endpoints.ts:338-341` |
| Workflow version history | BE only | `apps/backend/src/api/routers/packs.py:1503-1506` |
| Catalogue evaluations (61 of 109 runnable) | Partial | `apps/backend/src/api/routers/pack_catalogue_data/catalogue.json`, `apps/backend/src/application/services/evaluation_results.py:73-79` |
| Policy center `/policies` | Working | `apps/backend/api/routes/policy_center.py` |
| Policy release gate on the system page | BE only | `apps/backend/api/routes/policy_center.py:170-175` |
| Frameworks and controls `/compliance-dashboard` | Working | `apps/backend/api/routes/governance_assurance.py` |
| Compliance automation (schedules, violations, reports) | Partial (orphan page, unwired buttons, empty reports list, hardcoded Pass rows) | `apps/frontend/src/app/(dashboard)/compliance-automation/page.tsx:251-425`, `apps/backend/src/domain/compliance/services/compliance_automation_service.py:146-155` |
| India compliance API (NITI Aayog, RBI, DPDP) | BE only | `apps/backend/api/routes/india_compliance.py:62-634` |
| DPDP and GDPR as catalogue frameworks | Planned | `apps/backend/src/api/routers/pack_catalogue_data/catalogue.json` |
| Org audit-report export (JSON, CSV, PDF) | BE only (only caller is a redirected page) | `apps/backend/api/routes/compliance.py:74,180`, `apps/frontend/next.config.js:11-13` |
| compliance_check, compliance_reporting, compliance_audit routers | BE only (no callers, some placeholder output) | `apps/backend/api/main.py:530-531,544`, `apps/backend/api/routes/compliance_reporting.py:246-263` |

## Assurance and evidence

| Feature | Status | Evidence |
|---|---|---|
| Inspection packs: create, download, share, revoke | Working | `apps/backend/api/routes/evidence_packs.py:94-179` |
| Public pack verification `/verify/[packId]` and `fairmind verify` | Working | `apps/frontend/src/app/verify/[packId]/page.tsx:36`, `apps/cli/fairmind_cli/main.py:344` |
| Evidence hub `/evidence` | Working | `apps/frontend/src/app/(dashboard)/evidence/page.tsx` |
| Evidence-to-control mapping and four-eyes review | Working | `apps/backend/src/api/routers/governance_assurance.py:897,918` |
| Assurance report studio `/reports` | Working | `apps/backend/src/api/routers/ai_governance.py:2852` |
| Evidence Passport ingest | BE only (hook has no UI caller) | `apps/frontend/src/lib/api/hooks/useGovernanceAssurance.ts:526-537` |
| Legacy evaluation plans and runs `/tests` | Partial (plans work; run preparation always disabled) | `apps/backend/src/application/services/legacy_evaluation_feature_gates.py:19-27` |
| Assurance V2 workbench (plans, runs, evidence admission, decisions) | BE only (default off) | `apps/backend/src/api/routers/evaluation_workbench.py:839-1783` |
| Imported evidence upload | BE only (default off) | `apps/backend/src/api/routers/imported_evidence.py:115-119` |
| Evaluator catalog | Partial (list only, behind flag) | `apps/backend/src/api/routers/evaluator_catalog.py:229-384` |
| Trust administration (issuers, keys, policies) | BE only (default off) | `apps/backend/src/api/routers/trust_issuer_routes.py:34` |
| Bias-evaluation PDF and DOCX reports | BE only | `apps/backend/src/api/routers/reports.py:62,153,244` |
| `/lifecycle` | FE only (posts to missing route) | `apps/frontend/src/lib/api/hooks/useLifecycle.ts:29-35` |

## Monitoring

| Feature | Status | Evidence |
|---|---|---|
| Monitoring snapshots pushed by CLI and SDK, shown on the system page | Working | `apps/backend/api/routes/fairness_runs.py:452,551-562`, `apps/cli/fairmind_cli/main.py:217` |
| `/monitoring` page (Operate stage "Monitoring" button) | Partial (placeholder zeros, audit-log chart, inert switches) | `apps/backend/api/routes/database.py:321-332,362-364` |
| Per-model monitoring API, alert rules, WebSocket | BE only (in-memory) | `apps/backend/api/routes/monitoring.py:161-453` |
| `/alerts`, `/status` | Partial (always empty or constant) | `apps/frontend/src/app/(dashboard)/alerts/page.tsx:29`, `apps/backend/api/routes/ai_governance.py:1138-1145` |
| Realtime assurance | Planned | `docs/STATUS.md` |

## Platform (auth, organizations, settings)

| Feature | Status | Evidence |
|---|---|---|
| Login, signup, refresh, logout, password reset | Working | `apps/backend/src/api/routers/auth.py:394,425` |
| Org switcher, member list, member remove, roles list | Working | `apps/backend/src/api/routers/org_management.py:264` |
| Member invite | Partial (row created, email never sent) | `apps/backend/src/api/routers/org_management.py:501`, `apps/backend/src/infrastructure/email/resend_service.py:41` |
| Invitation accept `/invitations/[token]` | FE only (wrong path) | `apps/frontend/src/lib/api/endpoints.ts:368-370` |
| Org settings form | FE only | `apps/frontend/src/app/(dashboard)/org-admin/settings/page.tsx:47,79` |
| Org audit log page | FE only (wrong path and key) | `apps/frontend/src/app/(dashboard)/org-admin/audit-log/page.tsx:39-47` |
| Role delete | FE only | `apps/frontend/src/app/(dashboard)/org-admin/roles/page.tsx:53` |
| Member role change, custom role creation | BE only | `apps/backend/src/api/routers/org_management.py:772,989` |
| Create an organization after signup | Planned | `apps/frontend/src/lib/api/endpoints.ts:358-360` |
| Organization pages in the sidebar | Planned (not in AppShell) | `apps/frontend/src/components/layout/AppShell.tsx:21` |
| `/admin/users`, `/admin/roles` | Partial (always empty; static table) | `apps/backend/src/api/routers/auth.py:824-850`, `apps/frontend/src/app/(dashboard)/admin/roles/page.tsx:19` |
| Change password while signed in | Planned (button only re-saves preferences) | `apps/frontend/src/app/(dashboard)/settings/page.tsx:220,243` |
| User preferences | Partial (in memory; autoRefresh key mismatch) | `apps/backend/src/domain/settings/services/settings_service.py:19,32` |
| SSO (Authentik, opt-in) | Partial (redirect URI fixed to `/callback`) | `apps/frontend/src/lib/api/hooks/useAuthentik.ts:100` |
| Access requests (admin review) | Partial (review works; nothing submits) | `apps/backend/api/routes/registration.py:49` |
| API keys | BE only | `apps/backend/src/api/routers/auth.py:674,739,771` |
| Approval workflows and decision history | BE only | `apps/backend/api/routes/ai_governance.py:1640,1678,1714,1998` |
| Platform audit log `/admin/audit-log` | Partial (status column always empty) | `apps/frontend/src/app/(dashboard)/admin/audit-log/page.tsx:49,71` |

## Surfaces and docs

| Feature | Status | Evidence |
|---|---|---|
| CLI (`gate`, `test`, `monitor`, `systems`, `verify`) | Working | `apps/cli/fairmind_cli/main.py` |
| Python SDK | Working | `apps/sdk/src/fairmind/client.py:104-247` |
| MCP server (9 tools) | Working | `apps/mcp/src/fairmind_mcp/server.py:146-230` |
| GitHub Action `fairmind-gate` | Working | `.github/actions/fairmind-gate/action.yml` |
| Passport ingest and pack export from CLI or SDK | Planned | `apps/sdk/src/fairmind/client.py` |
| Website roadmap, features, comparison pages | Partial (out of date) | `apps/website/src/pages/roadmap.astro`, `apps/website/src/pages/features.astro` |
| Docs site API reference and limitations | Partial (out of date) | `apps/docs/content/docs/reference/api.mdx:18-32` |
| `apps/ml` pipelines | Partial (three dvc stages have no script) | `dvc.yaml:15,37,49` |

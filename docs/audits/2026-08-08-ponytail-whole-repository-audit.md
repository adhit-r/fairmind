# Ponytail whole-repository audit — 2026-08-08

Status: report-only release-gate audit; no deletion was performed

## Claim boundary

This audit uses static repository evidence: project imports, route composition,
Next.js/Astro page and navigation references, tests, package manifests, and
document references. It does not include production traffic, external package
consumers, customer bookmarks, deployment-specific environment variables, or
product-owner intent. A zero-import result is therefore a removal candidate,
not proof that a customer never relies on the capability.

The Task 12B evidence-admission kernel is explicitly retained. Its size follows
the approved evidence-integrity plan and its ports, service, repository
transaction, native PostgreSQL tests, and architecture boundary are all active
release work.

## Result

Ponytail found a possible net reduction of roughly 35,000 lines and 23 direct
dependencies. The highest-value result is not immediate deletion; it is a
truthful capability inventory. FairMind currently contains many implementation
files and dashboard pages whose presence can be mistaken for a working,
composed evaluation capability even when no active route or importer reaches
them.

| Rank | Ponytail tag | Static result | Candidate size | Required gate |
| --- | --- | --- | ---: | --- |
| 1 | `delete` | Zero-import application services, including simulated or aspirational evaluators | 19 files / 15,798 lines | Capability-owner classification, route/composition proof, focused tests |
| 2 | `delete` | Dormant legacy/library/domain modules | 22 files / 6,913 lines | External-consumer and package-barrel validation |
| 3 | `delete` | File-system dashboard routes with no internal navigation reference | 16 routes / 5,655 lines | Traffic, bookmarks, product intent, desktop/mobile E2E |
| 4 | `delete` | Frontend modules unreachable from pages, layouts, routes, and tests | 37 files / 5,033 lines | Typecheck, build, E2E, visual regression |
| 5 | `delete` | Unreferenced Astro files and duplicate plural stylesheet | 14 files / 1,597 lines | Website build and route smoke test |
| 6 | `delete` | Unmounted or duplicate backend middleware/health/helper infrastructure | 1,177 lines | Composition trace plus backend regressions |
| 7 | `yagni` | Test-only route registry and one-version API decorator registry | about 560 lines | Replace deliberately; preserve contract tests |
| 8 | `delete` | Explicitly unmounted duplicate approvals router | 457 lines | Route inventory and approval-flow regression |
| 9 | `delete` | Direct dependencies with no reachable consumer | 15 frontend/website packages | Lockfile update, clean install, build, E2E |
| 10 | `stdlib` | Redundant or speculative backend dependencies | 7 packages | Import, deployment, optional-extra, and vulnerability scan |
| 11 | `native` | Catch-all `OPTIONS` route duplicated by Starlette CORS | 25 lines | Preflight contract tests |
| 12 | `yagni` | Settings fields with no production-code reads | 23 fields | Deployment configuration and operations review |

## Capability-truth candidates

These zero-import application services require the first review because their
names can imply shipped product capability:

```text
apps/backend/src/application/services/comprehensive_bias_evaluation_pipeline.py
apps/backend/src/application/services/ai_bom_db_service.py
apps/backend/src/application/services/generative_ai_explainability.py
apps/backend/src/application/services/owasp_security_tester.py
apps/backend/src/application/services/benchmark_suite_service.py
apps/backend/src/application/services/ai_bom_service.py
apps/backend/src/application/services/lifecycle_integration.py
apps/backend/src/application/services/model_provenance_service.py
apps/backend/src/application/services/realtime_model_integration_service.py
apps/backend/src/application/services/evidence_collector.py
apps/backend/src/application/services/modern_tools_integration.py
apps/backend/src/application/services/risk_incident_manager.py
apps/backend/src/application/services/enhanced_bias_detection_service.py
apps/backend/src/application/services/india_compliance_metrics.py
apps/backend/src/application/services/comprehensive_bias_detection_service.py
apps/backend/src/application/services/model_performance_benchmarking.py
apps/backend/src/application/services/policy_engine.py
apps/backend/src/application/services/compliance_remediation_service.py
apps/backend/src/application/services/database_service.py
```

Disposition: inventory each as `composed`, `supporting kernel`, `fixture-only`,
`research-only`, `planned`, or `retire`. Remove runtime and marketing claims for
anything other than `composed`; retain future capability requirements in the
master plan rather than dormant runtime code.

## Legacy and domain candidates

Static search found no project importer beyond a dormant barrel for these
modules. `apps/backend/fairness_library/india_regulatory_frameworks.py` is not
in this list because it has an active importer.

```text
apps/backend/services/bias_remediation.py
apps/backend/services/bias_test_results.py
apps/backend/services/cyclonedx_aibom_service.py
apps/backend/services/dataset_storage.py
apps/backend/services/fairness_metrics.py
apps/backend/services/llm_bias_metrics.py
apps/backend/services/model_storage_service.py
apps/backend/services/monitoring.py
apps/backend/services/neon_data_api.py
apps/backend/fairness_library/__init__.py
apps/backend/fairness_library/governance.py
apps/backend/fairness_library/llm_bias.py
apps/backend/fairness_library/metrics.py
apps/backend/fairness_library/monitoring.py
apps/backend/fairness_library/registry.py
apps/backend/src/domain/analytics/services/analytics_service.py
apps/backend/src/domain/bias/services/llm_judge_service.py
apps/backend/src/domain/bias_detection/services/llm_bias_service.py
apps/backend/src/domain/bias_detection/services/multimodal_bias_service.py
apps/backend/src/domain/compliance/services/evidence_service.py
apps/backend/src/infrastructure/db/database/india_compliance_models.py
apps/backend/src/infrastructure/db/database/india_rag_models.py
```

Disposition: validate external/package consumers, migrations, and documentation
imports before removal. Do not fold any statistical kernel into a product pack
without independent validation.

## Dashboard route candidates

These file-system routes have no internal navigation, `href`, or router
reference in the static graph:

```text
advanced-bias
ai-bom
benchmarks
bias-simple
compliance
compliance/dashboard
compliance-automation
fairness-documentation
lifecycle
llm-testing
multimodal-bias
policies
provenance
realtime
security
stakeholder-dashboard
```

All paths are below `apps/frontend/src/app/(dashboard)`. Disposition: compare
against traffic, saved links, authorization entry points, and the intended 2027
information architecture. Retire misleading pages or add deliberate navigation
only after that product decision.

## Unreachable frontend and website modules

The frontend candidates include the `india-compliance` and
`compliance-automation` component trees; `BiasDetectionWidget.tsx`;
`ComparisonTable.tsx`; the three `model-dna` components; unused accordion,
avatar, data-table, popover, and radio-group primitives; compliance-automation
and model-DNA API clients; eight hooks or hook barrels; OAuth/performance
utilities; and `reports-service.ts`.

The website candidates include `styles/globals.css`, while live pages use the
singular `global.css`, plus the unreferenced ContactForm, Pricing, Welcome,
section, layout, UI, Markdown, and markdown utility files identified by the
audit.

Disposition: create one mechanical cleanup change per app, then require a clean
install, typecheck, production build, route smoke tests, E2E, and visual review.
Do not mix these deletions into assurance-domain changes.

## Backend composition candidates

Review for removal or consolidation:

```text
apps/backend/src/api/middleware/input_sanitization.py
apps/backend/src/api/middleware/rate_limiting.py
apps/backend/core/middleware/pipeline.py
apps/backend/core/middleware/request_logging.py
apps/backend/health/checker.py
apps/backend/health/routes.py
apps/backend/shared/constants.py
apps/backend/shared/utils.py
apps/backend/config/validator.py
apps/backend/middleware/security.py (unused code beginning near line 194)
apps/backend/api/registry.py
apps/backend/api/versioning.py
apps/backend/src/api/routers/approvals.py
apps/backend/api/main.py (catch-all OPTIONS route near line 312)
```

Disposition: trace `apps/backend/api/main.py` and test imports again immediately
before removal. Preserve the mounted CORS, rate-limit, error-handling, health,
and governance approval paths named in the repository onboarding guidance.

## Dependency and settings candidates

The backend direct-dependency candidates are `python-dotenv`, `aiosmtplib`,
`bcrypt`, `websockets`, `boto3`, `sentry-sdk`, and `tensorflow`. The static
replacement hypotheses are `pydantic-settings`, `smtplib`,
`passlib[bcrypt]`, and `uvicorn[standard]`, with cloud, telemetry, or ML
libraries reintroduced only with a real importer.

The frontend/website audit also found 15 direct packages and the Astro sitemap
integration with no reachable consumer after the dead-module set is removed.
Package names must be regenerated after source cleanup because dependency
reachability is conditional on that change.

Twenty-three settings fields for metrics, Sentry, AWS, timeout, encryption, and
retention have no production-code read. Deployment manifests and operator
configuration must be checked before any field is removed.

## Execution order

1. Build a capability registry from composed runtime paths and classify the 19
   service candidates.
2. Remove or quarantine misleading simulated/aspirational runtime code in a
   dedicated change with claim-boundary tests.
3. Validate dashboard routes against traffic and product intent.
4. Remove unreachable components and then recompute dependencies.
5. Consolidate backend middleware, registries, and settings one boundary at a
   time.
6. Re-run Ponytail, the full backend/frontend/website gates, and the capability
   truth-table check; record measured net reduction rather than the current
   estimate.

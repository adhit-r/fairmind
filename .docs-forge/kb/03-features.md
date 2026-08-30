# P0 feature inventory

| Feature | User-visible purpose | Primary source evidence | Release status | Documentation page |
| --- | --- | --- | --- | --- |
| Capability gates | Keep every Assurance V2 surface absent until its exact release gate is enabled | `apps/backend/config/settings.py:L50-L84`; `apps/backend/api/main.py:L381-L502` | Internal, default-off alpha | `release-boundary.mdx` |
| Versioned targets and suites | Bind evaluation intent to immutable target and suite identities | `apps/backend/src/api/routers/evaluation_workbench.py:L1066-L1136`; `apps/backend/src/api/routers/evaluation_workbench.py:L1137-L1221` | Included behind child gates | `assurance-workflow.mdx` |
| Plans, activation, and preflight | Create a content-bound plan, separate activation, and explicit blocker result | `apps/backend/src/api/routers/evaluation_workbench.py:L1222-L1344` | Included behind child gates; preflight is not execution | `assurance-workflow.mdx` |
| Immutable runs and envelopes | Record the exact lifecycle trigger and execution boundary | `apps/backend/src/api/routers/evaluation_workbench.py:L1345-L1426` | Included behind child gates | `assurance-workflow.mdx` |
| Signed Passport V2 admission | Verify evidence against server-owned evaluator and trust authority | `apps/backend/src/api/routers/evaluation_workbench.py:L1427-L1505`; `apps/backend/src/application/services/verified_evidence_admission_service.py` | Included behind a separate child gate | `evidence-trust-review.mdx` |
| Evidence linking | Connect one verified Passport revision to one exact suite execution | `apps/backend/src/api/routers/evaluation_workbench.py:L1506-L1561`; `apps/backend/src/application/services/verified_evidence_link_service.py` | Included behind a separate child gate | `evidence-trust-review.mdx` |
| Four-eyes review | Prevent requester, submitter, or linker from reviewing the same evidence | `apps/backend/src/api/routers/evaluation_workbench.py:L1562-L1625`; `apps/backend/src/application/services/verified_evidence_review_service.py` | Included; no review override | `permissions-and-separation.mdx` |
| Freshness and decision eligibility | Derive whether accepted evidence remains usable at decision time | `apps/backend/src/application/evidence_freshness.py`; `apps/backend/src/application/services/verified_evidence_review_service.py:L24-L138`; `apps/backend/src/application/services/governance_decision_service.py:L196-L205` | Included behind review and decision gates | `evidence-trust-review.mdx` |
| Governance decisions | Persist bounded decisions against an exact evidence set | `apps/backend/src/api/routers/evaluation_workbench.py:L1626-L1676`; `apps/backend/src/application/services/governance_decision_service.py:L464-L553` | Included behind a separate child gate | `operator-runbook.mdx` |
| Separation exception | Permit only an audited, separately gated decision exception without weakening review separation | `apps/backend/src/api/routers/evaluation_workbench.py:L1677-L1825`; `apps/backend/src/application/services/governance_decision_service.py:L554-L984` | Included as a narrow PostgreSQL-authoritative exception | `permissions-and-separation.mdx` |
| Evidence-trust dashboard | Display a scope-matched V2 run without legacy or fixture fallback | `apps/frontend/src/app/(dashboard)/assurance/evaluations/[runId]/page.tsx:L33-L175` | Read-only, separately default-off preview | `getting-started.mdx` |
| Worker execution and evaluator packs | Execute evaluations and produce real benchmarked evidence | `apps/docs/content/docs/limitations-roadmap.mdx:L14-L42` | Not released in P0 | `limitations-roadmap.mdx` |

## Product claim boundary

The supported P0 claim is an internal, default-off evidence-control foundation.
The feature inventory does not support claims that FairMind evaluates models,
continuously monitors deployments, certifies compliance, or automatically
approves or blocks releases (`apps/docs/content/docs/release-boundary.mdx:L38-L55`).

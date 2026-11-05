# The system journey

One AI system moves through six stages. Every screen in the product either serves one stage, serves the whole estate (the library), or is on its way out. The system file at `/systems/[id]` is where a user sees the whole journey for one system and the single next action at each stage.

## Stages

| Stage | For | Enter when | Leave when | Backed by | Next action shown |
|---|---|---|---|---|---|
| Onboard | Know the system exists and who owns it | Registered manually or promoted from a connector | Name, owner, tier and business line recorded | `GET /ai-governance/systems/{id}`, `/integrations` | Run the first evaluation |
| Assess | Produce evidence about behaviour: fairness, robustness, environmental cost | First evaluation run starts | At least one evaluation produced evidence | `/tests`, `/bias`, `/multimodal-bias`, `/llm-judge`, environmental impact | Run an evaluation |
| Govern | Bind evidence to framework controls and reach review-ready | Evidence exists | Evidence summary reports `review_ready` with no missing signals | `GET /evidence/{id}/summary`, `/compliance/frameworks` | Record or link evidence |
| Remediate | Close open findings before a release decision | Any open risk or remediation task | No open high or critical risks, no active tasks | `GET /dashboard/risk?system_id`, `GET /remediation?system_id` | Work the open findings |
| Decision | Ask for and record a release decision | Govern complete and nothing open in Remediate | Approval request decided | `GET /approval/system/{id}`, `POST /approval/system/{id}/request`, `POST /approval-requests/{id}/decision` | Request the release decision |
| Operate | Watch the system in production and keep the record current | Approved | System retired | `/monitoring` (live metrics not wired yet), `GET /reports?system_id` | Generate the audit report |

The decision endpoint refuses an approval with 409 while a high or critical finding is open, while a critical remediation task is active, and while the release gate says no go (a conditional go needs the accepted conditions in the notes). Lower-priority active tasks keep the system in Remediate on the system file but do not block an approval. A finding resolves once every remediation task linked to it is resolved or closed, and opens again if one of them is reopened. Rejecting is always allowed. The release gate (`GET /systems/{id}/gate`, `fairmind gate`) reports the latest decision as `approvalStatus`; a rejection keeps the gate no go until a reviewer approves a new request.

The backend already derives the stage and a readiness figure from these same inputs (`_derive_lifecycle_status` in `ai_governance.py`). The system file shows that derivation rather than a stage the user picked by hand.

## Where each page belongs

**System file** (new): `systems/[id]`. Replaces `lifecycle`, `stakeholder-dashboard` and the per-page "Current AI System" bar.

**Onboard**: `onboard`, `integrations`, `ai-bom`, `provenance`, `model-dna`.

**Assess**: `tests`, `tests/[testId]`, `assurance/evaluations/[runId]`, `bias`, `multimodal-bias`, `llm-judge`, `llm-testing`, `explainability-studio`, `benchmarks`, `ai-governance` (environmental evaluation path).

**Govern**: `evidence`, `compliance`, `compliance-automation`, `policies`, `fairness-documentation`, `security`.

**Remediate**: `risks`, `remediation`.

**Decision**: handled inside the system file; `audit-reports` produces the release report.

**Operate**: `monitoring`, `alerts`, `status`.

**Library** (estate-wide, in the sidebar): `dashboard`, `integrations`, `compliance` (frameworks), `evidence`, `risks` (findings), `audit-reports` (exports), `settings`, `reports`.

**Admin** (not part of the journey): `admin/*`, `org-admin/*`.

**Retire** (duplicates or superseded; leave untouched until removed): `lifecycle`, `stakeholder-dashboard`, `analytics`, `model-inventory`, `compliance-dashboard`, `compliance/dashboard`, `bias-simple`, `advanced-bias`, `modern-bias`, `remediation-wizard`, `realtime`, `marketplace`, `marketplace/[id]`.

## What this pass changes

- Adds the system file and routes every system link to it: estate tiles and the systems table on the overview, and the Govern action on the integrations review queue.
- Replaces the legacy `SystemContextBar` on every remaining page with a one-line breadcrumb back to the system file, so a user always knows which system they are acting on and how to get back.
- Leaves the legacy tool pages themselves as they are. Restyling them, and removing the "retire" list, is follow-up work, one stage at a time.

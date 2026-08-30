# P0 public-surface notes

The P0 Assurance V2 interface is an internal alpha. Every capability defaults
to disabled (`apps/backend/config/settings.py:L50-L84`) and is mounted only
when the master and relevant child gate are enabled
(`apps/backend/api/main.py:L381-L500`).

Core version, plan, and run routes are scoped to
`/api/v1/ai-governance/organizations/{org_id}`; exact route declarations are
in `apps/backend/src/api/routers/evaluation_workbench.py:L850-L1425`.

Signed evidence, linking, review, governance decision, and separation-exception
routes are separately declared in
`apps/backend/src/api/routers/evaluation_workbench.py:L1427-L1825`.

Human permissions and the service-principal-only worker vocabulary are defined
in `apps/backend/src/api/evaluation_permissions.py:L16-L151`. A worker route or
runtime is not mounted by P0.

The dashboard evidence-trust preview is gated by
`NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED` and
`NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED`; it is read-only and uses validated
scope-bound V2 responses (`apps/frontend/src/app/(dashboard)/assurance/evaluations/[runId]/page.tsx:L24-L156`).

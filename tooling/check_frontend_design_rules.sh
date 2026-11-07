#!/usr/bin/env bash
# Lifecycle-shell design gate for apps/frontend/src (see CLAUDE.md "Design Context").
# Fails on emoji, gradients and the retired neobrutalist styling.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET=apps/frontend/src
if [ ! -d "$TARGET" ]; then
  echo "Design check target missing: $TARGET"
  exit 1
fi

EMOJI='[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE0F}]'
RETIRED='bg-gradient|linear-gradient|radial-gradient|\bborder-[24]\b|\bborder-black\b|shadow-brutal|shadow-\[[0-9-]+px_[0-9-]+px_0|\bfont-black\b|\brounded-none\b|#0F1412|#FCFDF8|bg-\[#FF6B35\]'

# Files that still violate and have not been migrated yet. This list must only
# shrink: when you clean a file, delete its line. Never add new files here.
ALLOWLIST=(
  'app/(auth)/callback/page.tsx'
  'app/(auth)/invitations/[token]/page.tsx'
  'app/(dashboard)/admin/audit-log/page.tsx'
  'app/(dashboard)/admin/registrations/page.tsx'
  'app/(dashboard)/admin/roles/page.tsx'
  'app/(dashboard)/admin/users/page.tsx'
  'app/(dashboard)/ai-bom/page.tsx'
  'app/(dashboard)/ai-governance/page.tsx'
  'app/(dashboard)/alerts/page.tsx'
  'app/(dashboard)/assurance/evaluations/[runId]/page.tsx'
  'app/(dashboard)/benchmarks/page.tsx'
  'app/(dashboard)/bias/page.tsx'
  'app/(dashboard)/compliance-dashboard/components/ControlTracePanel.tsx'
  'app/(dashboard)/compliance-dashboard/components/FrameworkCatalog.tsx'
  'app/(dashboard)/compliance-dashboard/page.tsx'
  'app/(dashboard)/compliance/dashboard/page.tsx'
  'app/(dashboard)/compliance/workflows/[workflowId]/page.tsx'
  'app/(dashboard)/lifecycle/page.tsx'
  'app/(dashboard)/model-inventory/components/LifecycleStepper.tsx'
  'app/(dashboard)/model-inventory/components/SystemDetailDrawer.tsx'
  'app/(dashboard)/monitoring/page.tsx'
  'app/(dashboard)/org-admin/audit-log/page.tsx'
  'app/(dashboard)/org-admin/members/page.tsx'
  'app/(dashboard)/org-admin/page.tsx'
  'app/(dashboard)/org-admin/roles/page.tsx'
  'app/(dashboard)/org-admin/settings/page.tsx'
  'app/(dashboard)/provenance/page.tsx'
  'app/(dashboard)/realtime/page.tsx'
  'app/(dashboard)/remediation/page.tsx'
  'app/(dashboard)/security/page.tsx'
  'app/(dashboard)/settings/page.tsx'
  'app/(dashboard)/status/page.tsx'
  'app/globals.css'
  'components/ErrorBoundary.tsx'
  'components/OrangeLogo.tsx'
  'components/compliance/AuditReportPanel.tsx'
  'components/evaluations/EvaluatorRegistrationCatalogPanel.tsx'
  'components/evaluations/EvidenceTrustPanel.tsx'
  'components/india-compliance/IntegrationManagementPanel.tsx'
  'components/layout/AppShell.tsx'
  'components/packs/flow.tsx'
  'components/ui/slider.tsx'
  'components/ui/switch.tsx'
  'components/workflow/SystemContext.tsx'
)

globs=()
for f in "${ALLOWLIST[@]}"; do
  if [ ! -e "$TARGET/$f" ]; then
    echo "Allowlisted file no longer exists, remove it from ALLOWLIST: $f"
    exit 1
  fi
  # Escape glob metacharacters used in Next.js route segments.
  esc=$(printf '%s' "$f" | sed 's/[][*?{}]/\\&/g')
  globs+=(--glob "!$TARGET/$esc")
done

rc=0
rg -n -i -e "$EMOJI" -e "$RETIRED" "$TARGET" "${globs[@]}" || rc=$?
if [ "$rc" -eq 0 ]; then
  echo "Frontend design rule violations found (emoji, gradients or retired neobrutalist styling)."
  exit 1
elif [ "$rc" -ge 2 ]; then
  echo "Design check could not search $TARGET (rg exit $rc)."
  exit 1
fi

echo "No frontend design rule violations found (${#ALLOWLIST[@]} files allowlisted)."

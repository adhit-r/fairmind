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

# Emoji blocks plus the emoji-presentation symbols outside them, ZWJ and VS16.
EMOJI='[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{2300}-\x{23FF}\x{2139}\x{203C}\x{2049}\x{3030}\x{303D}\x{3297}\x{3299}\x{200D}\x{FE0F}]'
# Heavy borders cover every side variant (border-b-4, xl:border-r-2, border-8).
# A spinner ring may use border-[2px], which this does not match.
RETIRED='bg-gradient|linear-gradient|radial-gradient|\bborder-([xytrblse]-)?[248]\b|\bborder-black\b|shadow-brutal|shadow-\[[0-9-]+px_[0-9-]+px_0|\bfont-black\b|\brounded-none\b|#0F1412|#FCFDF8|bg-\[#FF6B35\]'

# Files not migrated yet, pinned to their current count of violating lines.
# Every file not listed must have zero. A pinned count may never go up; when it
# goes down the gate fails until you lower the pin (or delete the entry at zero),
# so this list only shrinks. Never add new files here.
PINS=(
  'app/(auth)/callback/page.tsx:2'
  'app/(auth)/invitations/[token]/page.tsx:3'
  'app/(dashboard)/admin/audit-log/page.tsx:1'
  'app/(dashboard)/admin/registrations/page.tsx:2'
  'app/(dashboard)/admin/roles/page.tsx:2'
  'app/(dashboard)/admin/users/page.tsx:3'
  'app/(dashboard)/ai-bom/page.tsx:1'
  'app/(dashboard)/ai-governance/page.tsx:7'
  'app/(dashboard)/assurance/evaluations/[runId]/page.tsx:2'
  'app/(dashboard)/compliance-dashboard/components/ControlTracePanel.tsx:1'
  'app/(dashboard)/compliance-dashboard/components/FrameworkCatalog.tsx:1'
  'app/(dashboard)/compliance-dashboard/page.tsx:1'
  'app/(dashboard)/compliance/dashboard/page.tsx:1'
  'app/(dashboard)/compliance/workflows/[workflowId]/page.tsx:2'
  'app/(dashboard)/model-inventory/components/LifecycleStepper.tsx:1'
  'app/(dashboard)/model-inventory/components/SystemDetailDrawer.tsx:2'
  'app/(dashboard)/monitoring/page.tsx:1'
  'app/(dashboard)/org-admin/audit-log/page.tsx:5'
  'app/(dashboard)/org-admin/members/page.tsx:4'
  'app/(dashboard)/org-admin/page.tsx:1'
  'app/(dashboard)/org-admin/roles/page.tsx:4'
  'app/(dashboard)/org-admin/settings/page.tsx:4'
  'app/(dashboard)/provenance/page.tsx:1'
  'app/(dashboard)/remediation/page.tsx:7'
  'app/(dashboard)/settings/page.tsx:1'
  'app/(dashboard)/status/page.tsx:1'
  'app/globals.css:1'
  'components/ComparisonTable.tsx:2'
  'components/ErrorBoundary.tsx:1'
  'components/OrangeLogo.tsx:1'
  'components/compliance/AuditReportPanel.tsx:3'
  'components/evaluations/EvaluatorRegistrationCatalogPanel.tsx:2'
  'components/evaluations/EvidenceTrustPanel.tsx:17'
  'components/india-compliance/IntegrationManagementPanel.tsx:1'
  'components/layout/AppShell.tsx:1'
  'components/packs/flow.tsx:3'
  'components/ui/slider.tsx:1'
  'components/ui/switch.tsx:1'
  'components/workflow/SystemContext.tsx:1'
)

# components/stageshow/kit is the vendored Stageshow kit (third-party, MIT, see its LICENSE). It is kept
# verbatim so it can be updated, and its gradients are mostly edge-fade masks. FairMind's own demo files
# beside it (fm.css, *Demo.tsx, *-demo.css) are still checked.
VENDORED='!**/components/stageshow/kit/**'

rc=0
raw=$(rg -c -i -e "$EMOJI" -e "$RETIRED" --glob "$VENDORED" "$TARGET") || rc=$?
if [ "$rc" -ge 2 ]; then
  echo "Design check could not search $TARGET (rg exit $rc)."
  exit 1
fi
actual=$(printf '%s\n' "$raw" | sed -e "s|^$TARGET/||" -e '/^$/d' | LC_ALL=C sort)
expected=$(printf '%s\n' "${PINS[@]}" | LC_ALL=C sort)

if [ "$actual" != "$expected" ]; then
  echo "Frontend design rule counts changed (file:violating lines; - pinned, + actual):"
  diff <(printf '%s\n' "$expected") <(printf '%s\n' "$actual") | grep '^[<>]' | sed -e 's/^</ -/' -e 's/^>/ +/' || true
  echo "Higher or new counts: remove the emoji, gradient or retired styling (rg the file to see the lines)."
  echo "Lower counts: update or delete the PINS entry in tooling/check_frontend_design_rules.sh."
  exit 1
fi

echo "No new frontend design rule violations (${#PINS[@]} files pinned)."

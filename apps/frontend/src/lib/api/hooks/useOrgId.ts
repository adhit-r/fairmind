'use client';

import { useOrg } from '@/context/OrgContext';

/**
 * Hook to get the selected organization ID for UI state
 *
 * This value is a browser preference, not an implicit request authority.
 * Scoped APIs must carry organization scope through their explicit route or
 * query contract rather than relying on this selection.
 *
 * Usage:
 * ```tsx
 * const orgId = useOrgId();
 * return <OrganizationLabel organizationId={orgId} />;
 * ```
 */
export function useOrgId(): string | null {
  const { selectedOrg } = useOrg();
  return selectedOrg?.id || null;
}

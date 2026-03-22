'use client';

import { useOrg } from '@/context/OrgContext';

/**
 * Hook to get the selected organization ID for API calls
 *
 * Returns the selected org ID that should be included in API requests.
 * Returns null if no org is selected (shouldn't happen in normal operation).
 *
 * Usage:
 * ```tsx
 * const orgId = useOrgId();
 * const response = await apiClient.get(`/api/v1/models?org_id=${orgId}`);
 * ```
 */
export function useOrgId(): string | null {
  const { selectedOrg } = useOrg();
  return selectedOrg?.id || null;
}

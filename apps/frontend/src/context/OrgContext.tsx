'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient, type ApiResponse } from '@/lib/api/api-client';

/**
 * Organization type structure
 * Represents a company/entity with users and resources
 */
export interface Organization {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  owner_id: string;
  created_at: string;
  role: string; // "admin", "analyst", "viewer"
}

/**
 * Context type definition for organization management
 */
export interface OrgContextType {
  organizations: Organization[];
  selectedOrg: Organization | null;
  isLoading: boolean;
  error: string | null;
  selectOrg: (orgId: string) => void;
  refreshOrgs: () => Promise<void>;
}

/**
 * Create the context
 */
const OrgContext = createContext<OrgContextType | undefined>(undefined);

/**
 * Organization Provider Component
 *
 * Wraps the application to provide organization context to all children.
 * Handles fetching user's organizations and managing org selection.
 *
 * Usage:
 * ```tsx
 * <OrgProvider>
 *   <YourApp />
 * </OrgProvider>
 * ```
 */
export function OrgProvider({ children }: { children: ReactNode }) {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch user's organizations on mount
   */
  useEffect(() => {
    fetchOrgs();
  }, []);

  const fetchOrgs = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const res: ApiResponse<{ organizations: Organization[] }> = await apiClient.get('/api/v1/organizations');

      if (res.success && res.data) {
        setOrganizations(res.data.organizations);

        // Select first org or restore from localStorage
        const savedOrgId = typeof window !== 'undefined' ? localStorage.getItem('selected_org_id') : null;
        const orgToSelect = savedOrgId
          ? res.data.organizations.find((o) => o.id === savedOrgId)
          : res.data.organizations[0];

        if (orgToSelect) {
          setSelectedOrg(orgToSelect);
          if (typeof window !== 'undefined') {
            localStorage.setItem('selected_org_id', orgToSelect.id);
          }
        }
      } else {
        throw new Error(res.error || 'Failed to fetch organizations');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch organizations';
      setError(errorMsg);
      console.error('[OrgContext] Error fetching organizations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const selectOrg = (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      setSelectedOrg(org);
      if (typeof window !== 'undefined') {
        localStorage.setItem('selected_org_id', orgId);
        // Reload dashboard with new org context
        window.location.reload();
      }
    }
  };

  const refreshOrgs = async () => {
    await fetchOrgs();
  };

  const value: OrgContextType = {
    organizations,
    selectedOrg,
    isLoading,
    error,
    selectOrg,
    refreshOrgs,
  };

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

/**
 * Hook to use organization context
 *
 * Usage:
 * ```tsx
 * const { organizations, selectedOrg, selectOrg } = useOrg();
 * ```
 *
 * @throws Error if used outside OrgProvider
 */
export function useOrg(): OrgContextType {
  const context = useContext(OrgContext);

  if (!context) {
    throw new Error('useOrg must be used within an OrgProvider');
  }

  return context;
}

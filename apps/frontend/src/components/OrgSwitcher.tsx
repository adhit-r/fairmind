'use client';

import React from 'react';
import { useOrg } from '@/context/OrgContext';

/**
 * Organization Switcher Component
 *
 * Displays current organization and allows switching between multiple orgs.
 * For single-org users, displays org name only.
 * For multi-org users, displays dropdown selector.
 *
 * Integrated with dashboard layout for easy access.
 */
export const OrgSwitcher: React.FC = () => {
  const { organizations, selectedOrg, selectOrg, isLoading, error } = useOrg();

  // Loading state: show nothing until orgs are loaded
  if (isLoading) {
    return (
      <div className="px-4 py-3 border-b-2 border-black bg-white">
        <div className="text-sm text-gray-500">Loading organizations...</div>
      </div>
    );
  }

  // Error state: show error message
  if (error) {
    return (
      <div className="px-4 py-3 border-b-2 border-black bg-white">
        <div className="text-sm text-red-600 font-bold">Error: {error}</div>
      </div>
    );
  }

  // No organizations: show message
  if (organizations.length === 0) {
    return (
      <div className="px-4 py-3 border-b-2 border-black bg-white">
        <div className="text-sm text-gray-600">No organizations assigned</div>
      </div>
    );
  }

  // Single org: just show name (read-only)
  if (organizations.length === 1) {
    return (
      <div className="px-4 py-3 border-b-2 border-black bg-white">
        <div className="text-xs font-bold uppercase text-gray-600 tracking-wide mb-1">Organization</div>
        <div className="text-sm font-bold">{selectedOrg?.name}</div>
      </div>
    );
  }

  // Multi-org: show dropdown
  return (
    <div className="px-4 py-3 border-b-2 border-black bg-white">
      <label className="block text-xs font-bold uppercase text-gray-600 tracking-wide mb-2">Organization</label>
      <select
        value={selectedOrg?.id || ''}
        onChange={(e) => selectOrg(e.target.value)}
        className="w-full p-2 border-2 border-black bg-white font-bold text-sm focus:outline-none focus:shadow-lg shadow-md"
      >
        {organizations.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name} ({org.role})
          </option>
        ))}
      </select>
    </div>
  );
};

'use client';

import React, { useEffect, useState } from 'react';
import { useOrg } from '@/context/OrgContext';
import { apiClient as api } from '@/lib/api/api-client';
import { IconTrash } from '@tabler/icons-react';

interface OrgRole {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system_role: boolean;
  member_count?: number;
}

export default function OrgRolesPage() {
  const { selectedOrg } = useOrg();
  const [roles, setRoles] = useState<OrgRole[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRoles();
  }, [selectedOrg]);

  const fetchRoles = async () => {
    if (!selectedOrg) return;
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get<{ roles: OrgRole[] }>(
        `/api/v1/organizations/${selectedOrg.id}/roles`
      );
      if (response.success && response.data) {
        setRoles(response.data.roles);
      } else {
        setError(response.error || 'Failed to fetch roles');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch roles';
      setError(errorMessage);
      console.error('Error fetching roles:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRole = async (roleId: string) => {
    if (!selectedOrg || !confirm('Delete this role? This action cannot be undone.')) return;

    try {
      const response = await api.delete(
        `/api/v1/organizations/${selectedOrg.id}/roles/${roleId}`
      );

      if (response.success) {
        await fetchRoles();
      } else {
        alert('Failed to delete role');
      }
    } catch (err) {
      console.error('Error deleting role:', err);
      alert('Failed to delete role');
    }
  };

  const getPermissionColor = (permission: string) => {
    const colors: Record<string, string> = {
      'members:read': 'bg-blue-100 text-blue-800',
      'members:write': 'bg-purple-100 text-purple-800',
      'members:delete': 'bg-red-100 text-red-800',
      'roles:read': 'bg-blue-100 text-blue-800',
      'roles:write': 'bg-purple-100 text-purple-800',
      'roles:delete': 'bg-red-100 text-red-800',
      'settings:read': 'bg-green-100 text-green-800',
      'settings:write': 'bg-emerald-100 text-emerald-800',
      'audit:read': 'bg-gray-100 text-gray-800',
    };
    return colors[permission] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <h1 className="text-4xl font-bold text-black">Organization Roles</h1>
          <p className="mt-2 text-gray-600">Manage roles and their permissions</p>
        </div>

        {/* Roles List */}
        {isLoading ? (
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        ) : error ? (
          <div className="rounded-lg border-2 border-red-800 bg-red-50 p-4">
            <p className="text-red-800">Error: {error}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {roles.length === 0 ? (
              <div className="rounded-lg border-2 border-gray-300 bg-gray-50 p-8 text-center">
                <p className="text-gray-600">No roles found</p>
              </div>
            ) : (
              roles.map((role) => (
                <div
                  key={role.id}
                  className="rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg"
                >
                  {/* Role Header */}
                  <div className="mb-6 flex items-start justify-between border-b-2 border-gray-200 pb-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-2xl font-bold text-black">{role.name}</h3>
                        {role.is_system_role && (
                          <span className="rounded-lg bg-gray-200 px-3 py-1 text-xs font-bold text-gray-700">
                            SYSTEM
                          </span>
                        )}
                      </div>
                      {role.description && (
                        <p className="mt-2 text-sm text-gray-600">{role.description}</p>
                      )}
                      {role.member_count !== undefined && (
                        <p className="mt-1 text-xs text-gray-500">
                          {role.member_count} member{role.member_count !== 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                    {!role.is_system_role && (
                      <button
                        onClick={() => handleDeleteRole(role.id)}
                        className="flex items-center gap-2 rounded bg-red-600 px-4 py-2 font-bold text-white transition-all hover:bg-red-700 active:translate-y-1"
                      >
                        <IconTrash size={18} />
                        Delete
                      </button>
                    )}
                  </div>

                  {/* Permissions */}
                  <div>
                    <p className="mb-4 font-bold text-black">Permissions</p>
                    {role.permissions.length === 0 ? (
                      <p className="text-sm text-gray-600">No permissions assigned</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {role.permissions.map((permission) => (
                          <span
                            key={permission}
                            className={`inline-block rounded-lg px-3 py-1 text-sm font-bold ${getPermissionColor(
                              permission
                            )}`}
                          >
                            {permission}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-12 rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
          <h3 className="mb-4 font-bold text-black">About Organization Roles</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <p>
              <strong className="text-black">System Roles</strong> are built-in roles managed
              by FairMind and cannot be modified.
            </p>
            <p>
              <strong className="text-black">Custom Roles</strong> allow you to define
              permissions specific to your organization's needs.
            </p>
            <p>
              <strong className="text-black">Permissions</strong> determine what actions
              members can perform within the organization.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useEffect, useState } from 'react';
import { useOrg } from '@/context/OrgContext';
import { apiClient as api } from '@/lib/api/api-client';
import { IconFilter } from '@tabler/icons-react';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  description: string;
  status: 'success' | 'failure';
  ip_address?: string;
}

export default function OrgAuditLogPage() {
  const { selectedOrg } = useOrg();
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterAction, setFilterAction] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchAuditLog();
  }, [selectedOrg, filterAction, filterStatus]);

  const fetchAuditLog = async () => {
    if (!selectedOrg) return;
    try {
      setIsLoading(true);
      setError(null);

      let endpoint = `/api/v1/organizations/${selectedOrg.id}/audit-log`;
      const params = new URLSearchParams();
      if (filterAction) params.append('action', filterAction);
      if (filterStatus) params.append('status', filterStatus);
      if (params.toString()) endpoint += `?${params.toString()}`;

      const response = await api.get<{ entries: AuditLogEntry[] }>(endpoint);
      if (response.success && response.data) {
        setEntries(response.data.entries);
      } else {
        setError(response.error || 'Failed to fetch audit log');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch audit log';
      setError(errorMessage);
      console.error('Error fetching audit log:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      create: 'bg-green-100 text-green-800 border-green-300',
      update: 'bg-blue-100 text-blue-800 border-blue-300',
      delete: 'bg-red-100 text-red-800 border-red-300',
      view: 'bg-gray-100 text-gray-800 border-gray-300',
      login: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      logout: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      invite: 'bg-purple-100 text-purple-800 border-purple-300',
    };
    return colors[action] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getStatusColor = (status: string) => {
    return status === 'success'
      ? 'bg-green-50 border-green-200'
      : 'bg-red-50 border-red-200';
  };

  const getStatusBadge = (status: string) => {
    return status === 'success'
      ? 'bg-green-100 text-green-800 border-green-300'
      : 'bg-red-100 text-red-800 border-red-300';
  };

  const uniqueActions = [
    ...new Set(
      entries.map((e) => e.action).filter((a) => a)
    ),
  ];

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <h1 className="text-4xl font-bold text-black">Audit Log</h1>
          <p className="mt-2 text-gray-600">
            Complete record of organization activity and events
          </p>
        </div>

        {/* Filters */}
        <div className="mb-8 rounded-lg border-2 border-black bg-white p-6 shadow-brutal-lg">
          <div className="flex items-center gap-2 mb-4 font-bold text-black">
            <IconFilter size={20} />
            <span>Filters</span>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* Action Filter */}
            <div>
              <label className="mb-2 block text-sm font-bold text-black">Action</label>
              <select
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="w-full rounded border-2 border-black px-4 py-2 text-black"
              >
                <option value="">All Actions</option>
                {uniqueActions.map((action) => (
                  <option key={action} value={action}>
                    {action.charAt(0).toUpperCase() + action.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="mb-2 block text-sm font-bold text-black">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full rounded border-2 border-black px-4 py-2 text-black"
              >
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
              </select>
            </div>
          </div>
        </div>

        {/* Audit Log Table */}
        {isLoading ? (
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        ) : error ? (
          <div className="rounded-lg border-2 border-red-800 bg-red-50 p-4">
            <p className="text-red-800">Error: {error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border-4 border-black shadow-brutal-lg">
            <table className="w-full">
              <thead className="border-b-4 border-black bg-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left font-bold text-black">Timestamp</th>
                  <th className="px-6 py-4 text-left font-bold text-black">User</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Action</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Resource</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Description</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Status</th>
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-600">
                      No audit log entries found
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr
                      key={entry.id}
                      className={`border-b border-gray-200 ${getStatusColor(entry.status)}`}
                    >
                      <td className="px-6 py-4 text-sm font-mono text-gray-600">
                        {formatDate(entry.timestamp)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-semibold text-black">{entry.user_email || entry.user_id}</span>
                          {entry.ip_address && (
                            <span className="text-xs text-gray-500">{entry.ip_address}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block rounded-lg border-2 px-3 py-1 text-sm font-bold ${getActionColor(
                            entry.action
                          )}`}
                        >
                          {entry.action}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-semibold text-black">{entry.resource_type}</span>
                          {entry.resource_id && (
                            <span className="text-xs font-mono text-gray-500">{entry.resource_id}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">{entry.description}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block rounded-lg border-2 px-3 py-1 text-sm font-bold ${getStatusBadge(
                            entry.status
                          )}`}
                        >
                          {entry.status === 'success' ? '✓ Success' : '✗ Failed'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
          <h3 className="mb-4 font-bold text-black">About Audit Logs</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>
              • Audit logs record all administrative actions performed within the
              organization
            </li>
            <li>• Entries are retained for compliance and security purposes</li>
            <li>
              • Actions logged include member management, role changes, and settings
              modifications
            </li>
            <li>• Failures are recorded to help identify unauthorized access attempts</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

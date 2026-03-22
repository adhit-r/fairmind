/**
 * Audit Log Viewer Page
 *
 * Admin interface for viewing audit logs and user action history.
 * Provides compliance-ready audit trail for regulatory reporting.
 */

"use client";

import { useState, useEffect } from "react";
import { apiClient as api } from "@/lib/api/api-client";
import { IconDownload, IconFilter } from "@tabler/icons-react";

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: string;
  timestamp: string;
  ip_address: string;
  user_agent: string;
  details: Record<string, any>;
  error_message?: string;
}

export default function AdminAuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<{
    action?: string;
    status?: string;
    resource_type?: string;
  }>({});
  const [page, setPage] = useState(1);
  const [limit] = useState(25);

  // Fetch audit logs on mount and filter change
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setIsLoading(true);
        const params = new URLSearchParams({
          limit: limit.toString(),
          offset: ((page - 1) * limit).toString(),
          ...(filter.action && { action: filter.action }),
          ...(filter.status && { status: filter.status }),
          ...(filter.resource_type && { resource_type: filter.resource_type }),
        });

        const response = await api.get<{ logs: AuditLog[] }>(
          `/api/v1/audit-logs?${params}`
        );
        setLogs(response.logs || []);
        setError(null);
      } catch (err) {
        // If API endpoint doesn't exist yet, show placeholder data
        console.warn("Audit logs API not yet implemented:", err);
        setLogs([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLogs();
  }, [filter, page, limit]);

  const getStatusColor = (status: string) => {
    return status === "success"
      ? "text-green-600 font-semibold"
      : "text-red-600 font-semibold";
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString();
  };

  const handleExportCSV = () => {
    // Convert logs to CSV
    const headers = [
      "Timestamp",
      "User",
      "Action",
      "Resource Type",
      "Status",
      "IP Address",
    ];
    const rows = logs.map((log) => [
      formatDate(log.timestamp),
      log.user_id,
      log.action,
      log.resource_type,
      log.status,
      log.ip_address,
    ]);

    const csvContent =
      [headers, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(",")).join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-log-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <h1 className="text-4xl font-bold text-black">Audit Log</h1>
          <p className="mt-2 text-gray-600">
            View audit trail of user actions for compliance and security
          </p>
        </div>

        {/* Actions */}
        <div className="mb-6 flex flex-wrap gap-4">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 rounded-lg bg-black px-4 py-2 font-bold text-white hover:shadow-brutal-lg"
          >
            <IconDownload size={20} />
            Export as CSV
          </button>
          <button className="flex items-center gap-2 rounded-lg border-2 border-black bg-white px-4 py-2 font-bold text-black hover:shadow-brutal-lg">
            <IconFilter size={20} />
            Filters
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        ) : logs.length === 0 ? (
          <div className="rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
            <div className="text-center">
              <h3 className="text-xl font-bold text-black">No Audit Logs</h3>
              <p className="mt-2 text-gray-600">
                Audit logs will appear here as users interact with FairMind.
                The audit logging system tracks all significant actions for
                compliance and security purposes.
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border-4 border-black shadow-brutal-lg">
            <table className="w-full">
              <thead className="border-b-4 border-black bg-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Timestamp
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    User
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Action
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Resource
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    IP Address
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-gray-200 hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 font-mono text-sm text-gray-600">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 text-gray-800">{log.user_id}</td>
                    <td className="px-6 py-4 font-semibold text-black">
                      {log.action}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {log.resource_type}
                      {log.resource_id && ` (${log.resource_id.substring(0, 8)})`}
                    </td>
                    <td className={`px-6 py-4 ${getStatusColor(log.status)}`}>
                      {log.status}
                    </td>
                    <td className="px-6 py-4 font-mono text-sm text-gray-600">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {logs.length > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-gray-600">
              Page {page} • Showing {Math.min(limit, logs.length)} of{" "}
              {logs.length} logs
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="rounded-lg border-2 border-black px-4 py-2 font-bold disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={logs.length < limit}
                className="rounded-lg border-2 border-black px-4 py-2 font-bold disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 rounded-lg border-2 border-black bg-white p-6">
          <h3 className="mb-2 font-bold text-black">Audit Trail Information</h3>
          <p className="text-gray-600">
            All user actions are logged for compliance and security purposes.
            Audit logs include user identity, timestamp, action performed,
            affected resource, and result status. This information is essential
            for regulatory compliance and security investigations.
          </p>
        </div>
      </div>
    </div>
  );
}

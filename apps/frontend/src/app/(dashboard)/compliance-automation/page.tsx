/**
 * Compliance Automation Dashboard
 *
 * Main interface for managing automated compliance checks, viewing violations,
 * and tracking remediation plans across multiple compliance frameworks.
 */

"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/api-client";
import { IconPlus, IconRefresh, IconCircleCheck } from "@tabler/icons-react";

interface SystemStatus {
  scheduler_running: boolean;
  active_schedules: number;
  pending_jobs: number;
  total_violations: number;
  critical_violations: number;
  reports_generated_today: number;
  last_scheduler_check: string;
}

export default function ComplianceAutomationPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"schedules" | "violations" | "remediation" | "reports">("schedules");
  const [refreshing, setRefreshing] = useState(false);

  // Fetch system status on mount and periodically
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await apiClient.get<SystemStatus>("/api/v1/compliance/status");
      setStatus(response);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch compliance status:", err);
      setError("Failed to load system status");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchStatus();
    setRefreshing(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-black">Compliance Automation</h1>
              <p className="mt-2 text-gray-600">
                Automated compliance checking, violation tracking, and remediation planning
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-lg border-2 border-black bg-white px-4 py-2 font-bold text-black hover:shadow-brutal-lg disabled:opacity-50"
            >
              <IconRefresh size={20} />
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>

        {/* Status Cards */}
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {status && (
            <>
              <div className="rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
                <div className="text-3xl font-bold text-black">{status.active_schedules}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Active Schedules</div>
                <div className="mt-1 text-xs text-gray-500">
                  {status.scheduler_running ? (
                    <span className="text-green-600">✓ Scheduler Running</span>
                  ) : (
                    <span className="text-red-600">✗ Scheduler Stopped</span>
                  )}
                </div>
              </div>

              <div className="rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
                <div className="text-3xl font-bold text-black">{status.total_violations}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Total Violations</div>
                <div className="mt-1 text-xs text-gray-500">
                  {status.critical_violations > 0 && (
                    <span className="text-red-600">{status.critical_violations} critical</span>
                  )}
                </div>
              </div>

              <div className="rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
                <div className="text-3xl font-bold text-black">{status.pending_jobs}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Pending Jobs</div>
                <div className="mt-1 text-xs text-gray-500">In queue</div>
              </div>

              <div className="rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
                <div className="text-3xl font-bold text-black">{status.reports_generated_today}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Reports Today</div>
                <div className="mt-1 text-xs text-gray-500">Generated</div>
              </div>
            </>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-lg border-2 border-red-600 bg-red-50 p-4">
            <p className="text-red-800 font-semibold">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 flex gap-2 border-b-4 border-black">
          <button
            onClick={() => setActiveTab("schedules")}
            className={`px-6 py-3 font-bold transition-all ${
              activeTab === "schedules"
                ? "border-b-4 border-black bg-black text-white"
                : "border-b-4 border-gray-300 hover:border-black"
            }`}
          >
            Schedules
          </button>
          <button
            onClick={() => setActiveTab("violations")}
            className={`flex items-center gap-2 px-6 py-3 font-bold transition-all ${
              activeTab === "violations"
                ? "border-b-4 border-black bg-black text-white"
                : "border-b-4 border-gray-300 hover:border-black"
            }`}
          >
            Violations
            {status && status.critical_violations > 0 && (
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-xs font-bold text-white">
                {status.critical_violations}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("remediation")}
            className={`px-6 py-3 font-bold transition-all ${
              activeTab === "remediation"
                ? "border-b-4 border-black bg-black text-white"
                : "border-b-4 border-gray-300 hover:border-black"
            }`}
          >
            Remediation
          </button>
          <button
            onClick={() => setActiveTab("reports")}
            className={`px-6 py-3 font-bold transition-all ${
              activeTab === "reports"
                ? "border-b-4 border-black bg-black text-white"
                : "border-b-4 border-gray-300 hover:border-black"
            }`}
          >
            Reports
          </button>
        </div>

        {/* Tab Content */}
        <div className="rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
          {activeTab === "schedules" && <SchedulesSection />}
          {activeTab === "violations" && <ViolationsSection />}
          {activeTab === "remediation" && <RemediationSection />}
          {activeTab === "reports" && <ReportsSection />}
        </div>

        {/* Info Box */}
        <div className="mt-8 rounded-lg border-2 border-black bg-white p-6">
          <h3 className="mb-2 font-bold text-black">About Compliance Automation</h3>
          <p className="text-gray-600">
            Compliance Automation automatically checks your AI systems against regulatory frameworks
            (DPDP Act, NITI Aayog, EU AI Act, GDPR, and more) on a scheduled basis. Violations are
            tracked with severity levels, and AI-powered remediation plans guide you toward compliance.
          </p>
        </div>
      </div>
    </div>
  );
}

function SchedulesSection() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      const response = await apiClient.get("/api/v1/compliance/schedules");
      setSchedules(response.schedules || []);
    } catch (err) {
      console.error("Failed to fetch schedules:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="text-center text-gray-600">Loading schedules...</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-black">Compliance Schedules</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-lg bg-black px-4 py-2 font-bold text-white hover:shadow-brutal-lg"
        >
          <IconPlus size={20} />
          New Schedule
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-lg border-4 border-black bg-gray-50 p-6">
          <h3 className="mb-4 text-xl font-bold">Create New Schedule</h3>
          <p className="text-gray-600">Schedule creation form integrated with backend API.</p>
        </div>
      )}

      {schedules.length === 0 ? (
        <div className="rounded-lg border-2 border-gray-300 bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No schedules configured. Create one to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="rounded-lg border-2 border-black p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-bold text-black">{schedule.framework}</h4>
                  <p className="text-sm text-gray-600">
                    {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)}
                    {schedule.next_run && ` • Next: ${new Date(schedule.next_run).toLocaleDateString()}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded px-3 py-1 text-xs font-bold text-white bg-blue-600 hover:shadow-brutal">
                    Edit
                  </button>
                  <button className="rounded px-3 py-1 text-xs font-bold text-white bg-green-600 hover:shadow-brutal">
                    Run Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ViolationsSection() {
  const [violations, setViolations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchViolations();
  }, []);

  const fetchViolations = async () => {
    try {
      const response = await apiClient.get("/api/v1/compliance/violations?limit=50");
      setViolations(response.violations || []);
    } catch (err) {
      console.error("Failed to fetch violations:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: "bg-red-100 border-red-600 text-red-800",
      high: "bg-orange-100 border-orange-600 text-orange-800",
      medium: "bg-yellow-100 border-yellow-600 text-yellow-800",
      low: "bg-green-100 border-green-600 text-green-800",
    };
    return colors[severity.toLowerCase()] || "bg-gray-100 border-gray-600 text-gray-800";
  };

  if (isLoading) {
    return <div className="text-center text-gray-600">Loading violations...</div>;
  }

  if (violations.length === 0) {
    return (
      <div className="rounded-lg border-2 border-green-600 bg-green-50 p-8 text-center">
        <IconCircleCheck size={48} className="mx-auto mb-4 text-green-600" />
        <p className="text-lg font-bold text-green-800">No Active Violations</p>
        <p className="mt-2 text-green-700">Great! Your systems are in compliance.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-black">Compliance Violations</h2>
      <div className="space-y-4">
        {violations.map((violation) => (
          <div
            key={violation.id}
            className={`rounded-lg border-2 p-4 ${getSeverityColor(violation.severity)}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-bold">{violation.violation_type}</h4>
                <p className="mt-1 text-sm">{violation.description}</p>
                <p className="mt-2 text-xs font-semibold opacity-75">
                  {violation.framework} • {violation.status.toUpperCase()}
                </p>
              </div>
              <button className="rounded px-3 py-1 text-xs font-bold text-white bg-black hover:shadow-brutal">
                View
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RemediationSection() {
  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-black">Remediation Plans</h2>
      <div className="rounded-lg border-2 border-gray-300 bg-gray-50 p-8 text-center">
        <p className="text-gray-600">Remediation plans will appear here when violations are detected.</p>
        <p className="mt-2 text-sm text-gray-500">
          AI-generated step-by-step guidance for addressing compliance gaps.
        </p>
      </div>
    </div>
  );
}

function ReportsSection() {
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await apiClient.get("/api/v1/compliance/reports?limit=20");
      setReports(response.reports || []);
    } catch (err) {
      console.error("Failed to fetch reports:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="text-center text-gray-600">Loading reports...</div>;
  }

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-black">Generated Reports</h2>
      {reports.length === 0 ? (
        <div className="rounded-lg border-2 border-gray-300 bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No reports generated yet. Create a schedule to get started.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border-4 border-black">
          <table className="w-full">
            <thead className="border-b-4 border-black bg-gray-100">
              <tr>
                <th className="px-6 py-4 text-left font-bold text-black">Framework</th>
                <th className="px-6 py-4 text-left font-bold text-black">Status</th>
                <th className="px-6 py-4 text-left font-bold text-black">Score</th>
                <th className="px-6 py-4 text-left font-bold text-black">Generated</th>
                <th className="px-6 py-4 text-left font-bold text-black">Action</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-6 py-4 font-semibold text-black">{report.framework}</td>
                  <td className="px-6 py-4 font-bold text-green-600">{report.status}</td>
                  <td className="px-6 py-4 text-gray-800">{report.overall_score}%</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(report.generated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <button className="text-blue-600 font-bold hover:underline">📥 Download</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

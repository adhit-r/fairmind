/**
 * Compliance Automation Dashboard
 *
 * Main interface for managing automated compliance checks, viewing violations,
 * and tracking remediation plans across multiple compliance frameworks.
 */

"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/api-client";
import { useToast } from "@/hooks/use-toast";
import { IconPlus, IconRefresh, IconCircleCheck, IconCircleX, IconDownload } from "@tabler/icons-react";

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
      if (response.data) setStatus(response.data);
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
      <div className="min-w-0">
        <div className="mx-auto max-w-7xl">
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-[2px] border-[var(--fm-line)] border-t-[var(--fm-ink)]" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-w-0">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 border-b border-[var(--fm-line)] pb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-[30px] font-semibold tracking-[-.03em] text-black">Compliance Automation</h1>
              <p className="mt-2 text-gray-600">
                Automated compliance checking, violation tracking, and remediation planning
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-lg border border-[var(--fm-line)] bg-white px-4 py-2 font-bold text-black disabled:opacity-50"
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
              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.active_schedules}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Active Schedules</div>
                <div className="mt-1 text-xs text-gray-500">
                  {status.scheduler_running ? (
                    <span className="inline-flex items-center gap-1 text-green-600"><IconCircleCheck className="h-3.5 w-3.5" aria-hidden /> Scheduler Running</span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-red-600"><IconCircleX className="h-3.5 w-3.5" aria-hidden /> Scheduler Stopped</span>
                  )}
                </div>
              </div>

              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.total_violations}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Total Violations</div>
                <div className="mt-1 text-xs text-gray-500">
                  {status.critical_violations > 0 && (
                    <span className="text-red-600">{status.critical_violations} critical</span>
                  )}
                </div>
              </div>

              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.pending_jobs}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Pending Jobs</div>
                <div className="mt-1 text-xs text-gray-500">In queue</div>
              </div>

              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.reports_generated_today}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Reports Today</div>
                <div className="mt-1 text-xs text-gray-500">Generated</div>
              </div>
            </>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-600 bg-red-50 p-4">
            <p className="text-red-800 font-semibold">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveTab("schedules")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "schedules"
                ? "bg-[var(--fm-ink)] text-white"
                : "text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)] hover:text-[var(--fm-ink)]"
            }`}
          >
            Schedules
          </button>
          <button
            onClick={() => setActiveTab("violations")}
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "violations"
                ? "bg-[var(--fm-ink)] text-white"
                : "text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)] hover:text-[var(--fm-ink)]"
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
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "remediation"
                ? "bg-[var(--fm-ink)] text-white"
                : "text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)] hover:text-[var(--fm-ink)]"
            }`}
          >
            Remediation
          </button>
          <button
            onClick={() => setActiveTab("reports")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "reports"
                ? "bg-[var(--fm-ink)] text-white"
                : "text-[var(--fm-ink2)] hover:bg-[var(--fm-bg)] hover:text-[var(--fm-ink)]"
            }`}
          >
            Reports
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-8 fm-card">
          {activeTab === "schedules" && <SchedulesSection />}
          {activeTab === "violations" && <ViolationsSection />}
          {activeTab === "remediation" && <RemediationSection />}
          {activeTab === "reports" && <ReportsSection />}
        </div>

        {/* Info Box */}
        <div className="mt-8 rounded-lg border border-[var(--fm-line)] bg-white p-6">
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

// Mirrors the backend FrameworkEnum values.
const FRAMEWORKS: Array<[string, string]> = [
  ["DPDP_ACT_2023", "DPDP Act 2023"],
  ["NITI_AAYOG_PRINCIPLES", "NITI Aayog Principles"],
  ["MEITY_GUIDELINES", "MeitY Guidelines"],
  ["EU_AI_ACT", "EU AI Act"],
  ["GDPR", "GDPR"],
  ["ISO_IEC_42001", "ISO/IEC 42001"],
  ["NIST_AI_RMF", "NIST AI RMF"],
  ["IEEE_7000", "IEEE 7000"],
];

function SchedulesSection() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [running, setRunning] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [framework, setFramework] = useState(FRAMEWORKS[0][0]);
  const [frequency, setFrequency] = useState("weekly");
  const [recipients, setRecipients] = useState("");
  const { toast } = useToast();

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      const response = await apiClient.get("/api/v1/compliance/schedules");
      setSchedules((response.data as any)?.schedules || []);
    } catch (err) {
      console.error("Failed to fetch schedules:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const createSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const response = await apiClient.post("/api/v1/compliance/schedules", {
        framework,
        frequency,
        recipients: recipients.split(",").map((r) => r.trim()).filter(Boolean),
      });
      if (!response.success) throw new Error(response.error || "Failed to create the schedule");
      toast({ title: "Schedule created" });
      setRecipients("");
      setShowForm(false);
      await fetchSchedules();
    } catch (err) {
      toast({ title: "Could not create the schedule", description: err instanceof Error ? err.message : "Request failed", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  };

  const runNow = async (id: string) => {
    setRunning(id);
    try {
      const response = await apiClient.post(`/api/v1/compliance/schedules/${id}/run`);
      if (!response.success) throw new Error(response.error || "Failed to start the run");
      toast({ title: "Run started", description: "The compliance check is running now." });
    } catch (err) {
      toast({ title: "Could not start the run", description: err instanceof Error ? err.message : "Request failed", variant: "destructive" });
    } finally {
      setRunning(null);
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
          className="flex items-center gap-2 rounded-full bg-[var(--fm-ink)] px-4 py-2 font-semibold text-white"
        >
          <IconPlus size={20} />
          New Schedule
        </button>
      </div>

      {showForm && (
        <form onSubmit={createSchedule} className="mb-6 grid gap-4 rounded-[14px] border border-[var(--fm-line)] bg-white p-6 md:grid-cols-2">
          <h3 className="text-xl font-semibold md:col-span-2">Create New Schedule</h3>
          <label className="grid gap-1 text-sm font-semibold">
            Framework
            <select value={framework} onChange={(e) => setFramework(e.target.value)} className="h-10 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 font-normal">
              {FRAMEWORKS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-semibold">
            Frequency
            <select value={frequency} onChange={(e) => setFrequency(e.target.value)} className="h-10 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 font-normal">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm font-semibold md:col-span-2">
            Recipients (comma-separated emails)
            <input value={recipients} onChange={(e) => setRecipients(e.target.value)} required className="h-10 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 font-normal" />
          </label>
          <div className="md:col-span-2">
            <button type="submit" disabled={creating} className="rounded-full bg-[var(--fm-ink)] px-4 py-2 font-semibold text-white disabled:opacity-50">
              {creating ? "Creating..." : "Create schedule"}
            </button>
          </div>
        </form>
      )}

      {schedules.length === 0 ? (
        <div className="rounded-lg border border-gray-300 bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No schedules configured. Create one to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="rounded-lg border border-[var(--fm-line)] p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-bold text-black">{schedule.framework}</h4>
                  <p className="text-sm text-gray-600">
                    {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)}
                    {schedule.next_run && ` • Next: ${new Date(schedule.next_run).toLocaleDateString()}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => runNow(schedule.id)}
                    disabled={running === schedule.id}
                    className="rounded-full bg-[var(--fm-ink)] px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
                  >
                    {running === schedule.id ? "Starting..." : "Run Now"}
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
      setViolations((response.data as any)?.violations || []);
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
      <div className="rounded-lg border border-green-600 bg-green-50 p-8 text-center">
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
            className={`rounded-lg border p-4 ${getSeverityColor(violation.severity)}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-bold">{violation.violation_type}</h4>
                <p className="mt-1 text-sm">{violation.description}</p>
                <p className="mt-2 text-xs font-semibold opacity-75">
                  {violation.framework} • {violation.status.toUpperCase()}
                </p>
              </div>
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
      <div className="rounded-lg border border-gray-300 bg-gray-50 p-8 text-center">
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
      setReports((response.data as any)?.reports || []);
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
        <div className="rounded-lg border border-gray-300 bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No reports generated yet. Create a schedule to get started.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[var(--fm-line)]">
          <table className="w-full">
            <thead className="border-b border-[var(--fm-line)] bg-gray-100">
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
                    <button className="inline-flex items-center gap-1 text-blue-600 font-bold hover:underline"><IconDownload className="h-4 w-4" aria-hidden /> Download</button>
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

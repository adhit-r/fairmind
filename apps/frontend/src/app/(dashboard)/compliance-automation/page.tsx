/**
 * Compliance Automation Dashboard
 *
 * Main interface for managing automated compliance checks, viewing violations,
 * and tracking remediation plans across multiple compliance frameworks.
 */

"use client";

import { pollWhileVisible } from '@/lib/poll'
import { useState, useEffect } from "react";
import { useOrgResource, withOrg } from "@/lib/api/hooks/usePacks";
import { useOrg } from "@/context/OrgContext";
import type { AutomationStatus, ComplianceSchedule, ComplianceViolation, ComplianceReport } from "@/lib/api/compliance-automation-service";
import { apiClient } from "@/lib/api/api-client";
import { useToast } from "@/hooks/use-toast";
import { IconPlus, IconRefresh, IconCircleCheck, IconCircleX, IconDownload } from "@tabler/icons-react";

function ReadError({ message, retry }: { message: string; retry: () => void }) {
  return (
    <div role="alert" className="my-4 rounded-lg border border-[var(--fm-line)] p-4">
      <p>{message}</p>
      <button className="mt-2 font-semibold underline" onClick={retry}>Try again</button>
    </div>
  );
}

function useComplianceList<T>(field: string, query: string) {
  const resource = useOrgResource<{ [key: string]: unknown }>(`/api/v1/compliance/${field}${query}`);
  const rows = resource.data?.[field];
  const total = resource.data?.total;
  const completePage = Array.isArray(rows) && typeof total === "number" && Number.isInteger(total) && total >= rows.length && (rows.length > 0 || total === 0);
  return {
    rows: completePage ? rows as T[] : [],
    total: completePage ? total : null,
    loading: resource.loading,
    error: resource.error || (!resource.loading && !completePage ? `The ${field} response was incomplete.` : null),
    reload: resource.reload,
  };
}

export default function ComplianceAutomationPage() {
  const summary = useOrgResource<AutomationStatus>("/api/v1/compliance/status");
  const status = summary.data;
  const valid = status && typeof status.scheduler_running === "boolean" &&
    [status.active_schedules, status.pending_jobs, status.total_violations, status.critical_violations, status.reports_generated_today].every((count) => Number.isInteger(count) && count >= 0);
  const error = summary.error || (!summary.loading && !valid ? "The automation summary was incomplete." : null);
  const [activeTab, setActiveTab] = useState<"schedules" | "violations" | "remediation" | "reports">("schedules");
  useEffect(() => pollWhileVisible(summary.reload, 30000), [summary.reload]);

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
              onClick={summary.reload}
              disabled={summary.loading}
              className="flex items-center gap-2 rounded-lg border border-[var(--fm-line)] bg-white px-4 py-2 font-bold text-black disabled:opacity-50"
            >
              <IconRefresh size={20} />
              {summary.loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>

        {/* Status Cards */}
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {summary.loading && <p role="status">Loading automation summary...</p>}
          {!summary.loading && !error && valid && (
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
                <div className="mt-2 text-sm font-semibold text-gray-600">Unresolved Violations</div>
                <div className="mt-1 text-xs text-gray-500">
                  {status.critical_violations > 0 && (
                    <span className="text-red-600">{status.critical_violations} critical</span>
                  )}
                </div>
              </div>

              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.pending_jobs}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Scheduler Jobs</div>
                <div className="mt-1 text-xs text-gray-500">Across the scheduler</div>
              </div>

              <div className="p-6 fm-card">
                <div className="text-[24px] font-semibold tracking-tight text-black">{status.reports_generated_today}</div>
                <div className="mt-2 text-sm font-semibold text-gray-600">Schedules Run Today</div>
                <div className="mt-1 text-xs text-gray-500">Since 00:00 UTC</div>
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
            {!summary.loading && !error && valid && status.critical_violations > 0 && (
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
            tracked with severity levels. Remediation plans are coming soon.
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
  const { selectedOrg } = useOrg();
  const { rows: schedules, loading: isLoading, error, reload } = useComplianceList<ComplianceSchedule>("schedules", "");
  const [showForm, setShowForm] = useState(false);
  const [running, setRunning] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [framework, setFramework] = useState(FRAMEWORKS[0][0]);
  const [frequency, setFrequency] = useState("weekly");
  const [recipients, setRecipients] = useState("");
  const { toast } = useToast();

  const createSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrg) return;
    setCreating(true);
    try {
      const response = await apiClient.post(withOrg("/api/v1/compliance/schedules", selectedOrg.id), {
        framework,
        frequency,
        recipients: recipients.split(",").map((r) => r.trim()).filter(Boolean),
      });
      if (!response.success) throw new Error(response.error || "Failed to create the schedule");
      toast({ title: "Schedule created" });
      setRecipients("");
      setShowForm(false);
      reload();
    } catch (err) {
      toast({ title: "Could not create the schedule", description: err instanceof Error ? err.message : "Request failed", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  };

  const runNow = async (id: string) => {
    if (!selectedOrg) return;
    setRunning(id);
    try {
      const response = await apiClient.post(withOrg(`/api/v1/compliance/schedules/${encodeURIComponent(id)}/run`, selectedOrg.id));
      if (!response.success) throw new Error(response.error || "Failed to start the run");
      toast({ title: "Run started", description: "The compliance check is running now." });
    } catch (err) {
      toast({ title: "Could not start the run", description: err instanceof Error ? err.message : "Request failed", variant: "destructive" });
    } finally {
      setRunning(null);
    }
  };

  if (error) return <ReadError message={`Schedules unavailable. ${error}`} retry={reload} />;
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
  const { selectedOrg } = useOrg();
  const { rows: violations, total, loading: isLoading, error, reload } = useComplianceList<ComplianceViolation>("violations", "?limit=50");
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

  if (error) return <ReadError message={`Violations unavailable. ${error}`} retry={reload} />;

  if (violations.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--fm-line)] p-8 text-center">
        <h2 className="text-lg font-bold">No recorded violations</h2>
        <p className="mt-2">The violation register for {selectedOrg?.name} contains no records across all dates. Assessment coverage is unknown.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-black">Compliance Violations</h2>
      <p className="mb-6">Showing {violations.length} of {total} recorded violations for {selectedOrg?.name} across all dates.</p>
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
        <p className="font-semibold text-gray-700">Coming soon</p>
        <p className="mt-2 text-sm text-gray-500">
          Remediation plans are not generated here yet. Track fixes for findings under Findings.
        </p>
      </div>
    </div>
  );
}

function ReportsSection() {
  const { rows: reports, loading: isLoading, error, reload } = useComplianceList<ComplianceReport>("reports", "?limit=20");
  if (error) return <ReadError message={`Report history unavailable. ${error}`} retry={reload} />;
  if (isLoading) {
    return <div className="text-center text-gray-600">Loading reports...</div>;
  }

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-black">Generated Reports</h2>
      {reports.length === 0 ? (
        <div className="rounded-lg border border-gray-300 bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No reports recorded.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[var(--fm-line)]">
          <table className="w-full">
            <thead className="border-b border-[var(--fm-line)] bg-gray-100">
              <tr>
                <th scope="col" className="px-6 py-4 text-left font-bold text-black">Framework</th>
                <th scope="col" className="px-6 py-4 text-left font-bold text-black">Status</th>
                <th scope="col" className="px-6 py-4 text-left font-bold text-black">Score</th>
                <th scope="col" className="px-6 py-4 text-left font-bold text-black">Generated</th>
                <th scope="col" className="px-6 py-4 text-left font-bold text-black">Action</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-6 py-4 font-semibold text-black">{report.framework}</td>
                  <td className="px-6 py-4 font-bold">{report.status}</td>
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

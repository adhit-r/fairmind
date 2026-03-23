'use client';

import { useState, useEffect } from 'react';
import { useOrg } from '@/context/OrgContext';
import { apiClient } from '@/lib/api/api-client';
import { AuditReportPanel } from '@/components/compliance/AuditReportPanel';
import { MetricsCards } from '@/components/compliance/MetricsCards';
import { EventsTimeline } from '@/components/compliance/EventsTimeline';
import { ActionDistributionChart } from '@/components/compliance/ActionDistributionChart';
import { AuditLogTable } from '@/components/compliance/AuditLogTable';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

interface AuditReport {
  report_period: { start: string; end: string };
  summary: {
    total_events: number;
    unique_users: number;
    top_actions: Array<{ action: string; count: number }>;
  };
  metrics: {
    events_per_day: Array<{ date: string; count: number }>;
    action_distribution: Array<{ action: string; count: number }>;
    top_users: Array<{ email: string; count: number }>;
  };
  audit_log: Array<{
    timestamp: string;
    user_email: string;
    action: string;
    resource_type: string;
    resource_id: string;
    ip_address: string;
  }>;
}

export default function ComplianceDashboard() {
  const { selectedOrg } = useOrg();
  const [reportData, setReportData] = useState<AuditReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);

  // Load initial data (last 30 days)
  useEffect(() => {
    if (selectedOrg?.id) {
      loadDashboardData();
    }
  }, [selectedOrg?.id]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 30);

      const startDateStr = startDate.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];

      const url = `/api/v1/organizations/${selectedOrg?.id}/compliance/audit-report?start_date=${startDateStr}&end_date=${endDateStr}&format=json`;
      const response = await apiClient.get<AuditReport>(url);

      if (response.success && response.data) {
        setReportData(response.data);
      } else {
        setError(response.error || 'Failed to load audit data');
      }
    } catch (err) {
      setError('Failed to load audit data');
      console.error('Error loading dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async (
    format: 'json' | 'csv' | 'pdf',
    startDate: string,
    endDate: string
  ) => {
    setIsGenerating(true);
    setReportError(null);
    setReportSuccess(false);

    try {
      const url = `/api/v1/organizations/${selectedOrg?.id}/compliance/audit-report?start_date=${startDate}&end_date=${endDate}&format=${format}`;
      const response = await apiClient.get(url);

      if (response.success) {
        if (format === 'json') {
          // For JSON, update the state
          setReportData(response.data as AuditReport);
          setReportSuccess(true);
        } else {
          // For CSV/PDF, response.data contains the file content
          // Use a fetch request for binary data instead
          const fetchUrl = `/api/proxy/api/v1/organizations/${selectedOrg?.id}/compliance/audit-report?start_date=${startDate}&end_date=${endDate}&format=${format}`;
          const fileResponse = await fetch(fetchUrl);
          if (!fileResponse.ok) {
            throw new Error('Failed to download file');
          }
          const blob = await fileResponse.blob();
          const downloadUrl = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = downloadUrl;
          a.download = `audit-report-${endDate}.${format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(downloadUrl);
          setReportSuccess(true);
        }

        setTimeout(() => setReportSuccess(false), 3000);
      } else {
        setReportError(response.error || 'Failed to generate report');
      }
    } catch (err) {
      setReportError('Failed to generate report. Please try again.');
      console.error('Error generating report:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">COMPLIANCE DASHBOARD</h1>
        <p className="text-gray-600 font-medium">
          Audit logs and compliance metrics for {selectedOrg?.name || 'your organization'}
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="border-2 border-red-600 bg-red-50">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <AlertDescription className="text-red-800 font-medium">{error}</AlertDescription>
        </Alert>
      )}

      {/* Audit Report Generator */}
      <AuditReportPanel
        onGenerateReport={handleGenerateReport}
        isLoading={isGenerating}
        error={reportError}
        success={reportSuccess}
      />

      {/* Metrics */}
      {reportData && (
        <>
          <MetricsCards
            totalEvents={reportData.summary.total_events}
            activeUsers={reportData.summary.unique_users}
            topAction={reportData.summary.top_actions[0]}
            isLoading={isLoading}
          />

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EventsTimeline
              data={reportData.metrics.events_per_day}
              isLoading={isLoading}
            />
            <ActionDistributionChart
              data={reportData.metrics.action_distribution}
              onActionClick={setSelectedAction}
              isLoading={isLoading}
            />
          </div>

          {/* Audit Log Table */}
          <AuditLogTable
            data={reportData.audit_log}
            isLoading={isLoading}
            actionFilter={selectedAction || undefined}
          />

          {selectedAction && (
            <div className="text-center">
              <button
                onClick={() => setSelectedAction(null)}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium underline"
              >
                Clear filter
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

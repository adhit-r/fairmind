'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { BTN, BTN_P, LABEL, MUTED } from '@/components/packs/parts'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { ReportHistoryTable, type SavedReport } from '../../audit-reports/components/ReportHistoryTable'
import { ReportPreview } from '../../audit-reports/components/ReportPreview'
import { reportMatchesAssuranceScope } from './assurancePdf'

type ReportSystem = {
  id: string
  name: string
  owner: string
  riskTier: string
  lifecycleStage: string
  readiness: number
}

function downloadJson(report: SavedReport) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${report.title.replace(/\s+/g, '_')}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

async function downloadExport(report: SavedReport, format: 'pdf' | 'docx'): Promise<string | null> {
  // The server renders the stored snapshot; nothing here is typeset from client state.
  const response = await apiClient.get<Blob>(API_ENDPOINTS.aiGovernance.exportReport(report.id, format), { responseType: 'blob' })
  if (!response.success || !response.data) return response.error || `Could not export the ${format.toUpperCase()}`
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${report.title.replace(/\s+/g, '_')}.${format}`
  anchor.click()
  URL.revokeObjectURL(url)
  return null
}

export function AssuranceReportStudio({
  system,
  frameworkLabel,
  readOnly,
}: {
  system: ReportSystem
  frameworkLabel: string
  readOnly: boolean
}) {
  const scopeKey = `${system.id}:${frameworkLabel}`
  const scopeKeyRef = useRef(scopeKey)
  scopeKeyRef.current = scopeKey
  const historyRequestIdRef = useRef(0)
  const generationRequestIdRef = useRef(0)
  const [historySnapshot, setHistorySnapshot] = useState<{
    scopeKey: string
    reports: SavedReport[]
    loading: boolean
    error: string | null
  }>({ scopeKey, reports: [], loading: true, error: null })
  const [generationSnapshot, setGenerationSnapshot] = useState({ scopeKey, loading: false })
  const [previewSnapshot, setPreviewSnapshot] = useState<{ scopeKey: string; report: SavedReport } | null>(null)
  const history = historySnapshot.scopeKey === scopeKey ? historySnapshot.reports : []
  const historyLoading = historySnapshot.scopeKey !== scopeKey || historySnapshot.loading
  const error = historySnapshot.scopeKey === scopeKey ? historySnapshot.error : null
  const generating = generationSnapshot.scopeKey === scopeKey && generationSnapshot.loading
  const preview = previewSnapshot?.scopeKey === scopeKey ? previewSnapshot.report : null

  const reportMatchesScope = useCallback((report: SavedReport) => {
    return reportMatchesAssuranceScope(report, system.id, frameworkLabel)
  }, [frameworkLabel, system.id])

  const loadHistory = useCallback(async () => {
    const targetScope = scopeKey
    const requestId = ++historyRequestIdRef.current
    setHistorySnapshot({ scopeKey: targetScope, reports: [], loading: true, error: null })
    try {
      const response = await apiClient.get<SavedReport[]>(
        `${API_ENDPOINTS.aiGovernance.listReports}?system_id=${encodeURIComponent(system.id)}`,
      )
      if (!response.success) throw new Error(response.error || 'Saved report history is unavailable')
      if (requestId === historyRequestIdRef.current && scopeKeyRef.current === targetScope) {
        setHistorySnapshot({
          scopeKey: targetScope,
          reports: (response.data || []).filter(reportMatchesScope),
          loading: false,
          error: null,
        })
      }
    } catch (reason) {
      if (requestId === historyRequestIdRef.current && scopeKeyRef.current === targetScope) {
        setHistorySnapshot({
          scopeKey: targetScope,
          reports: [],
          loading: false,
          error: reason instanceof Error ? reason.message : 'Saved report history is unavailable',
        })
      }
    }
  }, [reportMatchesScope, scopeKey, system.id])

  useEffect(() => {
    setPreviewSnapshot(null)
    void loadHistory()
  }, [loadHistory])

  const exportReport = async (report: SavedReport, format: 'pdf' | 'docx') => {
    const failure = await downloadExport(report, format)
    if (failure) setHistorySnapshot((current) => ({ ...current, error: failure }))
  }

  const generate = async () => {
    const targetScope = scopeKey
    const requestId = ++generationRequestIdRef.current
    setGenerationSnapshot({ scopeKey: targetScope, loading: true })
    try {
      const response = await apiClient.post<SavedReport>(API_ENDPOINTS.aiGovernance.generateReport, {
        system_id: system.id,
        report_type: 'governance',
        title: 'Governance Assurance Summary',
        frameworks: [frameworkLabel],
        sections: ['executive_summary', 'risk_overview', 'evidence_summary', 'remediations', 'decision_log'],
      })
      if (!response.success || !response.data) throw new Error(response.error || 'Report generation failed')
      if (requestId === generationRequestIdRef.current && scopeKeyRef.current === targetScope) {
        const generated = response.data
        setPreviewSnapshot({ scopeKey: targetScope, report: generated })
        setHistorySnapshot((current) => current.scopeKey === targetScope
          ? {
              ...current,
              reports: [generated, ...current.reports.filter((report) => report.id !== generated.id)],
              error: null,
            }
          : current)
      }
    } catch (reason) {
      if (requestId === generationRequestIdRef.current && scopeKeyRef.current === targetScope) {
        setHistorySnapshot((current) => current.scopeKey === targetScope
          ? { ...current, error: reason instanceof Error ? reason.message : 'Report generation failed' }
          : current)
      }
    } finally {
      if (requestId === generationRequestIdRef.current && scopeKeyRef.current === targetScope) {
        setGenerationSnapshot({ scopeKey: targetScope, loading: false })
      }
    }
  }

  return (
    <section aria-label="Report builder and history" className="fm-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-[15px] font-semibold">Assurance Report Studio</h2>
          <p className={`mt-1 max-w-[640px] text-[12.5px] ${MUTED}`}>
            Saved snapshots of the risks, evidence, remediation and decisions recorded for {system.name}, ready to export as PDF, DOCX or JSON. A snapshot does not change the assurance summary above.
          </p>
        </div>
        <button type="button" disabled={historyLoading} onClick={() => void loadHistory()} className={BTN}>
          Refresh history
        </button>
      </div>

      {error ? <p role="alert" className="mt-3 rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p> : null}

      {!readOnly ? (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[10px] bg-[var(--fm-bg)] px-4 py-3">
          <div className="min-w-0">
            <p className={LABEL}>Scope</p>
            <p className="mt-0.5 text-[13.5px] font-semibold">{system.name} · {frameworkLabel}</p>
          </div>
          <button type="button" disabled={generating} onClick={() => void generate()} className={BTN_P}>
            {generating ? 'Generating report' : 'Generate report'}
          </button>
        </div>
      ) : (
        <p className={`mt-4 rounded-[10px] bg-[var(--fm-bg)] px-4 py-3 text-[12.5px] ${MUTED}`}>
          Auditor mode can preview and export saved reports but cannot generate a new one.
        </p>
      )}

      {preview ? (
        <div className="mt-4">
          <p className={`mb-2 text-[12.5px] font-semibold ${MUTED}`}>Selected preview · {preview.title}</p>
          <ReportPreview
            reportType={preview.reportType}
            system={preview.data.system}
            data={preview.data}
            sections={preview.config.sections || []}
            frameworks={preview.config.frameworks || []}
          />
        </div>
      ) : null}

      <h3 className="mt-5 text-[13.5px] font-semibold">Saved reports</h3>
      {/* A failed history load has already said so above; an empty list would claim nothing was saved. */}
      {error && history.length === 0 ? null : (
        <ReportHistoryTable
          reports={history}
          loading={historyLoading}
          onPreview={(report) => setPreviewSnapshot({ scopeKey, report })}
          onDownloadJson={downloadJson}
          onDownloadPdf={(report) => void exportReport(report, 'pdf')}
          onDownloadDocx={(report) => void exportReport(report, 'docx')}
        />
      )}
    </section>
  )
}

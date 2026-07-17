'use client'

import { useCallback, useEffect, useState } from 'react'
import { IconFileAnalytics, IconLoader2, IconRefresh } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { ReportHistoryTable, type SavedReport } from '../../audit-reports/components/ReportHistoryTable'
import { ReportPreview } from '../../audit-reports/components/ReportPreview'

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

async function downloadPdf(report: SavedReport) {
  const { jsPDF } = await import('jspdf')
  const document = new jsPDF({ unit: 'pt', format: 'a4' })
  const system = report.data.system || {}
  document.setFont('helvetica', 'bold')
  document.setFontSize(18)
  document.text(report.title, 40, 48)
  document.setFont('helvetica', 'normal')
  document.setFontSize(10)
  document.text(`Generated ${new Date(report.createdAt).toLocaleString()}`, 40, 70)
  document.text(`System: ${system.name || report.systemId}`, 40, 92)
  document.text(`Framework scope: ${report.config.frameworks?.join(', ') || 'Not recorded'}`, 40, 110)
  document.text('This operational snapshot does not constitute certification or an assurance opinion.', 40, 138)
  document.save(`${report.title.replace(/\s+/g, '_')}.pdf`)
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
  const [history, setHistory] = useState<SavedReport[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<SavedReport | null>(null)

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const response = await apiClient.get<SavedReport[]>(
        `${API_ENDPOINTS.aiGovernance.listReports}?system_id=${encodeURIComponent(system.id)}`,
      )
      if (!response.success) throw new Error(response.error || 'Saved report history is unavailable')
      setHistory(response.data || [])
      setError(null)
    } catch (reason) {
      setHistory([])
      setError(reason instanceof Error ? reason.message : 'Saved report history is unavailable')
    } finally {
      setHistoryLoading(false)
    }
  }, [system.id])

  useEffect(() => {
    setPreview(null)
    void loadHistory()
  }, [loadHistory])

  const generate = async () => {
    setGenerating(true)
    try {
      const response = await apiClient.post<SavedReport>(API_ENDPOINTS.aiGovernance.generateReport, {
        system_id: system.id,
        report_type: 'governance',
        title: 'Governance Assurance Summary',
        frameworks: [frameworkLabel],
        sections: ['executive_summary', 'risk_overview', 'evidence_summary', 'remediations', 'decision_log'],
      })
      if (!response.success || !response.data) throw new Error(response.error || 'Report generation failed')
      setPreview(response.data)
      setHistory((current) => [response.data!, ...current.filter((report) => report.id !== response.data!.id)])
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Report generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <section aria-label="Report builder and history" className="border-4 border-[#0F1412] bg-[#FCFDF8] shadow-[8px_8px_0_0_#0F1412]">
      <div className="flex flex-col gap-3 border-b-4 border-[#0F1412] bg-[#F3F5F0] p-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[#0B7659]">Saved operational reports</p>
          <h2 className="mt-1 text-xl font-black uppercase">Assurance Report Studio</h2>
          <p className="mt-1 max-w-[70ch] text-sm text-[#59615D]">Generate, preview, export, and revisit operational report snapshots for {system.name}. Framework assurance remains governed by the transparent summary above.</p>
        </div>
        <Button type="button" variant="neutral" onClick={() => void loadHistory()} className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] font-black uppercase">
          <IconRefresh aria-hidden="true" /> Refresh history
        </Button>
      </div>

      {error ? <p role="alert" className="m-5 border-2 border-[#D83A2E] bg-[#FFF0ED] p-3 text-sm font-bold">{error}</p> : null}

      {!readOnly ? (
        <div className="grid gap-4 border-b-2 border-[#0F1412] p-5 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="text-xs font-black uppercase text-[#59615D]">Pinned generator scope</p>
            <p className="mt-1 font-black">{system.name} · {frameworkLabel}</p>
            <p className="mt-1 text-sm text-[#59615D]">The generated legacy operational snapshot is stored in report history. It does not replace the evidence-hash assurance summary.</p>
          </div>
          <Button type="button" disabled={generating} onClick={() => void generate()} className="rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]">
            {generating ? <IconLoader2 aria-hidden="true" className="animate-spin" /> : <IconFileAnalytics aria-hidden="true" />}
            {generating ? 'Generating report' : 'Generate report'}
          </Button>
        </div>
      ) : (
        <p className="border-b-2 border-[#0F1412] bg-[#E5F4EF] p-4 text-sm font-bold">Auditor mode can preview and export saved reports but cannot generate a new snapshot.</p>
      )}

      {preview ? (
        <div className="border-b-2 border-[#0F1412] p-5">
          <p className="mb-3 text-xs font-black uppercase tracking-[0.12em] text-[#59615D]">Selected preview · {preview.title}</p>
          <ReportPreview
            reportType={preview.reportType}
            system={preview.data.system}
            data={preview.data}
            sections={preview.config.sections || []}
            frameworks={preview.config.frameworks || []}
          />
        </div>
      ) : null}

      <div className="p-5">
        <h3 className="mb-3 font-black uppercase">Saved Report History</h3>
        <ReportHistoryTable
          reports={history}
          loading={historyLoading}
          onPreview={setPreview}
          onDownloadJson={downloadJson}
          onDownloadPdf={(report) => void downloadPdf(report)}
        />
      </div>
    </section>
  )
}

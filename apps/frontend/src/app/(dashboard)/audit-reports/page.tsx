'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  IconCheck,
  IconChevronDown,
  IconDownload,
  IconFileAnalytics,
  IconLoader2,
  IconRefresh,
  IconSettings,
} from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useModelInventory } from '@/lib/api/hooks/useModelInventory'
import { ReportPreview } from './components/ReportPreview'
import { ReportHistoryTable, type SavedReport } from './components/ReportHistoryTable'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REPORT_TYPES = [
  {
    id: 'compliance',
    label: 'Compliance Audit',
    description: 'Framework scores, control status, gaps, evidence references',
    color: 'border-blue-500 bg-blue-50 text-blue-800',
  },
  {
    id: 'bias',
    label: 'Bias Assessment',
    description: 'Scan results, demographic parity, threshold violations',
    color: 'border-purple-500 bg-purple-50 text-purple-800',
  },
  {
    id: 'governance',
    label: 'Governance Summary',
    description: 'Lifecycle, approvals, open risks, remediation status',
    color: 'border-emerald-500 bg-emerald-50 text-emerald-800',
  },
]

const ALL_FRAMEWORKS = ['EU AI Act', 'ISO 42001', 'NIST AI RMF', 'GDPR', 'DPDP Act']

const ALL_SECTIONS = [
  { id: 'executive_summary', label: 'Executive Summary' },
  { id: 'risk_overview', label: 'Risk Overview' },
  { id: 'compliance_status', label: 'Compliance Status' },
  { id: 'evidence_summary', label: 'Evidence Summary' },
  { id: 'remediations', label: 'Open Remediations' },
  { id: 'decision_log', label: 'Decision Log' },
]

// ---------------------------------------------------------------------------
// PDF generation helper (client-side via jspdf)
// ---------------------------------------------------------------------------

async function generatePdf(report: SavedReport): Promise<void> {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })

  const pageW = doc.internal.pageSize.getWidth()
  const margin = 40
  let y = margin

  const addLine = (text: string, size = 11, bold = false, gap = 6) => {
    doc.setFontSize(size)
    doc.setFont('helvetica', bold ? 'bold' : 'normal')
    const lines = doc.splitTextToSize(text, pageW - margin * 2)
    for (const line of lines) {
      if (y > doc.internal.pageSize.getHeight() - margin) {
        doc.addPage()
        y = margin
      }
      doc.text(line, margin, y)
      y += size + gap
    }
  }

  const addSection = (title: string) => {
    y += 8
    addLine(title.toUpperCase(), 10, true, 4)
    doc.setDrawColor(0)
    doc.line(margin, y, pageW - margin, y)
    y += 8
  }

  // Header
  addLine(report.title, 18, true, 8)
  addLine(
    `Generated: ${new Date(report.createdAt).toLocaleString()}${report.generatedBy ? ` by ${report.generatedBy}` : ''}`,
    9,
    false,
    4,
  )
  if (report.config.frameworks?.length) {
    addLine(`Frameworks: ${report.config.frameworks.join(', ')}`, 9, false, 10)
  }
  y += 6

  const d = report.data
  const system = d.system ?? {}

  // Executive summary
  addSection('Executive Summary')
  addLine(`System: ${system.name ?? '—'}`, 11)
  addLine(`Owner: ${system.owner ?? '—'}  |  Risk Tier: ${system.riskTier ?? '—'}  |  Stage: ${system.lifecycleStage ?? '—'}`, 10)
  addLine(`Governance Readiness: ${system.readiness ?? 0}%`, 10, false, 12)

  // Risks
  const risks = d.risks ?? []
  if (risks.length > 0) {
    addSection('Risk Overview')
    for (const risk of risks.slice(0, 10)) {
      addLine(`• [${(risk.severity ?? '').toUpperCase()}] ${risk.title} — ${risk.status}`, 10)
      if (risk.description) addLine(`  ${risk.description}`, 9)
    }
    if (risks.length > 10) addLine(`  +${risks.length - 10} more risks…`, 9)
  }

  // Evidence
  const evidence = d.evidence ?? []
  if (evidence.length > 0) {
    addSection('Evidence Summary')
    for (const item of evidence.slice(0, 8)) {
      addLine(`• ${item.title || item.type} — ${item.status} (${item.confidence ?? 0}% confidence)`, 10)
    }
    if (evidence.length > 8) addLine(`  +${evidence.length - 8} more items…`, 9)
  }

  // Remediations
  const remediation = d.remediation ?? []
  const open = remediation.filter((t: any) => t.status !== 'done')
  if (open.length > 0) {
    addSection(`Open Remediations (${open.length})`)
    for (const task of open.slice(0, 8)) {
      addLine(`• [${(task.priority ?? '').toUpperCase()}] ${task.title} — ${task.status}`, 10)
    }
  }

  // Approvals
  const approvals = d.approvals ?? []
  if (approvals.length > 0) {
    addSection('Decision Log')
    for (const a of approvals.slice(0, 5)) {
      addLine(`• ${a.status?.toUpperCase()} — ${new Date(a.createdAt).toLocaleDateString()}`, 10)
      if (a.decisionNotes) addLine(`  ${a.decisionNotes}`, 9)
    }
  }

  doc.save(`${report.title.replace(/\s+/g, '_')}.pdf`)
}

// ---------------------------------------------------------------------------
// JSON download helper
// ---------------------------------------------------------------------------

function downloadJson(report: SavedReport) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${report.title.replace(/\s+/g, '_')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function AuditReportsPage() {
  const { selectedSystem } = useSystemContext()
  const { systems } = useModelInventory()

  const [reportType, setReportType] = useState('governance')
  const [selectedSystemId, setSelectedSystemId] = useState<string>('')
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([])
  const [selectedSections, setSelectedSections] = useState<string[]>([])
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [generating, setGenerating] = useState(false)
  const [activeReport, setActiveReport] = useState<SavedReport | null>(null)
  const [previewReport, setPreviewReport] = useState<SavedReport | null>(null)

  const [history, setHistory] = useState<SavedReport[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)

  // Use selectedSystem from context as default when available
  useEffect(() => {
    if (selectedSystem?.id && !selectedSystemId) {
      setSelectedSystemId(selectedSystem.id)
    }
  }, [selectedSystem?.id])

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const response = await apiClient.get<SavedReport[]>(
        selectedSystemId
          ? `${API_ENDPOINTS.aiGovernance.listReports}?system_id=${encodeURIComponent(selectedSystemId)}`
          : API_ENDPOINTS.aiGovernance.listReports,
      )
      if (response.success && response.data) setHistory(response.data)
    } catch {
      // non-blocking
    } finally {
      setHistoryLoading(false)
    }
  }, [selectedSystemId])

  useEffect(() => {
    void loadHistory()
  }, [loadHistory])

  const handleGenerate = async () => {
    if (!selectedSystemId) return
    setGenerating(true)
    try {
      const response = await apiClient.post<SavedReport>(
        API_ENDPOINTS.aiGovernance.generateReport,
        {
          system_id: selectedSystemId,
          report_type: reportType,
          frameworks: selectedFrameworks,
          sections: selectedSections,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        },
      )
      if (response.success && response.data) {
        setActiveReport(response.data)
        setHistory((prev) => [response.data!, ...prev])
      }
    } finally {
      setGenerating(false)
    }
  }

  const currentSystem = systems.find((s) => s.id === selectedSystemId)

  const toggleFramework = (fw: string) => {
    setSelectedFrameworks((prev) =>
      prev.includes(fw) ? prev.filter((f) => f !== fw) : [...prev, fw],
    )
  }

  const toggleSection = (sec: string) => {
    setSelectedSections((prev) =>
      prev.includes(sec) ? prev.filter((s) => s !== sec) : [...prev, sec],
    )
  }

  const reportForPreview = previewReport ?? activeReport

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="overflow-hidden border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="border-b-4 border-black bg-black p-5 text-white">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="border-2 border-white bg-white px-2 py-0.5 text-[11px] font-black uppercase text-black">
              <IconFileAnalytics className="mr-1.5 h-3.5 w-3.5" />
              Audit Reports
            </Badge>
          </div>
          <h1 className="mt-3 text-3xl font-black uppercase">Governance Report Generator</h1>
          <p className="mt-1 text-sm text-slate-300">
            Generate structured audit reports for regulators, compliance teams, and governance boards.
          </p>
        </div>

        {/* Report type selector */}
        <div className="grid gap-0 sm:grid-cols-3">
          {REPORT_TYPES.map((type) => (
            <button
              key={type.id}
              type="button"
              onClick={() => setReportType(type.id)}
              className={`relative border-b-2 border-r-2 border-black p-5 text-left transition-colors last:border-r-0 hover:bg-slate-50 ${
                reportType === type.id ? 'bg-slate-100' : 'bg-white'
              }`}
            >
              {reportType === type.id && (
                <span className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-black text-white">
                  <IconCheck className="h-3 w-3" />
                </span>
              )}
              <Badge className={`border-2 px-2 py-0.5 text-[10px] font-black uppercase ${type.color}`}>
                {type.label}
              </Badge>
              <p className="mt-2 text-xs text-muted-foreground">{type.description}</p>
            </button>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
        {/* Configuration panel */}
        <div className="space-y-4">
          <Card className="border-2 border-black p-5 shadow-brutal">
            <h2 className="flex items-center gap-2 text-sm font-black uppercase">
              <IconSettings className="h-4 w-4" />
              Report Configuration
            </h2>

            <div className="mt-4 space-y-4">
              {/* AI System */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-muted-foreground">
                  AI System
                </label>
                <Select value={selectedSystemId} onValueChange={setSelectedSystemId}>
                  <SelectTrigger className="border-2 border-black font-semibold">
                    <SelectValue placeholder="Select system…" />
                  </SelectTrigger>
                  <SelectContent>
                    {systems.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.name}
                      </SelectItem>
                    ))}
                    {systems.length === 0 && (
                      <SelectItem value={selectedSystem.id}>
                        {selectedSystem.name || 'Current system'}
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* Frameworks */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-muted-foreground">
                  Frameworks to include
                </label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="neutral" className="w-full justify-between border-2 border-black font-semibold">
                      {selectedFrameworks.length > 0
                        ? `${selectedFrameworks.length} framework${selectedFrameworks.length > 1 ? 's' : ''} selected`
                        : 'All frameworks'}
                      <IconChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56 border-2 border-black">
                    <DropdownMenuLabel className="text-[10px] font-black uppercase">
                      Select frameworks
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {ALL_FRAMEWORKS.map((fw) => (
                      <DropdownMenuCheckboxItem
                        key={fw}
                        checked={selectedFrameworks.includes(fw)}
                        onCheckedChange={() => toggleFramework(fw)}
                      >
                        {fw}
                      </DropdownMenuCheckboxItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Date range */}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-black uppercase text-muted-foreground">
                    Date from
                  </label>
                  <Input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="border-2 border-black"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[11px] font-black uppercase text-muted-foreground">
                    Date to
                  </label>
                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="border-2 border-black"
                  />
                </div>
              </div>

              {/* Sections */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-muted-foreground">
                  Sections to include
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_SECTIONS.map((sec) => (
                    <button
                      key={sec.id}
                      type="button"
                      onClick={() => toggleSection(sec.id)}
                      className={`rounded border-2 border-black px-2 py-0.5 text-[11px] font-bold transition-colors ${
                        selectedSections.includes(sec.id)
                          ? 'bg-black text-white'
                          : 'bg-white hover:bg-slate-100'
                      }`}
                    >
                      {sec.label}
                    </button>
                  ))}
                </div>
                {selectedSections.length === 0 && (
                  <p className="text-[10px] text-muted-foreground">All sections included</p>
                )}
              </div>

              {/* Generate button */}
              <Button
                className="w-full border-2 border-black font-black uppercase shadow-[3px_3px_0px_0px_#000]"
                disabled={!selectedSystemId || generating}
                onClick={handleGenerate}
              >
                {generating ? (
                  <>
                    <IconLoader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating…
                  </>
                ) : (
                  <>
                    <IconFileAnalytics className="mr-2 h-4 w-4" />
                    Generate Report
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Quick export of active report */}
          {activeReport && (
            <Card className="border-2 border-black p-4 shadow-brutal">
              <h3 className="text-xs font-black uppercase text-muted-foreground">
                Export last generated
              </h3>
              <p className="mt-1 truncate text-sm font-bold">{activeReport.title}</p>
              <div className="mt-3 flex gap-2">
                <Button
                  variant="neutral"
                  className="flex-1 border-2 border-black text-xs font-bold"
                  onClick={() => downloadJson(activeReport)}
                >
                  <IconDownload className="mr-1 h-3.5 w-3.5" />
                  JSON
                </Button>
                <Button
                  className="flex-1 border-2 border-black text-xs font-bold shadow-[2px_2px_0px_0px_#000]"
                  onClick={() => generatePdf(activeReport)}
                >
                  <IconDownload className="mr-1 h-3.5 w-3.5" />
                  PDF
                </Button>
              </div>
            </Card>
          )}
        </div>

        {/* Preview panel */}
        <Card className="border-2 border-black p-5 shadow-brutal">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-black uppercase">Report Preview</h2>
            {previewReport && (
              <Button
                variant="neutral"
                className="h-7 border-2 border-black px-2 text-xs font-bold"
                onClick={() => setPreviewReport(null)}
              >
                Clear
              </Button>
            )}
          </div>

          {!reportForPreview ? (
            <div className="rounded-xl border-2 border-dashed border-black/30 bg-slate-50 p-10 text-center">
              <IconFileAnalytics className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-3 font-bold text-muted-foreground">No report generated yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Configure the report on the left and click Generate.
              </p>
            </div>
          ) : (
            <ReportPreview
              reportType={reportForPreview.reportType}
              system={reportForPreview.data?.system ?? currentSystem ?? undefined}
              data={reportForPreview.data ?? {}}
              sections={reportForPreview.config?.sections ?? []}
              frameworks={reportForPreview.config?.frameworks ?? []}
            />
          )}
        </Card>
      </div>

      {/* Report history */}
      <Card className="border-2 border-black p-5 shadow-brutal">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-black uppercase">Report History</h2>
          <Button
            variant="neutral"
            className="h-7 border-2 border-black px-2 text-xs font-bold"
            onClick={loadHistory}
          >
            <IconRefresh className="mr-1 h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
        <ReportHistoryTable
          reports={history}
          loading={historyLoading}
          onDownloadJson={downloadJson}
          onDownloadPdf={generatePdf}
          onPreview={(r) => setPreviewReport(r)}
        />
      </Card>
    </div>
  )
}

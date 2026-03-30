'use client'

import {
  IconDownload,
  IconFileAnalytics,
  IconFileCheck,
  IconLoader2,
} from '@tabler/icons-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export interface SavedReport {
  id: string
  systemId: string
  reportType: string
  title: string
  generatedBy: string
  config: {
    frameworks?: string[]
    dateFrom?: string
    dateTo?: string
    sections?: string[]
  }
  data: Record<string, any>
  createdAt: string
}

interface ReportHistoryTableProps {
  reports: SavedReport[]
  loading: boolean
  onDownloadJson: (report: SavedReport) => void
  onDownloadPdf: (report: SavedReport) => void
  onPreview: (report: SavedReport) => void
}

function formatDate(ts: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

const TYPE_LABELS: Record<string, string> = {
  compliance: 'Compliance',
  bias: 'Bias Assessment',
  governance: 'Governance Summary',
}

const TYPE_COLORS: Record<string, string> = {
  compliance: 'border-blue-500 bg-blue-50 text-blue-800',
  bias: 'border-purple-500 bg-purple-50 text-purple-800',
  governance: 'border-emerald-500 bg-emerald-50 text-emerald-800',
}

export function ReportHistoryTable({
  reports,
  loading,
  onDownloadJson,
  onDownloadPdf,
  onPreview,
}: ReportHistoryTableProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <IconLoader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (reports.length === 0) {
    return (
      <div className="rounded-xl border-2 border-dashed border-black/30 bg-slate-50 p-8 text-center">
        <IconFileAnalytics className="mx-auto h-8 w-8 text-muted-foreground" />
        <p className="mt-2 font-bold text-muted-foreground">No reports generated yet</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Configure and generate your first audit report above.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {reports.map((report) => (
        <div
          key={report.id}
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border-2 border-black bg-white p-4 shadow-[2px_2px_0px_0px_#000]"
        >
          <div className="flex min-w-0 flex-1 items-start gap-3">
            <IconFileCheck className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            <div className="min-w-0">
              <p className="truncate font-bold">{report.title}</p>
              <p className="text-xs text-muted-foreground">
                Generated {formatDate(report.createdAt)}
                {report.generatedBy ? ` by ${report.generatedBy}` : ''}
              </p>
              {report.config.frameworks && report.config.frameworks.length > 0 && (
                <p className="mt-0.5 text-[10px] text-muted-foreground">
                  Frameworks: {report.config.frameworks.join(', ')}
                </p>
              )}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge
              className={`border-2 px-2 py-0.5 text-[10px] font-black uppercase ${TYPE_COLORS[report.reportType] || 'border-black bg-slate-50'}`}
            >
              {TYPE_LABELS[report.reportType] ?? report.reportType}
            </Badge>
            <Button
              variant="neutral"
              className="h-7 border-2 border-black px-2 text-xs font-bold"
              onClick={() => onPreview(report)}
            >
              Preview
            </Button>
            <Button
              variant="neutral"
              className="h-7 border-2 border-black px-2 text-xs font-bold"
              onClick={() => onDownloadJson(report)}
              title="Download JSON"
            >
              <IconDownload className="mr-1 h-3.5 w-3.5" />
              JSON
            </Button>
            <Button
              variant="default"
              className="h-7 border-2 border-black px-2 text-xs font-bold"
              onClick={() => onDownloadPdf(report)}
              title="Download PDF"
            >
              <IconDownload className="mr-1 h-3.5 w-3.5" />
              PDF
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}

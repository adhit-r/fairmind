'use client'

import { BTN, MUTED, Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

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
  if (!ts) return 'date not recorded'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

const TYPE_LABELS: Record<string, string> = {
  compliance: 'Compliance',
  bias: 'Bias Assessment',
  governance: 'Governance Summary',
}

const SMALL = cn(BTN, 'h-8 px-3 text-[12px]')

export function ReportHistoryTable({
  reports,
  loading,
  onDownloadJson,
  onDownloadPdf,
  onPreview,
}: ReportHistoryTableProps) {
  if (loading) {
    return <p role="status" className={`mt-2 border-t border-[var(--fm-line)] pt-3 text-[13px] ${MUTED}`}>Loading saved reports</p>
  }

  if (reports.length === 0) {
    return (
      <p className={`mt-2 border-t border-[var(--fm-line)] pt-3 text-[13px] ${MUTED}`}>
        No reports are saved for this system and framework yet.
      </p>
    )
  }

  return (
    <ul className="mt-2">
      {reports.map((report) => (
        <li
          key={report.id}
          className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--fm-line)] py-3"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13.5px] font-semibold">{report.title}</p>
            <p className={`mt-0.5 text-[12px] ${MUTED}`}>
              Generated {formatDate(report.createdAt)}
              {report.generatedBy ? ` by ${report.generatedBy}` : ''}
              {report.config.frameworks && report.config.frameworks.length > 0
                ? ` · ${report.config.frameworks.join(', ')}`
                : ''}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Pill>{TYPE_LABELS[report.reportType] ?? report.reportType}</Pill>
            <button type="button" className={SMALL} onClick={() => onPreview(report)}>
              Preview
            </button>
            <button type="button" className={SMALL} onClick={() => onDownloadJson(report)} title="Download JSON">
              JSON
            </button>
            <button type="button" className={SMALL} onClick={() => onDownloadPdf(report)} title="Download PDF">
              PDF
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}

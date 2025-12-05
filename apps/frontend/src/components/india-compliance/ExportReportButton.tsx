'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Download, FileText, Loader2 } from 'lucide-react'

interface ReportData {
  framework: string
  overall_score: number
  status: string
  requirements_met: number
  total_requirements: number
  evidence_count: number
  gaps: any[]
  timestamp: string
  executive_summary?: string
  detailed_findings?: string
  legal_citations?: string[]
}

interface ExportReportButtonProps {
  reportData: ReportData
  systemId: string
  onExportStart?: () => void
  onExportComplete?: (format: string) => void
}

// Simple PDF generation utility
const generatePDFContent = (data: ReportData): string => {
  const date = new Date(data.timestamp).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const frameworkLabel = data.framework.replace(/_/g, ' ').toUpperCase()

  return `
INDIA AI COMPLIANCE REPORT
${frameworkLabel}

Generated: ${date}
Overall Compliance Score: ${data.overall_score}%
Status: ${data.status.replace(/_/g, ' ').toUpperCase()}

EXECUTIVE SUMMARY
================
This compliance report evaluates the system against ${frameworkLabel} requirements.

Compliance Score: ${data.overall_score}%
Requirements Met: ${data.requirements_met} / ${data.total_requirements}
Evidence Collected: ${data.evidence_count}

COMPLIANCE STATUS
=================
Current Status: ${data.status.replace(/_/g, ' ').toUpperCase()}
Compliance Rate: ${Math.round((data.requirements_met / data.total_requirements) * 100)}%

DETAILED FINDINGS
=================
${data.detailed_findings || 'Detailed findings will be populated from compliance checks.'}

IDENTIFIED GAPS
===============
Total Gaps: ${data.gaps.length}

${data.gaps
  .map(
    gap => `
Control: ${gap.control_name}
Severity: ${gap.severity.toUpperCase()}
Category: ${gap.category}
Legal Citation: ${gap.legal_citation}
Failed Checks:
${gap.failed_checks.map(check => `  - ${check}`).join('\n')}
`
  )
  .join('\n')}

LEGAL CITATIONS
===============
${data.legal_citations?.join('\n') || 'Legal citations from regulatory frameworks'}

RECOMMENDATIONS
===============
1. Address critical and high-severity gaps immediately
2. Implement remediation steps in priority order
3. Establish continuous monitoring for compliance
4. Schedule regular compliance reviews
5. Maintain audit trail of all compliance activities

AUDIT TRAIL
===========
Report Generated: ${date}
System ID: ${data.framework}
Framework: ${frameworkLabel}

---
This report is confidential and intended for internal compliance use only.
`
}

// Simple CSV generation utility
const generateCSVContent = (data: ReportData): string => {
  const headers = [
    'Framework',
    'Overall Score',
    'Status',
    'Requirements Met',
    'Total Requirements',
    'Evidence Count',
    'Generated Date',
  ]

  const rows = [
    [
      data.framework,
      data.overall_score,
      data.status,
      data.requirements_met,
      data.total_requirements,
      data.evidence_count,
      new Date(data.timestamp).toISOString(),
    ],
  ]

  // Add gaps data
  if (data.gaps.length > 0) {
    rows.push([])
    rows.push(['COMPLIANCE GAPS'])
    rows.push(['Control Name', 'Severity', 'Category', 'Legal Citation', 'Failed Checks'])

    data.gaps.forEach(gap => {
      rows.push([
        gap.control_name,
        gap.severity,
        gap.category,
        gap.legal_citation,
        gap.failed_checks.join('; '),
      ])
    })
  }

  return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
}

// Simple JSON generation utility
const generateJSONContent = (data: ReportData): string => {
  return JSON.stringify(
    {
      report_metadata: {
        generated_at: new Date(data.timestamp).toISOString(),
        framework: data.framework,
        system_id: data.framework,
      },
      compliance_summary: {
        overall_score: data.overall_score,
        status: data.status,
        requirements_met: data.requirements_met,
        total_requirements: data.total_requirements,
        evidence_count: data.evidence_count,
        compliance_rate: Math.round((data.requirements_met / data.total_requirements) * 100),
      },
      gaps: data.gaps,
      legal_citations: data.legal_citations || [],
    },
    null,
    2
  )
}

const downloadFile = (content: string, filename: string, mimeType: string) => {
  const blob = new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const ExportReportButton: React.FC<ExportReportButtonProps> = ({
  reportData,
  systemId,
  onExportStart,
  onExportComplete,
}) => {
  const [isExporting, setIsExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<string | null>(null)

  const handleExport = async (format: 'pdf' | 'csv' | 'json') => {
    try {
      setIsExporting(true)
      setExportFormat(format)
      onExportStart?.()

      const timestamp = new Date().toISOString().split('T')[0]
      const baseFilename = `india-compliance-report-${systemId}-${timestamp}`

      let content: string
      let filename: string
      let mimeType: string

      switch (format) {
        case 'pdf':
          content = generatePDFContent(reportData)
          filename = `${baseFilename}.txt`
          mimeType = 'text/plain'
          break
        case 'csv':
          content = generateCSVContent(reportData)
          filename = `${baseFilename}.csv`
          mimeType = 'text/csv'
          break
        case 'json':
          content = generateJSONContent(reportData)
          filename = `${baseFilename}.json`
          mimeType = 'application/json'
          break
        default:
          throw new Error('Unsupported format')
      }

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 500))

      downloadFile(content, filename, mimeType)
      onExportComplete?.(format)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
      setExportFormat(null)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button disabled={isExporting} className="gap-2">
          {isExporting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Export Report
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5">
          <p className="text-sm font-semibold">Export Format</p>
          <p className="text-xs text-gray-500">Choose your preferred format</p>
        </div>
        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => handleExport('pdf')}
          disabled={isExporting}
          className="gap-2 cursor-pointer"
        >
          <FileText className="h-4 w-4" />
          <div>
            <p className="text-sm font-medium">PDF Report</p>
            <p className="text-xs text-gray-500">With legal citations</p>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          className="gap-2 cursor-pointer"
        >
          <FileText className="h-4 w-4" />
          <div>
            <p className="text-sm font-medium">CSV Export</p>
            <p className="text-xs text-gray-500">For spreadsheet analysis</p>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => handleExport('json')}
          disabled={isExporting}
          className="gap-2 cursor-pointer"
        >
          <FileText className="h-4 w-4" />
          <div>
            <p className="text-sm font-medium">JSON Data</p>
            <p className="text-xs text-gray-500">For system integration</p>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default ExportReportButton

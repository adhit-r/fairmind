import { useMemo } from 'react'
import { useOrg } from '@/context/OrgContext'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { withOrg } from '@/lib/api/hooks/usePacks'
import type { Briefing, Role, SealedReport } from './types'

export type Scope = { role: Role; system_id?: string; framework?: string }
export type Format = 'PDF' | 'DOCX' | 'CSV'

const reason = (status: number | undefined, text: string | undefined, fallback: string) =>
  status === 403 ? 'Only editors and admins can seal a report' : text || fallback

/** Calls that need the selected organisation. Each returns the data or a plain error message. */
export function useReportCalls() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  return useMemo(() => {
    const scoped = (path: string) => (orgId ? withOrg(path, orgId) : null)
    return {
      briefing: async (body: Scope): Promise<Briefing | null> => {
        const path = scoped(API_ENDPOINTS.aiGovernance.reportBriefing)
        if (!path) return null
        try {
          const res = await apiClient.post<Briefing>(path, body)
          return res.success && res.data ? res.data : null
        } catch {
          return null
        }
      },
      seal: async (body: Scope & { narrative: string }): Promise<{ data: SealedReport | null; error: string | null }> => {
        const path = scoped(API_ENDPOINTS.aiGovernance.roleReports)
        if (!path) return { data: null, error: 'Select an organisation first.' }
        try {
          const res = await apiClient.post<SealedReport>(path, body)
          if (res.success && res.data) return { data: res.data, error: null }
          return { data: null, error: reason(res.apiError?.status, res.error || res.message, 'The report was not sealed') }
        } catch (e) {
          return { data: null, error: e instanceof Error ? e.message : 'The report was not sealed' }
        }
      },
    }
  }, [orgId])
}

/** Saves a sealed report in one format. Returns an error message, or null when the file was saved. */
export async function downloadSealed(report: Pick<SealedReport, 'id' | 'title'>, format: Format): Promise<string | null> {
  const ext = format.toLowerCase() as 'pdf' | 'docx' | 'csv'
  const response = await apiClient.get<Blob>(API_ENDPOINTS.aiGovernance.exportReport(report.id, ext), { responseType: 'blob' })
  if (!response.success || !response.data) return response.error || `Could not download the ${format}`
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${report.title.replace(/\s+/g, '_')}.${ext}`
  anchor.click()
  URL.revokeObjectURL(url)
  return null
}

/** The briefing as plain text, for the summary on page one. */
export const briefingText = (b: Briefing) => b.parts.map((p) => ('text' in p ? p.text : p.value)).join('')

/** What each role can download. Each one prepares a sealed snapshot of the current role and scope. */
export const LIBRARY: Record<Role, { key: string; name: string; description: string; formats: Format[] }[]> = {
  executive: [{ key: 'executive', name: 'Executive summary', description: 'The briefing, road to the audit, proof and oversight in a few pages.', formats: ['PDF', 'DOCX'] }],
  compliance: [{ key: 'compliance', name: 'Framework readiness', description: 'Proof for each requirement, open work and where systems fall short.', formats: ['PDF', 'DOCX', 'CSV'] }],
  engineering: [{ key: 'engineering', name: 'Technical report', description: 'Release gate checks, agent tools, fairness drift and fixes to make.', formats: ['PDF', 'DOCX', 'CSV'] }],
  auditor: [{ key: 'auditor', name: 'Auditor report', description: 'Ledger check, statement of applicability, audit sample and inspection packs.', formats: ['PDF', 'DOCX', 'CSV'] }],
  risk: [{ key: 'risk', name: 'Risk register', description: 'Every risk with its rating, owner and status, and what waits for acceptance.', formats: ['PDF', 'DOCX', 'CSV'] }],
}

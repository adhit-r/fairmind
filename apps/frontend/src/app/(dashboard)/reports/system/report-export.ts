import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { withOrg } from '@/lib/api/hooks/usePacks'

export type ReportFormat = 'pdf' | 'docx' | 'json'

export async function downloadApprovedReport(orgId: string, reportId: string, format: ReportFormat, isActive: () => boolean) {
  const response = await apiClient.get<Blob>(withOrg(API_ENDPOINTS.aiGovernance.exportReport(reportId, format), orgId), { responseType: 'blob' })
  if (!isActive()) return
  if (!response.success || !response.data) throw new Error(response.error || `Could not download the ${format.toUpperCase()}.`)
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `system-assurance-${reportId}.${format}`
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

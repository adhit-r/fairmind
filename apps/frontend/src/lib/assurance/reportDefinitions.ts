export type ReportDefinition = {
  id: string
  title: string
  systemId: string
  assignmentId: string
  createdBy: string
  createdAt: string
  periodPreset: 'previous_complete_utc_month'
}

export function isReportDefinition(record: ReportDefinition | null | undefined): record is ReportDefinition {
  return Boolean(record && typeof record.id === 'string' && record.id
    && typeof record.title === 'string' && record.title.trim()
    && typeof record.systemId === 'string' && record.systemId
    && typeof record.assignmentId === 'string' && record.assignmentId
    && record.periodPreset === 'previous_complete_utc_month')
}

export function reportHref(systemId: string, versionId?: string, definitionId?: string) {
  const query = new URLSearchParams()
  if (systemId) query.set('system', systemId)
  if (definitionId) query.set('definition', definitionId)
  if (versionId) query.set('report', versionId)
  return query.size ? `/reports/system?${query}` : '/reports/system'
}

export function scheduledReportHref(systemId: string, definitionId: string, runId: string) {
  return `/reports/system?${new URLSearchParams({ system: systemId, definition: definitionId, run: runId })}`
}

export function reportSchedulesHref(definitionId?: string) {
  return definitionId ? `/reports/schedules?${new URLSearchParams({ definition: definitionId })}` : '/reports/schedules'
}

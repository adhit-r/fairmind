export type Scope = { systemId: string; assignmentId: string; dateFrom: string; dateTo: string; definitionId?: string }

type ReportControl = {
  id: string
  externalId: string
  title: string
  applicability: string
  status: string
  owner?: string | null
  justification?: string | null
  evidenceStatus: string
  acceptedEvidenceCount: number
}

type ReportEvidence = {
  id: string
  runId: string
  evidenceId?: string | null
  contentHash?: string | null
  result: string
  sourceType: string
  sourceIdentifier: string
  capturedAt: string
  suiteName?: string | null
  suiteVersion?: string | null
  subjectVersion?: string | null
  runnerVersion?: string | null
  assuranceSource?: string | null
  stale?: boolean
  scopeExclusions?: string[]
  measurements?: { name: string; value: number | string; unit?: string | null; slice?: string | null; thresholdMet?: boolean | null }[]
  thresholds?: { metric: string; operator: string; value: number | string; unit?: string | null }[]
  limitations: string[]
}

export type ReportVersion = {
  id: string
  systemId: string
  reportType: 'system-assurance'
  title: string
  revision: string
  status: 'preview' | 'approved'
  approvedAt?: string | null
  approvedBy?: string | null
  sha256?: string | null
  narrative?: string | null
  createdAt: string
  config: { templateVersion: number; assignmentId: string; frameworkVersionId: string; frameworks: string[]; dateFrom: string; dateTo: string; timeZone: 'UTC'; definitionId?: string }
  data: {
    system: { id: string; name: string; version?: string | null; owner?: string | null; riskTier?: string | null; lifecycleStage?: string | null }
    framework: { assignmentId: string; versionId: string; key: string; name: string; versionLabel: string }
    period: { dateFrom: string; dateTo: string; timeZone: 'UTC' }
    controls: ReportControl[]
    evidence: ReportEvidence[]
    findings?: { id: string; title: string; severity: string; status: string; createdAt: string }[]
    coverage: { evidenceRuns: number; controls: number; excludedUnmappedRuns: number; excludedUndatedRuns: number }
    limitations: string[]
    generatedAt: string
  }
}

export function matchesReport(report: ReportVersion | null | undefined, systemId: string, status: ReportVersion['status'], scope?: Scope) {
  if (!report || report.reportType !== 'system-assurance' || report.status !== status ||
    report.systemId !== systemId || report.data?.system?.id !== systemId ||
    !report.id || !report.revision || !report.config) return false
  const { config, data } = report
  return data.period?.dateFrom === config.dateFrom && data.period?.dateTo === config.dateTo &&
    data.period?.timeZone === 'UTC' && data.framework?.assignmentId === config.assignmentId &&
    data.framework?.versionId === config.frameworkVersionId &&
    Array.isArray(data.controls) && Array.isArray(data.evidence) && Array.isArray(data.limitations) &&
    data.coverage?.controls === data.controls.length && data.coverage?.evidenceRuns === data.evidence.length &&
    (!scope || (config.assignmentId === scope.assignmentId && config.dateFrom === scope.dateFrom && config.dateTo === scope.dateTo &&
      (config.definitionId ?? undefined) === scope.definitionId))
}

export function calendarDate(value: string) {
  const date = new Date(`${value}T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
}

export function recordedAt(value?: string | null) {
  const date = value && new Date(value)
  return date && !Number.isNaN(date.getTime()) ? date.toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC' : 'Date unavailable'
}

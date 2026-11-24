'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { ArrowLeft, ArrowRight, ArrowUpRight, Bookmark, CalendarDays, FileCheck2 } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { resolveFrameworkAssignments, useAllFrameworkVersions, useFrameworkAssignments, useGovernanceCatalog } from '@/lib/api/hooks/useGovernanceAssurance'
import { useOrgResource, withOrg } from '@/lib/api/hooks/usePacks'
import { recordParam } from '@/lib/assurance/evaluationLinks'
import { isReportDefinition, reportHref, reportSchedulesHref, type ReportDefinition } from '@/lib/assurance/reportDefinitions'
import { ReportOutline, ReportReview } from './ReportReview'
import { ScheduledAssuranceReview } from './ScheduledAssuranceReview'
import { downloadApprovedReport, type ReportFormat } from './report-export'
import { calendarDate, matchesReport, recordedAt, type ReportVersion, type Scope } from './report-version'

const reports = API_ENDPOINTS.aiGovernance

type DraftInput = { period: { from: string; to: string }; narrative: string }

function previousFullMonth() {
  const now = new Date()
  const first = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1))
  const last = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 0))
  return { from: first.toISOString().slice(0, 10), to: last.toISOString().slice(0, 10) }
}

function distinguishOptions(options: { value: string; label: string }[]) {
  const names = new Map<string, number>()
  for (const { label } of options) names.set(label, (names.get(label) ?? 0) + 1)
  return options.map(({ label, value }) => ({
    value,
    label: (names.get(label) ?? 0) > 1 ? `${label} · ${value.slice(-8)}` : label,
  }))
}

export function SystemAssuranceReport() {
  const search = useSearchParams()
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const { systems, loading, error, refreshSystems } = useSystemContext()
  const [continued, setContinued] = useState<{ orgId: string; definition: ReportDefinition; input: DraftInput } | null>(null)
  const choices = systems.filter((system) => system.metadata?.source !== 'fallback')
  const requested = recordParam(search, 'system')
  const version = recordParam(search, 'report')
  const definitionId = recordParam(search, 'definition')
  const runId = recordParam(search, 'run')
  const scheduled = runId !== undefined
  const definitionResource = useOrgResource<ReportDefinition>(definitionId ? reports.systemAssuranceDefinition(definitionId) : null)
  const continuedInput = continued && continued.orgId === selectedOrg?.id && continued.definition.id === definitionId ? continued : null
  const definitionCandidate = definitionResource.data ?? continuedInput?.definition
  const definition = isReportDefinition(definitionCandidate) && definitionCandidate.id === definitionId
    && (requested === undefined || definitionCandidate.systemId === requested) ? definitionCandidate : undefined
  const systemId = definition?.systemId ?? requested
  const shown = choices.find((system) => system.id === systemId) ?? (definitionId === undefined && systemId === undefined && choices.length === 1 ? choices[0] : undefined)
  const definitionLoading = definitionId !== undefined && ((!definition && definitionResource.loading) || loading || orgLoading)
  const invalidDefinition = definitionId !== undefined && !definitionLoading && (!definition || !shown || error || definitionResource.error)
  const systemReadError = !loading && !orgLoading && (error || (requested !== undefined && !shown))
  const canWrite = Boolean(selectedOrg && (['owner', 'admin', 'editor'].includes(selectedOrg.role) ||
    selectedOrg.permissions?.includes('model:write')) && shown?.stage !== 'retired')
  const named = definition && shown && !invalidDefinition ? definition : undefined
  const invalidRun = scheduled && (!runId || !requested || !definitionId || version !== undefined)
  const summary = scheduled ? 'Inspect the evidence prepared for this scheduled run.'
    : !named ? 'Set the evidence window, inspect the source records and approve a version for export.'
    : canWrite ? 'Prepare a new report or open an approved version.' : 'Open an approved version and inspect its evidence.'
  return (
    <div className="sar-page">
      <header className="sar-page-header">
        <Link href={scheduled ? reportSchedulesHref(named?.id) : '/reports'} className="sar-text-link">
          <ArrowLeft size={15} aria-hidden /> {scheduled ? 'Back to schedule' : 'Reports'}
        </Link>
        {named && <div className="sar-definition-mark">
          {scheduled ? <CalendarDays size={15} aria-hidden /> : <Bookmark size={15} aria-hidden />}
          {scheduled ? 'Scheduled report' : 'Saved report'}
        </div>}
        <h1>{named?.title ?? 'System Assurance Report'}</h1>
        <p>{summary}</p>
        {named && !scheduled && <Link href={reportSchedulesHref(named.id)} className="sar-text-link sar-schedule-link">
          <CalendarDays size={15} aria-hidden /> Report schedule <ArrowRight size={14} aria-hidden />
        </Link>}
      </header>
      {invalidRun ? <section className="sar-paper sar-outline">
        <h2>Scheduled run unavailable</h2><p role="alert">Open one scheduled run from its history.</p>
      </section>
        : definitionLoading ? <section className="sar-paper sar-outline"><p role="status">Loading saved report…</p></section>
        : invalidDefinition ? <section className="sar-paper sar-outline">
          <h2>Saved report unavailable</h2>
          <p role="alert">{definitionResource.error || error || 'Choose a saved report for this system from the Reports library.'}</p>
          {(error || (definitionResource.error && definitionResource.errorStatus !== 404)) && <Button type="button" variant="outline"
            onClick={() => { if (error) void refreshSystems(); definitionResource.reload() }}>Retry saved report</Button>}
          <Link className="sar-text-link" href="/reports">Open Reports library <ArrowRight size={15} aria-hidden /></Link>
        </section>
        : runId && named && selectedOrg ? <ScheduledAssuranceReview
          key={JSON.stringify([selectedOrg.id, named.id, runId])}
          orgId={selectedOrg.id}
          definition={named}
          runId={runId}
          canWrite={canWrite}
        />
        : <AssuranceWorkspace
          key={JSON.stringify([selectedOrg?.id, shown?.id ?? requested, definition?.id])}
          orgId={selectedOrg?.id}
          system={shown}
          choices={choices}
          systemsLoading={loading || orgLoading}
          systemReadError={systemReadError ? (error || 'The system in this address is unavailable.') : null}
          canWrite={canWrite}
          definition={definition}
          initialInput={continuedInput?.input}
          versionId={version}
          onSystemChange={(id) => window.history.pushState(null, '', reportHref(id))}
          onOpenVersion={(id) => window.history.pushState(null, '', reportHref(shown?.id ?? '', id, definition?.id))}
          onDefinitionSaved={(record, input) => {
            if (!selectedOrg) return
            setContinued({ orgId: selectedOrg.id, definition: record, input })
            window.history.pushState(null, '', reportHref(record.systemId, undefined, record.id))
          }}
          onRetrySystems={() => void refreshSystems()}
        />}
    </div>
  )
}

function AssuranceWorkspace({ orgId, system, choices, systemsLoading, systemReadError, canWrite, definition, initialInput, versionId, onSystemChange, onOpenVersion, onDefinitionSaved, onRetrySystems }: {
  orgId?: string
  system?: AISystemSummary
  choices: AISystemSummary[]
  systemsLoading: boolean
  systemReadError: string | null
  canWrite: boolean
  definition?: ReportDefinition
  initialInput?: DraftInput
  versionId?: string | null
  onSystemChange: (id: string) => void
  onOpenVersion: (id?: string) => void
  onDefinitionSaved: (record: ReportDefinition, input: DraftInput) => void
  onRetrySystems: () => void
}) {
  const systemId = system?.id ?? ''
  const catalog = useGovernanceCatalog(systemId ? orgId : undefined)
  const versions = useAllFrameworkVersions(systemId ? orgId : undefined, catalog.frameworks)
  const assigned = useFrameworkAssignments(orgId, systemId || undefined)
  const assignments = useMemo(() => resolveFrameworkAssignments(catalog.frameworks, versions.data, assigned.assignments),
    [catalog.frameworks, versions.data, assigned.assignments])
  const historyQuery = new URLSearchParams({ system_id: systemId, report_type: 'system-assurance' })
  if (definition) historyQuery.set('definition_id', definition.id)
  const history = useOrgResource<ReportVersion[]>(systemId ? `${reports.listReports}?${historyQuery}` : null)
  const saved = useOrgResource<ReportVersion>(systemId && versionId ? reports.report(versionId) : null)
  const [picked, setPicked] = useState('')
  const [period, setPeriod] = useState(() => initialInput?.period ?? previousFullMonth())
  const [narrative, setNarrative] = useState(initialInput?.narrative ?? '')
  const [name, setName] = useState('')
  const [preview, setPreview] = useState<ReportVersion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [action, setAction] = useState<'preview' | 'approve' | 'download' | 'save' | null>(null)
  const active = useRef(true)
  const reportPanel = useRef<HTMLDivElement>(null)
  const problem = useRef<HTMLParagraphElement>(null)
  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  const scope: Scope = {
    systemId,
    assignmentId: definition?.assignmentId ?? (picked || (assignments.length === 1 ? assignments[0].assignment.id : '')),
    dateFrom: period.from,
    dateTo: period.to,
    definitionId: definition?.id,
  }
  const assignment = assignments.find(({ assignment }) => assignment.id === scope.assignmentId)
  const catalogLoading = catalog.loading || versions.loading || assigned.loading
  const catalogError = catalog.error || versions.error || assigned.error
  function matchesHistory(entry: ReportVersion) {
    return matchesReport(entry, systemId, 'approved') && (!definition || (
      entry.config.definitionId === definition.id && entry.config.assignmentId === definition.assignmentId && entry.title === definition.title))
  }
  const approved = saved.data && saved.data.id === versionId && matchesHistory(saved.data) ? saved.data : null
  const visibleReport = versionId ? approved : preview
  const availableHistory = Array.isArray(history.data) ? history.data.filter(matchesHistory) : []
  const historyInvalid = history.data != null && !Array.isArray(history.data)
  const systemOptions = distinguishOptions(choices.map(({ id, name }) => ({ value: id, label: name })))
  const assignmentOptions = distinguishOptions(assignments.map(({ assignment, framework, version }) =>
    ({ value: assignment.id, label: `${framework.name} · ${version.versionLabel}` })))

  useEffect(() => {
    if (!error) return
    problem.current?.focus({ preventScroll: true })
    problem.current?.scrollIntoView({ block: 'nearest' })
  }, [error])

  useEffect(() => {
    if (!visibleReport) return
    const heading = reportPanel.current?.querySelector<HTMLElement>('#sar-review')
    heading?.focus({ preventScroll: true })
    heading?.scrollIntoView({ block: 'nearest' })
  }, [visibleReport])

  function clearPreview() {
    setPreview(null)
    setError(null)
  }

  async function saveDefinition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const title = name.trim()
    if (!orgId || !canWrite || !assignment || definition || !title || action) return
    setAction('save')
    setError(null)
    try {
      const response = await apiClient.post<ReportDefinition>(withOrg(reports.systemAssuranceDefinitions, orgId), {
        title, system_id: systemId, assignment_id: scope.assignmentId,
      })
      if (!active.current) return
      if (!response.success) throw new Error(response.error || 'The report setup could not be saved.')
      const record = response.data
      if (!isReportDefinition(record) || record.systemId !== systemId || record.assignmentId !== scope.assignmentId || record.title !== title) {
        throw new Error('The saved setup returned a different report scope.')
      }
      onDefinitionSaved(record, { period, narrative })
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The report setup could not be saved.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!orgId || !canWrite || !assignment || action) return
    clearPreview()
    setAction('preview')
    try {
      const response = await apiClient.post<ReportVersion>(withOrg(reports.previewSystemAssurance, orgId), {
        system_id: scope.systemId, assignment_id: scope.assignmentId,
        date_from: scope.dateFrom, date_to: scope.dateTo, narrative: narrative.trim(),
        ...(definition && { definition_id: definition.id }),
      })
      if (!response.success) throw new Error(response.error || 'The report could not be prepared.')
      if (!matchesReport(response.data, systemId, 'preview', scope) || response.data?.config.frameworkVersionId !== assignment.version.id ||
        (definition && response.data?.title !== definition.title)) {
        throw new Error('The preview returned a different report scope.')
      }
      if (active.current && response.data) {
        setPreview(response.data)
      }
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The report could not be prepared.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function approve() {
    if (!orgId || !canWrite || !preview || versionId || action) return
    setAction('approve')
    setError(null)
    try {
      const response = await apiClient.post<ReportVersion>(withOrg(reports.approveSystemAssurance(preview.id), orgId), { revision: preview.revision })
      if (!active.current) return
      if (response.apiError?.status === 409) {
        setPreview(null)
        setError('The report source records changed. Prepare a new preview before approving.')
        return
      }
      if (!response.success) throw new Error(response.error || 'The version could not be approved.')
      const record = response.data
      if (!record || record.id !== preview.id || record.revision !== preview.revision ||
        !matchesReport(record, systemId, 'approved', scope) || !matchesHistory(record)) {
        throw new Error('The server returned a different version. Refresh version history before trying again.')
      }
      setPreview(null)
      history.reload()
      onOpenVersion(record.id)
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The version could not be approved.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function download(format: ReportFormat) {
    if (!orgId || !approved || action) return
    setAction('download')
    setError(null)
    try {
      await downloadApprovedReport(orgId, approved.id, format, () => active.current)
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The version could not be downloaded.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  const scopePanel = (
    <section className="sar-scope" aria-labelledby="sar-scope">
      <h2 id="sar-scope">{versionId ? 'Report scope' : 'Prepare a report'}</h2>
      {definition ? <dl className="sar-saved-scope">
        <div><dt>AI system</dt><dd>{system?.name}</dd></div>
        <div><dt>Framework assignment</dt><dd>{assignment ? `${assignment.framework.name} · ${assignment.version.versionLabel}`
          : approved ? `${approved.data.framework.name} · ${approved.data.framework.versionLabel}`
          : catalogLoading ? 'Loading assignment…' : 'Assignment unavailable'}</dd></div>
      </dl> : <label className="sar-field">
        <span>AI system</span>
        <select value={systemId} disabled={systemsLoading || !choices.length || action !== null}
          onChange={(event) => onSystemChange(event.target.value)}>
          <option value="">{systemsLoading ? 'Loading systems…' : 'Select an AI system'}</option>
          {systemOptions.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>}
      {systemReadError && <div className="sar-small-error"><p role="alert">{systemReadError}</p>
        <Button type="button" variant="outline" onClick={onRetrySystems}>Retry systems</Button></div>}
      {!systemsLoading && !systemReadError && !choices.length && <p>Register an AI system to prepare its assurance report.</p>}
      {versionId ? (
        <>
          <p>This report was frozen when approved.</p>
          <Button type="button" variant="outline" size="lg" disabled={action !== null} onClick={() => {
            setError(null)
            setPeriod(previousFullMonth())
            setNarrative('')
            onOpenVersion()
          }}>
            {canWrite ? 'Prepare another report' : 'Back to version history'}
          </Button>
        </>
      ) : system && canWrite ? (
        <form onSubmit={(event) => void prepare(event)}>
          <fieldset disabled={action !== null}>
            {!definition && <label className="sar-field">
              <span>Framework assignment</span>
              <select value={scope.assignmentId} required disabled={catalogLoading || !assignments.length}
                onChange={(event) => { setPicked(event.target.value); clearPreview() }}>
                <option value="">{catalogLoading ? 'Loading assignments…' : 'Select an assignment'}</option>
                {assignmentOptions.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>}
            {catalogError && <div className="sar-small-error">
              <p role="alert">Framework assignments could not be loaded.</p>
              <Button type="button" variant="outline" onClick={() => void Promise.all([catalog.refresh(), versions.refresh(), assigned.refresh()])}>Retry assignments</Button>
            </div>}
            {!catalogLoading && !catalogError && (definition ? !assignment : !assignments.length) && <p>{definition
              ? 'The saved assignment is unavailable. Approved versions are still listed below.'
              : 'Assign a framework version to this system before preparing a report.'}</p>}
            {(definition ? Boolean(assignment) : Boolean(assignments.length)) && (
              <>
                <div className="sar-date-fields">
                  <label className="sar-field"><span>Start date</span><input type="date" required value={period.from} max={period.to || undefined}
                    onChange={(event) => { setPeriod({ ...period, from: event.target.value }); clearPreview() }} /></label>
                  <label className="sar-field"><span>End date</span><input type="date" required value={period.to} min={period.from || undefined}
                    onChange={(event) => { setPeriod({ ...period, to: event.target.value }); clearPreview() }} /></label>
                </div>
                <p className="sar-date-note"><CalendarDays size={15} aria-hidden /> {definition
                  ? 'Starts with the previous full month. Dates are inclusive, in UTC.' : 'Both dates are inclusive, in UTC.'}</p>
                <label className="sar-field"><span>Reviewer note <small>Optional</small></span>
                  <textarea rows={3} maxLength={4000} value={narrative} onChange={(event) => { setNarrative(event.target.value); clearPreview() }} />
                </label>
                <Button size="lg" type="submit" disabled={!orgId || !assignment || !period.from || !period.to || period.from > period.to}>
                  {action === 'preview' ? 'Preparing preview…' : 'Preview report'} <ArrowRight size={15} aria-hidden />
                </Button>
              </>
            )}
          </fieldset>
        </form>
      ) : system ? <p>Access to approved reports and exports is available for this system.</p> : null}
      {!definition && !versionId && canWrite && assignment && <details className="sar-save-setup">
        <summary className="sar-text-link"><Bookmark size={16} aria-hidden /> Save report setup</summary>
        <form onSubmit={(event) => void saveDefinition(event)}>
          <fieldset disabled={action !== null}>
            <p>Reuse this system and framework assignment for future reports.</p>
            <label className="sar-field"><span>Report name</span>
              <input required maxLength={160} value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <Button variant="outline" type="submit" disabled={!name.trim()}>{action === 'save' ? 'Saving setup…' : 'Save setup'}</Button>
          </fieldset>
        </form>
      </details>}
      {system && <Link className="sar-text-link sar-assurance-link" href={`/reports/system?view=assurance&system=${encodeURIComponent(systemId)}`}>
        View assurance details <ArrowUpRight size={14} aria-hidden />
      </Link>}
    </section>
  )

  const readingPanel = (
    <div ref={reportPanel} className="sar-reading">
      {visibleReport ? <ReportReview report={visibleReport} canApprove={canWrite} busy={action !== null}
        onApprove={() => void approve()} onDownload={(format) => void download(format)} />
        : versionId ? <section className="sar-paper sar-outline">
          <h2>{saved.loading || systemsLoading ? 'Loading approved version…' : 'Approved version unavailable'}</h2>
          {!saved.loading && !systemsLoading && <p role="alert">{saved.error || 'This version could not be found for the selected system.'}</p>}
        </section> : <ReportOutline />}
    </div>
  )

  const versionHistory = (
    <section className="sar-history" aria-labelledby="sar-history">
      <header>
        <div><h2 id="sar-history">Version history</h2><p>Open and re-export an approved version.</p></div>
        {system && <Button variant="outline" type="button" disabled={history.loading || action !== null} onClick={history.reload}>Refresh history</Button>}
      </header>
      {!system ? <p>Select a system to see its approved versions.</p>
        : history.loading ? <p role="status">Loading approved versions…</p>
        : history.error || historyInvalid ? <p role="alert">{history.error || 'Version history is unavailable.'}</p>
        : !availableHistory.length ? <p>{definition ? 'No approved versions for this saved report yet.' : 'No approved versions for this system yet.'}</p>
        : <ol>
          {availableHistory.map((report) => <li key={report.id}>
            <FileCheck2 size={21} aria-hidden />
            <div><strong>{report.title}</strong><p>{calendarDate(report.config.dateFrom)} – {calendarDate(report.config.dateTo)} · {report.data.framework.versionLabel}</p>
              <p>Approved {recordedAt(report.approvedAt)}</p></div>
            <Link className="sar-version-link" href={reportHref(systemId, report.id, report.config.definitionId)} aria-current={versionId === report.id ? 'page' : undefined}>
              Open approved version <ArrowRight size={14} aria-hidden />
            </Link>
          </li>)}
        </ol>}
    </section>
  )

  return (
    <>
      {error && <p ref={problem} role="alert" tabIndex={-1} className="sar-error">{error}</p>}
      {versionId === null && <p role="alert" className="sar-error">Choose one approved version from the history list.</p>}
      {versionId ? (
        <div className="sar-workspace" data-version="true">
          {readingPanel}
          <aside className="sar-version-sidebar" aria-label="Report versions and scope">{versionHistory}{scopePanel}</aside>
        </div>
      ) : definition && !visibleReport ? (
        canWrite ? <div className="sar-workspace">{scopePanel}{versionHistory}</div>
          : <div className="sar-workspace" data-version="true">{versionHistory}{scopePanel}</div>
      ) : (
        <>
          <div className="sar-workspace">{scopePanel}{readingPanel}</div>
          {versionHistory}
        </>
      )}
    </>
  )
}

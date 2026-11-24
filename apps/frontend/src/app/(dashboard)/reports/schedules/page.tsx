'use client'

import './schedules.css'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense, useState, type FormEvent, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { useNeedsYou } from '@/astryx/data/needsYou'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { isReportDefinition, reportHref, reportSchedulesHref, scheduledReportHref, type ReportDefinition } from '@/lib/assurance/reportDefinitions'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource, withOrg } from '@/lib/api/hooks/usePacks'
import { ReviewerEditor, type Reviewer } from './ReviewerEditor'

type ScheduleInput = { cadence: 'weekly' | 'monthly'; time_zone: string; local_time: string }
type Occurrence = { scheduledAt: string; dateFrom: string; dateTo: string }
type Run = Occurrence & {
  id: string; definitionId: string; systemId: string
  status: 'pending' | 'ready' | 'failed' | 'approved'
  error?: string | null; reportId?: string | null
  reviewer?: Reviewer | null
  reviewState?: 'awaiting_review' | 'returned' | 'approved' | null
  returned?: { reason: string; by: string; at: string; revision: string } | null
}
type Schedule = {
  definitionId: string; systemId: string; title: string
  cadence: ScheduleInput['cadence']; timeZone: string; localTime: string
  paused: boolean; next: Occurrence[]; latestRun?: Run | null; attentionRun?: Run | null
  defaultReviewer?: Reviewer | null
}

const reports = API_ENDPOINTS.aiGovernance
const noRetry = { enableRetry: false }
const runLabels = { pending: 'Pending preparation', ready: 'Awaiting review', failed: 'Failed', approved: 'Approved' } as const
const runOrder = { failed: 0, ready: 2, pending: 3, approved: 4 } as const
const isReturned = (run: Run) => run.status === 'ready' && run.reviewState === 'returned'
const runPriority = (run: Run) => isReturned(run) ? 1 : runOrder[run.status]
const draftLabel = (run: Run) => isReturned(run) ? 'Open returned draft' : 'Review draft'
const dateFormat = new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeZone: 'UTC' })
const timeZones = ['UTC', ...(Intl.supportedValuesOf?.('timeZone') ?? ['Asia/Kolkata', 'Europe/London', 'America/New_York'])]

function runTime(instant: string, timeZone = 'UTC') {
  const date = new Date(instant)
  if (!Number.isFinite(date.valueOf())) return 'Time unavailable'
  try {
    return new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone, timeZoneName: 'short' }).format(date)
  } catch {
    return `${date.toISOString().slice(0, 16).replace('T', ' ')} UTC`
  }
}

function evidenceWindow({ dateFrom, dateTo }: Occurrence) {
  const start = new Date(`${dateFrom}T00:00:00Z`)
  const end = new Date(`${dateTo}T00:00:00Z`)
  return Number.isFinite(start.valueOf()) && Number.isFinite(end.valueOf())
    ? `${dateFormat.format(start)} – ${dateFormat.format(end)}` : 'Evidence dates unavailable'
}

function StateMessage({ error, retry, children }: { error?: boolean; retry?: () => void; children: ReactNode }) {
  return <div className="rs-state">
    <p role={error ? 'alert' : 'status'}>{children}</p>
    {retry && <Button variant="outline" size="sm" onClick={retry}>Retry</Button>}
  </div>
}

function OccurrenceList({ entries, zone }: { entries: Occurrence[]; zone: string }) {
  return <ol className="rs-dates">
    {entries.map((item) => <li key={item.scheduledAt}>
      <time dateTime={item.scheduledAt}>{runTime(item.scheduledAt, zone)}</time>
      <p>Evidence window · {evidenceWindow(item)} UTC</p>
    </li>)}
  </ol>
}

function RunStatus({ run }: { run: Run }) {
  return isReturned(run) ? <span className="rs-status" data-state="returned">Returned</span>
    : <span className="rs-status" data-state={run.status}>{runLabels[run.status]}</span>
}

function ScheduleWorkspace({ definition, schedule, orgId, canWrite, canPause, refresh }: {
  definition: ReportDefinition; schedule?: Schedule; orgId: string; canWrite: boolean; canPause: boolean; refresh: () => void
}) {
  const history = useOrgResource<Run[]>(schedule ? reports.systemAssuranceScheduleRuns(definition.id) : null)
  const reviewers = useOrgResource<Reviewer[]>(schedule && canWrite ? reports.systemAssuranceReviewers : null)
  const { reportAssignments: { reload: reloadReportAssignments } } = useNeedsYou()
  const [draft, setDraft] = useState<ScheduleInput | null>(null)
  const [preview, setPreview] = useState<Occurrence[] | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ error?: boolean; text: string } | null>(null)
  const input = draft ?? { cadence: schedule?.cadence ?? 'monthly', time_zone: schedule?.timeZone ?? 'UTC', local_time: schedule?.localTime?.slice(0, 5) ?? '09:00' }
  const valid = input.time_zone.trim() && /^\d{2}:\d{2}$/.test(input.local_time)
  const runs = Array.isArray(history.data) ? history.data.filter((run) => run.definitionId === definition.id && run.systemId === definition.systemId)
    .sort((a, b) => runPriority(a) - runPriority(b) || b.scheduledAt.localeCompare(a.scheduledAt)) : []

  function change(patch: Partial<ScheduleInput>) {
    setDraft({ ...input, ...patch })
    setPreview(null)
    setFeedback(null)
  }

  async function perform(action: string, request: () => Promise<void>) {
    if (busy) return
    setBusy(action)
    setFeedback(null)
    try {
      await request()
    } catch (error) {
      setFeedback({ error: true, text: error instanceof Error ? error.message : 'The request failed. Try again.' })
    } finally {
      setBusy(null)
    }
  }

  function previewSchedule() {
    if (!valid || !canWrite) return
    void perform('preview', async () => {
      setPreview(null)
      const response = await apiClient.post<{ next: Occurrence[] }>(withOrg(reports.previewSystemAssuranceSchedule, orgId), { ...input, time_zone: input.time_zone.trim() }, noRetry)
      if (!response.success || !Array.isArray(response.data?.next) || !response.data.next.length) {
        throw new Error(response.error || 'Upcoming preparation dates are unavailable.')
      }
      setPreview(response.data.next)
    })
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!valid || !canWrite) return
    void perform('save', async () => {
      const response = await apiClient.put<Schedule>(withOrg(reports.systemAssuranceSchedule(definition.id), orgId), { ...input, time_zone: input.time_zone.trim() }, noRetry)
      if (!response.success) throw new Error(response.error || 'The schedule could not be saved.')
      setPreview(null)
      setFeedback({ text: schedule ? 'Schedule updated.' : 'Schedule created.' })
      refresh()
    })
  }

  function togglePause() {
    if (!schedule || !canPause || (schedule.paused && !canWrite)) return
    void perform('pause', async () => {
      const response = await apiClient.patch<Schedule>(withOrg(reports.systemAssuranceSchedule(definition.id), orgId), { paused: !schedule.paused }, noRetry)
      if (!response.success) throw new Error(response.error || 'The schedule status could not be changed.')
      setPreview(null)
      setFeedback({ text: schedule.paused ? 'Schedule resumed.' : 'Schedule paused.' })
      refresh()
    })
  }

  function retryRun(run: Run) {
    if (!canWrite) return
    void perform(run.id, async () => {
      const response = await apiClient.post<Run>(withOrg(reports.retrySystemAssuranceRun(run.id), orgId), undefined, noRetry)
      if (!response.success) throw new Error(response.error || 'Preparation could not be retried.')
      reloadReportAssignments()
      history.reload()
      refresh()
    })
  }

  async function assignDefaultReviewer(reviewerId: string | null) {
    const response = await apiClient.patch<Schedule>(withOrg(reports.systemAssuranceScheduleReviewer(definition.id), orgId), { reviewer_id: reviewerId }, noRetry)
    if (!response.success) throw new Error(response.error || 'The default reviewer could not be saved.')
    refresh()
  }

  async function assignRunReviewer(runId: string, reviewerId: string | null) {
    const response = await apiClient.patch<Run>(withOrg(reports.systemAssuranceRunReviewer(runId), orgId), { reviewer_id: reviewerId }, noRetry)
    if (!response.success) throw new Error(response.error || 'The run reviewer could not be saved.')
    reloadReportAssignments()
    history.reload()
    refresh()
  }

  const pauseControl = schedule && canPause && (!schedule.paused || canWrite) && (
    <Button type="button" variant="outline" disabled={busy !== null} onClick={togglePause}>
      {schedule.paused ? 'Resume schedule' : 'Pause schedule'}
    </Button>
  )

  return <div className="rs-detail">
    <section className="rs-panel" aria-labelledby="rs-current-title">
      <header className="rs-panel-head">
        <div><h2 id="rs-current-title">{definition.title}</h2>
          <Link href={reportHref(definition.systemId, undefined, definition.id)}>Open saved report</Link>
        </div>
        {schedule && <span className="rs-status" data-state={schedule.paused ? 'paused' : 'active'}>{schedule.paused ? 'Paused' : 'Active'}</span>}
      </header>
      {canWrite ? <form className="rs-form" onSubmit={save}>
        <fieldset className="rs-fields" disabled={busy !== null}>
          <div><label htmlFor="rs-cadence">Cadence</label><select id="rs-cadence" value={input.cadence} onChange={(event) => change({ cadence: event.target.value as ScheduleInput['cadence'] })}>
            <option value="weekly">Weekly · Monday</option><option value="monthly">Monthly · 1st day</option>
          </select></div>
          <div><label htmlFor="rs-time-zone">Time zone</label><input id="rs-time-zone" list="rs-zones" value={input.time_zone} required onChange={(event) => change({ time_zone: event.target.value })} />
            <datalist id="rs-zones">{timeZones.map((zone) => <option key={zone} value={zone} />)}</datalist>
          </div>
          <div><label htmlFor="rs-local-time">Local time</label><input id="rs-local-time" type="time" value={input.local_time} required onChange={(event) => change({ local_time: event.target.value })} /></div>
        </fieldset>
        <div className="rs-actions">
          <Button type="submit" disabled={!valid || busy !== null}>{busy === 'save' ? 'Saving…' : schedule ? 'Save changes' : 'Create schedule'}</Button>
          <Button type="button" variant="outline" disabled={!valid || busy !== null} onClick={previewSchedule}>{busy === 'preview' ? 'Calculating…' : 'Preview schedule'}</Button>
          {pauseControl}
        </div>
      </form> : <>
        <p>{schedule ? `${schedule.cadence === 'weekly' ? 'Mondays' : 'First day of each month'} at ${schedule.localTime.slice(0, 5)} · ${schedule.timeZone}.` : 'No schedule set for this report.'}</p>
        {pauseControl && <div className="rs-actions">{pauseControl}</div>}
      </>}
      {feedback && <p className="rs-feedback" role={feedback.error ? 'alert' : 'status'}>{feedback.text}</p>}
      {schedule && <section className="rs-reviewer" aria-labelledby="rs-default-reviewer">
        <h3 id="rs-default-reviewer">Default reviewer</h3>
        <p>{schedule.defaultReviewer ? `${schedule.defaultReviewer.name} is assigned to future runs.` : 'Future runs have no assigned reviewer.'}</p>
        {canWrite && <ReviewerEditor label="Reviewer for future runs"
          current={schedule.defaultReviewer} reviewers={reviewers} disabled={busy !== null} onSave={assignDefaultReviewer} />}
      </section>}
      {preview ? <section className="rs-upcoming" aria-label="Schedule preview" aria-live="polite">
        <h3>Schedule preview</h3><OccurrenceList entries={preview} zone={input.time_zone.trim()} />
      </section> : schedule && <section className="rs-upcoming" aria-label="Upcoming preparations">
        <h3>Upcoming preparations</h3>
        {schedule.paused ? <p>{canWrite ? 'Resume the schedule to allow new preparations.' : 'New preparations are paused.'}</p>
          : schedule.next.length ? <OccurrenceList entries={schedule.next} zone={schedule.timeZone} /> : <p>No upcoming preparations were returned.</p>}
      </section>}
    </section>

    <section className="rs-panel" id="schedule-history" aria-labelledby="rs-history-title">
      <header className="rs-panel-head"><h2 id="rs-history-title">Run history</h2>
        {schedule && <Button variant="outline" size="sm" onClick={history.reload} disabled={history.loading}>Refresh history</Button>}
      </header>
      {history.loading && !history.data ? <StateMessage>Loading run history…</StateMessage>
        : schedule && (history.error || !Array.isArray(history.data)) ? <StateMessage error retry={history.reload}>Run history could not be loaded.</StateMessage>
        : runs.length ? <ol className="rs-runs">
          {runs.map((run) => <li key={run.id}>
            <div><time dateTime={run.scheduledAt}>{runTime(run.scheduledAt)}</time><p>Evidence window · {evidenceWindow(run)} UTC</p>
              {(run.reviewer || run.status === 'ready') && <p>Reviewer · {run.reviewer?.name || 'Unassigned'}</p>}
              {run.status === 'failed' && <p className="rs-run-error">{run.error || 'Preparation failed.'}</p>}
              {isReturned(run) && run.returned?.reason && <p className="rs-returned-reason"><strong>Return reason</strong>{run.returned.reason}</p>}
            </div>
            <div className="rs-run-actions"><RunStatus run={run} />
              {run.status === 'ready' && canWrite && <Button variant="outline" size="sm" asChild><Link href={scheduledReportHref(run.systemId, run.definitionId, run.id)}>{draftLabel(run)}</Link></Button>}
              {run.status === 'approved' && run.reportId && <Button variant="outline" size="sm" asChild><Link href={scheduledReportHref(run.systemId, run.definitionId, run.id)}>Open approved version</Link></Button>}
              {run.status === 'failed' && canWrite && <Button variant="outline" size="sm" disabled={busy !== null} onClick={() => retryRun(run)}>{busy === run.id ? 'Retrying…' : 'Retry preparation'}</Button>}
            </div>
            {run.status === 'ready' && canWrite && <details className="rs-run-reviewer">
              <summary>Reassign reviewer</summary>
              <ReviewerEditor label="Run reviewer" current={run.reviewer}
                reviewers={reviewers} disabled={busy !== null} onSave={(reviewerId) => assignRunReviewer(run.id, reviewerId)} />
            </details>}
          </li>)}
        </ol> : <p>No scheduled preparations yet.</p>}
    </section>
  </div>
}

function Schedules() {
  const selection = useSearchParams().get('definition') || ''
  const { selectedOrg } = useOrg()
  const { systems } = useSystemContext()
  const saved = useOrgResource<ReportDefinition[]>(reports.systemAssuranceDefinitions)
  const register = useOrgResource<Schedule[]>(reports.systemAssuranceSchedules)
  const definitions = Array.isArray(saved.data) ? saved.data.filter(isReportDefinition) : []
  const scheduleList = Array.isArray(register.data) ? register.data : []
  const selected = definitions.find((item) => item.id === selection)
  const schedule = selected && scheduleList.find((item) => item.definitionId === selected.id && item.systemId === selected.systemId)
  const canWrite = Boolean(selectedOrg && (['owner', 'admin', 'editor'].includes(selectedOrg.role) || selectedOrg.permissions?.includes('model:write')))
  const systemById = new Map(systems.filter((system) => system.metadata?.source !== 'fallback').map((system) => [system.id, system]))
  const mayEditSystem = (systemId: string) => canWrite && systemById.get(systemId)?.stage !== 'retired'
  const attention = scheduleList.flatMap((schedule) => {
    const run = schedule.attentionRun === undefined ? schedule.latestRun : schedule.attentionRun
    return run && run.systemId === schedule.systemId && run.definitionId === schedule.definitionId &&
      (run.status === 'failed' || run.status === 'ready') ? [{ title: schedule.title, run }] : []
  }).sort((a, b) => runPriority(a.run) - runPriority(b.run))
  const loading = (saved.loading && !saved.data) || (register.loading && !register.data)
  const registerError = Boolean(register.error) || (!register.loading && !Array.isArray(register.data))
  const savedError = Boolean(saved.error) || (!saved.loading && !Array.isArray(saved.data))

  return <div className="fm-page rs-page">
    <header className="rs-head">
      <Link href="/reports">Reports</Link>
      <h1>Report schedules</h1>
      <p>Prepare drafts from saved system assurance reports on a recurring schedule. Each draft needs human approval.</p>
    </header>
    {!registerError && attention.length > 0 && <section className="rs-panel rs-attention" aria-labelledby="rs-attention-title">
      <h2 id="rs-attention-title">Needs attention</h2>
      <ul className="rs-runs">{attention.map(({ title, run }) => {
        const canReview = run.status === 'ready' && mayEditSystem(run.systemId)
        return <li key={run.id}>
          <div><strong>{title}</strong><p>{runTime(run.scheduledAt)}</p>
            {run.reviewer && <p>Reviewer · {run.reviewer.name}</p>}
          </div>
          <div className="rs-run-actions"><RunStatus run={run} />
            <Link href={canReview ? scheduledReportHref(run.systemId, run.definitionId, run.id) : `${reportSchedulesHref(run.definitionId)}#schedule-history`}>{canReview ? draftLabel(run) : 'View run history'}</Link>
          </div>
        </li>
      })}</ul>
    </section>}

    <div className="rs-layout">
      <section className="rs-panel rs-register" aria-labelledby="rs-register-title">
        <h2 id="rs-register-title">Schedules</h2>
        {savedError ? <StateMessage error retry={saved.reload}>Saved reports could not be loaded.</StateMessage>
          : saved.loading && !saved.data ? <StateMessage>Loading saved reports…</StateMessage>
          : definitions.length ? <div className="rs-select"><label htmlFor="rs-definition">Saved report</label><select id="rs-definition" value={selected?.id ?? ''} onChange={(event) => window.history.pushState(null, '', reportSchedulesHref(event.target.value))}>
            <option value="">Choose a saved report</option>
            {definitions.map((item) => <option key={item.id} value={item.id}>{item.title}{systemById.has(item.systemId) ? ` · ${systemById.get(item.systemId)?.name}` : ''}</option>)}
          </select></div> : <p><Link href="/reports">Save a report setup in Reports</Link> to schedule its preparation.</p>}
        {registerError ? <StateMessage error retry={register.reload}>Schedules could not be loaded.</StateMessage>
          : register.loading && !register.data ? <StateMessage>Loading schedules…</StateMessage>
          : scheduleList.length ? <ul className="rs-schedule-list">
            {scheduleList.map((item) => <li key={item.definitionId}>
              <Link href={reportSchedulesHref(item.definitionId)} aria-current={item.definitionId === selection ? 'page' : undefined}>
                <strong>{item.title}</strong><span>{item.paused ? 'Paused' : item.next[0] ? `Next · ${runTime(item.next[0].scheduledAt, item.timeZone)}` : 'Next preparation unavailable'}</span>
              </Link>
            </li>)}
          </ul> : <p>No schedules configured yet.</p>}
      </section>

      {selected && selectedOrg && !registerError && !savedError && !loading ? (
        <ScheduleWorkspace key={`${selectedOrg.id}:${selected.id}`} definition={selected} schedule={schedule} orgId={selectedOrg.id} canWrite={mayEditSystem(selected.systemId)} canPause={canWrite} refresh={register.reload} />
      ) : selection && !selected && !loading && !savedError ? (
        <section className="rs-panel"><h2>Saved report unavailable</h2><p>Choose an available saved report to view its schedule.</p></section>
      ) : !selection && !loading && !savedError && definitions.length > 0 ? (
        <section className="rs-panel"><h2>Choose a saved report</h2><p>Open a saved report to view its next preparations and past runs.</p></section>
      ) : null}
    </div>
  </div>
}

export default function ReportSchedulesPage() {
  return <Suspense fallback={<div className="fm-page rs-page"><h1>Report schedules</h1><p role="status">Loading schedules…</p></div>}><Schedules /></Suspense>
}

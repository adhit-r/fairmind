'use client'

import { CalendarDays, Check, Clock3, FileCheck2, RotateCcw, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { useNeedsYou } from '@/astryx/data/needsYou'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource, withOrg } from '@/lib/api/hooks/usePacks'
import type { ReportDefinition } from '@/lib/assurance/reportDefinitions'
import { ReportReview } from './ReportReview'
import { downloadApprovedReport, type ReportFormat } from './report-export'
import { calendarDate, matchesReport, recordedAt, type ReportVersion } from './report-version'

const endpoints = API_ENDPOINTS.aiGovernance
const staleMessage = 'The reviewed revision is no longer current. Refresh the evidence for this run before approving.'

type Run = {
  id: string
  definitionId: string
  systemId: string
  scheduledAt: string
  dateFrom: string
  dateTo: string
  status: 'pending' | 'ready' | 'failed' | 'approved'
  error?: string | null
  reportId?: string | null
  attemptedAt?: string | null
  reviewer?: { id: string; name: string } | null
  reviewState?: 'awaiting_review' | 'returned' | 'approved' | null
  returned?: { reason: string; by: string; at: string; revision: string } | null
}

type ScheduledReview = { run: Run; report?: ReportVersion | null; canReview?: boolean; canRefresh?: boolean }

function matchesRunReport(report: ReportVersion | null | undefined, run: Run, definition: ReportDefinition, status: ReportVersion['status']) {
  return Boolean(report && report.id === run.reportId && report.title === definition.title &&
    matchesReport(report, definition.systemId, status, {
      systemId: definition.systemId,
      assignmentId: definition.assignmentId,
      definitionId: definition.id,
      dateFrom: run.dateFrom,
      dateTo: run.dateTo,
    }))
}

export function ScheduledAssuranceReview({ orgId, definition, runId, canWrite }: {
  orgId: string
  definition: ReportDefinition
  runId: string
  canWrite: boolean
}) {
  const resource = useOrgResource<ScheduledReview>(endpoints.reviewSystemAssuranceRun(runId))
  const { reportAssignments: { reload: reloadReportAssignments } } = useNeedsYou()
  const [action, setAction] = useState<'approve' | 'return' | 'retry' | 'download' | null>(null)
  const [error, setError] = useState('')
  const [blockedRevision, setBlockedRevision] = useState<string | null>(null)
  const [showReturn, setShowReturn] = useState(false)
  const [returnReason, setReturnReason] = useState('')
  const [submittedReturn, setSubmittedReturn] = useState<Run | null>(null)
  const active = useRef(true)
  const problem = useRef<HTMLParagraphElement>(null)
  const reasonInput = useRef<HTMLTextAreaElement>(null)
  const returnBanner = useRef<HTMLElement>(null)
  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])
  useEffect(() => {
    if (error) problem.current?.focus()
  }, [error])
  useEffect(() => {
    if (showReturn) reasonInput.current?.focus()
  }, [showReturn])

  const record = resource.data
  const currentRun = record?.run
  const keepReturnedState = currentRun?.status === 'ready' && Boolean(record?.report?.revision) &&
    submittedReturn?.returned?.revision === record?.report?.revision
  const run = keepReturnedState ? submittedReturn : currentRun
  const draft = run?.status === 'ready'
  const approved = run?.status === 'approved'
  const returned = draft && run.reviewState === 'returned'
  const report = (draft || approved) && run && matchesRunReport(record?.report, run, definition, draft ? 'preview' : 'approved')
    ? record?.report : null
  const sourceChanged = draft && !returned && Boolean(report && report.revision === blockedRevision)
  const canReview = canWrite && draft && !returned && (record?.canReview ?? !run?.reviewer)
  const canRefresh = canWrite && (record?.canRefresh ?? true)
  const busy = action !== null || resource.loading
  useEffect(() => {
    if (submittedReturn && returned) {
      returnBanner.current?.focus({ preventScroll: true })
      returnBanner.current?.scrollIntoView({ block: 'center' })
    }
  }, [submittedReturn, returned])

  async function approve() {
    if (!run || !report || !canReview || busy || sourceChanged || showReturn) return
    setAction('approve')
    setError('')
    try {
      const response = await apiClient.post<ReportVersion>(withOrg(endpoints.approveSystemAssurance(report.id), orgId), {
        revision: report.revision,
      })
      if (response.success) reloadReportAssignments()
      if (!active.current) return
      if (response.apiError?.status === 409) {
        setBlockedRevision(report.revision)
        setError(staleMessage)
        return
      }
      if (response.apiError?.status === 403) resource.reload()
      if (!response.success) throw new Error(response.error || 'The version could not be approved.')
      if (response.data?.revision !== report.revision || !matchesRunReport(response.data, run, definition, 'approved')) {
        throw new Error('The server returned a different approved version.')
      }
      resource.reload()
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The version could not be approved.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function returnDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const reason = returnReason.trim()
    if (!run?.reviewer || !report || !canReview || sourceChanged || busy || !reason) return
    setAction('return')
    setError('')
    try {
      const response = await apiClient.post<Run>(withOrg(endpoints.returnSystemAssuranceRun(runId), orgId), {
        revision: report.revision, reason,
      }, { enableRetry: false })
      if (response.success) reloadReportAssignments()
      if (!active.current) return
      if (response.apiError?.status === 409 || response.apiError?.status === 403) {
        setShowReturn(false)
        resource.reload()
      }
      if (!response.success) throw new Error(response.error || 'The draft could not be returned.')
      const updated = response.data
      if (updated?.id !== runId || updated.definitionId !== definition.id || updated.systemId !== definition.systemId ||
        updated.reviewState !== 'returned' || updated.returned?.revision !== report.revision) {
        throw new Error('The server returned a different review record.')
      }
      setSubmittedReturn(updated)
      setShowReturn(false)
      setReturnReason('')
      resource.reload()
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The draft could not be returned.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function retry() {
    if (!canRefresh || busy || (!sourceChanged && !returned && run?.status !== 'failed')) return
    setAction('retry')
    setError('')
    try {
      const response = await apiClient.post<Run>(withOrg(endpoints.retrySystemAssuranceRun(runId), orgId), {})
      if (response.success) reloadReportAssignments()
      if (!active.current) return
      if (!response.success) throw new Error(response.error || 'This run could not be prepared again.')
      resource.reload()
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'This run could not be prepared again.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  async function download(format: ReportFormat) {
    if (!approved || !report || busy) return
    setAction('download')
    setError('')
    try {
      await downloadApprovedReport(orgId, report.id, format, () => active.current)
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : 'The version could not be downloaded.')
    } finally {
      if (active.current) setAction(null)
    }
  }

  if (!run && resource.loading) return <section className="sar-paper sar-outline"><p role="status">Loading scheduled run…</p></section>
  if (resource.error || !run || !['pending', 'ready', 'failed', 'approved'].includes(run.status) ||
    run.id !== runId || run.definitionId !== definition.id || run.systemId !== definition.systemId ||
    ((draft || approved) && !report) || (returned && run.returned?.revision !== report?.revision) || (!canWrite && !approved)) {
    return <section className="sar-paper sar-outline">
      <h2>Scheduled run unavailable</h2>
      <p role="alert">The run could not be opened for this saved report.</p>
      {(returned || resource.error) && resource.errorStatus !== 404 && resource.errorStatus !== 403 &&
        <Button className="sar-run-retry" type="button" variant="outline" onClick={resource.reload}>Retry loading run</Button>}
    </section>
  }

  const failed = run.status === 'failed'
  const returnAction = canReview && Boolean(run.reviewer) && !sourceChanged && (showReturn ? (
    <form className="sar-return-form" onSubmit={(event) => void returnDraft(event)}>
      <label className="sar-field"><span>Reason for returning</span>
        <textarea ref={reasonInput} rows={3} required maxLength={1000} disabled={busy} value={returnReason}
          onChange={(event) => setReturnReason(event.target.value)} />
      </label>
      <div className="sar-review-actions">
        <Button type="submit" disabled={busy || !returnReason.trim()}>{action === 'return' ? 'Returning…' : 'Return draft'}</Button>
        <Button type="button" variant="outline" disabled={busy} onClick={() => { setShowReturn(false); setReturnReason('') }}>Cancel</Button>
      </div>
    </form>
  ) : <Button size="lg" type="button" variant="outline" disabled={busy} onClick={() => setShowReturn(true)}>Return for changes</Button>)
  return (
    <>
      {(error || sourceChanged) && <div className="sar-error sar-run-alert">
        <p ref={problem} role="alert" tabIndex={-1}>{error || staleMessage}</p>
        {canRefresh && sourceChanged && <Button type="button" variant="outline" disabled={busy} onClick={() => void retry()}>
          {action === 'retry' ? 'Preparing…' : 'Refresh evidence'}
        </Button>}
      </div>}
      {returned && run.returned && <section ref={returnBanner} tabIndex={-1} className="sar-paper sar-return-decision" aria-label="Return decision">
        <div className="sar-return-mark"><RotateCcw size={18} aria-hidden /></div>
        <div><h2>Returned for changes</h2><p>{run.returned.reason}</p>
          <small>{run.returned.by} · {recordedAt(run.returned.at)}</small></div>
        {canRefresh && <Button type="button" variant="outline" disabled={busy} onClick={() => void retry()}>
          {action === 'retry' ? 'Preparing…' : 'Prepare new revision'}
        </Button>}
      </section>}
      <div className="sar-workspace" data-version="true">
        <div className="sar-reading">
          {report ? <ReportReview report={report} canApprove={canReview && !sourceChanged && !showReturn} showApproval={canReview && !showReturn}
            busy={busy} stale={sourceChanged} returned={returned} reviewer={run.reviewer?.name} reviewAction={returnAction}
            onApprove={() => void approve()} onDownload={(format) => void download(format)} />
            : <section className="sar-paper sar-outline">
              <div className="sar-document-mark" aria-hidden>{failed ? <TriangleAlert size={24} /> : <Clock3 size={24} />}</div>
              <h2>{failed ? 'Preparation failed' : 'Waiting for preparation'}</h2>
              <p role={failed ? 'alert' : 'status'}>{failed ? run.error || 'The scheduled report could not be prepared.' : 'Refresh this run to check for its report preview.'}</p>
              {!failed && <Button className="sar-run-retry" type="button" variant="outline" disabled={busy} onClick={resource.reload}>Refresh run</Button>}
              {canRefresh && failed && <Button className="sar-run-retry" type="button" variant="outline" disabled={busy} onClick={() => void retry()}>
                {action === 'retry' ? 'Preparing…' : 'Retry preparation'}
              </Button>}
            </section>}
        </div>
        <aside className="sar-paper sar-outline sar-run-trail" aria-labelledby="sar-scheduled-preparation">
          <h2 id="sar-scheduled-preparation">Scheduled preparation</h2>
          <ol>
            <li>
              <span><CalendarDays size={16} aria-hidden /></span>
              <div><strong>Scheduled {recordedAt(run.scheduledAt)}</strong>
                <p>{calendarDate(run.dateFrom)} – {calendarDate(run.dateTo)} UTC evidence</p></div>
            </li>
            <li>
              <span>{failed ? <TriangleAlert size={16} aria-hidden /> : <FileCheck2 size={16} aria-hidden />}</span>
              <div><strong>{report ? 'Report prepared' : failed ? 'Preparation failed' : 'Preparation pending'}</strong>
                {run.attemptedAt && <p>{recordedAt(run.attemptedAt)}</p>}</div>
            </li>
            <li data-current={draft && !sourceChanged && !returned}>
              <span>{approved ? <Check size={16} aria-hidden /> : returned ? <RotateCcw size={16} aria-hidden /> : <Clock3 size={16} aria-hidden />}</span>
              <div><strong>{approved ? 'Approved by a reviewer' : returned ? 'Returned for changes'
                  : sourceChanged ? 'Evidence changed' : draft ? 'Awaiting review' : 'Review starts after preparation'}</strong>
                {run.reviewer && <p>Reviewer · {run.reviewer.name}</p>}
                {approved && <p>{recordedAt(report?.approvedAt)}</p>}</div>
            </li>
          </ol>
        </aside>
      </div>
    </>
  )
}

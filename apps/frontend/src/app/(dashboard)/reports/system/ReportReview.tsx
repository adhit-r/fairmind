'use client'

import Link from 'next/link'
import type { ReactNode } from 'react'
import { ArrowUpRight, BookOpenCheck, ChevronDown, FileCheck2, FileText, ListChecks } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { evidenceRecordHref } from '@/lib/assurance/evidenceLinks'
import { findingHref } from '@/lib/assurance/evaluationLinks'
import { calendarDate, recordedAt, type ReportVersion } from './report-version'

function label(value?: string | null) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1).replaceAll('_', ' ') : 'Unavailable'
}

export function ReportOutline() {
  return (
    <section className="sar-paper sar-outline" aria-labelledby="sar-outline">
      <div className="sar-document-mark" aria-hidden><FileText size={25} strokeWidth={1.6} /></div>
      <h2 id="sar-outline">What the report includes</h2>
      <ul>
        <li><ListChecks aria-hidden size={19} /><div><strong>Control assessments</strong><p>Recorded status for the assigned framework version.</p></div></li>
        <li><BookOpenCheck aria-hidden size={19} /><div><strong>Evidence index</strong><p>Source records captured in the selected period, with links to inspect them.</p></div></li>
        <li><FileCheck2 aria-hidden size={19} /><div><strong>Limitations and reviewer note</strong><p>Coverage gaps and context carried into the approved export.</p></div></li>
      </ul>
    </section>
  )
}

export function ReportReview({ report, canApprove, busy, stale = false, returned = false, reviewer, showApproval = true, reviewAction, onApprove, onDownload }: {
  report: ReportVersion
  canApprove: boolean
  busy: boolean
  stale?: boolean
  returned?: boolean
  reviewer?: string
  showApproval?: boolean
  reviewAction?: ReactNode
  onApprove: () => void
  onDownload: (format: 'pdf' | 'docx' | 'json') => void
}) {
  const { data, status } = report
  const approved = status === 'approved'
  const covered = data.controls.filter((control) => control.acceptedEvidenceCount > 0).length
  const total = data.coverage.controls
  const coverage = total > 0 ? Math.min(100, (covered / total) * 100) : 0
  return (
    <article className="sar-paper sar-review" aria-labelledby="sar-review">
      <header className="sar-review-heading">
        <div>
          <p className="sar-document-status" data-approved={approved}><i aria-hidden />
            {approved ? 'Approved version' : returned ? 'Returned for changes' : stale ? 'Evidence changed' : 'Ready for review'}
          </p>
          <h2 id="sar-review" tabIndex={-1}>{approved ? 'Approved report' : 'Report preview'}</h2>
          <p className="sar-report-system">{data.system.name}</p>
        </div>
        {approved && <Button size="lg" type="button" disabled={busy} onClick={() => onDownload('pdf')}>Download PDF</Button>}
      </header>
      <dl className="sar-report-facts">
        <div><dt>Framework assignment</dt><dd>{data.framework.name} · {data.framework.versionLabel}</dd></div>
        <div><dt>Evidence window</dt><dd>{calendarDate(data.period.dateFrom)} – {calendarDate(data.period.dateTo)} UTC</dd></div>
        {data.system.version && <div><dt>System version at preparation</dt><dd>{data.system.version}</dd></div>}
        {approved && <div><dt>Approved</dt><dd>{recordedAt(report.approvedAt)}{report.approvedBy && ` · ${report.approvedBy}`}</dd></div>}
        <div><dt>Prepared</dt><dd>{recordedAt(data.generatedAt)}</dd></div>
        {!approved && reviewer && <div><dt>Assigned reviewer</dt><dd>{reviewer}</dd></div>}
      </dl>

      <section className="sar-report-summary" aria-label="Report coverage">
        <div>
          <span>Evidence runs in period</span>
          <strong>{data.coverage.evidenceRuns}</strong>
        </div>
        <div>
          <span>Controls with accepted evidence</span>
          <p><strong>{covered}</strong> <span>of {total}</span></p>
          {total > 0 && <span className="sar-track" aria-hidden><i style={{ width: `${coverage}%` }} /></span>}
        </div>
      </section>

      <div className="sar-report-body">
        {!!data.findings?.length && <section aria-labelledby="sar-findings">
          <h3 id="sar-findings">Open findings</h3>
          <p>System-level findings opened during the evidence window. Status is as recorded at preparation.</p>
          <ul className="sar-index">
            {data.findings.map((finding) => <li className="sar-control-row" key={finding.id}>
              <div><Link href={findingHref(report.systemId, finding.id)} className="sar-text-link">{finding.title} <ArrowUpRight size={14} aria-hidden /></Link>
                <small>Opened {recordedAt(finding.createdAt)}</small></div>
              <span className="sar-state">{label(finding.severity)} · {label(finding.status)}</span>
            </li>)}
          </ul>
        </section>}
        {report.narrative && <section aria-label="Reviewer note"><h3>Reviewer note</h3><p className="sar-note">{report.narrative}</p></section>}
        {!!data.limitations.length && <section aria-label="Limitations">
          <h3>Limitations</h3>
          <ul className="sar-limits">{data.limitations.map((text, index) => <li key={`${index}:${text}`}>{text}</li>)}</ul>
        </section>}
        <section aria-labelledby="sar-evidence">
          <h3 id="sar-evidence">Evidence index</h3>
          {!data.evidence.length ? <p>No evidence runs matched this assignment and period.</p> : (
            <ol className="sar-index">
              {data.evidence.map((item) => (
                <li key={item.id}>
                  <details>
                    <summary>
                      <span><strong>{item.suiteName || item.sourceIdentifier || 'Evaluation evidence'}</strong>
                        <small>{recordedAt(item.capturedAt)} · {label(item.result)}{item.stale ? ' · Stale' : ''}</small>
                      </span>
                      <ChevronDown size={16} aria-hidden />
                    </summary>
                    <dl className="sar-evidence-facts">
                      <div><dt>Source</dt><dd>{item.sourceIdentifier || label(item.sourceType)}</dd></div>
                      <div><dt>Run ID</dt><dd>{item.runId}</dd></div>
                      {item.contentHash && <div><dt>Content hash</dt><dd>{item.contentHash}</dd></div>}
                      {item.subjectVersion && <div><dt>System version</dt><dd>{item.subjectVersion}</dd></div>}
                    </dl>
                    {!!item.measurements?.length && (
                      <ul className="sar-limits" aria-label="Recorded measurements">
                        {item.measurements.map((metric, index) => <li key={`${index}:${metric.name}`}>
                          {metric.name}{metric.slice && ` · ${metric.slice}`} <strong>{metric.value}{metric.unit && ` ${metric.unit}`}</strong>
                          {metric.thresholdMet === false && ' · Threshold failed'}
                        </li>)}
                      </ul>
                    )}
                    {!!item.thresholds?.length && (
                      <ul className="sar-limits" aria-label="Recorded thresholds">
                        {item.thresholds.map((metric, index) => <li key={`${index}:${metric.metric}`}>
                          {metric.metric} {metric.operator} {metric.value}{metric.unit && ` ${metric.unit}`}
                        </li>)}
                      </ul>
                    )}
                    {item.evidenceId && <Link className="sar-text-link" href={evidenceRecordHref(report.systemId, item.evidenceId)}>
                      Open evidence <ArrowUpRight size={14} aria-hidden />
                    </Link>}
                    {!!item.limitations?.length && <ul className="sar-limits">{item.limitations.map((text) => <li key={text}>{text}</li>)}</ul>}
                    {!!item.scopeExclusions?.length && <ul className="sar-limits" aria-label="Scope exclusions">
                      {item.scopeExclusions.map((text) => <li key={text}>{text}</li>)}
                    </ul>}
                  </details>
                </li>
              ))}
            </ol>
          )}
        </section>
        <details className="sar-controls">
          <summary>Control assessments <span>{data.controls.length}</span><ChevronDown size={16} aria-hidden /></summary>
          {data.controls.length ? (
            <ul className="sar-index">
              {data.controls.map((control) => (
                <li className="sar-control-row" key={control.id}>
                  <span><strong>{control.externalId} {control.title}</strong><small>{label(control.applicability)} · {label(control.evidenceStatus)}</small></span>
                  <span className="sar-state">{label(control.status)}</span>
                </li>
              ))}
            </ul>
          ) : <p>No control assessments were recorded for this assignment.</p>}
        </details>
      </div>

      {(approved || showApproval || reviewAction) && <footer className="sar-report-footer">
        {approved ? (
          <>
            <div className="sar-version-integrity"><span>Version ID</span><code>{report.id}</code>
              {report.sha256 && <details><summary>Show integrity hash</summary><code>{report.sha256}</code></details>}
            </div>
            <div className="sar-downloads">
              <Button size="lg" type="button" variant="outline" disabled={busy} onClick={() => onDownload('docx')}>DOCX</Button>
              <Button size="lg" type="button" variant="outline" disabled={busy} onClick={() => onDownload('json')}>JSON</Button>
            </div>
          </>
        ) : (
          <>
            {showApproval && <p>{stale ? 'Refresh the evidence to review the current revision.' : 'Approval freezes this revision for export.'}</p>}
            <div className="sar-review-actions">
              {showApproval && <Button size="lg" type="button" disabled={!canApprove || busy} onClick={onApprove}>Approve version</Button>}
              {reviewAction}
            </div>
          </>
        )}
      </footer>}
    </article>
  )
}

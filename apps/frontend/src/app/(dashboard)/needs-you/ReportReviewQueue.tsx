'use client'

import Link from 'next/link'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading } from '@astryxdesign/core/Text'
import { useNeedsYou } from '@/astryx/data/needsYou'
import { scheduledReportHref } from '@/lib/assurance/reportDefinitions'

const periodDate = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
})

function periodLabel(start: string, end: string) {
  const from = new Date(start)
  const to = new Date(end)
  return Number.isFinite(from.getTime()) && Number.isFinite(to.getTime()) && from <= to
    ? periodDate.formatRange(from, to)
    : `${start} – ${end}`
}

export function ReportReviewQueue() {
  const { reportAssignments: assignments } = useNeedsYou()
  const rows = assignments.data
  const unavailable = assignments.error || (!assignments.loading && !Array.isArray(rows))
  if (!unavailable && Array.isArray(rows) && rows.length === 0) return null

  return (
    <section className="fm-report-review-queue" aria-labelledby="assigned-report-heading">
      <Heading level={2} id="assigned-report-heading">Reports awaiting your review</Heading>
      {unavailable ? (
        <Banner
          status="error"
          title="Assigned reports could not load"
          description={assignments.error || 'The report queue returned an incomplete response.'}
          endContent={<Button label="Retry report reviews" size="sm" variant="secondary" onClick={assignments.reload} />}
        />
      ) : !Array.isArray(rows) ? (
        <div aria-busy="true" aria-label="Loading assigned report reviews"><Skeleton height={40} /></div>
      ) : (
        <ul className="fm-report-review-list">
          {rows.map(({ title, systemName, run }) => (
            <li key={run.id}>
              <div>
                <strong>{title}</strong>
                <span>{systemName} · {periodLabel(run.dateFrom, run.dateTo)} UTC</span>
              </div>
              <Link
                href={scheduledReportHref(run.systemId, run.definitionId, run.id)}
                aria-label={`Review draft of ${title} for ${systemName}, ${periodLabel(run.dateFrom, run.dateTo)}`}
              >Review draft</Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

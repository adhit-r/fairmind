'use client'

import '@/astryx/pages/internal-audit.css'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { useMembers } from '@/astryx/data/settings'
import { gradeLabel, useAudit, useAuditTrace, useManagementReview } from '@/lib/api/hooks/useInternalAudit'

export default function AuditRecordsPage() {
  const { id } = useParams<{ id: string }>()
  const trace = useAuditTrace(id)
  const review = useManagementReview(id)
  const audit = useAudit(id)
  const members = useMembers(useOrg().selectedOrg?.id)
  const who = (uid: string | null) => { const m = members.data.find((x) => x.user_id === uid); return m?.name || m?.email || uid || 'system' }

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Text color="secondary"><Link href={`/internal-audit/${id}`}>Back to the audit</Link></Text>
          <Heading level={1}>Audit records</Heading>
        </VStack>

        <section className="ia-card" aria-label="Trace verification">
          <VStack gap={3}>
            <Heading level={2}>Trace verification</Heading>
            {trace.error ? <Banner status="error" title="The trace could not load" description={trace.error} /> : trace.loading || !trace.data ? <Skeleton height={80} /> : (
              <>
                <Banner status={trace.data.valid ? 'success' : 'error'} title={trace.data.valid ? 'The trace verifies' : 'The trace does not verify'} description={trace.data.head ? `Head ${trace.data.head}` : 'No events yet.'} />
                <ul className="ia-list">
                  <li><span>Hash chain intact</span><small>{trace.data.chainValid ? 'Yes' : 'No'}</small></li>
                  <li><span>Chain ends at the issued report</span><small>{audit.data?.audit.status !== 'issued' ? 'Not issued yet' : trace.data.headMatchesIssue ? 'Yes' : 'No'}</small></li>
                  <li><span>Records match the chain</span><small>{trace.data.mismatches.length ? `${trace.data.mismatches.length} differ` : 'Yes'}</small></li>
                  {trace.data.mismatches.map((m) => <li key={m.checkId}><span className="ia-bad">Check {m.checkId}: {m.reason}</span></li>)}
                </ul>
                <ul className="ia-list">
                  {trace.data.events.map((e) => (
                    <li key={e.seq}><span><b>{e.seq}. {e.kind.replace(/_/g, ' ')}</b> <small>{e.createdAt} · {who(e.actor)} · {e.hash.slice(0, 12)}</small></span></li>
                  ))}
                </ul>
              </>
            )}
          </VStack>
        </section>

        <section className="ia-card" aria-label="Management review">
          <VStack gap={3}>
            <Heading level={2}>Results for the management review (clause 9.3)</Heading>
            {review.error ? <Banner status="error" title="The review could not load" description={review.error} /> : review.loading || !review.data ? <Skeleton height={80} /> : (
              <>
                <Text color="secondary">
                  {review.data.counts.concluded} of {review.data.counts.checks} checks concluded · {review.data.counts.openNonconformities} open nonconformities
                </Text>
                <ul className="ia-list">
                  {review.data.resultsByClause.map((r) => (
                    <li key={r.clause}>
                      <span><b>{r.clause}</b> {r.title}</span>
                      <small>{r.concluded} of {r.checks} concluded · {Object.entries(r.grades).filter(([, n]) => n).map(([g, n]) => `${n} ${gradeLabel(g)}`).join(', ') || 'no grades yet'}</small>
                    </li>
                  ))}
                </ul>
                {review.data.openNonconformities.length > 0 && <Heading level={3}>Open nonconformities</Heading>}
                <ul className="ia-list">
                  {review.data.openNonconformities.map((n) => (
                    <li key={n.checkId}>
                      <span><b>{n.clause}</b> {n.systemName} · {gradeLabel(n.grade)}<br /><small>{n.statement}</small></span>
                      <small>{n.owner ?? 'No owner'}{n.dueDate ? ` · due ${n.dueDate}` : ''}{n.status ? ` · ${n.status}` : ''}</small>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </VStack>
        </section>
      </VStack>
    </div>
  )
}

'use client'

import '@/astryx/pages/decisions.css'
import { useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useApprovalDecisions, useApprovalRequests, useSystemSeals } from '@/astryx/data/approvals'

type Status = 'pending' | 'approved' | 'rejected'
const WORD: Record<Status, string> = { pending: 'Pending', approved: 'Approved', rejected: 'Rejected' }
const COLOR: Record<Status, 'orange' | 'green' | 'red'> = { pending: 'orange', approved: 'green', rejected: 'red' }
const when = (iso?: string) => (iso ? new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Not recorded')

export default function DecisionsPage() {
  const { systems } = useSystemContext()
  const requests = useApprovalRequests()
  const [filter, setFilter] = useState<Status>('pending')
  const [openId, setOpenId] = useState<string | null>(null)

  const names = useMemo(() => new Map(systems.map((s) => [s.id, s.name])), [systems])
  const rows = useMemo(
    () => (requests.data ?? []).filter((r) => names.has(r.entity_id)).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
    [requests.data, names],
  )
  const count = (s: Status) => rows.filter((r) => r.status === s).length
  const visible = rows.filter((r) => r.status === filter)
  const open = rows.find((r) => r.id === openId) ?? null

  // Decisions and seals are read only for the request that is open.
  const decisions = useApprovalDecisions(open?.id ?? null)
  const seals = useSystemSeals(open?.entity_id ?? null)

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Decisions</Heading>
          <Text color="secondary">Every release decision for your systems, who asked, and the sealed record of what was decided. Waiting requests are decided on the system file, beside its release gate.</Text>
        </VStack>

        {requests.error && <Banner status="error" title="Decisions could not load" description={requests.error} endContent={<Button label="Try again" size="sm" onClick={() => requests.reload()} />} />}

        <SegmentedControl label="Filter by status" value={filter} onChange={(v) => setFilter(v as Status)}>
          {(Object.keys(WORD) as Status[]).map((s) => (
            <SegmentedControlItem key={s} value={s} label={`${WORD[s]} ${count(s)}`} />
          ))}
        </SegmentedControl>

        <section className="fm-card" aria-label="Approval requests">
          {requests.loading && !requests.data ? (
            <VStack gap={2}>{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={36} />)}</VStack>
          ) : visible.length === 0 ? (
            <EmptyState title={`No ${WORD[filter].toLowerCase()} requests`} description="Release approval requests appear here once a system asks for one from its file." />
          ) : (
            <div>
              <div className="fm-dec-row fm-dec-head" aria-hidden>
                <span>System</span><span>Requested by</span><span>Status</span><span>Updated</span>
              </div>
              {visible.map((r) => (
                <button key={r.id} type="button" className="fm-dec-row" onClick={() => setOpenId(r.id)}>
                  <b>{names.get(r.entity_id)}</b>
                  <span>{r.requested_by ?? 'Not recorded'}</span>
                  <Token size="sm" color={COLOR[r.status]} label={WORD[r.status]} />
                  <span>{when(r.updatedAt)}</span>
                </button>
              ))}
            </div>
          )}
        </section>
      </VStack>

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && setOpenId(null)} label={open ? `Decision for ${names.get(open.entity_id)}` : 'Decision'} width={480} padding={5}>
        {open && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              <Token size="sm" color={COLOR[open.status]} label={WORD[open.status]} />
              <Heading level={2}>{names.get(open.entity_id)}</Heading>
              <Text type="supporting">Requested {when(open.createdAt)}{open.requested_by ? ` by ${open.requested_by}` : ''}</Text>
            </VStack>

            {open.status === 'pending' && (
              <VStack gap={2} align="start">
                <Text color="secondary">This request waits for a reviewer. The decision is made on the system file, beside the release gate it rests on.</Text>
                <Button label="Review and decide" variant="primary" href={`/systems/${encodeURIComponent(open.entity_id)}?decide`} />
              </VStack>
            )}

            <VStack gap={2}>
              <Heading level={3}>Decisions</Heading>
              {decisions.loading && !decisions.data ? <Skeleton height={36} /> : decisions.error ? (
                <Text color="secondary">{decisions.error}</Text>
              ) : (decisions.data ?? []).length === 0 ? (
                <Text color="secondary">No decision has been recorded on this request yet.</Text>
              ) : (
                (decisions.data ?? []).map((d) => (
                  <div key={d.id} className="fm-seal">
                    <HStack gap={2} vAlign="center">
                      <Token size="sm" color={d.decision === 'approved' ? 'green' : 'red'} label={d.decision === 'approved' ? 'Approved' : 'Rejected'} />
                      <Text type="supporting">{d.decided_by ?? 'Not recorded'}, {when(d.createdAt)}</Text>
                    </HStack>
                    {d.notes && <Text>{d.notes}</Text>}
                  </div>
                ))
              )}
            </VStack>

            <VStack gap={2}>
              <Heading level={3}>Sealed records for this system</Heading>
              {seals.loading && !seals.data ? <Skeleton height={56} /> : seals.error ? (
                <Text color="secondary">{seals.error}</Text>
              ) : (seals.data ?? []).length === 0 ? (
                <Text color="secondary">Nothing sealed yet. A seal is made when a decision is recorded.</Text>
              ) : (
                (seals.data ?? []).map((s) => (
                  <div key={s.id} className="fm-seal">
                    <HStack gap={2} vAlign="center" wrap="wrap">
                      <Token size="sm" color={s.decision === 'approved' ? 'green' : 'red'} label={s.decision === 'approved' ? 'Approved' : 'Rejected'} />
                      <Token size="sm" color={s.verification.status === 'intact' ? 'green' : 'red'} label={s.verification.status === 'intact' ? 'Intact' : 'Broken'} />
                    </HStack>
                    <Text type="supporting">
                      {s.gate?.verdict ? `Gate said ${s.gate.verdict.replace(/_/g, ' ')}` : 'No gate verdict stored'}
                      {typeof s.gate?.confidence === 'number' ? ` at confidence ${s.gate.confidence.toFixed(2)}` : ''}
                    </Text>
                    <Text type="supporting">{s.evidenceCount} evidence item{s.evidenceCount === 1 ? '' : 's'}, sealed by {s.sealedBy ?? 'not recorded'}, {when(s.createdAt)}</Text>
                    <code>{s.chainHead.slice(0, 12)}</code>
                  </div>
                ))
              )}
            </VStack>

            <Button label="Open the system file" variant="secondary" href={`/systems/${encodeURIComponent(open.entity_id)}`} />
          </VStack>
        )}
      </Drawer>
    </div>
  )
}

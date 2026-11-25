'use client'

import { Empty } from '@/components/packs/parts'
import type { ApprovalStatus, DecisionSeal } from '@/lib/api/hooks/useSystemFile'

const when = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '')
const word = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
const ROW = 'grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-3 border-t border-[var(--fm-line)] px-[18px] py-2.5 text-[13px]'

function Head({ title, count }: { title: string; count: number }) {
  return (
    <div className="flex items-baseline gap-2 px-[18px] pb-3 pt-4">
      <h2 className="text-[15px] font-semibold tracking-[-0.01em]">{title}</h2>
      <span className="text-[12px] tabular-nums text-[var(--fm-ink3)]">{count}</span>
    </div>
  )
}

/** The sealed decisions, newest first, and the decisions recorded on the approval request. */
export function RecordTab({ seals, approval }: { seals: DecisionSeal[]; approval: ApprovalStatus | null }) {
  const decisions = approval?.decisions ?? []
  return (
    <>
      <section className="fm-card overflow-hidden" aria-label="Sealed decisions">
        <Head title="Sealed decisions" count={seals.length} />
        {seals.length === 0 ? (
          <div className="px-[18px] pb-[18px]">
            <Empty>A seal is taken when a release decision is recorded.</Empty>
          </div>
        ) : (
          <ul>
            {seals.map((s) => {
              const v = s.verification
              const broken = [v.changed.length && `${v.changed.length} changed`, v.missing.length && `${v.missing.length} missing`].filter(Boolean).join(', ')
              return (
                <li key={s.id} className={ROW}>
                  <span className="min-w-0">
                    <b className="font-semibold">{word(s.decision)}</b>
                    <span className="text-[var(--fm-ink2)]"> · {s.sealedBy || 'Not named'} · {when(s.createdAt)}</span>
                    <span className="ml-2 font-mono text-[11.5px] text-[var(--fm-ink3)]" title={s.chainHead}>
                      {s.chainHead.slice(0, 12)}
                    </span>
                  </span>
                  {v.status === 'intact' ? (
                    <span className="text-[12px] text-[var(--fm-ink2)]" title={`${s.evidenceCount} record${s.evidenceCount === 1 ? '' : 's'} sealed${v.addedSince ? `, ${v.addedSince} added since` : ''}`}>
                      Intact
                    </span>
                  ) : (
                    <span className="text-[12px] font-medium text-[#b4232c]" title={broken ? `${broken} since the seal` : undefined}>
                      Broken
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </section>
      <section className="fm-card overflow-hidden" aria-label="Approval decisions">
        <Head title="Approval decisions" count={decisions.length} />
        {decisions.length === 0 ? (
          <div className="px-[18px] pb-[18px]">
            <Empty>{approval?.request ? 'No decision recorded on the request yet.' : 'No release decision requested yet.'}</Empty>
          </div>
        ) : (
          <ul>
            {decisions.map((d) => (
              <li key={d.id} className={ROW}>
                <span className="min-w-0">
                  <b className="font-semibold">{word(d.decision)}</b>
                  <span className="text-[var(--fm-ink2)]"> · {d.decided_by || 'Not named'}</span>
                  {d.notes && <span className="block truncate text-[12px] text-[var(--fm-ink3)]" title={d.notes}>{d.notes}</span>}
                </span>
                <span className="text-[12px] tabular-nums text-[var(--fm-ink3)]">{when(d.createdAt)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}

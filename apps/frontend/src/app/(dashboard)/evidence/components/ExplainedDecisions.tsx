'use client'

import NextLink from 'next/link'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useExplainedDecisions } from '@/lib/api/hooks/usePacks'

const OK = '#1f7a4d'
const BAD = '#b4232c'
const CAP = 'text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]'
const CARD = 'flex min-w-0 flex-col gap-2 rounded-[12px] border border-[var(--fm-line)] bg-white px-3.5 py-3'
const STATUS: Record<string, [string, string]> = {
  passed: ['Passed', 'bg-[#e3f2ea] text-[#1f7a4d]'],
  failed: ['Failed', 'bg-[#fde9ea] text-[#b4232c]'],
  insufficient: ['Not enough runs', 'bg-[#ececea] text-[var(--fm-ink2)]'],
}

/** Records: every system's Explanation quality runs on live runs, kept as evidence, and the runs explained in the last 30 days. */
export function ExplainedDecisions() {
  const res = useExplainedDecisions()
  const t = res.data?.totals
  const pct = (part: number, whole: number) => (whole ? `${Math.round((part / whole) * 100)}%` : '-')
  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Explained decisions</Heading>
            <Text color="secondary">Recorded decisions replayed to test the reason each system stated. Every test is kept as evidence for human oversight.</Text>
          </VStack>
          <Button label="Back to evidence" variant="secondary" href="/evidence" />
        </HStack>
        {res.loading && !res.data ? (
          <Skeleton height={160} />
        ) : res.error || !res.data || !t ? (
          <EmptyState title="Explained decisions could not load" description={res.error ?? ''} actions={<Button label="Try again" onClick={res.reload} />} />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
              <div className={CARD}><span className={CAP}>Systems sending decisions</span><b className="text-[22px] font-semibold tabular-nums">{t.systemsSending}</b><span className="text-[12px] text-[var(--fm-ink2)]">last 30 days</span></div>
              <div className={CARD}><span className={CAP}>Decisions explained</span><b className="text-[22px] font-semibold tabular-nums">{t.explained}</b><span className="text-[12px] text-[var(--fm-ink2)]">last 30 days</span></div>
              <div className={CARD}>
                <span className={CAP}>Reason held</span>
                <b className="text-[22px] font-semibold tabular-nums">{pct(t.held, t.held + t.notHeld)}</b>
                {t.explained > 0 && (
                  <div className="flex h-2.5 overflow-hidden rounded-full bg-[#ececea]" aria-label={`${t.held} held, ${t.notHeld} did not hold, ${t.notReproducible} not reproducible`}>
                    {([[t.held, OK], [t.notHeld, BAD], [t.notReproducible, 'var(--fm-ink3)']] as const).map(([n, c], i) => <div key={i} style={{ width: `${(n / t.explained) * 100}%`, background: c }} />)}
                  </div>
                )}
              </div>
              <div className={CARD}><span className={CAP}>Decisions with a flip found</span><b className="text-[22px] font-semibold tabular-nums">{pct(t.withFlip, t.scored)}</b><span className="text-[12px] text-[var(--fm-ink2)]">what would change the outcome</span></div>
            </div>
            {res.data.systems.length === 0 ? (
              <EmptyState title="No decision tested yet" description="Run Explanation quality on a system's live runs. It needs the system to send decisions with a stated reason, and a model connection to replay them on."
                actions={<Button label="Open Explanation quality" variant="primary" href="/compliance/evaluations/EV-OVS-04?source=traces" />} />
            ) : (
              <section className="fm-card" aria-label="Systems">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-left text-[13px]">
                    <thead>
                      <tr className={CAP}>{['System', 'Tests', 'Reason held, per test', 'Latest', 'Counts for'].map((h) => <th key={h} className="py-2 pr-3 font-medium">{h}</th>)}</tr>
                    </thead>
                    <tbody>
                      {res.data.systems.map((s) => {
                        const latest = s.runs[s.runs.length - 1]
                        const [label, tone] = STATUS[latest.status] ?? STATUS.insufficient
                        return (
                          <tr key={s.systemId} className="border-t border-[var(--fm-line)] align-middle">
                            <td className="py-2.5 pr-3"><NextLink href={`/systems/${encodeURIComponent(s.systemId)}`} className="font-semibold text-[var(--fm-ink)] underline">{s.name}</NextLink></td>
                            <td className="py-2.5 pr-3 tabular-nums">{s.runs.length}</td>
                            <td className="py-2.5 pr-3">
                              <span className="inline-flex items-center gap-2">
                                <span className="inline-flex gap-[2px]" aria-hidden>
                                  {s.runs.slice(-12).map((r) => <i key={r.evidenceId} className="block h-3.5 w-1.5 rounded-[2px]" style={{ background: r.status === 'passed' ? OK : r.status === 'failed' ? BAD : '#c9cbc8' }} />)}
                                </span>
                                <span className="tabular-nums">{latest.reasonHeldRate === null ? '-' : latest.reasonHeldRate.toFixed(2)}</span>
                              </span>
                            </td>
                            <td className="py-2.5 pr-3"><span className={`rounded-md px-2 py-0.5 text-[12px] font-medium ${tone}`}>{label}</span></td>
                            <td className="py-2.5 pr-3 text-[var(--fm-ink2)]">Human oversight</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}
      </VStack>
    </div>
  )
}

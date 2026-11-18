'use client'

import { pollWhileVisible } from '@/lib/poll'
import './board.css'
import Link from 'next/link'
import { Fragment, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Check, Clock, PenLine, RefreshCw, X } from 'lucide-react'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Token } from '@astryxdesign/core/Token'
import { VStack } from '@astryxdesign/core/Layout'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { useEstateGates, type EstateGate } from '@/lib/api/hooks/useEstate'
import { useNeedsYou } from '@/astryx/data/needsYou'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { checkCell, classLabel, KIND_TITLE, type CellState } from '@/components/ui/matrix'

/** The release checks the gate can score (environmental only where the organisation weighs it), in the order the release story reads, then the decision. */
const CHECKS: Array<{ key: GateCheck['key']; name: string; group: string }> = [
  { key: 'data_governance', name: 'Data governance', group: 'Data' },
  { key: 'fairness', name: 'Fairness', group: 'Test' },
  { key: 'human_oversight', name: 'Human oversight', group: 'Test' },
  { key: 'environmental', name: 'Environment', group: 'Test' },
  { key: 'monitoring', name: 'Monitoring', group: 'Operate' },
]
const GROUPS = ['Data', 'Test', 'Release', 'Operate']
type Col = { key: string; name: string; group: string }
const ALL_COLS: Col[] = [...CHECKS.slice(0, 4), { key: 'decision', name: 'Decision', group: 'Release' }, CHECKS[4]]

/** A decision cell: approved is proven; a pending request waits on a person; a rejection fails. */
type DecisionState = 'proven' | 'needs' | 'fails' | 'planned'
function decisionCell(status: string | null | undefined): DecisionState {
  if (status === 'approved') return 'proven'
  if (status === 'pending') return 'needs'
  if (status === 'rejected') return 'fails'
  return 'planned'
}
const DECISION_WORD: Record<DecisionState, string> = {
  proven: 'Approved',
  needs: 'Waiting for a reviewer',
  fails: 'Rejected',
  planned: 'Not requested',
}
const WORD: Record<CellState, string> = {
  proven: 'Proven',
  estimated: 'Estimated',
  partial: 'Partial',
  attested: 'Attested',
  excluded: 'Excluded',
  planned: 'Planned',
  open: 'Nothing on file',
  fails: 'Fails',
  stale: 'Out of date',
  atorg: 'Held at organisation',
}
const TOKEN: Record<string, 'green' | 'red' | 'orange' | 'blue' | 'gray'> = {
  proven: 'green',
  estimated: 'blue',
  attested: 'green',
  fails: 'red',
  stale: 'orange',
  needs: 'orange',
}

function CellMark({ state }: { state: string }) {
  if (state === 'proven') return <Check size={15} strokeWidth={2.6} aria-hidden />
  if (state === 'attested') return <PenLine size={13} strokeWidth={2.4} aria-hidden />
  if (state === 'fails') return <X size={15} strokeWidth={2.6} aria-hidden />
  if (state === 'stale') return <Clock size={13} strokeWidth={2.4} aria-hidden />
  if (state === 'needs') return <b />
  if (state === 'estimated') return <span className="tilde" aria-hidden>~</span>
  return null
}

type Section = 'attention' | 'progress' | 'approved'
const SECTIONS: Array<{ key: Section; title: string }> = [
  // A failing or stale check is work on the system; only a pending decision waits on a person
  // (and is on the Needs you page), so this group is not called Needs you.
  { key: 'attention', title: 'Needs attention' },
  { key: 'progress', title: 'Being checked' },
  { key: 'approved', title: 'Approved and watched' },
]

type Open = { system: AISystemSummary; gate: EstateGate; col: Col }

/** Every registered system against every release check, from the release gate of each. */
export function LiveBoard() {
  const { systems, loading: systemsLoading } = useSystemContext()
  const gates = useEstateGates()
  // The menu's Needs you counts everything waiting on a person; the release card counts decisions only.
  const inbox = useNeedsYou()
  const [open, setOpen] = useState<Open | null>(null)
  const [checkedAt, setCheckedAt] = useState<Date | null>(null)

  // The board is live: it re-reads the gates every minute and says when it last did.
  useEffect(() => {
    if (gates.data) setCheckedAt(new Date())
  }, [gates.data])
  useEffect(() => {
    return pollWhileVisible(() => gates.reload(), 60_000)
  }, [gates])

  const rows = useMemo(() => {
    const byId = new Map((gates.data ?? []).map((g) => [g.systemId, g]))
    return systems.flatMap((s) => {
      const gate = byId.get(s.id)
      return gate ? [{ system: s, gate }] : []
    })
  }, [systems, gates.data])
  // An organisation that keeps energy use out of its release gate gets no Environment column.
  const COLS = gates.data?.some((g) => g.checks.some((c) => c.key === 'environmental')) ? ALL_COLS : ALL_COLS.filter((c) => c.key !== 'environmental')

  const stateOf = (gate: EstateGate, col: Col): string => {
    if (col.key === 'decision') return decisionCell(gate.approvalStatus)
    const check = gate.checks.find((c) => c.key === col.key)
    return check ? checkCell(check) : 'open'
  }
  const sectionOf = (gate: EstateGate): Section => {
    const states = COLS.map((c) => stateOf(gate, c))
    if (states.some((s) => s === 'fails' || s === 'stale' || s === 'needs')) return 'attention'
    return gate.approvalStatus === 'approved' ? 'approved' : 'progress'
  }
  const stats = useMemo(() => {
    const all = rows.flatMap((r) => COLS.map((c) => stateOf(r.gate, c)))
    return {
      proven: all.filter((s) => s === 'proven' || s === 'attested').length,
      due: all.length,
      needs: rows.filter((r) => r.gate.approvalStatus === 'pending').length,
      fails: all.filter((s) => s === 'fails').length,
      stale: all.filter((s) => s === 'stale').length,
    }
    // stateOf is pure over its inputs
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows])

  if ((gates.loading && !gates.data) || systemsLoading) {
    return (
      <section className="fm-board" aria-busy="true" aria-label="Loading the board">
        <div className="fm-board-pad">
          <VStack gap={2}>
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={28} />
            ))}
          </VStack>
        </div>
      </section>
    )
  }
  if (gates.error) {
    return (
      <section className="fm-board">
        <EmptyState title="The board could not load" description={gates.error} actions={<Button label="Try again" onClick={() => gates.reload()} />} />
      </section>
    )
  }
  if (!rows.length) {
    return (
      <section className="fm-board">
        <EmptyState
          title="No registered AI systems yet"
          description="Register systems by hand or from a CSV, or connect a source and let discovery find them. Each registered system gets a row here."
          actions={
            <>
              <Button variant="primary" label="Register systems" href="/onboard" />
              <Button label="Find unregistered AI" href="/discovery" />
            </>
          }
        />
      </section>
    )
  }

  // A system with nothing on file and no decision asked for would be a row of empty cells: it is listed once above the board instead.
  const blank = (gate: EstateGate) => COLS.every((c) => ['open', 'planned'].includes(stateOf(gate, c)))
  const empty = rows.filter((r) => blank(r.gate))
  const shown = rows.filter((r) => !blank(r.gate))
  const pending = rows.filter((r) => r.gate.approvalStatus === 'pending')
  const noEvidence = (gate: EstateGate) => gate.checks.every((c) => checkCell(c) === 'open')

  const sel = open ? stateOf(open.gate, open.col) : null
  const others = inbox.loading ? 0 : Math.max(0, inbox.items.length - pending.length)
  const selCheck = open && open.col.key !== 'decision' ? open.gate.checks.find((c) => c.key === open.col.key) : undefined

  return (
    <>
    {(pending.length > 0 || empty.length > 0) && (
      <div className={`fm-board-cards${pending.length && empty.length ? ' two' : ''}`}>
        {pending.length > 0 && (
          <section className="fm-card fm-board-act" aria-labelledby="bd-needs">
            <VStack gap={2}>
              <span className="fm-board-eyebrow need">Release decision · {pending.length}</span>
              <Heading level={2} id="bd-needs">
                {pending.length === 1 ? `${pending[0].system.name} is waiting for a release decision` : `${pending.length} systems are waiting for a release decision`}
              </Heading>
              {pending.some((r) => noEvidence(r.gate)) && (
                <Text color="secondary">
                  {pending.length === 1 ? 'Nothing has been tested on it yet, so a decision would rest on no evidence.' : 'Some have nothing tested yet, so a decision would rest on no evidence.'} Run a first evaluation before you decide.
                </Text>
              )}
              <VStack gap={1}>
                {pending.map((r) => (
                  <Link key={r.system.id} href={`/systems/${encodeURIComponent(r.system.id)}`}>
                    Open {r.system.name}
                  </Link>
                ))}
                {others > 0 && <Link href="/needs-you">{`${others} more ${others === 1 ? 'thing waits' : 'things wait'} for you on Needs you`}</Link>}
              </VStack>
            </VStack>
          </section>
        )}
        {empty.length > 0 && (
          <section className="fm-card fm-board-act" aria-labelledby="bd-empty">
            <VStack gap={3}>
              <span className="fm-board-eyebrow">Nothing on file yet · {empty.length}</span>
              <Heading level={2} id="bd-empty">
                {empty.length === 1 ? `${empty[0].system.name} has no evidence yet` : `${empty.length} systems have no evidence yet`}
              </Heading>
              <ul className="fm-board-names">
                {empty.map((r) => (
                  <li key={r.system.id}>
                    <Link href={`/systems/${encodeURIComponent(r.system.id)}`}>{r.system.name}</Link>
                  </li>
                ))}
              </ul>
              <ol className="fm-board-steps">
                <li><Link href="/systems">Name an owner and confirm the risk tier</Link> on each system</li>
                <li><Link href="/frameworks">Confirm which frameworks apply</Link></li>
                <li><Link href="/evaluations">Run a first evaluation</Link></li>
              </ol>
              <Text type="supporting">A system moves onto the board below as soon as it has a result or a decision is asked for.</Text>
            </VStack>
          </section>
        )}
      </div>
    )}
    <section className="fm-board" aria-label="Every system against every release check">
      <header className="fm-board-top">
        <div className="fm-board-live" role="status">
          <i aria-hidden />
          <Text weight="semibold">Live</Text>
          <Text color="secondary" maxLines={1}>
            {checkedAt ? `Checked at ${checkedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}` : 'Checking'}
          </Text>
          <Button label="Check now" variant="ghost" size="sm" icon={<RefreshCw size={14} />} isIconOnly onClick={() => gates.reload()} />
        </div>
        <div className="fm-board-stats">
          <span>
            <b>{stats.proven}</b> of {stats.due} proven
          </span>
          <span className="need">
            <b>{stats.needs}</b> waiting for a decision
          </span>
          <span className="stale">
            <b>{stats.stale}</b> out of date
          </span>
          <span className="fail">
            <b>{stats.fails}</b> failing
          </span>
        </div>
      </header>
      {shown.length === 0 ? (
        <div className="fm-board-pad">
          <Text color="secondary">No system has a result yet. Each one appears here with its first evidence.</Text>
        </div>
      ) : (
      <div className="fm-board-scroll">
        <table>
          <thead>
            <tr className="groups">
              <th scope="col" rowSpan={2} className="name">
                System
              </th>
              {GROUPS.map((g) => (
                <th key={g} scope="colgroup" colSpan={COLS.filter((c) => c.group === g).length}>
                  {g}
                </th>
              ))}
              <th scope="col" rowSpan={2} className="sum">
                Confidence
              </th>
            </tr>
            <tr className="cols">
              {COLS.map((c, i) => (
                <th key={c.key} scope="col" className={i > 0 && COLS[i - 1].group !== c.group ? 'gap' : undefined}>
                  {c.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SECTIONS.map((sec) => {
              const mine = shown.filter((r) => sectionOf(r.gate) === sec.key)
              if (!mine.length) return null
              return (
                <Fragment key={sec.key}>
                  <tr className={`sec sec-${sec.key}`}>
                    <th colSpan={COLS.length + 2} scope="rowgroup">
                      {sec.title} <span>{mine.length}</span>
                    </th>
                  </tr>
                  {mine.map(({ system, gate }) => (
                    <tr key={system.id} className="row">
                      <th scope="row" className="name">
                        <Link href={`/systems/${encodeURIComponent(system.id)}`}>
                          <span>{system.name}</span>
                          <em>{system.riskTier}</em>
                        </Link>
                      </th>
                      {COLS.map((c, i) => {
                        const state = stateOf(gate, c)
                        const word = c.key === 'decision' ? DECISION_WORD[state as DecisionState] : WORD[state as CellState]
                        return (
                          <td key={c.key} className={i > 0 && COLS[i - 1].group !== c.group ? 'gap' : undefined}>
                            <button type="button" className={`cell ${state}`} aria-label={`${c.name} on ${system.name}: ${word}`} title={word} onClick={() => setOpen({ system, gate, col: c })}>
                              <CellMark state={state} />
                            </button>
                          </td>
                        )
                      })}
                      <td className="sum">
                        <span className="bar">
                          <b style={{ width: `${Math.round(gate.confidence * 100)}%` }} />
                        </span>
                        <span className="n">{gate.confidence.toFixed(2)}</span>
                      </td>
                    </tr>
                  ))}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
      )}
      <footer className="fm-board-key">
        <span>
          <i className="cell proven">
            <CellMark state="proven" />
          </i>
          Proven
        </span>
        <span>
          <i className="cell attested">
            <CellMark state="attested" />
          </i>
          Attested
        </span>
        <span>
          <i className="cell estimated">
            <CellMark state="estimated" />
          </i>
          Estimated
        </span>
        <span>
          <i className="cell needs">
            <CellMark state="needs" />
          </i>
          Needs you
        </span>
        <span>
          <i className="cell stale">
            <CellMark state="stale" />
          </i>
          Out of date
        </span>
        <span>
          <i className="cell fails">
            <CellMark state="fails" />
          </i>
          Fails
        </span>
        <span>
          <i className="cell open" />
          Nothing on file
        </span>
        <span className="hint">Click a cell to see what is behind it.</span>
      </footer>

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && setOpen(null)} label={open ? `${open.col.name} on ${open.system.name}` : 'Check'} width={440} padding={5}>
        {open && sel && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              <Token size="sm" color={TOKEN[sel] ?? 'gray'} label={open.col.key === 'decision' ? DECISION_WORD[sel as DecisionState] : WORD[sel as CellState]} />
              <Heading level={2}>{open.col.name}</Heading>
              <Text type="supporting">
                {open.system.name} · {open.system.riskTier} risk
              </Text>
            </VStack>
            <MetadataList label={{ width: 120 }}>
              {selCheck ? (
                <>
                  <MetadataListItem label="What it means">{KIND_TITLE[sel as CellState] ?? WORD[sel as CellState]}</MetadataListItem>
                  <MetadataListItem label="How we know">{selCheck.evidenceClass ? classLabel(selCheck.evidenceClass) : 'No evidence yet'}</MetadataListItem>
                  <MetadataListItem label="Confidence">{selCheck.confidence.toFixed(2)}</MetadataListItem>
                  <MetadataListItem label="Evidence">{selCheck.evidenceId ? <Text type="code">{selCheck.evidenceId}</Text> : 'None on file'}</MetadataListItem>
                </>
              ) : (
                <>
                  <MetadataListItem label="Release decision">{DECISION_WORD[sel as DecisionState]}</MetadataListItem>
                  <MetadataListItem label="Gate verdict">{open.gate.verdict.replace(/_/g, ' ')}</MetadataListItem>
                  <MetadataListItem label="Confidence">{open.gate.confidence.toFixed(2)}</MetadataListItem>
                </>
              )}
            </MetadataList>
            {sel === 'fails' && (
              <Text color="secondary">
                <AlertTriangle size={14} aria-hidden /> Measured, and it fails its threshold. The system file shows the path forward.
              </Text>
            )}
            <VStack gap={2}>
              {open.col.key === 'decision' && sel === 'needs' && <Button variant="primary" label="Decide now" href="/needs-you" />}
              {selCheck?.evidenceId && <Button variant="secondary" label="Open the evidence" href="/evidence" />}
              <Button variant={sel === 'needs' ? 'secondary' : 'primary'} label="Open the system file" href={`/systems/${encodeURIComponent(open.system.id)}`} />
            </VStack>
          </VStack>
        )}
      </Drawer>
    </section>
    </>
  )
}

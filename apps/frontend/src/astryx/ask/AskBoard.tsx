'use client'

import './askBoard.css'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Renderer } from '@openuidev/react-lang'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEstateFrameworks, useEstateGates, type EstateGate } from '@/lib/api/hooks/useEstate'
import { useNeedsYou } from '@/astryx/data/needsYou'
import { checkCell, type CellState } from '@/components/ui/matrix'
import '@/astryx/pages/frameworks.css'
import { ReadinessBar, readinessCounts } from '@/app/(dashboard)/frameworks/parts'
import { useJourneys } from '@/lib/api/hooks/usePacks'
import { buildAskLibrary, type FRAMEWORK_SCOPES, type RELEASE_FILTERS, type WAITING_KINDS } from './boardSpec'

type Pill = { text: string; tone: 'fail' | 'ok' | 'part' | 'na' }

const CHECK_TEXT: Partial<Record<CellState, Pill>> = {
  fails: { text: 'Fails', tone: 'fail' },
  proven: { text: 'Passes', tone: 'ok' },
  estimated: { text: 'Estimated', tone: 'part' },
  attested: { text: 'Attested', tone: 'part' },
  partial: { text: 'Partly', tone: 'part' },
  stale: { text: 'Stale', tone: 'part' },
  open: { text: 'Not run', tone: 'na' },
}
const DECISION_TEXT: Record<string, Pill> = {
  approved: { text: 'Approved', tone: 'ok' },
  pending: { text: 'Waiting', tone: 'part' },
  rejected: { text: 'Rejected', tone: 'fail' },
}

const decisionPill = (status: string | null | undefined): Pill => DECISION_TEXT[status ?? ''] ?? { text: 'Not decided', tone: 'na' }
const failing = (g: EstateGate) => g.checks.some((c) => checkCell(c) === 'fails') || g.approvalStatus === 'rejected'

function PillCell({ pill }: { pill: Pill }) {
  return <span className={`fm-askb-pill fm-askb-${pill.tone}`}>{pill.text}</span>
}

function ReleaseMatrix({ props }: { props: { filter: (typeof RELEASE_FILTERS)[number] } }) {
  const { systems, loading, error } = useSystemContext()
  const gates = useEstateGates()
  const rows = useMemo(() => {
    const byId = new Map((Array.isArray(gates.data) ? gates.data : []).map((g) => [g.systemId, g]))
    return systems
      .filter((s) => s.stage !== 'retired')
      .flatMap((s) => {
        const gate = byId.get(s.id)
        if (!gate || !Array.isArray(gate.checks)) return []
        if (props.filter === 'failing' && !failing(gate)) return []
        if (props.filter === 'waiting_decision' && gate.approvalStatus !== 'pending') return []
        return [{ system: s, gate }]
      })
  }, [systems, gates.data, props.filter])
  const cols = useMemo(() => {
    const seen = new Map<string, string>()
    rows.forEach(({ gate }) => gate.checks.forEach((c) => seen.has(c.key) || seen.set(c.key, c.label)))
    return [...seen.entries()]
  }, [rows])

  if ((loading || gates.loading) && !gates.data) return <Skeleton height={96} />
  if (error || gates.error) return <p className="fm-askb-note">The release checks could not load: {error ?? gates.error}</p>
  if (!rows.length) return <p className="fm-askb-note">No systems match this view.</p>
  return (
    <section className="fm-askb-card" aria-label="Release checks">
      <div className="fm-askb-scroll">
        <table className="fm-askb-table">
          <thead>
            <tr>
              <th scope="col">System</th>
              {cols.map(([key, label]) => <th scope="col" key={key}>{label}</th>)}
              <th scope="col">Decision</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ system, gate }) => (
              <tr key={system.id}>
                <th scope="row"><Link href={`/systems/${encodeURIComponent(system.id)}`}>{system.name}</Link></th>
                {cols.map(([key]) => {
                  const check = gate.checks.find((c) => c.key === key)
                  return <td key={key}><PillCell pill={(check && CHECK_TEXT[checkCell(check)]) || { text: 'Not run', tone: 'na' }} /></td>
                })}
                <td><PillCell pill={decisionPill(gate.approvalStatus)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function WaitingOnYou({ props }: { props: { kind: (typeof WAITING_KINDS)[number] } }) {
  const { items, loading } = useNeedsYou()
  const shown = props.kind === 'all' ? items : items.filter((i) => i.kind === props.kind)
  if (loading && !items.length) return <Skeleton height={64} />
  if (!shown.length) return <p className="fm-askb-note">Nothing is waiting on you here.</p>
  return (
    <section className="fm-askb-card" aria-label="Waiting on you">
      <ul className="fm-askb-list">
        {shown.slice(0, 8).map((i) => (
          <li key={i.id}>
            <div>
              <strong>{i.title}</strong>
              <span>{i.detail}</span>
            </div>
            {/* Deciding always happens on the page the link opens; the board never approves. */}
            <Link className="fm-askb-link" href={i.href ?? '/needs-you'}>{i.cta ?? 'Open'}</Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

function FrameworkReadiness({ props }: { props: { scope: (typeof FRAMEWORK_SCOPES)[number] } }) {
  const estate = useEstateFrameworks()
  const journeys = useJourneys()
  const names = useMemo(() => new Map((journeys.data ?? []).map((j) => [j.key, j.name])), [journeys.data])
  const rows = useMemo(
    () =>
      (estate.data?.frameworks ?? [])
        .filter((f) => names.has(f.key))
        .map((f) => ({ key: f.key, name: names.get(f.key) ?? f.key, counts: readinessCounts(f.states) }))
        .filter((f) => props.scope === 'all' || f.counts.attention > 0),
    [estate.data, names, props.scope],
  )
  if ((estate.loading && !estate.data) || (journeys.loading && !journeys.data)) return <Skeleton height={96} />
  if (estate.error || journeys.error) return <p className="fm-askb-note">The frameworks could not load: {estate.error ?? journeys.error}</p>
  if (!rows.length) return <p className="fm-askb-note">{props.scope === 'all' ? 'You follow no framework yet.' : 'No framework has requirements that need attention.'}</p>
  return (
    <section className="fm-askb-card fm-askb-frameworks" aria-label="Framework readiness">
      {rows.map((f) => (
        <div key={f.key}>
          <Link href={`/frameworks/${encodeURIComponent(f.key)}`}>{f.name}</Link>
          <ReadinessBar counts={f.counts} />
        </div>
      ))}
    </section>
  )
}

const library = buildAskLibrary({
  Board: ({ props, renderNode }) => <div className="fm-askb">{renderNode(props.widgets)}</div>,
  ReleaseMatrix,
  WaitingOnYou,
  FrameworkReadiness,
  Note: ({ props }) => <p className="fm-askb-note">{props.text}</p>,
})

/** The model's board, drawn with FairMind's own widgets. Anything that does not parse or validate draws nothing, and the written answer stands alone. */
export function AskBoard({ board }: { board?: string | null }) {
  const [failed, setFailed] = useState(false)
  if (!board?.trim() || failed) return null
  return <Renderer response={board} library={library} onError={(errors) => setFailed(errors.length > 0)} />
}

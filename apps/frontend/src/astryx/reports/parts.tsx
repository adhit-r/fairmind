import type { ReactNode } from 'react'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import type { Proof, ProofCounts } from './types'
import { ZONE_NAME, type Zone } from './geometry'

export const num = (n: number) => n.toLocaleString('en-GB')
export const word = (s: string | null | undefined) => (s ? s.replace(/[_-]+/g, ' ').replace(/^./, (c) => c.toUpperCase()) : '')
export const shortHash = (h: string) => (h.length > 12 ? `${h.slice(0, 6)}…${h.slice(-4)}` : h)
export const dayWord = (n: number | null | undefined) => (n == null ? 'Waiting' : n === 1 ? '1 day' : `${n} days`)
export const when = (iso: string | null | undefined) => {
  if (!iso) return 'Not recorded'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? 'Not recorded' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function Card({ span, title, sub, children, aside }: { span: 4 | 5 | 6 | 7 | 8 | 12; title: string; sub?: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className={`fm-card rp-card rp-c${span}`} aria-label={title}>
      <div className="rp-ct">
        <div>
          <h3>{title}</h3>
          {sub ? <p>{sub}</p> : null}
        </div>
        {aside}
      </div>
      {children}
    </section>
  )
}

/** A card that exists but has no rows. */
export const Empty = ({ title, text }: { title: string; text: string }) => <EmptyState title={title} description={text} />

export const Hero = ({ value, children, tone }: { value: ReactNode; children: ReactNode; tone?: 'up' | 'dn' }) => (
  <div className="rp-hero">
    <b className={tone ? `rp-${tone}` : undefined}>{value}</b>
    <span>{children}</span>
  </div>
)

export type Part = [count: number, cls: string, label: string]
export function SegBar({ parts, tall }: { parts: Part[]; tall?: boolean }) {
  const total = parts.reduce((a, p) => a + p[0], 0)
  if (!total) return <div className={`rp-seg${tall ? ' tall' : ''}`} aria-hidden="true"><i className="f-o" style={{ flex: 1 }} /></div>
  return (
    <div className={`rp-seg${tall ? ' tall' : ''}`} role="img" aria-label={parts.map((p) => `${p[2]} ${p[0]}`).join(', ')}>
      {parts
        .filter((p) => p[0] > 0)
        .map((p) => (
          <i key={p[2]} className={p[1]} style={{ flex: p[0] / total }} title={`${p[2]}: ${p[0]}`} />
        ))}
    </div>
  )
}

export const Legend = ({ items }: { items: [label: string, cls: string][] }) => (
  <div className="rp-legend">
    {items.map(([label, cls]) => (
      <span key={label}>
        <i className={`rp-sw ${cls}`} />
        {label}
      </span>
    ))}
  </div>
)

export const proofParts = (p: ProofCounts): Part[] => [
  [p.measured, 'f-m', 'Measured by FairMind'],
  [p.estimated, 'f-e', 'Tool estimate'],
  [p.attested, 'f-a', 'Attested by a person'],
  [p.none, 'f-o', 'No proof yet'],
]
export const PROOF_LEGEND: [string, string][] = [['Measured by FairMind', 'f-m'], ['Tool estimate', 'f-e'], ['Attested by a person', 'f-a'], ['No proof yet', 'f-o']]

export const ZONE_PILL: Record<Zone, string> = { 1: 'ok', 2: 'cond', 3: 'need', 4: 'fail' }
export const Pill = ({ tone, children }: { tone: 'ok' | 'fail' | 'need' | 'cond' | 'run' | 'none'; children: ReactNode }) => <span className={`rp-pill p-${tone}`}>{children}</span>
export const ZonePill = ({ zone, extra }: { zone: Zone; extra?: string }) => <Pill tone={ZONE_PILL[zone] as 'ok'}>{ZONE_NAME[zone]}{extra ? ` ${extra}` : ''}</Pill>

/** Share of backed requirements whose proof FairMind measured itself, or null when nothing is backed. */
export function measuredShare(p: ProofCounts): number | null {
  const backed = p.measured + p.estimated + p.attested
  return backed ? Math.round((p.measured / backed) * 100) : null
}

export function ProofBars({ proof, by }: { proof: Proof; by: 'system' | 'group' }) {
  const share = measuredShare(proof)
  const backed = proof.measured + proof.estimated + proof.attested
  const rows = by === 'system' ? proof.bySystem.map((r) => ({ key: r.systemId, name: r.name, c: r as ProofCounts })) : proof.byGroup.map((r) => ({ key: r.group, name: r.group, c: r as ProofCounts }))
  return (
    <>
      <Hero value={share === null ? 'None' : `${share}%`}>
        {share === null ? 'No requirement has proof yet' : `measured by FairMind · ${Math.round((proof.attested / backed) * 100)}% rests on attestation`}
      </Hero>
      <SegBar parts={proofParts(proof)} tall />
      <Legend items={PROOF_LEGEND} />
      {rows.length ? (
        <div className="rp-rows">
          {rows.map((r) => {
            const s = measuredShare(r.c)
            return (
              <div className="rp-rowbar" key={r.key}>
                <span className="n" title={r.name}>{r.name}</span>
                <SegBar parts={proofParts(r.c)} />
                <span className="p">{s === null ? '–' : `${s}%`}</span>
              </div>
            )
          })}
        </div>
      ) : null}
    </>
  )
}

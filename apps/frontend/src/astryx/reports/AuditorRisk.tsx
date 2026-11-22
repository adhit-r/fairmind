import Link from 'next/link'
import { IMPACT, LIKELIHOOD, ZONE_NAME, heatZone, type Zone } from './geometry'
import type { Auditor, ReadinessKey, RiskModel } from './types'
import { Card, Empty, Hero, Legend, Pill, ZonePill, dayWord, num, shortHash, when, word } from './parts'

const KIND: Record<string, string> = { agent: 'ag', step: 'ev', decision: 'de', audit: 'au', seal: 'se' }
const KIND_WORD: Record<string, string> = { agent: 'Agent step', step: 'Step', decision: 'Decision by a person', audit: 'Audit', seal: 'Seal' }

export function LedgerCard({ l }: { l: Auditor['ledger'] }) {
  return (
    <Card span={12} title="Ledger chain" sub="The latest entries. Each one carries the hash of the one before it.">
      {l.entries === 0 && l.intact ? (
        <Hero value="Empty">nothing is on the ledger yet</Hero>
      ) : (
        <Hero value={l.intact ? 'Unbroken' : 'Broken'} tone={l.intact ? 'up' : 'dn'}>{num(l.entries)} entries checked just now</Hero>
      )}
      {l.recent.length === 0 ? (
        <p className="rp-muted">No entries on the ledger yet.</p>
      ) : (
        <div className="rp-chain">
          {l.recent.map((e, i) => (
            <i key={`${e.hash}-${i}`} className={`${KIND[e.kind] ?? 'ev'}${i === l.recent.length - 1 ? ' head' : ''}`} title={`${KIND_WORD[e.kind] ?? e.kind} · ${when(e.at)} · ${e.hash}`} />
          ))}
        </div>
      )}
      <Legend items={[['Agent step', 'f-a'], ['Step', 'f-m'], ['Decision by a person', 'rp-ink'], ['Audit', 'f-cond'], ['Seal', 'f-ok']]} />
      {l.chains.length ? (
        <div className="rp-stats">
          {l.chains.map((c) => (
            <div key={c.kind}>
              <b>{c.entries === null ? num(c.chains) : num(c.entries)}</b>
              <span>{c.entries === null ? 'chains of' : 'entries in'} {c.kind.toLowerCase()}{c.broken ? ` · ${c.broken} broken` : ''}</span>
            </div>
          ))}
        </div>
      ) : null}
    </Card>
  )
}

const MOS: Record<ReadinessKey | 'excluded', string> = { met: 'm-met', progress: 'm-part', attention: 'm-bad', notstarted: 'm-open', excluded: 'm-exc' }
const MOS_WORD: Record<ReadinessKey | 'excluded', string> = { met: 'Met', progress: 'Partly met', attention: 'Needs attention', notstarted: 'Open', excluded: 'Excluded' }
const isExcluded = (a: string | null) => !!a && /exclu|not.?applicable/i.test(a)

export function SoaCard({ soa }: { soa: Auditor['soa'] }) {
  if (!soa) {
    return (
      <Card span={7} title="Statement of applicability" sub="One system at a time.">
        <Empty title="Pick a system" text="Choose one system in the scope picker to see its statement of applicability." />
      </Card>
    )
  }
  const groups = new Map<string, typeof soa.controls>()
  for (const c of soa.controls) groups.set(c.group ?? 'Other', [...(groups.get(c.group ?? 'Other') ?? []), c])
  const tone = (c: (typeof soa.controls)[number]) => (isExcluded(c.applicability) ? 'excluded' : c.readiness)
  const count = (k: ReadinessKey | 'excluded') => soa.controls.filter((c) => tone(c) === k).length
  return (
    <Card span={7} title="Statement of applicability" sub={`${soa.systemName} · ${soa.controls.length} controls`}>
      {soa.controls.length === 0 ? (
        <Empty title="No controls" text="This system has no controls on file for the framework." />
      ) : (
        <>
          <Hero value={count('met')}>met · {count('progress')} partly · {count('attention')} need attention · {count('notstarted')} open · {count('excluded')} excluded</Hero>
          <div className="rp-mos">
            {[...groups.entries()].map(([g, cs]) => (
              <div className="g" key={g}>
                <span>{g}</span>
                <div className="sq">
                  {cs.map((c) => {
                    const t = tone(c)
                    const tip = `${c.control} ${c.title} · ${MOS_WORD[t]}${c.justification ? ` · ${c.justification}` : ''}`
                    return <i key={c.key} className={MOS[t]} title={tip} role="img" aria-label={tip} />
                  })}
                </div>
              </div>
            ))}
          </div>
          <Legend items={[['Met', 'm-met'], ['Partly met', 'm-part'], ['Needs attention', 'm-bad'], ['Open', 'm-open'], ['Excluded', 'm-exc']]} />
        </>
      )}
    </Card>
  )
}

export function SampleCard({ s }: { s: Auditor['sample'] }) {
  return (
    <Card span={5} title="Audit sample" sub="Drawn from the ledger with a fixed seed, so anyone can draw the same sample.">
      {s.items.length === 0 ? (
        <Empty title="Nothing to sample" text="There is nothing on the ledger to draw from yet." />
      ) : (
        <>
          <Hero value={s.size}>of {s.population} items · seed <span className="rp-mono">{shortHash(s.seed)}</span></Hero>
          <ul className="rp-list">
            {s.items.map((it) => (
              <li key={it.id}>
                <div>
                  <div className="t">{it.title}</div>
                  <div className="s"><span className="rp-mono">{shortHash(it.id)}</span> · {it.systemName} · {word(it.type)}</div>
                </div>
                <Pill tone="none">{word(it.provenance)}</Pill>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  )
}

export function PacksCard({ packs }: { packs: Auditor['packs'] }) {
  return (
    <Card span={5} title="Inspection packs" sub="Sealed bundles an outside auditor can open and verify.">
      {packs.length === 0 ? (
        <Empty title="No inspection packs" text="Prepare one and an auditor can verify it offline." />
      ) : (
        <ul className="rp-list">
          {packs.map((p) => (
            <li key={p.id}>
              <div>
                <div className="t">{p.title}</div>
                <div className="s"><span className="rp-mono" title={p.manifestHash}>{shortHash(p.manifestHash)}</span> · {p.items} items · {when(p.createdAt)}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
      <p className="rp-foot"><Link href="/auditor-packs">Open auditor packs</Link></p>
    </Card>
  )
}

const ZONES: Zone[] = [1, 2, 3, 4]

export function HeatCard({ risk }: { risk: RiskModel }) {
  const count = (l: number, i: number) => risk.heat.find((h) => h.chance === l && h.impact === i)?.count ?? 0
  const total = risk.heat.reduce((a, h) => a + h.count, 0)
  return (
    <Card span={7} title="Heat map" sub="How likely each risk is, and how bad it would be.">
      <Hero value={total}>{total === 1 ? 'risk' : 'risks'} on the register</Hero>
      <div className="rp-scroll">
        <table className="rp-heatmap">
          <thead>
            <tr>
              <th className="rl">Likelihood</th>
              {IMPACT.map((n, i) => <th key={n}>{i + 1} {n}</th>)}
            </tr>
          </thead>
          <tbody>
            {LIKELIHOOD.map((name, li) => (
              <tr key={name}>
                <td className="rl"><em>{li + 1}</em>{name}</td>
                {IMPACT.map((imp, ii) => {
                  const n = count(li + 1, ii + 1)
                  const z = heatZone(li + 1, ii + 1)
                  const tip = `${name}, ${imp.toLowerCase()} impact · ${ZONE_NAME[z]} · ${n} ${n === 1 ? 'risk' : 'risks'}`
                  return (
                    <td key={imp} className={`c z${z}`} title={tip} aria-label={tip}>
                      {n ? <b>{n}</b> : null}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Legend items={ZONES.map((z) => [ZONE_NAME[z], `z${z}`] as [string, string])} />
    </Card>
  )
}

export function AcceptanceCard({ list }: { list: RiskModel['acceptanceWaiting'] }) {
  return (
    <Card span={5} title="Waiting for acceptance" sub="A person must accept each residual risk.">
      {list.length === 0 ? (
        <Empty title="Nothing waiting" text="No residual risk is waiting for acceptance." />
      ) : (
        <ul className="rp-list">
          {list.map((r) => (
            <li key={r.id}>
              <div>
                <div className="t">{r.title}</div>
                <div className="s">{r.systemName} · owner {r.owner ?? 'unassigned'}{r.proposedBy ? ` · proposed by ${r.proposedBy}` : ''}</div>
              </div>
              <Pill tone="need">{dayWord(r.waitingDays)}</Pill>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export function RegisterCard({ risks }: { risks: RiskModel['risks'] }) {
  const rows = [...risks].sort((a, b) => b.chance * b.impact - a.chance * a.impact)
  return (
    <Card span={12} title="Risk register" sub={`${rows.length} ${rows.length === 1 ? 'risk' : 'risks'}, highest rating first`}>
      {rows.length === 0 ? (
        <Empty title="No risks recorded" text="Run a risk assessment on a system and its risks list here." />
      ) : (
        <div className="rp-scroll">
          <table className="rp-table">
            <thead>
              <tr><th>Risk</th><th>System</th><th>Rating</th><th>Likelihood</th><th>Owner</th><th>Status</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.title}</td>
                  <td className="rp-muted">{r.systemName}</td>
                  <td><ZonePill zone={heatZone(r.chance, r.impact)} /></td>
                  <td className="rp-muted">{r.likelihood}</td>
                  <td className="rp-muted">{r.owner ?? 'Unassigned'}</td>
                  <td className="rp-muted">{word(r.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

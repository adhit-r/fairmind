import { cellReadiness, sankey, type CellTone } from './geometry'
import type { Crosswalk, Grid, Tasks } from './types'
import { Card, Empty, Hero, Legend, Pill, SegBar } from './parts'

const SW = 700
const SH = 300

export function CrosswalkCard({ c }: { c: Crosswalk }) {
  const s = sankey(c.links, SH, 10)
  const L = 170
  const R = SW - 190
  const NW = 8
  const mid = (L + NW + R) / 2
  const followed = c.frameworks.find((f) => f.followed)
  return (
    <Card span={7} title="One proof, many frameworks" sub="Your proof, followed through the clause map. Grey is coverage you hold for frameworks you do not follow.">
      {c.frameworks.length === 0 || s.total === 0 ? (
        <Empty title="No links yet" text="Once evidence is mapped to clauses, the flow into each framework shows here." />
      ) : (
        <>
          {followed ? <Hero value={`${Math.round(followed.coverage)}%`}>of {followed.name} is covered by proof you hold · {s.total} links in all</Hero> : null}
          <div className="rp-scroll">
            <svg className="rp-svg rp-sankey" viewBox={`0 0 ${SW} ${SH}`} role="img" aria-label="Proof flowing into frameworks">
              {s.ribbons.map((r) => {
                const f = c.frameworks[r.target]
                return (
                  <path
                    key={`${r.source}-${r.target}`}
                    d={`M${L + NW} ${r.y0} C${mid} ${r.y0},${mid} ${r.y1},${R} ${r.y1} L${R} ${r.y1 + r.h} C${mid} ${r.y1 + r.h},${mid} ${r.y0 + r.h},${L + NW} ${r.y0 + r.h}Z`}
                    className={f?.followed ? 'rb-follow' : 'rb-other'}
                  >
                    <title>{`${c.sources[r.source]} to ${f?.name}: ${r.value} clauses`}</title>
                  </path>
                )
              })}
              {s.sources.map((n, i) => (
                <g key={c.sources[i]}>
                  <rect x={L} y={n.y} width={NW} height={n.h} rx={2} className="nd-src" />
                  <text x={L - 10} y={n.y + n.h / 2 + 4} textAnchor="end" className="lb">{c.sources[i]}</text>
                </g>
              ))}
              {s.targets.map((n, j) => {
                const f = c.frameworks[j]
                if (!f) return null
                return (
                  <g key={f.key}>
                    <rect x={R} y={n.y} width={NW} height={n.h} rx={2} className={f.followed ? 'nd-follow' : 'nd-other'} />
                    <text x={R + 16} y={n.y + n.h / 2 - 2} className="lb b">{f.name} · {Math.round(f.coverage)}%</text>
                    <text x={R + 16} y={n.y + n.h / 2 + 13}>{f.followed ? 'you follow' : 'not followed'}</text>
                  </g>
                )
              })}
            </svg>
          </div>
        </>
      )}
    </Card>
  )
}

export function TasksCard({ t }: { t: Tasks }) {
  const max = Math.max(1, ...t.byOwner.map((o) => o.onTime + o.overdue))
  return (
    <Card span={5} title="Who holds the open work" sub={`${t.open} open · ${t.overdue} overdue`}>
      {t.open === 0 ? (
        <Empty title="No open work" text="There are no open tasks." />
      ) : (
        <>
          {t.overdueList.length ? (
            <ul className="rp-list rp-gap">
              {t.overdueList.map((o, i) => (
                <li key={`${o.title}-${i}`}>
                  <div>
                    <div className="t">{o.title}</div>
                    <div className="s">{o.subject ? `${o.subject} · ` : ''}{o.owner}</div>
                  </div>
                  <Pill tone="fail">{o.daysLate} {o.daysLate === 1 ? 'day' : 'days'} late</Pill>
                </li>
              ))}
            </ul>
          ) : null}
          {t.byOwner.map((o) => (
            <div className="rp-rowbar rp-owner" key={o.owner}>
              <span className="n" title={o.owner}>{o.owner}</span>
              <div style={{ width: `${((o.onTime + o.overdue) / max) * 100}%` }}>
                <SegBar parts={[[o.onTime, 'f-m', 'On time'], [o.overdue, 'f-err', 'Overdue']]} />
              </div>
              <span className="p">{o.onTime + o.overdue}</span>
            </div>
          ))}
          <Legend items={[['On time', 'f-m'], ['Overdue', 'f-err']]} />
        </>
      )}
    </Card>
  )
}

const TONE_WORD: Record<CellTone, string> = { met: 'Met', progress: 'In progress', attention: 'Needs attention', notstarted: 'Not started' }

export function GridCard({ g }: { g: Grid }) {
  const groups: { name: string; rows: Grid['requirements'] }[] = []
  for (const r of g.requirements) {
    const name = r.group ?? 'Other'
    const last = groups[groups.length - 1]
    if (last && last.name === name) last.rows.push(r)
    else groups.push({ name, rows: [r] })
  }
  return (
    <Card span={12} title="Where systems fall short" sub="Each requirement against each system, from the proof on file.">
      {g.systems.length === 0 || g.requirements.length === 0 ? (
        <Empty title="Nothing to compare" text="Register a system and follow a framework to see requirements against systems." />
      ) : (
        <>
          <div className="rp-scroll rp-gridscroll">
            <table className="rp-heat">
              <thead>
                <tr>
                  <th className="rl" />
                  {g.systems.map((s) => <th key={s.id} title={s.name}>{s.name}</th>)}
                </tr>
              </thead>
              <tbody>
                {groups.map((grp) => [
                  <tr key={`g-${grp.name}`}><td className="grp" colSpan={g.systems.length + 1}>{grp.name}</td></tr>,
                  ...grp.rows.map((r) => (
                    <tr key={r.key}>
                      <td className="rl"><em>{r.control}</em>{r.title}</td>
                      {g.systems.map((s, i) => {
                        const state = r.cells[i] ?? 'open'
                        const tone = cellReadiness(state)
                        return <td key={s.id} className={`c t-${tone}`} title={`${r.control} on ${s.name}: ${TONE_WORD[tone]}`} aria-label={`${r.control} on ${s.name}: ${TONE_WORD[tone]}`} />
                      })}
                    </tr>
                  )),
                ])}
              </tbody>
            </table>
          </div>
          <Legend items={[['Met', 'f-ok'], ['In progress', 'f-cond'], ['Needs attention', 'f-err'], ['Not started', 'f-none']]} />
        </>
      )}
    </Card>
  )
}

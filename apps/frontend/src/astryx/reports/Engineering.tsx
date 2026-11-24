import { cellReadiness } from './geometry'
import type { Engineering, GateSystem } from './types'
import { Card, Empty, Hero, Pill, word } from './parts'

const verdict = (v: string | null): ['ok' | 'cond' | 'fail' | 'none', string] => {
  if (!v) return ['none', 'No verdict']
  if (/no_?go|block/i.test(v)) return ['fail', word(v)]
  if (/condition/i.test(v)) return ['cond', word(v)]
  if (/go|pass|approv/i.test(v)) return ['ok', word(v)]
  return ['none', word(v)]
}

export function GateCard({ systems, framework, outOfScope }: { systems: GateSystem[]; framework: string | null; outOfScope: number }) {
  const cols: { key: string; label: string }[] = []
  for (const s of systems) for (const c of s.checks) if (!cols.some((x) => x.key === c.key)) cols.push({ key: c.key, label: c.label ?? word(c.key) })
  const sub = framework
    ? `Systems in scope for ${framework}, against every check the release gate runs.${outOfScope ? ` ${outOfScope} registered ${outOfScope === 1 ? 'system is' : 'systems are'} outside its scope and not listed.` : ''}`
    : 'Every system against every check the release gate runs.'
  return (
    <Card span={8} title="Release gate checks" sub={sub}>
      {systems.length === 0 ? (
        <Empty title={framework ? 'No system in scope' : 'No systems yet'} text={framework ? `No registered system is in scope for ${framework}.` : 'Register a system to see its release gate checks.'} />
      ) : (
        <div className="rp-scroll">
          <table className="rp-heat">
            <thead>
              <tr>
                <th className="rl" />
                {cols.map((c) => <th key={c.key}>{c.label}</th>)}
                <th>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {systems.map((s) => {
                const [tone, text] = verdict(s.verdict)
                return (
                  <tr key={s.id}>
                    <td className="rl">{s.name}</td>
                    {cols.map((c) => {
                      const k = s.checks.find((x) => x.key === c.key)
                      if (!k) return <td key={c.key} className="c na" title="Not part of this system's gate" />
                      const t = k.fails || k.stale ? 'attention' : cellReadiness(k.state)
                      const say = k.fails ? 'Fails' : k.stale ? 'Out of date' : word(k.state)
                      return <td key={c.key} className={`c t-${t}`} title={`${c.label} on ${s.name}: ${say}`} aria-label={`${c.label} on ${s.name}: ${say}`} />
                    })}
                    <td className="c v"><Pill tone={tone}>{text}</Pill></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

export function ToolsCard({ tools }: { tools: Engineering['toolExposure'] }) {
  const bySystem = new Map<string, { name: string; tools: typeof tools }>()
  for (const t of tools) {
    const g = bySystem.get(t.systemId) ?? { name: t.systemName, tools: [] }
    g.tools.push(t)
    bySystem.set(t.systemId, g)
  }
  const ungated = tools.filter((t) => !t.gated).length
  return (
    <Card span={4} title="What agents can do" sub="Tools from the last agent audit, and whether a person approves each.">
      {tools.length === 0 ? (
        <Empty title="No agent audit on record" text="Run an agent audit and its tools show here." />
      ) : (
        <>
          <Hero value={ungated} tone={ungated ? 'dn' : undefined}>{ungated === 1 ? 'tool' : 'tools'} with no person in the loop</Hero>
          {[...bySystem.values()].map((g) => (
            <div className="rp-tools" key={g.name}>
              <h4>{g.name}</h4>
              {g.tools.map((t, i) => (
                <div key={`${t.tool}-${i}`} className={`rp-tool ${t.gated ? 'gated' : 'open'}`}>
                  <b>{t.tool}</b>
                  <span>{t.gated ? 'A person approves' : 'No person in the loop'}{t.effect ? ` · ${t.effect}` : ''}{t.agent ? ` · ${t.agent}` : ''}</span>
                </div>
              ))}
            </div>
          ))}
        </>
      )}
    </Card>
  )
}

const DW = 600
const DH = 170

export function DriftCard({ drift }: { drift: Engineering['fairnessDrift'] }) {
  const withPoints = drift.filter((d) => d.points.length > 0)
  return (
    <Card span={7} title="Fairness drift" sub="Each run of the fairness test, against the limit for that system.">
      {withPoints.length === 0 ? (
        <Empty title="No fairness runs yet" text="Run a fairness test and the trend shows here." />
      ) : (
        withPoints.map((d) => {
          const vals = d.points.map((p) => p.value)
          const all = d.threshold == null ? vals : [...vals, d.threshold]
          const lo = Math.min(...all)
          const hi = Math.max(...all)
          const pad = (hi - lo || 0.1) * 0.2
          const a = lo - pad
          const b = hi + pad
          const pl = 40
          const pr = 12
          const pt = 10
          const pb = 24
          const x = (i: number) => pl + ((DW - pl - pr) * (d.points.length === 1 ? 0.5 : i / (d.points.length - 1)))
          const y = (v: number) => pt + (DH - pt - pb) * (1 - (v - a) / (b - a))
          const line = d.points.map((p, i) => `${i ? 'L' : 'M'}${x(i)} ${y(p.value)}`).join(' ')
          const fmt = (v: number) => v.toFixed(2)
          return (
            <div key={d.systemId} className="rp-drift">
              <h4>{d.systemName}</h4>
              <svg className="rp-svg" viewBox={`0 0 ${DW} ${DH}`} role="img" aria-label={`Fairness over time for ${d.systemName}`}>
                {[a + pad, (a + b) / 2, b - pad].map((v) => (
                  <g key={v}>
                    <line x1={pl} x2={DW - pr} y1={y(v)} y2={y(v)} className="gridline" />
                    <text x={pl - 8} y={y(v) + 4} textAnchor="end">{fmt(v)}</text>
                  </g>
                ))}
                {d.threshold != null ? (
                  <g>
                    <line x1={pl} x2={DW - pr} y1={y(d.threshold)} y2={y(d.threshold)} className="limit" />
                    <text x={DW - pr} y={y(d.threshold) - 6} textAnchor="end" className="limit-t">Limit {fmt(d.threshold)}</text>
                  </g>
                ) : null}
                <path d={line} className="trend" />
                {d.points.map((p, i) => (
                  <circle key={p.at} cx={x(i)} cy={y(p.value)} r={i === d.points.length - 1 ? 4.5 : 3} className={d.threshold != null && p.value < d.threshold ? 'pt bad' : 'pt'}>
                    <title>{`${p.at.slice(0, 10)}: ${fmt(p.value)}`}</title>
                  </circle>
                ))}
                <text x={pl} y={DH - 6}>{d.points[0].at.slice(0, 10)}</text>
                {d.points.length > 1 ? <text x={DW - pr} y={DH - 6} textAnchor="end">{d.points[d.points.length - 1].at.slice(0, 10)}</text> : null}
              </svg>
            </div>
          )
        })
      )}
    </Card>
  )
}

export function FixesCard({ fixes }: { fixes: Engineering['fixes'] }) {
  return (
    <Card span={5} title="Fixes to make" sub="Failed evaluations and open remediation tasks. A passing rerun closes a failed evaluation.">
      {fixes.length === 0 ? (
        <Empty title="No fixes waiting" text="No failed evaluation and no open remediation task." />
      ) : (
        <ul className="rp-list">
          {fixes.map((f, i) => (
            <li key={`${f.title}-${i}`}>
              <div>
                <div className="t">{f.title}</div>
                <div className="s">
                  {f.systemName}
                  {f.kind === 'evaluation' ? <> · <span className="rp-mono">{f.evaluationId}</span> · Run it again once fixed</> : <> · {f.owner ?? 'Unassigned'} · {word(f.status)}</>}
                </div>
              </div>
              <Pill tone={/crit|high/i.test(f.priority) ? 'fail' : /med/i.test(f.priority) ? 'cond' : 'none'}>{word(f.priority)}</Pill>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

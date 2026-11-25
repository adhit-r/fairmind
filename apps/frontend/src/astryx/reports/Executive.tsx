import Link from 'next/link'
import type { Decision, Governed, Oversight, ReportModel, Road, RiskModel } from './types'
import { axisPct, heatZone, waterfall } from './geometry'
import { Card, Empty, Hero, Legend, Pill, ZonePill, dayWord, num, word } from './parts'

const ATTESTED = /attest|manual|person/i
// discovered asset kinds (governance_discovered_assets.kind) in the words the Discovery page uses
const KIND_LABEL: Record<string, string> = { ml_model: 'Model', llm_app: 'LLM app', agent: 'Agent', ai_service: 'AI service', ai_assisted_dev: 'AI coding tool' }

export function RoadCard({ road, span }: { road: Road; span: 8 | 12 }) {
  const w = waterfall(road.start, road.steps.map((s) => s.gain), road.forecast)
  const X = (v: number) => `${axisPct(v, w.lo, w.hi)}%`
  const grid = w.ticks.slice(1, -1).map((v) => <i key={v} className="gl" style={{ left: X(v) }} />)
  return (
    <Card span={span} title="Road to the audit" sub="Each step is the readiness it adds, taken in order. The forecast is what you reach if every step is done.">
      <Hero value={`${road.forecast}%`}>
        forecast if every step is done · {road.start}% today
      </Hero>
      {road.steps.length === 0 ? (
        <p className="rp-muted">No open steps. Nothing on the record would raise readiness further.</p>
      ) : (
        <div className="rp-br">
          <div className="lab first"><span className="t">Today</span><span className="s">Requirements met now</span></div>
          <div className="trk first">{grid}<i className="pin" style={{ left: X(road.start) }} /></div>
          <div className="val first">{road.start}%</div>
          {road.steps.map((s, i) => {
            const r = w.rows[i]
            const left = Math.min(r.from, r.to)
            const att = ATTESTED.test(s.evidenceClass ?? '')
            const name = s.action ?? s.check ?? 'Step'
            const closes = s.closes.length
            return (
              <div className="row" key={`${s.systemId}-${i}`}>
                <div className="lab">
                  <span className="t" title={name}>{name}</span>
                  <span className="s">
                    {s.systemName} · {s.owner ?? 'Unassigned'}
                    {closes ? ` · closes ${closes} ${closes === 1 ? 'requirement' : 'requirements'}` : ''}
                  </span>
                </div>
                <div className="trk">
                  {grid}
                  <i className="conn" style={{ left: X(r.from) }} />
                  <i
                    className={`bar ${att ? 'k-a' : 'k-m'}`}
                    style={{ left: X(left), width: `${axisPct(w.lo + Math.abs(r.gain), w.lo, w.hi)}%`, animationDelay: `${i * 70}ms` }}
                    title={`${name} · ${s.systemName} · ${att ? 'A person attests this' : 'FairMind measures this'} · ${r.gain > 0 ? '+' : ''}${r.gain} points`}
                  />
                </div>
                <div className={`val ${r.gain > 0 ? 'rp-up' : r.gain < 0 ? 'rp-dn' : ''}`}>{r.gain > 0 ? `+${r.gain}` : r.gain}</div>
              </div>
            )
          })}
          <div className="lab"><span className="t">Forecast</span><span className="s">If every step is done</span></div>
          <div className="trk">{grid}<i className="conn" style={{ left: X(road.forecast) }} /><i className="pin fc" style={{ left: X(road.forecast) }} /></div>
          <div className="val">{road.forecast}%</div>
          <div className="sp" />
          <div className="axis" aria-hidden="true">
            {w.ticks.map((v) => <span key={v} style={{ left: X(v) }}>{v}%</span>)}
          </div>
          <div className="sp" />
        </div>
      )}
      <Legend items={[['Gain FairMind measures', 'k-m'], ['Gain a person attests', 'k-a']]} />
    </Card>
  )
}

export function GovernedCard({ g }: { g: Governed }) {
  const steps: [string, number][] = [['Found', g.found], ['Registered', g.registered], ['Checked', g.checked], ['Approved', g.approved]]
  const pct = g.found ? Math.round((g.approved / g.found) * 100) : null
  const more = g.unregisteredCount - g.unregistered.length
  return (
    <Card span={4} title="Governed AI" sub="AI found in your estate, and how far each has come.">
      {g.found === 0 ? (
        <Empty title="Nothing found yet" text="Connect a source in Discovery and the agent will list what it finds." />
      ) : (
        <>
          <Hero value={`${pct}%`}>approved · {g.unregisteredCount} not registered</Hero>
          <div className="rp-fun">
            {steps.map(([name, n]) => (
              <div key={name}>
                <span>{name}</span>
                <u className="rp-grow" style={{ width: `${(n / g.found) * 100}%`, opacity: 0.35 + (n / g.found) * 0.65 }} title={`${name}: ${n} of ${g.found}`} />
                <b>{n}</b>
              </div>
            ))}
          </div>
          {g.unregistered.length ? (
            <>
              <div className="rp-unreg">
                {g.unregistered.map((u, i) => (
                  <span key={`${u.name}-${i}`}>{u.name} <em>{KIND_LABEL[u.kind] ?? word(u.kind)} · {word(u.source)}</em></span>
                ))}
                {more > 0 ? <span>and {more} more</span> : null}
              </div>
              <p className="rp-foot"><Link href="/discovery">Register them in Discovery</Link></p>
            </>
          ) : null}
        </>
      )}
    </Card>
  )
}

const DAY_W = 600
const DAY_H = 150

export function OversightCard({ o }: { o: Oversight }) {
  const n = o.days.length
  const bw = n ? DAY_W / n : DAY_W
  const max = Math.max(1, ...o.days.map((d) => d.agentSteps))
  const top = 34
  const base = DAY_H - 20
  return (
    <Card span={6} title="Agents work, people decide" sub="Every step on the ledger in the last 30 days.">
      <svg className="rp-svg" viewBox={`0 0 ${DAY_W} ${DAY_H}`} role="img" aria-label="Agent steps and decisions by people, per day">
        {o.days.map((d, i) => {
          const x = i * bw
          const h = ((base - top) * d.agentSteps) / max
          return (
            <g key={d.date}>
              <title>{`${d.date}: ${d.agentSteps} agent steps, ${d.decisions} decisions by people`}</title>
              <rect x={x + 1.5} y={base - h} width={Math.max(bw - 3, 1)} height={h} rx={2} className="s-agent" />
              {Array.from({ length: Math.min(d.decisions, 4) }, (_, k) => (
                <path key={k} d={`M${x + bw / 2} ${top - 8 - k * 8} l4 4 l-4 4 l-4 -4z`} className="s-dec" />
              ))}
              {i % 7 === 0 ? <text x={x + bw / 2} y={DAY_H - 4} textAnchor="middle">{d.date.slice(5)}</text> : null}
            </g>
          )
        })}
      </svg>
      <div className="rp-legend">
        <span><i className="rp-sw f-a" />Agent step</span>
        <span><i className="rp-sw rp-diamond" />Decision by a person</span>
      </div>
      <div className="rp-stats">
        <div><b>{num(o.agentSteps)}</b><span>agent steps</span></div>
        <div><b>{num(o.decisions)}</b><span>decisions by people</span></div>
        <div><b>{o.medianWaitHours === null ? 'No decisions yet' : `${Math.round(o.medianWaitHours)} h`}</b><span>median wait at a gate</span></div>
        <div><b>{num(o.approvedWithoutPerson)}</b><span>approved without a person</span></div>
      </div>
    </Card>
  )
}

export function DecisionsCard({ list }: { list: Decision[] }) {
  return (
    <Card span={4} title="Waiting for a decision" sub="Releases that need a person to approve or decline.">
      {list.length === 0 ? (
        <Empty title="Nothing is waiting" text="No release is waiting for a person right now." />
      ) : (
        <ul className="rp-list">
          {list.map((d) => (
            <li key={d.id}>
              <div>
                <div className="t">{d.systemName}</div>
                <div className="s">Requested by {d.requestedBy ?? 'the agent'}</div>
              </div>
              <Pill tone="need">{dayWord(d.waitingDays)}</Pill>
            </li>
          ))}
        </ul>
      )}
      <p className="rp-foot"><Link href="/decisions">Open decisions</Link></p>
    </Card>
  )
}

export function TopRisksCard({ risk }: { risk: RiskModel }) {
  const open = risk.risks
    .filter((r) => r.status === 'open' || r.status === 'acceptance_pending')
    .sort((a, b) => b.chance * b.impact - a.chance * a.impact)
    .slice(0, 4)
  return (
    <Card span={12} title="Highest open risks" sub="The four open risks with the highest rating.">
      {open.length === 0 ? (
        <Empty title="No open risks" text="Every risk on the register is treated or closed." />
      ) : (
        <ul className="rp-list">
          {open.map((r) => (
            <li key={r.id}>
              <div>
                <div className="t">{r.title}</div>
                <div className="s">{r.systemName} · {r.owner ?? 'Unassigned'} · {r.status === 'open' ? 'Open' : 'Waiting for acceptance'}</div>
              </div>
              <ZonePill zone={heatZone(r.chance, r.impact)} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export type ExecModel = Pick<ReportModel, 'road' | 'governed' | 'proof' | 'oversight' | 'decisions' | 'risk'>

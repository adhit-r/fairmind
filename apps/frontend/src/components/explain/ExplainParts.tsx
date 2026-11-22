'use client'

import type { ReactNode } from 'react'
import type { DecisionSummary, EngineRun, ExplainEdit, TraceExplanation } from '@/lib/api/hooks/usePacks'

/** Explained decisions (EV-OVS-04 on live runs): result charts, one run's explanation, and the system file's Decisions card. */

const OK = '#1f7a4d'
const BAD = '#b4232c'
const INK = 'var(--fm-ink)'
const GREY = '#c9cbc8'
const MUTED = 'text-[var(--fm-ink2)]'
const CAP = 'text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]'
const CARD = 'flex min-w-0 flex-col gap-2 rounded-[12px] border border-[var(--fm-line)] bg-white px-3.5 py-3'

export const VERDICT: Record<TraceExplanation['verdict'], { label: string; tone: string; color: string }> = {
  held: { label: 'Reason held', tone: 'bg-[#e3f2ea] text-[#1f7a4d]', color: OK },
  'did not hold': { label: 'Reason did not hold', tone: 'bg-[#fde9ea] text-[#b4232c]', color: BAD },
  untested: { label: 'Reason not testable', tone: 'bg-[#ececea] text-[var(--fm-ink2)]', color: GREY },
  'not reproducible': { label: 'Not reproducible', tone: 'bg-[#ececea] text-[var(--fm-ink2)]', color: 'var(--fm-ink3)' },
  error: { label: 'Failed', tone: 'bg-[#ececea] text-[var(--fm-ink2)]', color: GREY },
}

export function Verdict({ v }: { v: TraceExplanation['verdict'] }) {
  const t = VERDICT[v] ?? VERDICT.error
  return <span className={`inline-flex items-center whitespace-nowrap rounded-md px-2 py-0.5 text-[12px] font-medium ${t.tone}`}>{t.label}</span>
}

const num = (v: unknown) => (typeof v === 'number' ? v : null)
const fixed = (v: number | null, d = 2) => (v === null ? '-' : v.toFixed(d))

function Bar({ value, color = INK, height = 6 }: { value: number; color?: string; height?: number }) {
  return (
    <div className="overflow-hidden rounded-full bg-[#ececea]" style={{ height }}>
      <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%`, background: color }} />
    </div>
  )
}

function Tile({ cap, value, note, children }: { cap: string; value: ReactNode; note?: ReactNode; children?: ReactNode }) {
  return (
    <div className={CARD}>
      <span className={CAP}>{cap}</span>
      <div className="flex flex-wrap items-baseline gap-2">
        <b className="text-[22px] font-semibold tracking-tight tabular-nums text-[var(--fm-ink)]">{value}</b>
        {note && <span className={`text-[12px] tabular-nums ${MUTED}`}>{note}</span>}
      </div>
      {children}
    </div>
  )
}

/** A share against its agreed floor, with a bar in pass or fail colour. */
function Scored({ cap, rate, part, whole, floor }: { cap: string; rate: number | null; part: number; whole: number; floor: number | null }) {
  const pass = rate !== null && floor !== null ? rate >= floor : null
  return (
    <Tile cap={cap} value={fixed(rate)} note={`${part} / ${whole}${floor !== null ? ` · agreed ${floor}` : ''}`}>
      <Bar value={rate ?? 0} color={pass === false ? BAD : pass ? OK : INK} />
    </Tile>
  )
}

function Chart({ title, children, foot }: { title: string; children: ReactNode; foot?: ReactNode }) {
  return (
    <div className={CARD}>
      <span className={CAP}>{title}</span>
      {children}
      {foot}
    </div>
  )
}

function Legend({ items }: { items: Array<[string, string]> }) {
  return (
    <div className={`flex flex-wrap gap-3 text-[11.5px] ${MUTED}`}>
      {items.map(([color, text]) => (
        <span key={text} className="inline-flex items-center gap-1.5"><i className="inline-block size-2.5 rounded-[2px]" style={{ background: color }} />{text}</span>
      ))}
    </div>
  )
}

function HBars({ rows, max = 1, fmt = (v: number) => v.toFixed(2) }: { rows: Array<{ label: string; parts: Array<[number, string]> }>; max?: number; fmt?: (v: number) => string }) {
  if (!rows.length) return <p className={`m-0 text-[12.5px] ${MUTED}`}>Nothing to show yet.</p>
  return (
    <div className="flex flex-col gap-1.5">
      {rows.map((r) => {
        const total = r.parts.reduce((a, [v]) => a + v, 0)
        return (
          <div key={r.label} className="grid grid-cols-[minmax(0,120px)_minmax(0,1fr)_40px] items-center gap-2.5 text-[12.5px]">
            <span className="truncate" title={r.label}>{r.label}</span>
            <div className="flex h-3 overflow-hidden rounded-[3px] bg-[#ececea]">
              {r.parts.map(([v, color], i) => <div key={i} style={{ width: `${(v / max) * 100}%`, background: color }} />)}
            </div>
            <span className="text-right tabular-nums">{fmt(total)}</span>
          </div>
        )
      })}
    </div>
  )
}

type Detail = TraceExplanation & Record<string, unknown>

/** The result of an Explanation quality run on live runs: tiles, four charts and the runs tested. */
export function ExplanationResult({ run, onTrace }: { run: EngineRun; onTrace: (traceId: string, flag?: string) => void }) {
  const m = run.metrics as Record<string, unknown>
  const drivers = (m.drivers as Array<{ factor: string; mean: number }>) ?? []
  const matrix = (m.reasonVsDriver as Array<{ reason: string; driver: string; runs: number }>) ?? []
  const points = (m.comprehensiveness as Array<{ traceId: string; named: number; other: number }>) ?? []
  const flipsBy = (m.flipsBy as Array<{ factor: string; from: string; to: string; runs: number }>) ?? []
  const rows = (run.detail ?? []) as Detail[]
  const reproducible = num(m.reproducible) ?? 0

  const directions = [...new Set(flipsBy.map((f) => `${f.from} → ${f.to}`))]
  const dirColor = (d: string) => [OK, BAD, 'var(--fm-ink3)', GREY][directions.indexOf(d)] ?? GREY
  const flipRows = [...new Set(flipsBy.map((f) => f.factor))].map((factor) => ({
    label: factor,
    parts: flipsBy.filter((f) => f.factor === factor).map((f) => [f.runs, dirColor(`${f.from} → ${f.to}`)] as [number, string]),
  }))
  const flipMax = Math.max(1, ...flipRows.map((r) => r.parts.reduce((a, [v]) => a + v, 0)))

  const reasons = [...new Set(matrix.map((c) => c.reason))]
  const causes = [...new Set(matrix.map((c) => c.driver))]
  const cellMax = Math.max(1, ...matrix.map((c) => c.runs))

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
        <Tile cap="Not reproducible" value={num(m.notReproducible) ?? 0} note={`of ${num(m.runs) ?? 0} runs, set aside`} />
        <Scored cap="Reason held" rate={num(m.reasonHeldRate)} part={num(m.reasonHeld) ?? 0} whole={num(m.reasonTested) ?? 0} floor={num(m.minReasonHeld)} />
        <Scored cap="Drivers faithful" rate={num(m.faithfulness)} part={num(m.faithful) ?? 0} whole={num(m.faithTested) ?? 0} floor={num(m.minFaithfulness)} />
        <Tile cap="Flip found" value={num(m.flipsFound) ?? 0} note={`of ${reproducible}`}>
          <Bar value={reproducible ? (num(m.flipsFound) ?? 0) / reproducible : 0} />
        </Tile>
      </div>
      <div className="grid grid-cols-1 gap-2.5 lg:grid-cols-2">
        <Chart title="What drives decisions" foot={<span className={`text-[12px] ${MUTED}`}>How often hiding the fact changed the decision, across runs</span>}>
          <HBars rows={drivers.map((d) => ({ label: d.factor, parts: [[d.mean, INK]] }))} />
        </Chart>
        <Chart title="Stated reason against what drove it" foot={<Legend items={[[OK, 'Reason named the driver'], [BAD, 'Reason named something else']]} />}>
          {matrix.length === 0 ? <p className={`m-0 text-[12.5px] ${MUTED}`}>Nothing to show yet.</p> : (
            <div className="overflow-x-auto">
              <table className="border-separate border-spacing-1 text-[11.5px]">
                <thead><tr><th className={`text-left font-normal ${MUTED}`}>reason ↓ driver →</th>{causes.map((c) => <th key={c} className={`px-1 font-normal ${MUTED}`}>{c}</th>)}</tr></thead>
                <tbody>
                  {reasons.map((r) => (
                    <tr key={r}>
                      <td className={`pr-2 ${MUTED}`}>{r}</td>
                      {causes.map((c) => {
                        const n = matrix.find((x) => x.reason === r && x.driver === c)?.runs ?? 0
                        return (
                          <td key={c} className="h-7 min-w-[44px] rounded-[4px] text-center font-semibold text-white tabular-nums"
                            style={{ background: n ? (r === c ? OK : BAD) : 'var(--fm-bg)', opacity: n ? 0.35 + (0.65 * n) / cellMax : 1 }}>{n || ''}</td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Chart>
        <Chart title="Hiding named facts against hiding the others, per run" foot={<Legend items={[[INK, 'Faithful: named facts moved it more'], [BAD, 'Not faithful']]} />}>
          <svg viewBox="0 0 300 150" className="block h-auto w-full" role="img" aria-label="Per run: decision change when the named facts were hidden, against the others">
            <line x1="30" y1="130" x2="290" y2="130" stroke={GREY} />
            <line x1="30" y1="130" x2="30" y2="6" stroke={GREY} />
            <line x1="30" y1="130" x2="290" y2="6" stroke="var(--fm-ink3)" strokeDasharray="3 3" />
            <text x="290" y="146" textAnchor="end" fontSize="10.5" fill="var(--fm-ink2)">hiding named facts →</text>
            <text x="34" y="14" fontSize="10.5" fill="var(--fm-ink2)">↑ hiding the others</text>
            {points.map((p, i) => (
              <circle key={p.traceId + i} cx={30 + p.named * 260} cy={130 - p.other * 124} r="4.5" fill={p.named > p.other ? INK : BAD} opacity="0.85">
                <title>{`${p.traceId}: ${p.named.toFixed(2)} against ${p.other.toFixed(2)}`}</title>
              </circle>
            ))}
          </svg>
        </Chart>
        <Chart title="What flips decisions" foot={<Legend items={directions.map((d) => [dirColor(d), d])} />}>
          <HBars rows={flipRows} max={flipMax} fmt={(v) => String(v)} />
        </Chart>
      </div>
      <div className={CARD}>
        <span className={CAP}>Runs tested</span>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-[12.5px]">
            <thead>
              <tr className={MUTED}>{['Run', 'Decision', 'Stated reason', 'Result', 'Top driver', 'Flips if'].map((h) => <th key={h} className="whitespace-nowrap py-1.5 pr-3 font-semibold">{h}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.traceId} className="border-t border-[#15171a14] align-middle">
                  <td className="py-1.5 pr-3">
                    <button type="button" className="font-mono font-semibold underline" onClick={() => onTrace(r.traceId, r.verdict === 'did not hold' ? `The stated reason did not hold: changing ${r.reasonCheck?.factor ?? 'what it named'} did not change the decision` : undefined)}>{r.traceId}</button>
                  </td>
                  <td className="py-1.5 pr-3">{r.decision}</td>
                  <td className={`max-w-[260px] py-1.5 pr-3 ${MUTED}`}>{r.reason}</td>
                  <td className="py-1.5 pr-3"><Verdict v={r.verdict} /></td>
                  <td className="py-1.5 pr-3">{r.topDriver ?? '-'}</td>
                  <td className="py-1.5 pr-3">{r.flip ? `${r.flip.factor} → ${r.flip.to}` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

/** One dot per replay: green where the decision changed, `miss` where it did not. */
function Replays({ edit, miss }: { edit: ExplainEdit; miss: string }) {
  return (
    <span className="inline-flex gap-[3px]" aria-label={`${edit.changed} of ${edit.of} replays changed the decision`}>
      {Array.from({ length: edit.of }, (_, i) => (
        <i key={i} className="block size-2.5 rounded-full" style={{ background: i < edit.changed ? OK : miss }} />
      ))}
    </span>
  )
}

function EditRow({ edit, after }: { edit: ExplainEdit; after: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
      <span>{edit.factor} <span className="text-[#b4232c] line-through">{edit.from}</span> <span className="font-medium text-[#1f7a4d]">{edit.to}</span></span>
      <span className="text-[var(--fm-ink3)]">→</span>
      {after}
    </div>
  )
}

/** One run's explanation, under its decision step. */
export function RunExplanation({ e }: { e: TraceExplanation }) {
  if (e.verdict === 'not reproducible') {
    return (
      <div className="flex flex-col gap-1.5 border-l-2 border-[var(--fm-ink3)] pl-3">
        <span className="text-[12.5px]">Recorded <b>{e.decision}</b> <span className="text-[var(--fm-ink3)]">≠</span> replayed: {e.baseline?.same ?? 0} of {e.baseline?.of ?? 0} the same</span>
        <span className={`text-[12px] ${MUTED}`}>The model connection does not give this decision, so nothing about it was tested.</span>
      </div>
    )
  }
  const drivers = e.drivers ?? []
  return (
    <div className="flex flex-col gap-3 border-l-2 border-[var(--fm-ink)] pl-3">
      {drivers.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className={CAP}>Drivers{e.faithful === true ? ', faithful' : e.faithful === false ? ', not faithful' : ''}</span>
          <HBars rows={drivers.map((d) => ({ label: d.factor, parts: [[d.score, e.named?.includes(d.factor) ? INK : 'var(--fm-ink3)']] }))} />
        </div>
      )}
      {e.reasonCheck && (
        <div className="flex flex-col gap-1">
          <span className={CAP}>Reason check</span>
          <EditRow edit={e.reasonCheck} after={<><Replays edit={e.reasonCheck} miss={BAD} /><span>{e.reasonCheck.changed > e.reasonCheck.of / 2 ? 'changed' : `still ${e.decision}`} {e.reasonCheck.changed} / {e.reasonCheck.of}</span></>} />
        </div>
      )}
      {e.flip && (
        <div className="flex flex-col gap-1">
          <span className={CAP}>Flips if</span>
          <EditRow edit={e.flip} after={<><Replays edit={e.flip} miss={GREY} /><span><b className="text-[#1f7a4d]">{e.flip.decision}</b> {e.flip.changed} / {e.flip.of}</span></>} />
        </div>
      )}
      <span className="text-[11.5px] text-[var(--fm-ink3)]">{e.replays ?? 0} replays on the model connection · no tools called</span>
    </div>
  )
}

/** The run's input with each fact shaded by how much hiding it changed the decision. */
export function ShadedInput({ text, drivers }: { text: string; drivers: TraceExplanation['drivers'] }) {
  const facts = (drivers ?? []).filter((d) => d.value && text.includes(d.value)).sort((a, b) => b.value.length - a.value.length)
  if (!facts.length) return <>{text}</>
  const pattern = new RegExp(`(${facts.map((d) => d.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`)
  return (
    <>
      {text.split(pattern).map((part, i) => {
        const d = facts.find((f) => f.value === part)
        if (!d) return <span key={i}>{part}</span>
        const a = 0.06 + d.score * 0.7
        return <span key={i} title={`${d.factor}: ${d.score.toFixed(2)}`} className="rounded px-1" style={{ background: `rgba(21,23,26,${a})`, color: a > 0.45 ? '#fff' : undefined }}>{part}</span>
      })}
    </>
  )
}

/** Decisions per day by outcome, with the share of tested runs whose stated reason held. */
export function DecisionsCard({ d, latest, onOpen }: { d: DecisionSummary; latest?: Record<string, unknown>; onOpen: () => void }) {
  const tested = d.explained.held + d.explained.notHeld
  const heldRate = tested ? d.explained.held / tested : null
  const floor = num(latest?.minReasonHeld)
  const faith = num(latest?.faithfulness)
  const faithFloor = num(latest?.minFaithfulness)
  const max = Math.max(1, ...d.days.map((x) => x.total))
  const colors = [INK, GREY]
  const W = 560, H = 100, bw = W / d.days.length
  const line = d.days.map((x, i) => (x.tested ? `${i * bw + bw / 2},${H - (x.held / x.tested) * H}` : null)).filter(Boolean).join(' ')
  const shift = d.topShare !== null && d.priorTopShare !== null ? Math.round((d.topShare - d.priorTopShare) * 100) : null
  const pill = (pass: boolean | null, text: string) => pass === null ? null : (
    <span className={`rounded-md px-2 py-0.5 text-[12px] font-medium ${pass ? 'bg-[#e3f2ea] text-[#1f7a4d]' : 'bg-[#fde9ea] text-[#b4232c]'}`}>{text}</span>
  )
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
        <Tile cap="Decisions" value={d.total.toLocaleString()} note={`${d.withReason.toLocaleString()} with a stated reason`} />
        <Tile cap="Reason held" value={heldRate === null ? '-' : `${Math.round(heldRate * 100)}%`} note={tested ? `${d.explained.held} of ${tested} tested` : 'not tested yet'}>
          {heldRate !== null && floor !== null && pill(heldRate >= floor, `${heldRate >= floor ? 'at or above' : 'below'} ${Math.round(floor * 100)}%`)}
        </Tile>
        <Tile cap="Drivers faithful" value={fixed(faith)} note={faith === null ? 'not tested yet' : undefined}>
          {faith !== null && faithFloor !== null && pill(faith >= faithFloor, `${faith >= faithFloor ? 'at or above' : 'below'} ${faithFloor}`)}
        </Tile>
        <Tile cap={d.topLabel ? `Share ${d.topLabel}` : 'Outcomes'} value={d.topShare === null ? '-' : `${Math.round(d.topShare * 100)}%`}
          note={shift === null ? undefined : `${shift > 0 ? '+' : ''}${shift} pts vs prior ${d.days.length} days`} />
      </div>
      <div className={CARD}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className={CAP}>Decisions per day, and the share whose reason held</span>
          <Legend items={[...d.labels.map((l, i) => [colors[i], l] as [string, string]), ['#e4e5e2', 'other'], [BAD, 'reason held']]} />
        </div>
        <svg viewBox={`0 0 ${W} ${H + 20}`} className="block h-auto w-full" role="img" aria-label="Decisions per day by outcome">
          {d.days.map((x, i) => {
            let y = H
            const parts: Array<[number, string]> = [...d.labels.map((l, j) => [x.byLabel[l] ?? 0, colors[j]] as [number, string]), [x.byLabel.other ?? 0, '#e4e5e2']]
            return (
              <g key={x.date}>
                {parts.map(([n, c], j) => {
                  const h = (n / max) * H
                  y -= h
                  return n ? <rect key={j} x={i * bw + 4} y={y} width={bw - 8} height={h} rx="2" fill={c} /> : null
                })}
                {i % 2 === 0 && <text x={i * bw + bw / 2} y={H + 15} textAnchor="middle" fontSize="10.5" fill="var(--fm-ink2)">{x.date.slice(5)}</text>}
              </g>
            )
          })}
          {floor !== null && <line x1="0" x2={W} y1={H - floor * H} y2={H - floor * H} stroke={BAD} strokeDasharray="3 3" opacity="0.6" />}
          {line && <polyline points={line} fill="none" stroke={BAD} strokeWidth="2" />}
        </svg>
      </div>
      <div><button type="button" onClick={onOpen} className="rounded-full border border-[var(--fm-line)] bg-white px-3 py-1.5 text-[12.5px] font-semibold text-[var(--fm-ink)]">Open Explanation quality</button></div>
    </div>
  )
}

/** Held, did not hold and not reproducible as one bar, for the gate's human oversight row. */
export function ReasonStack({ held, notHeld, notReproducible, floor }: { held: number; notHeld: number; notReproducible: number; floor: number | null }) {
  const total = held + notHeld + notReproducible
  if (!total) return null
  return (
    <div className="flex flex-col gap-1.5 rounded-[10px] bg-[var(--fm-bg)] px-3 py-2.5">
      <div className="flex flex-wrap items-center gap-3">
        <Legend items={[[OK, `Reason held ${held}`], [BAD, `Did not hold ${notHeld}`], ['var(--fm-ink3)', `Not reproducible ${notReproducible}`]]} />
        {floor !== null && <span className={`ml-auto text-[11.5px] tabular-nums ${MUTED}`}>agreed {floor}</span>}
      </div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-[#ececea]">
        {([[held, OK], [notHeld, BAD], [notReproducible, 'var(--fm-ink3)']] as const).map(([n, c], i) => <div key={i} style={{ width: `${(n / total) * 100}%`, background: c }} />)}
      </div>
    </div>
  )
}

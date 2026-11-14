'use client'

import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Text } from '@astryxdesign/core/Text'
import { HStack } from '@astryxdesign/core/Layout'
import { SourceMark, detail, where } from '@/astryx/DiscoveryParts'
import {
  HEALTH_LABEL,
  KIND_LABEL,
  SOURCES,
  ago,
  healthOf,
  until,
  useDiscovery,
  type DiscoveredAsset,
  type Integration,
  type IntegrationStep,
  type RunStep,
} from '@/astryx/data/discovery'

type D = ReturnType<typeof useDiscovery>
type Sel = { type: 'source' | 'step' | 'rules' | 'inventory'; id: string }

// Canvas geometry, in px at 100%.
const PAD = 44
const SX = 24, SW = 240, SH = 116
const RX = 330, RW = 300, RH = 158, GAP = 16
const UX = 720, UW = 230, UH = 172
const IX = 1010, IW = 380, INSP_H = 330, INV_H = 470
const WIDTH = IX + IW + 24

type StepNode = { i: Integration; def: IntegrationStep; run?: RunStep; y: number; on: boolean; failing: boolean }

function curve(x1: number, y1: number, x2: number, y2: number) {
  const mx = (x1 + x2) / 2
  return `M${x1} ${y1} C${mx} ${y1},${mx} ${y2},${x2} ${y2}`
}

/** The last read that worked: a failing source still shows what it last found. */
const lastGood = (i: Integration) => i.recentRuns?.find((r) => r.status === 'ok')

export function DiscoveryFlow({ d, onReview }: { d: D; onReview: () => void }) {
  const [sel, setSel] = useState<Sel>(() => ({ type: 'source', id: d.integrations[0]?.id ?? '' }))
  // Steps turned off on screen but not saved yet, per source.
  const [draft, setDraft] = useState<Record<string, string[]>>({})
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const scroller = useRef<HTMLDivElement>(null)
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null)

  // Start zoomed so the whole width fits: sources on the left, inventory on the right.
  useEffect(() => {
    const w = scroller.current?.clientWidth
    if (w) setZoom(Math.max(0.6, Math.min(1, Math.floor(((w - 8) / WIDTH) * 20) / 20)))
  }, [])

  const assets = useMemo(() => {
    const m = new Map<string, DiscoveredAsset>()
    for (const a of d.discovered) m.set(`${a.integrationId}|${a.externalId}`, a)
    return m
  }, [d.discovered])

  const offFor = (i: Integration) => draft[i.id] ?? (i.steps ?? []).filter((s) => !s.on).map((s) => s.key)

  // Layout: each source's steps stacked; the source centred on them; rules and inventory to the right.
  let y = PAD
  const stepNodes: StepNode[] = []
  const sourceY = new Map<string, number>()
  for (const i of d.integrations) {
    const defs = i.steps ?? []
    const run = lastGood(i)
    const failing = healthOf(i) === 'failing'
    const top = y
    for (const def of defs) {
      stepNodes.push({ i, def, run: run?.steps?.find((s) => s.key === def.key), y, on: !offFor(i).includes(def.key), failing })
      y += RH + GAP
    }
    const block = Math.max(defs.length, 1) * (RH + GAP) - GAP
    sourceY.set(i.id, top + block / 2 - SH / 2)
    if (!defs.length) y += SH + GAP
  }
  const stepsBottom = y
  const ruleY = Math.max(PAD, (PAD + stepsBottom) / 2 - UH / 2)
  const invY = Math.max(PAD + INSP_H + 24, ruleY + UH / 2 - 230)
  const height = Math.max(stepsBottom, invY + INV_H) + PAD

  const maxFound = Math.max(1, ...stepNodes.map((s) => s.run?.found ?? 0))
  const live = (n: StepNode) => n.on && !n.failing && (n.run?.found ?? 0) > 0
  const flowing = stepNodes.filter(live).reduce((t, n) => t + (n.run?.found ?? 0), 0)

  const shown = d.discovered.filter((a) => a.status !== 'ignored')
  const tiers = ['critical', 'high', 'medium', 'low'].map((t) => ({ t, n: shown.filter((a) => a.suggestedTier === t).length }))
  const count = (s: string) => d.discovered.filter((a) => a.status === s).length
  const [reg, wait, ign] = [count('promoted'), count('new'), count('ignored')]
  const byKind = Object.entries(
    d.discovered.reduce<Record<string, number>>((m, a) => ({ ...m, [a.kind]: (m[a.kind] ?? 0) + 1 }), {}),
  ).sort((a, b) => b[1] - a[1])
  const today = d.discovered
    .filter((a) => Date.now() - new Date(a.discoveredAt).getTime() < 86_400_000)
    .sort((a, b) => b.discoveredAt.localeCompare(a.discoveredAt))
    .slice(0, 4)

  const changed = d.integrations.filter((i) => draft[i.id] && [...draft[i.id]].sort().join() !== (i.steps ?? []).filter((s) => !s.on).map((s) => s.key).sort().join())
  const offTotal = changed.reduce((t, i) => t + (draft[i.id]?.length ?? 0), 0)

  function toggle(n: StepNode) {
    const off = offFor(n.i)
    const next = off.includes(n.def.key) ? off.filter((k) => k !== n.def.key) : [...off, n.def.key]
    if (next.length >= (n.i.steps ?? []).length) {
      setErr(`Keep at least one step of ${n.i.name} on. To stop reading it, set its schedule to Manual on the Sources view.`)
      return
    }
    setErr(null)
    setDraft((p) => ({ ...p, [n.i.id]: next }))
    setSel({ type: 'step', id: `${n.i.id}|${n.def.key}` })
  }

  async function save() {
    setSaving(true)
    setErr(null)
    try {
      for (const i of changed) await d.setScope(i.id, draft[i.id])
      setDraft({})
      await d.refresh()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not save the scope')
    } finally {
      setSaving(false)
    }
  }

  function onPointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    if ((e.target as HTMLElement).closest('button, a')) return
    const s = scroller.current
    if (!s) return
    drag.current = { x: e.clientX, y: e.clientY, left: s.scrollLeft, top: s.scrollTop }
    s.setPointerCapture(e.pointerId)
  }
  function onPointerMove(e: ReactPointerEvent<HTMLDivElement>) {
    const s = scroller.current
    if (!s || !drag.current) return
    s.scrollLeft = drag.current.left - (e.clientX - drag.current.x)
    s.scrollTop = drag.current.top - (e.clientY - drag.current.y)
  }

  const sample = (i: Integration, id: string) => {
    const a = assets.get(`${i.id}|${id}`)
    return a ? detail(a).split(' · ').filter(Boolean).slice(0, 2).join(' · ') : ''
  }

  // Inspector content for the selected node.
  let insp: { kind: string; title: string; sub: string; what: string[]; scope: string; err?: string | null } | null = null
  if (sel.type === 'source') {
    const i = d.integrations.find((x) => x.id === sel.id)
    if (i) {
      const h = healthOf(i)
      insp = {
        kind: 'Source',
        title: i.name,
        sub: `${HEALTH_LABEL[h]} · last fetched ${ago(i.lastSyncedAt)}${i.scheduleMinutes ? ` · next read ${until(i.nextSyncAt)}` : ''}`,
        what: (i.steps ?? []).map((s) => `${s.title}${offFor(i).includes(s.key) ? ' (off)' : ''}`),
        scope: [where(i), ...(SOURCES[i.kind]?.permissions ?? [])].join('\n'),
        err: h === 'failing' ? i.recentRuns?.[0]?.error : null,
      }
    }
  } else if (sel.type === 'step') {
    const n = stepNodes.find((x) => `${x.i.id}|${x.def.key}` === sel.id)
    if (n) {
      insp = {
        kind: `Step · ${n.i.name}`,
        title: n.def.title,
        sub: !n.on ? 'Turned off: not read on the next run' : n.run ? `${n.run.found} found, ${n.run.created} new on the last good read` : 'Not read yet',
        what: (n.run?.samples ?? []).map((s) => `${s.name}${s.new ? ' (new)' : ''}${sample(n.i, s.id) ? ` · ${sample(n.i, s.id)}` : ''}`),
        scope: n.def.call,
        err: n.failing ? 'The source is failing; these are from the last good read.' : null,
      }
    }
  } else if (sel.type === 'rules') {
    insp = {
      kind: 'Rules',
      title: 'Suggest risk',
      sub: 'The same rules run on every source',
      what: ['A risk tier declared on the item wins', 'Credit, hiring, health, KYC and similar words in a name: high', 'Developer tools start low'],
      scope: 'FairMind discovery rules',
    }
  }

  return (
    <section className="fm-card fl-wrap" aria-label="Flow of every source into the inventory">
      <div className="fl-bar">
        <Text color="secondary" size="sm">
          Drag to move around. Click a step to see what it fetched; switch a step off to stop reading it.
        </Text>
        <HStack gap={2} vAlign="center">
          {changed.length > 0 && (
            <>
              <span className="fl-changed">
                {offTotal} step{offTotal === 1 ? '' : 's'} off in {changed.length} source{changed.length === 1 ? '' : 's'}
              </span>
              <Button size="sm" variant="ghost" label="Discard" onClick={() => setDraft({})} />
              <Button size="sm" variant="primary" label={saving ? 'Saving' : 'Save scope'} isDisabled={saving} onClick={() => void save()} />
            </>
          )}
          <Button size="sm" variant="secondary" label="Zoom out" onClick={() => setZoom((z) => Math.max(0.5, Math.round((z - 0.1) * 10) / 10))} />
          <span className="fl-zoom">{Math.round(zoom * 100)}%</span>
          <Button size="sm" variant="secondary" label="Zoom in" onClick={() => setZoom((z) => Math.min(1.5, Math.round((z + 0.1) * 10) / 10))} />
        </HStack>
      </div>
      {err && <div className="fl-err">{err}</div>}
      <div ref={scroller} className="fl-scroll" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={() => (drag.current = null)}>
        <div style={{ width: WIDTH * zoom, height: height * zoom }}>
          <div className="fl-canvas" style={{ width: WIDTH, height, transform: `scale(${zoom})` }}>
            <span className="fl-col" style={{ left: SX }}>Sources</span>
            <span className="fl-col" style={{ left: RX }}>What each read fetches</span>
            <span className="fl-col" style={{ left: UX }}>Rules</span>
            <span className="fl-col" style={{ left: IX }}>Inventory</span>

            <svg className="fl-edges" width={WIDTH} height={height} aria-hidden="true">
              {stepNodes.map((n) => {
                const sy = (sourceY.get(n.i.id) ?? 0) + SH / 2
                const ry = n.y + RH / 2
                const w = live(n) ? Math.max(2, Math.round(((n.run?.found ?? 0) / maxFound) * 12)) : 1.5
                return (
                  <g key={`${n.i.id}|${n.def.key}`}>
                    <path d={curve(SX + SW, sy, RX, ry)} className={n.failing || !n.on ? 'fl-e dead' : 'fl-e thin'} />
                    <path d={curve(RX + RW, ry, UX, ruleY + UH / 2)} className={live(n) ? 'fl-e' : 'fl-e dead'} style={{ strokeWidth: w }} />
                    {live(n) && <path d={curve(RX + RW, ry, UX, ruleY + UH / 2)} className="fl-e flow" />}
                  </g>
                )
              })}
              <path d={curve(UX + UW, ruleY + UH / 2, IX, invY + 230)} className="fl-e" style={{ strokeWidth: 16, stroke: 'var(--color-text-primary)' }} />
              {flowing > 0 && <path d={curve(UX + UW, ruleY + UH / 2, IX, invY + 230)} className="fl-e flow" />}
            </svg>

            {d.integrations.map((i) => {
              const h = healthOf(i)
              const runs = [...(i.recentRuns ?? [])].slice(0, 10).reverse()
              const max = Math.max(1, ...runs.map((r) => r.found ?? 0))
              return (
                <button
                  key={i.id}
                  type="button"
                  className={`fl-node fl-src${sel.type === 'source' && sel.id === i.id ? ' sel' : ''}${h === 'failing' ? ' bad' : ''}`}
                  style={{ left: SX, top: sourceY.get(i.id), width: SW, height: SH }}
                  onClick={() => setSel({ type: 'source', id: i.id })}
                >
                  <span className="fl-row">
                    <SourceMark kind={i.kind} />
                    <span className="fl-col2">
                      <span className="fl-title">{i.name}</span>
                      <span className="fl-sub">
                        <i className={`dv-dot ${h}`} />
                        {HEALTH_LABEL[h]}
                        {i.scheduleMinutes ? ` · ${i.scheduleMinutes === 60 ? 'hourly' : i.scheduleMinutes === 1440 ? 'daily' : 'every 6 h'}` : ''}
                      </span>
                    </span>
                  </span>
                  <span className="fl-row end">
                    <span className="fl-sub">
                      Fetched {ago(i.lastSyncedAt)}
                      <br />
                      {i.kind === 'proxy_logs' ? 'Reads uploads' : i.scheduleMinutes ? `Next ${until(i.nextSyncAt)}` : 'Manual'}
                    </span>
                    <span className="dv-runs" style={{ height: 22 }} aria-hidden="true">
                      {runs.map((r) => (
                        <span key={r.id} className={r.status === 'failed' ? 'failed' : r.created ? 'new' : ''} style={{ height: r.status === 'failed' ? 8 : Math.max(3, Math.round(((r.found ?? 0) / max) * 22)), width: 5 }} />
                      ))}
                    </span>
                  </span>
                  <span className="fl-port out" style={{ top: SH / 2 - 5 }} />
                </button>
              )
            })}

            {stepNodes.map((n) => {
              const id = `${n.i.id}|${n.def.key}`
              return (
                <div
                  key={id}
                  className={`fl-node fl-step${sel.type === 'step' && sel.id === id ? ' sel' : ''}${n.on ? '' : ' off'}${n.failing ? ' stale' : ''}`}
                  style={{ left: RX, top: n.y, width: RW, height: RH }}
                >
                  <span className="fl-port in" style={{ top: RH / 2 - 5 }} />
                  <span className="fl-port out" style={{ top: RH / 2 - 5 }} />
                  <div className="fl-row between">
                    <button type="button" className="fl-link" onClick={() => setSel({ type: 'step', id })}>
                      <span className="fl-title">{n.def.title}</span>
                      <span className={`fl-badge${n.failing ? ' bad' : ''}`}>{n.on ? (n.run?.found ?? '·') : 'off'}</span>
                    </button>
                    {n.def.toggleable && (
                      <button
                        type="button"
                        className={`fl-switch${n.on ? ' on' : ''}`}
                        role="switch"
                        aria-checked={n.on}
                        aria-label={`${n.on ? 'Stop reading' : 'Read'} ${n.def.title} from ${n.i.name}`}
                        onClick={() => toggle(n)}
                      >
                        <span />
                      </button>
                    )}
                  </div>
                  <div className="fl-samples">
                    {(n.run?.samples ?? []).map((s) => (
                      <div key={s.id} className="fl-sample">
                        <span className="nm">{s.name}</span>
                        <span className="dt">{s.new ? 'new' : sample(n.i, s.id)}</span>
                      </div>
                    ))}
                    {!n.run && <div className="fl-sample"><span className="dt">Not read yet</span></div>}
                    {n.run && n.run.found > n.run.samples.length && <div className="fl-sample"><span className="dt">and {n.run.found - n.run.samples.length} more</span></div>}
                  </div>
                  <div className="fl-foot">{!n.on ? 'Off: not read on the next run' : n.failing ? 'Not reached · last good read' : n.def.call}</div>
                </div>
              )
            })}

            <button
              type="button"
              className={`fl-node fl-rules${sel.type === 'rules' ? ' sel' : ''}`}
              style={{ left: UX, top: ruleY, width: UW, height: UH }}
              onClick={() => setSel({ type: 'rules', id: 'rules' })}
            >
              <span className="fl-port in" style={{ top: UH / 2 - 5 }} />
              <span className="fl-port out" style={{ top: UH / 2 - 5 }} />
              <span className="fl-title">Suggest risk</span>
              <span className="fl-sub">Same rules for every source</span>
              <span className="fl-tierbar" aria-hidden="true">
                {tiers.filter((x) => x.n).map((x) => (
                  <span key={x.t} className={`t-${x.t}`} style={{ flex: x.n }} />
                ))}
              </span>
              <span className="fl-tiers">
                {tiers.filter((x) => x.n).map((x) => (
                  <span key={x.t}>
                    <b className={x.t === 'high' || x.t === 'critical' ? 'hot' : ''}>{x.n}</b> {x.t}
                  </span>
                ))}
              </span>
            </button>

            <div className="fl-node fl-inv" style={{ left: IX, top: invY, width: IW, height: INV_H }}>
              <span className="fl-port in" style={{ top: 225 }} />
              <div className="fl-row" style={{ alignItems: 'baseline', gap: 10 }}>
                <span className="fl-big">{d.discovered.length}</span>
                <span className="fl-sub">found across {d.integrations.length} source{d.integrations.length === 1 ? '' : 's'}</span>
              </div>
              <div className="dv-flow" style={{ marginTop: 14 }} aria-hidden="true">
                {reg > 0 && <span style={{ flex: reg, background: 'var(--color-text-primary)' }} />}
                {wait > 0 && <span style={{ flex: wait, background: 'var(--color-text-warning)' }} />}
                {ign > 0 && <span style={{ flex: ign, background: 'var(--color-border)' }} />}
              </div>
              <div className="dv-legend" style={{ marginTop: 6, fontSize: 12 }}>
                <span><b>{reg}</b> registered</span>
                <span><b>{wait}</b> waiting</span>
                <span><b>{ign}</b> ignored</span>
              </div>
              <div className="fl-kinds">
                {byKind.slice(0, 3).map(([k, n]) => (
                  <div key={k}>
                    <b>{n}</b>
                    <span>{KIND_LABEL[k] ?? k}</span>
                  </div>
                ))}
              </div>
              <div className="fl-col fl-static">Arrived today</div>
              {today.length === 0 && <div className="fl-sub" style={{ marginTop: 6 }}>Nothing new in the last 24 hours.</div>}
              {today.map((a) => (
                <div key={a.id} className="fl-arrival">
                  <SourceMark kind={a.source} size="sm" />
                  <span className="nm">{a.name}</span>
                  <span className={`dv-chip ${a.suggestedTier}`}>{a.suggestedTier}</span>
                </div>
              ))}
              <div className="fl-inv-cta">
                <Button variant="primary" label={wait ? `Review ${wait} waiting` : 'See found items'} onClick={onReview} />
              </div>
            </div>

            <div className="fl-node fl-insp" style={{ left: IX, top: PAD, width: IW, height: INSP_H }} aria-live="polite">
              {insp ? (
                <>
                  <div className="fl-col fl-static">{insp.kind}</div>
                  <div className="fl-title" style={{ fontSize: 17, marginTop: 4 }}>{insp.title}</div>
                  <div className="fl-sub">{insp.sub}</div>
                  {insp.err && <div className="fl-insp-err">{insp.err}</div>}
                  <div className="fl-h">{sel.type === 'step' ? 'What it fetched' : 'What it fetches'}</div>
                  {insp.what.length === 0 && <div className="fl-sub">Nothing yet.</div>}
                  {insp.what.slice(0, 5).map((w) => (
                    <div key={w} className="fl-what">{w}</div>
                  ))}
                  <div className="fl-h">Scope</div>
                  <pre className="dv-perms">{insp.scope}</pre>
                </>
              ) : (
                <div className="fl-sub">Click a source, a step or the rules to see what it fetches.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

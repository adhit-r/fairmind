import { iso, TONES, type Figure, type Iso, type Tones } from './iso'

/** Latest run status of a workflow; null when it has never run. */
export type RunStatus = 'queued' | 'running' | 'waiting' | 'blocked' | 'done' | 'failed' | null

export interface FigWorkflow {
  status: RunStatus
  /** Number shown on the agent disc when the run waits for a person. */
  waitNo?: number
}

const DELAYS = ['', 'd2', 'd3']

function tonesFor(status: RunStatus): { m: Tones; cls: string } {
  if (status === 'done') return { m: TONES.seal, cls: 'e' }
  if (status === 'blocked' || status === 'failed') return { m: TONES.held, cls: 'e' }
  if (status === 'running' || status === 'waiting') return { m: TONES.paper, cls: 'e' }
  return { m: TONES.queued, cls: 'e dash' }
}

function agentFor(g: Iso, w: FigWorkflow, x: number, y: number, z: number, lift: number, i: number) {
  if (w.status === 'running') g.agent(x, y, z, lift, 'work', 0, DELAYS[i % 3])
  else if (w.status === 'waiting') g.agent(x, y, z, lift, 'need', w.waitNo ?? 0, DELAYS[i % 3])
  else if (w.status === 'blocked' || w.status === 'failed') g.agent(x, y, z, lift, 'held')
}

/** One platform per clause, rising toward the audit flag. Clauses are front to back. */
export function journeyFigure(clauses: Array<{ number: string; name: string; workflows: FigWorkflow[] }>): Figure {
  const g = iso(34)
  const { P } = g
  const W = 3.4
  const N = clauses.length
  const L = 2.7
  const Y0 = N * L
  const H = (i: number) => 0.75 + i * 0.5
  const rows = clauses.map((c) => Math.max(1, Math.ceil(c.workflows.length / 2)))
  g.shadow(-0.9, -0.9, -0.5, W + 1.8, Y0 + 1.8, 0.9)
  g.box(-0.9, -0.9, -0.5, W + 1.8, Y0 + 1.8, 0.5, TONES.stone)
  for (let i = N - 1; i >= 0; i--) g.box(0, Y0 - (i + 1) * L, 0, W, L, H(i), TONES.paper)
  if (N > 0) {
    const hp = H(N - 1)
    const px = W - 0.6
    const py = Y0 - N * L + 0.45
    g.box(px - 0.15, py - 0.15, hp, 0.3, 0.3, 0.12, TONES.graphite)
    g.line(P(px, py, hp + 0.12), P(px, py, hp + 2.1), 'pole')
    g.face([P(px, py, hp + 2.1), P(px, py - 1.25, hp + 1.85), P(px, py, hp + 1.6)], '#15171a', 'n')
  }
  let a = 0
  for (let i = N - 1; i >= 0; i--) {
    const y0 = Y0 - (i + 1) * L
    const zt = H(i)
    const ws = clauses[i].workflows
    // Two columns of blocks in row-major order, which is back to front; agents float above, so they go last.
    const bw = ws.length > 1 ? 1.25 : 1.5
    const bd = rows[i] > 1 ? 0.6 : 0.8
    const z2 = zt + 0.28
    const spots = ws.map((w, k) => {
      const bx = ws.length > 1 ? 0.35 + (k % 2) * 1.45 : 0.95
      const yb = y0 + 0.3 + (Math.floor(k / 2) * (L - 0.6 - bd)) / Math.max(1, rows[i] - 1)
      const { m, cls } = tonesFor(w.status)
      g.box(bx, yb, zt, bw, bd, 0.28, m, cls)
      if (w.status === 'done') {
        g.line(P(bx + 0.4, yb + bd * 0.5, z2), P(bx + 0.58, yb + bd * 0.72, z2), 'chk')
        g.line(P(bx + 0.58, yb + bd * 0.72, z2), P(bx + 0.95, yb + bd * 0.25, z2), 'chk')
      }
      return { w, x: bx + bw / 2, y: yb + bd / 2 }
    })
    for (const s of spots) agentFor(g, s.w, s.x, s.y, z2, 1.0, a++)
    g.xf(W, y0 + L - 0.2, zt - 0.34, `CLAUSE ${clauses[i].number}`, 'lbt')
    // The face fits about 12 capitals; longer clause titles keep their first word (the list below the figure has them in full).
    const name = clauses[i].name.length > 12 ? clauses[i].name.split(' ')[0] : clauses[i].name
    g.xf(W, y0 + L - 0.2, zt - 0.66, name.toUpperCase(), 'lbx')
  }
  return { viewBox: g.viewBox(16), items: g.items }
}

/** The organisation's AI management system as a board; one module per installed pack. */
export function packsFigure(packs: Array<{ label: string; installed: boolean; workflows: FigWorkflow[] }>): Figure {
  const g = iso(30)
  const { P } = g
  const n = Math.max(packs.length, 1)
  const SW = 4.2
  const BW = n * (SW + 0.6) + 0.6
  g.shadow(-0.6, -0.6, -0.5, BW + 1.2, 7.8, 0.9)
  g.box(-0.6, -0.6, -0.5, BW + 1.2, 7.8, 0.5, TONES.stone)
  g.box(0, 0, 0, BW, 6.6, 0.3, TONES.paper)
  // Back rail with one light per slot; lit when the slot holds a pack.
  g.box(0.2, -0.45, 0.3, BW - 0.4, 0.45, 0.35, TONES.graphite)
  packs.forEach((p, i) => {
    const x = 0.6 + i * (SW + 0.6)
    g.face([P(x + SW / 2 - 0.2, -0.3, 0.65), P(x + SW / 2 + 0.2, -0.3, 0.65), P(x + SW / 2 + 0.2, -0.1, 0.65), P(x + SW / 2 - 0.2, -0.1, 0.65)], p.installed ? '#3ee0a1' : '#6b6f78', p.installed ? 'n gw' : 'n')
  })
  let a = 0
  packs.forEach((p, i) => {
    const x = 0.6 + i * (SW + 0.6)
    const y = 0.5
    if (!p.installed) {
      g.face([P(x, y, 0.31), P(x + SW, y, 0.31), P(x + SW, y + 5.4, 0.31), P(x, y + 5.4, 0.31)], '#ebe8e1', 'e dash')
      const q = P(x + SW / 2, y + 2.7, 0.31)
      g.line([q[0] - 9, q[1]], [q[0] + 9, q[1]], 'plus')
      g.line([q[0], q[1] - 9], [q[0], q[1] + 9], 'plus')
      g.yf(x + 0.3, y + 5.4, 0.31, p.label.toUpperCase(), 'lbx')
      return
    }
    const h = 1.0 + Math.min(p.workflows.length, 12) * 0.05
    g.shadow(x, y, 0.3, SW, 5.4, 0.3)
    g.box(x, y, 0.3, SW, 5.4, h, TONES.paper)
    const zt = 0.3 + h
    const cols = 3
    const rows = Math.max(1, Math.ceil(p.workflows.length / cols))
    const tw = (SW - 0.4 - (cols - 1) * 0.15) / cols
    const td = Math.min(1.1, (5.4 - 0.4 - (rows - 1) * 0.15) / rows)
    p.workflows.forEach((w, k) => {
      const tx = x + 0.2 + (k % cols) * (tw + 0.15)
      const ty = y + 0.2 + Math.floor(k / cols) * (td + 0.15)
      const st = w.status
      const fill = st === 'done' ? '#a9d6bf' : st === 'waiting' ? '#ff7a45' : st === 'running' ? '#ffffff' : st === 'blocked' || st === 'failed' ? '#b0b3b9' : '#fbfaf8'
      g.face([P(tx, ty, zt), P(tx + tw, ty, zt), P(tx + tw, ty + td, zt), P(tx, ty + td, zt)], fill, st ? 'e' : 'e dash')
    })
    p.workflows.forEach((w, k) => {
      const tx = x + 0.2 + (k % cols) * (tw + 0.15) + tw / 2
      const ty = y + 0.2 + Math.floor(k / cols) * (td + 0.15) + td / 2
      agentFor(g, w, tx, ty, zt, 1.0, a++)
    })
    g.yf(x + 0.3, y + 5.4, 0.3 + h * 0.62, p.label.toUpperCase(), 'lbm')
  })
  return { viewBox: g.viewBox(16), items: g.items }
}

export interface RunFig {
  systems: string[]
  steps: Array<{ status: 'done' | 'current' | 'next' }>
  gate: 'closed' | 'open' | 'none'
  waitNo?: number
  agent: 'work' | 'need' | 'held' | 'idle'
  sealed: number
}

/** A live run: the agent reads its systems, steps advance, the gate holds, evidence stacks up. */
export function runFigure(r: RunFig): Figure {
  const g = iso(30)
  const { P } = g
  const sys = r.systems.slice(0, 4)
  const steps = r.steps.slice(0, 9)
  g.shadow(-0.6, -0.6, -0.5, 17.2, 11.2, 0.9)
  g.box(-0.5, -0.5, -0.5, 17, 11, 0.5, TONES.stone)
  const sy = (i: number) => 1.8 + i * 2.2
  sys.forEach((name, i) => {
    g.shadow(1.0, sy(i) - 0.8, 0, 1.6, 1.6, 0.3)
    g.cyl(1.8, sy(i), 0, 0.8, 1.7, [0.45, 1.15])
    g.top(1.8, sy(i) - 0.2, 1.7, name.toUpperCase().slice(0, 10), 'lbc')
  })
  g.shadow(4.2, 0.8, 0, 8.6, 8.4, 0.7)
  g.box(4.2, 0.8, 2.0, 8.6, 8.4, 0.15, TONES.glass)
  g.line(P(4.2, 9.2, 2.15), P(12.8, 9.2, 2.15), 'gle')
  g.line(P(12.8, 0.8, 2.15), P(12.8, 9.2, 2.15), 'gle')
  g.shadow(5.8, 3.0, 2.15, 4.4, 4.0, 0.25)
  g.box(5.8, 3.0, 2.15, 4.4, 4.0, 0.3, TONES.pad)
  if (r.agent === 'work') sys.forEach((_, i) => g.line(P(8, 5, 3.5), P(1.8, sy(i), 1.7), 'beam'))
  if (r.gate !== 'none') {
    g.box(10.2, 4.6, 2.15, 2.6, 0.8, 0.03, ['#efede8', '#dcd8d0', '#cfcac1'])
    for (const x of [10.45, 11.85]) {
      g.line(P(x, 4.75, 2.19), P(x + 0.28, 5.0, 2.19), 'chev')
      g.line(P(x + 0.28, 5.0, 2.19), P(x, 5.25, 2.19), 'chev')
    }
    g.box(11.0, 3.9, 2.15, 0.22, 0.22, 1.35, TONES.graphite)
    if (r.gate === 'closed') g.box(11.02, 4.12, 3.2, 0.18, 1.78, 0.2, TONES.need)
    else g.box(11.02, 3.95, 3.2, 0.18, 0.18, 1.6, TONES.seal)
    g.box(11.0, 5.9, 2.15, 0.22, 0.22, 1.35, TONES.graphite)
  }
  const sw = Math.min(0.9, (7.6 - (steps.length - 1) * 0.18) / Math.max(steps.length, 1))
  steps.forEach((s, k) => {
    const x = 4.75 + k * (sw + 0.18)
    const m = s.status === 'done' ? TONES.seal : s.status === 'current' ? TONES.need : TONES.card
    g.box(x, 7.85, 2.15, sw, 0.75, 0.1, m, s.status === 'next' ? 'e dash' : 'e')
    g.top(x + sw * 0.36, 7.85 + 0.5, 2.25, String(k + 1), 'lbn')
  })
  g.shadow(13.4, 6.4, 0, 2.2, 2.6, 0.35)
  g.box(13.4, 6.4, 0, 2.2, 2.6, 0.4, TONES.pad)
  const plates = Math.min(r.sealed, 7)
  for (let k = 0; k < plates; k++) g.box(13.7, 6.7, 0.4 + k * 0.26, 1.6, 2.0, 0.2, TONES.graphite, k === plates - 1 ? 'e newest' : 'e')
  g.yf(13.6, 9.0, 0.13, 'EVIDENCE', 'lbx')
  if (r.sealed > 0) g.agent(14.5, 7.6, 0.4 + plates * 0.26, 0.9, 'work', 0, 'd2')
  if (r.agent !== 'idle') g.agent(8, 5, 2.45, 1.05, r.agent, r.waitNo ?? 0)
  return { viewBox: g.viewBox(16), items: g.items }
}

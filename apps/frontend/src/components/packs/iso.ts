/**
 * Isometric drawing helper for the agentic-pack figures.
 *
 * World units: x and y on the floor, z up. Everything is pushed into one
 * ordered list, so callers draw back to front and labels sit in true depth.
 */

export type Pt = [number, number]
export type IsoItem =
  | { kind: 'path'; d: string; fill: string; cls: string }
  | { kind: 'text'; tr: string; text: string; cls: string }
export type Tones = [top: string, left: string, right: string]
export type AgentState = 'work' | 'need' | 'held'

const C = Math.cos(Math.PI / 6)
const S = 0.5
const f = (n: number) => n.toFixed(1)
const D = (a: Pt[]) => 'M' + a.map((p) => `${f(p[0])} ${f(p[1])}`).join(' L') + ' Z'

export function iso(sc: number) {
  const items: IsoItem[] = []
  const bb = [1e9, 1e9, -1e9, -1e9]

  const P = (x: number, y: number, z: number): Pt => {
    const X = (x - y) * C * sc
    const Y = ((x + y) * S - z) * sc
    bb[0] = Math.min(bb[0], X)
    bb[1] = Math.min(bb[1], Y)
    bb[2] = Math.max(bb[2], X)
    bb[3] = Math.max(bb[3], Y)
    return [X, Y]
  }
  const path = (d: string, fill: string, cls: string) => items.push({ kind: 'path', d, fill, cls })
  const text = (tr: string, t: string, cls: string) => items.push({ kind: 'text', tr, text: t, cls })

  const g = {
    P,
    items,
    face: (a: Pt[], fill: string, cls = 'e') => path(D(a), fill, cls),
    box(x: number, y: number, z: number, w: number, d: number, h: number, m: Tones, cls = 'e') {
      g.face([P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)], m[1], cls)
      g.face([P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)], m[2], cls)
      g.face([P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)], m[0], cls)
    },
    shadow(x: number, y: number, z: number, w: number, d: number, s: number, cls = 'sh') {
      for (const k of [1, 0.6, 0.3]) {
        const t = s * k
        path(D([P(x - t, y - t, z), P(x + w + t, y - t, z), P(x + w + t, y + d + t, z), P(x - t, y + d + t, z)]), '#2a241a', cls)
      }
    },
    arc(cx: number, cy: number, z: number, r: number, a0: number, a1: number, n: number): Pt[] {
      return Array.from({ length: n + 1 }, (_, j) => {
        const t = a0 + ((a1 - a0) * j) / n
        return P(cx + r * Math.cos(t), cy + r * Math.sin(t), z)
      })
    },
    circ: (cx: number, cy: number, z: number, r: number, n: number) => g.arc(cx, cy, z, r, 0, 2 * Math.PI, n).slice(0, n),
    ring: (cx: number, cy: number, z: number, r: number, cls: string) => path(D(g.circ(cx, cy, z, r, 28)), 'none', cls),
    /** Upright cylinder shaded in five tone bands, for a connected system. */
    cyl(cx: number, cy: number, z: number, r: number, h: number, rings: number[] = []) {
      const tones = ['#a9afb9', '#c9ced5', '#e4e7eb', '#d5d9de', '#b6bcc5']
      const A0 = (3 * Math.PI) / 4
      const A1 = -Math.PI / 4
      const band = (a0: number, a1: number, z0: number, z1: number, n: number) =>
        g.arc(cx, cy, z0, r, a0, a1, n).concat(g.arc(cx, cy, z1, r, a0, a1, n).reverse())
      tones.forEach((tone, b) => g.face(band(A0 + ((A1 - A0) * b) / 5, A0 + ((A1 - A0) * (b + 1)) / 5, z, z + h, 4), tone, 'n'))
      rings.forEach((rz) => g.face(band(A0, A1, z + rz, z + rz + 0.07, 16), 'rgba(21,23,26,.16)', 'n'))
      g.face(band(A0, A1, z, z + h, 16), 'none', 'e')
      g.face(g.circ(cx, cy, z + h, r, 32), '#eef0f3', 'e')
      g.face(g.circ(cx, cy, z + h, r * 0.62, 28), '#e0e3e8', 'e')
    },
    disc: (p: Pt, r: number, fill: string, cls = 'e') =>
      path(`M${f(p[0] - r)} ${f(p[1])} a${r} ${r} 0 1 0 ${2 * r} 0 a${r} ${r} 0 1 0 ${-2 * r} 0 Z`, fill, cls),
    line: (a: Pt, b: Pt, cls: string) => path(`M${f(a[0])} ${f(a[1])} L${f(b[0])} ${f(b[1])}`, 'none', cls),
    /** Text lying on a top face, running along +x. */
    top(x: number, y: number, z: number, t: string, cls: string) {
      const p = P(x, y, z)
      text(`matrix(${C} ${S} ${-C} ${S} ${f(p[0])} ${f(p[1])})`, t, cls)
    },
    /** Text on a +x face, running toward -y. */
    xf(x: number, y: number, z: number, t: string, cls: string) {
      const p = P(x, y, z)
      text(`matrix(${C} ${-S} 0 1 ${f(p[0])} ${f(p[1])})`, t, cls)
    },
    /** Text on a +y face, running along +x. */
    yf(x: number, y: number, z: number, t: string, cls: string) {
      const p = P(x, y, z)
      text(`matrix(${C} ${S} 0 1 ${f(p[0])} ${f(p[1])})`, t, cls)
    },
    scr: (p: Pt, t: string, cls: string) => text(`translate(${f(p[0])} ${f(p[1])})`, t, cls),
    /** A floating agent cube: working (green light), needs you (numbered disc), or held. */
    agent(x: number, y: number, zs: number, lift: number, st: AgentState, n = 0, delay = '') {
      const s = 0.66
      const h = s / 2
      const z = zs + lift
      const held = st === 'held'
      if (held) g.shadow(x - h, y - h, zs, s, s, 0.1)
      else g.shadow(x - h + 0.08, y - h + 0.08, zs, s - 0.16, s - 0.16, 0.12, `csh ${delay}`)
      if (st === 'need') g.ring(x, y, zs, 0.78, 'ringp')
      g.box(x - h, y - h, z, s, s, s, held ? ['#c9cbd0', '#a9acb2', '#92959c'] : ['#3d4048', '#25272c', '#141518'], held ? 'e' : `e bob ${delay}`)
      const zt = z + s
      const sq = (x0: number, y0: number, x1: number, y1: number): Pt[] => [P(x0, y0, zt), P(x1, y0, zt), P(x1, y1, zt), P(x0, y1, zt)]
      if (st === 'work') g.face(sq(x - 0.17, y - 0.17, x + 0.17, y + 0.17), '#3ee0a1', `n gl ${delay}`)
      if (held) {
        g.face(sq(x - 0.2, y - 0.16, x - 0.07, y + 0.16), '#15171a', 'n')
        g.face(sq(x + 0.07, y - 0.16, x + 0.2, y + 0.16), '#15171a', 'n')
      }
      if (st === 'need') {
        const c = P(x + h, y - h, zt)
        const p: Pt = [c[0] + 12, c[1] - 8]
        g.disc(p, 9.5, '#ff6b35')
        g.scr([p[0], p[1] + 4], String(n), 'dn')
      }
    },
    viewBox: (pad: number) => `${f(bb[0] - pad)} ${f(bb[1] - pad)} ${f(bb[2] - bb[0] + 2 * pad)} ${f(bb[3] - bb[1] + 2 * pad)}`,
  }
  return g
}

export type Iso = ReturnType<typeof iso>
export interface Figure {
  viewBox: string
  items: IsoItem[]
}

/** Tone sets shared by the figures: [top, +y face, +x face]. */
export const TONES = {
  paper: ['#ffffff', '#e9e7e2', '#dbd8d1'],
  stone: ['#e3e0d8', '#d1ccc2', '#c2bdb2'],
  pad: ['#f6f4ef', '#dcd7cc', '#cdc7bb'],
  card: ['#ffffff', '#e6e3dd', '#d7d3cb'],
  seal: ['#d3eee0', '#a9d6bf', '#93c9ad'],
  held: ['#d0d2d6', '#b0b3b9', '#999ca3'],
  queued: ['#fbfaf8', '#ebe9e4', '#dedbd4'],
  need: ['#ff7a45', '#e15e2b', '#c75224'],
  graphite: ['#45484f', '#2a2c31', '#1b1c20'],
  glass: ['rgba(255,255,255,.5)', 'rgba(196,205,216,.55)', 'rgba(180,190,202,.6)'],
} satisfies Record<string, Tones>

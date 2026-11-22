/** Pure layout maths for the report instruments. No React, no DOM. */

export type WaterfallRow = { from: number; to: number; gain: number }
export type Waterfall = { rows: WaterfallRow[]; lo: number; hi: number; ticks: number[]; end: number }

/** Running totals from `start` through each gain, and an axis in steps of 5 that holds every value. */
export function waterfall(start: number, gains: number[], forecast: number): Waterfall {
  const rows: WaterfallRow[] = []
  let at = start
  for (const gain of gains) {
    rows.push({ from: at, to: at + gain, gain })
    at += gain
  }
  const all = [start, forecast, ...rows.flatMap((r) => [r.from, r.to])]
  const lo = Math.max(0, Math.floor((Math.min(...all) - 3) / 5) * 5)
  const hi = Math.min(100, Math.max(lo + 10, Math.ceil((Math.max(...all) + 3) / 5) * 5))
  const ticks: number[] = []
  for (let v = lo; v <= hi; v += 5) ticks.push(v)
  return { rows, lo, hi, ticks, end: at }
}

/** Position of a value on the axis, as a percentage of its width. */
export const axisPct = (v: number, lo: number, hi: number) => (hi === lo ? 0 : ((v - lo) / (hi - lo)) * 100)

export type SankeyNode = { y: number; h: number }
export type SankeyRibbon = { source: number; target: number; value: number; y0: number; y1: number; h: number }
export type Sankey = { sources: SankeyNode[]; targets: SankeyNode[]; ribbons: SankeyRibbon[]; total: number }

/** Two columns of nodes sized by the links through them, with ribbons stacked inside each node. */
export function sankey(links: number[][], height: number, gap: number): Sankey {
  const nT = links.reduce((n, r) => Math.max(n, r.length), 0)
  const sums = links.map((r) => r.reduce((a, b) => a + b, 0))
  const tsums = Array.from({ length: nT }, (_, j) => links.reduce((a, r) => a + (r[j] ?? 0), 0))
  const total = sums.reduce((a, b) => a + b, 0)
  const room = Math.max(0, height - gap * (Math.max(links.length, nT) - 1))
  const k = total ? room / total : 0
  const lay = (vals: number[]) => {
    let y = 0
    return vals.map((v) => {
      const node = { y, h: v * k }
      y += v * k + gap
      return node
    })
  }
  const sources = lay(sums)
  const targets = lay(tsums)
  const sy = sources.map((n) => n.y)
  const ty = targets.map((n) => n.y)
  const ribbons: SankeyRibbon[] = []
  links.forEach((row, i) =>
    row.forEach((value, j) => {
      if (value <= 0) return
      const h = value * k
      ribbons.push({ source: i, target: j, value, y0: sy[i], y1: ty[j], h })
      sy[i] += h
      ty[j] += h
    }),
  )
  return { sources, targets, ribbons, total }
}

export type Zone = 1 | 2 | 3 | 4
export const ZONE_NAME: Record<Zone, string> = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' }
export const LIKELIHOOD = ['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost certain']
export const IMPACT = ['Low', 'Medium', 'High', 'Critical']

/** Rating of a likelihood (1 to 5) times impact (1 to 4) cell. */
export function heatZone(likelihood: number, impact: number): Zone {
  const s = likelihood * impact
  return s >= 15 ? 4 : s >= 10 ? 3 : s >= 5 ? 2 : 1
}

export type CellTone = 'met' | 'progress' | 'attention' | 'notstarted'

/** How a requirement cell reads on the compliance grid. Unknown states count as not started. */
export function cellReadiness(state: string): CellTone {
  if (state === 'proven' || state === 'attested' || state === 'excluded') return 'met'
  if (state === 'partial' || state === 'estimated' || state === 'planned' || state === 'atorg') return 'progress'
  if (state === 'fails' || state === 'stale') return 'attention'
  return 'notstarted'
}

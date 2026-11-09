import type { Cell, CellState, MatrixGroup, MatrixProps } from '@/components/ui/matrix'
import type { Controls, FrameworkSystems } from '@/lib/api/hooks/useEstate'
import type { Journey } from '@/lib/api/hooks/usePacks'

type Tier = FrameworkSystems['systems'][number]['riskTier']
export type GridBase = Omit<MatrixProps, 'id' | 'onCell'>

export const TIERS: Tier[] = ['critical', 'high', 'medium', 'low']
const TIER_LABEL: Record<Tier, string> = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' }
export const NOT_TRACKED = 'Not tracked per system yet'
export const ORG_BLANK = 'Not covered by organisation packs'
const PROVEN_LIKE = new Set<CellState>(['proven', 'estimated', 'attested'])
/** Crosswalk relation to cell strength; "Aligns with" draws blank and is named in the cell title. */
export const STRENGTH: Record<string, 1 | 2 | 3> = { Satisfies: 3, 'Partially satisfies': 2, Supports: 1 }

/** The frameworks confirmed by any system, in system order, from each system's metadata.applicability. */
export function confirmedFrameworks(systems: Array<{ metadata?: Record<string, unknown> }>) {
  const out = new Map<string, string>()
  for (const s of systems) {
    const a = s.metadata?.applicability as { frameworks?: Array<{ key: string; name: string }> } | null | undefined
    for (const f of a?.frameworks ?? []) if (!out.has(f.key)) out.set(f.key, f.name)
  }
  return [...out].map(([key, name]) => ({ key, name }))
}

const emptyTotals = (): Record<CellState, number> => ({ proven: 0, estimated: 0, attested: 0, planned: 0, open: 0, fails: 0, stale: 0, atorg: 0 })

/** Requirements by system: an Org column, then one group per risk tier of the systems that confirmed the framework. */
export function systemGrid(journey: Journey, fw: FrameworkSystems, showAll: boolean) {
  const byKey = new Map(fw.requirements.map((r) => [r.key, r.cells]))
  const tiers = TIERS.map((t) => ({ t, at: fw.systems.flatMap((s, i) => (s.riskTier === t ? [i] : [])) })).filter((x) => x.at.length)
  const order = tiers.flatMap((x) => x.at)
  const totals = emptyTotals()
  let total = 0
  const groups: MatrixGroup[] = journey.groups.map((g) => ({
    label: g.name,
    rows: g.requirements.flatMap((r) => {
      total += 1
      const cells = byKey.get(r.key)
      const sys = order.map((i) => cells?.[i]?.state ?? null)
      const org: Cell = r.status === 'covered' || r.status === 'tested' ? 'atorg' : null
      if (!cells && !showAll) return []
      // The footer totals what the grid draws, so it moves with Show all.
      for (const c of [org, ...sys]) if (c) totals[c] += 1
      return [
        {
          key: r.key,
          code: r.control,
          label: r.title,
          title: `${r.control} · ${r.title} · ${g.name}`,
          cells: [org, ...sys],
          blank: cells ? 'No state recorded for this system' : NOT_TRACKED,
          count: cells && order.length ? `${sys.filter((c) => c && PROVEN_LIKE.has(c)).length}/${order.length}` : undefined,
        },
      ]
    }),
  }))
  const matrix: GridBase = {
    head: 'Requirement',
    colGroups: [
      { label: 'Org', cols: [{ key: 'org', label: 'Organisation', title: 'Organisation packs', blank: ORG_BLANK }] },
      ...tiers.map((x) => ({
        label: TIER_LABEL[x.t],
        cols: x.at.map((i) => ({ key: fw.systems[i].id, label: fw.systems[i].name, href: `/systems/${fw.systems[i].id}` })),
      })),
    ],
    groups,
    countHead: order.length ? 'Proven' : undefined,
    legendLabels: { atorg: 'covered by organisation packs' },
  }
  return { matrix, totals, tracked: fw.requirements.length, total }
}

const NEEDS_WORK = new Set<CellState>(['open', 'fails', 'stale'])
/** The command bar's number: tracked requirements open, failing or stale in at least one High or Critical system. */
export function needsWorkInHighCritical(fw: FrameworkSystems) {
  const at = fw.systems.flatMap((s, i) => (s.riskTier === 'high' || s.riskTier === 'critical' ? [i] : []))
  return fw.requirements.filter((r) => at.some((i) => NEEDS_WORK.has(r.cells[i]?.state as CellState))).length
}

/** Requirements by common control: the crosswalk relation of every control that touches this framework. */
export function controlGrid(journey: Journey, controls: Controls) {
  const keys = new Set(journey.groups.flatMap((g) => g.requirements.map((r) => r.key)))
  const rel = new Map<string, Map<string, string>>()
  for (const x of controls.crosswalk) {
    if (!keys.has(x.key)) continue
    const m = rel.get(x.key) ?? new Map<string, string>()
    const prev = m.get(x.commonControl)
    if (!prev || (STRENGTH[x.relation] ?? 0) > (STRENGTH[prev] ?? 0)) m.set(x.commonControl, x.relation)
    rel.set(x.key, m)
  }
  // A control earns a column only through a relation that draws; "Aligns with" alone would be a column of blanks.
  const touched = new Set([...rel.values()].flatMap((m) => [...m].flatMap(([c, x]) => (STRENGTH[x] ? [c] : []))))
  const used = controls.controls.filter((c) => touched.has(c.id))
  const families: Array<{ family: string; cols: typeof used }> = []
  for (const c of used) {
    const family = c.id.split('-')[1] ?? c.id
    const f = families.find((x) => x.family === family)
    if (f) f.cols.push(c)
    else families.push({ family, cols: [c] })
  }
  const cols = families.flatMap((f) => f.cols)
  const groups: MatrixGroup[] = journey.groups.map((g) => ({
    label: g.name,
    rows: g.requirements.map((r) => {
      const m = rel.get(r.key)
      const relations = cols.map((c) => m?.get(c.id))
      return {
        key: r.key,
        code: r.control,
        label: r.title,
        title: `${r.control} · ${r.title} · ${g.name}`,
        cells: relations.map((x) => (x ? (STRENGTH[x] ?? null) : null)),
        blank: relations.map((x) => x ?? 'Not in the crosswalk'),
        count: relations.filter((x) => x && STRENGTH[x]).length,
      }
    }),
  }))
  const matrix: GridBase = {
    head: 'Requirement',
    colGroups: families.map((f) => ({
      label: f.cols.length > 1 ? f.family : '',
      cols: f.cols.map((c) => ({ key: c.id, label: c.name, title: `${c.id} · ${c.name}` })),
    })),
    groups,
    countHead: 'Controls',
  }
  return { matrix, used: used.length, total: controls.controls.length, relationOf: (reqKey: string, controlId: string) => rel.get(reqKey)?.get(controlId) ?? null }
}

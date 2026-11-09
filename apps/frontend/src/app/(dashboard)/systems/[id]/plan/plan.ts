import type { Cell, MatrixRow } from '@/components/ui/matrix'
import { shortFrameworkName, type ApplicabilityRecord } from '@/lib/api/hooks/useApplicability'
import type { Journey } from '@/lib/api/hooks/usePacks'
import type { ReleaseGate } from '@/lib/api/hooks/useSystemFile'
import type { GridBase } from '../../../frameworks/[key]/grid'
import { bestRelation } from '../RequirementsTab'
import { VERDICT_LABEL, bestOption, pathSummary } from '../VerdictExplainer'

export type PlanPack = { pack: string; name: string; installed: boolean; newlyCovered: number }
export type PlanRow = MatrixRow & { best: Cell }

/** Every pack that covers a confirmed framework, once, in catalogue order; newlyCovered sums over the frameworks. */
export function planPacks(journeys: Journey[], order: string[]): PlanPack[] {
  const by = new Map<string, PlanPack>()
  for (const j of journeys)
    for (const s of j.steps) {
      const p = by.get(s.pack)
      if (p) p.newlyCovered += s.newlyCovered
      else by.set(s.pack, { pack: s.pack, name: s.name, installed: s.installed, newlyCovered: s.newlyCovered })
    }
  const rank = (id: string) => (order.includes(id) ? order.indexOf(id) : order.length)
  return [...by.values()].sort((a, b) => rank(a.pack) - rank(b.pack))
}

/** Requirements of the confirmed frameworks against the recommended packs; Best is over the ticked packs only. */
export function planGrid(journeys: Journey[], packs: PlanPack[], ticked: ReadonlySet<string>, all: boolean) {
  let total = 0
  const groups: Array<{ label: string; rows: PlanRow[] }> = journeys.flatMap((j) =>
    j.groups.map((g) => ({
      label: `${shortFrameworkName(j.name)} · ${g.name}`,
      rows: g.requirements.flatMap((r) => {
        total++
        const cells = packs.map((p) => bestRelation(r.workflows, p.pack))
        if (!all && !cells.some(Boolean)) return []
        const best = Math.max(0, ...cells.map((c, i) => (ticked.has(packs[i].pack) ? Number(c) : 0)))
        return [{ key: r.key, code: r.control, label: r.title, title: `${r.control} · ${r.title} · ${g.name}`, cells, best: (best || null) as Cell, blank: 'No workflow of this pack maps here' }]
      }),
    })),
  )
  const grid: GridBase = {
    head: 'Requirement',
    colGroups: [{ label: 'Recommended packs', cols: packs.map((p) => ({ key: p.pack, label: p.name, title: `${p.name} · ${p.installed ? 'installed' : 'not installed'}`, off: !ticked.has(p.pack) })) }],
    groups,
    countHead: 'Best',
  }
  return { grid, groups, total, shown: groups.reduce((n, g) => n + g.rows.length, 0) }
}

const MARKET: Record<string, string> = { IN: 'India', EU: 'EU or EEA', OTHER: 'Elsewhere' }
const RBI: Record<string, string> = { yes: 'Yes', no: 'No', unsure: 'Not sure' }
const SOURCE: Record<string, string> = { mlflow: 'MLflow registry', github: 'GitHub' }
const word = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
const yesNo = (b: boolean | null) => (b === null ? 'Not answered' : b ? 'Yes' : 'No')

/** What the AI read: the applicability answers, the tier rules that fired, and the integration that found the system. */
export function aiRead(a: ApplicabilityRecord | null | undefined, source: string | undefined) {
  const rows: Array<{ label: string; value: string; title?: string }> = []
  if (a) {
    const x = a.answers
    rows.push({ label: 'Use', value: x.use ? word(x.use) : 'Not answered' })
    rows.push({ label: 'Decides about people', value: yesNo(x.decidesAboutPeople) })
    if (x.decidesAboutPeople)
      rows.push({ label: 'Before it takes effect', value: x.humanReview === 'each' ? 'A person reviews each one' : x.humanReview === 'automatic' ? 'Automatic' : 'Not answered' })
    rows.push({ label: 'People in', value: x.markets.map((m) => MARKET[m] ?? m).join(', ') || 'Not answered' })
    rows.push({ label: 'RBI regulated', value: x.rbiRegulated ? RBI[x.rbiRegulated] : 'Not answered' })
    rows.push({ label: 'Personal data in India', value: yesNo(x.personalDataIndia) })
    if (x.intendedPurpose) rows.push({ label: 'Intended purpose', value: x.intendedPurpose })
    for (const r of a.tierRules) rows.push({ label: `Rule ${r.id}`, value: r.text, title: r.cite?.title })
  }
  if (source && source !== 'manual' && source !== 'fallback') rows.push({ label: 'Discovered from', value: SOURCE[source] ?? word(source) })
  return rows
}

/** The one top line: where the gate lands after the steps of its best path run; the summary names the first step. */
export function afterSteps(gate: ReleaseGate | null) {
  if (!gate?.path) return null
  const best = bestOption(gate.path)
  const summary = pathSummary(gate)
  if (best?.steps.length) return { text: `After the steps run: ${VERDICT_LABEL[best.verdictAfter]}, ${best.confidenceAfter.toFixed(2)}`, title: summary ?? undefined }
  return summary ? { text: summary } : null
}

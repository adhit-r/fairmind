import { checkCell, classLabel, type Cell, type MatrixGroup, type MatrixProps } from '@/components/ui/matrix'
import type { AISystemSummary } from '@/components/workflow/SystemContext'
import type { Controls, EstateGate } from '@/lib/api/hooks/useEstate'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { CHECK_ACTION } from '../dashboard/estate'
import { STRENGTH } from '../frameworks/[key]/grid'

type Sys = Pick<AISystemSummary, 'id' | 'name' | 'riskTier'>
type Fw = { key: string; name: string }
type Check = EstateGate['checks'][number]
export type Touch = { key: string; code: string; relation: string; strength: 1 | 2 | 3 }

/** The common control each release check produces evidence for (mirrors the backend's CHECK_CONTROLS). */
export const CHECK_CONTROLS: Record<GateCheck['key'], string> = {
  fairness: 'FMC-FAI-01',
  data_governance: 'FMC-DAT-01',
  human_oversight: 'FMC-OVS-01',
  monitoring: 'FMC-MON-01',
  environmental: 'FMC-ENV-01',
}
export const CHECK_CODE: Record<GateCheck['key'], string> = {
  fairness: 'FAIR',
  data_governance: 'DATA',
  human_oversight: 'HUMN',
  monitoring: 'MON',
  environmental: 'ENV',
}

/**
 * The Evidence grid: per system, one row per release check that read an evidence record. Its proof state, then
 * how far its control reaches into each framework the estate confirmed (blank where that system did not confirm it).
 */
export function evidenceGrid(systems: Sys[], gates: Map<string, Pick<EstateGate, 'checks'>>, controls: Controls, confirmedBySystem: Map<string, Fw[]>) {
  // control -> framework -> the requirements it touches with a relation that draws
  const touch = new Map<string, Map<string, Touch[]>>()
  for (const x of controls.crosswalk) {
    const strength = STRENGTH[x.relation]
    if (!strength) continue
    const at = x.key.indexOf('|')
    const fw = at < 0 ? x.key : x.key.slice(0, at)
    const m = touch.get(x.commonControl) ?? new Map<string, Touch[]>()
    const list = m.get(fw) ?? []
    const prev = list.find((t) => t.key === x.key)
    if (!prev) list.push({ key: x.key, code: at < 0 ? x.key : x.key.slice(at + 1), relation: x.relation, strength })
    else if (strength > prev.strength) Object.assign(prev, { relation: x.relation, strength })
    m.set(fw, list)
    touch.set(x.commonControl, m)
  }
  const touched = (control: string, fw: string) => touch.get(control)?.get(fw) ?? []

  const fws = new Map<string, string>()
  for (const s of systems) for (const f of confirmedBySystem.get(s.id) ?? []) if (!fws.has(f.key)) fws.set(f.key, f.name)
  const frameworks = [...fws].map(([key, name]) => ({ key, name }))

  const found = new Map<string, { system: Sys; check: Check; control: string }>()
  const groups: MatrixGroup[] = systems.map((s) => {
    const mine = new Set((confirmedBySystem.get(s.id) ?? []).map((f) => f.key))
    return {
      label: `${s.name} · ${s.riskTier}`,
      rows: (gates.get(s.id)?.checks ?? []).flatMap((c) => {
        if (!c.evidenceClass) return []
        const control = CHECK_CONTROLS[c.key]
        const key = `${s.id}:${c.key}`
        found.set(key, { system: s, check: c, control })
        const reach = frameworks.map((f) => (mine.has(f.key) ? Math.max(0, ...touched(control, f.key).map((t) => t.strength)) : null))
        return [
          {
            key,
            code: CHECK_CODE[c.key],
            label: c.label,
            title: `${CHECK_ACTION[c.key]} · ${classLabel(c.evidenceClass)} · ${c.confidence.toFixed(2)}`,
            cells: [checkCell(c), ...reach.map((r): Cell => (r ? (r as 1 | 2 | 3) : null))],
            blank: [undefined, ...reach.map((r, i) => (r === null ? `Not confirmed for ${s.name}` : `${control} does not reach ${frameworks[i].name}`))],
            count: [...mine].reduce((n, f) => n + touched(control, f).length, 0),
          },
        ]
      }),
    }
  })

  const matrix: Omit<MatrixProps, 'id' | 'onCell'> = {
    head: 'Evidence',
    colGroups: [
      { label: 'Proof', cols: [{ key: 'state', label: 'State', title: 'Proof' }] },
      ...(frameworks.length
        ? [{ label: 'Frameworks', cols: frameworks.map((f) => ({ key: f.key, label: f.name, title: f.name, href: `/frameworks/${encodeURIComponent(f.key)}` })) }]
        : []),
    ],
    groups,
    countHead: 'Requirements',
  }
  const systemIds = systems.filter((_, i) => groups[i].rows.length).map((s) => s.id)
  return { matrix, items: found.size, systemIds, frameworks, find: (rowKey: string) => found.get(rowKey) ?? null, touched }
}

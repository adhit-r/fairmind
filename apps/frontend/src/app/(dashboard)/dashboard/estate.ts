import type { AISystemSummary } from '@/components/workflow/SystemContext'
import type { EstateGate } from '@/lib/api/hooks/useEstate'
import type { DiscoveredAsset } from '@/lib/api/hooks/useIntegrations'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'

type Sys = Pick<AISystemSummary, 'id' | 'name' | 'stage' | 'createdAt'>
export type Stage = { key: string; label: string }

/** The five release checks, in gate order, as the Estate grid's columns. */
export const CHECKS: Array<{ key: GateCheck['key']; label: string }> = [
  { key: 'fairness', label: 'Fairness' },
  { key: 'data_governance', label: 'Data governance' },
  { key: 'human_oversight', label: 'Human oversight' },
  { key: 'monitoring', label: 'Monitoring' },
  { key: 'environmental', label: 'Environmental' },
]
/** The gate action that produces each check's evidence (static configuration, as the gate's path names them). */
export const CHECK_ACTION: Record<GateCheck['key'], string> = {
  fairness: 'Run a fairness test',
  data_governance: 'Attest data governance, or upload its evidence',
  human_oversight: 'Attest human oversight, or upload its evidence',
  monitoring: 'Record a monitoring snapshot',
  environmental: 'Run an environmental assessment',
}

/** The spine's stations: the lifecycle stages with Decision before Operate. */
export const stations = (stages: Stage[]): Stage[] => [...stages.slice(0, 4), { key: 'decision', label: 'Decision' }, ...stages.slice(4)]

/** Systems grouped by station; a system with a pending decision sits in Decision. Empty groups are dropped. */
export function estateGroups<S extends Sys>(
  systems: S[],
  gates: Map<string, Pick<EstateGate, 'confidence'>>,
  pending: Set<string>,
  stages: Stage[],
  { filter = null, sort = false }: { filter?: string | null; sort?: boolean } = {},
) {
  const conf = (s: S) => gates.get(s.id)?.confidence ?? Number.POSITIVE_INFINITY
  return stations(stages)
    .map((st, i) => {
      let items = filter && filter !== st.key ? [] : systems.filter((s) => (pending.has(s.id) ? 'decision' : s.stage) === st.key)
      if (sort) items = [...items].sort((a, b) => conf(a) - conf(b))
      return { key: st.key, label: `${String(i + 1).padStart(2, '0')} ${st.label} · ${items.length}`, systems: items }
    })
    .filter((g) => g.systems.length > 0)
}

export interface Next {
  stage?: string
  title: string
  reason?: string
  primary?: { label: string; href: string }
}

/** The command bar: decisions first, then the weakest No go, else nothing. */
export function estateNext(systems: Sys[], gates: Map<string, Pick<EstateGate, 'verdict' | 'confidence'>>, pending: Set<string>): Next {
  const waiting = systems.filter((s) => pending.has(s.id))
  if (waiting.length) {
    const n = waiting.length
    return {
      stage: 'decision',
      title: `${n} decision${n === 1 ? ' waits' : 's wait'} for you`,
      reason: waiting.map((s) => s.name).join(', '),
      primary: { label: 'Review', href: `/systems/${waiting[0].id}` },
    }
  }
  const nogo = systems
    .filter((s) => gates.get(s.id)?.verdict === 'no_go')
    .sort((a, b) => gates.get(a.id)!.confidence - gates.get(b.id)!.confidence)[0]
  if (nogo) {
    return {
      stage: nogo.stage,
      title: `Raise ${nogo.name} from No go`,
      reason: `Gate confidence ${gates.get(nogo.id)!.confidence.toFixed(2)}, the lowest of the systems at No go`,
      primary: { label: 'Open system', href: `/systems/${nogo.id}` },
    }
  }
  return { title: 'Nothing needs you' }
}

export interface Since {
  parts: string[]
  rows: Array<{ key: string; label: string; detail: string; href?: string }>
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/**
 * What changed since the last visit; null when nothing did or there is no earlier visit.
 * A lapse carries no timestamp, so `seenLapsed` (the systems already lapsed when the line was last dismissed) are left out.
 */
export function sinceLine(
  lastVisit: string | null,
  systems: Sys[],
  gates: Map<string, Pick<EstateGate, 'checks'>>,
  discovered: Array<Pick<DiscoveredAsset, 'id' | 'name' | 'source' | 'discoveredAt'>>,
  seenLapsed: string[] = [],
): Since | null {
  const t = lastVisit ? Date.parse(lastVisit) : Number.NaN
  if (Number.isNaN(t)) return null
  const fresh = systems.filter((s) => s.createdAt && Date.parse(s.createdAt) > t)
  const lapsed = systems.filter((s) => !seenLapsed.includes(s.id) && gates.get(s.id)?.checks.some((c) => c.stale))
  const found = discovered.filter((d) => Date.parse(d.discoveredAt) > t)
  if (!fresh.length && !lapsed.length && !found.length) return null
  return {
    parts: [
      fresh.length ? plural(fresh.length, 'new system', 'new systems') : '',
      lapsed.length ? `${plural(lapsed.length, 'monitoring check', 'monitoring checks')} lapsed` : '',
      found.length ? `${found.length} found by the agent` : '',
    ].filter(Boolean),
    rows: [
      ...fresh.map((s) => ({ key: `new:${s.id}`, label: s.name, detail: 'New system', href: `/systems/${s.id}` })),
      ...lapsed.map((s) => ({ key: `lapsed:${s.id}`, label: s.name, detail: 'Monitoring snapshot older than its cadence', href: `/systems/${s.id}` })),
      ...found.map((d) => ({ key: `found:${d.id}`, label: d.name, detail: `Found in ${d.source}` })),
    ],
  }
}

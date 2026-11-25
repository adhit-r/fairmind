'use client'

import type { CellState } from '@/components/ui/matrix'
import type { FrameworkCellCheck, FrameworkSystems } from '@/lib/api/hooks/useEstate'
import type { Journey, ReqStatus } from '@/lib/api/hooks/usePacks'

/** A requirement's state on the Frameworks screens: a gate cell, coverage at organisation level, or nothing tracked. */
export type ReqState = CellState | 'none'

/** Weakest first: the state "all systems" shows is the first one any system has. */
export const WEAKEST_FIRST: ReqState[] = ['fails', 'stale', 'open', 'planned', 'estimated', 'partial', 'attested', 'excluded', 'proven', 'atorg', 'none']
/** States that put a requirement on the work queue. */
export const NEEDS_WORK: ReqState[] = ['fails', 'stale', 'open']
/** The order the legend and the state bar read in. */
export const BAR_ORDER: ReqState[] = ['proven', 'partial', 'attested', 'excluded', 'estimated', 'planned', 'open', 'fails', 'stale', 'none']

export const STATE_LABEL: Record<ReqState, string> = {
  proven: 'Proven',
  partial: 'Partial',
  attested: 'Attested',
  excluded: 'Excluded',
  estimated: 'Estimated',
  planned: 'Planned',
  open: 'Open',
  fails: 'Failing',
  stale: 'Stale',
  atorg: 'Covered at organisation level',
  none: 'Not tracked',
}

export const weakest = (states: ReqState[]): ReqState =>
  states.reduce<ReqState>((w, s) => (WEAKEST_FIRST.indexOf(s) < WEAKEST_FIRST.indexOf(w) ? s : w), 'none')

/** Organisation-level coverage from installed packs, for a requirement no system's gate tracks. */
export const orgState = (status: ReqStatus): ReqState => (status === 'covered' || status === 'tested' ? 'atorg' : 'none')

export type CellOf = { state: CellState; checks: FrameworkCellCheck[] } | null

/** Per requirement key, the cell of each system (in `fw.systems` order). */
export function cellIndex(fw: FrameworkSystems | null): Map<string, CellOf[]> {
  return new Map((fw?.requirements ?? []).map((r) => [r.key, r.cells]))
}

/** The state a requirement shows: one system's cell, or the weakest across systems; organisation coverage when untracked. */
export function stateFor(cells: CellOf[] | undefined, status: ReqStatus, system: number | 'all'): ReqState {
  const picked = system === 'all' ? cells ?? [] : [cells?.[system] ?? null]
  const tracked = picked.filter((c): c is NonNullable<CellOf> => !!c).map((c) => c.state as ReqState)
  return tracked.length ? weakest(tracked) : orgState(status)
}

export const requirementHref = (fwKey: string, control: string, systemId?: string) =>
  `/frameworks/${encodeURIComponent(fwKey)}/${encodeURIComponent(control)}${systemId ? `?system=${encodeURIComponent(systemId)}` : ''}`

/** Every requirement of a journey in its standard's order, with its group. */
export function flatRequirements(journey: Journey) {
  return journey.groups.flatMap((g) => g.requirements.map((r) => ({ ...r, group: g.name })))
}

/** The state mark: shape and fill carry the state, so it reads without colour. */
export function Glyph({ state, size = 'sm', label }: { state: ReqState; size?: 'sm' | 'md' | 'lg'; label?: string }) {
  return label ? <i className={`fx-g ${size} s-${state}`} role="img" aria-label={label} /> : <i className={`fx-g ${size} s-${state}`} aria-hidden="true" />
}

export function Legend({ states = BAR_ORDER, extra }: { states?: ReqState[]; extra?: React.ReactNode }) {
  return (
    <p className="fx-legend" aria-label="Requirement states">
      {states.map((s) => (
        <span key={s}>
          <Glyph state={s} />
          {STATE_LABEL[s]}
        </span>
      ))}
      {extra}
    </p>
  )
}

/** Tracked requirements by state as one proportional bar, with the counts written out beside it. */
export function StateBar({ states }: { states: Partial<Record<ReqState, number>> }) {
  const parts = BAR_ORDER.filter((s) => (states[s] ?? 0) > 0).map((s) => ({ s, n: states[s] ?? 0 }))
  const total = parts.reduce((a, p) => a + p.n, 0)
  const words = parts.map((p) => `${p.n} ${STATE_LABEL[p.s].toLowerCase()}`).join(', ')
  return (
    <div>
      <div className="fx-bar" role="img" aria-label={words || 'Nothing tracked'}>
        {parts.map((p) => (
          <i key={p.s} className={`s-${p.s}`} style={{ flexGrow: p.n, flexBasis: 0 }} />
        ))}
      </div>
      <div className="fx-counts" aria-hidden="true">
        {parts.map((p) => (
          <span key={p.s}>
            <b>{p.n}</b> {STATE_LABEL[p.s].toLowerCase()}
          </span>
        ))}
        {total === 0 && <span>Nothing tracked yet</span>}
      </div>
    </div>
  )
}

/** The four states a person reads readiness in. The detailed states stay on the trace; these answer "how ready are we". */
export type Readiness = 'met' | 'progress' | 'attention' | 'notstarted'
export const READINESS_ORDER: Readiness[] = ['met', 'progress', 'attention', 'notstarted']
export const READINESS_LABEL: Record<Readiness, string> = { met: 'Met', progress: 'In progress', attention: 'Needs attention', notstarted: 'Not started' }
/** Met: proven by evidence, attested by a person, or excluded with a justification. Needs attention: failing or out of date. */
export const READINESS_OF: Record<ReqState, Readiness> = {
  proven: 'met', attested: 'met', excluded: 'met',
  partial: 'progress', estimated: 'progress', planned: 'progress', atorg: 'progress',
  fails: 'attention', stale: 'attention',
  open: 'notstarted', none: 'notstarted',
}

export function readinessCounts(states: Partial<Record<ReqState, number>>): Record<Readiness, number> {
  const out: Record<Readiness, number> = { met: 0, progress: 0, attention: 0, notstarted: 0 }
  for (const [s, n] of Object.entries(states)) out[READINESS_OF[s as ReqState] ?? 'notstarted'] += n ?? 0
  return out
}

export function ReadinessLegend() {
  return (
    <p className="fx-legend" aria-label="Readiness states">
      {READINESS_ORDER.map((r) => (
        <span key={r}>
          <i className={`fx-rk r-${r}`} aria-hidden="true" />
          {READINESS_LABEL[r]}
        </span>
      ))}
    </p>
  )
}

/** One bar in the four readiness states, with "X of N met" and the other counts written out. */
export function ReadinessBar({ counts }: { counts: Record<Readiness, number> }) {
  const total = READINESS_ORDER.reduce((a, r) => a + counts[r], 0)
  const words = `${counts.met} of ${total} met, ${counts.progress} in progress, ${counts.attention} need attention, ${counts.notstarted} not started`
  return (
    <div className="fx-ready">
      <div className="fx-rbar" role="img" aria-label={words}>
        {READINESS_ORDER.filter((r) => counts[r] > 0).map((r) => (
          <i key={r} className={`r-${r}`} style={{ flexGrow: counts[r], flexBasis: 0 }} />
        ))}
      </div>
      <div className="fx-counts" aria-hidden="true">
        <span><b>{counts.met} of {total}</b> met</span>
        {counts.progress > 0 && <span>{counts.progress} in progress</span>}
        {counts.attention > 0 && <span className="warn">{counts.attention} need attention</span>}
        {counts.notstarted > 0 && <span>{counts.notstarted} not started</span>}
      </div>
    </div>
  )
}

/** How a catalogue framework reads to a buyer: law, a standard you can certify against, guidance, or a security reference. */
export type FrameworkGroup = 'law' | 'cert' | 'guidance' | 'security'
export const GROUP_LABEL: Record<FrameworkGroup, string> = { law: 'Binding law', cert: 'Certifiable standard', guidance: 'Guidance', security: 'Security reference' }
export function groupOf(f: { type: string | null; binding: string | null }): FrameworkGroup {
  const type = (f.type || '').toLowerCase()
  const binding = (f.binding || '').toLowerCase()
  if (/\blaw\b|treaty|federal policy/.test(type) || binding.startsWith('binding')) return 'law'
  if (type.includes('certifiable') || binding.includes('certifiable') || binding.includes('star')) return 'cert'
  if (/taxonomy|security|threat|attack|adversary|secure development/.test(type)) return 'security'
  return 'guidance'
}

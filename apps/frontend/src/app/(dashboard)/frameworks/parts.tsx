'use client'

import type { CellState } from '@/components/ui/matrix'
import type { FrameworkCellCheck, FrameworkSystems } from '@/lib/api/hooks/useEstate'
import type { Journey, ReqStatus } from '@/lib/api/hooks/usePacks'

/** A requirement's state on the Frameworks screens: a gate cell, coverage at organisation level, or nothing tracked. */
export type ReqState = CellState | 'none'

/** Weakest first: the state "all systems" shows is the first one any system has. */
export const WEAKEST_FIRST: ReqState[] = ['fails', 'stale', 'open', 'planned', 'estimated', 'partial', 'attested', 'proven', 'atorg', 'none']
/** States that put a requirement on the work queue. */
export const NEEDS_WORK: ReqState[] = ['fails', 'stale', 'open']
/** The order the legend and the state bar read in. */
export const BAR_ORDER: ReqState[] = ['proven', 'partial', 'attested', 'estimated', 'planned', 'open', 'fails', 'stale', 'none']

export const STATE_LABEL: Record<ReqState, string> = {
  proven: 'Proven',
  partial: 'Partial',
  attested: 'Attested',
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

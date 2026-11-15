import type { PartKey, SystemChange } from '@/lib/api/hooks/useLifecycle'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'

export const PART_LABEL: Record<PartKey, string> = { data: 'Data', model: 'Model', tools: 'Prompts and tools', threshold: 'Threshold', use: 'Who it is used on', docs: 'Docs or owner' }

export type CellClass = 'proven' | 'attested' | 'open' | 'reopen'

const checkClass = (c: Pick<GateCheck, 'state'> & { reopenedBy?: number }): CellClass => (c.reopenedBy ? 'reopen' : c.state)

export type Column = { key: string; title: string; sub: string; tone: 'old' | 'live' | 'wait'; pill?: { label: string; material: boolean }; cells: Record<string, CellClass> }

/** One column per version: each change's snapshot of the gate before it, then the gate now. At most the last four. */
export function columns(changes: SystemChange[], checks: GateCheck[], approved: boolean): Column[] {
  const cols: Column[] = changes.map((ch, i) => ({
    key: `before-${ch.number}`,
    title: ch.fromVersion || (i === 0 ? 'First version' : `After change ${changes[i - 1].number}`),
    sub: 'Before change ' + ch.number,
    tone: 'old',
    pill: i === 0 ? undefined : { label: changes[i - 1].parts.map((p) => PART_LABEL[p]).join(', '), material: changes[i - 1].material },
    cells: Object.fromEntries(ch.gateBefore.map((c) => [c.key, c.state as CellClass])),
  }))
  const last = changes[changes.length - 1]
  const waiting = checks.some((c) => c.reopenedBy)
  cols.push({
    key: 'now',
    title: last?.toVersion || 'Now',
    sub: waiting ? 'Waiting on reopened checks' : approved ? 'Approved' : 'Current',
    tone: waiting ? 'wait' : 'live',
    pill: last ? { label: last.parts.map((p) => PART_LABEL[p]).join(', '), material: last.material } : undefined,
    cells: Object.fromEntries(checks.map((c) => [c.key, checkClass(c)])),
  })
  return cols.slice(-4)
}


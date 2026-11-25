import type { ResultStatus, RunWay, SystemFit } from '@/lib/api/hooks/usePacks'

/** How a stored evaluation result reads on screen. Static labels only. */
export const RESULT_WORD: Record<ResultStatus, string> = {
  passed: 'Passed',
  failed: 'Failed',
  insufficient: 'Not enough data',
  not_run: 'No result yet',
}
export const RESULT_COLOR: Record<ResultStatus, 'green' | 'red' | 'yellow' | 'gray'> = {
  passed: 'green',
  failed: 'red',
  insufficient: 'yellow',
  not_run: 'gray',
}

export const fmtWhen = (iso: string | null | undefined) => {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

type Ways = NonNullable<SystemFit['ways']>

/** The way a run page opens on: the asked one when it applies and is ready, else calling the system, then live runs, then the platform, then records FairMind holds, when set up, then files. */
export function defaultWay(ways: Ways, asked?: RunWay | null): RunWay | null {
  if (asked && ways.some((w) => w.way === asked && w.ready)) return asked
  for (const way of ['calls_system', 'live_runs', 'platform', 'fairmind_data'] as const) if (ways.some((w) => w.way === way && w.ready)) return way
  return ways.find((w) => w.way === 'files')?.way ?? ways[0]?.way ?? null
}

type Bounds = Array<{ count: number; bound: number }>
/** A pass stands when the 95% upper bound is within the limit (common.sampled); a zero limit is zero tolerance, which any count meets. */
export const proves = (bound: number, limit: number) => limit === 0 || bound <= limit
/** The smallest offered count that can prove the limit, else the largest; null when there is no limit to prove yet. */
export function presetFor(bounds: Bounds, limit: number | null): number | null {
  if (limit === null || Number.isNaN(limit) || bounds.length === 0) return null
  const sorted = [...bounds].sort((a, b) => a.count - b.count)
  return (sorted.find((b) => proves(b.bound, limit)) ?? sorted[sorted.length - 1]).count
}

export type Bucket = 'ready' | 'file' | 'setup' | 'other'
/** Where an evaluation sits for one system; null when FairMind cannot run it at all. */
export function bucketOf(row: SystemFit): Bucket | null {
  const ways = row.ways ?? []
  if (ways.length === 0) return null
  if (row.fit === 'other') return 'other'
  if (ways.some((w) => w.way !== 'files' && w.ready)) return 'ready'
  return ways.some((w) => w.way === 'files') ? 'file' : 'setup'
}
export function groupRows<T extends SystemFit>(rows: T[]): Record<Bucket, T[]> {
  const out: Record<Bucket, T[]> = { ready: [], file: [], setup: [], other: [] }
  for (const r of rows) {
    const b = bucketOf(r)
    if (b) out[b].push(r)
  }
  return out
}

/** How a run by this way is kept (evaluation_runs provenance): calling the system, FairMind's own agent, the platform or replaying live runs on the connection is measured live; files, records FairMind holds and live runs read alone are computed. Records FairMind holds keep the computed class but read as that, since nothing is uploaded. */
export const keptAs = (way: RunWay, live = false, replays = false) =>
  way === 'fairmind_data' ? 'Computed from FairMind records' : way === 'calls_system' || way === 'platform' || (live && way !== 'live_runs') || (replays && way === 'live_runs') ? 'Measured live' : 'Computed from upload'

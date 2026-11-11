import type { ResultStatus } from '@/lib/api/hooks/usePacks'

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

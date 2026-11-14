'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'

const SOURCES = {
  judge: { label: 'LLM judge', path: '/api/v1/bias/llm-judge' },
  advanced: { label: 'Advanced bias', path: '/api/v1/advanced-bias-detection' },
} as const

type Source = keyof typeof SOURCES

interface StoredAnalysis {
  id: string
  kind: string
  verdict: 'pass' | 'fail' | 'insufficient'
  severity: string | null
  createdAt: string
}

const VERDICT_TONE: Record<StoredAnalysis['verdict'], string> = {
  pass: 'text-green-700',
  fail: 'text-red-700',
  insufficient: 'text-amber-700',
}

/** The stored judge and advanced-bias results of one AI system, latest first. `refreshKey` reloads after a new run. */
export function StoredAnalyses({ systemId, sources, refreshKey = 0 }: { systemId: string; sources: Source[]; refreshKey?: string | number }) {
  const [rows, setRows] = useState<Array<StoredAnalysis & { source: Source }>>([])
  const [failed, setFailed] = useState(false)
  const key = sources.join(',')

  useEffect(() => {
    if (!systemId) return
    let live = true
    Promise.all(
      (key.split(',') as Source[]).map(async (source) => {
        const res = await apiClient.get<StoredAnalysis[]>(`${SOURCES[source].path}/systems/${encodeURIComponent(systemId)}/analyses`)
        if (!res.success || !res.data) throw new Error(res.error || 'Could not load stored analyses')
        return res.data.map((r) => ({ ...r, source }))
      })
    )
      .then((all) => {
        if (!live) return
        setFailed(false)
        setRows(all.flat().sort((a, b) => b.createdAt.localeCompare(a.createdAt)))
      })
      .catch(() => live && setFailed(true))
    return () => {
      live = false
    }
  }, [systemId, key, refreshKey])

  return (
    <div className="rounded-[14px] bg-white p-4 shadow-[var(--fm-shadow)] sm:col-span-2 xl:col-span-3">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--fm-ink3)]">Stored analyses</p>
      {failed ? (
        <p className="text-[12.5px] text-[var(--fm-ink2)]">Stored analyses could not be loaded.</p>
      ) : rows.length === 0 ? (
        <p className="text-[12.5px] text-[var(--fm-ink2)]">None stored for this system yet.</p>
      ) : (
        <ul className="divide-y divide-[var(--fm-line)]">
          {rows.map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-3 py-2 text-[13px]">
              <span className="text-[var(--fm-ink)]">
                {SOURCES[r.source].label}, {r.kind}
              </span>
              <span className="flex items-center gap-3 text-[var(--fm-ink2)]">
                <span className={`font-medium ${VERDICT_TONE[r.verdict]}`}>
                  {r.verdict}
                  {r.severity ? `, ${r.severity}` : ''}
                </span>
                <span>{new Date(r.createdAt).toLocaleString()}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

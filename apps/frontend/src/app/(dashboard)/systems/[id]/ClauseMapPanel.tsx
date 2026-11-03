'use client'

import { useState } from 'react'
import type { ClauseMap } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

const LEAD = 4
const STATE_WORD = { proven: 'proven', attested: 'attested', open: 'open' } as const

function Dot({ state }: { state: 'proven' | 'attested' | 'open' }) {
  return (
    <span
      aria-hidden="true"
      className={cn('inline-block h-2 w-2 shrink-0 rounded-full', state === 'proven' && 'bg-[#1f7a4d]', state === 'attested' && 'bg-[#a14d00]', state === 'open' && 'border border-[var(--fm-ink3)]')}
    />
  )
}

/** The release gate read clause by clause: which articles and controls each check speaks to, and how well. */
export function ClauseMapPanel({ map }: { map: ClauseMap }) {
  const [openKey, setOpenKey] = useState<string | null>(map.frameworks[0]?.key ?? null)
  const [showAll, setShowAll] = useState(false)
  const frameworks = showAll ? map.frameworks : map.frameworks.slice(0, LEAD)
  const rest = map.frameworks.length - LEAD
  if (map.frameworks.length === 0) return null

  return (
    <div className="grid min-w-0 gap-3 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
      <div>
        <div className="text-[13.5px] font-semibold">What the gate says per framework</div>
        <div className="text-[12px] text-[var(--fm-ink2)]">Each gate check maps to the clauses it satisfies, supports or aligns with. A clause is as good as its best-evidenced check.</div>
      </div>
      <div className="grid gap-1.5">
        {frameworks.map((fw) => {
          const open = openKey === fw.key
          const evidenced = fw.counts.proven + fw.counts.attested
          return (
            <div key={fw.key} className="rounded-[10px] border border-[var(--fm-line)] bg-white">
              <button type="button" onClick={() => setOpenKey(open ? null : fw.key)} className="flex w-full items-center gap-3 px-3 py-2 text-left">
                <span className="min-w-0 flex-1 truncate text-[13px] font-medium">{fw.name}</span>
                <span className="text-[12px] tabular-nums text-[var(--fm-ink2)]">
                  {evidenced} of {fw.counts.total} clause{fw.counts.total === 1 ? '' : 's'} evidenced
                  {fw.counts.attested > 0 && <span className="text-[var(--fm-ink3)]"> ({fw.counts.attested} attested)</span>}
                </span>
                <span className="flex h-1.5 w-24 overflow-hidden rounded-full bg-[var(--fm-line)]" aria-hidden="true">
                  <span className="bg-[#1f7a4d]" style={{ width: `${(fw.counts.proven / Math.max(fw.counts.total, 1)) * 100}%` }} />
                  <span className="bg-[#a14d00]" style={{ width: `${(fw.counts.attested / Math.max(fw.counts.total, 1)) * 100}%` }} />
                </span>
                <span className="text-[11px] text-[var(--fm-ink3)]">{open ? 'Hide' : 'Show'}</span>
              </button>
              {open && (
                <ul className="grid gap-1 border-t border-[var(--fm-line)] px-3 py-2">
                  {fw.clauses.map((c) => (
                    <li key={c.key} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-baseline gap-x-2 text-[12.5px]">
                      <Dot state={c.state} />
                      <span className="min-w-0">
                        <span className="font-medium">{c.control}</span> <span className="text-[var(--fm-ink2)]">{c.title}</span>
                      </span>
                      <span className="text-right text-[11.5px] text-[var(--fm-ink3)]">
                        {STATE_WORD[c.state]} · {c.checks.map((ch) => `${ch.label} ${ch.relation.toLowerCase()}`).join(', ')}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </div>
      {rest > 0 && (
        <button type="button" onClick={() => setShowAll((v) => !v)} className="justify-self-start text-[12.5px] font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">
          {showAll ? 'Show the four lead frameworks only' : `Show ${rest} more framework${rest === 1 ? '' : 's'}`}
        </button>
      )}
    </div>
  )
}

'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Matrix, type MatrixGroup, type MatrixProps } from '@/components/ui/matrix'
import { useJourney, type Journey, type Resource } from '@/lib/api/hooks/usePacks'
import type { ClauseMap } from '@/lib/api/hooks/useSystemFile'
import { ORG_BLANK } from '../../frameworks/[key]/grid'

const CAP = 12

/** Loads one framework's journey and hands it up, so a page can hold one per confirmed framework. */
export function JourneyFeed({ fw, onChange }: { fw: string; onChange: (fw: string, r: Resource<Journey>) => void }) {
  const { data, loading, error, reload } = useJourney(fw)
  useEffect(() => onChange(fw, { data, loading, error, reload }), [fw, data, loading, error, reload, onChange])
  return null
}

/** Requirements of the confirmed frameworks this system leaves open or fails: failures first, then those the organisation does not hold, capped. */
export function leavesOpen(clauseMap: ClauseMap | null, journeys: Journey[]): { n: number; groups: MatrixGroup[]; more: { n: number; href: string } } {
  // An unscoped map (no confirmed frameworks) is the whole catalogue: nothing to leave open yet.
  const fws = clauseMap?.scoped ? clauseMap.frameworks : []
  const org = new Map(journeys.map((j) => [j.key, new Map(j.groups.flatMap((g) => g.requirements.map((r) => [r.key, r.status === 'covered' || r.status === 'tested'])))]))
  const all = fws.flatMap((f, fi) =>
    f.clauses
      .filter((c) => c.cell === 'open' || c.cell === 'fails')
      .map((c, i) => {
        const held = org.get(f.key)?.get(c.key)
        return { f, fi, i, c, fails: c.cell === 'fails', held: !!held, known: org.has(f.key) }
      }),
  )
  const ranked = [...all].sort((a, b) => +b.fails - +a.fails || +a.held - +b.held || a.fi - b.fi || a.i - b.i)
  const shown = ranked.slice(0, CAP).sort((a, b) => a.fi - b.fi || +b.fails - +a.fails || a.i - b.i)
  const hidden = ranked.slice(CAP)
  const groups: MatrixGroup[] = []
  for (const r of shown) {
    let g = groups[groups.length - 1]
    if (g?.label !== r.f.name) groups.push((g = { label: r.f.name, rows: [] }))
    g.rows.push({
      key: r.c.key,
      code: r.c.control,
      label: r.c.title,
      title: [r.c.control, r.c.title, r.c.group].filter(Boolean).join(' · '),
      cells: [r.c.cell, r.held ? 'atorg' : null],
      blank: [undefined, r.known ? ORG_BLANK : 'Organisation status not loaded'],
    })
  }
  const fw = (hidden[0] ?? all[0])?.f.key ?? ''
  return { n: all.length, groups, more: { n: hidden.length, href: `/frameworks/${encodeURIComponent(fw)}` } }
}

const COLS: MatrixProps['colGroups'] = [{ label: '', cols: [{ key: 'state', label: 'This system' }, { key: 'org', label: 'Organisation', title: 'Organisation packs' }] }]

/** What a release decision leaves open, collapsed until asked for; organisation status loads on show. */
export function LeavesOpen({ clauseMap }: { clauseMap: ClauseMap | null }) {
  const [shown, setShown] = useState(false)
  const [feeds, setFeeds] = useState<Record<string, Journey>>({})
  const onFeed = useCallback((fw: string, r: Resource<Journey>) => r.data && setFeeds((f) => ({ ...f, [fw]: r.data! })), [])
  const view = useMemo(() => leavesOpen(clauseMap, Object.values(feeds)), [clauseMap, feeds])
  if (!view.n) return null
  return (
    <div className="mt-3">
      <p className="text-[12.5px]">
        {view.n} requirement{view.n === 1 ? '' : 's'} left open ·{' '}
        <button type="button" aria-expanded={shown} onClick={() => setShown(!shown)} className="font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">
          {shown ? 'Hide' : 'Show'}
        </button>
      </p>
      {shown && (
        <>
          {clauseMap?.frameworks.map((f) => <JourneyFeed key={f.key} fw={f.key} onChange={onFeed} />)}
          <div className="mt-2">
            <Matrix id="leaves" head="Requirement" colGroups={COLS} groups={view.groups} more={view.more} legendLabels={{ atorg: 'covered by organisation packs' }} />
          </div>
        </>
      )}
    </div>
  )
}

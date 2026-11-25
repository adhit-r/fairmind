'use client'

import { Text } from '@astryxdesign/core/Text'
import Link from 'next/link'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { detail, SourceMark } from '@/astryx/DiscoveryParts'
import { KIND_LABEL, SOURCE_LABEL, type DiscoveredAsset } from '@/astryx/data/discovery'

export type Show = 'all' | 'waiting' | 'registered' | 'ignored'
export const SHOWS: Show[] = ['all', 'waiting', 'registered', 'ignored']

const date = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })

/** Where a found item came from, in the words of its source: the repository for GitHub, else the source's name. */
function origin(a: DiscoveredAsset): string {
  const m = a.metadata ?? {}
  return (m.repo as string) || (m.workspace as string) || (m.project as string) || SOURCE_LABEL[a.source] || a.source
}

/** Every item discovery found, whatever was decided about it, with what happened and a link to the system it became. */
export function FoundList({
  discovered,
  waiting,
  show,
  onShow,
  children,
}: {
  discovered: DiscoveredAsset[]
  waiting: number
  show: Show
  onShow: (s: Show) => void
  /** What the Waiting filter shows: the review list and panel, where decisions are made. */
  children: React.ReactNode
}) {
  const { systems } = useSystemContext()
  const nameOf = new Map(systems.map((s) => [s.id, s.name]))
  const registered = discovered.filter((a) => a.status === 'promoted')
  const ignored = discovered.filter((a) => a.status === 'ignored')
  const rows = show === 'registered' ? registered : show === 'ignored' ? ignored : discovered
  const newest = [...rows].sort((a, b) => b.discoveredAt.localeCompare(a.discoveredAt))

  return (
    <div className="dv-found">
      <SegmentedControl label="Show" value={show} onChange={(v) => onShow(v as Show)} size="sm">
        <SegmentedControlItem label={`All ${discovered.length}`} value="all" />
        <SegmentedControlItem label={`Waiting for you ${waiting}`} value="waiting" />
        <SegmentedControlItem label={`Registered ${registered.length}`} value="registered" />
        <SegmentedControlItem label={`Ignored ${ignored.length}`} value="ignored" />
      </SegmentedControl>

      {show === 'waiting' ? (
        children
      ) : newest.length === 0 ? (
        <section className="fm-card">
          <Text color="secondary">{show === 'ignored' ? 'Nothing ignored.' : show === 'registered' ? 'Nothing registered from discovery yet.' : 'Nothing found yet. Connect a source and what it finds lands here.'}</Text>
        </section>
      ) : (
        <div className="dv-found-wrap">
          <table className="dv-found-table">
            <thead>
              <tr>
                <th scope="col">Found</th>
                <th scope="col">Why it counts as AI</th>
                <th scope="col">Source</th>
                <th scope="col">When</th>
                <th scope="col">What happened</th>
              </tr>
            </thead>
            <tbody>
              {newest.map((a) => {
                const system = a.systemId ? nameOf.get(a.systemId) : undefined
                const merged = a.status === 'promoted' && system && system !== a.name
                return (
                  <tr key={a.id}>
                    <td>
                      <b>{a.name}</b>
                      <br />
                      <Text type="supporting">
                        {KIND_LABEL[a.kind] ?? a.kind} · suggested {a.suggestedTier} risk
                      </Text>
                    </td>
                    <td>{detail(a) || <Text type="supporting">No detail recorded</Text>}</td>
                    <td>
                      <span className="dv-found-src">
                        <SourceMark kind={a.source} size="sm" />
                        <span>{origin(a)}</span>
                      </span>
                    </td>
                    <td>{date(a.discoveredAt)}</td>
                    <td>
                      {a.status === 'promoted' ? (
                        <>
                          <span className="dv-chip ok">{merged ? 'Merged' : 'Registered'}</span>
                          <br />
                          {a.systemId && <Link href={`/systems/${a.systemId}`}>{merged ? `Into ${system}` : `Open ${system ?? 'the system'}`}</Link>}
                        </>
                      ) : a.status === 'ignored' ? (
                        <span className="dv-chip">Ignored</span>
                      ) : (
                        <>
                          <span className="dv-chip wait">Waiting for you</span>
                          <br />
                          <button type="button" className="dv-linkbtn" onClick={() => onShow('waiting')}>Review it</button>
                        </>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

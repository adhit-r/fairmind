'use client'

import '@/astryx/pages/evaluations.css'
import Link from 'next/link'
import { Fragment, useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Divider } from '@astryxdesign/core/Divider'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { VStack, HStack } from '@astryxdesign/core/Layout'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useEvaluations, type EvaluationRow, type ResultStatus } from '@/lib/api/hooks/usePacks'
import { RESULT_COLOR, RESULT_WORD, fmtWhen } from '@/astryx/data/evaluations'

/** Pillar labels as the catalogue names them; a pillar not listed here shows as it comes. */
const PILLAR_ORDER = ['GOVERN', 'EVALUATE', 'SECURE', 'COMPLY']
const sentence = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

function ResultToken({ row }: { row: EvaluationRow }) {
  if (!row.results) return <Text type="supporting" color="secondary">Not recorded</Text>
  const status: ResultStatus = row.results.status
  const n = row.results.systems.length
  return (
    <VStack gap={1}>
      <Token size="sm" color={RESULT_COLOR[status]} label={RESULT_WORD[status]} />
      {n > 0 && <Text type="supporting" color="secondary">{n} system{n === 1 ? '' : 's'}</Text>}
    </VStack>
  )
}

function Panel({ row, onClose }: { row: EvaluationRow; onClose: () => void }) {
  const systems = row.results?.systems ?? []
  return (
    <aside className="fm-ev-panel" aria-label="Evaluation details">
      <VStack gap={3}>
        <HStack gap={2} hAlign="between" vAlign="center">
          <span className="fm-ev-id">{row.id}</span>
          <Button label="Close" variant="ghost" size="sm" onClick={onClose} />
        </HStack>
        <Heading level={2}>{row.name}</Heading>
        <MetadataList columns="single" label={{ position: 'start', width: 96 }}>
          <MetadataListItem label="Pillar">{sentence(row.pillar)}</MetadataListItem>
          <MetadataListItem label="Measures">{row.measures || 'Not stated'}</MetadataListItem>
          <MetadataListItem label="Metric">{row.metric || 'Not stated'}</MetadataListItem>
          <MetadataListItem label="Threshold">{row.threshold || 'Not stated'}</MetadataListItem>
          <MetadataListItem label="Applies to">{row.appliesTo || 'Not stated'}</MetadataListItem>
          <MetadataListItem label="Pack">{row.pack.name}{row.installed ? '' : ' (not installed)'}</MetadataListItem>
          <MetadataListItem label="Engine">
            <Token size="sm" color={row.runnable ? 'green' : 'gray'} label={row.runnable ? 'Runnable' : 'Not built yet'} />
          </MetadataListItem>
        </MetadataList>
        <Button label={row.runnable ? 'Open to run' : 'Open details'} variant={row.runnable ? 'primary' : 'secondary'} href={`/compliance/evaluations/${row.id}`} />
        <Divider />
        <Heading level={3}>Results by system</Heading>
        {!row.results ? (
          <Text type="supporting" color="secondary">FairMind does not record results for this evaluation yet.</Text>
        ) : systems.length === 0 ? (
          <Text type="supporting" color="secondary">No system has a result for this evaluation yet.</Text>
        ) : (
          <div>
            {systems.map((s) => (
              <div className="fm-ev-sys" key={`${s.systemId}-${s.evidenceId}`}>
                <div className="fm-ev-sys-top">
                  <Link href={`/systems/${s.systemId}`}>{s.systemName}</Link>
                  <Token size="sm" color={RESULT_COLOR[s.status]} label={RESULT_WORD[s.status]} />
                </div>
                {s.detail && <Text type="supporting" color="secondary">{s.detail}</Text>}
                <Text type="supporting" color="secondary">
                  Evidence <span className="fm-ev-id">{s.evidenceId}</span>
                  {fmtWhen(s.at) ? `, ${fmtWhen(s.at)}` : ''}
                </Text>
              </div>
            ))}
          </div>
        )}
      </VStack>
    </aside>
  )
}

export default function EvaluationsPage() {
  const evals = useEvaluations()
  const [q, setQ] = useState('')
  const [pillar, setPillar] = useState('all')
  const [engine, setEngine] = useState('all')
  const [pack, setPack] = useState('all')
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set())
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const rows = evals.data ?? []
  const counts = useMemo(
    () => ({
      total: rows.length,
      runnable: rows.filter((r) => r.runnable).length,
      installed: rows.filter((r) => r.installed).length,
      withResults: rows.filter((r) => (r.results?.systems.length ?? 0) > 0).length,
    }),
    [rows],
  )
  const pillars = useMemo(() => {
    const found = [...new Set(rows.map((r) => r.pillar))]
    return [...PILLAR_ORDER.filter((p) => found.includes(p)), ...found.filter((p) => !PILLAR_ORDER.includes(p)).sort()]
  }, [rows])

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return rows.filter(
      (r) =>
        (pillar === 'all' || r.pillar === pillar) &&
        (engine === 'all' || (engine === 'runnable' ? r.runnable : !r.runnable)) &&
        (pack === 'all' || r.installed) &&
        (!needle || `${r.id} ${r.name} ${r.measures} ${r.appliesTo}`.toLowerCase().includes(needle)),
    )
  }, [rows, q, pillar, engine, pack])

  const groups = pillars.map((p) => ({ pillar: p, rows: filtered.filter((r) => r.pillar === p) })).filter((g) => g.rows.length > 0)
  const selected = rows.find((r) => r.id === selectedId) ?? null
  const toggle = (p: string) =>
    setCollapsed((prev) => {
      const n = new Set(prev)
      if (n.has(p)) n.delete(p)
      else n.add(p)
      return n
    })

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Evaluations</Heading>
          <Text color="secondary">
            {evals.loading && !evals.data
              ? 'Loading the evaluation catalogue.'
              : `${counts.total} evaluations. ${counts.runnable} can run today, ${counts.installed} are in installed packs, ${counts.withResults} have results on at least one system.`}
          </Text>
        </VStack>

        {evals.error && (
          <Banner
            status="error"
            title="The evaluations could not be loaded"
            description={evals.error}
            endContent={<Button label="Try again" size="sm" variant="secondary" onClick={evals.reload} />}
          />
        )}

        {evals.loading && !evals.data ? (
          <VStack gap={2}>
            <Skeleton height={40} />
            <Skeleton height={220} />
          </VStack>
        ) : evals.data ? (
          <>
            <div className="fm-ev-filters">
              <div className="fm-ev-search">
                <TextInput label="Search" value={q} onChange={setQ} />
              </div>
              <SegmentedControl label="Pillar" value={pillar} onChange={setPillar} size="sm">
                <SegmentedControlItem label="All" value="all" />
                {pillars.map((p) => (
                  <SegmentedControlItem key={p} label={sentence(p)} value={p} />
                ))}
              </SegmentedControl>
              <SegmentedControl label="Engine" value={engine} onChange={setEngine} size="sm">
                <SegmentedControlItem label="All" value="all" />
                <SegmentedControlItem label="Runnable" value="runnable" />
                <SegmentedControlItem label="Not built yet" value="not" />
              </SegmentedControl>
              <SegmentedControl label="Packs" value={pack} onChange={setPack} size="sm">
                <SegmentedControlItem label="All" value="all" />
                <SegmentedControlItem label="Installed" value="installed" />
              </SegmentedControl>
            </div>

            {groups.length === 0 ? (
              <EmptyState title="No matching evaluations" description="Change the search or clear a filter." isCompact />
            ) : (
              <div className={`fm-ev-split${selected ? ' has-panel' : ''}`}>
                <div className="fm-ev-wrap">
                  <table className="fm-ev-table">
                    <thead>
                      <tr>
                        <th scope="col">Evaluation</th>
                        <th scope="col">Measures</th>
                        <th scope="col">Metric and threshold</th>
                        <th scope="col">Engine</th>
                        <th scope="col">Latest result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {groups.map((g) => {
                        const open = !collapsed.has(g.pillar)
                        return (
                          <Fragment key={g.pillar}>
                            <tr className="fm-ev-group">
                              <td colSpan={5}>
                                <button type="button" aria-expanded={open} onClick={() => toggle(g.pillar)}>
                                  {open ? <ChevronDown size={16} aria-hidden /> : <ChevronRight size={16} aria-hidden />}
                                  {sentence(g.pillar)}
                                  <span className="fm-ev-muted" style={{ fontWeight: 400 }}>
                                    {g.rows.length} evaluations, {g.rows.filter((r) => r.runnable).length} runnable
                                  </span>
                                </button>
                              </td>
                            </tr>
                            {open &&
                              g.rows.map((r) => (
                                <tr key={r.id} className={`fm-ev-row${r.id === selectedId ? ' is-selected' : ''}`} onClick={() => setSelectedId(r.id)}>
                                  <td>
                                    <div className="fm-ev-name">
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          setSelectedId(r.id)
                                        }}
                                      >
                                        {r.name}
                                      </button>
                                      <span className="fm-ev-id">{r.id}</span>
                                    </div>
                                  </td>
                                  <td>{r.measures || <span className="fm-ev-muted">Not stated</span>}</td>
                                  <td>
                                    <div className="fm-ev-name">
                                      <span>{r.metric || <span className="fm-ev-muted">Not stated</span>}</span>
                                      {r.threshold && <span className="fm-ev-muted">{r.threshold}</span>}
                                    </div>
                                  </td>
                                  <td>
                                    <Token size="sm" color={r.runnable ? 'green' : 'gray'} label={r.runnable ? 'Runnable' : 'Not built yet'} />
                                  </td>
                                  <td>
                                    <ResultToken row={r} />
                                  </td>
                                </tr>
                              ))}
                          </Fragment>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                {selected && <Panel row={selected} onClose={() => setSelectedId(null)} />}
              </div>
            )}
          </>
        ) : null}
      </VStack>
    </div>
  )
}

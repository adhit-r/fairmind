'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Empty, ErrorNote, Loading, ReqPill } from '@/components/packs/parts'
import { CellDrawer, CellMeaning, classLabel, DrawerBlock, Matrix, type Cell, type MatrixGroup } from '@/components/ui/matrix'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useJourney, type Journey } from '@/lib/api/hooks/usePacks'
import type { ClauseMap } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'
import { NOT_TRACKED, ORG_BLANK, STRENGTH, type GridBase } from '../../frameworks/[key]/grid'

const SEG = 'inline-flex max-w-full overflow-x-auto rounded-full border border-[var(--fm-line)] bg-white p-0.5'
const SEG_ITEM = 'inline-flex h-7 flex-none items-center whitespace-nowrap rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]'
const SEG_ON = 'bg-[var(--fm-ink)] text-white hover:text-white'

/** The strongest crosswalk relation among the workflows of one pack; 0 when none draws. */
export const bestRelation = (workflows: Journey['groups'][number]['requirements'][number]['workflows'], pack: string): Cell =>
  (Math.max(0, ...workflows.filter((w) => w.pack === pack).map((w) => STRENGTH[w.relation] ?? 0)) as 0 | 1 | 2 | 3) || null

/** One framework's requirements for one system: Org, one column per installed pack, then this system's state. */
export function requirementsGrid(journey: Journey, clauseMap: ClauseMap | null): GridBase {
  const packs = journey.steps.filter((s) => s.installed)
  const clauses = new Map((clauseMap?.frameworks.find((f) => f.key === journey.key)?.clauses ?? []).map((c) => [c.key, c]))
  const groups: MatrixGroup[] = journey.groups.map((g) => ({
    label: g.name,
    rows: g.requirements.map((r) => {
      const clause = clauses.get(r.key)
      return {
        key: r.key,
        code: r.control,
        label: r.title,
        title: `${r.control} · ${r.title} · ${g.name}`,
        cells: [r.status === 'covered' || r.status === 'tested' ? 'atorg' : null, ...packs.map((p) => bestRelation(r.workflows, p.pack)), clause?.cell ?? null],
        blank: [ORG_BLANK, ...packs.map(() => 'No workflow of this pack maps here'), clause ? 'No state recorded for this system' : NOT_TRACKED],
      }
    }),
  }))
  return {
    head: 'Requirement',
    colGroups: [
      { label: 'Org', cols: [{ key: 'org', label: 'Organisation', title: 'Organisation packs' }] },
      ...(packs.length ? [{ label: 'Packs', cols: packs.map((p) => ({ key: p.pack, label: p.name, title: `${p.name} · installed` })) }] : []),
      { label: 'This system', cols: [{ key: 'state', label: 'State', title: 'This system' }] },
    ],
    groups,
    legendLabels: { atorg: 'covered by organisation packs' },
  }
}

/** The system's requirements, one confirmed framework at a time. */
export function RequirementsTab({ confirmed, clauseMap }: { confirmed: Array<{ key: string; name: string }>; clauseMap: ClauseMap | null }) {
  const [picked, setPicked] = useState<string | undefined>(confirmed[0]?.key)
  const fw = confirmed.some((f) => f.key === picked) ? picked : confirmed[0]?.key
  const journey = useJourney(fw)
  const grid = useMemo(() => (journey.data ? requirementsGrid(journey.data, clauseMap) : null), [journey.data, clauseMap])
  const [cell, setCell] = useState<{ row: string; col: string } | null>(null)
  const short = shortFrameworkName(confirmed.find((f) => f.key === fw)?.name ?? fw ?? '')

  const found = (() => {
    if (!cell || !journey.data) return null
    for (const g of journey.data.groups) {
      const r = g.requirements.find((x) => x.key === cell.row)
      if (r) return { r, group: g.name }
    }
    return null
  })()
  const clause = found ? clauseMap?.frameworks.find((f) => f.key === fw)?.clauses.find((c) => c.key === found.r.key) : undefined
  const pack = cell && journey.data?.steps.find((s) => s.pack === cell.col)

  if (!confirmed.length) {
    return (
      <section className="fm-card p-[18px]" aria-label="Requirements">
        <Empty>No framework is confirmed for this system yet. Confirm tier and rules in the Onboard stage of the Journey tab.</Empty>
      </section>
    )
  }

  return (
    <section className="fm-card overflow-hidden" aria-label={`${short} requirements`}>
      <div className="flex flex-wrap items-center gap-2 px-[18px] pb-3 pt-4">
        <h2 className="text-[15px] font-semibold tracking-[-0.01em]">Requirements</h2>
        {grid && <span className="text-[12px] tabular-nums text-[var(--fm-ink3)]">{grid.groups.reduce((n, g) => n + g.rows.length, 0)}</span>}
        {confirmed.length > 1 && (
          <nav aria-label="Framework" className={cn(SEG, 'ml-auto')}>
            {confirmed.map((f) => (
              <button key={f.key} type="button" onClick={() => setPicked(f.key)} aria-pressed={f.key === fw} className={cn(SEG_ITEM, f.key === fw && SEG_ON)} title={f.name}>
                {shortFrameworkName(f.name)}
              </button>
            ))}
          </nav>
        )}
      </div>
      {journey.loading ? (
        <div className="px-[18px] pb-[18px]">
          <Loading label={`Loading ${short}`} />
        </div>
      ) : journey.error ? (
        <div className="px-[18px] pb-[18px]">
          <ErrorNote message={journey.error} onRetry={journey.reload} />
        </div>
      ) : grid ? (
        <Matrix id="sysreq" {...grid} onCell={(row, col) => setCell({ row, col })} />
      ) : null}

      <CellDrawer open={!!found} onClose={() => setCell(null)} label={found ? `${short} ${found.r.control}` : short} title={found?.r.title ?? ''} sub={found?.group}>
        {found && cell?.col === 'org' && (
          <DrawerBlock label="Organisation">
            <CellMeaning cell={found.r.status === 'covered' || found.r.status === 'tested' ? 'atorg' : null} labels={grid?.legendLabels} />
            <span>
              <ReqPill status={found.r.status} />
            </span>
          </DrawerBlock>
        )}
        {found && pack && (
          <DrawerBlock label={pack.name}>
            <CellMeaning cell={bestRelation(found.r.workflows, pack.pack)} />
            {found.r.workflows
              .filter((w) => w.pack === pack.pack)
              .map((w) => (
                <span key={w.id}>
                  {w.name} <span className="text-[var(--fm-ink3)]">· {w.relation}</span>
                </span>
              ))}
          </DrawerBlock>
        )}
        {found && cell?.col === 'state' && (
          <>
            <DrawerBlock label="This system">
              <CellMeaning cell={clause?.cell ?? null} />
            </DrawerBlock>
            <DrawerBlock label="Release checks behind it">
              {clause?.checks.length ? (
                clause.checks.map((x) => (
                  <div key={x.check} className="grid gap-0.5">
                    <span>
                      <b className="font-semibold">{x.label}</b> <span className="text-[var(--fm-ink2)]">· {x.relation}</span>
                    </span>
                    <span className="text-[12px] text-[var(--fm-ink2)]">
                      {x.evidenceClass ? classLabel(x.evidenceClass) : 'Nothing current on file'} · <span className="font-mono">{x.confidence.toFixed(2)}</span>
                    </span>
                  </div>
                ))
              ) : (
                <span className="text-[var(--fm-ink2)]">{NOT_TRACKED}</span>
              )}
            </DrawerBlock>
          </>
        )}
        {fw && (
          <Link href={`/frameworks/${encodeURIComponent(fw)}`} className="mt-auto self-start text-[12.5px] text-[var(--fm-ink2)] underline-offset-2 hover:underline">
            Open {short} for every system
          </Link>
        )}
      </CellDrawer>
    </section>
  )
}

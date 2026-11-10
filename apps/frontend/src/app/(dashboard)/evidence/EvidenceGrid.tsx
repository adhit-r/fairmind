'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { CommandBar } from '@/components/layout/CommandBar'
import { Empty, ErrorNote, Loading } from '@/components/packs/parts'
import { CellDrawer, CellMeaning, classLabel, DrawerBlock, Matrix } from '@/components/ui/matrix'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useControls, useEstateGates } from '@/lib/api/hooks/useEstate'
import { useEvidencePacks } from '@/lib/api/hooks/useEvidencePacks'
import { useJourney } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'
import { confirmedFrameworks } from '../frameworks/[key]/grid'
import { evidenceGrid } from './grid'
import { EvidenceDemo } from '@/components/stageshow/EvidenceDemo'
import { Illustration } from '@/components/stageshow/fm'

const SEG = 'inline-flex rounded-full border border-[var(--fm-line)] bg-white p-0.5'
const SEG_ITEM = 'inline-flex h-7 items-center whitespace-nowrap rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]'
const SEG_ON = 'bg-[var(--fm-ink)] text-white hover:text-white'
const LINK = 'font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline'
export const LIBRARY_HREF = '/evidence?view=artifacts'
const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`

/** Grid | Library: the Evidence page's one switch. */
export function EvidenceSeg({ grid }: { grid: boolean }) {
  return (
    <nav aria-label="Evidence layout" className={SEG}>
      <Link href="/evidence" className={cn(SEG_ITEM, grid && SEG_ON)} aria-current={grid ? 'page' : undefined}>
        Grid
      </Link>
      <Link href={LIBRARY_HREF} className={cn(SEG_ITEM, !grid && SEG_ON)} aria-current={!grid ? 'page' : undefined}>
        Library
      </Link>
    </nav>
  )
}

/** Every evidence item a release check reads, by system: its proof, and how far it reaches into each framework. */
export function EvidenceGrid() {
  const router = useRouter()
  const { systems, loading: systemsLoading } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const gatesRes = useEstateGates()
  const controls = useControls()
  const { create } = useEvidencePacks()
  const [cell, setCell] = useState<{ row: string; col: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const grid = useMemo(() => {
    if (!gatesRes.data || !controls.data) return null
    const gates = new Map(gatesRes.data.map((g) => [g.systemId, g]))
    const confirmed = new Map(real.map((s) => [s.id, confirmedFrameworks([s])]))
    const g = evidenceGrid(real, gates, controls.data, confirmed)
    for (const cg of g.matrix.colGroups) if (cg.label === 'Frameworks') cg.cols = cg.cols.map((c) => ({ ...c, label: shortFrameworkName(c.label) }))
    return g
  }, [gatesRes.data, controls.data, real])

  const picked = cell && grid ? grid.find(cell.row) : null
  const row = picked ? grid?.matrix.groups.flatMap((g) => g.rows).find((r) => r.key === cell?.row) : undefined
  const fw = cell && cell.col !== 'state' ? grid?.frameworks.find((f) => f.key === cell.col) : undefined
  const journey = useJourney(fw?.key)
  const titles = useMemo(() => new Map((journey.data?.groups ?? []).flatMap((g) => g.requirements.map((r) => [r.key, r.title]))), [journey.data])

  const exportPack = async () => {
    if (!grid) return
    setBusy(true)
    setExportError(null)
    const res = await create({ title: 'Evidence inspection pack', frameworks: grid.frameworks.map((f) => f.key), systemIds: grid.systemIds })
    setBusy(false)
    if (res.success && res.data) router.push(`/evidence/packs/${res.data.id}`)
    else setExportError(res.error || 'Could not create the inspection pack')
  }

  const loading = systemsLoading || gatesRes.loading || controls.loading
  const error = gatesRes.error || controls.error
  const n = grid?.items ?? 0
  const m = grid?.systemIds.length ?? 0

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      <CommandBar
        stage="assess"
        title={grid ? `${plural(n, 'evidence item')} across ${plural(m, 'system')}` : 'Evidence'}
        reason="Every record a release check reads, and the framework requirements its control reaches"
        primary={{ label: busy ? 'Exporting' : 'Export for inspection', onClick: exportPack, busy, disabled: !grid || !n || !grid.frameworks.length }}
      />
      {exportError && <ErrorNote message={exportError} />}

      <section className="fm-card overflow-hidden" aria-label="Evidence">
        <div className="flex items-center gap-2 px-[18px] pb-3 pt-4">
          <EvidenceSeg grid />
        </div>
        {loading ? (
          <div className="px-[18px] pb-[18px]">
            <Loading label="Loading evidence" />
          </div>
        ) : error ? (
          <div className="px-[18px] pb-[18px]">
            <ErrorNote
              message={error}
              onRetry={() => {
                gatesRes.reload()
                controls.reload()
              }}
            />
          </div>
        ) : !real.length ? (
          <div className="px-[18px] pb-[18px]">
            <Empty>
              No AI system registered yet.{' '}
              <Link className={LINK} href="/onboard">
                Register a system
              </Link>
            </Empty>
          </div>
        ) : grid && !n ? (
          <div className="px-[18px] pb-[18px]">
            <Illustration className="mx-auto mb-4 max-w-[440px]" label="A sealed evidence item: a measured fairness run mapped to an EU AI Act article, in front of the evidence list">
              <EvidenceDemo />
            </Illustration>
            <Empty>
              No release check has read an evidence record yet.{' '}
              <Link className={LINK} href={LIBRARY_HREF}>
                Open the Library
              </Link>
            </Empty>
          </div>
        ) : grid ? (
          <>
            <Matrix id="evidence" {...grid.matrix} onCell={(row, col) => setCell({ row, col })} />
            <div className="border-t border-[var(--fm-line)] px-[18px] py-2.5 text-[12px] tabular-nums text-[var(--fm-ink2)]">
              {plural(n, 'item')} read by release checks ·{' '}
              <Link className={LINK} href={LIBRARY_HREF}>
                Library
              </Link>
            </div>
          </>
        ) : null}
      </section>

      <CellDrawer
        open={!!picked}
        onClose={() => setCell(null)}
        label={picked ? `${picked.system.name} · ${picked.control}` : 'Evidence'}
        title={row?.label ?? ''}
        sub={picked?.check.evidenceClass ? `${classLabel(picked.check.evidenceClass)} · ${picked.check.confidence.toFixed(2)}` : undefined}
      >
        {picked && (
          <DrawerBlock label="Proof">
            <CellMeaning cell={row?.cells[0] ?? null} />
          </DrawerBlock>
        )}
        {picked && fw && (() => {
          const list = grid?.touched(picked.control, fw.key) ?? []
          return (
            <>
              <DrawerBlock label={`${shortFrameworkName(fw.name)} · ${plural(list.length, 'requirement')}`}>
                {journey.loading && <span className="text-[var(--fm-ink2)]">Loading requirement titles</span>}
                {list.map((t) => (
                  <span key={t.key} className="flex items-center gap-2">
                    <i aria-hidden className={`fm-cel r${t.strength}`} />
                    <span className="min-w-0">
                      <span className="font-mono text-[var(--fm-ink3)]">{t.code}</span> {titles.get(t.key) ?? ''}{' '}
                      <span className="text-[var(--fm-ink3)]">· {t.relation.toLowerCase()}</span>
                    </span>
                  </span>
                ))}
              </DrawerBlock>
              <Link href={`/frameworks/${encodeURIComponent(fw.key)}`} className="self-start text-[13px] font-semibold underline-offset-2 hover:underline">
                Open framework
              </Link>
            </>
          )
        })()}
        {picked && !fw && (
          <Link href={`/systems/${picked.system.id}`} className="self-start text-[13px] font-semibold underline-offset-2 hover:underline">
            Open {picked.system.name}
          </Link>
        )}
      </CellDrawer>
    </div>
  )
}

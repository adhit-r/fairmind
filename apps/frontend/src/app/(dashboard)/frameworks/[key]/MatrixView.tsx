'use client'

import Link from 'next/link'
import { withPackSystem } from '@/lib/assurance/packScope'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { useMemo, useState } from 'react'
import { CommandBar } from '@/components/layout/CommandBar'
import { Empty, ErrorNote, Loading, ReqPill } from '@/components/packs/parts'
import { CellDrawer, CellMeaning, classLabel, DrawerBlock, Matrix } from '@/components/ui/matrix'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { CheckEvidenceLinks } from '@/components/workflow/CheckEvidenceLinks'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useControls, useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useEvidencePacks } from '@/lib/api/hooks/useEvidencePacks'
import { useJourney, useJourneys } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'
import { STRENGTH, confirmedFrameworks, controlGrid, needsWorkInHighCritical, systemGrid } from './grid'
import { requirementHref } from '../parts'

const SEG = 'inline-flex rounded-full border border-[var(--fm-line)] bg-white p-0.5'
const SEG_ITEM = 'inline-flex h-7 items-center whitespace-nowrap rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]'
const SEG_ON = 'bg-[var(--fm-ink)] text-white hover:text-white'
const SELECT = 'h-8 rounded-full border border-[var(--fm-line)] bg-white px-3 text-[12.5px] font-medium text-[var(--fm-ink2)]'
const LINK = 'font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline'

/** The system-by-requirement and control-by-requirement matrices, kept as the framework page's secondary views. */
export function MatrixView() {
  const params = useParams<{ key: string }>()
  const key = decodeURIComponent(params.key)
  const search = useSearchParams()
  const byControl = search.get('view') === 'controls'
  const router = useRouter()
  const { systems } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const confirmed = useMemo(() => confirmedFrameworks(real), [real])
  const journeys = useJourneys()
  const journey = useJourney(key)
  const fw = useFrameworkSystems(key)
  const controls = useControls(byControl)
  const { create } = useEvidencePacks()
  const showAll = search.get('all') === '1'
  const [busy, setBusy] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const name = fw.data?.framework.name ?? journey.data?.name ?? confirmed.find((f) => f.key === key)?.name ?? key
  const short = shortFrameworkName(name)
  const sys = useMemo(() => (journey.data && fw.data ? systemGrid(journey.data, fw.data, showAll) : null), [journey.data, fw.data, showAll])
  const ctl = useMemo(() => (journey.data && controls.data ? controlGrid(journey.data, controls.data) : null), [journey.data, controls.data])
  const openN = fw.data ? needsWorkInHighCritical(fw.data) : null
  const inScope = fw.data?.systems ?? []
  const view = byControl ? '?view=controls' : '?view=matrix'
  const fwHref = (k: string) => `/frameworks/${encodeURIComponent(k)}${view}`
  const more = (journeys.data ?? []).filter((j) => !confirmed.some((c) => c.key === j.key))

  const exportPack = async () => {
    setBusy(true)
    setExportError(null)
    const res = await create({ title: `${short} inspection pack`, frameworks: [key], systemIds: inScope.map((s) => s.id) })
    setBusy(false)
    if (res.success && res.data) router.push(`/evidence/packs/${res.data.id}`)
    else setExportError(res.error || 'Could not create the inspection pack')
  }

  const reqOf = (k: string) => {
    for (const g of journey.data?.groups ?? []) {
      const r = g.requirements.find((x) => x.key === k)
      if (r) return { r, group: g.name }
    }
    return null
  }
  const loading = journey.loading || (byControl ? controls.loading : fw.loading)
  const error = journey.error || (byControl ? controls.error : fw.error)
  const rows = search.getAll('row')
  const cols = search.getAll('col')
  const matrix = byControl ? ctl?.matrix : sys?.matrix
  const columnIndex = matrix?.colGroups.flatMap((g) => g.cols).findIndex((column) => column.key === cols[0]) ?? -1
  const cell = !error && rows.length === 1 && cols.length === 1 && columnIndex >= 0 &&
    matrix?.groups.some((g) => g.rows.some((r) => r.key === rows[0] && r.cells[columnIndex]))
    ? { row: rows[0], col: cols[0] } : null
  const picked = cell ? reqOf(cell.row) : null
  const cellSystem = !byControl && cell ? inScope.find((s) => s.id === cell.col) : undefined
  const updateView = (updates: Record<string, string | null>) => {
    const url = new URL(window.location.href)
    for (const [param, value] of Object.entries(updates)) {
      if (value === null) url.searchParams.delete(param)
      else url.searchParams.set(param, value)
    }
    window.history.replaceState(null, '', url)
  }
  const openCell = (row: string, col: string) => updateView({ row, col })
  const closeCell = () => updateView({ row: null, col: null })
  const reload = () => {
    journey.reload()
    if (byControl) controls.reload()
    else fw.reload()
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      <CommandBar
        stage="govern"
        title={openN === null ? short : `${openN} ${short} requirement${openN === 1 ? ' needs' : 's need'} work in High and Critical systems`}
        reason={inScope.length ? `${inScope.length} system${inScope.length === 1 ? '' : 's'} confirmed ${short}` : `No system has confirmed ${short}`}
        primary={{ label: busy ? 'Exporting' : 'Export for inspection', onClick: exportPack, busy, disabled: !inScope.length }}
      />
      {exportError && <ErrorNote message={exportError} />}
      {!loading && !error && (rows.length > 0 || cols.length > 0) && !picked && (
        <div role="status">This matrix cell is unavailable. <button type="button" className={LINK} onClick={closeCell}>Clear selection</button></div>
      )}

      <section className="fm-card overflow-hidden" aria-label={`${short} requirements`}>
        <div className="flex flex-wrap items-center gap-2 px-[18px] pb-3 pt-4">
          {confirmed.length > 0 && (
            <nav aria-label="Framework" className={cn(SEG, 'max-md:hidden')}>
              {confirmed.map((f) => (
                <Link key={f.key} href={fwHref(f.key)} className={cn(SEG_ITEM, f.key === key && SEG_ON)} aria-current={f.key === key ? 'page' : undefined} title={f.name}>
                  {shortFrameworkName(f.name)}
                </Link>
              ))}
            </nav>
          )}
          {more.length > 0 && (
            <select aria-label="More frameworks" className={cn(SELECT, 'max-md:hidden')} value={more.some((j) => j.key === key) ? key : ''} onChange={(e) => e.target.value && router.push(fwHref(e.target.value))}>
              <option value="">More</option>
              {more.map((j) => (
                <option key={j.key} value={j.key}>
                  {shortFrameworkName(j.name)}
                </option>
              ))}
            </select>
          )}
          <select aria-label="Framework" className={cn(SELECT, 'max-w-[150px] md:hidden')} value={key} onChange={(e) => router.push(fwHref(e.target.value))}>
            {[...confirmed, ...more].some((f) => f.key === key) ? null : <option value={key}>{short}</option>}
            {[...confirmed, ...more].map((f) => (
              <option key={f.key} value={f.key}>
                {shortFrameworkName(f.name)}
              </option>
            ))}
          </select>
          <nav aria-label="View" className={SEG}>
            <Link href={`/frameworks/${encodeURIComponent(key)}`} className={SEG_ITEM}>
              Requirements
            </Link>
            <Link href={`/frameworks/${encodeURIComponent(key)}?view=matrix`} className={cn(SEG_ITEM, !byControl && SEG_ON)} aria-current={!byControl ? 'page' : undefined}>
              By system
            </Link>
            <Link href={`/frameworks/${encodeURIComponent(key)}?view=controls`} className={cn(SEG_ITEM, byControl && SEG_ON)} aria-current={byControl ? 'page' : undefined}>
              By control
            </Link>
          </nav>
          <span className="ml-auto text-[12px] tabular-nums text-[var(--fm-ink2)]">
            {byControl && ctl && `${ctl.used} of ${ctl.total} controls`}
            {!byControl && sys && inScope.length > 0 && (
              <button type="button" className={LINK} onClick={() => updateView({ all: showAll ? null : '1' })}>
                {showAll ? `${sys.tracked} tracked only` : `Show all ${sys.total}`}
              </button>
            )}
          </span>
        </div>

        {loading ? (
          <div className="px-[18px] pb-[18px]">
            <Loading label={`Loading ${short}`} />
          </div>
        ) : error ? (
          <div className="px-[18px] pb-[18px]">
            <ErrorNote message={error} onRetry={reload} />
          </div>
        ) : byControl && ctl ? (
          <Matrix id="fwctl" {...ctl.matrix} onCell={openCell} />
        ) : !byControl && sys && inScope.length === 0 ? (
          <div className="px-[18px] pb-[18px]">
            <Empty>
              No system has confirmed {short}.{' '}
              {real.length > 0 ? (
                <Link className={LINK} href="/systems">
                  Choose a system to review
                </Link>
              ) : (
                <Link className={LINK} href="/onboard">
                  Register a system
                </Link>
              )}
            </Empty>
          </div>
        ) : !byControl && sys ? (
          <>
            <Matrix id="fwsys" {...sys.matrix} onCell={openCell} />
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-[var(--fm-line)] px-[18px] py-2.5 text-[12px] tabular-nums text-[var(--fm-ink2)]">
              <span>{sys.totals.proven} proven</span>
              <span>{sys.totals.estimated} estimated</span>
              <span>{sys.totals.attested} attested</span>
              <span className="font-medium text-[var(--fm-brand)]">{sys.totals.open} open</span>
              {sys.totals.fails > 0 && <span className="text-[#b4232c]">{sys.totals.fails} fail</span>}
              {sys.totals.stale > 0 && <span className="text-[#a14d00]">{sys.totals.stale} stale</span>}
              <span>{sys.totals.atorg} covered by organisation packs</span>
              {fw.data && fw.data.unconfirmed > 0 && (
                <span className="ml-auto">
                  {fw.data.unconfirmed} system{fw.data.unconfirmed === 1 ? '' : 's'} not confirmed ·{' '}
                  <Link className={LINK} href="/systems">
                    Choose a system
                  </Link>
                </span>
              )}
            </div>
          </>
        ) : null}
      </section>

      <CellDrawer
        open={!!(cell && picked)}
        onClose={closeCell}
        label={picked ? `${short} ${picked.r.control}` : short}
        title={picked?.r.title ?? ''}
        sub={picked?.group}
      >
        {cell && picked && !byControl && cell.col === 'org' && (
          <DrawerBlock label="Organisation">
            <CellMeaning cell={picked.r.status === 'covered' || picked.r.status === 'tested' ? 'atorg' : null} labels={sys?.matrix.legendLabels} />
            <span>
              <ReqPill status={picked.r.status} />
            </span>
          </DrawerBlock>
        )}
        {cell && picked && !byControl && cell.col !== 'org' && fw.data && (() => {
          const i = fw.data.systems.findIndex((s) => s.id === cell.col)
          const c = fw.data.requirements.find((r) => r.key === cell.row)?.cells[i] ?? null
          const s = fw.data.systems[i]
          return (
            <>
              <DrawerBlock label={s ? `${s.name} · ${s.riskTier}` : 'System'}>
                <CellMeaning cell={c?.state ?? null} />
              </DrawerBlock>
              <DrawerBlock label="Release checks behind it">
                {c?.checks.length ? (
                  c.checks.map((x) => (
                    <div key={x.check} className="grid gap-0.5">
                      <span>
                        <b className="font-semibold">{x.label}</b> <span className="text-[var(--fm-ink2)]">· {x.relation}</span>
                      </span>
                      <span className="text-[12px] text-[var(--fm-ink2)]">
                        {!x.fails && x.evidenceClass ? `${classLabel(x.evidenceClass)} · ` : ''}Check confidence <span className="font-mono">{x.confidence.toFixed(2)}</span>
                      </span>
                      <CheckEvidenceLinks systemId={s?.id} check={x} failed={Boolean(x.fails || x.cell === 'fails')} />
                    </div>
                  ))
                ) : (
                  <span className="text-[var(--fm-ink2)]">Not tracked per system yet</span>
                )}
              </DrawerBlock>
              {s && (
                <Link href={requirementHref(key, picked.r.control, s.id)} className={LINK}>Review {picked.r.control} for {s.name}</Link>
              )}
              {s && (
                <Link href={`/systems/${encodeURIComponent(s.id)}`} className="self-start text-[13px] font-semibold underline-offset-2 hover:underline">
                  Open {s.name}
                </Link>
              )}
            </>
          )
        })()}
        {cell && picked && byControl && controls.data && ctl && (() => {
          const control = controls.data.controls.find((c) => c.id === cell.col)
          const relation = ctl.relationOf(cell.row, cell.col)
          if (!control) return null
          return (
            <>
              <DrawerBlock label={control.id}>
                <b className="font-semibold">{control.name}</b>
                {control.objective && <span className="text-[var(--fm-ink2)]">{control.objective}</span>}
                {relation && STRENGTH[relation] ? <CellMeaning cell={STRENGTH[relation]} /> : <span className="text-[var(--fm-ink2)]">{relation ?? 'Not in the crosswalk'}</span>}
              </DrawerBlock>
              <DrawerBlock label="Workflows that produce it">
                {control.workflows.length ? (
                  control.workflows.map((w) => (
                    <span key={w.id}>
                      {w.name} <span className="text-[var(--fm-ink3)]">· approver {w.approver || 'not named'}{w.scope ? ` · ${w.scope}` : ''}</span>
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--fm-ink2)]">Evidence mapping only</span>
                )}
              </DrawerBlock>
            </>
          )
        })()}
        <Link href={withPackSystem(`/compliance/journeys/${encodeURIComponent(key)}`, cellSystem?.id)} className="mt-auto self-start text-[12.5px] text-[var(--fm-ink2)] underline-offset-2 hover:underline">
          Packs for {short}
        </Link>
      </CellDrawer>
    </div>
  )
}

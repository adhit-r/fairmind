'use client'

import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo, useState } from 'react'
import { CommandBar } from '@/components/layout/CommandBar'
import { Empty, ErrorNote, Loading, ReqPill } from '@/components/packs/parts'
import { CellDrawer, CellMeaning, classLabel, DrawerBlock, Matrix } from '@/components/ui/matrix'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useControls, useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useEvidencePacks } from '@/lib/api/hooks/useEvidencePacks'
import { useJourney, useJourneys } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'
import { STRENGTH, confirmedFrameworks, controlGrid, needsWorkInHighCritical, systemGrid } from './grid'

const SEG = 'inline-flex rounded-full border border-[var(--fm-line)] bg-white p-0.5'
const SEG_ITEM = 'inline-flex h-7 items-center whitespace-nowrap rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]'
const SEG_ON = 'bg-[var(--fm-ink)] text-white hover:text-white'
const SELECT = 'h-8 rounded-full border border-[var(--fm-line)] bg-white px-3 text-[12.5px] font-medium text-[var(--fm-ink2)]'
const LINK = 'font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline'

function FrameworkGrid() {
  const params = useParams<{ key: string }>()
  const key = decodeURIComponent(params.key)
  const byControl = useSearchParams().get('view') === 'controls'
  const router = useRouter()
  const { systems } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const confirmed = useMemo(() => confirmedFrameworks(real), [real])
  const journeys = useJourneys()
  const journey = useJourney(key)
  const fw = useFrameworkSystems(key)
  const controls = useControls(byControl)
  const { create } = useEvidencePacks()
  const [showAll, setShowAll] = useState(false)
  const [cell, setCell] = useState<{ row: string; col: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const name = fw.data?.framework.name ?? journey.data?.name ?? confirmed.find((f) => f.key === key)?.name ?? key
  const short = shortFrameworkName(name)
  const sys = useMemo(() => (journey.data && fw.data ? systemGrid(journey.data, fw.data, showAll) : null), [journey.data, fw.data, showAll])
  const ctl = useMemo(() => (journey.data && controls.data ? controlGrid(journey.data, controls.data) : null), [journey.data, controls.data])
  const openN = fw.data ? needsWorkInHighCritical(fw.data) : null
  const inScope = fw.data?.systems ?? []
  const firstUnconfirmed = real.find((s) => !s.metadata?.applicability)
  const view = byControl ? '?view=controls' : ''
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
  const picked = cell ? reqOf(cell.row) : null
  const loading = journey.loading || (byControl ? controls.loading : fw.loading)
  const error = journey.error || (byControl ? controls.error : fw.error)
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
            <Link href={`/frameworks/${encodeURIComponent(key)}`} className={cn(SEG_ITEM, !byControl && SEG_ON)} aria-current={!byControl ? 'page' : undefined}>
              By system
            </Link>
            <Link href={`/frameworks/${encodeURIComponent(key)}?view=controls`} className={cn(SEG_ITEM, byControl && SEG_ON)} aria-current={byControl ? 'page' : undefined}>
              By control
            </Link>
          </nav>
          <span className="ml-auto text-[12px] tabular-nums text-[var(--fm-ink2)]">
            {byControl && ctl && `${ctl.used} of ${ctl.total} controls`}
            {!byControl && sys && inScope.length > 0 && (
              <button type="button" className={LINK} onClick={() => setShowAll((v) => !v)}>
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
          <Matrix id="fwctl" {...ctl.matrix} onCell={(row, col) => setCell({ row, col })} />
        ) : !byControl && sys && inScope.length === 0 ? (
          <div className="px-[18px] pb-[18px]">
            <Empty>
              No system has confirmed {short}.{' '}
              {firstUnconfirmed || real[0] ? (
                <Link className={LINK} href={`/systems/${(firstUnconfirmed ?? real[0]).id}`}>
                  Confirm frameworks for {(firstUnconfirmed ?? real[0]).name}
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
            <Matrix id="fwsys" {...sys.matrix} onCell={(row, col) => setCell({ row, col })} />
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-[var(--fm-line)] px-[18px] py-2.5 text-[12px] tabular-nums text-[var(--fm-ink2)]">
              <span>{sys.totals.proven} proven</span>
              <span>{sys.totals.estimated} estimated</span>
              <span>{sys.totals.attested} attested</span>
              <span className="font-medium text-[var(--fm-brand)]">{sys.totals.open} open</span>
              {sys.totals.fails > 0 && <span className="text-[#b4232c]">{sys.totals.fails} fail</span>}
              {sys.totals.stale > 0 && <span className="text-[#a14d00]">{sys.totals.stale} stale</span>}
              <span>{sys.totals.atorg} covered by organisation packs</span>
              {fw.data && fw.data.unconfirmed > 0 && firstUnconfirmed && (
                <span className="ml-auto">
                  {fw.data.unconfirmed} system{fw.data.unconfirmed === 1 ? '' : 's'} not confirmed ·{' '}
                  <Link className={LINK} href={`/systems/${firstUnconfirmed.id}`}>
                    Confirm
                  </Link>
                </span>
              )}
            </div>
          </>
        ) : null}
      </section>

      <CellDrawer
        open={!!(cell && picked)}
        onClose={() => setCell(null)}
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
                        {x.evidenceClass ? classLabel(x.evidenceClass) : 'Nothing current on file'} · <span className="font-mono">{x.confidence.toFixed(2)}</span>
                        {x.evidenceId && (
                          <>
                            {' · '}
                            <Link className={LINK} href={`/evidence?item=${encodeURIComponent(x.evidenceId)}`}>
                              Open evidence
                            </Link>
                          </>
                        )}
                      </span>
                    </div>
                  ))
                ) : (
                  <span className="text-[var(--fm-ink2)]">Not tracked per system yet</span>
                )}
              </DrawerBlock>
              {s && (
                <Link href={`/systems/${s.id}`} className="self-start text-[13px] font-semibold underline-offset-2 hover:underline">
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
        <Link href={`/compliance/journeys/${encodeURIComponent(key)}`} className="mt-auto self-start text-[12.5px] text-[var(--fm-ink2)] underline-offset-2 hover:underline">
          Packs for {short}
        </Link>
      </CellDrawer>
    </div>
  )
}

export default function FrameworkPage() {
  return (
    <Suspense fallback={null}>
      <FrameworkGrid />
    </Suspense>
  )
}

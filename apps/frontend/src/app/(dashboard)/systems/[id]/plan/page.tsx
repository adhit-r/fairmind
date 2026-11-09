'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Fragment, useCallback, useMemo, useState, type ReactNode } from 'react'
import { useOrg } from '@/context/OrgContext'
import { CommandBar } from '@/components/layout/CommandBar'
import { BTN, Crumbs, Empty, ErrorNote, Loading, Pill, lifecycleStage } from '@/components/packs/parts'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { KIND_TITLE, Matrix, cellKind, type Cell } from '@/components/ui/matrix'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { usePackActions, usePackDetail, usePacks, type Journey, type Resource } from '@/lib/api/hooks/usePacks'
import { systemFileScopeKey, useSystemFile } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'
import { JourneyFeed } from '../LeavesOpen'
import { afterSteps, aiRead, planGrid, planPacks, type PlanPack } from './plan'

const TAB_LIST = 'h-auto rounded-full border border-[var(--fm-line)] bg-white p-0.5 text-[var(--fm-ink2)]'
const TAB = 'h-7 rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)] data-[state=active]:bg-[var(--fm-ink)] data-[state=active]:text-white data-[state=active]:shadow-none'
const LINK = 'font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline'
const COUNT = 'text-[12px] tabular-nums text-[var(--fm-ink3)]'

function Head({ title, count, children }: { title: string; count?: number; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline gap-2 px-[18px] pb-3 pt-4">
      <h2 className="text-[15px] font-semibold tracking-[-0.01em]">{title}</h2>
      {count !== undefined && <span className={COUNT}>{count}</span>}
      {children}
    </div>
  )
}

function BestCell({ cell }: { cell: Cell }) {
  const k = cellKind(cell)
  if (!k) return null
  const t = `Best over the ticked packs · ${KIND_TITLE[k]}`
  return <i role="img" className={`fm-cel ${k}`} title={t} aria-label={t} />
}

function PackWorkflows({ pack }: { pack: string }) {
  const d = usePackDetail(pack)
  if (d.loading) return <p className="pb-3 pl-[46px] pr-[18px] text-[12.5px] text-[var(--fm-ink3)]">Loading workflows</p>
  if (d.error) return <div className="px-[18px] pb-3"><ErrorNote message={d.error} onRetry={d.reload} /></div>
  const wfs = d.data?.patterns.flatMap((p) => p.workflows) ?? []
  return (
    <ul className="grid gap-1 pb-3 pl-[46px] pr-[18px] text-[12.5px]">
      {wfs.map((w) => (
        <li key={w.id} className="flex min-w-0 gap-2">
          <Link href={`/compliance/workflows/${encodeURIComponent(w.id)}`} className="min-w-0 truncate hover:underline" title={w.name}>{w.name}</Link>
          <span className="flex-none text-[var(--fm-ink3)]">{lifecycleStage(w.stage)}</span>
        </li>
      ))}
    </ul>
  )
}

function PackRow({ p, on, workflows, onToggle }: { p: PlanPack; on: boolean; workflows: number | undefined; onToggle: () => void }) {
  const [open, setOpen] = useState(false)
  return (
    <li className="border-t border-[var(--fm-line)]">
      <div className="flex min-h-[44px] items-center gap-3 px-[18px] py-2">
        <input type="checkbox" checked={on} onChange={onToggle} aria-label={`Include ${p.name}`} className="h-4 w-4 flex-none accent-[var(--fm-ink)]" />
        <span className={cn('min-w-0 flex-1 truncate text-[13.5px] font-medium transition-opacity [transition-duration:120ms]', !on && 'opacity-50')} title={`${p.name} · first covers ${p.newlyCovered} requirement${p.newlyCovered === 1 ? '' : 's'}`}>
          {p.name}
        </span>
        {p.installed && <Pill tone="done">Installed</Pill>}
        <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex-none whitespace-nowrap text-[12px] text-[var(--fm-ink2)] underline-offset-2 hover:underline">
          {workflows === undefined ? 'Workflows' : `${workflows} workflow${workflows === 1 ? '' : 's'}`}
        </button>
      </div>
      {open && <PackWorkflows pack={p.pack} />}
    </li>
  )
}

/** Remounts per organisation and system, so ticks never carry over to another system. */
export default function PlanPage() {
  const { id } = useParams<{ id: string }>()
  const { selectedOrg } = useOrg()
  return <PlanBody key={systemFileScopeKey(selectedOrg?.id, id)} id={id} />
}

function PlanBody({ id }: { id: string }) {
  const { system, gate, clauseMap, loading, error } = useSystemFile(id)
  const confirmed = system?.applicability?.frameworks ?? clauseMap?.confirmed ?? []
  const [feeds, setFeeds] = useState<Record<string, Resource<Journey>>>({})
  const onFeed = useCallback((fw: string, r: Resource<Journey>) => setFeeds((f) => ({ ...f, [fw]: r })), [])
  const packList = usePacks()
  const { installPack } = usePackActions()
  const [unticked, setUnticked] = useState<Set<string>>(new Set())
  const [all, setAll] = useState(false)
  const [busy, setBusy] = useState(false)
  const [installError, setInstallError] = useState<string | null>(null)

  const loaded = confirmed.map((f) => feeds[f.key])
  const jLoading = loaded.some((r) => !r || r.loading)
  const jError = loaded.find((r) => r?.error)?.error ?? null
  const keys = confirmed.map((f) => f.key).join('\n')
  const journeys = useMemo(() => keys.split('\n').flatMap((k) => (feeds[k]?.data ? [feeds[k].data!] : [])), [feeds, keys])
  const packs = useMemo(() => planPacks(journeys, (packList.data ?? []).map((p) => p.id)), [journeys, packList.data])
  const ticked = useMemo(() => new Set(packs.filter((p) => !unticked.has(p.pack)).map((p) => p.pack)), [packs, unticked])
  const plan = useMemo(() => planGrid(journeys, packs, ticked, all), [journeys, packs, ticked, all])
  const workflows = useMemo(() => new Map((packList.data ?? []).map((p) => [p.id, p.workflowCount])), [packList.data])
  const toInstall = packs.filter((p) => ticked.has(p.pack) && !p.installed)
  const top = afterSteps(gate)
  const read = aiRead(system?.applicability, system?.metadata?.source as string | undefined)

  const toggle = (pack: string) =>
    setUnticked((u) => {
      const next = new Set(u)
      if (!next.delete(pack)) next.add(pack)
      return next
    })
  const reloadAll = () => {
    Object.values(feeds).forEach((f) => f.reload())
    packList.reload()
  }
  async function install() {
    setBusy(true)
    setInstallError(null)
    for (const p of toInstall) {
      const res = await installPack(p.pack)
      if (res.error) {
        setInstallError(res.error)
        break
      }
    }
    setBusy(false)
    reloadAll()
  }

  if (!loading && (error || !system)) {
    return (
      <div className="mx-auto max-w-[720px]">
        <h1 className="text-[30px] font-semibold tracking-[-.03em]">This system is not in your estate</h1>
        <p className="mt-2 text-[15px] text-[var(--fm-ink2)]">{error || 'It may belong to another organisation or have been removed.'}</p>
        <Link href="/dashboard" className="mt-5 inline-flex h-10 items-center rounded-full bg-[var(--fm-ink)] px-5 text-[13px] font-semibold text-white">Back to the estate</Link>
      </div>
    )
  }

  const short = confirmed.map((f) => shortFrameworkName(f.name)).join(', ')
  const n = toInstall.length
  const primary = !system
    ? undefined
    : !confirmed.length
      ? { label: 'Confirm tier and rules', href: `/systems/${encodeURIComponent(id)}` }
      : n || jLoading
        ? { label: busy ? 'Installing' : `Install ${n} pack${n === 1 ? '' : 's'} for the organisation`, onClick: install, busy, disabled: jLoading || !n }
        : { label: 'Open system', href: `/systems/${encodeURIComponent(id)}` }
  const noFramework = <Empty>No framework is confirmed for this system yet. Confirm its tier and rules on the system file.</Empty>
  const body = (node: ReactNode) =>
    jLoading ? <div className="px-[18px] pb-[18px]"><Loading label="Loading the plan" /></div>
      : jError ? <div className="px-[18px] pb-[18px]"><ErrorNote message={jError} onRetry={reloadAll} /></div>
        : node

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      {confirmed.map((f) => <JourneyFeed key={f.key} fw={f.key} onChange={onFeed} />)}
      <Crumbs items={[{ label: 'Today', href: '/dashboard' }, { label: system?.name ?? 'System', href: `/systems/${encodeURIComponent(id)}` }, { label: 'Plan' }]} />
      <CommandBar
        stage="govern"
        title={system ? `Plan for ${system.name}` : 'Plan'}
        reason={confirmed.length ? `${packs.length} pack${packs.length === 1 ? '' : 's'} cover ${short}` : 'No framework confirmed yet'}
        primary={primary}
      />
      {installError && <ErrorNote message={installError} />}
      {top && <p className="px-1 text-[12.5px] text-[var(--fm-ink2)]" title={top.title}>{top.text}</p>}

      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <Tabs defaultValue="packs" className="grid grid-cols-[minmax(0,1fr)] gap-4">
          <TabsList aria-label="Plan" className={cn(TAB_LIST, 'justify-self-start')}>
            <TabsTrigger value="packs" className={TAB}>Packs</TabsTrigger>
            <TabsTrigger value="requirements" className={TAB}>Requirements</TabsTrigger>
          </TabsList>

          <TabsContent value="packs" className="mt-0">
            <section className="fm-card overflow-hidden" aria-label="Recommended packs">
              <Head title="Recommended packs" count={confirmed.length && !jLoading ? ticked.size : undefined} />
              {!confirmed.length && !loading ? (
                <div className="px-[18px] pb-[18px]">{noFramework}</div>
              ) : (
                body(
                  packs.length ? (
                    <>
                      <ul>
                        {packs.map((p) => <PackRow key={p.pack} p={p} on={ticked.has(p.pack)} workflows={workflows.get(p.pack)} onToggle={() => toggle(p.pack)} />)}
                      </ul>
                      <div className="flex flex-wrap items-center gap-3 border-t border-[var(--fm-line)] px-[18px] py-3">
                        <button type="button" disabled className={BTN} title="Coming soon">Save plan for this system</button>
                        <span className="text-[12px] text-[var(--fm-ink3)]">Coming soon</span>
                      </div>
                    </>
                  ) : (
                    <div className="px-[18px] pb-[18px]"><Empty>No pack in the catalogue covers {short} yet.</Empty></div>
                  ),
                )
              )}
            </section>
          </TabsContent>

          <TabsContent value="requirements" className="mt-0">
            <section className="fm-card overflow-hidden" aria-label="Requirements the plan covers">
              <Head title="Requirements the plan covers" count={confirmed.length && !jLoading ? plan.shown : undefined}>
                {confirmed.length > 0 && !jLoading && plan.total > 0 && (
                  <button type="button" className={cn(LINK, 'ml-auto text-[12px]')} onClick={() => setAll((v) => !v)}>
                    {all ? 'Covered only' : `Show all ${plan.total}`}
                  </button>
                )}
              </Head>
              {!confirmed.length && !loading ? (
                <div className="px-[18px] pb-[18px]">{noFramework}</div>
              ) : (
                body(
                  <Matrix
                    id="plancov"
                    {...plan.grid}
                    groups={plan.groups.map((g) => ({ ...g, rows: g.rows.map((r) => ({ ...r, count: <BestCell cell={r.best} /> })) }))}
                  />,
                )
              )}
            </section>
          </TabsContent>
        </Tabs>

        <section className="fm-card grid gap-3 p-[18px] lg:mt-[46px]" aria-label="What the AI read">
          <h2 className="text-[15px] font-semibold tracking-[-0.01em]">What the AI read</h2>
          {read.length ? (
            <dl className="grid grid-cols-[minmax(0,110px)_minmax(0,1fr)] gap-x-4 gap-y-2 text-[13px]">
              {read.map((r) => (
                <Fragment key={r.label}>
                  <dt className="text-[var(--fm-ink3)]">{r.label}</dt>
                  <dd className="min-w-0 break-words" title={r.title}>{r.value}</dd>
                </Fragment>
              ))}
            </dl>
          ) : (
            <Empty>{loading ? 'Loading' : 'Nothing read yet. Confirm the tier and rules on the system file.'}</Empty>
          )}
        </section>
      </div>
    </div>
  )
}

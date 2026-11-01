'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { IconShield, IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react'
import { useCompliance } from '@/lib/api/hooks/useCompliance'
import { usePackActions, usePacks, useRuns, type Pack, type RunStatus, type RunSummary } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { packsFigure } from '@/components/packs/figures'
import { BTN, BTN_P, Empty, ErrorNote, Loading, MUTED, Pill } from '@/components/packs/parts'

function ComplianceFrameworks() {
  const { data, loading, error } = useCompliance()
  
  const frameworks = data?.frameworks || []
  const controls = data?.controls || []

  const getStatusBadge = (status: string) => {
    if (status === 'compliant') {
      return <Badge variant="default" className="border-2 border-black bg-green-500">Compliant</Badge>
    } else if (status === 'partial') {
      return <Badge variant="secondary" className="border-2 border-black bg-yellow-400">Partial</Badge>
    } else {
      return <Badge variant="destructive" className="border-2 border-black">Non-Compliant</Badge>
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Compliance Data</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Compliance</h1>
        <p className="text-muted-foreground mt-1">
          Monitor compliance with AI governance frameworks
        </p>
      </div>

      {/* Framework Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {frameworks.map((framework) => (
          <Card key={framework.name} className="p-6 border-2 border-black shadow-brutal">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold">{framework.name}</h3>
              {getStatusBadge(framework.status)}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Compliance</span>
                <span className="text-sm font-bold">{framework.compliance}%</span>
              </div>
              <Progress value={framework.compliance} className="h-3 border-2 border-black" />
            </div>
          </Card>
        ))}
      </div>

      {/* Controls */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Compliance Controls</h2>
        <div className="space-y-3">
          {controls.map((control) => (
            <div
              key={control.id}
              className="p-4 border-2 border-black bg-white flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                {control.status === 'compliant' ? (
                  <IconCheck className="h-5 w-5 text-green-600" />
                ) : control.status === 'partial' ? (
                  <IconAlertTriangle className="h-5 w-5 text-yellow-600" />
                ) : (
                  <IconX className="h-5 w-5 text-red-600" />
                )}
                <div>
                  <p className="font-medium">{control.name}</p>
                  <p className="text-sm text-muted-foreground">{control.framework}</p>
                </div>
              </div>
              {getStatusBadge(control.status)}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}


/** The pack's home: its journey when it has one, else its first workflow. */
function packHref(p: Pack) {
  if (p.hasJourney) return `/compliance/journeys/${p.id}`
  return p.workflowIds[0] ? `/compliance/workflows/${p.workflowIds[0]}` : null
}

function PacksSection() {
  const packs = usePacks()
  const runs = useRuns()
  const { installPack, uninstallPack } = usePackActions()
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const { figure, byPack } = useMemo(() => {
    // Runs arrive newest first, so the first run seen per workflow is its latest.
    const latest = new Map<string, RunSummary>()
    for (const r of runs.data ?? []) if (!latest.has(r.workflowId)) latest.set(r.workflowId, r)
    let waitNo = 0
    const per = (packs.data ?? []).map((p) => {
      const statuses: Array<RunStatus | null> = p.workflowIds.map((id) => latest.get(id)?.status ?? null)
      const workflows = statuses.map((status) => ({ status, waitNo: status === 'waiting' ? ++waitNo : undefined }))
      const count = (s: RunStatus) => statuses.filter((x) => x === s).length
      return { pack: p, workflows, waiting: count('waiting'), done: count('done'), running: count('running'), blocked: count('blocked') + count('failed') }
    })
    return {
      byPack: per,
      figure: packsFigure(per.map((x) => ({ label: x.pack.name, installed: x.pack.installed, workflows: x.workflows }))),
    }
  }, [packs.data, runs.data])

  async function install(id: string, remove = false) {
    setBusy(id)
    setFailure(null)
    const res = await (remove ? uninstallPack(id) : installPack(id))
    setBusy(null)
    if (res.error) setFailure(res.error)
    packs.reload()
  }

  if (packs.loading && !packs.data) return <Loading label="Loading frameworks" />
  if (packs.error && !packs.data) return <ErrorNote message={`Frameworks could not be loaded. ${packs.error}`} onRetry={packs.reload} />

  const installed = byPack.filter((x) => x.pack.installed)
  const available = byPack.filter((x) => !x.pack.installed)
  const label = `Your AI management system drawn as a board with ${byPack.length} slots. ${installed.length} plugged in${
    installed.length ? `: ${installed.map((x) => x.pack.name).join(', ')}` : ''
  }. Each installed pack shows one tile per workflow, coloured by its latest run.`

  return (
    <div className="flex flex-col gap-[22px]">
      <div className="flex max-w-[720px] flex-col gap-2">
        <h2 className="m-0 text-[28px] font-semibold tracking-[-0.02em]">Frameworks</h2>
        <p className={`m-0 text-[15px] leading-normal ${MUTED}`}>
          {installed.length} of {byPack.length} packs installed. Agents run their workflows and file the evidence; you approve anything that would change a system.
        </p>
      </div>

      <section aria-label="Installed packs" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
        <div className="min-w-0 flex-[999_1_560px]">
          <IsoFigure figure={figure} label={label} className="p-2.5" />
        </div>
        <div className="flex flex-[1_1_280px] flex-col gap-3.5 px-1 py-1.5">
          <h3 className="m-0 text-base font-semibold">Plugged in</h3>
          {installed.length === 0 && <Empty>Nothing is installed yet. Add a framework below.</Empty>}
          {installed.map(({ pack, waiting, done, running, blocked }) => {
            const href = packHref(pack)
            return (
              <div key={pack.id} className="flex flex-col gap-2 rounded-xl border border-[#15171a14] p-3.5">
                <div className="flex items-center justify-between gap-2">
                  <b className="font-semibold">{pack.name}</b>
                  {waiting > 0 && <Pill tone="you" dot>{waiting} waiting</Pill>}
                </div>
                <span className={`text-[13px] leading-snug ${MUTED}`}>
                  {pack.workflowIds.length} {pack.workflowIds.length === 1 ? 'workflow' : 'workflows'}. {done} done, {running} running, {blocked} blocked.
                </span>
                <div className="flex flex-wrap gap-2">
                  {href && (
                    <Link href={href} className={pack.hasJourney ? BTN_P : BTN}>
                      {pack.hasJourney ? 'Open journey' : 'Open workflows'}
                    </Link>
                  )}
                  <button type="button" className={BTN} disabled={busy !== null} onClick={() => install(pack.id, true)} aria-label={`Remove ${pack.name}`}>
                    {busy === pack.id ? 'Removing' : 'Remove'}
                  </button>
                </div>
              </div>
            )
          })}
          {runs.error && <ErrorNote message={`Run status could not be loaded. ${runs.error}`} onRetry={runs.reload} />}
        </div>
      </section>

      <section id="browse" aria-labelledby="add-fw" className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-baseline justify-between gap-2.5">
          <h3 id="add-fw" className="m-0 text-lg font-semibold">Add a framework</h3>
          <span className={`text-[13px] ${MUTED}`}>Installing adds its journey here and its workflows to the lifecycle.</span>
        </div>
        {failure && <ErrorNote message={failure} />}
        {available.length === 0 ? (
          <Empty>Every available framework is installed. More frameworks are coming soon.</Empty>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4">
            {available.map(({ pack }) => (
              <article key={pack.id} className="pk-card flex flex-col gap-2 p-5">
                <b className="text-[15px] font-semibold">{pack.name}</b>
                <p className={`m-0 flex-grow text-[13px] leading-normal ${MUTED}`}>{pack.description}</p>
                <button type="button" className={`${BTN_P} self-start`} disabled={busy !== null} onClick={() => install(pack.id)}>
                  {busy === pack.id ? 'Installing' : 'Install'}
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default function CompliancePage() {
  return (
    <div className="space-y-10">
      <PacksSection />
      <ComplianceFrameworks />
    </div>
  )
}

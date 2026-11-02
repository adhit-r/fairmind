'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useMemo, useState, type ReactNode } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import { needsPerson, usePackActions, useRun, useWorkflow, versionName } from '@/lib/api/hooks/usePacks'
import { FitWhenReady, KIND_LABEL, KindIcon, flowGraph, nodeTypes, type NodeState } from '@/components/packs/flow'
import { BTN, BTN_P, Crumbs, EnginePill, ErrorNote, Heading, LABEL, LINE, Loading, MUTED, Pill, StatusPill, cap, when } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

export default function WorkflowPage() {
  const { workflowId } = useParams<{ workflowId: string }>()
  const router = useRouter()
  const { startRun, createDraft } = usePackActions()
  const wf = useWorkflow(workflowId)
  const run = useRun(wf.data?.latestRun?.id)
  const [overlay, setOverlay] = useState(true)
  const [starting, setStarting] = useState(false)
  const [opening, setOpening] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)

  const graph = useMemo(() => {
    const steps = wf.data?.steps ?? []
    const r = overlay ? run.data : null
    const completed = new Set((r?.events ?? []).filter((e) => e.kind === 'step.completed' && e.stepId).map((e) => e.stepId))
    const stateOf = (id: string): NodeState => {
      if (!r) return 'idle'
      if (r.currentStep === id && r.status === 'waiting') return 'waiting'
      if (r.currentStep === id && (r.status === 'running' || r.status === 'blocked')) return 'current'
      return completed.has(id) ? 'done' : 'idle'
    }
    return flowGraph(steps, { stateOf, run: r !== null })
  }, [wf.data, run.data, overlay])

  async function start() {
    if (!wf.data) return
    setStarting(true)
    setFailure(null)
    const res = await startRun(wf.data.id)
    setStarting(false)
    wf.reload()
    if (res.error || !res.data) setFailure(res.error ?? 'The run could not be started.')
    else router.push(`/compliance/runs/${res.data.id}`)
  }

  async function edit() {
    if (!wf.data) return
    if (!wf.data.draft) {
      setOpening(true)
      setFailure(null)
      const res = await createDraft(wf.data.id)
      setOpening(false)
      if (res.error) return setFailure(res.error)
    }
    router.push(`/compliance/workflows/${wf.data.id}/edit`)
  }

  if (wf.loading && !wf.data) return <Loading label="Loading workflow" />
  if (wf.error || !wf.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Workflow' }]} />
        <ErrorNote message={`This workflow could not be loaded. ${wf.error ?? ''}`} onRetry={wf.reload} />
      </div>
    )
  }


  const w = wf.data
  const last = w.latestRun
  const facts: Array<[string, ReactNode]> = [
    ['Runs in', cap(w.stage)],
    ['Autonomy', <span key="a" title={w.autonomy}>{w.autonomy.split(/\s/)[0]}</span>],
    ['Approver', w.approver],
    ['Pattern', w.pattern.name],
    ['Version', versionName(w.version)],
  ]
  const governance = ([
    ['Common control', w.commonControl],
    ['Autonomy', w.autonomy],
    ['Gate', w.gate],
    ['Gate conditions', w.gateConditions],
    ['Separation of duties', w.separationOfDuties],
    ['External write', w.externalWrite],
    ['Triggers', w.triggers.length ? w.triggers.join('; ') : null],
  ] as Array<[string, ReactNode]>).filter(([, v]) => v)
  const byFramework = [...new Set(w.mappings.map((m) => m.framework))].map((f) => ({ framework: f, rows: w.mappings.filter((m) => m.framework === f) }))
  const people = w.steps.filter(needsPerson).length

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: w.pack.name, href: `/compliance/packs/${w.pack.id}` }, { label: w.name }]} />
      <Heading title={w.name} lead={w.description}>
        {last && <Link href={`/compliance/runs/${last.id}`} className={BTN}>Open latest run</Link>}
        <button type="button" className={BTN} onClick={edit} disabled={!w.installed || opening}>
          {opening ? 'Opening' : w.draft ? `Continue draft of version ${w.draft.version}` : 'Edit workflow'}
        </button>
        <button type="button" className={BTN_P} onClick={start} disabled={!w.installed || starting} aria-describedby={w.installed ? undefined : 'start-reason'}>
          {starting ? 'Starting' : 'Start run'}
        </button>
      </Heading>
      {!w.installed && (
        <p id="start-reason" className={cn('-mt-3 m-0 text-[13px]', MUTED)}>
          Start run and editing are off because this workflow&apos;s pack is not installed.{' '}
          <Link href={`/compliance/packs/${w.pack.id}`} className="font-semibold text-[var(--fm-ink)] underline">Install {w.pack.name}</Link>.
        </p>
      )}
      {failure && <ErrorNote message={failure} />}

      <section aria-label="Workflow summary" className="pk-card grid grid-cols-2 gap-x-6 gap-y-4 px-6 py-5 sm:grid-cols-3 lg:grid-cols-[repeat(5,minmax(0,1fr))_minmax(240px,1.6fr)]">
        {facts.map(([k, v]) => (
          <div key={k} className="flex min-w-0 flex-col gap-1">
            <span className={LABEL}>{k}</span>
            <span className="break-words text-[13.5px] font-semibold leading-snug text-[var(--fm-ink)]">{v ?? <span className="font-normal text-[var(--fm-ink3)]">Not set</span>}</span>
          </div>
        ))}
        <div className={cn('col-span-full flex min-w-0 flex-col gap-1 border-t pt-4 lg:col-span-1 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0', LINE)}>
          <span className={LABEL}>Latest run</span>
          {last ? (
            <span className="flex flex-wrap items-center gap-2 text-[13px]">
              <StatusPill status={last.status} />
              <span className={MUTED}>Updated {when(last.updatedAt)}</span>
            </span>
          ) : (
            <span className={cn('text-[13px]', MUTED)}>Not run yet. Each run records its steps on a hash-chained ledger.</span>
          )}
        </div>
      </section>

      <section aria-label="Workflow canvas" className="pk-card flex flex-col overflow-hidden">
        <div className={cn('flex flex-wrap items-center gap-x-5 gap-y-2 border-b px-5 py-3', LINE)}>
          <div className="flex flex-grow flex-col">
            <b className="text-sm font-semibold text-[var(--fm-ink)]">Flow</b>
            <span className={cn('text-[12px]', MUTED)}>
              {w.steps.length} {w.steps.length === 1 ? 'step' : 'steps'}, {people} {people === 1 ? 'needs' : 'need'} a person.{w.draft ? ` A draft of version ${w.draft.version} is in progress; runs use ${versionName(w.version)} until it is published.` : ''}
            </span>
          </div>
          {last && overlay && (
            <ul aria-label="Legend" className={cn('m-0 flex list-none flex-wrap items-center gap-x-4 gap-y-1 p-0 text-[12px]', MUTED)}>
              <li className="flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-2.5 rounded-full bg-[#009869]" />Done</li>
              <li className="flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-2.5 rounded-[3px] border-2 border-[var(--fm-ink)]" />Current</li>
              <li className="flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-2.5 rounded-[3px] border-2 border-[var(--fm-brand)]" />Waiting for you</li>
            </ul>
          )}
          <label className={cn('flex items-center gap-2 text-[13px] font-semibold', last ? 'text-[var(--fm-ink)]' : 'text-[var(--fm-ink3)]')}>
            <input type="checkbox" checked={overlay && Boolean(last)} onChange={(e) => setOverlay(e.target.checked)} disabled={!last} className="h-4 w-4 accent-[var(--fm-ink)]" />
            Show last run
          </label>
        </div>
        <div className="h-[480px] bg-[var(--fm-bg)]" role="group" aria-label={`Workflow graph with ${w.steps.length} steps: ${w.steps.map((s) => s.title).join(', ')}.`}>
          {w.steps.length === 0 ? (
            <p className={`m-0 p-6 text-[13px] ${MUTED}`}>This workflow has no steps defined yet.</p>
          ) : (
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable={false}
              minZoom={0.3}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} size={1} color="rgba(21,23,26,.12)" />
              <Controls showInteractive={false} />
              <FitWhenReady />
            </ReactFlow>
          )}
        </div>
      </section>

      <section aria-labelledby="steps-h" className="pk-card px-6 py-5">
        <h2 id="steps-h" className="m-0 mb-2 text-base font-semibold text-[var(--fm-ink)]">Steps</h2>
        {w.steps.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>This workflow has no steps defined yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] border-collapse text-left text-[13px] text-[var(--fm-ink)]">
              <thead>
                <tr className={LABEL}>
                  <th scope="col" className="w-8 py-2 pr-3 font-semibold">No.</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Step</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Kind</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Permission</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Needs a person</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">If it fails</th>
                  <th scope="col" className="py-2 font-semibold">Output</th>
                </tr>
              </thead>
              <tbody>
                {w.steps.map((s, i) => (
                  <tr key={s.id} className={cn('border-t align-top', LINE)}>
                    <td className={`py-[10px] pr-3 tabular-nums ${MUTED}`}>{i + 1}</td>
                    <td className="max-w-[280px] py-[10px] pr-3">
                      <b className="font-semibold">{s.title}</b>
                      {s.detail && <div className={`mt-0.5 text-[12.5px] leading-snug ${MUTED}`}>{s.detail}</div>}
                      {s.systems.length > 0 && <div className="mt-0.5 text-[12px] text-[var(--fm-ink3)]">{s.systems.join(', ')}</div>}
                    </td>
                    <td className="whitespace-nowrap py-[10px] pr-3">
                      <span className="inline-flex items-center gap-1.5"><KindIcon kind={s.kind} size={14} />{KIND_LABEL[s.kind] ?? s.kind}</span>
                    </td>
                    <td className="py-[10px] pr-3">{s.permission ?? <span className="text-[var(--fm-ink3)]">None</span>}</td>
                    <td className="py-[10px] pr-3">{needsPerson(s) ? <Pill tone="you">Yes</Pill> : <Pill>No</Pill>}</td>
                    <td className="max-w-[220px] py-[10px] pr-3">{s.failure ?? <span className="text-[var(--fm-ink3)]">Not set</span>}</td>
                    <td className="max-w-[220px] py-[10px]">{s.output ?? <span className="text-[var(--fm-ink3)]">None</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="flex flex-wrap items-start gap-[22px]">
        <section aria-labelledby="map-h" className="pk-card min-w-0 flex-[2_1_480px] px-6 py-5">
          <h2 id="map-h" className="m-0 text-base font-semibold text-[var(--fm-ink)]">This run counts toward</h2>
          {w.mappings.length === 0 ? (
            <p className={`m-0 mt-2 text-[13px] ${MUTED}`}>No framework requirements are mapped to this workflow.</p>
          ) : (
            <>
              <p className={`m-0 mb-3 mt-1 text-[13px] ${MUTED}`}>
                {w.mappings.length} {w.mappings.length === 1 ? 'requirement' : 'requirements'} across {byFramework.length} {byFramework.length === 1 ? 'framework' : 'frameworks'}, from one run.
              </p>
              <div className="flex flex-col gap-4">
                {byFramework.map((g) => (
                  <div key={g.framework}>
                    <h3 className={cn('m-0 mb-1', LABEL)}>{g.framework}</h3>
                    <ul className="m-0 list-none p-0">
                      {g.rows.map((m) => (
                        <li key={m.key} className={cn('flex flex-wrap items-start gap-x-3 gap-y-1 border-t py-2 text-[13px]', LINE)}>
                          <span className={cn('w-20 flex-none pt-px font-mono text-xs', MUTED)}>{m.control}</span>
                          <span className="min-w-0 flex-[1_1_220px] text-[var(--fm-ink)]">
                            {m.title}
                            {m.note && <span className={`block text-[12.5px] ${MUTED}`}>{m.note}</span>}
                          </span>
                          <Pill>{m.relation}</Pill>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>

        <div className="flex min-w-0 flex-[1_1_320px] flex-col gap-[22px]">
          {governance.length > 0 && (
            <section aria-labelledby="gov-h" className="pk-card px-6 py-5">
              <h2 id="gov-h" className="m-0 mb-3 text-base font-semibold text-[var(--fm-ink)]">Controls</h2>
              <dl className="m-0 flex flex-col gap-3 text-[13px]">
                {governance.map(([k, v]) => (
                  <div key={k} className="flex flex-col gap-0.5">
                    <dt className={LABEL}>{k}</dt>
                    <dd className="m-0 leading-snug text-[var(--fm-ink)]">{v}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
          <section aria-labelledby="ev-h" className="pk-card px-6 py-5">
            <h2 id="ev-h" className="m-0 mb-1 text-base font-semibold text-[var(--fm-ink)]">Evaluations in this pattern</h2>
            {w.evaluations.length === 0 ? (
              <p className={`m-0 text-[13px] ${MUTED}`}>This pattern has no evaluations.</p>
            ) : (
              <ul className="m-0 list-none p-0">
                {w.evaluations.map((e) => (
                  <li key={e.id} className={cn('flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t py-2.5 text-[13px]', LINE)}>
                    <Link href={`/compliance/evaluations#${encodeURIComponent(e.id)}`} className="min-w-0 flex-[1_1_160px] font-semibold text-[var(--fm-ink)] hover:underline">{e.name}</Link>
                    <EnginePill engine={e.engine} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

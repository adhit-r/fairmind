'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import ReactFlow, { Background, Controls, Handle, MarkerType, Position, useNodesInitialized, useReactFlow, type Edge, type Node, type NodeProps } from 'reactflow'
import 'reactflow/dist/style.css'
import { GATE_KINDS, usePackActions, useRun, useWorkflow, type Step, type StepKind } from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, Crumbs, EnginePill, ErrorNote, Heading, LABEL, LINE, Loading, MUTED, Pill, StatusPill, cap, when } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

type NodeState = 'done' | 'current' | 'waiting' | 'idle'

const ICON: Record<StepKind, string[]> = {
  trigger: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z', 'M12 7v5l3 2'],
  collect: ['M4 5c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z', 'M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5', 'M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3'],
  check: ['M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z', 'm9 12 2 2 4-4'],
  suggest: ['M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01'],
  preflight: ['M9 11l3 3L22 4', 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'],
  ask: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z', 'm16 11 2 2 4-4'],
  exception: ['M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z', 'M12 9v4', 'M12 17h.01'],
  decide: ['M6 3v12', 'M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z', 'M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z', 'M18 9a9 9 0 0 1-9 9'],
  act: ['M13 2 3 14h9l-1 8 10-12h-9l1-8z'],
  verify: ['M21.8 10A10 10 0 1 1 17 3.3', 'm9 11 3 3L22 4'],
  escalate: ['M12 19V5', 'm5 12 7-7 7 7'],
  file: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z', 'M14 2v6h6', 'm9 15 2 2 4-4'],
}
const KIND_LABEL: Record<StepKind, string> = {
  trigger: 'Trigger',
  collect: 'Collect',
  check: 'Check',
  suggest: 'Suggest',
  preflight: 'Preflight',
  ask: 'Ask a person',
  exception: 'Exception',
  decide: 'Decide',
  act: 'Act',
  verify: 'Verify',
  escalate: 'Escalate',
  file: 'File evidence',
}

function KindIcon({ kind, size = 16 }: { kind: StepKind; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {(ICON[kind] ?? ICON.act).map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}

const PORT = '!h-2 !w-2 !border-2 !border-[var(--fm-ink3)] !bg-white'

function StepNode({ data }: NodeProps<{ step: Step; state: NodeState }>) {
  const { step, state } = data
  const waiting = state === 'waiting'
  const detail = step.detail || (step.systems.length ? step.systems.join(', ') : '')
  return (
    <div
      title={KIND_LABEL[step.kind] ?? step.kind}
      className={[
        'relative flex h-[92px] w-[160px] items-start gap-2 rounded-xl p-2.5 text-left shadow-[0_1px_2px_#14141e0a,0_10px_24px_-14px_#14141e40]',
        waiting ? 'border-2 border-[var(--fm-brand)] bg-[#fff7f2]' : state === 'current' ? 'border-2 border-[var(--fm-ink)] bg-white' : 'border border-[var(--fm-line)] bg-white',
        step.kind === 'trigger' ? 'border-dashed border-[rgba(21,23,26,.2)] bg-[var(--fm-bg)]' : '',
      ].join(' ')}
    >
      <Handle type="target" position={Position.Left} className={PORT} />
      {state === 'done' && (
        <span aria-label="Done" role="img" className="absolute -right-[7px] -top-[7px] flex h-[18px] w-[18px] items-center justify-center rounded-full border-2 border-white bg-[#009869]">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </span>
      )}
      <span className={`flex h-7 w-7 flex-none items-center justify-center rounded-lg ${waiting ? 'bg-[var(--fm-brand)] text-[var(--fm-ink)]' : 'bg-[var(--fm-bg)] text-[var(--fm-ink)]'}`}>
        <KindIcon kind={step.kind} />
      </span>
      <span className="min-w-0">
        <b className="line-clamp-2 text-[13px] font-semibold leading-tight text-[var(--fm-ink)]">{step.title}</b>
        {detail && <small title={detail} className={`mt-[3px] text-[11.5px] leading-tight ${MUTED} ${waiting ? 'line-clamp-1' : 'line-clamp-2'}`}>{detail}</small>}
        {waiting && <small className="mt-[3px] block text-[11.5px] font-semibold text-[#a8430b]">Agent waiting here</small>}
      </span>
      <Handle type="source" position={Position.Right} className={PORT} />
      <Handle type="source" id="back-out" position={Position.Bottom} className="!h-px !w-px !min-w-0 !border-0 !bg-transparent" />
      <Handle type="target" id="back-in" position={Position.Bottom} className="!h-px !w-px !min-w-0 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { step: StepNode }

/** Fit the whole flow once every node has been measured; the fitView prop runs too early. */
function FitWhenReady() {
  const ready = useNodesInitialized()
  const { fitView } = useReactFlow()
  useEffect(() => {
    if (ready) fitView({ padding: 0.12, maxZoom: 1 })
  }, [ready, fitView])
  return null
}
const COL = 240
const ROW = 140

/** Columns by first-reached depth from the entry step(s); steps in a column fan out vertically. */
function layout(steps: Step[]): Map<string, { x: number; y: number }> {
  const incoming = new Set(steps.flatMap((s) => s.next.map((n) => n.to)))
  const roots = steps.filter((s) => !incoming.has(s.id))
  const byId = new Map(steps.map((s) => [s.id, s]))
  const depth = new Map<string, number>()
  const queue = (roots.length ? roots : steps.slice(0, 1)).map((s) => s.id)
  queue.forEach((id) => depth.set(id, 0))
  for (let i = 0; i < queue.length; i++) {
    for (const n of byId.get(queue[i])?.next ?? []) {
      if (!depth.has(n.to) && byId.has(n.to)) {
        depth.set(n.to, (depth.get(queue[i]) ?? 0) + 1)
        queue.push(n.to)
      }
    }
  }
  const cols = new Map<number, string[]>()
  for (const s of steps) {
    const d = depth.get(s.id) ?? 0
    cols.set(d, [...(cols.get(d) ?? []), s.id])
  }
  const pos = new Map<string, { x: number; y: number }>()
  cols.forEach((ids, d) => ids.forEach((id, i) => pos.set(id, { x: 20 + d * COL, y: (i - (ids.length - 1) / 2) * ROW })))
  return pos
}

export default function WorkflowPage() {
  const { workflowId } = useParams<{ workflowId: string }>()
  const router = useRouter()
  const { startRun } = usePackActions()
  const wf = useWorkflow(workflowId)
  const run = useRun(wf.data?.latestRun?.id)
  const [overlay, setOverlay] = useState(true)
  const [starting, setStarting] = useState(false)
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
    const pos = layout(steps)
    const minY = Math.min(0, ...[...pos.values()].map((p) => p.y))
    const nodes: Node[] = steps.map((s) => {
      const p = pos.get(s.id) ?? { x: 0, y: 0 }
      return { id: s.id, type: 'step', position: { x: p.x, y: p.y - minY + 20 }, data: { step: s, state: stateOf(s.id) }, draggable: false, selectable: false, connectable: false }
    })
    const edges: Edge[] = steps.flatMap((s) =>
      s.next.map((n) => {
        const traced = r !== null && stateOf(s.id) === 'done' && stateOf(n.to) !== 'idle'
        const untraced = r !== null && !traced
        // A loop back (e.g. Revise -> Suggest) routes below the row instead of through the nodes.
        const back = (pos.get(n.to)?.x ?? 0) <= (pos.get(s.id)?.x ?? 0)
        return {
          id: `${s.id}>${n.to}`,
          type: back ? 'smoothstep' : 'default',
          sourceHandle: back ? 'back-out' : undefined,
          targetHandle: back ? 'back-in' : undefined,
          pathOptions: back ? { offset: 24, borderRadius: 12 } : undefined,
          source: s.id,
          target: n.to,
          label: n.label ?? undefined,
          animated: traced && stateOf(n.to) !== 'done',
          markerEnd: { type: MarkerType.ArrowClosed, color: untraced ? 'var(--fm-ink3)' : 'var(--fm-ink)' },
          style: { stroke: untraced ? 'var(--fm-ink3)' : 'var(--fm-ink)', strokeWidth: 1.6, strokeDasharray: untraced ? '5 5' : undefined },
          labelStyle: { fontSize: 11.5, fontWeight: 600, fill: 'var(--fm-ink2)' },
          labelBgStyle: { fill: 'var(--fm-bg)' },
          labelBgBorderRadius: 999,
        }
      }),
    )
    return { nodes, edges }
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
    ['Version', w.version],
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
  const people = w.steps.filter((s) => GATE_KINDS.includes(s.kind) || !s.runsWithoutApproval).length

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: w.pack.name, href: `/compliance/packs/${w.pack.id}` }, { label: w.name }]} />
      <Heading title={w.name} lead={w.description}>
        {last && <Link href={`/compliance/runs/${last.id}`} className={BTN}>Open latest run</Link>}
        <button type="button" className={BTN_P} onClick={start} disabled={!w.installed || starting} aria-describedby={w.installed ? undefined : 'start-reason'}>
          {starting ? 'Starting' : 'Start run'}
        </button>
      </Heading>
      {!w.installed && (
        <p id="start-reason" className={cn('-mt-3 m-0 text-[13px]', MUTED)}>
          Start run is off because this workflow&apos;s pack is not installed.{' '}
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
              {w.steps.length} {w.steps.length === 1 ? 'step' : 'steps'}, {people} {people === 1 ? 'needs' : 'need'} a person. Editing steps is coming soon.
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
                    <td className="py-[10px] pr-3">{GATE_KINDS.includes(s.kind) || !s.runsWithoutApproval ? <Pill tone="you">Yes</Pill> : <Pill>No</Pill>}</td>
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

'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useMemo, useState, type ReactNode } from 'react'
import ReactFlow, { Background, Controls, Handle, MarkerType, Position, type Edge, type Node, type NodeProps } from 'reactflow'
import 'reactflow/dist/style.css'
import { GATE_KINDS, usePackActions, useRun, useWorkflow, type Step, type StepKind } from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, Crumbs, EnginePill, ErrorNote, Heading, Loading, MUTED, Pill, StatusPill, cap, when } from '@/components/packs/parts'

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

const PORT = '!h-2 !w-2 !border-2 !border-[#8a8f98] !bg-white'

function StepNode({ data }: NodeProps<{ step: Step; state: NodeState }>) {
  const { step, state } = data
  const waiting = state === 'waiting'
  const detail = step.detail || (step.systems.length ? step.systems.join(', ') : '')
  return (
    <div
      title={KIND_LABEL[step.kind] ?? step.kind}
      className={[
        'relative flex h-[92px] w-[160px] items-start gap-2 rounded-xl p-2.5 text-left shadow-[0_1px_2px_#14141e0a,0_10px_24px_-14px_#14141e40]',
        waiting ? 'border-2 border-[#ff6b35] bg-[#fff7f2]' : state === 'current' ? 'border-2 border-[#15171a] bg-white' : 'border border-[#15171a14] bg-white',
        step.kind === 'trigger' ? 'border-dashed bg-[#fbfaf8]' : '',
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
      <span className={`flex h-7 w-7 flex-none items-center justify-center rounded-lg ${waiting ? 'bg-[#ff6b35] text-[#15171a]' : 'bg-[#f4f4f2] text-[#15171a]'}`}>
        <KindIcon kind={step.kind} />
      </span>
      <span className="min-w-0">
        <b className="line-clamp-2 text-[13px] font-semibold leading-tight">{step.title}</b>
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
          markerEnd: { type: MarkerType.ArrowClosed, color: untraced ? '#a3a8b0' : '#15171a' },
          style: { stroke: untraced ? '#a3a8b0' : '#15171a', strokeWidth: 1.6, strokeDasharray: untraced ? '5 5' : undefined },
          labelStyle: { fontSize: 11.5, fontWeight: 600, fill: '#5a5f68' },
          labelBgStyle: { fill: '#f4f4f2' },
          labelBgBorderRadius: 999,
        }
      }),
    )
    // Open at the start of the flow at a readable zoom, vertically centred in the 480px canvas.
    const bottom = Math.max(0, ...nodes.map((n) => n.position.y + 92))
    const viewport = { x: 16, y: Math.max(16, (480 - bottom * 0.8) / 2), zoom: 0.8 }
    return { nodes, edges, viewport }
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
  const stage = cap(w.stage)

  return (
    <div className="flex flex-col gap-5">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: w.name }]} />
      <Heading title={w.name} lead={w.description}>
        <button type="button" className={BTN_P} onClick={start} disabled={!w.installed || starting} aria-describedby={w.installed ? undefined : 'start-reason'}>
          {starting ? 'Starting' : 'Start run'}
        </button>
      </Heading>
      <div className="-mt-3 flex flex-wrap items-center gap-2">
        <Pill>Version {w.version}</Pill>
        <Pill>Runs in {stage}</Pill>
        <Pill>{cap(w.pillar.toLowerCase())}</Pill>
        <span title={w.autonomy}><Pill>Autonomy {w.autonomy.split(/\s/)[0]}</Pill></span>
        {!w.installed && (
          <span id="start-reason" className={`text-[13px] ${MUTED}`}>
            Start run is off because this workflow&apos;s pack is not installed. <Link href={`/compliance/packs/${w.pack.id}`} className="font-semibold underline">Install {w.pack.name}</Link>.
          </span>
        )}
      </div>
      {failure && <ErrorNote message={failure} />}

      <section aria-label="Workflow canvas" className="pk-card flex flex-col overflow-hidden">
        <div className="flex flex-wrap items-center gap-2.5 border-b border-[#15171a14] px-3.5 py-3">
          <b className="flex-grow text-sm font-semibold">Canvas</b>
          <label className="flex items-center gap-2 text-[13px] font-semibold">
            <input type="checkbox" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} disabled={!last} className="h-[18px] w-[18px] accent-[#15171a]" />
            Show last run
          </label>
        </div>
        <div role="group" aria-label="Add a step" className="flex flex-wrap items-center gap-2 border-b border-[#15171a14] px-3.5 py-2.5">
          <span className={`mr-1 text-[12.5px] font-semibold ${MUTED}`}>Add a step</span>
          {(Object.keys(KIND_LABEL) as StepKind[])
            .filter((k) => k !== 'trigger')
            .map((k) => (
              <button key={k} type="button" disabled className="inline-flex h-9 cursor-not-allowed items-center gap-2 rounded-full border border-[#15171a14] bg-white pl-1 pr-3 text-[13px] font-semibold opacity-60">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#f4f4f2]"><KindIcon kind={k} /></span>
                {KIND_LABEL[k]}
              </button>
            ))}
          <Pill>Coming soon</Pill>
        </div>
        <div className="h-[480px] bg-[#f7f6f3]" role="group" aria-label={`Workflow graph with ${w.steps.length} steps: ${w.steps.map((s) => s.title).join(', ')}.`}>
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
              defaultViewport={graph.viewport}
              minZoom={0.3}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} size={1} color="rgba(21,23,26,.14)" />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
      </section>

      <div className="flex flex-wrap items-start gap-5">
        <section aria-labelledby="about" className="pk-card min-w-0 flex-[1_1_360px] px-[22px] py-5">
          <h2 id="about" className="m-0 mb-2 text-base font-semibold">About this workflow</h2>
          <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-[13px]">
            {([
              ['Pattern', w.pattern.name],
              ['Pack', <Link key="pk" href={`/compliance/packs/${w.pack.id}`} className="font-semibold hover:underline">{w.pack.name}</Link>],
              ['Common control', w.commonControl],
              ['Autonomy', w.autonomy],
              ['Gate', w.gate],
              ['Gate conditions', w.gateConditions],
              ['Approver', w.approver],
              ['Separation of duties', w.separationOfDuties],
              ['External write', w.externalWrite],
              ['Triggers', w.triggers.length ? w.triggers.join('; ') : null],
            ] as Array<[string, ReactNode]>)
              .filter(([, v]) => v)
              .map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className={`font-semibold ${MUTED}`}>{k}</dt>
                  <dd className="m-0 leading-snug">{v}</dd>
                </div>
              ))}
          </dl>
        </section>
        <section aria-labelledby="lastrun" className="pk-card min-w-0 flex-[1_1_320px] px-[22px] py-5">
          <h2 id="lastrun" className="m-0 mb-2 text-base font-semibold">Latest run</h2>
          {last ? (
            <div className="flex flex-col gap-2 text-[13px]">
              <div className="flex items-center gap-2"><StatusPill status={last.status} /></div>
              <span className={MUTED}>Updated {when(last.updatedAt)}</span>
              <Link href={`/compliance/runs/${last.id}`} className={`${BTN} self-start`}>Open the run</Link>
            </div>
          ) : (
            <p className={`m-0 text-[13px] ${MUTED}`}>This workflow has not run yet.</p>
          )}
          <p className={`m-0 mt-3 text-[13px] ${MUTED}`}>Editing steps and publishing versions are coming soon.</p>
        </section>
      </div>

      <section aria-labelledby="steps-h" className="pk-card px-6 py-5">
        <h2 id="steps-h" className="m-0 mb-2 text-base font-semibold">Steps</h2>
        {w.steps.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>This workflow has no steps defined yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className={`text-[12px] ${MUTED}`}>
                  <th scope="col" className="py-2 pr-3 font-semibold">Step</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Kind</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Permission</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Needs a person</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">If it fails</th>
                  <th scope="col" className="py-2 font-semibold">Output</th>
                </tr>
              </thead>
              <tbody>
                {w.steps.map((s) => (
                  <tr key={s.id} className="border-t border-[#15171a14] align-top">
                    <td className="max-w-[280px] py-[9px] pr-3">
                      <b className="font-semibold">{s.title}</b>
                      {s.detail && <div className={`mt-0.5 text-[12.5px] leading-snug ${MUTED}`}>{s.detail}</div>}
                      {s.systems.length > 0 && <div className={`mt-0.5 text-[12px] ${MUTED}`}>{s.systems.join(', ')}</div>}
                    </td>
                    <td className="py-[9px] pr-3">
                      <span className="inline-flex items-center gap-1.5"><KindIcon kind={s.kind} size={14} />{KIND_LABEL[s.kind] ?? s.kind}</span>
                    </td>
                    <td className="py-[9px] pr-3">{s.permission ?? <span className={MUTED}>None</span>}</td>
                    <td className="py-[9px] pr-3">{GATE_KINDS.includes(s.kind) || !s.runsWithoutApproval ? <Pill tone="you">Yes</Pill> : <Pill>No</Pill>}</td>
                    <td className="max-w-[220px] py-[9px] pr-3">{s.failure ?? <span className={MUTED}>Not set</span>}</td>
                    <td className="max-w-[220px] py-[9px]">{s.output ?? <span className={MUTED}>None</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby="map-h" className="pk-card px-6 py-5">
        <h2 id="map-h" className="m-0 mb-1 text-base font-semibold">This run counts toward</h2>
        {w.mappings.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>No framework requirements are mapped to this workflow.</p>
        ) : (
          <>
            <p className={`m-0 mb-2 text-[13px] ${MUTED}`}>{w.mappings.length} {w.mappings.length === 1 ? 'requirement' : 'requirements'} across {new Set(w.mappings.map((m) => m.framework)).size} frameworks, from one run.</p>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-[13px]">
                <thead>
                  <tr className={`text-[12px] ${MUTED}`}>
                    <th scope="col" className="py-2 pr-3 font-semibold">Framework</th>
                    <th scope="col" className="py-2 pr-3 font-semibold">Control</th>
                    <th scope="col" className="py-2 pr-3 font-semibold">Title</th>
                    <th scope="col" className="py-2 font-semibold">Relation</th>
                  </tr>
                </thead>
                <tbody>
                  {w.mappings.map((m) => (
                    <tr key={m.key} className="border-t border-[#15171a14] align-top">
                      <td className="py-[9px] pr-3">{m.framework}</td>
                      <td className="py-[9px] pr-3 font-mono text-xs">{m.control}</td>
                      <td className="py-[9px] pr-3">
                        {m.title}
                        {m.note && <div className={`mt-0.5 text-[12.5px] ${MUTED}`}>{m.note}</div>}
                      </td>
                      <td className="py-[9px]"><Pill>{m.relation}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section aria-labelledby="ev-h" className="pk-card px-6 py-5">
        <h2 id="ev-h" className="m-0 mb-1 text-base font-semibold">Evaluations in this pattern</h2>
        {w.evaluations.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>This pattern has no evaluations.</p>
        ) : (
          <ul className="m-0 list-none p-0">
            {w.evaluations.map((e) => (
              <li key={e.id} className="flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-[#15171a14] py-2.5">
                <Link href={`/compliance/evaluations#${encodeURIComponent(e.id)}`} className="min-w-[180px] flex-[1_1_220px] font-semibold hover:underline">{e.name}</Link>
                <EnginePill engine={e.engine} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

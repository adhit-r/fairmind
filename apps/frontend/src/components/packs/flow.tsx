'use client'

import { useEffect } from 'react'
import { Handle, MarkerType, Position, useNodesInitialized, useReactFlow, type Edge, type Node, type NodeProps } from 'reactflow'
import type { Step, StepKind } from '@/lib/api/hooks/usePacks'
import { MUTED } from '@/components/packs/parts'

export type NodeState = 'done' | 'current' | 'waiting' | 'idle'

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
export const KIND_LABEL: Record<StepKind, string> = {
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

export function KindIcon({ kind, size = 16 }: { kind: StepKind; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {(ICON[kind] ?? ICON.act).map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}

const PORT = '!h-2 !w-2 !border-2 !border-[var(--fm-ink3)] !bg-white'

function StepNode({ data }: NodeProps<{ step: Step; state: NodeState; selected?: boolean }>) {
  const { step, state, selected } = data
  const waiting = state === 'waiting'
  const detail = step.detail || (step.systems.length ? step.systems.join(', ') : '')
  return (
    <div
      title={KIND_LABEL[step.kind] ?? step.kind}
      className={[
        'relative flex h-[92px] w-[160px] items-start gap-2 rounded-xl p-2.5 text-left shadow-[0_1px_2px_#14141e0a,0_10px_24px_-14px_#14141e40]',
        waiting ? 'border-2 border-[var(--fm-brand)] bg-[#fff7f2]' : state === 'current' || selected ? 'border-2 border-[var(--fm-ink)] bg-white' : 'border border-[var(--fm-line)] bg-white',
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

export const nodeTypes = { step: StepNode }

/** Fit the whole flow once every node has been measured; the fitView prop runs too early. */
export function FitWhenReady() {
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
export function layout(steps: Step[]): Map<string, { x: number; y: number }> {
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


/** Nodes and edges for a workflow. With a run, edges it has travelled are solid and the rest dashed. */
export function flowGraph(
  steps: Step[],
  { stateOf = () => 'idle', run = false, selected = null }: { stateOf?: (id: string) => NodeState; run?: boolean; selected?: string | null } = {},
): { nodes: Node[]; edges: Edge[] } {
  const pos = layout(steps)
  const minY = Math.min(0, ...[...pos.values()].map((p) => p.y))
  const nodes: Node[] = steps.map((s) => {
    const p = pos.get(s.id) ?? { x: 0, y: 0 }
    return {
      id: s.id,
      type: 'step',
      position: { x: p.x, y: p.y - minY + 20 },
      data: { step: s, state: stateOf(s.id), selected: s.id === selected },
      draggable: false,
      selectable: false,
      connectable: false,
    }
  })
  const ids = new Set(steps.map((s) => s.id))
  const edges: Edge[] = steps.flatMap((s) =>
    s.next
      .filter((n) => ids.has(n.to))
      .map((n) => {
        const traced = run && stateOf(s.id) === 'done' && stateOf(n.to) !== 'idle'
        const untraced = run && !traced
        // A loop back (e.g. Revise -> Suggest) routes below the row instead of through the nodes.
        const back = (pos.get(n.to)?.x ?? 0) <= (pos.get(s.id)?.x ?? 0)
        return {
          id: `${s.id}>${n.to}>${n.label ?? ''}`,
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
}

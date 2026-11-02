'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import { GATE_KINDS, useDraft, usePackActions, useWorkflow, versionName, type Step, type StepKind } from '@/lib/api/hooks/usePacks'
import { FitWhenReady, KIND_LABEL, KindIcon, flowGraph, nodeTypes } from '@/components/packs/flow'
import { BTN, BTN_P, Crumbs, ErrorNote, Heading, LABEL, LINE, Loading, MUTED } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

/** Kinds a person can add; the start step is fixed and there is only one. */
const ADDABLE: StepKind[] = ['collect', 'check', 'suggest', 'preflight', 'ask', 'act', 'verify', 'escalate', 'file']
/** Branch names the run engine matches a gate decision against. */
const GATE_LABELS = ['approved', 'changes asked', 'rejected: reasons recorded', 'no decision by SLA']
const INPUT =
  'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-2.5 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'

function newId(kind: StepKind, steps: Step[]): string {
  let n = 1
  while (steps.some((s) => s.id === `${kind}-${n}`)) n++
  return `${kind}-${n}`
}

function Field({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-semibold text-[var(--fm-ink)]">{label}</label>
      {children}
    </div>
  )
}

export default function WorkflowBuilderPage() {
  const { workflowId } = useParams<{ workflowId: string }>()
  const router = useRouter()
  const wf = useWorkflow(workflowId)
  const draft = useDraft(wf.data?.draft ? workflowId : undefined)
  const { createDraft, saveDraft, discardDraft, publishDraft } = usePackActions()
  const [steps, setSteps] = useState<Step[] | null>(null)
  const [problems, setProblems] = useState<string[]>([])
  const [dirty, setDirty] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [busy, setBusy] = useState<'start' | 'save' | 'publish' | 'discard' | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  useEffect(() => {
    if (draft.data && steps === null) {
      setSteps(draft.data.steps)
      setProblems(draft.data.problems)
    }
  }, [draft.data, steps])

  useEffect(() => {
    if (!dirty) return
    const warn = (e: BeforeUnloadEvent) => e.preventDefault()
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const graph = useMemo(() => flowGraph(steps ?? [], { selected }), [steps, selected])
  const current = steps?.find((s) => s.id === selected) ?? null

  function update(next: Step[]) {
    setSteps(next)
    setDirty(true)
  }
  const patch = (id: string, change: Partial<Step>) => steps && update(steps.map((s) => (s.id === id ? { ...s, ...change } : s)))

  /** Insert a step after the selected one, taking over its single next step. */
  function add(kind: StepKind) {
    if (!steps || !current || current.next.length > 1) return
    const id = newId(kind, steps)
    const after = current.next[0]?.to
    const file = steps.find((s) => s.kind === 'file')?.id
    const gate = GATE_KINDS.includes(kind)
    const next = gate
      ? [...(after ? [{ to: after, label: 'approved' }] : []), ...(file && file !== after ? [{ to: file, label: 'rejected: reasons recorded' }] : [])]
      : after
        ? [{ to: after, label: null }]
        : []
    const step: Step = {
      id,
      kind,
      type: KIND_LABEL[kind],
      title: KIND_LABEL[kind],
      detail: '',
      systems: [],
      permission: null,
      runsWithoutApproval: gate ? 'No' : null,
      next,
      failure: null,
      output: null,
    }
    const at = steps.indexOf(current) + 1
    const rewired = steps.map((s) => (s.id === current.id ? { ...s, next: [{ to: id, label: current.next[0]?.label ?? null }] } : s))
    update([...rewired.slice(0, at), step, ...rewired.slice(at)])
    setSelected(id)
  }

  /** Remove a step; arrows into it go to its next step when it had exactly one, and are dropped otherwise. */
  function remove(id: string) {
    if (!steps) return
    const gone = steps.find((s) => s.id === id)
    if (!gone || gone.kind === 'trigger') return
    const onward = gone.next.length === 1 ? gone.next[0].to : null
    update(
      steps
        .filter((s) => s.id !== id)
        .map((s) => ({ ...s, next: s.next.flatMap((e) => (e.to !== id ? [e] : onward && onward !== s.id ? [{ ...e, to: onward }] : [])) })),
    )
    setSelected(null)
  }

  async function save(): Promise<string[] | null> {
    if (!steps) return null
    setBusy('save')
    setFailure(null)
    const res = await saveDraft(workflowId, steps)
    setBusy(null)
    if (res.error || !res.data) {
      setFailure(res.error ?? 'The draft could not be saved.')
      return null
    }
    setProblems(res.data.problems)
    setDirty(false)
    return res.data.problems
  }

  async function publish() {
    const found = dirty ? await save() : problems
    if (found === null || found.length > 0) return
    setBusy('publish')
    const res = await publishDraft(workflowId)
    setBusy(null)
    if (res.error) setFailure(res.error)
    else router.push(`/compliance/workflows/${workflowId}`)
  }

  async function discard() {
    if (!window.confirm('Discard this draft? Your edits are lost; runs keep using the published version.')) return
    setBusy('discard')
    const res = await discardDraft(workflowId)
    setBusy(null)
    if (res.error) setFailure(res.error)
    else router.push(`/compliance/workflows/${workflowId}`)
  }

  async function start() {
    setBusy('start')
    setFailure(null)
    const res = await createDraft(workflowId)
    setBusy(null)
    if (res.error) setFailure(res.error)
    wf.reload()
  }

  if ((wf.loading && !wf.data) || (wf.data?.draft && draft.loading && !draft.data)) return <Loading label="Loading draft" />
  if (wf.error || !wf.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Edit workflow' }]} />
        <ErrorNote message={`This workflow could not be loaded. ${wf.error ?? ''}`} onRetry={wf.reload} />
      </div>
    )
  }

  const w = wf.data
  const crumbs = [
    { label: 'Frameworks', href: '/compliance' },
    { label: w.pack.name, href: `/compliance/packs/${w.pack.id}` },
    { label: w.name, href: `/compliance/workflows/${w.id}` },
    { label: 'Edit' },
  ]

  if (!w.draft || !draft.data || !steps) {
    return (
      <div className="flex flex-col gap-[22px]">
        <Crumbs items={crumbs} />
        <Heading title={`Edit ${w.name}`} lead={`Runs use ${versionName(w.version)}. Start a draft from it to change the steps; nothing changes for runs until you publish.`}>
          <button type="button" className={BTN_P} onClick={start} disabled={!w.installed || busy !== null}>
            {busy === 'start' ? 'Starting draft' : 'Start a draft'}
          </button>
        </Heading>
        {draft.error && w.draft && <ErrorNote message={`The draft could not be loaded. ${draft.error}`} onRetry={draft.reload} />}
        {failure && <ErrorNote message={failure} />}
      </div>
    )
  }

  const d = draft.data
  const others = steps.filter((s) => s.id !== current?.id)
  const canAdd = current !== null && current.next.length <= 1

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={crumbs} />
      <Heading
        title={`Edit ${w.name}`}
        lead={`Draft of version ${d.version}, started from ${versionName(d.basedOn)}. Runs keep using ${versionName(w.version)} until you publish.`}
      >
        <button type="button" className={BTN} onClick={discard} disabled={busy !== null}>
          {busy === 'discard' ? 'Discarding' : 'Discard draft'}
        </button>
        <button type="button" className={BTN} onClick={save} disabled={!dirty || busy !== null}>
          {busy === 'save' ? 'Saving' : dirty ? 'Save draft' : 'Saved'}
        </button>
        <button type="button" className={BTN_P} onClick={publish} disabled={busy !== null || (!dirty && problems.length > 0)}>
          {busy === 'publish' ? 'Publishing' : `Publish version ${d.version}`}
        </button>
      </Heading>
      {failure && <ErrorNote message={failure} />}
      {problems.length > 0 && (
        <section aria-labelledby="problems-h" className="pk-card border border-[#f3c9a8] px-6 py-4">
          <h2 id="problems-h" className="m-0 text-sm font-semibold text-[#a8430b]">Fix before publishing</h2>
          <p className={cn('m-0 mt-0.5 text-[12.5px]', MUTED)}>Checked each time you save{dirty ? '; you have unsaved changes' : ''}.</p>
          <ul className="m-0 mt-2 flex list-disc flex-col gap-1 pl-5 text-[13px] text-[var(--fm-ink)]">
            {problems.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-wrap items-start gap-[22px]">
        <section aria-label="Workflow canvas" className="pk-card flex min-w-0 flex-[999_1_600px] flex-col overflow-hidden">
          <div className={cn('flex flex-wrap items-center gap-2 border-b px-5 py-3', LINE)}>
            <span className="mr-1 text-[13px] font-semibold text-[var(--fm-ink)]">Add a step</span>
            {ADDABLE.map((k) => (
              <button
                key={k}
                type="button"
                className={cn(BTN, 'h-8 gap-1.5 px-3 text-[12.5px]')}
                onClick={() => add(k)}
                disabled={!canAdd}
                aria-describedby="add-hint"
              >
                <KindIcon kind={k} size={14} />
                {KIND_LABEL[k]}
              </button>
            ))}
            <span id="add-hint" className={cn('basis-full text-[12px]', MUTED)}>
              {current === null
                ? 'Select a step; the new one goes after it.'
                : canAdd
                  ? `Adds after ${current.title}.`
                  : `${current.title} branches, so add after one of its branches instead.`}
            </span>
          </div>
          <div className="h-[520px] bg-[var(--fm-bg)]" role="group" aria-label={`Draft with ${steps.length} steps. Select a step to edit it.`}>
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable={false}
              onNodeClick={(_, node) => setSelected(node.id)}
              onPaneClick={() => setSelected(null)}
              minZoom={0.3}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} size={1} color="rgba(21,23,26,.12)" />
              <Controls showInteractive={false} />
              <FitWhenReady />
            </ReactFlow>
          </div>
        </section>

        <section aria-labelledby="step-h" className="pk-card flex min-w-0 flex-[1_1_340px] flex-col gap-4 px-5 py-5">
          <div className="flex flex-col gap-1.5">
            <h2 id="step-h" className="m-0 text-base font-semibold text-[var(--fm-ink)]">Selected step</h2>
            <label htmlFor="pick" className="sr-only">Step to edit</label>
            <select id="pick" className={INPUT} value={selected ?? ''} onChange={(e) => setSelected(e.target.value || null)}>
              <option value="">Choose a step</option>
              {steps.map((s, i) => (
                <option key={s.id} value={s.id}>{`${i + 1}. ${s.title}`}</option>
              ))}
            </select>
          </div>
          {!current ? (
            <p className={cn('m-0 text-[13px]', MUTED)}>Select a step on the canvas or in the list to change what it does and where it goes next.</p>
          ) : (
            <>
              <Field id="title" label="Name">
                <input id="title" className={INPUT} value={current.title} maxLength={200} onChange={(e) => patch(current.id, { title: e.target.value })} />
              </Field>
              {current.kind !== 'trigger' && (
                <Field id="kind" label="Kind">
                  <select
                    id="kind"
                    className={INPUT}
                    value={current.kind}
                    onChange={(e) => patch(current.id, { kind: e.target.value as StepKind, type: KIND_LABEL[e.target.value as StepKind] })}
                  >
                    {[...new Set([...ADDABLE, current.kind])].map((k) => (
                      <option key={k} value={k}>{KIND_LABEL[k]}</option>
                    ))}
                  </select>
                </Field>
              )}
              <Field id="detail" label="What it does">
                <textarea id="detail" rows={3} className={cn(INPUT, 'resize-y')} value={current.detail} onChange={(e) => patch(current.id, { detail: e.target.value })} />
              </Field>
              <Field id="systems" label="Systems (comma separated)">
                <input
                  id="systems"
                  className={INPUT}
                  value={current.systems.join(', ')}
                  onChange={(e) => patch(current.id, { systems: e.target.value.split(',').map((x) => x.trimStart()).filter((x, i, a) => x || i === a.length - 1) })}
                  onBlur={(e) => patch(current.id, { systems: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) })}
                />
              </Field>
              <Field id="output" label="Expected output">
                <input id="output" className={INPUT} value={current.output ?? ''} onChange={(e) => patch(current.id, { output: e.target.value || null })} />
              </Field>
              <Field id="failure" label="If it fails">
                <input id="failure" className={INPUT} value={current.failure ?? ''} onChange={(e) => patch(current.id, { failure: e.target.value || null })} />
              </Field>

              <fieldset className={cn('m-0 flex flex-col gap-2 border-0 border-t p-0 pt-4', LINE)}>
                <legend className={cn('mb-1', LABEL)}>Next steps</legend>
                {GATE_KINDS.includes(current.kind) && (
                  <p className={cn('m-0 text-[12.5px] leading-snug', MUTED)}>
                    Name each branch after the decision that takes it: approved, changes asked, rejected, or no decision by SLA.
                  </p>
                )}
                {current.next.length === 0 && <p className={cn('m-0 text-[13px]', MUTED)}>None: the run finishes after this step.</p>}
                {current.next.map((e, i) => (
                  <div key={i} className="flex flex-wrap items-center gap-2">
                    <label htmlFor={`to-${i}`} className="sr-only">Branch {i + 1} goes to</label>
                    <select
                      id={`to-${i}`}
                      className={cn(INPUT, 'min-w-0 flex-[1_1_140px]')}
                      value={e.to}
                      onChange={(ev) => patch(current.id, { next: current.next.map((x, j) => (j === i ? { ...x, to: ev.target.value } : x)) })}
                    >
                      {!steps.some((s) => s.id === e.to) && <option value={e.to}>Missing step</option>}
                      {others.map((s) => (
                        <option key={s.id} value={s.id}>{s.title}</option>
                      ))}
                    </select>
                    <label htmlFor={`label-${i}`} className="sr-only">Branch {i + 1} name</label>
                    <input
                      id={`label-${i}`}
                      className={cn(INPUT, 'min-w-0 flex-[1_1_120px]')}
                      placeholder={current.next.length > 1 || GATE_KINDS.includes(current.kind) ? 'Branch name' : 'Name (optional)'}
                      list="gate-labels"
                      value={e.label ?? ''}
                      onChange={(ev) => patch(current.id, { next: current.next.map((x, j) => (j === i ? { ...x, label: ev.target.value || null } : x)) })}
                    />
                    <button
                      type="button"
                      className={cn(BTN, 'h-9 w-9 px-0')}
                      aria-label={`Remove branch ${i + 1}`}
                      onClick={() => patch(current.id, { next: current.next.filter((_, j) => j !== i) })}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                        <path d="M18 6 6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
                <datalist id="gate-labels">
                  {GATE_LABELS.map((l) => (
                    <option key={l} value={l} />
                  ))}
                </datalist>
                <div>
                  <button
                    type="button"
                    className={cn(BTN, 'h-8 px-3 text-[12.5px]')}
                    disabled={others.length === 0}
                    onClick={() => patch(current.id, { next: [...current.next, { to: others[0].id, label: null }] })}
                  >
                    Add a branch
                  </button>
                </div>
              </fieldset>

              {current.kind !== 'trigger' && (
                <div className={cn('border-t pt-4', LINE)}>
                  <button type="button" className={cn(BTN, 'text-[#b42318]')} onClick={() => remove(current.id)}>
                    Delete step
                  </button>
                </div>
              )}
            </>
          )}
          <p className={cn('m-0 text-[12px]', MUTED)}>
            <Link href={`/compliance/workflows/${w.id}`} className="font-semibold text-[var(--fm-ink)] underline">Back to the workflow</Link>
            {dirty ? ' (save first to keep your edits)' : ''}
          </p>
        </section>
      </div>
    </div>
  )
}

'use client'

import { Check, CircleAlert, X, Database, GitBranch, MessageSquare, Search, Sparkles, Wrench, type LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { usePackActions, useTrace, type TraceStep } from '@/lib/api/hooks/usePacks'
import { RunExplanation, ShadedInput, Verdict } from '@/components/explain/ExplainParts'

const KIND: Record<TraceStep['kind'], { label: string; icon: LucideIcon }> = {
  llm: { label: 'Model', icon: Sparkles },
  tool: { label: 'Tool', icon: Wrench },
  retrieval: { label: 'Retrieval', icon: Search },
  memory: { label: 'Memory', icon: Database },
  decision: { label: 'Decision', icon: GitBranch },
  other: { label: 'Step', icon: GitBranch },
}
// A reason is expected where the system chose something: a model call, a tool call or a decision.
const EXPLAINS = new Set<TraceStep['kind']>(['llm', 'tool', 'decision'])
const MUTED = 'text-[var(--fm-ink2)]'

const text = (v: unknown) => (v === null || v === undefined ? '' : typeof v === 'string' ? v : JSON.stringify(v))

/** One live run: what was asked, each step with the reason the system stated, and the answer. `flag` marks why FairMind's check flagged it. */
export function TraceView({ systemId, traceId, flag }: { systemId: string; traceId: string; flag?: string }) {
  const res = useTrace(systemId, traceId)
  const { explainTrace } = usePackActions()
  const [explaining, setExplaining] = useState(false)
  const [failed, setFailed] = useState<string | null>(null)
  if (res.error) return <p className="m-0 text-[13px] text-[#b4232c]">This run could not be loaded. {res.error}</p>
  if (!res.data) return <p className={`m-0 text-[13px] ${MUTED}`}>Loading the run</p>
  const t = res.data.trace
  const e = t.explanation ?? null
  // The explanation sits on the step that made the decision: the last decision step, else the run's answer.
  const decisionAt = t.steps.map((s) => s.kind).lastIndexOf('decision')
  async function explain() {
    setExplaining(true)
    setFailed(null)
    const out = await explainTrace(systemId, traceId)
    setExplaining(false)
    if (out.error) setFailed(out.error)
    else res.reload()
  }
  const explainBlock = e ? <RunExplanation e={e} /> : t.explainable ? (
    <div className="flex flex-col gap-1.5">
      <button type="button" disabled={explaining} onClick={() => void explain()}
        className="self-start rounded-full border border-[var(--fm-line)] bg-white px-3 py-1 text-[12.5px] font-semibold text-[var(--fm-ink)] disabled:opacity-60">
        {explaining ? 'Explaining, about 20 replays' : 'Explain this decision'}
      </button>
      {failed && <span className="text-[12.5px] text-[#b4232c]">{failed}</span>}
    </div>
  ) : null
  const struck = e?.verdict === 'did not hold'
  const tone = t.status === 'error' ? 'bg-[#fde9ea] text-[#b4232c]' : t.status === 'running' ? 'bg-[#e6eefb] text-[#2457b8]' : 'bg-[#e3f2ea] text-[#1f7a4d]'
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2 text-[12px]">
        <span className={`rounded-md px-2 py-0.5 font-medium ${tone}`}>{t.status === 'ok' ? 'Finished' : t.status === 'error' ? 'Error' : 'Running'}</span>
        <span className={`font-mono ${MUTED}`}>{t.traceId}</span>
        {e && <Verdict v={e.verdict} />}
        <span className={MUTED}>{new Date(t.receivedAt).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
        {t.truncated && <span className={MUTED}>Long text was cut</span>}
      </div>
      {flag && <p className="m-0 rounded-[8px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">Flagged: {flag}</p>}
      {text(t.input) && (
        <div className="flex gap-2 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2.5 text-[13px]">
          <MessageSquare className="mt-0.5 size-3.5 shrink-0 text-[var(--fm-ink3)]" aria-label="Asked" />
          <span className="min-w-0 break-words">{e?.drivers?.length ? <ShadedInput text={text(t.input)} drivers={e.drivers} /> : text(t.input)}</span>
        </div>
      )}
      <ol className="m-0 flex list-none flex-col p-0">
        {t.steps.map((s, i) => {
          const { label, icon: Icon } = KIND[s.kind] ?? KIND.other
          const last = i === t.steps.length - 1
          return (
            <li key={s.id} className={`grid grid-cols-[26px_minmax(0,1fr)] gap-x-2.5 ${s.parentId ? 'ml-[18px]' : ''}`}>
              <div className="flex flex-col items-center">
                <span
                  title={label}
                  className={`grid size-[26px] place-items-center rounded-[7px] border ${s.status === 'error' ? 'border-[#b4232c] bg-[#fde9ea] text-[#b4232c]' : 'border-[rgba(21,23,26,.14)] bg-white text-[var(--fm-ink2)]'}`}
                >
                  <Icon className="size-3.5" aria-label={label} />
                </span>
                {!last && <span className="my-1 min-h-2 w-px flex-1 bg-[rgba(21,23,26,.14)]" />}
              </div>
              <div className="flex min-w-0 flex-col gap-1 pb-2.5">
                <span className="font-mono text-[12.5px] font-medium">{s.name || label}</span>
                {s.rationale ? (
                  i === decisionAt && struck ? (
                    <span className="flex gap-1.5 text-[12.5px] text-[var(--fm-ink)]"><X className="mt-0.5 size-3 shrink-0 text-[#b4232c]" aria-label="Did not hold" /><s className="decoration-[#b4232c]">{s.rationale}</s></span>
                  ) : (
                    <span className={`flex gap-1.5 text-[12.5px] ${MUTED}`}><Check className="mt-0.5 size-3 shrink-0 text-[#1f7a4d]" aria-hidden />{s.rationale}</span>
                  )
                ) : EXPLAINS.has(s.kind) && s.status !== 'running' ? (
                  <span className="flex gap-1.5 text-[12.5px] text-[#8a5200]"><CircleAlert className="mt-0.5 size-3 shrink-0" aria-hidden />No reason given</span>
                ) : null}
                {s.status === 'blocked' && <span className="text-[12.5px] text-[#8a5200]">Blocked by a guardrail</span>}
                {s.error && <span className="text-[12.5px] text-[#b4232c]">{s.error}</span>}
                {text(s.output) && (
                  <span className={`break-words rounded-[8px] border border-[var(--fm-line)] bg-white px-2.5 py-1.5 font-mono text-[11.5px] ${MUTED}`}>{text(s.output).slice(0, 600)}</span>
                )}
                {i === decisionAt && explainBlock}
              </div>
            </li>
          )
        })}
      </ol>
      {text(t.output) && (
        <div className="flex flex-col gap-1 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2.5 text-[13px]">
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]">Answered</span>
          <span className="break-words">{text(t.output)}</span>
          {t.rationale && <span className={`flex gap-1.5 text-[12.5px] ${MUTED}`}><Check className="mt-0.5 size-3 shrink-0 text-[#1f7a4d]" aria-hidden />{t.rationale}</span>}
          {decisionAt < 0 && explainBlock}
        </div>
      )}
      <p className={`m-0 text-[12px] ${MUTED}`}>{e && e.verdict !== 'not reproducible' ? 'The decision step\'s reason was checked by replaying the run; other reasons are as the system stated them.' : 'Reasons are as the system stated them; FairMind has not checked them.'}</p>
    </div>
  )
}

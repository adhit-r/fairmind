'use client'

import { useState } from 'react'
import { Check, Database, Loader2, Route, User, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAutopilot, type AutopilotMode, type AutopilotStep, type DataPurpose } from '@/lib/api/hooks/useAutopilot'
import { VERDICT_LABEL } from './VerdictExplainer'

const MODES: Array<{ key: AutopilotMode; label: string; hint: string }> = [
  { key: 'off', label: 'Off', hint: 'Nothing runs on its own' },
  { key: 'ask', label: 'Ask first', hint: 'The agent prepares; you run each step' },
  { key: 'run', label: 'Run', hint: 'Measurable steps run on a schedule; people still sign' },
]
const CLASS_LABEL: Record<string, string> = { measured: 'measured', tool_estimated: 'tool estimate', manual: 'attested' }
const ACTION_TEXT: Record<AutopilotStep['action'], (label: string) => string> = {
  fairness_run: () => 'Re-run the fairness test',
  monitoring_snapshot: () => 'Take a monitoring snapshot',
  environmental_assessment: () => 'Run an environmental assessment',
  attest: (label) => `Attest ${label.toLowerCase()}`,
  evidence_upload: (label) => `Record ${label.toLowerCase()} evidence`,
  request_release: () => 'Request the release decision',
}
const PURPOSE_TEXT: Record<DataPurpose, string> = {
  fairness: 'Fairness data: labelled decisions the agent re-tests',
  monitoring: 'Monitoring data: recent production decisions',
}

const pct = (v: number) => `${Math.max(0, Math.min(1, v)) * 100}%`
const ago = (iso: string) => {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  return mins < 60 ? `${Math.max(mins, 1)}m ago` : mins < 1440 ? `${Math.round(mins / 60)}h ago` : `${Math.round(mins / 1440)}d ago`
}

/** The release autopilot for one system: the route to its next verdict, who does each step, and what the agent did. */
export function AutopilotCard({ systemId, reloadKey, onChanged, onPersonStep }: {
  systemId: string
  reloadKey: unknown
  onChanged: () => void
  onPersonStep: (step: AutopilotStep) => void
}) {
  const ap = useAutopilot(systemId, reloadKey)
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [urls, setUrls] = useState<Record<DataPurpose, string>>({ fairness: '', monitoring: '' })
  const d = ap.data
  if (!d) return ap.error ? <section className="fm-card p-5 text-[13px] text-[var(--fm-ink2)]">{ap.error}</section> : null

  const act = async (key: string, fn: () => Promise<unknown>, changesEvidence = false) => {
    setBusy(key)
    setFailure(null)
    try {
      await fn()
      if (changesEvidence) onChanged()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setBusy(null)
    }
  }

  const target = d.target
  const agentSteps = d.steps.filter((s) => s.by === 'agent')
  const personSteps = d.steps.filter((s) => s.by === 'person')

  return (
    <section className="fm-card grid gap-4 p-5" aria-label="Release autopilot">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">
            <Route className="h-3.5 w-3.5 text-[var(--fm-brand)]" aria-hidden /> Release autopilot
          </div>
          <div className="mt-1 text-[15px] font-semibold tracking-[-0.01em]">
            {target ? `Route to ${VERDICT_LABEL[target.verdict as keyof typeof VERDICT_LABEL] ?? target.verdict}` : 'No route to a better verdict today'}
          </div>
          <div className="mt-0.5 text-[12.5px] text-[var(--fm-ink2)]">
            {agentSteps.length} by the agent · {personSteps.length} need a person{d.owner ? `, owner ${d.owner}` : ''}
          </div>
        </div>
        <div role="radiogroup" aria-label="Autopilot mode" className="ml-auto flex gap-0.5 rounded-full bg-[var(--fm-bg)] p-[3px]">
          {MODES.map((m) => (
            <button
              key={m.key}
              type="button"
              role="radio"
              aria-checked={d.mode === m.key}
              title={m.hint}
              disabled={busy !== null}
              onClick={() => d.mode !== m.key && act(`mode-${m.key}`, () => ap.setMode(m.key), m.key === 'run')}
              className={cn('rounded-full px-3 py-1 text-[12px] font-medium text-[var(--fm-ink2)]', d.mode === m.key && 'bg-[var(--fm-ink)] text-white')}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {target && (
        <div>
          <div className="relative h-2 rounded-full bg-[var(--fm-line)]" aria-hidden>
            <span className="absolute inset-y-0 left-0 rounded-full bg-[var(--fm-ink)]" style={{ width: pct(d.gate.confidence) }} />
            {d.afterAgent > d.gate.confidence && (
              <span className="fm-tex absolute inset-y-0" style={{ left: pct(d.gate.confidence), width: pct(d.afterAgent - d.gate.confidence) }} />
            )}
            <span className="absolute -top-1 h-4 w-0.5 rounded bg-[#1D9E75]" style={{ left: pct(target.confidence) }} />
          </div>
          <div className="mt-1.5 flex flex-wrap gap-x-4 text-[12px] tabular-nums text-[var(--fm-ink2)]">
            <span>Now {d.gate.confidence.toFixed(2)}</span>
            {d.afterAgent > d.gate.confidence && <span>After the agent {d.afterAgent.toFixed(2)}</span>}
            <span className="text-[#0F6E56]">With everyone {target.confidence.toFixed(2)}</span>
          </div>
        </div>
      )}

      <ul className="grid">
        {d.steps.map((s) => {
          const agent = s.by === 'agent'
          return (
            <li key={`${s.check}-${s.action}`} className="flex items-center gap-3 border-t border-[var(--fm-line)] py-2.5 text-[13px]">
              <span className={cn('grid h-6 w-6 flex-none place-items-center rounded-full', agent ? 'bg-[var(--fm-bg)] text-[var(--fm-ink)]' : 'bg-[#fff1ea] text-[var(--fm-brand)]')} aria-hidden>
                {agent ? <Database className="h-3.5 w-3.5" /> : <User className="h-3.5 w-3.5" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="font-medium">{ACTION_TEXT[s.action]?.(s.label) ?? s.label}</span>
                <span className="block truncate text-[12px] text-[var(--fm-ink3)]">
                  {agent ? (s.upkeep ? 'The agent keeps this fresh on its cadence' : 'The agent runs this from the data source') : s.needs ?? (d.owner ? `For ${d.owner}` : 'For the system owner')}
                </span>
              </span>
              {s.evidenceClass && <span className="hidden rounded-full border border-[var(--fm-line)] px-2 py-0.5 text-[11px] text-[var(--fm-ink2)] sm:inline">{CLASS_LABEL[s.evidenceClass]}</span>}
              {s.gain > 0 && <span className="w-11 text-right text-[12px] tabular-nums text-[var(--fm-ink2)]">+{s.gain.toFixed(2)}</span>}
              {agent ? (
                <button type="button" disabled={busy !== null} onClick={() => act(`run-${s.action}`, () => ap.runNow(s.action), true)} className="inline-flex h-8 items-center gap-1.5 rounded-full border border-[var(--fm-line)] bg-white px-3 text-[12px] font-medium hover:border-[var(--fm-ink)] disabled:opacity-60">
                  {busy === `run-${s.action}` && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />}
                  {busy === `run-${s.action}` ? 'Running' : 'Run now'}
                </button>
              ) : (
                <button type="button" onClick={() => onPersonStep(s)} className="inline-flex h-8 items-center rounded-full bg-[var(--fm-ink)] px-3 text-[12px] font-semibold text-white">
                  Open
                </button>
              )}
            </li>
          )
        })}
        {d.steps.length === 0 && (
          <li className="grid gap-1 border-t border-[var(--fm-line)] py-2.5 text-[13px] text-[var(--fm-ink2)]">
            {(d.notes.length ? d.notes : ['Nothing on the route today.']).map((n) => <p key={n}>{n}</p>)}
          </li>
        )}
      </ul>

      <div className="grid gap-2 rounded-[10px] bg-[var(--fm-bg)] p-3">
        <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Data the agent can use</div>
        {!d.canConnect && <p className="text-[12.5px] text-[var(--fm-ink2)]">Run a fairness test below and confirm its protected attributes first. The agent reuses those columns and attributes and never picks its own.</p>}
        {(['fairness', 'monitoring'] as DataPurpose[]).map((p) => {
          const src = d.sources[p]
          return (
            <div key={p} className="flex flex-wrap items-center gap-2 text-[12.5px]">
              <span className="min-w-[220px] flex-1 text-[var(--fm-ink2)]">{PURPOSE_TEXT[p]}</span>
              {src ? (
                <>
                  <span className="max-w-[280px] truncate font-medium" title={src.url ?? src.fileName ?? undefined}>{src.kind === 'url' ? src.url : `Kept file ${src.fileName ?? ''}`}</span>
                  <button type="button" aria-label={`Remove the ${p} data source`} disabled={busy !== null} onClick={() => act(`rm-${p}`, () => ap.removeSource(p))} className="grid h-7 w-7 place-items-center rounded-full text-[var(--fm-ink3)] hover:bg-white hover:text-[var(--fm-ink)]">
                    <X className="h-3.5 w-3.5" aria-hidden />
                  </button>
                </>
              ) : (
                <form
                  className="flex min-w-[260px] flex-1 items-center gap-1.5"
                  onSubmit={(e) => {
                    e.preventDefault()
                    if (urls[p].trim()) void act(`src-${p}`, () => ap.setSource(p, urls[p].trim()).then(() => setUrls((u) => ({ ...u, [p]: '' }))))
                  }}
                >
                  <input
                    type="url"
                    value={urls[p]}
                    onChange={(e) => setUrls((u) => ({ ...u, [p]: e.target.value }))}
                    disabled={!d.canConnect}
                    placeholder="https://exports.example.com/decisions.csv"
                    aria-label={`${p} data URL`}
                    className="h-8 min-w-0 flex-1 rounded-[10px] border border-[var(--fm-line)] bg-white px-2.5 text-[12.5px] outline-none focus:border-[var(--fm-ink)] disabled:opacity-60"
                  />
                  <button type="submit" disabled={!d.canConnect || busy !== null || !urls[p].trim()} className="h-8 rounded-full border border-[var(--fm-line)] bg-white px-3 text-[12px] font-medium hover:border-[var(--fm-ink)] disabled:opacity-60">Connect</button>
                </form>
              )}
            </div>
          )
        })}
        {d.canConnect && !d.sources.fairness && <p className="text-[11.5px] text-[var(--fm-ink3)]">Or tick &quot;Keep this file&quot; on your next fairness test.</p>}
      </div>

      {failure && <div className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-[12.5px] text-red-700">{failure}</div>}

      {d.events.length > 0 && (
        <div>
          <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Agent trace</div>
          <ul className="mt-1.5 grid gap-1">
            {d.events.slice(0, 6).map((e, i) => (
              <li key={i} className="flex items-center gap-2 text-[12.5px]">
                {e.status === 'done' ? <Check className="h-3.5 w-3.5 flex-none text-[#0F6E56]" aria-hidden /> : <X className="h-3.5 w-3.5 flex-none text-[#A32D2D]" aria-hidden />}
                <span className={cn('min-w-0 flex-1 truncate', e.status === 'failed' && 'text-[#A32D2D]')}>{e.detail}</span>
                <span className="flex-none text-[11.5px] text-[var(--fm-ink3)]">{e.actor === 'autopilot' ? 'scheduled' : e.actor} · {ago(e.at)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-1.5 text-[11.5px] text-[var(--fm-ink3)]">Each run is measured evidence on the system&apos;s record, with the data fingerprint and the attributes a person confirmed.</p>
        </div>
      )}
    </section>
  )
}

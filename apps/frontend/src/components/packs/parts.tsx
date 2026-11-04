import Link from 'next/link'
import './iso.css'
import type { ReactNode } from 'react'
import type { EngineStatus, ReqStatus, ResultStatus, RunStatus } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'

/** Class strings shared by the pack screens; they follow the approved design (pill buttons, soft pills). */
export const BTN =
  'inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-full border border-[var(--fm-line)] bg-white px-[18px] text-[13px] font-semibold text-[var(--fm-ink)] transition-colors hover:border-[var(--fm-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-[var(--fm-line)]'
export const BTN_P = cn(BTN, 'border-transparent bg-[var(--fm-ink)] text-white hover:border-transparent hover:bg-black disabled:hover:border-transparent disabled:hover:bg-[var(--fm-ink)]')
export const MUTED = 'text-[var(--fm-ink2)]'
/** Small uppercase section label (10-11px only, per the design). */
export const LABEL = 'text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]'
/** Hairline row divider. */
export const LINE = 'border-[var(--fm-line)]'

type Tone = 'plain' | 'you' | 'done' | 'run' | 'block' | 'info' | 'warn'
const TONE: Record<Tone, string> = {
  plain: 'bg-[var(--fm-bg)] text-[var(--fm-ink2)]',
  you: 'bg-[#ffeee4] text-[#a8430b]',
  done: 'bg-[#e3f5ec] text-[#00704e]',
  run: 'bg-[rgba(21,23,26,.06)] text-[var(--fm-ink)]',
  block: 'bg-[#fde8e8] text-[#b42318]',
  info: 'bg-[#e6effb] text-[#1d4f91]',
  warn: 'bg-[#fff4d6] text-[#8a5a00]',
}

export function Pill({ tone = 'plain', dot, children }: { tone?: Tone; dot?: boolean; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-[3px] text-[11.5px] font-semibold', TONE[tone])}>
      {dot && <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}

const RESULT: Record<ResultStatus, { label: string; tone: Tone }> = {
  passed: { label: 'Passed', tone: 'done' },
  failed: { label: 'Failed', tone: 'block' },
  insufficient: { label: 'Insufficient data', tone: 'warn' },
  not_run: { label: 'Not run yet', tone: 'plain' },
}

/** An evaluation's result on a system, or across the organisation's systems. */
export function ResultPill({ status }: { status: ResultStatus }) {
  return <Pill tone={RESULT[status].tone}>{RESULT[status].label}</Pill>
}

/** The catalogue names 12 workflow stages; each belongs to one of the five lifecycle stages in the menu. */
const LIFECYCLE: Record<string, string> = {
  map: 'Onboard',
  assess: 'Assess',
  test: 'Assess',
  measure: 'Assess',
  govern: 'Govern',
  manage: 'Govern',
  build: 'Govern',
  deploy: 'Govern',
  respond: 'Remediate',
  improve: 'Remediate',
  operate: 'Operate',
  retire: 'Operate',
}
/** The lifecycle stage a catalogue stage belongs to; an unknown stage is shown as the catalogue names it. */
export const lifecycleStage = (stage: string) => LIFECYCLE[stage.toLowerCase()] ?? cap(stage)

/** A workflow's lifecycle stage, with the catalogue's finer stage on hover when it differs. */
export function StagePill({ stage }: { stage: string }) {
  const life = lifecycleStage(stage)
  const fine = cap(stage)
  return (
    <span title={fine === life ? undefined : `Catalogue stage: ${fine}`}>
      <Pill>{life}</Pill>
    </span>
  )
}

const STATUS: Record<RunStatus, { label: string; tone: Tone }> = {
  queued: { label: 'Queued', tone: 'plain' },
  running: { label: 'Running', tone: 'run' },
  waiting: { label: 'Needs you', tone: 'you' },
  blocked: { label: 'Blocked', tone: 'block' },
  done: { label: 'Done', tone: 'done' },
  failed: { label: 'Failed', tone: 'block' },
}

export function StatusPill({ status }: { status: RunStatus | null | undefined }) {
  if (!status) return <Pill>Not started</Pill>
  return <Pill tone={STATUS[status].tone} dot={status === 'waiting'}>{STATUS[status].label}</Pill>
}

/** Requirement coverage on a journey; the same words and colours everywhere. */
const REQ: Record<ReqStatus, { label: string; tone: Tone; hint: string }> = {
  covered: { label: 'Covered', tone: 'done', hint: 'An installed workflow covers this requirement.' },
  tested: { label: 'Tested', tone: 'info', hint: 'An evaluation that tests this requirement passed on your AI systems.' },
  available: { label: 'Available', tone: 'you', hint: 'A pack that is not installed would cover it, or an evaluation would test it once it passes.' },
  supported: { label: 'Supported', tone: 'plain', hint: 'Workflows only support this requirement; none satisfies it.' },
  gap: { label: 'Gap', tone: 'block', hint: 'Nothing in the catalogue maps to this requirement.' },
}
export const REQ_ORDER: ReqStatus[] = ['covered', 'tested', 'available', 'supported', 'gap']
export const reqLabel = (s: ReqStatus) => REQ[s].label
export const reqHint = (s: ReqStatus) => REQ[s].hint

export function ReqPill({ status }: { status: ReqStatus }) {
  return (
    <span title={REQ[status].hint}>
      <Pill tone={REQ[status].tone}>{REQ[status].label}</Pill>
    </span>
  )
}

const ENGINE: Record<EngineStatus, { label: string; tone: Tone }> = {
  'Engine exists': { label: 'Engine exists', tone: 'done' },
  Partial: { label: 'Partial', tone: 'warn' },
  'Not found': { label: 'Not built yet', tone: 'plain' },
}

export function EnginePill({ engine }: { engine: EngineStatus }) {
  const e = ENGINE[engine] ?? { label: String(engine), tone: 'plain' as Tone }
  return <Pill tone={e.tone}>{e.label}</Pill>
}

/** Installed coverage (dark) over what every pack would cover (light), out of the active requirements. */
export function CoverageBar({ installed, all, total, label, allLabel = 'with every pack' }: { installed: number; all: number; total: number; label: string; allLabel?: string }) {
  const pct = (n: number) => (total > 0 ? Math.min(100, Math.round((n / total) * 100)) : 0)
  return (
    <div className="flex flex-col gap-1">
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={installed}
        aria-valuetext={`${installed} of ${total} requirements covered by installed packs, ${all} ${allLabel}`}
        className="relative h-2 w-full overflow-hidden rounded-full bg-[rgba(21,23,26,.06)]"
      >
        <div className="absolute inset-y-0 left-0 bg-[#a9d6bf]" style={{ width: `${pct(all)}%` }} />
        <div className="absolute inset-y-0 left-0 bg-[#009869]" style={{ width: `${pct(installed)}%` }} />
      </div>
      <span className={cn('text-[12px] tabular-nums', MUTED)}>
        {installed} of {total} covered. {all} {allLabel}.
      </span>
    </div>
  )
}

export const cap = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s)

/** Orange numbered disc; the number matches the agent in the figure. */
export function Num({ n }: { n: number }) {
  return (
    <span className="inline-flex h-[22px] w-[22px] flex-none items-center justify-center rounded-full bg-[var(--fm-brand)] text-xs font-bold text-[var(--fm-ink)]">
      {n}
    </span>
  )
}

export function Crumbs({ items }: { items: Array<{ label: string; href?: string }> }) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex flex-wrap gap-1.5 text-[13px]', MUTED)}>
      {items.map((c, i) => (
        <span key={c.label} className="flex gap-1.5">
          {i > 0 && <span aria-hidden>/</span>}
          {c.href ? (
            <Link href={c.href} className="hover:text-[var(--fm-ink)]">{c.label}</Link>
          ) : (
            <span className="font-semibold text-[var(--fm-ink)]">{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}

export function Heading({ title, lead, children }: { title: string; lead?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex max-w-[720px] flex-col gap-2">
        <h1 className="m-0 text-[28px] font-semibold tracking-[-0.02em] text-[var(--fm-ink)]">{title}</h1>
        {lead && <p className={cn('m-0 text-[15px] leading-normal', MUTED)}>{lead}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2.5">{children}</div>}
    </div>
  )
}

export function Loading({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col gap-4">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-black/5" />
      <div className="h-72 animate-pulse rounded-[14px] bg-black/5" />
      <span className="sr-only">{label}</span>
    </div>
  )
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl bg-[#fde8e8] px-4 py-3 text-[13px] text-[#b42318]">
      <span className="min-w-0 flex-1 font-medium">{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="font-semibold underline">
          Try again
        </button>
      )}
    </div>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className={cn('m-0 rounded-xl border border-dashed border-[rgba(21,23,26,.16)] px-4 py-6 text-center text-[13px]', MUTED)}>{children}</p>
}

export function when(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

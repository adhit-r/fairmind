import Link from 'next/link'
import type { ReactNode } from 'react'
import type { RunStatus } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'

/** Class strings shared by the pack screens; they follow the approved design (pill buttons, soft pills). */
export const BTN =
  'inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-full border border-[#15171a24] bg-white px-[18px] text-[13px] font-semibold text-[var(--fm-ink)] hover:bg-[#f4f4f2] disabled:cursor-not-allowed disabled:opacity-50'
export const BTN_P = cn(BTN, 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white hover:bg-[#2b2e3a]')
export const MUTED = 'text-[var(--fm-ink2)]'

type Tone = 'plain' | 'you' | 'done' | 'run' | 'block'
const TONE: Record<Tone, string> = {
  plain: 'bg-[#f4f4f2] text-[#5a5f68]',
  you: 'bg-[#ffeee4] text-[#a8430b]',
  done: 'bg-[#e3f5ec] text-[#00704e]',
  run: 'bg-[#eceef1] text-[#15171a]',
  block: 'bg-[#fde8e8] text-[#b42318]',
}

export function Pill({ tone = 'plain', dot, children }: { tone?: Tone; dot?: boolean; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-[3px] text-[11.5px] font-semibold', TONE[tone])}>
      {dot && <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
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
        <h1 className="m-0 text-[28px] font-semibold tracking-[-0.02em]">{title}</h1>
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
  return <p className={cn('m-0 rounded-xl border border-dashed border-[#15171a24] px-4 py-6 text-center text-[13px]', MUTED)}>{children}</p>
}

export function when(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

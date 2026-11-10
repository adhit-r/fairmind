'use client'

import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import { AlertTriangle, FileCheck2, FileOutput, FileText, ListChecks, Plug, Scale, Settings, Sparkles, type LucideIcon } from 'lucide-react'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { usePendingDecisions } from '@/lib/api/hooks/usePendingDecisions'
import { useAIProvider, useRuns, useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { useSession } from '@/context/SessionContext'
import { cn } from '@/lib/utils'
import { AskPanel } from './AskPanel'

export const STAGES: Array<{ key: AISystemSummary['stage']; label: string }> = [
  { key: 'onboard', label: 'Onboard' },
  { key: 'assess', label: 'Assess' },
  { key: 'govern', label: 'Govern' },
  { key: 'remediate', label: 'Remediate' },
  { key: 'operate', label: 'Operate' },
]

const LIBRARY: Array<{ section: string; links: Array<{ label: string; href: string; icon: LucideIcon }> }> = [
  {
    section: 'Records',
    links: [
      { label: 'Plan', href: '/plan', icon: ListChecks },
      { label: 'Findings', href: '/risks', icon: AlertTriangle },
      { label: 'Evidence', href: '/evidence', icon: FileCheck2 },
      { label: 'Exports', href: '/audit-reports', icon: FileOutput },
    ],
  },
  {
    section: 'Setup',
    links: [
      { label: 'Integrations', href: '/integrations', icon: Plug },
      { label: 'Frameworks', href: '/frameworks', icon: Scale },
      { label: 'Policies', href: '/policies', icon: FileText },
      { label: 'Settings', href: '/settings', icon: Settings },
    ],
  },
]

/** Release requests for systems in this estate plus workflow runs paused for a person: everything waiting on a decision. */
function useDecisions() {
  const { systems } = useSystemContext()
  const { requests: allRequests } = usePendingDecisions()
  // Approval requests are not org-scoped yet; count only those for systems in this estate.
  const requests = allRequests.filter((r) => systems.some((s) => s.id === r.entity_id))
  const waitingRuns = useWaitingRuns().data ?? []
  return { requests, count: requests.length + waitingRuns.length }
}

function initials(text: string) {
  return text
    .split(/[\s@._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('')
}

/** The lifecycle, drawn as a spine. Each station carries its live count. */
function Spine() {
  const { systems } = useSystemContext()
  const { requests, count: decisions } = useDecisions()
  const pathname = usePathname()
  const params = useSearchParams()
  // On a system page the station is that system's stage, or Decision while its release decision is pending.
  const systemId = pathname.match(/^\/systems\/([^/]+)/)?.[1]
  const viewed = systemId ? systems.find((s) => s.id === decodeURIComponent(systemId)) : undefined
  const activeStage = pathname === '/dashboard' ? params.get('stage') : viewed ? (requests.some((r) => r.entity_id === viewed.id) ? 'decision' : viewed.stage) : null
  const counts = systems.reduce<Record<string, number>>((acc, s) => {
    acc[s.stage] = (acc[s.stage] ?? 0) + 1
    return acc
  }, {})
  const stations = [
    ...STAGES.slice(0, 4).map((s) => ({ ...s, count: counts[s.key] ?? 0, hot: false })),
    { key: 'decision', label: 'Decision', count: decisions, hot: decisions > 0, href: '/compliance/runs' },
    { ...STAGES[4], count: counts.operate ?? 0, hot: false },
  ]

  return (
    <nav aria-label="Lifecycle" className="fm-strip relative mt-1.5 pl-1.5 max-md:mt-2 max-md:flex max-md:gap-1.5 max-md:overflow-x-auto max-md:pl-0">
      <span aria-hidden className="absolute bottom-3 left-[11px] top-3 w-0.5 rounded bg-[var(--fm-line)] max-md:hidden" />
      {stations.map((s) => {
        const on = activeStage === s.key || (s.key === 'decision' && pathname.startsWith('/compliance/runs'))
        return (
          <Link
            key={s.key}
            href={'href' in s && s.href ? s.href : `/dashboard?stage=${s.key}`}
            aria-current={on ? 'step' : undefined}
            className={cn(
              'relative flex h-[34px] items-center gap-3 pr-2.5 text-[13px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]',
              'max-md:h-8 max-md:flex-none max-md:gap-2 max-md:rounded-full max-md:border max-md:border-[var(--fm-line)] max-md:bg-white max-md:px-2.5',
              (on || s.hot) && 'text-[var(--fm-ink)]',
            )}
          >
            {s.hot && <span aria-hidden className="absolute -top-3.5 left-[5px] z-10 h-5 w-0.5 rounded bg-[var(--fm-brand)] max-md:hidden" />}
            <i
              className={cn(
                'relative z-10 h-3 w-3 flex-none rounded-full border-2 border-[#c3c6cc] bg-[var(--fm-bg)]',
                on && 'border-[var(--fm-ink)] bg-[var(--fm-ink)]',
                s.hot && 'border-[var(--fm-brand)] bg-[var(--fm-brand)] shadow-[0_0_0_4px_rgba(255,107,53,.18)]',
              )}
            />
            {s.label}
            <em
              className={cn(
                'ml-auto text-[12.5px] not-italic tabular-nums text-[var(--fm-ink3)] max-md:ml-0',
                s.hot && 'rounded-full bg-[var(--fm-brand)] px-[7px] py-px text-[11.5px] font-semibold text-white',
              )}
            >
              {s.count}
            </em>
          </Link>
        )
      })}
    </nav>
  )
}

function OrgBlock() {
  const { organizations, selectedOrg, selectOrg } = useOrg()
  if (!selectedOrg) return null
  return (
    <div className="mt-[18px] flex items-center gap-2 rounded-[10px] border border-[var(--fm-line)] bg-white px-2.5 py-2 shadow-[0_1px_2px_rgba(20,20,30,.04)]">
      <span className="grid h-[26px] w-[26px] flex-none place-items-center rounded-[7px] bg-[#2b2e3a] text-[11px] font-semibold text-white">
        {initials(selectedOrg.name)}
      </span>
      {organizations.length > 1 ? (
        <select
          aria-label="Organisation"
          value={selectedOrg.id}
          onChange={(e) => selectOrg(e.target.value)}
          className="min-w-0 flex-1 bg-transparent text-[13px] font-semibold outline-none"
        >
          {organizations.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
      ) : (
        <span className="min-w-0">
          <b className="block truncate text-[13px] font-semibold leading-tight">{selectedOrg.name}</b>
          <small className="block text-[11.5px] capitalize text-[var(--fm-ink2)]">{selectedOrg.role}</small>
        </span>
      )}
    </div>
  )
}

/** What the organisation's agent is doing now, and which model it uses. */
function AgentStatus() {
  const runs = useRuns().data ?? []
  const config = useAIProvider().data?.config
  const active = runs.filter((r) => r.status === 'running' || r.status === 'queued').length
  return (
    <Link href="/org-admin/settings" className="flex items-center gap-2 border-t border-[var(--fm-line)] px-2 pb-1 pt-3 text-[12px] text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]">
      <span aria-hidden className={cn('h-1.5 w-1.5 flex-none rounded-full', active ? 'animate-pulse bg-[#1D9E75]' : 'bg-[#c3c6cc]')} />
      {active ? `Agent: ${active} run${active === 1 ? '' : 's'} active` : 'Agent idle'}
      <span className="ml-auto truncate text-[var(--fm-ink3)]">{config?.enabled ? config.providerName : 'Rules only'}</span>
    </Link>
  )
}

function TodayLink() {
  const { count } = useDecisions()
  return (
    <Link
      href="/dashboard"
      className="mt-3 flex items-center justify-between rounded-[10px] bg-[var(--fm-ink)] px-2.5 py-2 pl-3 text-[13px] font-semibold text-white max-md:mt-3"
    >
      Today
      {count > 0 ? (
        <small className="rounded-full bg-[var(--fm-brand)] px-[7px] py-px text-[11.5px] font-semibold text-white">{count} need you</small>
      ) : (
        <small className="text-[11.5px] font-medium text-white/60">{new Date().toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}</small>
      )}
    </Link>
  )
}

function Me() {
  // The shell reads the one verified session, so logout here also clears sibling tabs.
  const { user, logout } = useSession()
  const router = useRouter()
  if (!user) return null
  const name = user.username || user.email
  return (
    <div className="mt-2 flex items-center gap-2.5 px-2 py-1.5">
      <span className="grid h-8 w-8 flex-none place-items-center rounded-full bg-[#2b2e3a] text-[11px] font-semibold text-white">
        {initials(name)}
      </span>
      <span className="min-w-0 flex-1">
        <b className="block truncate text-[13px] font-semibold leading-tight">{name}</b>
        <small className="block truncate text-[11.5px] capitalize text-[var(--fm-ink2)]">{user.role ?? user.email}</small>
      </span>
      <button
        type="button"
        onClick={() => logout().finally(() => router.push('/login'))}
        className="text-[11.5px] font-medium text-[var(--fm-ink3)] hover:text-[var(--fm-ink)]"
      >
        Sign out
      </button>
    </div>
  )
}

function LibraryNav() {
  const pathname = usePathname()
  return (
    <>
      {LIBRARY.map((group) => (
        <div key={group.section}>
          <div className="fm-sec">{group.section}</div>
          <nav aria-label={group.section} className="fm-strip max-md:flex max-md:gap-1.5 max-md:overflow-x-auto">
            {group.links.map(({ label, href, icon: Icon }) => {
              const on = pathname === href || pathname.startsWith(`${href}/`)
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={on ? 'page' : undefined}
                  className={cn(
                    'flex h-8 items-center gap-2.5 rounded-lg px-2.5 text-[13px] font-medium text-[var(--fm-ink2)] hover:bg-white hover:text-[var(--fm-ink)]',
                    'max-md:flex-none max-md:rounded-full max-md:border max-md:border-[var(--fm-line)] max-md:bg-white',
                    on && 'bg-white text-[var(--fm-ink)] shadow-[0_1px_2px_rgba(20,20,30,.04)]',
                  )}
                >
                  <Icon className={cn('h-4 w-4 flex-none text-[var(--fm-ink3)] max-md:hidden', on && 'text-[var(--fm-ink)]')} aria-hidden />
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
      ))}
    </>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [asking, setAsking] = useState(false)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setAsking((open) => !open)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  return (
    <div className="grid min-h-screen grid-cols-[minmax(0,1fr)] items-start bg-[var(--fm-bg)] text-[var(--fm-ink)] md:grid-cols-[236px_minmax(0,1fr)]">
      <aside className="flex flex-col px-3 pb-4 pl-5 pt-5 max-md:px-4 max-md:pb-0 max-md:pt-3.5 md:sticky md:top-0 md:h-screen md:overflow-y-auto">
        <div className="flex items-center justify-between px-2 max-md:px-0">
          <Link href="/dashboard" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight">
            <span className="h-6 w-6 overflow-hidden rounded-full"><img src="/logo.png" alt="" className="h-full w-full scale-[1.35] object-cover" /></span>
            FairMind
          </Link>
        </div>
        <div className="max-md:hidden">
          <OrgBlock />
        </div>
        <button
          type="button"
          onClick={() => setAsking(true)}
          className="mt-3 flex items-center gap-2 rounded-full border border-[var(--fm-ink)] bg-white px-3 py-1.5 text-left text-[13px] font-medium text-[var(--fm-ink)] hover:bg-[var(--fm-bg)]"
        >
          <Sparkles className="h-[15px] w-[15px] text-[var(--fm-brand)]" aria-hidden />
          <span className="flex-1">Ask FairMind</span>
          <kbd className="rounded-[5px] border border-[var(--fm-line)] px-1.5 font-sans text-[11px] text-[var(--fm-ink3)] max-md:hidden">⌘K</kbd>
        </button>
        <Suspense fallback={null}>
          <TodayLink />
        </Suspense>
        <div className="fm-sec">Lifecycle</div>
        <Suspense fallback={null}>
          <Spine />
        </Suspense>
        <LibraryNav />
        <div className="mt-auto pt-4 max-md:hidden">
          <AgentStatus />
          <Me />
        </div>
      </aside>
      <main className="min-w-0 px-7 pb-16 pl-3.5 pt-[22px] max-md:px-4 max-md:pb-12 max-md:pt-3.5">{children}</main>
      <AskPanel open={asking} onOpenChange={setAsking} />
    </div>
  )
}

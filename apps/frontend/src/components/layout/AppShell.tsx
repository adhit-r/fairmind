'use client'

import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { usePendingDecisions } from '@/lib/api/hooks/usePendingDecisions'
import { useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { useSession } from '@/context/SessionContext'
import { cn } from '@/lib/utils'

export const STAGES: Array<{ key: AISystemSummary['stage']; label: string }> = [
  { key: 'onboard', label: 'Onboard' },
  { key: 'assess', label: 'Assess' },
  { key: 'govern', label: 'Govern' },
  { key: 'remediate', label: 'Remediate' },
  { key: 'operate', label: 'Operate' },
]

const LIBRARY = [
  { label: 'Plan', href: '/plan' },
  { label: 'Integrations', href: '/integrations' },
  { label: 'Frameworks', href: '/frameworks' },
  { label: 'Policies', href: '/policies' },
  { label: 'Evidence', href: '/evidence' },
  { label: 'Findings', href: '/risks' },
  { label: 'Exports', href: '/audit-reports' },
  { label: 'Settings', href: '/settings' },
]

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
  const { requests: allRequests } = usePendingDecisions()
  // Approval requests are not org-scoped yet; count only those for systems in this estate.
  const requests = allRequests.filter((r) => systems.some((s) => s.id === r.entity_id))
  // Workflow runs paused for a person's input or approval are decisions too.
  const waitingRuns = useWaitingRuns().data ?? []
  const decisions = requests.length + waitingRuns.length
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

function Me() {
  // The shell reads the one verified session, so logout here also clears sibling tabs.
  const { user, logout } = useSession()
  const router = useRouter()
  if (!user) return null
  const name = user.username || user.email
  return (
    <div className="mt-auto flex items-center gap-2.5 px-2 py-1.5">
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

export function AppShell({ children }: { children: React.ReactNode }) {
  const today = new Date().toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
  return (
    <div className="grid min-h-screen grid-cols-[minmax(0,1fr)] items-start bg-[var(--fm-bg)] text-[var(--fm-ink)] md:grid-cols-[236px_minmax(0,1fr)]">
      <aside className="flex flex-col px-3 pb-4 pl-5 pt-5 max-md:px-4 max-md:pb-0 max-md:pt-3.5 md:sticky md:top-0 md:h-screen">
        <div className="flex items-center justify-between px-2 max-md:px-0">
          <Link href="/dashboard" className="flex items-center gap-2 text-[15px] font-bold tracking-tight">
            <i className="h-[22px] w-[22px] rounded-md bg-[var(--fm-brand)]" />
            FairMind
          </Link>
        </div>
        <div className="max-md:hidden">
          <OrgBlock />
        </div>
        <Link
          href="/dashboard"
          className="mt-[22px] flex items-center justify-between rounded-[10px] bg-[var(--fm-ink)] px-2.5 py-2 pl-3 text-[13px] font-semibold text-white max-md:mt-3"
        >
          Today <small className="text-[11.5px] font-medium text-white/60">{today}</small>
        </Link>
        <div className="fm-sec">Lifecycle</div>
        <Suspense fallback={null}>
          <Spine />
        </Suspense>
        <div className="fm-sec">Library</div>
        <nav className="fm-strip max-md:flex max-md:gap-1.5 max-md:overflow-x-auto">
          {LIBRARY.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="flex h-8 items-center rounded-lg px-2.5 text-[13px] font-medium text-[var(--fm-ink2)] hover:bg-white hover:text-[var(--fm-ink)] max-md:flex-none max-md:rounded-full max-md:border max-md:border-[var(--fm-line)] max-md:bg-white"
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="max-md:hidden">
          <Me />
        </div>
      </aside>
      <main className="min-w-0 px-7 pb-16 pl-3.5 pt-[22px] max-md:px-4 max-md:pb-12 max-md:pt-3.5">{children}</main>
    </div>
  )
}

'use client'

import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo } from 'react'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { usePendingDecisions } from '@/lib/api/hooks/usePendingDecisions'
import { useAIGovernance } from '@/lib/api/hooks/useAIGovernance'
import { STAGES } from '@/components/layout/AppShell'
import { cn } from '@/lib/utils'

const STAGE_LABEL = Object.fromEntries(STAGES.map((s) => [s.key, s.label])) as Record<AISystemSummary['stage'], string>
const TIER_ORDER: AISystemSummary['riskTier'][] = ['critical', 'high', 'medium', 'low']

function businessLine(s: AISystemSummary) {
  const m = s.metadata ?? {}
  const v = m.businessLine ?? m.business_line ?? m.businessUnit ?? m.business_unit ?? m.department
  return typeof v === 'string' && v.trim() ? v : 'Unassigned'
}

function median(values: number[]) {
  if (!values.length) return 0
  const v = [...values].sort((a, b) => a - b)
  const mid = Math.floor(v.length / 2)
  return v.length % 2 ? v[mid] : Math.round((v[mid - 1] + v[mid]) / 2)
}

function Gauge({ value }: { value: number }) {
  const r = 48
  const c = Math.PI * r
  return (
    <svg viewBox="0 0 120 68" className="mx-auto mt-3 block w-[150px]" aria-hidden>
      <path d="M12 60 A48 48 0 0 1 108 60" fill="none" stroke="rgba(21,23,26,.08)" strokeWidth="11" strokeLinecap="round" />
      <path
        d="M12 60 A48 48 0 0 1 108 60"
        fill="none"
        stroke="var(--fm-brand)"
        strokeWidth="11"
        strokeLinecap="round"
        strokeDasharray={`${(c * value) / 100} ${c}`}
      />
      <text x="60" y="60" textAnchor="middle" fontSize="24" fontWeight="600" fill="var(--fm-ink)">
        {value}%
      </text>
    </svg>
  )
}

function Overview() {
  const { selectedOrg } = useOrg()
  const { systems, loading, setSelectedSystemId } = useSystemContext()
  const router = useRouter()
  const openSystem = (id: string) => {
    setSelectedSystemId(id)
    router.push(`/systems/${id}`)
  }
  const { requests: allRequests } = usePendingDecisions()
  const { frameworks } = useAIGovernance()
  // P0 frameworks; fall back to all when the API sends no priorities.
  const core = frameworks.filter((f) => f.priority === 'P0')
  const coreFrameworks = core.length ? core : frameworks
  const stage = useSearchParams().get('stage')

  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  // Approval requests are not org-scoped yet; keep only those for systems in this estate.
  const requests = useMemo(() => allRequests.filter((r) => real.some((s) => s.id === r.entity_id)), [allRequests, real])
  const pendingSystemIds = useMemo(() => new Set(requests.map((r) => r.entity_id)), [requests])
  const shown = useMemo(
    () =>
      stage === 'decision'
        ? real.filter((s) => pendingSystemIds.has(s.id))
        : stage
          ? real.filter((s) => s.stage === stage)
          : real,
    [real, stage, pendingSystemIds],
  )
  const lines = useMemo(() => {
    const map = new Map<string, AISystemSummary[]>()
    shown.forEach((s) => map.set(businessLine(s), [...(map.get(businessLine(s)) ?? []), s]))
    return [...map.entries()].sort((a, b) => b[1].length - a[1].length)
  }, [shown])

  const byStage = (k: AISystemSummary['stage']) => real.filter((s) => s.stage === k).length
  const highTier = real.filter((s) => s.riskTier === 'high' || s.riskTier === 'critical')
  const readiness = median(real.map((s) => s.readiness))
  const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  if (!loading && real.length === 0) {
    return (
      <section className="fm-card grid min-h-[420px] place-items-center p-9 text-center">
        <div className="max-w-md">
          <h1 className="text-[28px] font-semibold tracking-tight">No AI systems under governance yet</h1>
          <p className="mt-3 text-[15px] text-[var(--fm-ink2)]">
            Register the first system to start the lifecycle. Evidence, decisions and framework coverage build from there.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link href="/integrations" className="inline-flex h-10 items-center rounded-full bg-[var(--fm-ink)] px-5 text-[13px] font-semibold text-white">
              Connect MLflow or GitHub
            </Link>
            <Link href="/onboard" className="inline-flex h-10 items-center rounded-full border border-[var(--fm-line)] bg-white px-5 text-[13px] font-medium text-[var(--fm-ink2)]">
              Register manually
            </Link>
          </div>
        </div>
      </section>
    )
  }

  return (
    <div className="grid gap-4">
      <section className="fm-card grid grid-cols-1 overflow-hidden rounded-[20px] lg:grid-cols-[420px_minmax(0,1fr)]" aria-label="Overview">
        <div className="border-b border-[var(--fm-line)] p-6 lg:border-b-0 lg:border-r lg:p-9 lg:pb-8">
          <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
            {selectedOrg?.name} · {today}
          </div>
          <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em] lg:text-[34px]">
            {loading ? 'Loading' : `${real.length} AI system${real.length === 1 ? '' : 's'} under governance`}
          </h1>
          <p className="mt-3 text-[15px] leading-[1.55] text-[var(--fm-ink2)]">
            <b className="font-semibold text-[var(--fm-ink)]">{requests.length}</b> await a decision.{' '}
            <b className="font-semibold text-[var(--fm-ink)]">{byStage('remediate')}</b> in remediation.{' '}
            <b className="font-semibold text-[var(--fm-ink)]">{highTier.length}</b> high or critical tier.
          </p>

          <div className="mt-5 grid h-[54px] grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2.5 rounded-full border border-white/90 bg-white/80 pl-3.5 pr-2 shadow-[var(--fm-shadow)]">
            <span className="grid h-[26px] w-[26px] place-items-center rounded-full bg-[var(--fm-brand)] text-white">
              <svg viewBox="0 0 16 16" className="h-[13px] w-[13px]" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round">
                <path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M6 10l-2 2" />
              </svg>
            </span>
            <input
              disabled
              placeholder="Ask about any system or finding"
              className="min-w-0 bg-transparent text-[14.5px] outline-none placeholder:text-[var(--fm-ink3)]"
            />
            <span className="rounded-full bg-[var(--fm-bg)] px-3 py-1.5 text-[11.5px] font-semibold text-[var(--fm-ink2)]">Coming soon</span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
              <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">Median readiness</div>
              <Gauge value={readiness} />
              <div className="mt-1 text-center text-[12px] text-[var(--fm-ink2)]">across {real.length} systems</div>
            </div>
            <div className="rounded-xl border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
              <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">By risk tier</div>
              <div className="mt-3 grid gap-2">
                {TIER_ORDER.map((t) => {
                  const n = real.filter((s) => s.riskTier === t).length
                  return (
                    <div key={t} className="grid grid-cols-[56px_minmax(0,1fr)_20px] items-center gap-2 text-[12px]">
                      <span className="capitalize text-[var(--fm-ink2)]">{t}</span>
                      <span className="h-2 overflow-hidden rounded-full bg-[rgba(21,23,26,.08)]">
                        <i
                          className={cn('block h-full rounded-full', t === 'critical' || t === 'high' ? 'bg-[var(--fm-brand)]' : 'bg-[#2b2e3a]')}
                          style={{ width: `${real.length ? (n / real.length) * 100 : 0}%` }}
                        />
                      </span>
                      <span className="text-right tabular-nums">{n}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="grid content-start gap-3.5 p-6 lg:px-8 lg:py-7">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-[15px] font-semibold">
              Estate by business line
              {stage && (
                <Link href="/dashboard" className="ml-2 rounded-full border border-[var(--fm-line)] px-2.5 py-0.5 text-[11.5px] font-medium text-[var(--fm-ink2)]">
                  {stage === 'decision' ? 'Awaiting decision' : STAGE_LABEL[stage as AISystemSummary['stage']]} · clear
                </Link>
              )}
            </h2>
            <div className="flex flex-wrap gap-4 text-[12px] text-[var(--fm-ink2)]">
              <span className="flex items-center gap-1.5"><i className="h-3 w-3 rounded-[3px] border border-[rgba(21,23,26,.2)] bg-white" />Operating</span>
              <span className="flex items-center gap-1.5"><i className="fm-hatch h-3 w-3 rounded-[3px] border border-[rgba(21,23,26,.2)]" />In remediation</span>
              <span className="flex items-center gap-1.5"><i className="h-3 w-3 rounded-[3px] bg-[var(--fm-brand)]" />Decision needed</span>
            </div>
          </div>
          {lines.length === 0 && <p className="text-[13px] text-[var(--fm-ink2)]">No systems in this stage.</p>}
          {lines.map(([line, items]) => (
            <div key={line} className="grid grid-cols-1 gap-3 border-t border-[var(--fm-line)] pt-3.5 md:grid-cols-[150px_minmax(0,1fr)] md:gap-4">
              <div>
                <div className="text-[14px] font-semibold">{line}</div>
                <div className="text-[12px] text-[var(--fm-ink2)]">
                  {items.length} system{items.length === 1 ? '' : 's'}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {items.map((s) => {
                  const open = pendingSystemIds.has(s.id)
                  return (
                    <button
                      type="button"
                      key={s.id}
                      onClick={() => openSystem(s.id)}
                      className={cn('text-left',
                        'relative w-[148px] rounded-[10px] border border-[rgba(21,23,26,.1)] bg-white px-2.5 pb-2 pt-[9px] shadow-[0_2px_0_rgba(21,23,26,.06),0_8px_16px_-12px_rgba(21,23,26,.25)] transition-transform hover:-translate-y-0.5 max-md:w-[calc(50%-4px)]',
                        s.stage === 'remediate' && 'fm-hatch',
                        open && 'border-[rgba(255,107,53,.5)] shadow-[0_2px_0_rgba(255,107,53,.35),0_8px_16px_-12px_rgba(21,23,26,.25)]',
                      )}
                    >
                      <div className="flex items-center gap-1.5 text-[13px] font-semibold leading-tight">
                        {open && <i className="h-1.5 w-1.5 flex-none rounded-full bg-[var(--fm-brand)]" />}
                        <span className="truncate">{s.name}</span>
                      </div>
                      <div className="mt-1 text-[11.5px] capitalize text-[var(--fm-ink2)]">
                        {s.riskTier} · {STAGE_LABEL[s.stage]}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 xl:grid-cols-4" aria-label="Key figures">
        {[
          { label: 'Onboarding', value: byStage('onboard'), href: '/dashboard?stage=onboard' },
          { label: 'In assessment', value: byStage('assess'), href: '/dashboard?stage=assess' },
          { label: 'In remediation', value: byStage('remediate'), href: '/dashboard?stage=remediate' },
          { label: 'Awaiting decision', value: requests.length, href: '/dashboard?stage=decision', hot: requests.length > 0 },
        ].map((k) => (
          <Link key={k.label} href={k.href} className="fm-card p-5">
            <div className="flex items-center justify-between text-[13px] font-medium text-[var(--fm-ink2)]">
              {k.label}
              {k.hot && <span className="rounded-full bg-[#ffeee4] px-2 py-0.5 text-[11.5px] font-semibold text-[#c2520f]">action</span>}
            </div>
            <div className="mt-2 text-[32px] font-semibold tabular-nums tracking-tight">{k.value}</div>
            <div className="mt-2 text-[12px] text-[var(--fm-ink2)]">of {real.length}</div>
          </Link>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div className="fm-card p-5">
          <h2 className="text-[15px] font-semibold">Systems</h2>
          <p className="text-[12.5px] text-[var(--fm-ink2)]">Every registered system, newest first.</p>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[520px] text-[13px]">
              <thead className="text-left text-[11.5px] uppercase tracking-wide text-[var(--fm-ink3)]">
                <tr>
                  <th className="pb-2 font-medium">System</th>
                  <th className="pb-2 font-medium">Owner</th>
                  <th className="pb-2 font-medium">Tier</th>
                  <th className="pb-2 font-medium">Stage</th>
                  <th className="pb-2 text-right font-medium">Readiness</th>
                </tr>
              </thead>
              <tbody>
                {real.map((s) => (
                  <tr key={s.id} className="border-t border-[var(--fm-line)]">
                    <td className="py-2.5 font-medium">
                      <button type="button" onClick={() => openSystem(s.id)} className="hover:underline">{s.name}</button>
                    </td>
                    <td className="py-2.5 text-[var(--fm-ink2)]">{s.owner}</td>
                    <td className="py-2.5 capitalize">{s.riskTier}</td>
                    <td className="py-2.5">{STAGE_LABEL[s.stage]}</td>
                    <td className="py-2.5 text-right tabular-nums">{s.readiness}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="fm-card p-5">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-[15px] font-semibold">Frameworks</h2>
            {frameworks.length > 0 && (
              <span className="text-[12px] tabular-nums text-[var(--fm-ink2)]">{coreFrameworks.length} core of {frameworks.length}</span>
            )}
          </div>
          <p className="text-[12.5px] text-[var(--fm-ink2)]">Core control sets. The rest are in the catalogue.</p>
          <div className="mt-3 grid gap-2.5">
            {coreFrameworks.map((f) => (
              <Link key={f.id} href="/compliance" className="flex items-center justify-between gap-3 border-t border-[var(--fm-line)] pt-2.5 text-[13px]">
                <span className="font-medium">{f.name}</span>
                <span className="tabular-nums text-[var(--fm-ink2)]">{f.controls?.length ?? 0} controls</span>
              </Link>
            ))}
            {frameworks.length === 0 && <p className="text-[13px] text-[var(--fm-ink2)]">No frameworks loaded.</p>}
            {frameworks.length > coreFrameworks.length && (
              <Link href="/compliance" className="justify-self-end border-t border-[var(--fm-line)] pt-2.5 text-[13px] font-medium text-[var(--fm-ink)]">
                See all {frameworks.length} frameworks
              </Link>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <Overview />
    </Suspense>
  )
}

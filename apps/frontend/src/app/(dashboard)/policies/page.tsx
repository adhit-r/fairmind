'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { BTN, BTN_P, Empty, ErrorNote, Heading, Loading, MUTED, Pill, when } from '@/components/packs/parts'
import { OutcomePill, PolicyStatusPill } from '@/components/policies/PolicyPills'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import {
  usePolicyActions,
  usePolicyResource,
  type AIDraftedPolicy,
  type Evaluation,
  type FrameworkCoverage,
  type Policy,
  type PolicyAlert,
} from '@/lib/api/hooks/usePolicies'

const INPUT = 'h-10 rounded-full border border-[#15171a24] bg-white px-4 text-[13px] outline-none focus:border-[var(--fm-ink,#15171a)]'

function NewPolicy({ onCreate }: { onCreate: (name: string) => Promise<void> }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  return (
    <form
      className="flex flex-wrap gap-2"
      onSubmit={async (e) => {
        e.preventDefault()
        if (!name.trim()) return
        setBusy(true)
        await onCreate(name.trim())
        setBusy(false)
      }}
    >
      <label className="sr-only" htmlFor="new-policy">Policy name</label>
      <input id="new-policy" className={`${INPUT} w-64`} placeholder="Name a new policy" value={name} onChange={(e) => setName(e.target.value)} />
      <button type="submit" className={BTN_P} disabled={busy || !name.trim()}>{busy ? 'Creating' : 'Draft policy'}</button>
    </form>
  )
}

function AIDraft({ onDraft }: { onDraft: (brief: string) => Promise<AIDraftedPolicy | null> }) {
  const [brief, setBrief] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<AIDraftedPolicy | null>(null)
  const ready = brief.trim().length >= 10
  return (
    <section aria-labelledby="ai-draft" className="pk-card flex flex-col gap-3 p-5">
      <div>
        <h2 id="ai-draft" className="m-0 text-lg font-semibold">Draft with AI</h2>
        <span className={`text-[13px] ${MUTED}`}>
          Describe the policy you need. Your organisation&apos;s model writes the policy text and the rules the platform can check, mapped to framework controls. It is saved as a draft for people to review and approve. The model is set in{' '}
          <Link href="/org-admin/settings" className="font-semibold underline">Organisation settings</Link>.
        </span>
      </div>
      <form
        className="flex flex-col gap-2.5"
        onSubmit={async (e) => {
          e.preventDefault()
          if (!ready) return
          setBusy(true)
          setResult(null)
          const drafted = await onDraft(brief.trim())
          setBusy(false)
          if (drafted) {
            setResult(drafted)
            setBrief('')
          }
        }}
      >
        <label className="sr-only" htmlFor="ai-brief">Policy brief</label>
        <textarea
          id="ai-brief"
          rows={3}
          maxLength={4000}
          className="w-full resize-y rounded-[10px] border border-[var(--fm-line)] bg-white px-3.5 py-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]"
          placeholder="For example: high-risk credit models need a named owner, no open critical risks and an approved release before they go live"
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
        />
        <div>
          <button type="submit" className={BTN_P} disabled={busy || !ready}>{busy ? 'Drafting' : 'Draft with AI'}</button>
        </div>
      </form>
      {result && (
        <div role="status" className="flex flex-col gap-1.5 rounded-[10px] bg-[var(--fm-bg)] px-3.5 py-3 text-[13px]">
          <span>
            Drafted <Link href={`/policies/${result.id}`} className="font-semibold underline">{result.name}</Link> with {result.draft.model}:{' '}
            {result.rules.length} {result.rules.length === 1 ? 'rule' : 'rules'} mapped to {result.controlRefs.length} {result.controlRefs.length === 1 ? 'control' : 'controls'}. Review it, then submit it for approval.
          </span>
          {result.draft.dropped.length > 0 && (
            <div className={MUTED}>
              Left out {result.draft.dropped.length} {result.draft.dropped.length === 1 ? 'rule' : 'rules'} the platform cannot check:
              <ul className="m-0 mt-1 list-disc pl-5">
                {result.draft.dropped.map((d) => <li key={d}>{d}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

function Alerts({ alerts, onAcknowledge }: { alerts: PolicyAlert[]; onAcknowledge: (id: string) => Promise<void> }) {
  if (!alerts.length) return null
  return (
    <section aria-labelledby="alerts" className="flex flex-col gap-3.5">
      <div>
        <h2 id="alerts" className="m-0 text-lg font-semibold">Open alerts</h2>
        <span className={`text-[13px] ${MUTED}`}>
          Published rules that started failing on a system. The policy owner is emailed once when an alert opens, and it closes by itself when the rule passes again.
        </span>
      </div>
      <ul className="m-0 flex list-none flex-col gap-2 p-0">
        {alerts.map((a) => (
          <li key={a.id} className="pk-card flex flex-wrap items-start gap-3 p-4">
            <OutcomePill outcome="fail" enforcement={a.enforcement} />
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-semibold">{a.systemName}: {a.ruleTitle}</div>
              <div className={`text-[12px] ${MUTED}`}>{a.detail}</div>
              <div className={`mt-1 text-[12px] ${MUTED}`}>
                Failing since {when(a.openedAt)} · <Link href={`/policies/${a.policyId}`} className="font-semibold hover:underline">{a.policyName}</Link>
                {a.notifiedAt ? ' · Owner emailed' : ''}
              </div>
            </div>
            {a.acknowledgedAt ? (
              <span className={`text-[12px] ${MUTED}`}>Acknowledged {when(a.acknowledgedAt)}</span>
            ) : (
              <button type="button" className={BTN} onClick={() => onAcknowledge(a.id)}>Acknowledge</button>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

function PolicyTable({ policies, evaluations }: { policies: Policy[]; evaluations: Evaluation[] }) {
  const failures = useMemo(() => {
    const out = new Map<string, number>()
    for (const e of evaluations) if (e.outcome === 'fail') out.set(e.policyId, (out.get(e.policyId) ?? 0) + 1)
    return out
  }, [evaluations])
  if (!policies.length) return <Empty>No policies yet. Draft your first AI policy above.</Empty>
  return (
    <div className="pk-card overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-left text-[13px]">
        <thead className={MUTED}>
          <tr className="border-b border-[#15171a14]">
            {['Policy', 'Status', 'Rules', 'Framework controls', 'Acknowledged', 'Enforcement'].map((h) => (
              <th key={h} scope="col" className="px-4 py-3 font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {policies.map((p) => {
            const failed = failures.get(p.id) ?? 0
            return (
              <tr key={p.id} className="border-b border-[#15171a0d] last:border-0 hover:bg-[#f9f9f7]">
                <td className="px-4 py-3">
                  <Link href={`/policies/${p.id}`} className="font-semibold hover:underline">{p.name}</Link>
                  <div className={`text-[12px] ${MUTED}`}>v{p.version}{p.publishedVersion && p.publishedVersion !== p.version ? `, v${p.publishedVersion} in force` : ''}</div>
                </td>
                <td className="px-4 py-3"><PolicyStatusPill status={p.status} /></td>
                <td className="px-4 py-3">{p.rules.length}</td>
                <td className="px-4 py-3">{p.controlRefs.length}</td>
                <td className="px-4 py-3">
                  {p.acknowledgement.required ? `${p.acknowledgement.acknowledged} of ${p.acknowledgement.required}` : <span className={MUTED}>Not distributed</span>}
                </td>
                <td className="px-4 py-3">
                  {!p.enforced ? <span className={MUTED}>Not enforced</span> : failed ? <Pill tone="block" dot>{failed} failing</Pill> : <Pill tone="done">Passing</Pill>}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function Enforcement({ evaluations, policies, onRun }: { evaluations: Evaluation[]; policies: Policy[]; onRun: () => Promise<void> }) {
  const [busy, setBusy] = useState(false)
  const names = new Map(policies.map((p) => [p.id, p]))
  const failing = evaluations.filter((e) => e.outcome === 'fail')
  return (
    <section aria-labelledby="enf" className="flex flex-col gap-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div>
          <h2 id="enf" className="m-0 text-lg font-semibold">Enforcement</h2>
          <span className={`text-[13px] ${MUTED}`}>
            Published rules checked against every AI system as its data stands now. A failing blocking rule stops the release approval. Running enforcement records these results for the audit trail.
          </span>
        </div>
        <button type="button" className={BTN} disabled={busy} onClick={async () => { setBusy(true); await onRun(); setBusy(false) }}>
          {busy ? 'Running' : 'Run enforcement now'}
        </button>
      </div>
      {!evaluations.length ? (
        <Empty>No results yet. Publish a policy with rules to start enforcing it.</Empty>
      ) : !failing.length ? (
        <Empty>Every applicable rule passes on every system ({evaluations.length} checks).</Empty>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {failing.map((e) => (
            <li key={`${e.policyId}-${e.systemId}-${e.ruleId}`} className="pk-card flex flex-wrap items-start gap-3 p-4">
              <OutcomePill outcome={e.outcome} enforcement={e.enforcement} />
              <div className="min-w-0 flex-1">
                <div className="text-[13px] font-semibold">
                  {e.systemName}: {names.get(e.policyId)?.rules.find((r) => r.id === e.ruleId)?.title ?? e.ruleId}
                </div>
                <div className={`text-[12px] ${MUTED}`}>{e.detail}</div>
              </div>
              <Link href={`/policies/${e.policyId}`} className={`text-[12px] font-semibold ${MUTED} hover:underline`}>
                {names.get(e.policyId)?.name ?? 'Policy'}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function ControlList({ title, controls }: { title: string; controls: FrameworkCoverage['controls'] }) {
  if (!controls.length) return null
  return (
    <details className="text-[13px]">
      <summary className="cursor-pointer font-semibold">{controls.length} {title}</summary>
      <ul className="m-0 mt-2 flex max-h-64 list-none flex-col gap-2 overflow-y-auto p-0">
        {controls.map((c) => (
          <li key={c.ref} className="flex flex-col gap-0.5">
            <span><code className="text-[12px]">{c.externalId}</code> <span className={MUTED}>{c.title}</span></span>
            {c.coveredBy.map((r) => (
              <span key={`${r.policyId}:${r.ruleId}`} className={`text-[12px] ${MUTED}`}>
                <Link href={`/policies/${r.policyId}`} className="underline">{r.policyName}</Link> / {r.ruleTitle}
                {r.failingSystems ? `: failing on ${r.failingSystems} system${r.failingSystems === 1 ? '' : 's'}` : ''}
              </span>
            ))}
          </li>
        ))}
      </ul>
    </details>
  )
}

function Coverage({ coverage }: { coverage: FrameworkCoverage[] }) {
  return (
    <section aria-labelledby="cov" className="flex flex-col gap-3.5">
      <div>
        <h2 id="cov" className="m-0 text-lg font-semibold">Framework coverage</h2>
        <span className={`text-[13px] ${MUTED}`}>
          Controls mapped to a published policy rule, and whether that rule holds on every system it applies to right now.
        </span>
      </div>
      {!coverage.length ? (
        <Empty>No framework is imported yet. Import one under Frameworks to map policies to its controls.</Empty>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4">
          {coverage.map((f) => {
            const pct = (n: number) => (f.totalControls ? (n / f.totalControls) * 100 : 0)
            const by = (status: string) => f.controls.filter((c) => c.status === status)
            return (
              <article key={f.frameworkKey} className="pk-card flex flex-col gap-3 p-5">
                <div className="flex items-baseline justify-between gap-2">
                  <b className="text-[15px] font-semibold">{f.name}</b>
                  <span className={`text-[12px] ${MUTED}`}>{f.versionLabel}</span>
                </div>
                <div className="text-[13px]"><b>{f.coveredControls}</b> of {f.totalControls} controls mapped to a published policy</div>
                <div
                  className="flex h-2 overflow-hidden rounded-full bg-[#f4f4f2]"
                  role="img"
                  aria-label={`${f.name}: ${f.passingControls} passing, ${f.failingControls} failing, ${f.uncheckedControls} not checked, ${f.totalControls - f.coveredControls} with no policy`}
                >
                  <div className="h-full bg-[#00704e]" style={{ width: `${pct(f.passingControls)}%` }} />
                  <div className="h-full bg-[#b42318]" style={{ width: `${pct(f.failingControls)}%` }} />
                  <div className="h-full bg-[#15171a40]" style={{ width: `${pct(f.uncheckedControls)}%` }} />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Pill tone="done">{f.passingControls} passing</Pill>
                  <Pill tone="block">{f.failingControls} failing</Pill>
                  <Pill>{f.uncheckedControls} not checked</Pill>
                  <Pill>{f.totalControls - f.coveredControls} no policy</Pill>
                </div>
                <ControlList title="failing controls" controls={by('failing')} />
                <ControlList title="controls not checked yet" controls={by('unchecked')} />
                <ControlList title="passing controls" controls={by('passing')} />
                <ControlList title="controls with no policy" controls={by('unmapped')} />
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default function PoliciesPage() {
  const orgId = useOrgId()
  const router = useRouter()
  const policies = usePolicyResource<Policy[]>(orgId, '')
  const evaluations = usePolicyResource<Evaluation[]>(orgId, '/evaluations')
  const coverage = usePolicyResource<FrameworkCoverage[]>(orgId, '/coverage')
  const alerts = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')
  const actions = usePolicyActions(orgId)
  const [failure, setFailure] = useState<string | null>(null)

  async function guarded(fn: () => Promise<void>) {
    setFailure(null)
    try {
      await fn()
    } catch (err) {
      setFailure(err instanceof Error ? err.message : 'Request failed')
    }
  }

  if (!orgId) return <Empty>Select an organisation to manage its policies.</Empty>
  if (policies.loading && !policies.data) return <Loading label="Loading policies" />
  if (policies.error && !policies.data) return <ErrorNote message={`Policies could not be loaded. ${policies.error}`} onRetry={policies.reload} />

  const list = policies.data ?? []
  const toAcknowledge = list.filter((p) => p.enforced && !p.acknowledgement.mine)

  return (
    <div className="flex flex-col gap-10">
      <Heading
        title="Policies"
        lead="Write your organisation's AI policies, distribute them for acknowledgement, map them to framework controls and enforce their rules on every AI system."
      >
        <NewPolicy
          onCreate={(name) => guarded(async () => {
            const created = await actions.create({ name })
            router.push(`/policies/${created.id}`)
          })}
        />
      </Heading>
      {failure && <ErrorNote message={failure} />}

      <AIDraft
        onDraft={async (brief) => {
          let drafted: AIDraftedPolicy | null = null
          await guarded(async () => {
            drafted = await actions.draftWithAI(brief)
            await policies.reload()
          })
          return drafted
        }}
      />

      {toAcknowledge.length > 0 && (
        <section aria-label="Awaiting your acknowledgement" className="flex flex-col gap-2 rounded-xl bg-[#ffeee4] px-4 py-3 text-[13px] text-[#a8430b]">
          <b>{toAcknowledge.length === 1 ? 'A published policy needs' : `${toAcknowledge.length} published policies need`} your acknowledgement</b>
          <div className="flex flex-wrap gap-2">
            {toAcknowledge.map((p) => (
              <Link key={p.id} href={`/policies/${p.id}`} className="font-semibold underline">{p.name}</Link>
            ))}
          </div>
        </section>
      )}

      <Alerts
        alerts={alerts.data ?? []}
        onAcknowledge={(id) => guarded(async () => {
          await actions.acknowledgeAlert(id)
          await alerts.reload()
        })}
      />

      <PolicyTable policies={list} evaluations={evaluations.data ?? []} />

      {evaluations.error && <ErrorNote message={`Enforcement results could not be loaded. ${evaluations.error}`} onRetry={evaluations.reload} />}
      <Enforcement
        evaluations={evaluations.data ?? []}
        policies={list}
        onRun={() => guarded(async () => {
          await actions.enforce()
          await Promise.all([evaluations.reload(), policies.reload(), alerts.reload()])
        })}
      />

      {coverage.error ? (
        <ErrorNote message={`Framework coverage could not be loaded. ${coverage.error}`} onRetry={coverage.reload} />
      ) : (
        <Coverage coverage={coverage.data ?? []} />
      )}
    </div>
  )
}

'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { BTN, BTN_P, Crumbs, Empty, ErrorNote, Heading, Loading, MUTED, Pill, when } from '@/components/packs/parts'
import { OutcomePill, PolicyStatusPill } from '@/components/policies/PolicyPills'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import {
  usePolicyActions,
  usePolicyResource,
  type Acknowledgement,
  type Evaluation,
  type FrameworkCoverage,
  type Policy,
  type PolicyAction,
  type PolicyVersion,
  type RuleLanguage,
} from '@/lib/api/hooks/usePolicies'

const FIELD = 'w-full rounded-xl border border-[#15171a24] bg-white px-3.5 py-2.5 text-[13px] outline-none focus:border-[var(--fm-ink,#15171a)]'
const LABEL = 'flex flex-col gap-1.5 text-[13px] font-semibold'

const ACTIONS: Record<Policy['status'], Array<{ action: PolicyAction; label: string; primary?: boolean }>> = {
  draft: [{ action: 'submit', label: 'Submit for review', primary: true }],
  in_review: [{ action: 'approve', label: 'Approve', primary: true }, { action: 'reject', label: 'Send back to draft' }],
  approved: [{ action: 'publish', label: 'Publish and distribute', primary: true }],
  published: [{ action: 'revise', label: 'Start a revision' }, { action: 'retire', label: 'Retire' }],
  retired: [],
}

const RULE_EXAMPLE = `[
  {
    "id": "high-risk-approval",
    "title": "High-risk systems need a release approval",
    "severity": "high",
    "enforcement": "block",
    "when": { "fact": "system.risk_tier", "op": "in", "value": ["high", "unacceptable"] },
    "check": { "fact": "approval.status", "op": "eq", "value": "approved" },
    "controls": []
  }
]`

function Section({ title, lead, children }: { title: string; lead?: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3.5">
      <div>
        <h2 className="m-0 text-lg font-semibold">{title}</h2>
        {lead && <span className={`text-[13px] ${MUTED}`}>{lead}</span>}
      </div>
      {children}
    </section>
  )
}

function Reference({ language, coverage }: { language: RuleLanguage | null; coverage: FrameworkCoverage[] }) {
  const [q, setQ] = useState('')
  const controls = coverage.flatMap((f) => f.controls.map((c) => ({ ...c, framework: f.name })))
  const needle = q.trim().toLowerCase()
  const shown = needle ? controls.filter((c) => `${c.ref} ${c.title}`.toLowerCase().includes(needle)) : controls
  return (
    <div className="flex flex-col gap-2 text-[13px]">
      <details>
        <summary className="cursor-pointer font-semibold">Facts and operators</summary>
        <p className={`m-0 mt-2 ${MUTED}`}>
          Operators: {language?.ops.join(', ')}. Combine conditions with {'{"all": [...]}'}, {'{"any": [...]}'} and {'{"not": {...}}'}. Any value in a system&apos;s metadata is
          readable as <code>system.metadata.&lt;key&gt;</code>.
        </p>
        <ul className="m-0 mt-2 grid list-none gap-1 p-0 sm:grid-cols-2">
          {language?.facts.map((f) => (
            <li key={f.name}><code className="text-[12px]">{f.name}</code> <span className={MUTED}>{f.description}</span></li>
          ))}
        </ul>
      </details>
      <details>
        <summary className="cursor-pointer font-semibold">Framework controls to map ({controls.length})</summary>
        {!controls.length ? (
          <p className={`m-0 mt-2 ${MUTED}`}>No framework is imported yet.</p>
        ) : (
          <>
            <input className={`${FIELD} mt-2`} placeholder="Search controls" aria-label="Search framework controls" value={q} onChange={(e) => setQ(e.target.value)} />
            <ul className="m-0 mt-2 flex max-h-72 list-none flex-col gap-1 overflow-y-auto p-0">
              {shown.map((c) => (
                <li key={c.ref}><code className="text-[12px]">{c.ref}</code> <span className={MUTED}>{c.title}</span></li>
              ))}
            </ul>
          </>
        )}
      </details>
    </div>
  )
}

export default function PolicyPage() {
  const { id } = useParams<{ id: string }>()
  const orgId = useOrgId()
  const router = useRouter()
  const policy = usePolicyResource<Policy>(orgId, `/${id}`)
  const results = usePolicyResource<Evaluation[]>(orgId, `/${id}/evaluations`)
  const acks = usePolicyResource<Acknowledgement[]>(orgId, `/${id}/acknowledgements`)
  const versions = usePolicyResource<PolicyVersion[]>(orgId, `/${id}/versions`)
  const coverage = usePolicyResource<FrameworkCoverage[]>(orgId, '/coverage')
  const language = usePolicyResource<RuleLanguage>(orgId, '/language')
  const actions = usePolicyActions(orgId)
  const [draft, setDraft] = useState({ name: '', owner: '', summary: '', body: '', rules: '' })
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const p = policy.data
  useEffect(() => {
    if (p) setDraft({ name: p.name, owner: p.owner ?? '', summary: p.summary, body: p.body, rules: p.rules.length ? JSON.stringify(p.rules, null, 2) : '' })
  }, [p])

  const controlTitle = useMemo(
    () => new Map(coverage.data?.flatMap((f) => f.controls.map((c) => [c.ref, c.title] as const)) ?? []),
    [coverage.data],
  )

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label)
    setFailure(null)
    setSaved(false)
    try {
      await fn()
      await Promise.all([policy.reload(), results.reload(), acks.reload(), versions.reload()])
      return true
    } catch (err) {
      setFailure(err instanceof Error ? err.message : 'Request failed')
      return false
    } finally {
      setBusy(null)
    }
  }

  async function save() {
    let rules: unknown = []
    try {
      rules = draft.rules.trim() ? JSON.parse(draft.rules) : []
    } catch (err) {
      setFailure(`Rules are not valid JSON: ${err instanceof Error ? err.message : ''}`)
      return
    }
    const ok = await run('save', () =>
      actions.update(id, { name: draft.name, owner: draft.owner || null, summary: draft.summary, body: draft.body, rules: rules as Policy['rules'] }),
    )
    setSaved(ok)
  }

  if (!orgId) return <Empty>Select an organisation to manage its policies.</Empty>
  if (policy.loading && !p) return <Loading label="Loading policy" />
  if (!p) return <ErrorNote message={`Policy could not be loaded. ${policy.error ?? ''}`} onRetry={policy.reload} />

  const editable = p.status === 'draft'
  const byRule = new Map<string, Evaluation[]>()
  for (const r of results.data ?? []) byRule.set(r.ruleId, [...(byRule.get(r.ruleId) ?? []), r])

  return (
    <div className="flex flex-col gap-10">
      <div className="flex flex-col gap-3">
        <Crumbs items={[{ label: 'Policies', href: '/policies' }, { label: p.name }]} />
        <Heading
          title={p.name}
          lead={
            <span className="flex flex-wrap items-center gap-2">
              <PolicyStatusPill status={p.status} />
              <span>Version {p.version}</span>
              {p.publishedVersion && <Pill tone={p.enforced ? 'done' : 'plain'}>v{p.publishedVersion} {p.enforced ? 'in force' : 'retired'}</Pill>}
              {p.approvedBy && p.approvedAt && <span>Approved {when(p.approvedAt)}</span>}
            </span>
          }
        >
          {ACTIONS[p.status].map((a) => (
            <button key={a.action} type="button" className={a.primary ? BTN_P : BTN} disabled={busy !== null} onClick={() => run(a.action, () => actions.act(id, a.action))}>
              {busy === a.action ? 'Working' : a.label}
            </button>
          ))}
          {editable && p.publishedVersion && (
            <button type="button" className={BTN} disabled={busy !== null} onClick={() => run('retire', () => actions.act(id, 'retire'))}>Retire</button>
          )}
          {editable && !p.publishedVersion && (
            <button
              type="button"
              className={BTN}
              disabled={busy !== null}
              onClick={async () => {
                if (!window.confirm(`Delete the draft "${p.name}"? This cannot be undone.`)) return
                setBusy('delete')
                try {
                  await actions.remove(id)
                  router.push('/policies')
                } catch (err) {
                  setFailure(err instanceof Error ? err.message : 'Delete failed')
                  setBusy(null)
                }
              }}
            >
              Delete draft
            </button>
          )}
        </Heading>
      </div>

      {failure && <ErrorNote message={failure} />}
      {p.enforced && !p.acknowledgement.mine && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[#ffeee4] px-4 py-3 text-[13px] text-[#a8430b]">
          <b>Read version {p.publishedVersion} of this policy and confirm you will follow it.</b>
          <button type="button" className={BTN_P} disabled={busy !== null} onClick={() => run('ack', () => actions.acknowledge(id))}>
            {busy === 'ack' ? 'Recording' : 'I have read and will follow this policy'}
          </button>
        </div>
      )}

      <Section title="Policy document" lead={editable ? 'Edit while in draft. Submit for review when it is ready.' : 'Start a revision to change a published policy.'}>
        {editable ? (
          <div className="pk-card flex flex-col gap-4 p-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className={LABEL}>Name<input className={FIELD} value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></label>
              <label className={LABEL}>Owner<input className={FIELD} value={draft.owner} onChange={(e) => setDraft({ ...draft, owner: e.target.value })} /></label>
            </div>
            <label className={LABEL}>Summary<input className={FIELD} value={draft.summary} onChange={(e) => setDraft({ ...draft, summary: e.target.value })} /></label>
            <label className={LABEL}>
              Policy text
              <textarea className={`${FIELD} min-h-[280px] font-normal leading-relaxed`} value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />
            </label>
          </div>
        ) : (
          <article className="pk-card flex flex-col gap-2 p-5 text-[14px] leading-relaxed">
            {p.summary && <p className="m-0 font-semibold">{p.summary}</p>}
            {p.owner && <p className={`m-0 text-[13px] ${MUTED}`}>Owner: {p.owner}</p>}
            {p.body ? <div className="whitespace-pre-wrap">{p.body}</div> : <span className={MUTED}>No policy text.</span>}
          </article>
        )}
      </Section>

      <Section title="Rules as code" lead="Each rule is checked against every AI system. Blocking rules fail the release gate; warnings are reported only.">
        {editable && (
          <div className="pk-card flex flex-col gap-3 p-5">
            <label className={LABEL}>
              Rules (JSON)
              <textarea
                className={`${FIELD} min-h-[260px] font-mono text-[12px] font-normal`}
                spellCheck={false}
                placeholder={RULE_EXAMPLE}
                value={draft.rules}
                onChange={(e) => setDraft({ ...draft, rules: e.target.value })}
              />
            </label>
            <Reference language={language.data} coverage={coverage.data ?? []} />
            <div className="flex items-center gap-3">
              <button type="button" className={`${BTN_P} self-start`} disabled={busy !== null} onClick={save}>{busy === 'save' ? 'Saving' : 'Save draft'}</button>
              {saved && <span className={`text-[13px] ${MUTED}`} role="status">Saved</span>}
            </div>
          </div>
        )}
        {!p.rules.length ? (
          <Empty>No rules yet. A policy without rules is distributed but not enforced.</Empty>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {p.rules.map((r) => (
              <li key={r.id} className="pk-card flex flex-col gap-3 p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <b className="text-[14px]">{r.title}</b>
                  <Pill tone={r.severity === 'critical' || r.severity === 'high' ? 'block' : 'plain'}>{r.severity}</Pill>
                  <Pill tone={r.enforcement === 'block' ? 'run' : 'plain'}>{r.enforcement === 'block' ? 'Blocks release' : 'Warns'}</Pill>
                  <code className={`text-[12px] ${MUTED}`}>{r.id}</code>
                </div>
                <div className="flex flex-col gap-1 text-[13px]">
                  <span className="font-semibold">Mapped framework controls</span>
                  {r.controls.length ? (
                    <ul className="m-0 flex list-none flex-col gap-0.5 p-0">
                      {r.controls.map((c) => <li key={c}><code className="text-[12px]">{c}</code> <span className={MUTED}>{controlTitle.get(c) ?? ''}</span></li>)}
                    </ul>
                  ) : (
                    <span className={MUTED}>Not mapped to any framework control.</span>
                  )}
                </div>
                {p.publishedVersion && (
                  <div className="flex flex-col gap-1 text-[13px]">
                    <span className="font-semibold">Latest results</span>
                    {(byRule.get(r.id) ?? []).length ? (
                      <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
                        {byRule.get(r.id)!.map((e) => (
                          <li key={e.systemId} className="flex flex-wrap items-center gap-2">
                            <OutcomePill outcome={e.outcome} enforcement={e.enforcement} />
                            <b>{e.systemName}</b>
                            {e.outcome === 'fail' && <span className={MUTED}>{e.detail}</span>}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className={MUTED}>
                        {p.publishedVersion === p.version ? 'No results for this rule yet.' : 'Rules changed in this revision take effect when it is published.'}
                      </span>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        {p.enforced && (
          <button type="button" className={`${BTN} self-start`} disabled={busy !== null} onClick={() => run('enforce', () => actions.enforce(id))}>
            {busy === 'enforce' ? 'Running' : 'Re-run enforcement'}
          </button>
        )}
      </Section>

      <Section
        title="Distribution"
        lead={p.publishedVersion ? `${p.acknowledgement.acknowledged} of ${p.acknowledgement.required} members acknowledged version ${p.publishedVersion}.` : 'Publishing distributes the policy to every member of the organisation.'}
      >
        {p.publishedVersion && (acks.data?.length ? (
          <div className="pk-card overflow-x-auto">
            <table className="w-full min-w-[480px] border-collapse text-left text-[13px]">
              <thead className={MUTED}>
                <tr className="border-b border-[#15171a14]">
                  {['Member', 'Role', 'Acknowledged'].map((h) => <th key={h} scope="col" className="px-4 py-3 font-semibold">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {acks.data.map((m) => (
                  <tr key={m.userId} className="border-b border-[#15171a0d] last:border-0">
                    <td className="px-4 py-3">{m.name || m.email}{m.name && <div className={`text-[12px] ${MUTED}`}>{m.email}</div>}</td>
                    <td className="px-4 py-3 capitalize">{m.role}</td>
                    <td className="px-4 py-3">{m.acknowledgedAt ? when(m.acknowledgedAt) : <Pill tone="you">Pending</Pill>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : acks.error ? <ErrorNote message={`Members could not be loaded. ${acks.error}`} onRetry={acks.reload} /> : null)}
      </Section>

      <Section title="Published versions" lead="Each published version is kept unchanged for audit.">
        {!versions.data?.length ? (
          <Empty>Not published yet.</Empty>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {versions.data.map((v) => (
              <li key={v.version} className="pk-card flex flex-wrap items-center gap-3 p-4 text-[13px]">
                <b>Version {v.version}</b>
                <span className={MUTED}>Published {when(v.publishedAt)}, {v.rules.length} {v.rules.length === 1 ? 'rule' : 'rules'}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}

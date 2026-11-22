'use client'

import '@/astryx/pages/frameworks.css'
import '@/astryx/pages/tasks.css'
import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useJourney } from '@/lib/api/hooks/usePacks'
import { GROUP_LABEL, Glyph, Legend, NEEDS_WORK, READINESS_LABEL, READINESS_OF, READINESS_ORDER, STATE_LABEL, WEAKEST_FIRST, cellIndex, groupOf, readinessCounts, requirementHref, stateFor, type ReqState } from '../parts'
import { MatrixView } from './MatrixView'
import { ScopeCard } from './ScopeCard'
import { useFrameworkScope } from '@/lib/api/hooks/useFrameworkScope'
import { PrepareAudit } from './PrepareAudit'
import { TaskForm, initials, personName, useAssignees } from '@/components/tasks/TaskForm'
import { useTasks } from '@/lib/api/hooks/useTasks'

/** Why a requirement is on the work queue, from the checks behind its cell. */
function reason(state: ReqState, all: Array<{ label: string; cell?: string; stale?: true; fails?: true }>): string {
  const checks = all.filter((c) => c.cell !== 'not in gate')
  if (state === 'fails') return `Failing check: ${checks.find((c) => c.fails)?.label ?? checks[0]?.label ?? 'a release check'}`
  if (state === 'stale') return `Stale evidence: ${checks.find((c) => c.stale)?.label ?? checks[0]?.label ?? 'a release check'}`
  return checks[0] ? `No current evidence for ${checks[0].label}` : 'No current evidence'
}

function ClauseView() {
  const params = useParams<{ key: string }>()
  const key = decodeURIComponent(params.key)
  const router = useRouter()
  const search = useSearchParams()
  const tabParam = search.get('tab')
  const tab = tabParam === 'systems' || tabParam === 'all' || tabParam === 'audit' ? tabParam : 'requirements'
  const setTab = (t: string) => router.replace(`/frameworks/${encodeURIComponent(key)}${t === 'requirements' ? '' : `?tab=${t}`}`)
  useOrg()
  const journey = useJourney(key)
  const fw = useFrameworkSystems(key)
  const scope = useFrameworkScope(key)
  const tasks = useTasks({ subject_type: 'requirement', status: 'open' })
  const [assigning, setAssigning] = useState<string | null>(null)
  const assignees = useAssignees()
  const whoHas = (t: { assigneeAgent: string | null; assigneeUserId: string | null }) =>
    t.assigneeAgent
      ? assignees.agents.find((a) => a.key === t.assigneeAgent)?.name ?? 'An agent'
      : t.assigneeUserId
        ? (() => { const m = assignees.members.find((x) => x.user_id === t.assigneeUserId); return m ? personName(m) : 'A member' })()
        : 'Nobody yet'
  // An open task on a requirement for a system: the queue shows who has it instead of an Assign button.
  const taskFor = useMemo(() => new Map((tasks.data?.tasks ?? []).map((t) => [`${t.subject.id}@${t.systemId}`, t])), [tasks.data])
  const [system, setSystem] = useState<number | 'all'>('all')
  const [groupPick, setGroupPick] = useState<string | null>(null)

  const j = journey.data
  const f = fw.data
  const systems = useMemo(() => f?.systems ?? [], [f])
  const cells = useMemo(() => cellIndex(f ?? null), [f])
  const name = j?.name ?? f?.framework.name ?? key
  const short = shortFrameworkName(name)

  const groups = useMemo(
    () =>
      (j?.groups ?? []).map((g) => {
        const reqs = g.requirements.map((r) => ({ ...r, state: stateFor(cells.get(r.key), r.status, system) }))
        return {
          name: g.name,
          reqs,
          proven: reqs.filter((r) => r.state === 'proven').length,
          work: reqs.filter((r) => NEEDS_WORK.includes(r.state)).length,
        }
      }),
    [j, cells, system],
  )
  const group = groups.find((g) => g.name === groupPick) ?? groups.find((g) => g.work > 0) ?? groups[0]

  const queue = useMemo(
    () =>
      systems
        .map((s, i) => ({
          system: s,
          items: groups
            .flatMap((g) => g.reqs)
            .map((r) => {
              const c = cells.get(r.key)?.[i]
              return c && NEEDS_WORK.includes(c.state) ? { r, state: c.state as ReqState, why: reason(c.state, c.checks) } : null
            })
            .filter((x): x is NonNullable<typeof x> => !!x)
            .sort((a, b) => WEAKEST_FIRST.indexOf(a.state) - WEAKEST_FIRST.indexOf(b.state)),
        }))
        .filter((q) => q.items.length > 0),
    [systems, groups, cells],
  )
  const queued = queue.reduce((a, q) => a + q.items.length, 0)

  const allReqs = groups.flatMap((g) => g.reqs)
  const readiness = readinessCounts(allReqs.reduce<Partial<Record<ReqState, number>>>((m, r) => ({ ...m, [r.state]: (m[r.state] ?? 0) + 1 }), {}))
  const attention = allReqs.filter((r) => READINESS_OF[r.state] === 'attention')

  if ((journey.loading && !j) || (fw.loading && !f)) {
    return (
      <VStack gap={3} aria-busy="true">
        <Skeleton height={40} />
        <Skeleton height={360} />
      </VStack>
    )
  }
  if (journey.error || fw.error || !j) {
    return (
      <EmptyState
        title={`${short} could not load`}
        description={journey.error || fw.error || 'No data came back.'}
        actions={<Button label="Try again" onClick={() => { journey.reload(); fw.reload() }} />}
      />
    )
  }

  return (
    <VStack gap={5}>
      <VStack gap={3}>
        <Text type="supporting">
          <Link href="/frameworks">Frameworks</Link> / {short}
        </Text>
        <HStack gap={3} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <span className="fx-eyebrow">{[GROUP_LABEL[groupOf(j)], j.version].filter(Boolean).join(' · ')}</span>
            <Heading level={1}>{name}</Heading>
            <Text color="secondary">
              {f?.followedByPlan ? 'Chosen in your plan' : systems.length ? 'Confirmed on systems, not in your plan' : 'You do not follow this framework'}
              {' · '}
              {systems.length} system{systems.length === 1 ? '' : 's'} in scope
              {(f?.inherited ?? 0) > 0 ? `, ${f?.inherited} not assessed yet` : ''}
            </Text>
          </VStack>
          <HStack gap={2}>
            <Button variant="secondary" label="Matrix" href={`/frameworks/${encodeURIComponent(key)}?view=matrix`} />
            <Button variant="primary" label="Prepare audit pack" onClick={() => setTab('audit')} />
          </HStack>
        </HStack>
      </VStack>

      {!systems.length && (
        <Banner
          status="info"
          title={`You do not follow ${short}`}
          description="Follow it from Frameworks and every AI system you have not assessed is in scope. Until then, the map shows only what installed packs cover at organisation level."
        />
      )}

      <ScopeCard frameworkKey={key} view={scope.data} onChange={scope.reload} />

      <section className="fm-card" aria-label="Readiness">
        <div className="fx-summary">
          {READINESS_ORDER.map((r) => (
            <div key={r} className={`fx-sbox r-${r}`}>
              <b>{readiness[r]}</b>
              <span>{r === 'met' ? 'Met, by evidence or attestation' : r === 'attention' ? 'Need attention: failing or out of date' : READINESS_LABEL[r]}</span>
            </div>
          ))}
        </div>
      </section>

      <TabList value={tab} onChange={setTab} hasDivider aria-label={`${short} views`}>
        <Tab value="requirements" label="Requirements" />
        <Tab value="systems" label={`Systems ${systems.length}`} />
        <Tab value="all" label={`All requirements ${allReqs.length}`} />
        <Tab value="audit" label="Audit and packs" />
      </TabList>

      {tab === 'audit' ? (
        <PrepareAudit
          frameworkKey={key}
          name={short}
          systems={systems.map((s) => ({ id: s.id, name: s.name }))}
          counts={readiness}
          attention={attention.map((r) => ({ control: r.control, title: r.title }))}
          notAssessed={f?.inherited ?? 0}
        />
      ) : tab === 'systems' ? (
        <section className="fm-card" aria-label="Systems in scope" style={{ padding: 0 }}>
          <div className="fx-scroll">
            <table className="fx-table">
              <thead>
                <tr><th scope="col">System</th><th scope="col">Tier</th><th scope="col">Where it stands</th></tr>
              </thead>
              <tbody>
                {systems.map((sys, i) => {
                  const st: Partial<Record<ReqState, number>> = {}
                  for (const r of allReqs) {
                    const s2 = stateFor(cells.get(r.key), r.status, i)
                    st[s2] = (st[s2] ?? 0) + 1
                  }
                  const c = readinessCounts(st)
                  return (
                    <tr key={sys.id}>
                      <td><Link href={`/systems/${encodeURIComponent(sys.id)}`}>{sys.name}</Link></td>
                      <td>{sys.riskTier}</td>
                      <td style={{ minWidth: 320 }}><span className="fx-counts" style={{ marginTop: 0 }}><span><b>{c.met} of {allReqs.length}</b> met</span><span>{c.progress} in progress</span>{c.attention > 0 && <span className="warn">{c.attention} need attention</span>}<span>{c.notstarted} not started</span></span></td>
                    </tr>
                  )
                })}
                {systems.length === 0 && <tr><td colSpan={3}>No system is in scope.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      ) : tab === 'all' ? (
        <section className="fm-card" aria-label="All requirements" style={{ padding: 0 }}>
          <div className="fx-scroll">
            <table className="fx-table">
              <thead>
                <tr><th scope="col">ID</th><th scope="col">Requirement</th><th scope="col">Group</th><th scope="col">Status</th></tr>
              </thead>
              <tbody>
                {groups.flatMap((g) => g.reqs.map((r) => {
                  const ready = READINESS_OF[r.state]
                  return (
                    <tr key={r.key}>
                      <td className="num"><Link href={requirementHref(key, r.control)}>{r.control}</Link></td>
                      <td><Link href={requirementHref(key, r.control)}>{r.title}</Link></td>
                      <td>{g.name}</td>
                      <td><span className="fx-state"><i className={`fx-rk r-${ready}`} aria-hidden="true" />{READINESS_LABEL[ready]}</span></td>
                    </tr>
                  )
                }))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
            <div className="fx-cols">
        <VStack gap={5}>
          <section className="fm-card fx-map" aria-labelledby="fx-map-title" style={{ padding: 0 }}>
            <div className="fx-pad">
              <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
                <VStack gap={0}>
                  <Heading level={2} id="fx-map-title">Requirement map</Heading>
                  <Text type="supporting">Every requirement in the standard&rsquo;s order. Pick one to open its trace.</Text>
                </VStack>
                {systems.length > 0 && (
                  <SegmentedControl label="Show state for" value={String(system)} onChange={(v) => setSystem(v === 'all' ? 'all' : Number(v))}>
                    <SegmentedControlItem value="all" label="All systems" />
                    {systems.map((s, i) => (
                      <SegmentedControlItem key={s.id} value={String(i)} label={s.name} />
                    ))}
                  </SegmentedControl>
                )}
              </HStack>
            </div>
            <div className="fx-pad" style={{ paddingTop: 0 }}>
              <Legend
                states={['proven', 'attested', 'estimated', 'open', 'fails', 'stale', 'atorg', 'none']}
                extra={system === 'all' && systems.length > 1 ? <span className="end">All systems shows the weakest state</span> : null}
              />
            </div>
            {groups.map((g) => (
              <div key={g.name} className={`fx-grp${g.name === group?.name ? ' on' : ''}`}>
                <button type="button" className="nm" onClick={() => setGroupPick(g.name)} aria-pressed={g.name === group?.name}>
                  {g.name}
                </button>
                <span className="fx-sq">
                  {g.reqs.map((r) => {
                    const label = `${r.control} ${r.title}: ${STATE_LABEL[r.state]}`
                    return (
                      <Link key={r.key} href={requirementHref(key, r.control, system === 'all' ? undefined : systems[system]?.id)} title={label} aria-label={label}>
                        <Glyph state={r.state} size="lg" />
                      </Link>
                    )
                  })}
                </span>
                <span className="sum">
                  {g.proven} of {g.reqs.length} proven{g.work ? ` · ${g.work} to do` : ''}
                </span>
              </div>
            ))}
          </section>

          {group && (
            <section className="fm-card" aria-labelledby="fx-grp-title" style={{ padding: 0 }}>
              <div className="fx-pad">
                <Heading level={2} id="fx-grp-title">{group.name}</Heading>
                <Text type="supporting">
                  {group.reqs.length} requirement{group.reqs.length === 1 ? '' : 's'} · each opens its trace
                </Text>
              </div>
              <div className="fx-scroll">
                <table className="fx-table">
                  <thead>
                    <tr>
                      <th scope="col">ID</th>
                      <th scope="col">Requirement</th>
                      {systems.length ? systems.map((s) => <th key={s.id} scope="col">{s.name}</th>) : <th scope="col">Organisation</th>}
                      <th scope="col">Evidence</th>
                      <th scope="col">Freshness</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.reqs.map((r) => {
                      const row = cells.get(r.key) ?? []
                      const checks = row.flatMap((c) => c?.checks ?? [])
                      const evidence = new Set(checks.map((c) => c.evidenceId).filter(Boolean)).size
                      const stale = checks.filter((c) => c.stale).length
                      return (
                        <tr key={r.key}>
                          <td className="num">
                            <Link href={requirementHref(key, r.control)}>{r.control}</Link>
                          </td>
                          <td>
                            <Link href={requirementHref(key, r.control)}>{r.title}</Link>
                          </td>
                          {systems.length ? (
                            systems.map((s, i) => {
                              const st = stateFor(row, r.status, i)
                              return (
                                <td key={s.id}>
                                  <span className="fx-state">
                                    <Glyph state={st} />
                                    {STATE_LABEL[st]}
                                  </span>
                                </td>
                              )
                            })
                          ) : (
                            <td>
                              <span className="fx-state">
                                <Glyph state={r.state} />
                                {STATE_LABEL[r.state]}
                              </span>
                            </td>
                          )}
                          <td className="num">{evidence || 'None'}</td>
                          <td>{stale ? <b style={{ color: '#8a5a00' }}>{stale} stale</b> : checks.length ? 'Current' : 'Not tracked'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </VStack>

        <aside className="fm-card fx-q" aria-labelledby="fx-q-title" style={{ padding: 0 }}>
          <div className="fx-pad" style={{ paddingBottom: 4 }}>
            <Heading level={2} id="fx-q-title">Needs work</Heading>
            <Text type="supporting">
              {queued ? `${queued} open, failing or stale on confirmed systems` : systems.length ? 'Nothing open on the confirmed systems' : 'Confirm the framework on a system to see its work'}
            </Text>
          </div>
          {queue.map((q) => (
            <div key={q.system.id}>
              <h3>{q.system.name}</h3>
              {q.items.slice(0, 8).map(({ r, state, why }) => (
                <div key={r.key} className="fx-qrow">
                  <Glyph state={state} label={STATE_LABEL[state]} />
                  <span>
                    <b>{r.control}</b>
                    {r.title}
                    <small>{why}</small>
                  </span>
                  {(() => {
                    const task = taskFor.get(`${r.key}@${q.system.id}`)
                    if (task) {
                      const who = whoHas(task)
                      return (
                        <Link className="fx-chip" href={`/tasks?view=team&task=${encodeURIComponent(task.id)}`} aria-label={`Task for ${who}; open it`}>
                          <span className={`tk-av${task.assigneeAgent ? ' agent' : task.assigneeUserId ? '' : ' none'}`} aria-hidden="true" style={{ width: 22, height: 22, fontSize: 9 }}>
                            {task.assigneeAgent ? 'AI' : task.assigneeUserId ? initials(who) : '?'}
                          </span>
                          {task.dueDate ? `Due ${new Date(`${task.dueDate}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}` : 'Task'}
                        </Link>
                      )
                    }
                    return <Button variant="secondary" size="sm" label="Assign" onClick={() => setAssigning(assigning === `${r.key}@${q.system.id}` ? null : `${r.key}@${q.system.id}`)} />
                  })()}
                  {assigning === `${r.key}@${q.system.id}` && (
                    <div style={{ gridColumn: '1 / -1', paddingTop: 8 }}>
                      <TaskForm
                        about={{ subject_type: 'requirement', subject_id: r.key, subject_label: `${short} ${r.control} ${r.title} · ${q.system.name}`, system_id: q.system.id }}
                        defaultTitle={`${r.control} ${r.title}: ${why}`}
                        onDone={() => { setAssigning(null); tasks.reload() }}
                        onCancel={() => setAssigning(null)}
                      />
                    </div>
                  )}
                </div>
              ))}
              {q.items.length > 8 && (
                <div className="fx-qrow" style={{ gridTemplateColumns: '1fr' }}>
                  <Text type="supporting">{q.items.length - 8} more on {q.system.name}: filter the map to this system</Text>
                </div>
              )}
            </div>
          ))}
          {queued > 0 && (
            <div className="fx-pad" style={{ borderTop: '1px solid var(--color-border)' }}>
              <Link href="/needs-you">
                Open Needs you
              </Link>
            </div>
          )}
        </aside>
      </div>
      )}
    </VStack>
  )
}

function FrameworkPage() {
  const view = useSearchParams().get('view')
  return <div className="fm-page">{view === 'matrix' || view === 'controls' ? <MatrixView /> : <ClauseView />}</div>
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <FrameworkPage />
    </Suspense>
  )
}

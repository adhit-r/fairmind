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
import { Heading, Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useEvidencePacks } from '@/lib/api/hooks/useEvidencePacks'
import { useJourney } from '@/lib/api/hooks/usePacks'
import { Glyph, Legend, NEEDS_WORK, STATE_LABEL, WEAKEST_FIRST, cellIndex, requirementHref, stateFor, type ReqState } from '../parts'
import { MatrixView } from './MatrixView'
import { TaskForm, initials, personName, useAssignees } from '@/components/tasks/TaskForm'
import { useTasks } from '@/lib/api/hooks/useTasks'

/** Why a requirement is on the work queue, from the checks behind its cell. */
function reason(state: ReqState, checks: Array<{ label: string; stale?: true; fails?: true }>): string {
  if (state === 'fails') return `Failing check: ${checks.find((c) => c.fails)?.label ?? checks[0]?.label ?? 'a release check'}`
  if (state === 'stale') return `Stale evidence: ${checks.find((c) => c.stale)?.label ?? checks[0]?.label ?? 'a release check'}`
  return checks[0] ? `No current evidence for ${checks[0].label}` : 'No current evidence'
}

function ClauseView() {
  const params = useParams<{ key: string }>()
  const key = decodeURIComponent(params.key)
  const router = useRouter()
  const { selectedOrg } = useOrg()
  const journey = useJourney(key)
  const fw = useFrameworkSystems(key)
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
  const { create } = useEvidencePacks()
  const [system, setSystem] = useState<number | 'all'>('all')
  const [groupPick, setGroupPick] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

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

  const exportPack = async () => {
    setBusy(true)
    setExportError(null)
    const res = await create({ title: `${short} inspection pack`, frameworks: [key], systemIds: systems.map((s) => s.id) })
    setBusy(false)
    if (res.success && res.data) router.push(`/evidence/packs/${res.data.id}`)
    else setExportError(res.error || 'Could not create the inspection pack')
  }

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
            <Heading level={1}>{name}</Heading>
            <Text color="secondary">{[j.binding || j.type, j.version].filter(Boolean).join(' · ')}</Text>
          </VStack>
          <HStack gap={2}>
            <Button variant="secondary" label="Matrix view" href={`/frameworks/${encodeURIComponent(key)}?view=matrix`} />
            <Button label={busy ? 'Exporting' : 'Export for an auditor'} onClick={exportPack} isDisabled={busy || !systems.length} />
          </HStack>
        </HStack>
        <ul className="fx-scope" aria-label="Scope">
          {selectedOrg && (
            <li>
              Organisation <b>{selectedOrg.name}</b>
            </li>
          )}
          <li>
            Systems in scope <b>{systems.length ? systems.map((s) => s.name).join(', ') : 'None yet'}</b>
          </li>
          <li>
            Covered by installed packs <b>{j.coveredInstalled} of {j.active}</b>
          </li>
          {(f?.unconfirmed ?? 0) > 0 && (
            <li>
              Not confirmed{' '}
              <b>
                {f?.unconfirmed} system{f?.unconfirmed === 1 ? '' : 's'}
              </b>{' '}
              · <Link href="/systems">Confirm</Link>
            </li>
          )}
        </ul>
      </VStack>

      {exportError && <Banner status="error" title="Export failed" description={exportError} />}
      {!systems.length && (
        <Banner
          status="info"
          title={`No system has confirmed ${short}`}
          description="The map shows what installed packs cover at organisation level. Confirm the framework on a system to see where that system stands on each requirement."
        />
      )}

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

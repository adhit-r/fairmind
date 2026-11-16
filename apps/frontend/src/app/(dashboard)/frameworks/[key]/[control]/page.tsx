'use client'

import '@/astryx/pages/frameworks.css'
import Link from 'next/link'
import { useParams, useSearchParams } from 'next/navigation'
import { Suspense, useMemo } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { classLabel } from '@/components/ui/matrix'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import { useControls, useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useJourney, useJourneys } from '@/lib/api/hooks/usePacks'
import { Glyph, STATE_LABEL, cellIndex, flatRequirements, orgState, requirementHref, type ReqState } from '../../parts'

const RUN_LABEL: Record<string, string> = { queued: 'Queued', running: 'Running', waiting: 'Waiting for a person', blocked: 'Blocked', done: 'Done', failed: 'Failed' }
const RESULT_LABEL: Record<string, string> = { passed: 'Passed', failed: 'Failed', insufficient: 'Insufficient', not_run: 'Not run' }
const STRONG = new Set(['Satisfies', 'Partially satisfies'])

/** What the decision column says for a state. */
const DECISION: Record<ReqState, string> = {
  proven: 'Current evidence proves this on the system.',
  attested: 'A person attested to this; no measured evidence yet.',
  estimated: 'Estimated from related evidence; nothing measures it directly.',
  planned: 'Planned, with no evidence yet.',
  open: 'No current evidence for the checks that satisfy this.',
  fails: 'A check behind this fails.',
  stale: 'The evidence behind this is out of date.',
  atorg: 'No system gate tracks this; installed packs cover it at organisation level.',
  none: 'Nothing tracks this yet.',
}

const Arrow = () => (
  <div className="fx-gut" aria-hidden="true">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  </div>
)

function Trace() {
  const params = useParams<{ key: string; control: string }>()
  const key = decodeURIComponent(params.key)
  const control = decodeURIComponent(params.control)
  const systemId = useSearchParams().get('system')
  const journey = useJourney(key)
  const journeys = useJourneys()
  const fw = useFrameworkSystems(key)
  const controls = useControls()

  const j = journey.data
  const reqs = useMemo(() => (j ? flatRequirements(j) : []), [j])
  const at = reqs.findIndex((r) => r.control === control)
  const req = at >= 0 ? reqs[at] : null
  const systems = fw.data?.systems ?? []
  const cells = useMemo(() => cellIndex(fw.data ?? null), [fw.data])
  const row = req ? cells.get(req.key) ?? [] : []
  const si = Math.max(0, systems.findIndex((s) => s.id === systemId))
  const system = systems[si] ?? null
  const cell = system ? row[si] ?? null : null
  const state: ReqState = cell ? (cell.state as ReqState) : req ? orgState(req.status) : 'none'

  const names = useMemo(() => new Map((journeys.data ?? []).map((x) => [x.key, shortFrameworkName(x.name)])), [journeys.data])
  const mapped = useMemo(() => {
    if (!req || !controls.data) return []
    const byId = new Map(controls.data.controls.map((c) => [c.id, c]))
    return controls.data.crosswalk.filter((x) => x.key === req.key).map((x) => ({ ...x, control: byId.get(x.commonControl) }))
  }, [req, controls.data])
  const alsoCounts = useMemo(() => {
    if (!req || !controls.data) return []
    const strong = new Set(mapped.filter((m) => STRONG.has(m.relation)).map((m) => m.commonControl))
    const seen = new Set<string>()
    return controls.data.crosswalk
      .filter((x) => strong.has(x.commonControl) && x.relation === 'Satisfies' && !x.key.startsWith(`${key}|`))
      .filter((x) => !seen.has(x.key) && seen.add(x.key))
      .slice(0, 6)
  }, [req, controls.data, mapped, key])

  if ((journey.loading && !j) || (fw.loading && !fw.data)) {
    return (
      <VStack gap={3} aria-busy="true">
        <Skeleton height={40} />
        <Skeleton height={300} />
      </VStack>
    )
  }
  if (journey.error || fw.error || !j) {
    return <EmptyState title="This requirement could not load" description={journey.error || fw.error || 'No data came back.'} actions={<Button label="Try again" onClick={() => { journey.reload(); fw.reload() }} />} />
  }
  if (!req) {
    return <EmptyState title={`${control} is not in ${shortFrameworkName(j.name)}`} description="The link may point at an older version of the framework." actions={<Button variant="secondary" label="Back to the framework" href={`/frameworks/${encodeURIComponent(key)}`} />} />
  }

  const short = shortFrameworkName(j.name)
  const prev = reqs[at - 1]
  const next = reqs[at + 1]
  const checks = cell?.checks ?? []
  const dashed = (s: ReqState) => (s === 'open' || s === 'none' ? ' dash' : '')
  const keep = system ? system.id : undefined

  return (
    <VStack gap={5}>
      <VStack gap={3}>
        <Text type="supporting">
          <Link href="/frameworks">Frameworks</Link> / <Link href={`/frameworks/${encodeURIComponent(key)}`}>{short}</Link> / {req.group}
        </Text>
        <HStack gap={3} hAlign="between" vAlign="start" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>
              {req.control} {req.title}
            </Heading>
            <Text color="secondary">
              {short} · {req.group}
            </Text>
          </VStack>
          <HStack gap={2}>
            {prev && <Button variant="secondary" label={`Previous: ${prev.control}`} href={requirementHref(key, prev.control, keep)} />}
            {next && <Button variant="secondary" label={`Next: ${next.control}`} href={requirementHref(key, next.control, keep)} />}
          </HStack>
        </HStack>
        {systems.length > 0 ? (
          <nav className="fx-chips" aria-label="AI system">
            <Text type="supporting">For</Text>
            {systems.map((s, i) => {
              const st = row[i] ? (row[i]!.state as ReqState) : orgState(req.status)
              return (
                <Link key={s.id} className="fx-chip" href={requirementHref(key, req.control, s.id)} aria-current={i === si ? 'true' : undefined}>
                  <Glyph state={st} />
                  {s.name} <span>{STATE_LABEL[st]}</span>
                </Link>
              )
            })}
          </nav>
        ) : (
          <Text type="supporting">No system has confirmed {short}, so this shows organisation-level coverage only.</Text>
        )}
      </VStack>

      <section className="fm-card" aria-labelledby="fx-trace-title" style={{ padding: 0 }}>
        <div className="fx-pad">
          <Heading level={2} id="fx-trace-title">
            Trace{system ? ` for ${system.name}` : ''}
          </Heading>
          <Text type="supporting">Read left to right: what the standard asks, the FairMind controls that check it, the proof, and where it stands.</Text>
        </div>
        <div className="fx-trace">
          <div>
            <h3>The standard asks</h3>
            <div className="fx-node focus">
              <span className="t">
                {short} {req.control}
              </span>
              <span className="s">{req.title}</span>
            </div>
            {alsoCounts.length > 0 && (
              <div className="fx-node">
                <span className="t" style={{ fontWeight: 500 }}>The same proof also counts for</span>
                {alsoCounts.map((x) => {
                  const [fwKey, code] = x.key.split('|')
                  return (
                    <Link key={x.key} className="s" href={requirementHref(fwKey, code)}>
                      {names.get(fwKey) ?? fwKey} {code}
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
          <Arrow />
          <div>
            <h3>FairMind controls</h3>
            {mapped.length ? (
              mapped.map((m) => (
                <div key={m.commonControl} className="fx-node">
                  <span className="t">
                    {m.commonControl} {m.control?.name ?? ''}
                  </span>
                  <span className="s">{m.relation} this requirement</span>
                </div>
              ))
            ) : (
              <div className="fx-node dash">
                <span className="s">{controls.loading ? 'Loading the crosswalk' : 'No FairMind control maps to this yet'}</span>
              </div>
            )}
          </div>
          <Arrow />
          <div>
            <h3>Proof: checks, workflows and evaluations</h3>
            {checks.map((c) => {
              const st = (c.cell ?? (c.fails ? 'fails' : c.stale ? 'stale' : c.evidenceId ? 'proven' : 'open')) as ReqState
              return (
                <div key={c.check} className={`fx-node${dashed(st)}`}>
                  <span className="t">
                    <Glyph state={st} label={STATE_LABEL[st]} />
                    {c.label}
                  </span>
                  <span className="s">
                    Release check · {c.relation} · {c.evidenceClass ? classLabel(c.evidenceClass) : 'nothing current on file'}
                  </span>
                </div>
              )
            })}
            {req.workflows.map((w) => (
              <Link key={w.id} className={`fx-node${w.latestRun ? '' : ' dash'}`} href={w.latestRun ? `/compliance/runs/${encodeURIComponent(w.latestRun.id)}` : `/compliance/workflows/${encodeURIComponent(w.id)}`}>
                <span className="t">{w.name}</span>
                <span className="s">
                  Workflow · {w.latestRun ? `${RUN_LABEL[w.latestRun.status] ?? w.latestRun.status} · ${new Date(w.latestRun.updatedAt).toLocaleDateString()}` : w.installed ? 'Never run' : 'Its pack is not installed'}
                </span>
                <span className="fx-tag">{w.relation}</span>
              </Link>
            ))}
            {req.evaluations.map((e) => (
              <div key={e.id} className={`fx-node${e.result && e.result !== 'not_run' ? '' : ' dash'}`}>
                <span className="t">
                  {e.result === 'passed' && <Glyph state="proven" label="Passed" />}
                  {e.result === 'failed' && <Glyph state="fails" label="Failed" />}
                  {e.name}
                </span>
                <span className="s">Evaluation · {e.result ? RESULT_LABEL[e.result] : e.installed ? 'Not run' : 'Its pack is not installed'}</span>
              </div>
            ))}
            {!checks.length && !req.workflows.length && !req.evaluations.length && (
              <div className="fx-node dash">
                <span className="s">Nothing produces proof for this yet.</span>
              </div>
            )}
          </div>
          <Arrow />
          <div>
            <h3>Where it stands</h3>
            <div className={`fx-node${dashed(state)}`} style={{ padding: 16 }}>
              <span className="fx-verdict">
                <Glyph state={state} size="lg" />
                {STATE_LABEL[state]}
              </span>
              <p style={{ margin: '8px 0 14px' }}>
                <Text color="secondary">{DECISION[state]}</Text>
              </p>
              <VStack gap={2}>
                {system && <Button label="Open the system" href={`/systems/${encodeURIComponent(system.id)}`} />}
                <Button variant="secondary" label="Attach evidence" href={system ? `/evidence?system=${encodeURIComponent(system.id)}` : '/evidence'} />
              </VStack>
            </div>
          </div>
        </div>
      </section>

      {checks.length > 0 && (
        <section className="fm-card" aria-labelledby="fx-ev-title" style={{ padding: 0 }}>
          <div className="fx-pad">
            <Heading level={2} id="fx-ev-title">Release checks behind it</Heading>
            <Text type="supporting">The checks on {system?.name} that speak to {req.control}, with the evidence each holds now.</Text>
          </div>
          <div className="fx-scroll">
            <table className="fx-table">
              <thead>
                <tr>
                  <th scope="col">Check</th>
                  <th scope="col">Relation</th>
                  <th scope="col">Evidence</th>
                  <th scope="col">Confidence</th>
                  <th scope="col">State</th>
                </tr>
              </thead>
              <tbody>
                {checks.map((c) => {
                  const st = (c.cell ?? 'open') as ReqState
                  return (
                    <tr key={c.check}>
                      <td>{c.label}</td>
                      <td>{c.relation}</td>
                      <td>{c.evidenceClass ? classLabel(c.evidenceClass) : 'Nothing current on file'}</td>
                      <td className="num">{c.confidence.toFixed(2)}</td>
                      <td>
                        <span className="fx-state">
                          <Glyph state={st} />
                          {STATE_LABEL[st]}
                          {c.stale ? ' · stale' : ''}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </VStack>
  )
}

export default function RequirementPage() {
  return (
    <div className="fm-page">
      <Suspense fallback={null}>
        <Trace />
      </Suspense>
    </div>
  )
}

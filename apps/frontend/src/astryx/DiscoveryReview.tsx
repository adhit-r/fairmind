'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useId, useMemo, useState, type MouseEvent } from 'react'
import { ArrowDown, ArrowRight, Check, ScanSearch } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { CheckboxInput } from '@astryxdesign/core/CheckboxInput'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { RadioList, RadioListItem } from '@astryxdesign/core/RadioList'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { SourceMark, detail } from '@/astryx/DiscoveryParts'
import { KIND_LABEL, SOURCE_LABEL, ago, when, type DiscoveredAsset, type Integration } from '@/astryx/data/discovery'
import {
  askOwner,
  decide,
  ignoreCandidate,
  splitSighting,
  useCandidate,
  type Candidate,
  type CandidateDetail,
  type Decision,
  type Tier,
} from '@/astryx/data/review'
import './discovery-review.css'

const STRENGTH_LABEL = { strong: 'Strong match', fair: 'Fair match', single: 'One sighting' } as const
const CHECK_LABEL = { name: 'Same name', service: 'Same service', repo: 'Same repo', person: 'Same person' } as const

function ownerState(c: Candidate): { label: string; tone: 'ok' | 'wait' | '' } {
  if (c.ownerCheck?.answeredAt) return { label: 'Owner answered', tone: 'ok' }
  if (c.ownerCheck) return { label: `Asked ${ago(c.ownerCheck.sentAt)}`, tone: 'wait' }
  return c.owners.length ? { label: 'Owner not asked', tone: '' } : { label: 'No owner found', tone: '' }
}

/** Every waiting system, one row each however many sources saw it. */
export function WaitingList({ candidates, selected, onPick, title, emptyLabel, compact }: {
  candidates: Candidate[]
  selected?: string | null
  onPick: (id: string) => void
  title?: string
  emptyLabel?: string
  compact?: boolean
}) {
  const rowId = useId()
  return (
    <section className="dv-queue" data-compact={compact || undefined} aria-label="Waiting for you">
      <header className="dv-queue-heading">
        <h2>{title ?? (compact ? 'Waiting for review' : `${candidates.length} candidate${candidates.length === 1 ? '' : 's'} awaiting review`)}</h2>
        {!compact && candidates.length > 1 && <span>Newest first</span>}
      </header>
      {candidates.length === 0 ? (
        <p className="dv-queue-empty">{emptyLabel ?? 'No candidates are waiting for review.'}</p>
      ) : (
        <ul>
          {candidates.map((c) => {
            const status = ownerState(c)
            const owner = c.ownerCheck?.email || c.owners[0]?.email
            const sources = c.sources.map((source) => SOURCE_LABEL[source] ?? source).join(', ')
            const sourceId = `${rowId}-${c.id}-source`
            const ownerId = `${rowId}-${c.id}-owner`
            return (
              <li key={c.id}>
                <button
                  type="button"
                  className="dv-queue-row"
                  data-candidate-id={c.id}
                  aria-current={selected === c.id || undefined}
                  aria-label={`Review ${c.name}`}
                  aria-describedby={compact ? sourceId : `${sourceId} ${ownerId}`}
                  onClick={() => onPick(c.id)}
                >
                  <span className="dv-queue-mark" aria-hidden="true">
                    {c.sources[0] ? <SourceMark kind={c.sources[0]} /> : <ScanSearch size={16} />}
                  </span>
                  <span className="dv-queue-item">
                    <strong>{c.name}</strong>
                    <span id={sourceId}>
                      {sources || 'Source unavailable'}{!compact && c.sightings > 1 && ` · ${c.sightings} sightings`}
                    </span>
                  </span>
                  {!compact && (
                    <span className="dv-queue-owner" id={ownerId} data-tone={status.tone || undefined}>
                      {owner && <span>{owner}</span>}
                      <small>{status.label}</small>
                    </span>
                  )}
                  <span className="dv-queue-action">Review <ArrowRight size={13} aria-hidden="true" /></span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

function Merge({ d, integrations, onSplit, busy }: { d: CandidateDetail; integrations?: Integration[]; onSplit: (assetId: string) => void; busy: boolean }) {
  return (
    <section className="dv-review-card" aria-labelledby="merge-title">
      <VStack gap={3}>
        <header className="dv-review-card-heading">
          <h3 id="merge-title" tabIndex={-1}>Source sightings</h3>
          <span>{d.sightings === 1 ? '1 sighting' : `${d.sightings} sightings · ${STRENGTH_LABEL[d.strength]}`}</span>
        </header>
        <ul className="dv-sighting-list">
          {d.members.map((a) => {
            const sourceLabel = SOURCE_LABEL[a.source] ?? a.source
            const connection = integrations?.find((i) => i.id === a.integrationId && i.kind === a.source)?.name
            const connectionPrefix = `${sourceLabel}: `
            const connectionName = connection?.startsWith(connectionPrefix) ? connection.slice(connectionPrefix.length) : connection
            const repo = a.source === 'github' && typeof a.metadata?.repo === 'string' ? a.metadata.repo : ''
            const sighting = repo && repo !== a.name && !repo.endsWith(`/${a.name}`) ? `${a.name} · ${repo}` : repo || a.name
            const evidence = detail(a)
            return (
              <li key={a.id} className="dv-src-row">
                <SourceMark kind={a.source} />
                <span className="dv-sighting-details">
                  <strong>{sourceLabel}{connectionName && connectionName !== sourceLabel && ` · ${connectionName}`}</strong>
                  <span>{sighting}</span>
                  {evidence && <span>{evidence}</span>}
                  {a.discoveredAt && <time dateTime={a.discoveredAt}>{when(a.discoveredAt)}</time>}
                </span>
                {d.sightings > 1 && <Button size="sm" variant="ghost" label="Split" tooltip="Not part of this system" isDisabled={busy} onClick={() => onSplit(a.id)} />}
              </li>
            )
          })}
        </ul>
        {d.checks.length > 0 && (
          <div className="dv-checks">
            {d.checks.map((c) => (
              <div key={`${c.type}:${c.label}`} className="dv-check">
                <Check size={16} strokeWidth={2.4} aria-hidden="true" />
                <span>
                  <b>{CHECK_LABEL[c.type]}</b>
                  <br />
                  {c.label} in {c.sources.map((s) => SOURCE_LABEL[s] ?? s).join(' and ')}
                </span>
              </div>
            ))}
          </div>
        )}
      </VStack>
    </section>
  )
}

function Reach({ d }: { d: CandidateDetail }) {
  const reasons = d.tierReasons.map((reason) => `${reason.charAt(0).toUpperCase()}${reason.slice(1)}.`).join(' ')
  return (
    <section className="dv-review-card" aria-labelledby="reach-title">
      <VStack gap={3}>
        <header className="dv-review-card-heading">
          <h3 id="reach-title" tabIndex={-1}>What it can reach</h3>
          <span className={`dv-chip ${d.suggestedTier}`}>Suggested tier: {d.suggestedTier}</span>
        </header>
        {d.reach.length > 0 ? (
          <dl className="dv-review-reach">
            {d.reach.map((f) => (
              <div key={f.key} data-value={f.value}>
                <dt>{f.label}</dt>
                <dd className="dv-reach-state">
                  <i aria-hidden="true" />
                  {f.value === 'yes' ? 'Yes' : f.value === 'no' ? 'No' : 'Not known'}
                </dd>
                {f.detail && <dd>{f.by === 'owner' ? 'Owner: ' : ''}{f.detail}</dd>}
              </div>
            ))}
          </dl>
        ) : <Text size="sm" color="secondary">No reach evidence recorded.</Text>}
        {(reasons || d.frameworks.length > 0) && (
          <div className="dv-why">
            {reasons && <span>{reasons}</span>}
            {d.frameworks.map((f) => <span key={f} className="dv-chip">{f} may apply</span>)}
          </div>
        )}
      </VStack>
    </section>
  )
}

const QA: { key: keyof NonNullable<CandidateDetail['answers']>; label: string }[] = [
  { key: 'purpose', label: 'What it is for' },
  { key: 'users', label: 'Who uses it' },
  { key: 'data_in', label: 'Data that goes in' },
  { key: 'never_do', label: 'Should never' },
]

function Owner({ id, d, onAsked, onBusy }: { id: string; d: CandidateDetail; onAsked: () => void; onBusy: (busy: boolean) => void }) {
  const orgId = useOrgId()
  const [email, setEmail] = useState(d.ownerCheck?.email ?? d.owners[0]?.email ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState<{ link: string; emailSent: boolean } | null>(null)
  const a = d.answers
  async function ask() {
    setBusy(true)
    onBusy(true)
    setError(null)
    try {
      const out = await askOwner(id, email.trim(), orgId)
      setSent(out)
      onAsked()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send it')
    } finally {
      setBusy(false)
      onBusy(false)
    }
  }
  return (
    <section className="dv-review-card" aria-labelledby="owner-title">
      <VStack gap={3}>
        <header className="dv-review-card-heading">
          <h3 id="owner-title" tabIndex={-1}>Owner</h3>
          {d.ownerCheck?.answeredAt ? (
            <span className="dv-chip ok">Answered {ago(d.ownerCheck.answeredAt)}</span>
          ) : d.ownerCheck ? (
            <span className="dv-chip wait">Asked {ago(d.ownerCheck.sentAt)}</span>
          ) : null}
        </header>
        {d.owners.length > 0 ? (
          d.owners.slice(0, 2).map((o) => (
            <div key={o.email}>
              <HStack gap={3} vAlign="center">
                <span className="dv-av" aria-hidden="true">
                  {o.email.slice(0, 2).toUpperCase()}
                </span>
                <Text weight="semibold">{o.email}</Text>
              </HStack>
              <div className="dv-chips" style={{ marginTop: 8 }}>
                {o.reasons.map((r) => (
                  <span key={r} className="dv-chip">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          ))
        ) : (
          <Text size="sm" color="secondary">
            None of its sources names an owner. Ask the person you think runs it.
          </Text>
        )}
        {a && (
          <>
            {a.own !== 'yes' && (
              <Banner
                status="warning"
                title={a.own === 'someone_else' ? 'They say it belongs to someone else' : 'They do not recognise it'}
                description={a.own === 'someone_else' && a.other_owner ? `They named ${a.other_owner}.` : 'Ask someone else, or ignore it.'}
              />
            )}
            <dl className="dv-qa">
              {QA.filter((q) => a[q.key]).map((q) => (
                <div key={q.key} style={{ display: 'contents' }}>
                  <dt>{q.label}</dt>
                  <dd>{String(a[q.key])}</dd>
                </div>
              ))}
            </dl>
          </>
        )}
        {d.mismatches.map((m) => (
          <div key={m} className="dv-miss">
            <span className="dot" aria-hidden="true" />
            <span>
              <b>Does not match what we found.</b> {m}
            </span>
          </div>
        ))}
        {!d.ownerCheck?.answeredAt && (
          <VStack gap={2}>
            <TextInput label={d.ownerCheck ? 'Ask again, or ask someone else' : 'Ask the owner'} type="email" value={email} onChange={setEmail} description="They get a link to a short form. No account needed; the link lasts 14 days." />
            <HStack gap={2}>
              <Button variant="secondary" label={busy ? 'Sending' : d.ownerCheck ? 'Send again' : 'Send the question'} isDisabled={busy || !email.includes('@')} onClick={() => void ask()} />
            </HStack>
          </VStack>
        )}
        {sent && (
          <Banner
            status={sent.emailSent ? 'success' : 'info'}
            title={sent.emailSent ? 'Sent' : 'Email is not set up here, so copy the link'}
            description={sent.link}
            endContent={<Button size="sm" variant="secondary" label="Copy link" onClick={() => void navigator.clipboard?.writeText(sent.link)} />}
          />
        )}
        {error && <Banner status="error" title="That did not work" description={error} />}
      </VStack>
    </section>
  )
}

function suggestedConditions(d: CandidateDetail): { text: string; from: string; on: boolean }[] {
  const out: { text: string; from: string; on: boolean }[] = []
  const allowed = new Set(d.answers?.tools_allowed ?? d.tools)
  for (const t of d.tools.filter((t) => !allowed.has(t))) out.push({ text: `Remove ${t} from its tools`, from: 'From the mismatch', on: true })
  if (d.answers?.acts_without_person === false) out.push({ text: 'A person checks before it acts', from: "From the owner's answer", on: true })
  if (d.answers?.personal_data === false) out.push({ text: 'No personal data goes in', from: "From the owner's answer", on: true })
  if (d.reach.find((f) => f.key === 'leaves_india')?.value === 'yes' && d.answers?.personal_data) out.push({ text: 'A transfer assessment for personal data leaving India', from: 'From what it can reach', on: false })
  if (!d.sources.includes('litellm') && (d.kind === 'llm_app' || d.kind === 'agent')) out.push({ text: 'Use models only through the gateway', from: 'Suggested', on: false })
  return out
}

const TIER_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

function DecisionCard({ id, d, onDone, onBusy }: { id: string; d: CandidateDetail; onDone: (systemId: string | null) => void; onBusy: (busy: boolean) => void }) {
  const orgId = useOrgId()
  const suggested = useMemo(() => suggestedConditions(d), [d])
  const [choice, setChoice] = useState<Decision['decision']>(suggested.length ? 'conditions' : 'approve')
  const [picked, setPicked] = useState<Record<string, boolean>>(() => Object.fromEntries(suggested.map((s) => [s.text, s.on])))
  const [extra, setExtra] = useState('')
  const [review, setReview] = useState<Decision['review_days']>(90)
  const [tier, setTier] = useState<Tier>(d.suggestedTier)
  const [owner, setOwner] = useState(d.ownerCheck?.answeredAt && d.answers?.own === 'yes' ? d.ownerCheck.email : d.owners[0]?.email ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => setTier(d.suggestedTier), [d.suggestedTier])
  const conditions = [...suggested.filter((s) => picked[s.text]).map((s) => s.text), ...(extra.trim() ? [extra.trim()] : [])]
  async function submit() {
    setBusy(true)
    onBusy(true)
    setError(null)
    try {
      const out = await decide(id, { decision: choice, conditions: choice === 'conditions' ? conditions : [], review_days: review, risk_tier: tier, owner: owner.trim() || undefined }, orgId)
      onDone(out.systemId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the decision')
      setBusy(false)
      onBusy(false)
    }
  }
  return (
    <section className="dv-review-card" aria-labelledby="decide-title">
      <VStack gap={3}>
        <header className="dv-review-card-heading">
          <h3 id="decide-title" tabIndex={-1}>Decision</h3>
          <span>Records who decided and when</span>
        </header>
        <RadioList label="Decision" isLabelHidden value={choice} onChange={(v) => setChoice(v as Decision['decision'])}>
          <RadioListItem value="approve" label="Approve" description="Register it as it is" />
          <RadioListItem value="conditions" label="Approve with conditions" description="Register it, with each condition recorded" />
          <RadioListItem value="retire" label="Retire" description="Do not register it; ask the owner to shut it down" />
        </RadioList>
        {choice === 'conditions' && (
          <VStack gap={2}>
            {suggested.map((s) => (
              <CheckboxInput key={s.text} label={s.text} description={s.from} value={!!picked[s.text]} onChange={(v) => setPicked((p) => ({ ...p, [s.text]: v }))} />
            ))}
            <TextInput label="Another condition" isOptional value={extra} onChange={setExtra} />
          </VStack>
        )}
        {choice !== 'retire' && (
          <div className="dv-fields">
            <Selector label="Risk tier" value={tier} options={TIER_OPTIONS} onChange={(v: string) => setTier(v as Tier)} />
            <Selector
              label="Review again in"
              value={String(review)}
              options={[30, 90, 180].map((n) => ({ value: String(n), label: `${n} days` }))}
              onChange={(v: string) => setReview(Number(v) as Decision['review_days'])}
            />
            <div className="wide">
              <TextInput label="Owner" type="email" value={owner} onChange={setOwner} />
            </div>
          </div>
        )}
        {error && <Banner status="error" title="That did not work" description={error} />}
        <div className="dv-foot">
          <Text size="sm" color="secondary">
            {choice === 'retire'
              ? `Every sighting of ${d.name} is set aside, and the decision is recorded.`
              : `Adds ${d.name} to AI systems with tier ${tier}${owner ? `, owner ${owner}` : ''}${choice === 'conditions' ? ` and ${conditions.length} condition${conditions.length === 1 ? '' : 's'}` : ''}.`}
          </Text>
          <Button
            variant="primary"
            label={busy ? 'Saving' : choice === 'retire' ? 'Retire it' : 'Add to AI systems'}
            isDisabled={busy || (choice === 'conditions' && conditions.length === 0)}
            onClick={() => void submit()}
          />
        </div>
      </VStack>
    </section>
  )
}

function jumpToReviewSection(event: MouseEvent<HTMLAnchorElement>) {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  const target = document.getElementById(event.currentTarget.hash.slice(1))
  if (!target) return
  event.preventDefault()
  target.focus({ preventScroll: true })
  target.scrollIntoView({ block: 'start' })
}

/** One waiting system: how it was merged, what it can reach, its owner, and the decision. */
export function CandidatePanel({ id, reviewed, integrations, onChanged, onClosed, onSplit, onResolved }: {
  id: string
  reviewed?: DiscoveredAsset
  integrations?: Integration[]
  onChanged: () => void
  onClosed: () => void
  onSplit: () => void
  onResolved: (value: { member: string; group: string } | null) => void
}) {
  const router = useRouter()
  const orgId = useOrgId()
  const { refreshSystems } = useSystemContext()
  const { detail: d, loading, error, notFound, refresh } = useCandidate(id)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const group = d?.id
  useEffect(() => {
    onResolved(group ? { member: id, group } : null)
  }, [group, id, onResolved])
  async function act(fn: () => Promise<unknown>, completed: () => void) {
    setBusy(true)
    setActionError(null)
    try {
      await fn()
      completed()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'That did not work')
    } finally {
      setBusy(false)
    }
  }
  if (loading && !d) return <div role="status" aria-label="Loading candidate evidence"><Skeleton height={420} /></div>
  if (notFound) {
    return (
      <EmptyState
        title={reviewed ? reviewed.name : 'Candidate is no longer in this queue'}
        description={reviewed ? `This sighting was ${reviewed.status === 'promoted' ? 'registered' : 'ignored'}.` : 'It may have been reviewed, or the link may no longer match a waiting sighting.'}
        actions={reviewed?.systemId ? <Button label="Open registered system" href={`/systems/${encodeURIComponent(reviewed.systemId)}`} /> : undefined}
      />
    )
  }
  if (error || !d) return <EmptyState title="Candidate evidence could not load" description={error ?? 'The candidate detail is unavailable.'} actions={<Button label="Retry candidate" onClick={() => void refresh()} />} />
  return (
    <fieldset className="dv-candidate-actions" disabled={busy || loading} aria-labelledby="candidate-title">
      <div className="dv-review-stack">
        <section className="dv-review-card dv-review-intro" aria-labelledby="candidate-title">
          <div className="dv-review-intro-main">
            <div>
              <p className="dv-review-status"><i aria-hidden="true" />Awaiting review</p>
              <h2 id="candidate-title">{d.name}</h2>
              <p className="dv-review-meta">
                <span>{KIND_LABEL[d.kind] ?? d.kind}</span>
                <span>First seen <time dateTime={d.firstSeen} title={when(d.firstSeen)}>{ago(d.firstSeen)}</time></span>
                {d.lastSeen !== d.firstSeen && <span>Last seen <time dateTime={d.lastSeen} title={when(d.lastSeen)}>{ago(d.lastSeen)}</time></span>}
              </p>
            </div>
            <Button variant="ghost" label="Ignore" isDisabled={busy} onClick={() => void act(() => ignoreCandidate(id, orgId), onClosed)} />
          </div>
          <nav className="dv-review-navigation" aria-label="Candidate review sections">
            <a href="#merge-title" onClick={jumpToReviewSection}>Source sightings</a>
            <a href="#reach-title" onClick={jumpToReviewSection}>What it can reach</a>
            <a href="#owner-title" onClick={jumpToReviewSection}>Owner</a>
            <a className="dv-review-decision-link" href="#decide-title" onClick={jumpToReviewSection}>Decision <ArrowDown size={14} aria-hidden="true" /></a>
          </nav>
        </section>
        {actionError && <Banner status="error" title="That did not work" description={actionError} isDismissable onDismiss={() => setActionError(null)} />}
        <Merge d={d} integrations={integrations} busy={busy} onSplit={(assetId) => void act(() => splitSighting(assetId, orgId), onSplit)} />
        <Reach d={d} />
        <div className="dv-review-outcome">
          <Owner key={d.id} id={id} d={d} onBusy={setBusy} onAsked={() => {
            refresh()
            onChanged()
          }} />
          <DecisionCard
            key={JSON.stringify([d.id, d.members.map((member) => member.id), d.ownerCheck?.answeredAt])}
            id={id}
            onBusy={setBusy}
            d={d}
            onDone={async (systemId) => {
              if (systemId) {
                onChanged()
                await refreshSystems()
                router.push(`/systems/${encodeURIComponent(systemId)}`)
              } else {
                onClosed()
              }
            }}
          />
        </div>
      </div>
    </fieldset>
  )
}

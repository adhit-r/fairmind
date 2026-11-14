'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Check } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { CheckboxInput } from '@astryxdesign/core/CheckboxInput'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { RadioList, RadioListItem } from '@astryxdesign/core/RadioList'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { SourceMark, detail } from '@/astryx/DiscoveryParts'
import { KIND_LABEL, SOURCE_LABEL, ago, when } from '@/astryx/data/discovery'
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

const KIND: Record<string, string> = { ...KIND_LABEL, agent: 'Agent' }
const STRENGTH_LABEL = { strong: 'Strong match', fair: 'Fair match', single: 'One sighting' } as const
const STRENGTH_BARS = { strong: 3, fair: 2, single: 1 } as const
const CHECK_LABEL = { name: 'Same name', service: 'Same service', repo: 'Same repo', person: 'Same person' } as const

function Conf({ strength }: { strength: Candidate['strength'] }) {
  return (
    <span className="dv-conf" role="img" aria-label={STRENGTH_LABEL[strength]}>
      {[0, 1, 2].map((i) => (
        <span key={i} className={i < STRENGTH_BARS[strength] ? 'f' : ''} />
      ))}
    </span>
  )
}

function ownerState(c: Candidate): { label: string; tone: 'ok' | 'wait' | '' } {
  if (c.ownerCheck?.answeredAt) return { label: 'Owner answered', tone: 'ok' }
  if (c.ownerCheck) return { label: `Asked ${ago(c.ownerCheck.sentAt)}`, tone: 'wait' }
  return c.owners.length ? { label: 'Owner not asked', tone: '' } : { label: 'No owner found', tone: '' }
}

/** Every waiting system, one row each however many sources saw it. */
export function WaitingList({ candidates, selected, onPick, title }: { candidates: Candidate[]; selected?: string | null; onPick: (id: string) => void; title?: string }) {
  const sightings = candidates.reduce((n, c) => n + c.sightings, 0)
  return (
    <section className="fm-card dv-wlist" aria-label="Waiting for you">
      <div className="dv-wlist-hd">
        <Text size="sm" weight="semibold" color="secondary">
          {title ?? `${candidates.length} waiting, ${sightings} sighting${sightings === 1 ? '' : 's'}`}
        </Text>
        <Text size="sm" color="secondary">
          Newest first
        </Text>
      </div>
      {candidates.length === 0 && (
        <div style={{ padding: 16 }}>
          <Text color="secondary">Nothing waiting. Connectors on a schedule keep looking.</Text>
        </div>
      )}
      {candidates.map((c) => {
        const st = ownerState(c)
        return (
          <button key={c.id} type="button" className={`dv-witem${selected === c.id ? ' on' : ''}`} aria-current={selected === c.id} onClick={() => onPick(c.id)}>
            <span style={{ minWidth: 0 }}>
              <span className="nm">{c.name}</span>
              <span className="k">
                {KIND[c.kind] ?? c.kind} · seen {c.sightings === 1 ? 'once' : `${c.sightings} times`}
              </span>
            </span>
            <span className="dv-stack">
              {c.sources.map((s) => (
                <SourceMark key={s} kind={s} size="sm" />
              ))}
            </span>
            <Conf strength={c.strength} />
            <span className={`dv-chip ${st.tone}`}>{st.label}</span>
          </button>
        )
      })}
    </section>
  )
}

function Steps({ d }: { d: CandidateDetail }) {
  const steps: { label: string; done: boolean }[] = [
    { label: `Found ${when(d.firstSeen).split(',')[0]}`, done: true },
    ...(d.sightings > 1 ? [{ label: 'Merged', done: true }] : []),
    { label: d.ownerCheck ? `Owner asked ${when(d.ownerCheck.sentAt).split(',')[0]}` : 'Owner asked', done: !!d.ownerCheck },
    { label: d.ownerCheck?.answeredAt ? `Owner answered ${when(d.ownerCheck.answeredAt).split(',')[0]}` : 'Owner answered', done: !!d.ownerCheck?.answeredAt },
  ]
  return (
    <ol className="dv-steps" aria-label="Progress">
      {steps.map((s) => (
        <li key={s.label} className={s.done ? '' : 'todo'}>
          <span className="d" />
          {s.label}
        </li>
      ))}
      <li className="now">
        <span className="d" />
        Your decision
      </li>
    </ol>
  )
}

function Merge({ d, onSplit, busy }: { d: CandidateDetail; onSplit: (assetId: string) => void; busy: boolean }) {
  return (
    <section className="fm-card" aria-labelledby="merge-title">
      <VStack gap={3}>
        <div>
          <Heading level={3} id="merge-title">
            {d.sightings === 1 ? 'Seen once' : `One system, seen ${d.sightings} times`}
          </Heading>
          <Text size="sm" color="secondary">
            {d.sightings === 1 ? 'Only one source has seen it so far.' : 'Each source saw a piece of it. Together they describe one system.'}
          </Text>
        </div>
        <div className={`dv-merge${d.sightings === 1 ? ' one' : ''}`}>
          <div className="dv-srcs">
            {d.members.map((a) => (
              <div key={a.id} className="dv-src-row">
                <SourceMark kind={a.source} />
                <span style={{ minWidth: 0, flex: 1 }}>
                  <span className="t">{SOURCE_LABEL[a.source] ?? a.source}</span>
                  <span className="s">
                    {a.name}
                    {detail(a) ? ` · ${detail(a)}` : ''}
                  </span>
                </span>
                {d.sightings > 1 && <Button size="sm" variant="ghost" label="Split" tooltip="Not part of this system" isDisabled={busy} onClick={() => onSplit(a.id)} />}
              </div>
            ))}
          </div>
          {d.sightings > 1 && (
            <>
              <div className="dv-bracket" aria-hidden="true" />
              <div className="dv-node">
                <Text size="sm" weight="semibold" color="secondary">
                  Merged as
                </Text>
                <div className="nm">{d.name}</div>
                <HStack gap={2} vAlign="center">
                  <Conf strength={d.strength} />
                  <Text size="sm">{STRENGTH_LABEL[d.strength]}</Text>
                </HStack>
              </div>
            </>
          )}
        </div>
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
  return (
    <section className="fm-card" aria-labelledby="reach-title">
      <VStack gap={3}>
        <div>
          <Heading level={3} id="reach-title">
            What it can reach
          </Heading>
          <Text size="sm" color="secondary">
            The tier comes from what it can touch and do, not from its name.
          </Text>
        </div>
        <div className="dv-reach">
          {d.reach.map((f) => (
            <div key={f.key} className={`dv-rt ${f.value}`}>
              <span className="q">{f.label}</span>
              <span className="a">
                <span className="sq" aria-hidden="true" />
                {f.value === 'yes' ? 'Yes' : f.value === 'no' ? 'No' : 'Not known'}
              </span>
              <span className="w">
                {f.by === 'owner' ? 'Owner: ' : ''}
                {f.detail}
              </span>
            </div>
          ))}
        </div>
        <div className="dv-why">
          <span className={`dv-chip ${d.suggestedTier}`}>{d.suggestedTier[0].toUpperCase() + d.suggestedTier.slice(1)}</span>
          {d.tierReasons.length > 0 && <span>because {d.tierReasons.join(', ')}.</span>}
          {d.frameworks.map((f) => (
            <span key={f} className="dv-chip">
              {f} may apply
            </span>
          ))}
        </div>
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

function Owner({ d, onAsked }: { d: CandidateDetail; onAsked: () => void }) {
  const [email, setEmail] = useState(d.ownerCheck?.email ?? d.owners[0]?.email ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState<{ link: string; emailSent: boolean } | null>(null)
  const a = d.answers
  async function ask() {
    setBusy(true)
    setError(null)
    try {
      const out = await askOwner(d.id, email.trim())
      setSent(out)
      onAsked()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send it')
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="fm-card" aria-labelledby="owner-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
          <Heading level={3} id="owner-title">
            Owner
          </Heading>
          {d.ownerCheck?.answeredAt ? (
            <span className="dv-chip ok">Answered {ago(d.ownerCheck.answeredAt)}</span>
          ) : d.ownerCheck ? (
            <span className="dv-chip wait">Asked {ago(d.ownerCheck.sentAt)}</span>
          ) : null}
        </HStack>
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

const TIERS: Tier[] = ['low', 'medium', 'high', 'critical']

function DecisionCard({ d, onDone }: { d: CandidateDetail; onDone: (systemId: string | null) => void }) {
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
    setError(null)
    try {
      const out = await decide(d.id, { decision: choice, conditions: choice === 'conditions' ? conditions : [], review_days: review, risk_tier: tier, owner: owner.trim() || undefined })
      onDone(out.systemId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the decision')
      setBusy(false)
    }
  }
  return (
    <section className="fm-card" aria-labelledby="decide-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="center">
          <Heading level={3} id="decide-title">
            Decision
          </Heading>
          <Text size="sm" color="secondary">
            Kept as a record with who decided and when
          </Text>
        </HStack>
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
            <Selector label="Risk tier" value={tier} options={TIERS.map((t) => ({ value: t, label: t === d.suggestedTier ? `${t} (suggested)` : t }))} onChange={(v: string) => setTier(v as Tier)} />
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

/** One waiting system: how it was merged, what it can reach, its owner, and the decision. */
export function CandidatePanel({ id, onChanged }: { id: string; onChanged: () => void }) {
  const router = useRouter()
  const { refreshSystems } = useSystemContext()
  const { detail: d, loading, error, refresh } = useCandidate(id)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  async function act(fn: () => Promise<unknown>) {
    setBusy(true)
    setActionError(null)
    try {
      await fn()
      onChanged()
      await refresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'That did not work')
    } finally {
      setBusy(false)
    }
  }
  if (loading && !d) return <Skeleton height={420} />
  if (error || !d) return <EmptyState title="Not waiting any more" description={error ?? 'It may have been decided or ignored.'} />
  return (
    <VStack gap={4}>
      <section className="fm-card">
        <HStack hAlign="between" vAlign="start" wrap="wrap" gap={3}>
          <VStack gap={1}>
            <HStack gap={2} vAlign="center" wrap="wrap">
              <Heading level={2}>{d.name}</Heading>
              <Token size="sm" label={KIND[d.kind] ?? d.kind} />
              <span className={`dv-chip ${d.suggestedTier}`}>Suggested tier: {d.suggestedTier}</span>
            </HStack>
            <Text size="sm" color="secondary">
              First seen {ago(d.firstSeen)} in {SOURCE_LABEL[d.members[0].source] ?? d.members[0].source}. Last seen {ago(d.lastSeen)}.
            </Text>
          </VStack>
          <Button variant="ghost" label="Ignore" isDisabled={busy} onClick={() => void act(() => ignoreCandidate(d.id))} />
        </HStack>
        <Steps d={d} />
      </section>
      {actionError && <Banner status="error" title="That did not work" description={actionError} isDismissable onDismiss={() => setActionError(null)} />}
      <Merge d={d} busy={busy} onSplit={(assetId) => void act(() => splitSighting(assetId))} />
      <Reach d={d} />
      <div className="dv-two">
        <Owner d={d} onAsked={() => void refresh().then(onChanged)} />
        <DecisionCard
          key={`${d.id}:${d.ownerCheck?.answeredAt ?? ''}`}
          d={d}
          onDone={async (systemId) => {
            onChanged()
            if (systemId) {
              await refreshSystems()
              router.push(`/systems/${encodeURIComponent(systemId)}`)
            } else {
              router.replace('/discovery?view=waiting')
            }
          }}
        />
      </div>
    </VStack>
  )
}

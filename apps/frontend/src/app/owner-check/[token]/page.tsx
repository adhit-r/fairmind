'use client'

import '@astryxdesign/core/reset.css'
import '@/astryx/shell.css'
import '@/astryx/pages/discovery.css'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Theme } from '@astryxdesign/core/theme'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { CheckboxInput } from '@astryxdesign/core/CheckboxInput'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { RadioList, RadioListItem } from '@astryxdesign/core/RadioList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { fairmindTheme } from '@/astryx/theme'
import type { OwnerAnswers } from '@/astryx/data/review'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/proxy'
const KIND: Record<string, string> = { agent: 'agent', llm_app: 'AI app', ml_model: 'model', ai_service: 'AI service', ai_assisted_dev: 'AI coding tool', mcp_server: 'MCP server' }
const REASONS: Record<number, string> = {
  404: 'This link is not valid. The address may be incomplete.',
  410: 'This link has expired. Ask your governance team for a new one.',
}

interface View {
  closed: boolean
  name?: string
  kind?: string
  reasons?: string[]
  tools?: string[]
  prefill?: { purpose: string }
  answers?: OwnerAnswers | null
  subject?: string
  questions?: Question[]
}

interface Question { key: string; text: string; options?: string[]; draft?: string; basis?: string }

function QuestionsForm({ url, subject, questions, previous }: { url: string; subject: string; questions: Question[]; previous: Record<string, string> | null }) {
  const [vals, setVals] = useState<Record<string, string>>(() => Object.fromEntries(questions.map((q) => [q.key, previous?.[q.key] ?? q.draft ?? ''])))
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function send() {
    setBusy(true)
    setError(null)
    try {
      const res = await fetch(`${url}/questions`, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, referrerPolicy: 'no-referrer', body: JSON.stringify({ answers: vals }) })
      if (!res.ok) {
        const d = await res.json().catch(() => null)
        throw new Error((d && typeof d.detail === 'string' && d.detail) || REASONS[res.status] || 'Your answers could not be saved')
      }
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Your answers could not be saved')
    } finally {
      setBusy(false)
    }
  }
  if (done) {
    return (
      <>
        <Heading level={1}>Thank you</Heading>
        <Text color="secondary">Your governance team has your answers. They go back as a draft; a reviewer still confirms.</Text>
        <HStack>
          <Button variant="secondary" label="Change my answers" onClick={() => setDone(false)} />
        </HStack>
      </>
    )
  }
  return (
    <>
      <Heading level={1}>{subject}</Heading>
      {questions.map((q) => (
        <section key={q.key} className="fm-card">
          <VStack gap={2}>
            <Text weight="semibold">{q.text}</Text>
            {q.options?.length ? (
              <HStack gap={2} wrap="wrap">
                {q.options.map((o) => (
                  <Button key={o} variant={vals[q.key] === o ? 'primary' : 'secondary'} label={o} onClick={() => setVals((p) => ({ ...p, [q.key]: o }))} />
                ))}
              </HStack>
            ) : (
              <TextArea label="Your answer" rows={3} value={vals[q.key] ?? ''} onChange={(v) => setVals((p) => ({ ...p, [q.key]: v }))} />
            )}
            {q.draft && <Text size="sm" color="secondary">Draft: {q.draft}</Text>}
            {q.basis && <Text size="sm" color="secondary">{q.basis}</Text>}
          </VStack>
        </section>
      ))}
      {error && <Banner status="error" title="Not saved" description={error} />}
      <HStack hAlign="between" vAlign="center" wrap="wrap" gap={3}>
        <Text size="sm" color="secondary">Your answers go back as a draft; a reviewer still confirms.</Text>
        <Button variant="primary" label={busy ? 'Sending' : 'Send answers'} isDisabled={busy || !Object.values(vals).some((v) => v.trim())} onClick={() => void send()} />
      </HStack>
    </>
  )
}

type YesNo = 'yes' | 'no' | 'unsure'
const toYesNo = (v: boolean | null | undefined): YesNo => (v === true ? 'yes' : v === false ? 'no' : 'unsure')
const fromYesNo = (v: YesNo): boolean | null => (v === 'yes' ? true : v === 'no' ? false : null)

const QUESTIONS: { key: 'personal_data' | 'acts_without_person' | 'moves_money' | 'decides_about_people'; label: string; description: string }[] = [
  { key: 'personal_data', label: 'Does personal data go into it?', description: 'Names, emails, phone numbers, health, payment or ID details of customers or staff.' },
  { key: 'acts_without_person', label: 'Does it act without a person checking first?', description: 'For example sends messages, changes records or calls tools on its own.' },
  { key: 'moves_money', label: 'Can it move money?', description: 'Payments, refunds, credits or prices.' },
  { key: 'decides_about_people', label: 'Does it decide about people?', description: 'Hiring, lending, insurance, eligibility, access to services.' },
]

function YesNoQuestion({ label, description, value, onChange }: { label: string; description: string; value: YesNo; onChange: (v: YesNo) => void }) {
  return (
    <RadioList label={label} description={description} value={value} onChange={(v) => onChange(v as YesNo)}>
      <RadioListItem value="yes" label="Yes" />
      <RadioListItem value="no" label="No" />
      <RadioListItem value="unsure" label="Not sure" />
    </RadioList>
  )
}

function Frame({ children }: { children: React.ReactNode }) {
  return (
    <Theme theme={fairmindTheme} mode="light">
      <main style={{ minHeight: '100vh', background: 'var(--color-background-body)', padding: '40px 16px' }}>
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <VStack gap={5}>
            <HStack gap={2} vAlign="center">
              <img src="/logo.png" alt="" width={24} height={24} style={{ borderRadius: '50%' }} />
              <Text weight="semibold">FairMind</Text>
            </HStack>
            {children}
          </VStack>
        </div>
      </main>
    </Theme>
  )
}

export default function OwnerCheckPage() {
  const { token } = useParams<{ token: string }>()
  const url = `${API_BASE}/api/v1/public/owner-check/${encodeURIComponent(token)}`
  const [view, setView] = useState<View | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [own, setOwn] = useState<OwnerAnswers['own']>('yes')
  const [other, setOther] = useState('')
  const [purpose, setPurpose] = useState('')
  const [users, setUsers] = useState('')
  const [dataIn, setDataIn] = useState('')
  const [yn, setYn] = useState<Record<string, YesNo>>({})
  const [tools, setTools] = useState<Record<string, boolean>>({})
  const [never, setNever] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(url, { headers: { Accept: 'application/json' }, referrerPolicy: 'no-referrer' })
      .then(async (res) => {
        if (cancelled) return
        if (!res.ok) {
          setFailure(REASONS[res.status] ?? 'This page could not load. Try again in a minute.')
          return
        }
        const v: View = await res.json()
        setView(v)
        const a = v.answers
        setOwn(a?.own ?? 'yes')
        setOther(a?.other_owner ?? '')
        setPurpose(a?.purpose ?? v.prefill?.purpose ?? '')
        setUsers(a?.users ?? '')
        setDataIn(a?.data_in ?? '')
        setNever(a?.never_do ?? '')
        setYn(Object.fromEntries(QUESTIONS.map((q) => [q.key, toYesNo(a?.[q.key])])))
        const allowed = a?.tools_allowed ? new Set(a.tools_allowed) : null
        setTools(Object.fromEntries((v.tools ?? []).map((t) => [t, allowed ? allowed.has(t) : true])))
      })
      .catch(() => !cancelled && setFailure('This page could not load. Try again in a minute.'))
    return () => {
      cancelled = true
    }
  }, [url])

  async function send() {
    setBusy(true)
    setError(null)
    const body: OwnerAnswers = {
      own,
      other_owner: own === 'someone_else' ? other.trim() || null : null,
      purpose,
      users,
      data_in: dataIn,
      personal_data: fromYesNo(yn.personal_data ?? 'unsure'),
      acts_without_person: fromYesNo(yn.acts_without_person ?? 'unsure'),
      moves_money: fromYesNo(yn.moves_money ?? 'unsure'),
      decides_about_people: fromYesNo(yn.decides_about_people ?? 'unsure'),
      tools_allowed: view?.tools?.length ? Object.entries(tools).filter(([, on]) => on).map(([t]) => t) : null,
      never_do: never,
    }
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, referrerPolicy: 'no-referrer', body: JSON.stringify(body) })
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error((detail && typeof detail.detail === 'string' && detail.detail) || REASONS[res.status] || 'Your answers could not be saved')
      }
      setSaved(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Your answers could not be saved')
    } finally {
      setBusy(false)
    }
  }

  if (failure) {
    return (
      <Frame>
        <Banner status="error" title="This link does not work" description={failure} />
      </Frame>
    )
  }
  if (!view) {
    return (
      <Frame>
        <Skeleton height={320} />
      </Frame>
    )
  }
  if (view.closed) {
    return (
      <Frame>
        <Heading level={1}>Already handled</Heading>
        <Text color="secondary">Your governance team has already decided about this. Nothing more is needed from you.</Text>
      </Frame>
    )
  }
  if (view.questions) {
    return (
      <Frame>
        <QuestionsForm url={url} subject={view.subject ?? 'A few questions'} questions={view.questions} previous={view.answers as unknown as Record<string, string> | null} />
      </Frame>
    )
  }
  if (saved) {
    return (
      <Frame>
        <Heading level={1}>Thank you</Heading>
        <Text color="secondary">Your governance team has your answers. You can change them from this link until it expires.</Text>
        <HStack>
          <Button variant="secondary" label="Change my answers" onClick={() => setSaved(false)} />
        </HStack>
      </Frame>
    )
  }
  const kind = KIND[view.kind ?? ''] ?? 'AI system'
  return (
    <Frame>
      <VStack gap={1}>
        <Heading level={1}>Is this {kind} yours?</Heading>
        <Text color="secondary">
          Your AI governance team found it and your account is linked to it. Your answers help them register it. We filled in what we could; change anything that is wrong. It takes about two minutes.
        </Text>
      </VStack>
      <section className="fm-card">
        <VStack gap={2}>
          <Text weight="semibold" size="lg">
            {view.name}
          </Text>
          {!!view.reasons?.length && (
            <>
              <Text size="sm" weight="semibold" color="secondary">
                Why we think it is yours
              </Text>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {view.reasons.map((r) => (
                  <li key={r}>
                    <Text size="sm" color="secondary">
                      {r}
                    </Text>
                  </li>
                ))}
              </ul>
            </>
          )}
        </VStack>
      </section>
      <RadioList label="Is it yours?" value={own} onChange={(v) => setOwn(v as OwnerAnswers['own'])}>
        <RadioListItem value="yes" label="Yes, I own it" />
        <RadioListItem value="someone_else" label="It belongs to someone else" />
        <RadioListItem value="unknown" label="I don't recognise it" />
      </RadioList>
      {own === 'someone_else' && <TextInput label="Who owns it?" type="email" description="Their work email, so your governance team can ask them." value={other} onChange={setOther} />}
      {own === 'yes' && (
        <>
          <TextArea label="What is it for?" rows={3} value={purpose} onChange={(v) => setPurpose(v)} />
          <TextInput label="Who uses it, and roughly how many people?" value={users} onChange={setUsers} />
          <TextArea label="What data goes into it?" rows={2} value={dataIn} onChange={(v) => setDataIn(v)} />
          {QUESTIONS.map((q) => (
            <YesNoQuestion key={q.key} label={q.label} description={q.description} value={yn[q.key] ?? 'unsure'} onChange={(v) => setYn((p) => ({ ...p, [q.key]: v }))} />
          ))}
          {!!view.tools?.length && (
            <section className="fm-card">
              <VStack gap={2}>
                <Text weight="semibold">Which of these MCP servers should it use?</Text>
                <Text size="sm" color="secondary">
                  Read from its MCP configuration. Untick any it should not have.
                </Text>
                {view.tools.map((t) => (
                  <CheckboxInput key={t} label={t} value={!!tools[t]} onChange={(on) => setTools((p) => ({ ...p, [t]: on }))} />
                ))}
              </VStack>
            </section>
          )}
          <TextInput label="Anything it should never do?" isOptional value={never} onChange={setNever} />
        </>
      )}
      {error && <Banner status="error" title="Not saved" description={error} />}
      <HStack hAlign="between" vAlign="center" wrap="wrap" gap={3}>
        <Text size="sm" color="secondary">
          Only your governance team sees your answers.
        </Text>
        <Button variant="primary" label={busy ? 'Sending' : 'Send answers'} isDisabled={busy || (own === 'someone_else' && !other.includes('@'))} onClick={() => void send()} />
      </HStack>
    </Frame>
  )
}

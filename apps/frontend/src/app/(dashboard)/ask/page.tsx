'use client'

import '@/astryx/pages/ask.css'
import Link from 'next/link'
import { Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { SparklesIcon } from '@heroicons/react/24/outline'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Card } from '@astryxdesign/core/Card'
import { ChatComposer } from '@astryxdesign/core/Chat'
import { ClickableCard } from '@astryxdesign/core/ClickableCard'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Icon } from '@astryxdesign/core/Icon'
import { VStack, HStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'

import { useAIProvider, usePackActions, type AskAnswer } from '@/lib/api/hooks/usePacks'

/** Prompts that work for any estate; they name no system. */
const SUGGESTIONS = [
  'Which AI systems are not ready to release, and why?',
  'What evidence is missing across my systems?',
  'Which release checks are failing?',
  'Which systems have a decision waiting for a person?',
  'What changed in the last week?',
  'Which systems have stale evidence?',
]

interface Turn {
  id: number
  question: string
  answer: AskAnswer | null
  error: string | null
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className="fm-ask"><Skeleton height={120} /></div>}>
      <Ask />
    </Suspense>
  )
}

function Ask() {
  const prefill = useSearchParams().get('q')
  const provider = useAIProvider()
  const { ask } = usePackActions()
  const [draft, setDraft] = useState(prefill ?? '')
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const nextId = useRef(1)
  const prefilled = useRef(false)

  const enabled = provider.data?.config?.enabled === true

  const send = useCallback(
    async (raw: string) => {
      const question = raw.trim().slice(0, 2000)
      if (!question) return
      const id = nextId.current++
      setDraft('')
      setPending(true)
      setTurns((t) => [{ id, question, answer: null, error: null }, ...t])
      const res = await ask(question)
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, answer: res.data, error: res.data ? null : res.error || 'No answer came back' } : x)))
      setPending(false)
    },
    [ask],
  )

  // ?q= asks once, as soon as the provider is known to be switched on.
  useEffect(() => {
    if (prefilled.current || !prefill || !enabled) return
    prefilled.current = true
    void send(prefill)
  }, [prefill, enabled, send])

  return (
    <div className="fm-ask">
      <VStack gap={6}>
        <HStack gap={2} vAlign="center">
          <Icon icon={SparklesIcon} size="md" color="accent" />
          <Heading level={1}>Ask about your AI estate</Heading>
        </HStack>

        {provider.loading ? (
          <Skeleton height={120} />
        ) : provider.error ? (
          <EmptyState title="The AI provider could not load" description={provider.error} actions={<Button label="Try again" onClick={() => provider.reload()} />} />
        ) : !enabled ? (
          <EmptyState
            title="Connect an AI provider to ask questions"
            description="Ask FairMind uses your organisation's own model key. Add one in settings and the questions you ask are answered from your systems and records."
            actions={<Button label="Open AI provider settings" variant="primary" href="/settings?section=ai-provider" />}
          />
        ) : (
          <>
            <VStack gap={2}>
              <ChatComposer
                value={draft}
                onChange={setDraft}
                onSubmit={(v) => void send(v)}
                isDisabled={pending}
                placeholder="Ask a question about your systems, checks or evidence"
              />
              <Text color="secondary" size="sm">
                Answers come from your own systems and records, and link to them. Uses {provider.data?.config?.providerName} {provider.data?.config?.model}.
              </Text>
            </VStack>

            {turns.length === 0 && (
              <div className="fm-ask-suggest">
                {SUGGESTIONS.map((s) => (
                  <ClickableCard key={s} label={s} variant="muted" padding={3} onClick={() => void send(s)}>
                    <Text>{s}</Text>
                  </ClickableCard>
                ))}
              </div>
            )}

            {turns.map((t) => (
              <Card key={t.id} padding={4}>
                <VStack gap={3}>
                  <Text weight="semibold">{t.question}</Text>
                  {t.error ? (
                    <Banner status="error" title="No answer" description={t.error} />
                  ) : t.answer ? (
                    <>
                      <div className="fm-ask-answer"><Text>{t.answer.answer}</Text></div>
                      {t.answer.systems.length > 0 && (
                        <VStack gap={1}>
                          <Text color="secondary" size="sm">Systems it named</Text>
                          <ul className="fm-ask-systems">
                            {t.answer.systems.map((s) => (
                              <li key={s.id}>
                                <Link href={`/systems/${s.id}`}>{s.name}</Link>
                                <Text color="secondary" size="sm">{s.reason}</Text>
                              </li>
                            ))}
                          </ul>
                        </VStack>
                      )}
                      <Text color="secondary" size="sm">
                        Read {t.answer.systemsRead} system{t.answer.systemsRead === 1 ? '' : 's'}, {t.answer.runsRead} run{t.answer.runsRead === 1 ? '' : 's'}, by {t.answer.provider} {t.answer.model}
                      </Text>
                    </>
                  ) : (
                    <Skeleton height={64} />
                  )}
                </VStack>
              </Card>
            ))}
          </>
        )}
      </VStack>
    </div>
  )
}

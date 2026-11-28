'use client'

import '@astryxdesign/core/reset.css'
import '@/astryx/shell.css'
import { useParams } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import { Theme } from '@astryxdesign/core/theme'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { fairmindTheme } from '@/astryx/theme'
import { AskBoard, ReadOnlyBoard } from '@/astryx/ask/AskBoard'
import { SystemContextProvider } from '@/components/workflow/SystemContext'
import { OrgSnapshotProvider } from '@/context/OrgContext'
import { apiClient } from '@/lib/api/api-client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/proxy'
const JSON_HEADERS = { 'Content-Type': 'application/json', Accept: 'application/json' }

interface Content {
  question: string
  board: string
  orgId: string
  data: Record<string, unknown>
  sealedAt: string
  seal: string
  expiresAt: string
}

const day = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

function Frame({ children }: { children: React.ReactNode }) {
  return (
    <Theme theme={fairmindTheme} mode="light">
      <main style={{ minHeight: '100vh', background: 'var(--color-background-body)', padding: '32px 16px' }}>
        <div style={{ maxWidth: 1120, margin: '0 auto' }}>
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

export default function SharedViewPage() {
  const { id } = useParams<{ id: string }>()
  const base = `${API_BASE}/api/v1/public/shared-views/${encodeURIComponent(id)}`
  const [step, setStep] = useState<'loading' | 'gone' | 'email' | 'code' | 'open'>('loading')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [content, setContent] = useState<Content | null>(null)
  const [busy, setBusy] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [check, setCheck] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(
    async (token: string) => {
      const res = await fetch(`${base}/content`, { headers: { Accept: 'application/json', 'X-View-Token': token }, referrerPolicy: 'no-referrer' })
      if (!res.ok) throw new Error(res.status === 404 ? 'gone' : 'Open the view again to continue')
      const c: Content = await res.json()
      apiClient.replay = c.data // the board reads the sealed figures, never the network
      setToken(token)
      setContent(c)
    },
    [base],
  )

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(base, { headers: { Accept: 'application/json' }, referrerPolicy: 'no-referrer' })
        if (cancelled) return
        if (!res.ok) return setStep('gone')
        const v: { access: 'named' | 'link' } = await res.json()
        if (v.access === 'named') return setStep('email')
        setStep('open')
        const opened = await fetch(`${base}/open`, { method: 'POST', headers: JSON_HEADERS, referrerPolicy: 'no-referrer' })
        if (!opened.ok) return setStep('gone')
        await load((await opened.json()).token)
      } catch {
        if (!cancelled) setError('This page could not load. Try again in a minute.')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [base, load])

  const post = (path: string, body: unknown) => fetch(`${base}/${path}`, { method: 'POST', headers: JSON_HEADERS, referrerPolicy: 'no-referrer', body: JSON.stringify(body) })
  const sendCode = async () => {
    setBusy(true)
    setError(null)
    const res = await post('code', { email }).catch(() => null)
    setBusy(false)
    if (res?.ok) setStep('code')
    else setError('The code could not be sent. Try again in a minute.')
  }
  const verify = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await post('verify', { email, code })
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || 'That code did not work. Ask for a new one.')
      await load((await res.json()).token)
    } catch (e) {
      setError(e instanceof Error ? (e.message === 'gone' ? 'This view is no longer available.' : e.message) : 'That code did not work.')
    } finally {
      setBusy(false)
    }
  }

  // Recompute the seal on the server and compare it with the entry the ledger took when the view was sealed.
  const verifySeal = async () => {
    setBusy(true)
    setCheck(null)
    try {
      const res = await fetch(`${base}/seal`, { headers: { Accept: 'application/json', 'X-View-Token': token ?? '' }, referrerPolicy: 'no-referrer' })
      if (!res.ok) throw new Error()
      const r: { matchesStored: boolean; onLedger: boolean; ledgerSeq: number | null; ledgerAt: string | null; chainValid: boolean } = await res.json()
      setCheck(
        !r.matchesStored || !r.chainValid
          ? 'The seal does not match. Do not rely on this view.'
          : r.onLedger
            ? `The seal matches entry ${r.ledgerSeq} on the organisation's ledger, recorded ${r.ledgerAt ? day(r.ledgerAt) : ''}. The ledger chain checks out.`
            : 'The figures match their seal, but the ledger has no entry for this view because it was sealed before views were recorded.',
      )
    } catch {
      setCheck('The seal could not be checked. Try again.')
    } finally {
      setBusy(false)
    }
  }

  if (content) {
    return (
      <Frame>
        <VStack gap={4}>
          <VStack gap={1}>
            <Heading level={1}>{content.question}</Heading>
            <Text color="secondary">Shared with you read-only. You can look and print. You cannot change anything.</Text>
          </VStack>
          <HStack gap={5} wrap="wrap" vAlign="center" hAlign="between">
            <HStack gap={5} wrap="wrap">
              <VStack gap={0}><Text color="secondary" size="sm">Kind</Text><Text weight="semibold">Sealed snapshot</Text></VStack>
              <VStack gap={0}><Text color="secondary" size="sm">Sealed</Text><Text weight="semibold">{day(content.sealedAt)}</Text></VStack>
              <VStack gap={0}><Text color="secondary" size="sm">Seal</Text><Text weight="semibold">sha256 {content.seal.slice(0, 8)}...{content.seal.slice(-4)}</Text></VStack>
              <VStack gap={0}><Text color="secondary" size="sm">Link expires</Text><Text weight="semibold">{day(content.expiresAt)}</Text></VStack>
            </HStack>
            <HStack gap={2}>
              <Button label="Verify seal" onClick={() => void verifySeal()} isDisabled={busy} />
              <Button label="Print" variant="secondary" onClick={() => window.print()} />
            </HStack>
          </HStack>
          {check && <Text role="status">{check}</Text>}
          <ReadOnlyBoard.Provider value>
            <OrgSnapshotProvider orgId={content.orgId}>
              <SystemContextProvider>
                <AskBoard board={content.board} />
              </SystemContextProvider>
            </OrgSnapshotProvider>
          </ReadOnlyBoard.Provider>
          <Text color="secondary" size="sm">This view shows what was on file when it was sealed. It does not certify compliance and it does not approve a release. A person at the organisation makes that decision.</Text>
        </VStack>
      </Frame>
    )
  }

  return (
    <Frame>
      <div style={{ maxWidth: 480 }}>
        <VStack gap={4}>
          {step === 'loading' || step === 'open' ? (
            error ? <Banner status="error" title={error} /> : <Skeleton height={96} />
          ) : step === 'gone' ? (
            <>
              <Heading level={1}>This view is not available</Heading>
              <Text color="secondary">The link may have expired or been closed by the person who shared it. Ask them for a new one.</Text>
            </>
          ) : step === 'email' ? (
            <>
              <Heading level={1}>Open the shared board</Heading>
              <Text color="secondary">Enter the email address the link was sent to. We will send it a one-time code.</Text>
              <TextInput label="Email address" value={email} onChange={setEmail} placeholder="you@example.com" />
              {error && <Banner status="error" title={error} />}
              <HStack><Button label={busy ? 'Sending...' : 'Send code'} variant="primary" isDisabled={busy || !email.includes('@')} onClick={() => void sendCode()} /></HStack>
            </>
          ) : (
            <>
              <Heading level={1}>Enter your code</Heading>
              <Text color="secondary">If {email} was named, a six-digit code is on its way. It works for 10 minutes.</Text>
              <TextInput label="Code" value={code} onChange={setCode} placeholder="123456" />
              {error && <Banner status="error" title={error} />}
              <HStack gap={2}>
                <Button label={busy ? 'Checking...' : 'Open'} variant="primary" isDisabled={busy || code.trim().length !== 6} onClick={() => void verify()} />
                <Button label="Use another email" variant="ghost" onClick={() => { setStep('email'); setCode(''); setError(null) }} />
              </HStack>
            </>
          )}
        </VStack>
      </div>
    </Frame>
  )
}

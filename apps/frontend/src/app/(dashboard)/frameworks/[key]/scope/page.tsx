'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMemo, useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { shortFrameworkName } from '@/lib/api/hooks/useApplicability'
import {
  MIN_SCOPE_REASON, acceptSure, askOwner, confirmScope, isSure, nextItem, sortQueue, toReview,
  useFrameworkScope, type AskOwnerResult, type ScopeItem, type ScopeVerdict,
} from '@/lib/api/hooks/useFrameworkScope'
import { DOT } from '../ScopeCard'

const verdictText = (v: ScopeItem['verdict'], fw: string) =>
  v === 'in' ? `In scope for ${fw}` : v === 'out' ? 'Out of scope' : 'The agent is not sure'
const dotOf = (i: ScopeItem) => (i.status === 'waiting_owner' ? DOT.check : i.verdict === 'unsure' || i.confidence !== 'high' ? DOT.check : DOT.sure)
const field = { width: '100%', padding: '8px 10px', borderRadius: 10, border: '1px solid var(--fm-line)', font: 'inherit', background: '#fff', color: 'var(--fm-ink)' } as const

function Review({ fk, orgId, fw, item, onDone }: { fk: string; orgId: string; fw: string; item: ScopeItem; onDone: (id: string) => void }) {
  const [mode, setMode] = useState<'view' | 'change' | 'ask'>('view')
  const [pick, setPick] = useState<ScopeVerdict>(item.verdict === 'in' ? 'out' : 'in')
  const [reason, setReason] = useState('')
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState<AskOwnerResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const differs = item.verdict === 'unsure' || pick !== item.verdict
  const reasonOk = !differs || reason.trim().length >= MIN_SCOPE_REASON

  const run = async (fn: () => Promise<unknown>, after?: () => void) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
      after ? after() : onDone(item.systemId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'That did not go through')
    } finally {
      setBusy(false)
    }
  }
  const accept = () => item.verdict !== 'unsure' && run(() => confirmScope(fk, orgId, item.systemId, item.verdict as ScopeVerdict))
  const change = () => run(() => confirmScope(fk, orgId, item.systemId, pick, reason.trim()))

  return (
    <section className="fm-card" aria-labelledby="sc-sys" style={{ padding: 16 }}>
      <span style={{ fontSize: 10, letterSpacing: '.09em', textTransform: 'uppercase', color: 'var(--fm-ink3)', fontWeight: 600 }} id="sc-sys">{item.systemName}</span>
      <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-.02em', margin: '6px 0 4px' }}>{verdictText(item.verdict, fw)}</div>
      <div style={{ color: 'var(--fm-ink2)' }}>{item.reason}</div>
      <div style={{ fontSize: 10, letterSpacing: '.09em', textTransform: 'uppercase', color: 'var(--fm-ink3)', fontWeight: 600, marginTop: 14 }}>Evidence</div>
      <div style={{ background: '#fafaf9', border: '1px solid var(--fm-line)', borderRadius: 10, padding: '8px 12px', margin: '6px 0 14px', fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 11.5, lineHeight: 1.8, overflowWrap: 'anywhere' }}>
        {item.evidence.length ? item.evidence.map((e, n) => <div key={n}>{e.ref ? `${e.ref}: ` : ''}{e.text}</div>) : 'No evidence found.'}
      </div>

      {mode === 'change' && (
        <div style={{ display: 'grid', gap: 10, marginBottom: 12 }}>
          <fieldset style={{ border: 0, padding: 0, margin: 0, display: 'flex', gap: 16 }}>
            <legend style={{ fontWeight: 600, marginBottom: 4 }}>Your decision</legend>
            {(['in', 'out'] as const).map((v) => (
              <label key={v} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <input type="radio" name="verdict" checked={pick === v} onChange={() => setPick(v)} />
                {v === 'in' ? 'In scope' : 'Out of scope'}
              </label>
            ))}
          </fieldset>
          {differs && (
            <label style={{ display: 'grid', gap: 4 }}>
              <span style={{ fontWeight: 600 }}>Why? (at least {MIN_SCOPE_REASON} characters, kept in the record)</span>
              <textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} style={field} />
            </label>
          )}
        </div>
      )}
      {mode === 'ask' && !sent && (
        <form style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'end' }} onSubmit={(e) => { e.preventDefault(); void run(async () => setSent(await askOwner(fk, orgId, item.systemId, email.trim())), () => undefined) }}>
          <label style={{ display: 'grid', gap: 4, flex: 1, minWidth: 220 }}>
            <span style={{ fontWeight: 600 }}>Owner&rsquo;s email</span>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} style={field} />
          </label>
          <Button variant="primary" label={busy ? 'Sending' : 'Send the question'} isDisabled={busy || !email.includes('@')} type="submit" />
        </form>
      )}
      {sent && (
        <p role="status" style={{ margin: '0 0 12px', color: 'var(--fm-ink2)', overflowWrap: 'anywhere' }}>
          {sent.emailSent ? 'Email sent. ' : 'No email was sent; share this link yourself. '}
          <a href={sent.link}>{sent.link}</a> (expires {new Date(sent.expiresAt).toLocaleDateString()}).{' '}
          <Button variant="secondary" size="sm" label="Next system" onClick={() => onDone(item.systemId)} />
        </p>
      )}
      {error && <p role="alert" style={{ margin: '0 0 12px', color: '#d64545' }}>{error}</p>}

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        {mode === 'change' ? (
          <>
            <Button variant="primary" label={busy ? 'Saving' : 'Save my decision'} isDisabled={busy || !reasonOk} onClick={() => void change()} />
            <Button variant="secondary" label="Cancel" onClick={() => setMode('view')} />
          </>
        ) : (
          <>
            <Button variant="primary" label={busy ? 'Saving' : 'Accept'} isDisabled={busy || item.verdict === 'unsure'} onClick={() => void accept()} />
            <Button variant="secondary" label="Change" onClick={() => setMode('change')} />
          </>
        )}
        <span style={{ flex: 1 }} />
        {mode !== 'ask' && !sent && (
          <button type="button" onClick={() => setMode('ask')} style={{ background: 'none', border: 0, padding: 0, color: 'var(--fm-ink2)', textDecoration: 'underline', textUnderlineOffset: 3, cursor: 'pointer', font: 'inherit' }}>
            Not sure? Ask the owner
          </button>
        )}
      </div>
    </section>
  )
}

export default function ScopePage() {
  const key = decodeURIComponent(useParams<{ key: string }>().key)
  const { selectedOrg } = useOrg()
  const scope = useFrameworkScope(key)
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const v = scope.data
  const items = useMemo(() => sortQueue(v?.items ?? []), [v])
  const fwName = v ? shortFrameworkName(v.framework.name) : key
  const current = items.find((i) => i.systemId === currentId) ?? nextItem(items) ?? items[0] ?? null
  const total = items.length
  const done = total - toReview(v ?? { items: [] } as never)
  const sure = items.filter(isSure).length

  const back = <Text type="supporting"><Link href={`/frameworks/${encodeURIComponent(key)}`}>{fwName}</Link> / Scope</Text>

  if (scope.loading && !v) return <div className="fm-page"><Skeleton height={40} /><Skeleton height={320} /></div>
  if (scope.error || !v || !selectedOrg) {
    return (
      <div className="fm-page">
        <EmptyState title="The scope could not load" description={scope.error || 'No data came back.'} actions={<Button label="Try again" onClick={scope.reload} />} />
      </div>
    )
  }
  if (!total) {
    return (
      <div className="fm-page">
        {back}
        <EmptyState title="No systems sorted yet" description={`Go back to ${fwName} and choose Sort my systems.`} actions={<Button label={`Back to ${fwName}`} href={`/frameworks/${encodeURIComponent(key)}`} />} />
      </div>
    )
  }

  const onDone = (id: string) => {
    const after = nextItem(items, id)
    setCurrentId(after && after.systemId !== id ? after.systemId : null)
    scope.reload()
  }
  const acceptAll = async () => {
    setBusy(true)
    setError(null)
    try {
      await acceptSure(key, selectedOrg.id)
      setCurrentId(null)
      scope.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not accept the sure ones')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fm-page" style={{ display: 'grid', gap: 14 }}>
      {back}
      <Heading level={1}>Review scope for {fwName}</Heading>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600 }}>{done} of {total}</span>
        <div role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={done} aria-label="Systems reviewed" style={{ height: 4, borderRadius: 999, background: '#e8e8e5', overflow: 'hidden', flex: 1, minWidth: 120 }}>
          <i style={{ display: 'block', height: '100%', width: `${(done / total) * 100}%`, background: 'var(--fm-ink)' }} />
        </div>
        {sure > 0 && (
          <button type="button" disabled={busy} onClick={() => void acceptAll()} style={{ background: 'none', border: 0, padding: 0, font: 'inherit', fontWeight: 600, textDecoration: 'underline', textUnderlineOffset: 3, cursor: 'pointer', color: 'var(--fm-ink)' }}>
            Accept all {sure} the agent is sure of
          </button>
        )}
      </div>
      {error && <p role="alert" style={{ margin: 0, color: '#d64545' }}>{error}</p>}
      {toReview(v) === 0 && <p role="status" style={{ margin: 0, fontWeight: 600 }}>Every system is sorted. <Link href={`/frameworks/${encodeURIComponent(key)}`}>Back to {fwName}</Link></p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(160px, 200px) 1fr', gap: 14, alignItems: 'start' }}>
        <nav className="fm-card" aria-label="Systems" style={{ padding: 6 }}>
          {items.map((i) => (
            <button key={i.systemId} type="button" aria-current={i.systemId === current?.systemId ? 'true' : undefined} onClick={() => setCurrentId(i.systemId)}
              style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '6px 8px', borderRadius: 8, border: 0, font: 'inherit', fontSize: 12, textAlign: 'left', cursor: 'pointer', background: i.systemId === current?.systemId ? '#f1f1ef' : 'none', color: 'var(--fm-ink)', fontWeight: i.systemId === current?.systemId ? 600 : 400 }}>
              {i.status === 'confirmed' ? <span aria-label="Confirmed" style={{ color: DOT.sure, width: 9 }}>&#10003;</span> : <span aria-hidden="true" style={{ width: 9, height: 9, borderRadius: '50%', background: dotOf(i), flex: 'none' }} />}
              <span style={{ overflowWrap: 'anywhere' }}>{i.systemName}</span>
              {i.status === 'waiting_owner' && <span style={{ marginLeft: 'auto', fontSize: 10, color: DOT.check, fontWeight: 600 }}>Owner</span>}
            </button>
          ))}
        </nav>
        {current && <Review key={current.systemId} fk={key} orgId={selectedOrg.id} fw={fwName} item={current} onDone={onDone} />}
      </div>
    </div>
  )
}

'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { allConfirmed, draftScope, hasDrafts, summaryLine, toReview, type ScopeView } from '@/lib/api/hooks/useFrameworkScope'

export const DOT = { sure: '#2e9d5b', check: '#d9962b', wait: 'var(--fm-ink3)' } as const

/** Step 1: the agent's sort of the organisation's systems for this framework. The agent only runs on a click. */
export function ScopeCard({ frameworkKey, view, onChange }: { frameworkKey: string; view: ScopeView | null; onChange: () => void }) {
  const { selectedOrg } = useOrg()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const href = `/frameworks/${encodeURIComponent(frameworkKey)}/scope`

  const sort = async () => {
    if (!selectedOrg) return
    setBusy(true)
    setError(null)
    try {
      await draftScope(frameworkKey, selectedOrg.id)
      onChange()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The agent could not sort the systems')
    } finally {
      setBusy(false)
    }
  }

  const s = view?.summary
  return (
    <section className="fm-card" aria-labelledby="scope-title" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <Heading level={2} id="scope-title">
          {view && hasDrafts(view) ? summaryLine(view) : 'Which of your systems does this framework cover?'}
        </Heading>
        <span style={{ flex: 1 }} />
        {!view || !hasDrafts(view) ? (
          <Button variant="primary" label={busy ? 'Sorting your systems' : 'Sort my systems'} isDisabled={busy || !selectedOrg} onClick={() => void sort()} />
        ) : allConfirmed(view) ? (
          <Link href={href} style={{ fontWeight: 600, textDecoration: 'underline', textUnderlineOffset: 3 }}>Review again</Link>
        ) : (
          <Button variant="primary" label={`Review ${toReview(view)}`} href={href} />
        )}
      </div>
      {!view || !hasDrafts(view) ? (
        <Text type="supporting">The agent reads each system and suggests in scope or out of scope, with its evidence. You confirm each one.</Text>
      ) : (
        !allConfirmed(view) && s && (
          <div style={{ display: 'flex', gap: 16, marginTop: 8, color: 'var(--fm-ink2)' }}>
            <span><i className="scope-dot" style={{ background: DOT.sure }} aria-hidden="true" /><b>{s.sure}</b> sure</span>
            <span><i className="scope-dot" style={{ background: DOT.check }} aria-hidden="true" /><b>{s.check}</b> to check</span>
            <span><i className="scope-dot" style={{ background: DOT.wait }} aria-hidden="true" /><b>{s.waitingOwner}</b> waiting on owner</span>
          </div>
        )
      )}
      {view && hasDrafts(view) && !allConfirmed(view) && <p style={{ margin: '8px 0 0', color: 'var(--fm-ink3)', fontSize: 12 }}>Requirements apply once scope is confirmed.</p>}
      {error && <p role="alert" style={{ margin: '8px 0 0', color: '#d64545' }}>{error}</p>}
      <style>{`.scope-dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:middle}`}</style>
    </section>
  )
}

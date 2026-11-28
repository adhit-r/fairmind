'use client'

import { useEffect, useState } from 'react'
import type { LedgerEntry, PackManifest } from '@/lib/api/hooks/useEvidencePacks'

const GENESIS = '0'.repeat(64)
const NEWEST = 6

const KIND: Record<string, string> = {
  'view.sealed': 'Board shared as a view',
  'view.revoked': 'Shared view closed',
  'board.pinned': 'Board pinned',
  'board.unpinned': 'Board unpinned',
}
const SUBJECT: Record<string, string> = { shared_view: 'Shared view', saved_board: 'Saved board' }

/** Python's json.dumps(sort_keys=True, separators=(",", ":")): the form each entry's hash was taken over, with non-ASCII written as \uXXXX. */
function canonical(v: unknown): string {
  const text = Array.isArray(v)
    ? `[${v.map(canonical).join(',')}]`
    : v && typeof v === 'object'
      ? `{${Object.keys(v as object).sort().map((k) => `${JSON.stringify(k)}:${canonical((v as Record<string, unknown>)[k])}`).join(',')}}`
      : JSON.stringify(v)
  return text.replace(/[\u0080-￿]/g, (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`)
}

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

export type LedgerState =
  | { status: 'none' }
  | { status: 'empty' }
  | { status: 'checking'; count: number }
  | { status: 'unchecked'; count: number }
  | { status: 'intact'; count: number; head: string }
  | { status: 'broken'; count: number; brokenAt: number; expected: string; got: string }

/** The browser's own walk of the ledger, from the first entry: each hash rebuilt, each link to the one before checked. Packs before version 3 carry none. */
export function useLedgerCheck(manifest: PackManifest): LedgerState {
  const chain = (manifest.version ?? 1) >= 3 ? manifest.ledger : undefined
  const canCheck = !!globalThis.crypto?.subtle
  const [state, setState] = useState<LedgerState>(
    !chain ? { status: 'none' } : chain.length === 0 ? { status: 'empty' } : canCheck ? { status: 'checking', count: chain.length } : { status: 'unchecked', count: chain.length },
  )
  useEffect(() => {
    if (!chain || chain.length === 0 || !canCheck) return
    let live = true
    void (async () => {
      let prev = GENESIS
      for (const [i, e] of chain.entries()) {
        const { hash, ...fields } = e
        const rebuilt = await sha256(canonical(fields))
        if (e.seq !== i + 1 || e.prev_hash !== prev || rebuilt !== hash) {
          if (live) setState({ status: 'broken', count: chain.length, brokenAt: e.seq, expected: hash, got: rebuilt })
          return
        }
        prev = hash
      }
      if (live) setState({ status: 'intact', count: chain.length, head: prev })
    })()
    return () => {
      live = false
    }
  }, [chain, canCheck])
  return state
}

const short = (id: string) => (id.length > 12 ? `${id.slice(0, 4)}…${id.slice(-4)}` : id)
const when = (iso: string) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC', hour12: false })
const day = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

/** The second check beside the pack hash: whether the ledger's chain still holds. */
export function LedgerCheckCard({ state }: { state: LedgerState }) {
  const icon = (color: string, body: React.ReactNode) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{body}</svg>
  )
  const link = icon('#1a7f4b', <><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1" /><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" /></>)
  const grey = icon('#5a5f68', <><circle cx="12" cy="12" r="9" /><path d="M8 12h8" /></>)
  const alert = icon('#b42318', <><circle cx="12" cy="12" r="9" /><path d="M12 7v6" /><path d="M12 16.5v.01" /></>)
  if (state.status === 'broken') {
    return (
      <div className="ar-card ar-bad">
        <div className="ar-integrity-head">{alert}<b style={{ color: '#b42318' }}>Ledger chain broken at entry {state.brokenAt}</b></div>
        <p role="alert" className="ar-muted" style={{ color: 'var(--fm-ink, #15171a)' }}>
          Entry {state.brokenAt} does not match its own hash. Entries {state.brokenAt} to {state.count} cannot be relied on. Do not rely on this ledger until the organisation explains it.
        </p>
        <code className="ar-hash">expected {state.expected.slice(0, 12)}…{state.expected.slice(-6)}, got {state.got.slice(0, 12)}…{state.got.slice(-6)}</code>
      </div>
    )
  }
  if (state.status === 'intact') {
    return (
      <div className="ar-card">
        <div className="ar-integrity-head">{link}<b>Ledger chain intact</b></div>
        <p className="ar-muted">Your browser rebuilt all {state.count} entries. Each one links to the one before it, from the first to the last.</p>
        <code className="ar-hash">head {state.head.slice(0, 12)}…{state.head.slice(-6)}</code>
      </div>
    )
  }
  if (state.status === 'checking') {
    return (
      <div className="ar-card">
        <div className="ar-integrity-head">{grey}<b>Checking the ledger</b></div>
        <p className="ar-muted" role="status">Rebuilding {state.count} entries in your browser.</p>
      </div>
    )
  }
  if (state.status === 'unchecked') {
    return (
      <div className="ar-card">
        <div className="ar-integrity-head">{grey}<b>Check the ledger offline</b></div>
        <p className="ar-muted">Your browser could not rebuild the ledger. Run the offline check below before relying on it.</p>
      </div>
    )
  }
  return (
    <div className="ar-card">
      <div className="ar-integrity-head">{grey}<b>{state.status === 'empty' ? 'The ledger is empty' : 'No ledger in this pack'}</b></div>
      <p className="ar-muted">
        {state.status === 'empty'
          ? 'The organisation had recorded nothing on its ledger when this pack was built.'
          : 'This pack was built before packs carried the organisation’s ledger. Its evidence is still checked. Ask for a newer pack if you need the ledger.'}
      </p>
    </div>
  )
}

/** The ledger itself, oldest to newest underneath, shown newest first. Left out for a pack that has none, so a missing ledger is never read as an empty one. */
export function LedgerCard({ chain, state }: { chain: LedgerEntry[]; state: LedgerState }) {
  const broken = state.status === 'broken' ? state.brokenAt : null
  const [all, setAll] = useState(false)
  const rows = [...chain].reverse()
  const shown = all || broken !== null ? rows : rows.slice(0, NEWEST)
  const first = chain[0]
  const last = chain[chain.length - 1]
  return (
    <section className="ar-card" aria-labelledby="ar-ledger">
      <div>
        <h2 id="ar-ledger">Organisation ledger</h2>
        <p className="ar-muted" style={{ marginTop: 4, maxWidth: 720 }}>
          {broken === null
            ? 'What this organisation recorded in FairMind, oldest to newest. Every entry carries the hash of the one before it, so a changed or removed entry breaks every hash after it.'
            : 'Entries before the break still check out. The first entry that does not is marked, and the ones after it are greyed because they follow a link that no longer holds.'}
        </p>
      </div>
      <dl className="ar-facts">
        <div><dt>Entries</dt><dd>{chain.length}</dd></div>
        <div><dt>First entry</dt><dd>{day(first.created_at)}</dd></div>
        <div><dt>Latest entry</dt><dd>{when(last.created_at)} UTC</dd></div>
      </dl>
      <div className="ar-scroll">
        <table className="ar-table" style={{ minWidth: 760 }}>
          <caption className="ar-sr">{broken === null ? 'The newest ledger entries' : 'The ledger entries, with the break marked'}</caption>
          <thead>
            <tr>
              <th scope="col">No.</th><th scope="col">What happened</th><th scope="col">About</th><th scope="col">When (UTC)</th>
              <th scope="col">{broken === null ? 'By' : 'Check'}</th><th scope="col">Hash</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((e) => {
              const after = broken !== null && e.seq > broken
              const at = broken !== null && e.seq === broken
              return (
                <tr key={e.seq} className={at ? 'ar-row-bad' : after ? 'ar-row-dim' : undefined}>
                  <td>{e.seq}</td>
                  <td><b>{KIND[e.kind] ?? e.kind}</b></td>
                  <td>{SUBJECT[e.subject_type] ?? e.subject_type} {short(e.subject_id)}</td>
                  <td>{when(e.created_at)}</td>
                  <td>
                    {broken === null
                      ? e.actor ? `user ${short(e.actor)}` : 'FairMind'
                      : at ? <b style={{ color: '#b42318' }}>Does not match its hash</b> : after ? 'Follows a broken link' : <span style={{ color: '#1a7f4b', fontWeight: 500 }}>Matches</span>}
                  </td>
                  <td className="ar-muted">{e.hash.slice(0, 8)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {broken === null && chain.length > NEWEST && (
        <div className="ar-head">
          <span className="ar-muted">{all ? `Showing all ${chain.length} entries.` : `Showing the newest ${NEWEST} of ${chain.length}.`}</span>
          <button type="button" className="ar-btn" onClick={() => setAll((v) => !v)}>{all ? 'Show the newest only' : `Show all ${chain.length} entries`}</button>
        </div>
      )}
      <p className="ar-muted" style={{ maxWidth: 760, lineHeight: 1.5 }}>
        {broken === null
          ? 'Entries hold ids, hashes and counts. The person is an internal id, not a name or an email address. The ledger shows that something was recorded and that nothing was changed afterwards. It does not certify compliance.'
          : <>A break means an entry was changed or removed after it was written, or the pack was edited. It does not say which. Ask the organisation, and run <b>fairmind verify pack.json</b> to confirm the same result offline.</>}
      </p>
    </section>
  )
}

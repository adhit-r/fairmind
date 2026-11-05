'use client'

import { useState } from 'react'
import { usePackActions, usePlatformConnections, type PlatformConnection, type PlatformTest } from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, ErrorNote, LABEL, MUTED, Pill, when } from '@/components/packs/parts'

const FIELD = 'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'
const COUNT_LABELS: Record<string, string> = { memoryStores: 'memory stores' }

function Platform({ conn, reload }: { conn: PlatformConnection; reload: () => void }) {
  const { savePlatformConnection, deletePlatformConnection, testPlatformConnection } = usePackActions()
  const [apiKey, setApiKey] = useState('')
  const [busy, setBusy] = useState<'save' | 'test' | 'remove' | null>(null)
  const [test, setTest] = useState<PlatformTest | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  async function act(kind: 'save' | 'test' | 'remove') {
    setBusy(kind)
    setFailure(null)
    const res =
      kind === 'save'
        ? await savePlatformConnection(conn.platform, apiKey.trim())
        : kind === 'test'
          ? await testPlatformConnection(conn.platform)
          : await deletePlatformConnection(conn.platform)
    if (res.error) setFailure(res.error)
    else if (kind === 'test') setTest(res.data as PlatformTest)
    else {
      setApiKey('')
      setTest(null)
    }
    setBusy(null)
    reload()
  }

  return (
    <form
      className="flex flex-col gap-4 border-t border-[var(--fm-line)] pt-5 first:border-t-0 first:pt-0"
      onSubmit={(e) => {
        e.preventDefault()
        act('save')
      }}
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <h3 className="m-0 text-[15px] font-semibold text-[var(--fm-ink)]">{conn.name}</h3>
        {conn.connected ? (
          conn.keyReadable ? <Pill tone="done" dot>Connected {conn.keyHint}</Pill> : <Pill tone="warn" dot>Key unreadable</Pill>
        ) : (
          <Pill dot>Not connected</Pill>
        )}
      </div>
      {conn.connected && !conn.keyReadable && <ErrorNote message="The saved key can no longer be read. Enter it again and save." />}
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`platform-key-${conn.platform}`} className="text-[13px] font-semibold text-[var(--fm-ink)]">API key</label>
        <input
          id={`platform-key-${conn.platform}`}
          type="password"
          autoComplete="off"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder={conn.connected ? `Saved key ${conn.keyHint ?? ''}. Paste a new one to replace it.` : 'Paste the key'}
          className={`${FIELD} font-mono`}
        />
        <a href={conn.docs} target="_blank" rel="noreferrer" className={`text-xs underline ${MUTED}`}>
          Get a key for the workspace whose agents you want audited
        </a>
      </div>
      {test && (
        <div role="status" className={`rounded-xl px-4 py-3 text-[13px] ${test.ok ? 'bg-[#e3f5ec] text-[#00704e]' : 'bg-[#fde8e8] text-[#b42318]'}`}>
          <b className="font-semibold">{test.ok ? 'Connection works.' : 'Connection failed.'}</b>{' '}
          {test.counts
            ? `Read ${Object.entries(test.counts).map(([k, n]) => `${n} ${COUNT_LABELS[k] ?? k}`).join(', ')}.`
            : test.message}
        </div>
      )}
      {!test && conn.testedAt && (
        <p className={`m-0 text-xs ${MUTED}`}>
          Last tested {when(conn.testedAt)}: {conn.testedOk ? 'worked' : 'failed'}. {conn.testMessage}
        </p>
      )}
      {failure && <ErrorNote message={failure} />}
      <div className="flex flex-wrap gap-2.5">
        <button type="submit" className={BTN_P} disabled={!!busy || apiKey.trim().length < 8}>
          {busy === 'save' ? 'Saving' : 'Save'}
        </button>
        {conn.connected && (
          <>
            <button type="button" className={BTN} disabled={!!busy || !conn.keyReadable} onClick={() => act('test')}>
              {busy === 'test' ? 'Testing' : 'Test connection'}
            </button>
            <button type="button" className={BTN} disabled={!!busy} onClick={() => act('remove')}>
              {busy === 'remove' ? 'Removing' : 'Remove'}
            </button>
          </>
        )}
      </div>
    </form>
  )
}

/** Agent platforms FairMind reads, with list calls only, to audit how their agents are configured. */
export function PlatformConnectionSettings() {
  const connections = usePlatformConnections()
  if (connections.error) {
    return <ErrorNote message={`Platform connections could not be loaded. ${connections.error}`} onRetry={connections.reload} />
  }
  return (
    <section id="platform-connections" className="mt-8 p-8 fm-card">
      <h2 className="m-0 text-lg font-semibold text-[var(--fm-ink)]">Agent platform connections</h2>
      <p className={`mb-6 mt-2 text-sm leading-normal ${MUTED}`}>
        Connect the platform your agents run on and configuration evaluations read its agents, environments, vaults, memory stores, deployments and recent sessions directly, with read-only calls. The key is encrypted and never shown again. Credential values in vaults are write-only on the platform, so FairMind never sees them.
      </p>
      <div className="flex flex-col gap-5">
        {(connections.data ?? []).map((c) => (
          <Platform key={c.platform} conn={c} reload={connections.reload} />
        ))}
      </div>
      <p className={`mb-0 mt-5 ${LABEL}`}>Only owners and admins can change this.</p>
    </section>
  )
}

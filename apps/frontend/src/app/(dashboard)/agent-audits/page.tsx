'use client'

import '@/astryx/pages/agent-audits.css'
import Link from 'next/link'
import { Fragment, useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import {
  useEvaluations,
  usePackActions,
  usePlatformConnections,
  type PlatformConnection,
  type PlatformTest,
} from '@/lib/api/hooks/usePacks'
import { RESULT_COLOR, RESULT_WORD, fmtWhen } from '@/astryx/data/evaluations'

const PLATFORM = 'claude_managed_agents'
/** Checks that read the connected platform, then the one that runs on an uploaded file. Static config. */
const PLATFORM_CHECKS = ['EV-SEC-18', 'EV-SEC-19', 'EV-SEC-06', 'EV-SEC-27', 'EV-SEC-21', 'EV-SEC-20', 'EV-DEV-01', 'EV-DEV-02', 'EV-SEC-14', 'EV-AGT-01']
const FILE_CHECKS = ['EV-SEC-17']
const COUNT_LABELS: Record<string, string> = { memoryStores: 'memory stores' }

function ConnectionCard({ conn, reload }: { conn: PlatformConnection | null; reload: () => void }) {
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
        ? await savePlatformConnection(PLATFORM, apiKey.trim())
        : kind === 'test'
          ? await testPlatformConnection(PLATFORM)
          : await deletePlatformConnection(PLATFORM)
    if (res.error) setFailure(res.error)
    else if (kind === 'test') setTest(res.data as PlatformTest)
    else {
      setApiKey('')
      setTest(null)
    }
    setBusy(null)
    reload()
  }

  const connected = !!conn?.connected
  return (
    <section className="fm-card" aria-labelledby="au-conn">
      <VStack gap={3}>
        <HStack gap={2} vAlign="center" wrap="wrap">
          <Heading level={2} id="au-conn">{conn?.name ?? 'Claude Managed Agents'}</Heading>
          {connected ? (
            conn?.keyReadable ? (
              <Token size="sm" color="green" label={`Connected${conn.keyHint ? ` ${conn.keyHint}` : ''}`} />
            ) : (
              <Token size="sm" color="yellow" label="Key unreadable" />
            )
          ) : (
            <Token size="sm" color="gray" label="Not connected" />
          )}
        </HStack>
        <Text color="secondary">
          Claude Managed Agents is the only platform FairMind can audit today. With a key for the workspace whose agents you want checked, the audits read its agents, environments, vaults, memory stores, deployments and recent sessions with read-only calls. The key is encrypted and never shown again.
        </Text>
        {connected && !conn?.keyReadable && <Banner status="warning" title="The saved key can no longer be read" description="Enter it again and save." />}
        {test && (
          <Banner
            status={test.ok ? 'success' : 'error'}
            title={test.ok ? 'Connection works' : 'Connection failed'}
            description={
              test.counts
                ? `Read ${Object.entries(test.counts).map(([k, n]) => `${n} ${COUNT_LABELS[k] ?? k}`).join(', ')}.`
                : test.message
            }
          />
        )}
        {!test && conn?.testedAt && (
          <Text type="supporting" color="secondary">
            Last tested {fmtWhen(conn.testedAt)}: {conn.testedOk ? 'worked' : 'failed'}. {conn.testMessage}
          </Text>
        )}
        <div className="fm-au-key">
          <TextInput
            label="API key"
            type="password"
            value={apiKey}
            onChange={setApiKey}
            description={connected ? `Saved key ${conn?.keyHint ?? ''}. Paste a new one to replace it.` : 'Paste the key'}
          />
        </div>
        {conn?.docs && (
          <Text type="supporting" color="secondary">
            <a href={conn.docs} target="_blank" rel="noreferrer">How to get a key</a>
          </Text>
        )}
        {failure && <Banner status="error" title="That did not go through" description={failure} />}
        <HStack gap={2} wrap="wrap">
          <Button label="Save key" variant="primary" size="sm" isLoading={busy === 'save'} isDisabled={!!busy || apiKey.trim().length < 8} onClick={() => act('save')} />
          {connected && (
            <>
              <Button label="Test connection" variant="secondary" size="sm" isLoading={busy === 'test'} isDisabled={!!busy || !conn?.keyReadable} onClick={() => act('test')} />
              <Button label="Disconnect" variant="secondary" size="sm" isLoading={busy === 'remove'} isDisabled={!!busy} onClick={() => act('remove')} />
            </>
          )}
        </HStack>
        <Text type="supporting" color="secondary">Only owners and admins can change this.</Text>
      </VStack>
    </section>
  )
}

export default function AgentAuditsPage() {
  const connections = usePlatformConnections()
  const evals = useEvaluations()
  const [open, setOpen] = useState<Set<string>>(() => new Set())

  const conn = connections.data?.find((c) => c.platform === PLATFORM) ?? null
  const ready = !!conn?.connected && !!conn.keyReadable

  const byId = useMemo(() => new Map((evals.data ?? []).map((e) => [e.id, e])), [evals.data])
  const checks = [...PLATFORM_CHECKS, ...FILE_CHECKS].map((id) => byId.get(id)).filter((e) => !!e)
  const missing = [...PLATFORM_CHECKS, ...FILE_CHECKS].filter((id) => evals.data && !byId.has(id))
  const toggle = (id: string) =>
    setOpen((prev) => {
      const n = new Set(prev)
      if (n.has(id)) n.delete(id)
      else n.add(id)
      return n
    })

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Agent audits</Heading>
          <Text color="secondary">
            Checks on how your agents are set up: tools, MCP servers, memory, sessions and network reach. Only Claude Managed Agents is supported today.
          </Text>
        </VStack>

        {connections.error && (
          <Banner
            status="error"
            title="The platform connection could not be loaded"
            description={connections.error}
            endContent={<Button label="Try again" size="sm" variant="secondary" onClick={connections.reload} />}
          />
        )}
        {connections.loading && !connections.data ? (
          <Skeleton height={200} />
        ) : connections.data ? (
          <ConnectionCard conn={conn} reload={connections.reload} />
        ) : null}

        <VStack gap={2}>
          <Heading level={2}>Audit checks</Heading>
          <Text color="secondary">
            {ready
              ? 'Open a check to run it from the connection on a registered system. Results are the latest per system.'
              : 'Connect Claude Managed Agents above to run the platform checks. Until then each check can run on an uploaded export instead.'}
          </Text>
        </VStack>

        {evals.error && (
          <Banner
            status="error"
            title="The audit checks could not be loaded"
            description={evals.error}
            endContent={<Button label="Try again" size="sm" variant="secondary" onClick={evals.reload} />}
          />
        )}
        {evals.loading && !evals.data ? (
          <Skeleton height={260} />
        ) : evals.data && checks.length === 0 ? (
          <EmptyState title="No audit checks in the catalogue" description="None of the agent audit evaluations are in this organisation's catalogue yet." isCompact />
        ) : evals.data ? (
          <>
            <div className="fm-au-wrap">
              <table className="fm-au-table">
                <thead>
                  <tr>
                    <th scope="col">Check</th>
                    <th scope="col">Reads</th>
                    <th scope="col">Latest result</th>
                    <th scope="col">Systems</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((e) => {
                    const systems = e.results?.systems ?? []
                    const isOpen = open.has(e.id)
                    const fromFile = FILE_CHECKS.includes(e.id)
                    return (
                      <Fragment key={e.id}>
                        <tr className="fm-au-check">
                          <td>
                            <button type="button" className="fm-au-twisty" aria-expanded={isOpen} onClick={() => toggle(e.id)}>
                              {isOpen ? <ChevronDown size={16} aria-hidden /> : <ChevronRight size={16} aria-hidden />}
                              {e.name}
                            </button>
                            <div className="fm-au-id">{e.id}</div>
                          </td>
                          <td>{fromFile ? 'An uploaded file' : 'The connected platform'}</td>
                          <td>
                            {e.results ? (
                              <Token size="sm" color={RESULT_COLOR[e.results.status]} label={RESULT_WORD[e.results.status]} />
                            ) : (
                              <span className="fm-au-muted">Not recorded</span>
                            )}
                          </td>
                          <td>{systems.length}</td>
                          <td>
                            <Button label="Run" variant="secondary" size="sm" href={`/compliance/evaluations/${e.id}`} />
                          </td>
                        </tr>
                        {isOpen && systems.length === 0 && (
                          <tr className="fm-au-child">
                            <td colSpan={5} className="fm-au-muted">
                              {e.results ? 'No system has a result for this check yet.' : 'FairMind does not record results for this check yet.'}
                            </td>
                          </tr>
                        )}
                        {isOpen &&
                          systems.map((s) => (
                            <tr className="fm-au-child" key={`${e.id}-${s.systemId}-${s.evidenceId}`}>
                              <td>
                                <Link href={`/systems/${s.systemId}`}>{s.systemName}</Link>
                              </td>
                              <td colSpan={2}>
                                <HStack gap={2} vAlign="start" wrap="wrap">
                                  <Token size="sm" color={RESULT_COLOR[s.status]} label={RESULT_WORD[s.status]} />
                                  {s.detail && <span>{s.detail}</span>}
                                </HStack>
                              </td>
                              <td colSpan={2} className="fm-au-muted">
                                Evidence <span className="fm-au-id">{s.evidenceId}</span>
                                {fmtWhen(s.at) ? `, ${fmtWhen(s.at)}` : ''}
                              </td>
                            </tr>
                          ))}
                      </Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {missing.length > 0 && (
              <Text type="supporting" color="secondary">Not in this catalogue: {missing.join(', ')}.</Text>
            )}
          </>
        ) : null}
      </VStack>
    </div>
  )
}

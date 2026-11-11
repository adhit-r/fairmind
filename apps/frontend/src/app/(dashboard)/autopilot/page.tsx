'use client'

import '@/astryx/pages/autopilot.css'
import Link from 'next/link'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useAutopilot, useEstateAutopilot, type AutopilotMode } from '@/lib/api/hooks/useAutopilot'
import { useAIProvider, useRuns, type RunStatus } from '@/lib/api/hooks/usePacks'

const MODES: Array<{ value: AutopilotMode; label: string }> = [
  { value: 'off', label: 'Off' },
  { value: 'ask', label: 'Ask first' },
  { value: 'run', label: 'Run' },
]
const RUN_COLOR: Record<RunStatus, 'blue' | 'orange' | 'green' | 'red' | 'gray'> = { running: 'blue', queued: 'gray', waiting: 'orange', blocked: 'orange', done: 'green', failed: 'red' }
const RUN_WORD: Record<RunStatus, string> = { running: 'Running', queued: 'Queued', waiting: 'Waiting', blocked: 'Blocked', done: 'Done', failed: 'Failed' }
const when = (iso?: string | null) => (iso ? new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Never');

/** One system's autopilot; each row owns its hook so the estate needs no bulk endpoint. */
function SystemRow({ id, name }: { id: string; name: string }) {
  const ap = useAutopilot(id)
  const [err, setErr] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const next = (ap.data?.steps ?? []).filter((s) => s.by === 'agent')
  const mode = ap.data?.mode ?? 'off'

  const change = async (m: string) => {
    setSaving(true)
    setErr(null)
    try {
      await ap.setMode(m as AutopilotMode)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not change the mode')
    }
    setSaving(false)
  }

  return (
    <div className="fm-ap-row">
      <div>
        <Link href={`/systems/${encodeURIComponent(id)}`}><b>{name}</b></Link>
        <span className="sub">Last run {when(ap.data?.lastRunAt)}</span>
      </div>
      <div>
        {ap.error && !ap.data ? <Text color="secondary">{ap.error}</Text> : !ap.data ? <Skeleton height={32} /> : (
          <Selector label={`Autopilot mode for ${name}`} isLabelHidden size="sm" value={mode} options={MODES} onChange={change} isDisabled={saving} />
        )}
        {err && <Text color="secondary">{err}</Text>}
      </div>
      <div>
        {!ap.data ? null : next.length === 0 ? (
          <Text color="secondary">Nothing left for the agent to do.</Text>
        ) : (
          <>
            <Text weight="semibold">{next.length} next step{next.length === 1 ? '' : 's'}</Text>
            <span className="sub">{next[0].label}{next.length > 1 ? `, and ${next.length - 1} more` : ''}</span>
          </>
        )}
      </div>
    </div>
  )
}

export default function AutopilotPage() {
  const { systems, loading } = useSystemContext()
  const estate = useEstateAutopilot()
  const provider = useAIProvider()
  const runs = useRuns()

  const all = runs.data ?? []
  const active = all.filter((r) => r.status === 'running' || r.status === 'queued' || r.status === 'waiting' || r.status === 'blocked')
  const recent = all.filter((r) => r.status === 'done' || r.status === 'failed').sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 6)
  const enabled = !!provider.data?.config?.enabled

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Autopilot</Heading>
          <Text color="secondary">What the agents do on your behalf, and how much room each system gives them.</Text>
        </VStack>

        {!provider.loading && !enabled && (
          <Banner
            status="warning"
            title="No AI provider is set up"
            description="Agents that read or write need your organisation's AI provider."
            endContent={<Button label="Set it up in Settings" size="sm" href="/settings" />}
          />
        )}

        <section className="fm-card" aria-label="Estate summary">
          {estate ? (
            <div className="fm-ap-stats">
              <div><b>{estate.systems}</b><span>systems under autopilot view</span></div>
              <div><b>{estate.doneThisWeek}</b><span>steps done this week</span></div>
              <div><b>{estate.needsPerson}</b><span>steps that need a person</span></div>
            </div>
          ) : (
            <Skeleton height={64} />
          )}
        </section>

        <section className="fm-card" aria-label="Agent runs">
          <VStack gap={2}>
            <HStack hAlign="between" vAlign="center">
              <Heading level={2}>Agent runs</Heading>
              <Button label="Open all runs" variant="ghost" size="sm" href="/runs" />
            </HStack>
            {runs.loading && !runs.data ? <Skeleton height={64} /> : runs.error ? (
              <Banner status="error" title="Runs could not load" description={runs.error} endContent={<Button label="Try again" size="sm" onClick={() => runs.reload()} />} />
            ) : active.length + recent.length === 0 ? (
              <EmptyState title="No runs yet" description="Runs appear here when a workflow starts, by an agent or by a person." />
            ) : (
              <div>
                {[...active, ...recent].map((r) => (
                  <Link key={r.id} href={`/runs?run=${encodeURIComponent(r.id)}`} className="fm-ap-run">
                    <span><b>{r.workflowName}</b><br /><span className="sub">{r.currentStep ? `At ${r.currentStep}` : 'No current step'}</span></span>
                    <Token size="sm" color={RUN_COLOR[r.status]} label={RUN_WORD[r.status]} />
                    <span className="sub">{when(r.updatedAt)}</span>
                  </Link>
                ))}
              </div>
            )}
          </VStack>
        </section>

        <section className="fm-card" aria-label="Autopilot by system">
          <VStack gap={2}>
            <Heading level={2}>By system</Heading>
            <Text color="secondary">Off does nothing. Ask first lines up the steps and waits for you. Run lets the agent do the steps it can.</Text>
            {loading ? <Skeleton height={64} /> : systems.length === 0 ? (
              <EmptyState title="No registered AI systems yet" description="Register a system and it gets its own autopilot here." actions={<Button label="Go to Discovery" variant="primary" href="/discovery" />} />
            ) : (
              <div>{systems.map((s) => <SystemRow key={s.id} id={s.id} name={s.name} />)}</div>
            )}
          </VStack>
        </section>
      </VStack>
    </div>
  )
}

'use client'

import '@/astryx/pages/monitoring.css'
import Link from 'next/link'
import { useMemo } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Banner } from '@astryxdesign/core/Banner'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Token } from '@astryxdesign/core/Token'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEstateGates, type EstateGate } from '@/lib/api/hooks/useEstate'
import { usePolicyResource, type PolicyAlert } from '@/lib/api/hooks/usePolicies'
import { useRisks } from '@/lib/api/hooks/useRisks'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import { checkCell, type CellState } from '@/components/ui/matrix'
import { useSystemMonitoring } from '@/astryx/data/monitoring'

const STATE: Record<string, { word: string; color: 'green' | 'blue' | 'orange' | 'red' | 'default' }> = {
  proven: { word: 'Proven', color: 'green' },
  attested: { word: 'Attested', color: 'green' },
  estimated: { word: 'Estimated', color: 'blue' },
  stale: { word: 'Out of date', color: 'orange' },
  fails: { word: 'Drifting', color: 'red' },
  open: { word: 'Never watched', color: 'default' },
}

const when = (iso: string | null | undefined) => {
  const d = iso ? new Date(iso) : null
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'unknown'
}
const cadence = (hours: number) => (hours % 24 === 0 ? `every ${hours / 24 === 1 ? 'day' : `${hours / 24} days`}` : `every ${hours} hours`)

function SystemRow({ id, name, tier, state }: { id: string; name: string; tier: string; state: CellState }) {
  const { runs, policy, loading, error } = useSystemMonitoring(id)
  const latest = runs[0]
  const drift = latest ? latest.attributes.map((a) => a.maxRateDrift).filter((d): d is number => d != null) : []
  const worst = drift.length ? Math.max(...drift) : null
  const s = STATE[state] ?? STATE.open
  return (
    <li className="fm-mon-row">
      <div className="fm-mon-name">
        <Link href={`/systems/${encodeURIComponent(id)}`}>{name}</Link>
        <div>
          <Token size="sm" color={s.color} label={s.word} />
        </div>
      </div>
      <div className="fm-mon-facts">
        {loading ? (
          <Skeleton height={16} width={240} />
        ) : error ? (
          <span>{error}</span>
        ) : latest ? (
          <>
            <span>
              Latest snapshot <b>{when(latest.createdAt)}</b>
            </span>
            <span>
              Overall PSI <b>{latest.overallPsi == null ? 'not scored' : latest.overallPsi.toFixed(3)}</b>
            </span>
            <span>
              Worst attribute drift <b>{worst == null ? 'not scored' : worst.toFixed(3)}</b>
            </span>
            <span>
              Checks <b>{latest.allChecksPass == null ? 'not scored' : latest.allChecksPass ? 'all pass' : 'some fail'}</b>
            </span>
          </>
        ) : (
          <span>No snapshot uploaded yet. {tier} risk.</span>
        )}
        {policy && (
          <span>
            Expected <b>{cadence(policy.cadenceHours)}</b>
            {policy.isDefault ? ' (default)' : ''}
          </span>
        )}
      </div>
      <Button label="Upload a snapshot" variant="secondary" size="sm" href={`/systems/${encodeURIComponent(id)}`} />
    </li>
  )
}

export default function MonitoringPage() {
  const orgId = useOrgId()
  const { systems, loading: systemsLoading } = useSystemContext()
  const gates = useEstateGates()
  const alerts = usePolicyResource<PolicyAlert[]>(orgId ?? null, '/alerts')
  const risks = useRisks()

  const rows = useMemo(() => {
    const byId = new Map((gates.data ?? []).map((g: EstateGate) => [g.systemId, g]))
    return systems.flatMap((s) => {
      const check = byId.get(s.id)?.checks.find((c) => c.key === 'monitoring')
      return check ? [{ system: s, state: checkCell(check) }] : []
    })
  }, [systems, gates.data])

  const count = (...states: CellState[]) => rows.filter((r) => states.includes(r.state)).length
  const nameOf = (id: string | undefined) => systems.find((s) => s.id === id)?.name ?? 'Unknown system'
  const openAlerts = (alerts.data ?? []).filter((a) => a.status === 'open')
  // Findings the watch opened when a system kept drifting; the API sends the system as system_id.
  const watchFindings = risks.data.filter((r) => r.source === 'fairmind.watch' && r.status !== 'closed' && r.status !== 'resolved')

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Monitoring</Heading>
          <Text color="secondary">Is each registered system still behaving the way it was released? Uploaded snapshots are compared against a baseline on a schedule.</Text>
        </VStack>

        {gates.error && <Banner status="error" title="The monitoring checks could not load" description={gates.error} endContent={<Button label="Try again" size="sm" onClick={() => gates.reload()} />} />}

        {(gates.loading && !gates.data) || systemsLoading ? (
          <VStack gap={2}>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={44} />
            ))}
          </VStack>
        ) : !gates.error && rows.length === 0 ? (
          <EmptyState title="No registered AI systems yet" description="Register a system and upload a snapshot of its predictions to start watching it." actions={<Button variant="primary" label="Go to Discovery" href="/discovery" />} />
        ) : (
          !gates.error && (
            <>
              <ul className="fm-mon-counts" aria-label="Monitoring across the estate">
                <li>
                  <b>{count('proven', 'attested')}</b>
                  <span>Proven</span>
                </li>
                <li>
                  <b>{count('estimated')}</b>
                  <span>Estimated</span>
                </li>
                <li className="warn">
                  <b>{count('stale')}</b>
                  <span>Out of date</span>
                </li>
                <li className="bad">
                  <b>{count('fails')}</b>
                  <span>Drifting</span>
                </li>
                <li>
                  <b>{count('open')}</b>
                  <span>Never watched</span>
                </li>
              </ul>

              <div className="fm-mon">
                <section className="fm-card" aria-labelledby="mon-systems">
                  <VStack gap={2}>
                    <Heading level={2} id="mon-systems">
                      Systems
                    </Heading>
                    <ul className="fm-mon-list">
                      {rows.map((r) => (
                        <SystemRow key={r.system.id} id={r.system.id} name={r.system.name} tier={r.system.riskTier} state={r.state} />
                      ))}
                    </ul>
                  </VStack>
                </section>

                <aside className="fm-mon-rail" aria-labelledby="mon-alerts">
                  <section className="fm-card">
                    <VStack gap={3}>
                      <HStack gap={2} vAlign="center" hAlign="between">
                        <Heading level={2} id="mon-alerts">
                          Alerts
                        </Heading>
                        <Text color="secondary">{openAlerts.length + watchFindings.length} open</Text>
                      </HStack>
                      {alerts.error && <Banner status="error" title="Policy alerts could not load" description={alerts.error} endContent={<Button label="Try again" size="sm" onClick={() => alerts.reload()} />} />}
                      {risks.error && <Banner status="error" title="Watch findings could not load" description={risks.error.message} />}
                      {(alerts.loading || risks.loading) && !alerts.error ? (
                        <Skeleton height={60} />
                      ) : openAlerts.length + watchFindings.length === 0 && !alerts.error && !risks.error ? (
                        <Text color="secondary">Nothing open. No policy rule is failing and no watch has opened a finding.</Text>
                      ) : (
                        <ul className="fm-mon-alerts">
                          {openAlerts.map((a) => (
                            <li key={a.id}>
                              <Link href={`/systems/${encodeURIComponent(a.systemId)}`}>{a.systemName}</Link>
                              <span>{a.ruleTitle}</span>
                              <small>
                                Policy {a.policyName} · {a.severity} · opened {when(a.openedAt)}
                              </small>
                            </li>
                          ))}
                          {watchFindings.map((r) => {
                            const sid = (r as { system_id?: string }).system_id ?? r.systemId
                            return (
                              <li key={r.id}>
                                <Link href={sid ? `/findings?system=${encodeURIComponent(sid)}` : '/findings'}>{nameOf(sid)}</Link>
                                <span>{r.title}</span>
                                <small>Monitoring finding · {r.severity}</small>
                              </li>
                            )
                          })}
                        </ul>
                      )}
                      <Button label="See all alerts" variant="ghost" size="sm" href="/alerts" />
                    </VStack>
                  </section>
                </aside>
              </div>
            </>
          )
        )}
      </VStack>
    </div>
  )
}

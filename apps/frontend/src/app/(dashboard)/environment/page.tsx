'use client'

import '@/astryx/pages/environment.css'
import Link from 'next/link'
import { Suspense, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Token } from '@astryxdesign/core/Token'
import { VStack } from '@astryxdesign/core/Layout'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import { useEstateGates } from '@/lib/api/hooks/useEstate'
import { checkCell, type CellState } from '@/components/ui/matrix'
import { downloadCsrd, useEnvAssessments, useEnvBenchmarks } from '@/astryx/data/environment'
import { FindingRetestDraft } from '@/components/workflow/FindingRetestDraft'
import { recordParam } from '@/lib/assurance/evaluationLinks'
import { EnvAssessForm } from '@/astryx/EnvAssessForm'

type Coverage = CellState | 'unknown'

const STATE: Record<string, { word: string; color: 'green' | 'blue' | 'orange' | 'red' | 'default' }> = {
  unknown: { word: 'Gate status unknown', color: 'default' },
  proven: { word: 'Proven', color: 'green' },
  attested: { word: 'Attested', color: 'green' },
  estimated: { word: 'Estimated', color: 'blue' },
  stale: { word: 'Out of date', color: 'orange' },
  fails: { word: 'Fails', color: 'red' },
  excluded: { word: 'Outside release gate', color: 'default' },
  open: { word: 'No current gate evidence', color: 'default' },
}
const TIER: Record<string, 'green' | 'orange' | 'red' | 'default'> = { low: 'green', medium: 'orange', high: 'red' }
const words = (s: string | null | undefined) => (s ? s.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase()) : 'Not recorded')
const day = (iso: string | null | undefined) => {
  const d = iso ? new Date(iso) : null
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : 'unknown date'
}
const yesNo = (v: boolean | undefined) => (v == null ? 'Not recorded' : v ? 'Yes' : 'No')

type Sys = { id: string; name: string }

function SystemRow({ system, orgId, state, focused, onAssess }: { system: Sys; orgId: string | undefined; state: Coverage; focused: boolean; onAssess: (s: Sys) => void }) {
  const { latest, history, loading, error, reload } = useEnvAssessments(orgId, system.id)
  const [exporting, setExporting] = useState<string | null>(null)
  const s = STATE[state] ?? STATE.unknown
  const tier = latest?.impactTier ?? latest?.riskTier ?? null

  const exportIt = async () => {
    if (!orgId) return
    setExporting('')
    try {
      await downloadCsrd(orgId, system.id, system.name)
      setExporting(null)
    } catch (e) {
      setExporting(e instanceof Error ? e.message : 'The export failed')
    }
  }

  return (
    <li className="fm-env-row">
      <div className="fm-env-name">
        <Link href={focused ? `/systems/${encodeURIComponent(system.id)}` : `/environment?system=${encodeURIComponent(system.id)}`}>{system.name}</Link>
        <div>
          <Token size="sm" color={s.color} label={s.word} />
        </div>
      </div>
      <div className="fm-env-facts">
        {loading ? (
          <Skeleton height={16} width={260} />
        ) : error ? (
          <span>{error} <Button label="Retry assessment" size="sm" variant="ghost" onClick={reload} /></span>
        ) : latest ? (
          <>
            <span>
              Impact tier <Token size="sm" color={TIER[(tier ?? '').toLowerCase()] ?? 'default'} label={words(tier)} />
            </span>
            <span>
              Confidence <b>{words(latest.confidenceBand)}</b>
            </span>
            <span>
              Needs a plan to reduce impact <b>{yesNo(latest.result?.requires_mitigation)}</b>
            </span>
            <span>
              Blocks approval <b>{yesNo(latest.result?.approval_blocking)}</b>
            </span>
            <span>
              Version <b>{latest.version}</b>, {day(latest.createdAt)}
            </span>
          </>
        ) : (
          <span>No assessment yet.</span>
        )}
      </div>
      <div className="fm-env-acts">
        <Button label="Start an assessment" size="sm" variant="secondary" onClick={() => onAssess(system)} />
        {latest && <Button label="Export for CSRD" size="sm" variant="ghost" onClick={() => void exportIt()} />}
      </div>
      {exporting && <div className="fm-env-detail"><Banner status="error" title="The export failed" description={exporting} /></div>}
      {focused && history.length > 0 && (
        <div className="fm-env-detail">
          <table>
            <thead>
              <tr>
                <th scope="col">Version</th>
                <th scope="col">Date</th>
                <th scope="col">Impact tier</th>
                <th scope="col">Confidence</th>
                <th scope="col">Recommendation</th>
                <th scope="col">Review</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.assessmentId ?? `${h.version}`}>
                  <td>{h.version}</td>
                  <td>{day(h.createdAt)}</td>
                  <td>{words(h.impactTier ?? h.riskTier)}</td>
                  <td>{words(h.confidenceBand)}</td>
                  <td>{words(h.recommendation)}</td>
                  <td>{words(h.reviewerState)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </li>
  )
}

function Benchmarks() {
  const { data, loading, error } = useEnvBenchmarks()
  if (loading) return <Skeleton height={60} />
  if (error || !data?.thresholds) return <Text color="secondary">{error ?? 'Benchmark thresholds unavailable.'}</Text>
  return (
    <VStack gap={2}>
      {data.provisional && <Text color="secondary">These thresholds are provisional and will be recalibrated from real assessments.</Text>}
      <table>
        <thead>
          <tr>
            <th scope="col">Measured</th>
            <th scope="col">Figure</th>
            <th scope="col">Low below</th>
            <th scope="col">High above</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data.thresholds).map(([phase, t]) => (
            <tr key={phase}>
              <td>{words(phase)}</td>
              <td>{words(t.metric)}</td>
              <td>
                {t.low_max} {t.unit}
              </td>
              <td>
                {t.high_min} {t.unit}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </VStack>
  )
}

function EnvironmentView() {
  const router = useRouter()
  const params = useSearchParams()
  const scope = recordParam(params, 'system')
  const focus = scope ?? undefined
  const finding = recordParam(params, 'finding')
  const orgId = useOrgId() ?? undefined
  const { systems, loading: systemsLoading, error: registryError, refreshSystems } = useSystemContext()
  const gates = useEstateGates()
  const [selected, setAssessing] = useState<Sys | null>(null)
  const [saved, setSaved] = useState(0)

  const rows = useMemo(() => {
    const observed = !gates.error && !gates.loading && Array.isArray(gates.data) ? gates.data : []
    const byId = new Map(observed.map((gate) => [gate.systemId, gate]))
    const live = systems.filter((system) => system.stage !== 'retired' && (!focus || system.id === focus))
    return live.map((system) => {
      const gate = byId.get(system.id)
      const check = gate?.checks?.find((c) => c.key === 'environmental')
      const state: Coverage = check ? checkCell(check) : Array.isArray(gate?.checks) ? 'excluded' : 'unknown'
      return { system, state }
    })
  }, [systems, gates.data, gates.error, gates.loading, focus])
  const requested = params.get('action') === 'assess'
  const assessing = requested ? rows.find(({ system }) => system.id === focus)?.system ?? null : selected
  function closeAssessment() {
    setAssessing(null)
    if (requested) {
      const next = new URLSearchParams(params.toString())
      next.delete('action')
      next.delete('finding')
      router.replace(`/environment?${next}`, { scroll: false })
    }
  }
  const hasKnownGate = rows.some((row) => row.state !== 'unknown')
  const count = (...states: Coverage[]) =>
    hasKnownGate || states.includes('unknown') ? rows.filter((row) => states.includes(row.state)).length : '—'


  const form = assessing && orgId ? (
    <EnvAssessForm
      orgId={orgId}
      systemId={assessing.id}
      onSaved={() => {
        closeAssessment()
        setSaved((n) => n + 1)
        gates.reload()
      }}
    />
  ) : null
  if (requested && (!focus || (!systemsLoading && !registryError && !assessing))) {
    return <div className="fm-page fm-env"><Banner status="warning" title="Assessment unavailable" description="An active system with the requested ID could not be verified." /></div>
  }

  return (
    <div className="fm-page fm-env">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Environment</Heading>
          <Text color="secondary">
            Energy and carbon for active registered AI systems, scored into an impact tier with a stated confidence. {focus && <Link href="/environment">Show every system</Link>}
          </Text>
        </VStack>

        {rows.length > 0 && rows.every((row) => row.state === 'excluded') && (
          <Banner
            status="info"
            title="Not counted in release decisions"
            description="Environmental impact is outside the release gate for the systems shown. Assessments here still feed CSRD reporting. An owner or admin can count them in Settings."
            endContent={<Button label="Open Settings" size="sm" href="/settings" />}
          />
        )}

        {registryError && <Banner status="error" title="The system register could not load" description={registryError} endContent={<Button label="Retry register" size="sm" onClick={() => void refreshSystems()} />} />}
        {gates.loading && <Text color="secondary">Loading gate coverage…</Text>}
        {gates.error && <Banner status="error" title="The environmental checks could not load" description={gates.error} endContent={<Button label="Try again" size="sm" onClick={() => gates.reload()} />} />}

        {systemsLoading ? (
          <VStack gap={2}>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} height={44} />
            ))}
          </VStack>
        ) : registryError ? null : rows.length === 0 ? (
          <EmptyState title={focus ? 'That system is outside the active register' : 'No active registered systems'} description="Register a system, then assess its energy and carbon use here." actions={<Button label="Open AI systems" href="/systems" />} />
        ) : (
          <>
              <ul className="fm-env-counts" aria-label="Environmental checks for active systems in this view">
                <li>
                  <b>{count('proven', 'attested')}</b>
                  <span>Proven or attested</span>
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
                  <span>Fails</span>
                </li>
                <li>
                  <b>{count('unknown')}</b>
                  <span>Gate status unknown</span>
                </li>
                <li>
                  <b>{count('open')}</b>
                  <span>No current gate evidence</span>
                </li>
                <li>
                  <b>{count('excluded')}</b>
                  <span>Outside release gate</span>
                </li>
              </ul>
              <section className="fm-card" aria-labelledby="env-systems">
                <VStack gap={2}>
                  <Heading level={2} id="env-systems">
                    Systems
                  </Heading>
                  <ul className="fm-env-list">
                    {rows.map((r) => (
                      <SystemRow key={`${r.system.id}-${saved}`} system={r.system} orgId={orgId} state={r.state} focused={Boolean(focus)} onAssess={setAssessing} />
                    ))}
                  </ul>
                </VStack>
              </section>
              <section className="fm-card" aria-labelledby="env-bench">
                <VStack gap={3}>
                  <Heading level={2} id="env-bench">
                    How impact tiers are set
                  </Heading>
                  <Benchmarks />
                </VStack>
              </section>
          </>
        )}
      </VStack>

      <Drawer isOpen={assessing !== null} onOpenChange={(o) => !o && closeAssessment()} label={assessing ? `Start an assessment on ${assessing.name}` : 'Start an assessment'} width={460} padding={5}>
        {assessing && orgId && (
          <VStack gap={4}>
            <Heading level={2}>Start an assessment</Heading>
            <Text color="secondary">{assessing.name}. The result is scored on save and added to the version trail.</Text>
            {requested && finding !== undefined
              ? <FindingRetestDraft systemId={assessing.id} findingId={finding} source="environmental_impact">{form}</FindingRetestDraft>
              : form}
          </VStack>
        )}
      </Drawer>
    </div>
  )
}

export default function EnvironmentPage() {
  return (
    <Suspense fallback={<div className="fm-page"><Skeleton height={40} /></div>}>
      <EnvironmentView />
    </Suspense>
  )
}

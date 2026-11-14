'use client'

import '@/astryx/pages/frameworks.css'
import Link from 'next/link'
import { Fragment, useEffect, useState } from 'react'
import { Check, Clock, PenLine, X } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Token } from '@astryxdesign/core/Token'
import { useFrameworkSystems } from '@/lib/api/hooks/useEstate'
import { useInstaller, useJourney, useJourneys } from '@/lib/api/hooks/usePacks'
import { KIND_LABEL, type CellState } from '@/components/ui/matrix'

function Mark({ state }: { state: string }) {
  if (state === 'proven') return <Check size={14} strokeWidth={2.6} aria-hidden />
  if (state === 'attested') return <PenLine size={12} strokeWidth={2.4} aria-hidden />
  if (state === 'fails') return <X size={14} strokeWidth={2.6} aria-hidden />
  if (state === 'stale') return <Clock size={12} strokeWidth={2.4} aria-hidden />
  if (state === 'estimated') return <span className="tilde" aria-hidden>~</span>
  return null
}

const KEY: CellState[] = ['proven', 'attested', 'estimated', 'stale', 'fails', 'open']

/** One framework's requirements against the systems that confirmed it, from the system-by-requirement coverage. */
function Coverage({ fwKey }: { fwKey: string }) {
  const journey = useJourney(fwKey)
  const fw = useFrameworkSystems(fwKey)
  if ((journey.loading && !journey.data) || (fw.loading && !fw.data)) {
    return (
      <VStack gap={2} aria-busy="true">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={26} />
        ))}
      </VStack>
    )
  }
  const err = journey.error || fw.error
  if (err || !journey.data || !fw.data) {
    return <EmptyState title="Coverage could not load" description={err ?? 'No data came back.'} actions={<Button label="Try again" onClick={() => { journey.reload(); fw.reload() }} />} />
  }
  const j = journey.data
  const f = fw.data
  if (!f.systems.length) {
    return (
      <EmptyState
        title="No system has confirmed this framework"
        description={`${f.unconfirmed} registered system${f.unconfirmed === 1 ? '' : 's'} not confirmed yet, ${f.notInScope} not in scope. Confirm the frameworks that apply on a system's file and it appears here.`}
        actions={<Button variant="secondary" label="Open AI systems" href="/systems" />}
      />
    )
  }
  const byKey = new Map(f.requirements.map((r) => [r.key, r.cells]))
  return (
    <VStack gap={3}>
      <div className="fw-cov">
        <table>
          <thead>
            <tr>
              <th scope="col" className="req">Requirement</th>
              {f.systems.map((s) => (
                <th key={s.id} scope="col" title={`${s.name} (${s.riskTier} risk)`}>
                  <Link href={`/systems/${encodeURIComponent(s.id)}`}>{s.name}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {j.groups.map((g) => (
              <Fragment key={g.name}>
                <tr className="grp">
                  <th colSpan={f.systems.length + 1} scope="rowgroup">{g.name}</th>
                </tr>
                {g.requirements.map((r) => {
                  const cells = byKey.get(r.key)
                  return (
                    <tr key={r.key}>
                      <th scope="row" className="req">
                        <code>{r.control}</code>
                        {r.title}
                      </th>
                      {f.systems.map((s, i) => {
                        const c = cells?.[i]
                        const state = c?.state ?? 'none'
                        const word = c ? KIND_LABEL[c.state] ?? c.state : 'Not tracked for this system'
                        return (
                          <td key={s.id}>
                            <span className={`cell mini ${state}`} role="img" aria-label={`${r.control} on ${s.name}: ${word}`} title={word} style={{ cursor: 'default' }}>
                              <Mark state={state} />
                            </span>
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <div className="fw-key">
        {KEY.map((k) => (
          <span key={k}>
            <i className={`cell ${k}`}>
              <Mark state={k} />
            </i>
            {(KIND_LABEL[k] ?? k).replace(/^./, (c) => c.toUpperCase())}
          </span>
        ))}
        <span>
          <i className="cell none" />
          Not tracked
        </span>
      </div>
      {(f.unconfirmed > 0 || f.notInScope > 0) && (
        <Text type="supporting">
          {f.unconfirmed} registered system{f.unconfirmed === 1 ? ' has' : 's have'} not confirmed which frameworks apply; {f.notInScope} {f.notInScope === 1 ? 'is' : 'are'} not in scope.
        </Text>
      )}
    </VStack>
  )
}

export default function FrameworksPage() {
  const journeys = useJourneys()
  const installer = useInstaller(() => journeys.reload())
  const [sel, setSel] = useState<string | null>(null)
  const rows = journeys.data ?? []

  useEffect(() => {
    if (!sel && rows.length) setSel(rows.find((r) => r.active > 0)?.key ?? rows[0].key)
  }, [rows, sel])

  const chosen = rows.find((r) => r.key === sel)

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Frameworks</Heading>
          <Text color="secondary">The rules and standards you answer to, how much of each the installed packs cover, and where each system stands.</Text>
        </VStack>

        {installer.failure && <Banner status="error" title="Install failed" description={installer.failure} />}

        {journeys.loading && !journeys.data ? (
          <VStack gap={2} aria-busy="true">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={36} />
            ))}
          </VStack>
        ) : journeys.error ? (
          <EmptyState title="Frameworks could not load" description={journeys.error} actions={<Button label="Try again" onClick={() => journeys.reload()} />} />
        ) : rows.length === 0 ? (
          <EmptyState title="No frameworks are loaded" description="This organisation has no frameworks yet." actions={<Button variant="secondary" label="Open the packs hub" href="/compliance" />} />
        ) : (
          <section className="fm-card" aria-label="Frameworks">
            <div className="fw-scroll">
              <table className="fw-table">
                <thead>
                  <tr>
                    <th scope="col">Framework</th>
                    <th scope="col">Pillar</th>
                    <th scope="col">Type</th>
                    <th scope="col">Covered by installed packs</th>
                    <th scope="col">Covered by all packs</th>
                    <th scope="col">Packs</th>
                    <th scope="col">Waiting</th>
                    <th scope="col"><span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => {
                    const missing = r.coveredAll > r.coveredInstalled
                    return (
                      <tr key={r.key} className={r.key === sel ? 'on' : undefined}>
                        <td className="name">
                          <Link href={`/frameworks/${encodeURIComponent(r.key)}`}>{r.name}</Link>
                        </td>
                        <td>{r.pillar}</td>
                        <td>{[r.type, r.binding].filter(Boolean).join(' · ') || ''}</td>
                        <td className="num">{r.coveredInstalled} of {r.active}</td>
                        <td className="num">{r.coveredAll} of {r.active}</td>
                        <td className="num">{r.contributingPacks.length}</td>
                        <td>{r.waiting > 0 ? <Token size="sm" color="orange" label={`${r.waiting} waiting`} /> : ''}</td>
                        <td className="act">
                          <HStack gap={2} hAlign="end">
                            {missing && (
                              <Button
                                label={installer.busy === r.key ? 'Installing' : 'Install all packs'}
                                variant="secondary"
                                size="sm"
                                isDisabled={installer.busy !== null}
                                onClick={() => installer.framework(r.key)}
                              />
                            )}
                            <Button label="Show coverage" variant={r.key === sel ? 'primary' : 'ghost'} size="sm" onClick={() => setSel(r.key)} />
                          </HStack>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {chosen && (
          <section className="fm-card" aria-labelledby="fw-cov-title">
            <VStack gap={4}>
              <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
                <VStack gap={1}>
                  <Heading level={2} id="fw-cov-title">{chosen.name}</Heading>
                  <Text color="secondary">Every requirement against every system that confirmed this framework.</Text>
                </VStack>
                <HStack gap={2}>
                  <Button label="Open the framework" variant="secondary" href={`/frameworks/${encodeURIComponent(chosen.key)}`} />
                  <Button label="Export an auditor pack" variant="primary" href={`/auditor-packs?framework=${encodeURIComponent(chosen.key)}`} />
                </HStack>
              </HStack>
              <Coverage fwKey={chosen.key} />
            </VStack>
          </section>
        )}
      </VStack>
    </div>
  )
}

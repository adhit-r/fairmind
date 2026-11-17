'use client'

import '@/astryx/pages/frameworks.css'
import Link from 'next/link'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Token } from '@astryxdesign/core/Token'
import { useEstateFrameworks } from '@/lib/api/hooks/useEstate'
import { useInstaller, useJourneys, type JourneySummary } from '@/lib/api/hooks/usePacks'
import { Legend, NEEDS_WORK, StateBar } from './parts'

const href = (key: string) => `/frameworks/${encodeURIComponent(key)}`
const kind = (r: JourneySummary) => r.binding || r.type || ''

function Rows({ n }: { n: number }) {
  return (
    <VStack gap={2} aria-busy="true">
      {Array.from({ length: n }, (_, i) => (
        <Skeleton key={i} height={44} />
      ))}
    </VStack>
  )
}

export default function FrameworksPage() {
  const journeys = useJourneys()
  const estate = useEstateFrameworks()
  const installer = useInstaller(() => journeys.reload())
  const all = journeys.data ?? []
  const used = new Map((estate.data?.frameworks ?? []).map((f) => [f.key, f]))
  const inUse = all.filter((j) => used.has(j.key))
  const rest = all.filter((j) => !used.has(j.key))
  const loading = (journeys.loading && !journeys.data) || (estate.loading && !estate.data)
  const error = journeys.error || estate.error

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={3} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Frameworks</Heading>
            <Text color="secondary">
              The rules and standards your AI systems answer to. Each one reads the same FairMind controls and evidence, so work done once counts everywhere it applies.
            </Text>
          </VStack>
          <Button variant="secondary" label="Open AI systems" href="/systems" />
        </HStack>

        {installer.failure && <Banner status="error" title="Install failed" description={installer.failure} />}

        {loading ? (
          <Rows n={5} />
        ) : error ? (
          <EmptyState title="Frameworks could not load" description={error} actions={<Button label="Try again" onClick={() => { journeys.reload(); estate.reload() }} />} />
        ) : (
          <>
            <section className="fm-card" aria-labelledby="fx-inuse">
              <VStack gap={3}>
                <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
                  <Heading level={2} id="fx-inuse">In use</Heading>
                  {(estate.data?.unconfirmed ?? 0) > 0 && (
                    <Text type="supporting">
                      {estate.data?.unconfirmed} system{estate.data?.unconfirmed === 1 ? ' has' : 's have'} not confirmed which frameworks apply · <Link href="/systems">Confirm</Link>
                    </Text>
                  )}
                </HStack>
                {inUse.length === 0 ? (
                  <EmptyState
                    title="No system has confirmed a framework yet"
                    description="Open an AI system and confirm the frameworks that apply to it. Each confirmed framework appears here with where every requirement stands."
                    actions={<Button variant="secondary" label="Open AI systems" href="/systems" />}
                  />
                ) : (
                  <>
                    <Legend />
                    <div className="fx-scroll">
                      <table className="fx-table">
                        <thead>
                          <tr>
                            <th scope="col">Framework</th>
                            <th scope="col">Kind</th>
                            <th scope="col">Systems</th>
                            <th scope="col">Where each tracked requirement stands</th>
                            <th scope="col">Needs work</th>
                          </tr>
                        </thead>
                        <tbody>
                          {inUse.map((r) => {
                            const f = used.get(r.key)!
                            // the same rule as the queue this number links to: a requirement nothing reaches shows in the bar as not tracked
                            const untracked = f.states.none ?? 0
                            const work = NEEDS_WORK.reduce((a, s) => a + (f.states[s as keyof typeof f.states] ?? 0), 0)
                            const failing = f.states.fails ?? 0
                            return (
                              <tr key={r.key}>
                                <td>
                                  <span className="fx-name">
                                    <span>
                                      <Link href={href(r.key)}>{r.name}</Link>
                                      <small>
                                        {f.tracked - untracked} of {r.active} requirements checked per system
                                      </small>
                                    </span>
                                  </span>
                                </td>
                                <td>{kind(r)}</td>
                                <td className="num">{f.systems}</td>
                                <td style={{ minWidth: 280 }}>
                                  <StateBar states={f.states} />
                                </td>
                                <td className="num">
                                  {work > 0 ? (
                                    <Link href={href(r.key)}>
                                      <b>{work}</b>
                                      {failing > 0 ? ` · ${failing} failing` : ''}
                                    </Link>
                                  ) : (
                                    'None'
                                  )}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </VStack>
            </section>

            {rest.length > 0 && (
              <section className="fm-card" aria-labelledby="fx-rest">
                <VStack gap={3}>
                  <VStack gap={1}>
                    <Heading level={2} id="fx-rest">Not applied yet</Heading>
                    <Text type="supporting">No system has confirmed these. Installed packs may already cover part of each.</Text>
                  </VStack>
                  <div className="fx-scroll">
                    <table className="fx-table">
                      <thead>
                        <tr>
                          <th scope="col">Framework</th>
                          <th scope="col">Kind</th>
                          <th scope="col">Covered by completed pack work</th>
                          <th scope="col"><span className="sr-only">Actions</span></th>
                        </tr>
                      </thead>
                      <tbody>
                        {rest.map((r) => (
                          <tr key={r.key}>
                            <td>
                              <span className="fx-name">
                                <span>
                                  <Link href={href(r.key)}>{r.name}</Link>
                                  <small>{r.active} requirements</small>
                                </span>
                              </span>
                            </td>
                            <td>{kind(r)}</td>
                            <td className="num">
                              {r.coveredInstalled} of {r.active}
                              {r.waiting > 0 && (
                                <>
                                  {' '}
                                  <Token size="sm" color="orange" label={`${r.waiting} waiting`} />
                                </>
                              )}
                            </td>
                            <td className="act">
                              {r.coveredAll > r.coveredInstalled && (
                                <Button
                                  label={installer.busy === r.key ? 'Installing' : 'Install its packs'}
                                  variant="secondary"
                                  size="sm"
                                  isDisabled={installer.busy !== null}
                                  onClick={() => installer.framework(r.key)}
                                />
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </VStack>
              </section>
            )}
          </>
        )}
      </VStack>
    </div>
  )
}

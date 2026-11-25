'use client'

import '@/astryx/pages/frameworks.css'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useEstateFrameworks, type EstateFrameworks } from '@/lib/api/hooks/useEstate'
import { useInstaller, useJourneys, type JourneySummary } from '@/lib/api/hooks/usePacks'
import { usePlan } from '@/lib/api/hooks/usePlan'
import { GROUP_LABEL, NEEDS_WORK, ReadinessBar, ReadinessLegend, groupOf, readinessCounts, type FrameworkGroup } from './parts'

const href = (key: string, tab?: string) => `/frameworks/${encodeURIComponent(key)}${tab ? `?tab=${tab}` : ''}`
const GROUPS: FrameworkGroup[] = ['law', 'cert', 'guidance', 'security']
type Followed = EstateFrameworks['frameworks'][number]

function Rows({ n }: { n: number }) {
  return (
    <VStack gap={2} aria-busy="true">
      {Array.from({ length: n }, (_, i) => (
        <Skeleton key={i} height={72} />
      ))}
    </VStack>
  )
}

/** Where the organisation's commitment to a framework comes from, in a person's words. */
function scopeLine(f: Followed): string {
  const systems = `${f.systems} system${f.systems === 1 ? '' : 's'} in scope`
  if (f.source === 'plan') {
    const inherited = f.inherited ?? 0
    const note = inherited === 0 ? '' : inherited === f.systems ? ' (none assessed yet)' : ` (${inherited} not assessed yet)`
    return `Chosen in your plan · ${systems}${note}`
  }
  return `Confirmed on ${f.confirmed ?? f.systems} system${(f.confirmed ?? f.systems) === 1 ? '' : 's'} · not in your plan`
}

export default function FrameworksPage() {
  const journeys = useJourneys()
  const estate = useEstateFrameworks()
  const plan = usePlan()
  const installer = useInstaller(() => journeys.reload())
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const all = useMemo(() => journeys.data ?? [], [journeys.data])
  const byKey = useMemo(() => new Map(all.map((j) => [j.key, j])), [all])
  const followed = (estate.data?.frameworks ?? []).filter((f) => byKey.has(f.key))
  // plan frameworks first, in the order chosen; then frameworks only systems confirmed
  const planKeys = estate.data?.plan ?? []
  followed.sort((a, b) => (planKeys.indexOf(a.key) + 1 || 999) - (planKeys.indexOf(b.key) + 1 || 999))
  const following = new Set(followed.map((f) => f.key))
  const suggested = (plan.data?.discovery.suggested ?? []).filter((s) => !following.has(s.key) && byKey.has(s.key))
  const q = query.trim().toLowerCase()
  const catalogue = all.filter((j) => !q || j.name.toLowerCase().includes(q) || j.key.toLowerCase().includes(q))

  const loading = (journeys.loading && !journeys.data) || (estate.loading && !estate.data)
  const error = journeys.error || estate.error

  async function setPlan(next: string[], key: string) {
    if (next.length === 0) {
      setFailure('The plan needs at least one framework. Follow another one before you stop following this.')
      return
    }
    setBusy(key)
    setFailure(null)
    try {
      await plan.answer('frameworks', next)
      estate.reload()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Could not change the frameworks you follow')
    } finally {
      setBusy(null)
    }
  }
  const follow = (key: string) => setPlan([...planKeys, key], key)
  const unfollow = (key: string) => setPlan(planKeys.filter((k) => k !== key), key)

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={3} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Frameworks</Heading>
            <Text color="secondary">What your organisation follows, and how close each one is to audit-ready.</Text>
          </VStack>
          <Button variant="primary" label="Add a framework" href="#fx-all" />
        </HStack>

        {(failure || installer.failure) && <Banner status="error" title={failure || 'Install failed'} description={failure ? undefined : installer.failure ?? undefined} isDismissable onDismiss={() => setFailure(null)} />}

        {loading ? (
          <Rows n={3} />
        ) : error ? (
          <EmptyState title="Frameworks could not load" description={error} actions={<Button label="Try again" onClick={() => { journeys.reload(); estate.reload() }} />} />
        ) : (
          <>
            <section className="fm-card" aria-labelledby="fx-follow">
              <VStack gap={4}>
                <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
                  <Heading level={2} id="fx-follow">You follow {followed.length || ''}</Heading>
                  <ReadinessLegend />
                </HStack>
                {followed.length === 0 ? (
                  <EmptyState
                    title="You do not follow a framework yet"
                    description="Pick the frameworks that apply to you below, or answer the plan's questions and it will suggest them. Every AI system you have not assessed yet is in scope of what you follow."
                    actions={<Button variant="secondary" label="Open the plan" href="/plan" />}
                  />
                ) : (
                  followed.map((f) => {
                    const j = byKey.get(f.key)!
                    const counts = readinessCounts(f.states)
                    const work = NEEDS_WORK.reduce((a, s) => a + (f.states[s as keyof typeof f.states] ?? 0), 0)
                    const packsToInstall = j.coveredAll > j.coveredInstalled
                    return (
                      <div key={f.key} className="fx-follow">
                        <VStack gap={1}>
                          <span className="fx-eyebrow">{GROUP_LABEL[groupOf(j)]}</span>
                          <Link href={href(f.key)} style={{ fontSize: 17, fontWeight: 600 }}>{j.name}</Link>
                          <Text type="supporting">{scopeLine(f)}</Text>
                        </VStack>
                        <ReadinessBar counts={counts} />
                        <VStack gap={2} hAlign="start">
                          <Text type="supporting">
                            {counts.attention > 0 ? `${counts.attention} need attention first` : work > 0 ? `${work} requirements still to do` : 'Nothing open'}
                          </Text>
                          <HStack gap={2} wrap="wrap">
                            <Button size="sm" variant="secondary" label="Open" href={href(f.key)} />
                            <Button size="sm" variant="secondary" label="Prepare audit pack" href={href(f.key, 'audit')} />
                            {packsToInstall && (
                              <Button size="sm" variant="ghost" label={installer.busy === f.key ? 'Installing' : 'Install its packs'} isDisabled={installer.busy !== null} onClick={() => installer.framework(f.key)} />
                            )}
                            {f.source === 'plan' && (
                              <Button size="sm" variant="ghost" label={busy === f.key ? 'Saving' : 'Stop following'} isDisabled={busy !== null} onClick={() => void unfollow(f.key)} />
                            )}
                            {f.source === 'system' && (
                              <Button size="sm" variant="ghost" label={busy === f.key ? 'Saving' : 'Add to plan'} isDisabled={busy !== null} onClick={() => void follow(f.key)} />
                            )}
                          </HStack>
                        </VStack>
                      </div>
                    )
                  })
                )}
                {(estate.data?.unconfirmed ?? 0) > 0 && followed.length > 0 && (
                  <Text type="supporting">
                    {estate.data?.unconfirmed} system{estate.data?.unconfirmed === 1 ? ' has' : 's have'} not been assessed
                    {planKeys.length > 0 ? `, so ${estate.data?.unconfirmed === 1 ? 'it counts' : 'they count'} towards every framework in your plan` : ' and follow no framework yet'}. <Link href="/systems">Assess them</Link> to confirm or exclude.
                  </Text>
                )}
              </VStack>
            </section>

            {suggested.length > 0 && (
              <section className="fm-card" aria-labelledby="fx-suggest">
                <VStack gap={3}>
                  <VStack gap={1}>
                    <Heading level={2} id="fx-suggest">Likely to apply to you</Heading>
                    <Text type="supporting">From your answers in the plan.</Text>
                  </VStack>
                  <div className="fx-suggest">
                    {suggested.map((s) => (
                      <div key={s.key} className="fm-card">
                        <VStack gap={2} hAlign="start">
                          <span className="fx-eyebrow">{GROUP_LABEL[groupOf(byKey.get(s.key)!)]}</span>
                          <Link href={href(s.key)} style={{ fontWeight: 600 }}>{s.name}</Link>
                          <Text type="supporting">{s.reason}</Text>
                          <Button size="sm" variant="secondary" label={busy === s.key ? 'Saving' : 'Follow'} isDisabled={busy !== null} onClick={() => void follow(s.key)} />
                        </VStack>
                      </div>
                    ))}
                  </div>
                </VStack>
              </section>
            )}

            <section aria-labelledby="fx-all-h" id="fx-all">
              <VStack gap={3}>
                <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
                  <Heading level={2} id="fx-all-h">All frameworks <Text type="supporting">{all.length}</Text></Heading>
                  <div style={{ width: 260 }}>
                    <TextInput label="Search frameworks" isLabelHidden placeholder="Search frameworks" value={query} onChange={setQuery} />
                  </div>
                </HStack>
                <div className="fx-groups">
                  {GROUPS.map((g) => {
                    const items = catalogue.filter((j) => groupOf(j) === g)
                    if (items.length === 0) return null
                    return (
                      <div key={g} className="fm-card">
                        <VStack gap={3}>
                          <span className="fx-eyebrow" id={`fx-g-${g}`}>{GROUP_LABEL[g]} · {items.length}</span>
                          <ul className="fx-grouplist" aria-labelledby={`fx-g-${g}`}>
                            {items.map((j: JourneySummary) => (
                              <li key={j.key}>
                                <Link href={href(j.key)}>{j.name}</Link>
                                {following.has(j.key) ? (
                                  <Token size="sm" label="Following" />
                                ) : (
                                  <Button size="sm" variant="ghost" label={busy === j.key ? 'Saving' : 'Follow'} isDisabled={busy !== null} onClick={() => void follow(j.key)} />
                                )}
                              </li>
                            ))}
                          </ul>
                        </VStack>
                      </div>
                    )
                  })}
                </div>
              </VStack>
            </section>
          </>
        )}
      </VStack>
    </div>
  )
}

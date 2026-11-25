'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { CheckboxList, CheckboxListItem } from '@astryxdesign/core/CheckboxList'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { sharePack } from '@/astryx/data/packs'
import { useEvidencePacks, type PackSummary } from '@/lib/api/hooks/useEvidencePacks'
import type { Readiness } from '../parts'

type Gap = { control: string; title: string }

/** A framework's audit pack: scope comes from the framework, gaps show before anything is shared. */
export function PrepareAudit({
  frameworkKey,
  name,
  systems,
  counts,
  attention,
  notAssessed,
}: {
  frameworkKey: string
  name: string
  systems: Array<{ id: string; name: string }>
  counts: Record<Readiness, number>
  attention: Gap[]
  notAssessed: number
}) {
  const router = useRouter()
  const { packs, create } = useEvidencePacks()
  const [title, setTitle] = useState(`${name} audit pack`)
  const [picked, setPicked] = useState<string[]>(() => systems.map((s) => s.id))
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [link, setLink] = useState<{ url: string; expiresAt: string } | null>(null)
  const mine = packs.filter((p) => p.frameworks.includes(frameworkKey))

  async function build(): Promise<PackSummary | null> {
    setBusy('build')
    setFailure(null)
    const res = await create({ title: title.trim(), frameworks: [frameworkKey], systemIds: picked })
    setBusy(null)
    if (res.success && res.data) return res.data
    setFailure(res.error || res.message || 'The pack could not be built')
    return null
  }

  async function previewNew() {
    const pack = await build()
    // same tab: a window opened after the build's await is treated as a popup and blocked
    if (pack) router.push(`/auditor-preview/${pack.id}`)
  }

  async function shareNew() {
    const pack = await build()
    if (!pack) return
    setBusy('share')
    const res = await sharePack(pack.id)
    setBusy(null)
    if (res.success && res.data) setLink({ url: `${window.location.origin}/verify/${pack.id}?t=${encodeURIComponent(res.data.token)}`, expiresAt: res.data.expiresAt })
    else setFailure(res.error || res.message || 'The pack was built but the link could not be made. Share it from Auditor packs.')
  }

  const canBuild = title.trim() !== '' && picked.length > 0 && busy === null

  return (
    <div className="fx-cols">
      <section className="fm-card" aria-labelledby="pa-what">
        <VStack gap={4}>
          <VStack gap={1}>
            <Heading level={2} id="pa-what">What the auditor sees</Heading>
            <Text type="supporting">A frozen, hashed copy of where {name} stands now, readable without a FairMind account.</Text>
          </VStack>
          <TextInput label="Title" value={title} onChange={setTitle} />
          {systems.length ? (
            <CheckboxList label={`Systems in scope (${picked.length} of ${systems.length})`} value={picked} onChange={setPicked}>
              {systems.map((s) => (
                <CheckboxListItem key={s.id} value={s.id} label={s.name} />
              ))}
            </CheckboxList>
          ) : (
            <Banner status="info" title="No system is in scope yet" description="Follow this framework from Frameworks, or confirm it on a system, before you build a pack." />
          )}
          <Text type="supporting">
            Included: where each requirement stands, every evidence record and release decision for these systems, approved policies, attestations with who and when, and the Statement of Applicability for controls you excluded.
          </Text>
          {failure && <Banner status="error" title={failure} />}
          {link && (
            <Banner
              status="success"
              title="Link made. Copy it now: it is shown once."
              description={
                <span style={{ wordBreak: 'break-all' }}>
                  {link.url} · works until {new Date(link.expiresAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                </span>
              }
            />
          )}
          <HStack gap={2} hAlign="end" wrap="wrap">
            <Button variant="secondary" label={busy === 'build' ? 'Building' : 'Preview as auditor'} isDisabled={!canBuild} onClick={() => void previewNew()} />
            <Button variant="primary" label={busy === 'share' ? 'Making the link' : 'Build and share a link'} isDisabled={!canBuild} onClick={() => void shareNew()} />
          </HStack>
        </VStack>
      </section>

      <VStack gap={4}>
        <section className="fm-card" aria-labelledby="pa-gaps">
          <VStack gap={3}>
            <Heading level={2} id="pa-gaps">Before you share</Heading>
            <Text type="supporting">The auditor sees these as open. Fix them first, or share as they are.</Text>
            <ul className="fx-grouplist">
              {counts.attention > 0 && (
                <li>
                  <span>
                    <b>{counts.attention} need attention</b>
                    <br />
                    <Text type="supporting">{attention.slice(0, 4).map((g) => g.control).join(', ')}{attention.length > 4 ? ' and more' : ''}</Text>
                  </span>
                  <Link href={`/frameworks/${encodeURIComponent(frameworkKey)}`}>Fix</Link>
                </li>
              )}
              {counts.notstarted > 0 && (
                <li>
                  <span><b>{counts.notstarted} not started</b></span>
                  <Link href={`/frameworks/${encodeURIComponent(frameworkKey)}?tab=all`}>Open</Link>
                </li>
              )}
              {notAssessed > 0 && (
                <li>
                  <span><b>{notAssessed} system{notAssessed === 1 ? '' : 's'} not assessed</b><br /><Text type="supporting">No tier or applicability confirmed</Text></span>
                  <Link href="/systems">Assess</Link>
                </li>
              )}
              {counts.attention + counts.notstarted + notAssessed === 0 && <li><span>Nothing open. The auditor sees every requirement met.</span></li>}
            </ul>
          </VStack>
        </section>
        <section className="fm-card" aria-labelledby="pa-packs">
          <VStack gap={3}>
            <Heading level={2} id="pa-packs">Packs for {name}</Heading>
            {mine.length === 0 ? (
              <Text type="supporting">None built yet.</Text>
            ) : (
              <ul className="fx-grouplist">
                {mine.slice(0, 6).map((p) => (
                  <li key={p.id}>
                    <span>
                      <b>{p.title}</b>
                      <br />
                      <Text type="supporting">
                        {new Date(p.createdAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} · {p.share.shared && !p.share.expired ? 'shared' : 'not shared'}
                      </Text>
                    </span>
                    <Link href={`/auditor-preview/${p.id}`}>Preview</Link>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/auditor-packs">All auditor packs</Link>
          </VStack>
        </section>
      </VStack>
    </div>
  )
}

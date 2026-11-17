'use client'

import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useMembers } from '@/astryx/data/settings'

const OUTSIDE = '__outside__'

/** Name the person accountable for the system: an org member, or someone not in FairMind. */
export function OwnerPanel({ orgId, current, onSubmit, onCancel }: { orgId?: string; current: string; onSubmit: (owner: string) => Promise<void>; onCancel: () => void }) {
  const { data: members } = useMembers(orgId)
  const active = members.filter((m) => m.status === 'active' && m.email)
  const [pick, setPick] = useState<string | null>(null)
  const [other, setOther] = useState(current)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isMember = active.some((m) => m.email === current)
  // Until a choice is made, the current owner shows as a member, or as someone outside FairMind.
  const choice = pick ?? (!current ? undefined : isMember ? current : OUTSIDE)
  const owner = (choice === OUTSIDE ? other : choice ?? '').trim()
  const tooLong = owner.length > 320
  const ready = owner.length > 0 && !tooLong && owner !== current

  const options = [
    ...active.map((m) => ({ value: m.email as string, label: m.name ? `${m.name}, ${m.email}` : (m.email as string) })),
    { value: OUTSIDE, label: 'Someone not in FairMind' },
  ]

  const submit = async () => {
    setBusy(true)
    setError(null)
    try {
      await onSubmit(owner)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not change the owner')
      setBusy(false)
    }
  }

  return (
    <VStack gap={4}>
      {error && <Banner status="error" title="Owner not changed" description={error} />}
      <Text type="body" color="secondary">The person accountable for this system. Auditors read this as the named owner.</Text>
      <Selector label="Owner" placeholder="Choose a person" options={options} value={choice} onChange={(v) => { setPick(v); if (v === OUTSIDE && isMember) setOther('') }} />
      {choice === OUTSIDE && (
        <TextInput label="Name or email" description={tooLong ? 'At most 320 characters.' : undefined} value={other} onChange={setOther} hasAutoFocus />
      )}
      <Text type="supporting" color="secondary">Recorded as a minor change on the change record. No check reopens.</Text>
      <HStack gap={2}>
        <Button label="Save owner" variant="primary" isDisabled={!ready || busy} isLoading={busy} onClick={() => void submit()} />
        <Button label="Cancel" variant="secondary" onClick={onCancel} />
      </HStack>
    </VStack>
  )
}

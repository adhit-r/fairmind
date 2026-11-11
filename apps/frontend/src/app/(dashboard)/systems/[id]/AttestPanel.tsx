'use client'

import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import type { AttestableCheck } from '@/lib/api/hooks/useSystemFile'

const PROMPT: Record<AttestableCheck, string> = {
  data_governance: 'Where the training and evaluation data came from, its lawful basis, and who owns it.',
  human_oversight: "Who reviews or can override the system's decisions, and when.",
  monitoring: 'How the system is watched in production and who is paged.',
}

/** A person states that a check is satisfied. It is recorded as a statement: it attests, it never proves. */
export function AttestPanel({ check, onSubmit, onCancel }: { check: AttestableCheck; onSubmit: (statement: string, reference?: string) => Promise<void>; onCancel: () => void }) {
  const [statement, setStatement] = useState('')
  const [reference, setReference] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ready = statement.trim().length >= 12

  const submit = async () => {
    setBusy(true)
    setError(null)
    try {
      await onSubmit(statement.trim(), reference.trim() || undefined)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not record the attestation')
      setBusy(false)
    }
  }

  return (
    <VStack gap={4}>
      {error && <Banner status="error" title="Not recorded" description={error} />}
      <TextArea label="Your statement" description={`${PROMPT[check]} At least 12 characters.`} value={statement} onChange={setStatement} rows={5} hasAutoFocus />
      <TextInput label="Reference" isOptional description="A link or document that backs the statement." value={reference} onChange={setReference} />
      <HStack gap={2}>
        <Button label="Record attestation" variant="primary" isDisabled={!ready || busy} isLoading={busy} onClick={() => void submit()} />
        <Button label="Cancel" variant="secondary" onClick={onCancel} />
      </HStack>
    </VStack>
  )
}

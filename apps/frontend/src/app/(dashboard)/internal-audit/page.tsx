'use client'

import '@/astryx/pages/internal-audit.css'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useOrg } from '@/context/OrgContext'
import { useMembers } from '@/astryx/data/settings'
import { createAudit, useAudits } from '@/lib/api/hooks/useInternalAudit'

export default function InternalAuditPage() {
  const router = useRouter()
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const { data, loading, error } = useAudits()
  const members = useMembers(orgId)
  const [title, setTitle] = useState('')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [fieldworkStart, setFieldworkStart] = useState('')
  const [fieldworkEnd, setFieldworkEnd] = useState('')
  const [lead, setLead] = useState('')
  const [saving, setSaving] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  const options = members.data.map((m) => ({ value: m.user_id, label: m.name || m.email || m.user_id }))
  const ready = !!orgId && !!title.trim() && !!periodStart && !!periodEnd && !!lead

  const create = async () => {
    if (!orgId) return
    setSaving(true)
    setProblem(null)
    try {
      const { id } = await createAudit(orgId, { title, periodStart, periodEnd, fieldworkStart, fieldworkEnd, leadAuditorId: lead })
      router.push(`/internal-audit/${id}`)
    } catch (e) {
      setProblem(e instanceof Error ? e.message : 'The audit was not created')
      setSaving(false)
    }
  }

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Internal audit</Heading>
          <Text color="secondary">Your audit plan, the checks on each area, and the auditors&apos; grades (ISO/IEC 42001 clause 9.2). Auditors decide; the assistant only gathers evidence.</Text>
        </VStack>

        {error ? (
          <Banner status="error" title="Audits could not load" description={error} />
        ) : loading ? (
          <Skeleton height={48} />
        ) : !data?.audits.length ? (
          <EmptyState title="No internal audit yet" description="Start one below, then upload your audit plan." />
        ) : (
          <ul className="ia-list">
            {data.audits.map((a) => (
              <li key={a.id}>
                <Link href={`/internal-audit/${a.id}`}>
                  <span>
                    <b>{a.title}</b>
                    <small> · evidence period {a.periodStart} to {a.periodEnd}</small>
                  </span>
                  <small>{a.status === 'issued' ? `Issued ${a.issuedAt?.slice(0, 10) ?? ''}` : a.status}</small>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <div className="ia-card">
          <VStack gap={3}>
            <Heading level={2}>Start an audit</Heading>
            {problem && <Banner status="error" title="Could not start the audit" description={problem} />}
            <div className="ia-form">
              <TextInput label="Title" value={title} onChange={setTitle} isRequired />
              <Selector label="Lead auditor" options={options} value={lead} onChange={(v) => setLead(String(v))} isRequired />
              <label className="ia-field">Evidence period starts<input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} /></label>
              <label className="ia-field">Evidence period ends<input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} /></label>
              <label className="ia-field">Fieldwork starts (optional)<input type="date" value={fieldworkStart} onChange={(e) => setFieldworkStart(e.target.value)} /></label>
              <label className="ia-field">Fieldwork ends (optional)<input type="date" value={fieldworkEnd} onChange={(e) => setFieldworkEnd(e.target.value)} /></label>
            </div>
            <div>
              <Button label="Create audit" variant="primary" isDisabled={!ready || saving} onClick={() => void create()} />
            </div>
          </VStack>
        </div>
      </VStack>
    </div>
  )
}

'use client'

import '@/astryx/pages/evidence.css'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { Table, pixel, proportional } from '@astryxdesign/core/Table'
import type { TableColumn } from '@astryxdesign/core/Table'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import { useEvidence, type Evidence } from '@/lib/api/hooks/useEvidence'
import { resolveEvidenceHubFeatureGates } from '@/lib/assurance/evidenceHubFeatureGates'
import {
  useEvidenceMappingReview,
  useEvidenceRuns,
  useAllFrameworkAssignmentControls,
  useFrameworkAssignments,
} from '@/lib/api/hooks/useGovernanceAssurance'
import { useSystemSeals } from '@/astryx/data/evidence'

import { EvidenceUploader } from './components/EvidenceUploader'
import { EvidenceDetailDrawer } from './components/EvidenceDetailDrawer'
import { EvaluationRunList } from './components/EvaluationRunList'
import { EvaluatorRegistrationCatalogSection } from '@/components/evaluations/EvaluatorRegistrationCatalogPanel'

const EVALUATOR_CATALOG_UI_ENABLED = process.env.NEXT_PUBLIC_ASSURANCE_V2_EVALUATOR_CATALOG_UI_ENABLED === 'true'
const EVIDENCE_HUB_FEATURE_GATES = resolveEvidenceHubFeatureGates({
  untrustedExternalEvidenceLinking:
    process.env.NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED,
})

interface Row extends Record<string, unknown> {
  id: string
  evidence: Evidence
  title: string
  type: string
  confidence: number
  tags: string[]
  folder: string
  links: number
  stale: boolean
  created: string
}

const day = (ts: string) => {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
const short = (hash: string) => (hash.length > 16 ? `${hash.slice(0, 8)} ${hash.slice(8, 16)}` : hash)

/** An old link to ?view=evaluations still opens the run list and the evaluator catalog. */
export default function EvidencePage() {
  return useSearchParams().get('view') === 'evaluations' ? <EvidenceEvaluations /> : <EvidenceList />
}

function EvidenceList() {
  const { selectedOrg, isLoading: orgLoading, error: orgError } = useOrg()
  const { systems, selectedSystem, setSelectedSystemId, loading: systemsLoading, error: systemsError, refreshSystems } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const hasSystem = selectedSystem.metadata?.source !== 'fallback' && Boolean(selectedSystem.id)
  const assignments = useFrameworkAssignments(selectedOrg?.id, selectedSystem.id)
  const assignmentIds = useMemo(
    () => assignments.assignments.filter((a) => a.systemId === selectedSystem.id).map((a) => a.id),
    [assignments.assignments, selectedSystem.id],
  )
  const assessmentState = useAllFrameworkAssignmentControls(selectedOrg?.id, assignmentIds)
  const canReview =
    selectedOrg?.role === 'admin' || selectedOrg?.role === 'owner' || selectedOrg?.permissions?.includes('model:write') === true
  const roleKnown = !orgLoading && !orgError && Boolean(selectedOrg)

  const { data, summary, loading, error, collectEvidence, updateEvidence, addLink, removeLink, refreshEvidence } = useEvidence(selectedSystem.id)
  const seal = useSystemSeals(hasSystem ? selectedSystem.id : undefined)

  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const [saved, setSaved] = useState<string | null>(null)
  const [selected, setSelected] = useState<Evidence | null>(null)

  useEffect(() => {
    setSearch('')
    setSelected(null)
    setSaved(null)
  }, [selectedSystem.id])

  const rows = useMemo<Row[]>(() => {
    const q = search.trim().toLowerCase()
    return data
      .filter((e) => !q || [e.title, e.type, e.folder, ...(e.tags ?? [])].join(' ').toLowerCase().includes(q))
      .map((e) => ({
        id: e.id,
        evidence: e,
        title: e.title || e.type,
        type: e.type,
        confidence: e.confidence,
        tags: e.tags ?? [],
        folder: e.folder,
        links: e.linkedEntityCount,
        stale: e.stale,
        created: e.timestamp,
      }))
  }, [data, search])

  const columns: TableColumn<Row>[] = [
    {
      key: 'title',
      header: 'Evidence',
      width: proportional(3),
      renderCell: (r) => (
        <VStack gap={0}>
          <Button label={r.title} variant="ghost" size="sm" onClick={() => setSelected(r.evidence)} />
          <Text color="secondary" size="sm" maxLines={1}>{r.type}</Text>
        </VStack>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      width: pixel(110),
      renderCell: (r) => <Text hasTabularNumbers>{Math.round(r.confidence * 100)}%</Text>,
    },
    {
      key: 'tags',
      header: 'Tags',
      width: proportional(2),
      renderCell: (r) =>
        r.tags.length === 0 ? (
          <Text color="secondary">None</Text>
        ) : (
          <div className="fm-ev-tags">
            {r.tags.slice(0, 3).map((t) => <Token key={t} size="sm" label={t} />)}
            {r.tags.length > 3 && <Text color="secondary" size="sm">+{r.tags.length - 3}</Text>}
          </div>
        ),
    },
    { key: 'folder', header: 'Folder', width: pixel(140), renderCell: (r) => <Text color="secondary" maxLines={1}>{r.folder || 'None'}</Text> },
    { key: 'links', header: 'Links', width: pixel(90), renderCell: (r) => <Text hasTabularNumbers>{r.links}</Text> },
    {
      key: 'stale',
      header: 'State',
      width: pixel(100),
      renderCell: (r) => (r.stale ? <Token size="sm" color="orange" label="Stale" /> : <Text color="secondary">Current</Text>),
    },
    { key: 'created', header: 'Created', width: pixel(120), renderCell: (r) => <Text color="secondary" hasTabularNumbers>{day(r.created)}</Text> },
  ]

  const handleCollect = async (params: Parameters<typeof collectEvidence>[0]) => {
    await collectEvidence(params)
    setSaved(`${params.title || params.type} added to ${selectedSystem.name}.`)
    void seal.reload()
  }

  const chain = seal.loading ? (
    <Skeleton height={20} width={160} />
  ) : seal.error ? (
    <Text color="secondary">Could not load the chain</Text>
  ) : seal.latest ? (
    <>
      <code>{short(seal.latest.chainHead)}</code>
      <Token size="sm" color={seal.latest.verification.status === 'intact' ? 'green' : 'red'} label={seal.latest.verification.status === 'intact' ? 'Chain intact' : 'Chain broken'} />
    </>
  ) : (
    <Text color="secondary">Not sealed yet, a release decision seals the evidence</Text>
  )

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Evidence</Heading>
            <Text color="secondary">
              {hasSystem ? `What backs the release decision for ${selectedSystem.name}.` : 'Evidence is collected per AI system.'}
            </Text>
          </VStack>
          <HStack gap={2} wrap="wrap">
            <Button label="Auditor packs" variant="secondary" href="/auditor-packs" />
            {hasSystem && canReview && <Button label="Add evidence" variant="primary" onClick={() => setAdding(true)} />}
          </HStack>
        </HStack>

        {!hasSystem ? (
          systemsLoading ? (
            <Skeleton height={120} />
          ) : systemsError ? (
            <EmptyState title="The AI systems could not load" description={String(systemsError)} actions={<Button label="Try again" onClick={() => void refreshSystems()} />} />
          ) : (
            <EmptyState title="No AI system registered yet" description="Register a system first, then add the evidence behind its release decision." actions={<Button label="Register a system" variant="primary" href="/onboard" />} />
          )
        ) : (
          <>
            <div style={{ maxWidth: 360 }}>
              <Selector
                label="AI system"
                value={selectedSystem.id}
                onChange={(v: string) => setSelectedSystemId(v)}
                options={real.map((s) => ({ value: s.id, label: s.name }))}
              />
            </div>

            <section className="fm-card" aria-label="Evidence chain">
              <dl className="fm-ev-facts">
                <div><dt>Evidence items</dt><dd>{summary.totalEvidence > 0 ? summary.totalEvidence : data.length}</dd></div>
                <div><dt>Chain</dt><dd>{chain}</dd></div>
                <div><dt>Last sealed</dt><dd>{seal.latest ? day(seal.latest.createdAt) : 'Never'}</dd></div>
                <div><dt>Stale items</dt><dd>{data.filter((e) => e.stale).length}</dd></div>
              </dl>
            </section>

            {saved && <Banner status="success" title={saved} isDismissable onDismiss={() => setSaved(null)} />}
            {summary.missingSignals.length > 0 && (
              <Banner status="warning" title="Evidence gaps reported" description={summary.missingSignals.join(', ')} />
            )}

            {loading ? (
              <VStack gap={2}>{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={36} />)}</VStack>
            ) : error ? (
              <EmptyState title="The evidence could not load" description={error.message} actions={<Button label="Try again" onClick={() => void refreshEvidence()} />} />
            ) : data.length === 0 ? (
              <EmptyState
                title="No evidence collected yet"
                description={canReview ? `Upload a file, write a narrative or record an attestation for ${selectedSystem.name}.` : `Nothing has been collected for ${selectedSystem.name}.`}
                actions={canReview ? <Button label="Add first evidence" variant="primary" onClick={() => setAdding(true)} /> : undefined}
              />
            ) : (
              <VStack gap={3}>
                <div className="fm-ev-search">
                  <TextInput label="Search evidence" isLabelHidden value={search} onChange={setSearch} placeholder="Search by title, type, folder or tag" />
                </div>
                {rows.length === 0 ? (
                  <EmptyState title="No matching evidence" description="Nothing matches the search." actions={<Button label="Clear search" onClick={() => setSearch('')} />} />
                ) : (
                  <Table<Row> data={rows} columns={columns} idKey="id" density="balanced" textOverflow="truncate" />
                )}
              </VStack>
            )}
          </>
        )}
      </VStack>

      <Dialog isOpen={adding} onOpenChange={setAdding} width={560}>
        <DialogHeader title="Add evidence" subtitle={`For ${selectedSystem.name}`} onOpenChange={setAdding} />
        <div style={{ padding: 16 }}>
          <EvidenceUploader
            systemId={selectedSystem.id}
            onCollect={handleCollect}
            onClose={() => setAdding(false)}
            externalUrlsEnabled={EVIDENCE_HUB_FEATURE_GATES.untrustedExternalEvidenceLinking}
          />
        </div>
      </Dialog>

      <EvidenceDetailDrawer
        evidence={selected?.systemId === selectedSystem.id ? selected : null}
        open={Boolean(selected) && selected?.systemId === selectedSystem.id}
        onClose={() => setSelected(null)}
        onUpdate={async (id, updates) => {
          const updated = await updateEvidence(id, updates)
          setSelected(updated)
          return updated
        }}
        onAddLink={async (evidenceId, entityType, entityId) => {
          const link = await addLink(evidenceId, entityType, entityId)
          setSelected((prev) => {
            if (!prev || prev.id !== evidenceId) return prev
            const links = [...prev.linkedEntities, link]
            return { ...prev, linkedEntities: links, linkedEntityCount: links.length, workflowState: 'linked' }
          })
          return link
        }}
        onRemoveLink={async (evidenceId, linkId) => {
          await removeLink(evidenceId, linkId)
          setSelected((prev) => {
            if (!prev || prev.id !== evidenceId) return prev
            const links = prev.linkedEntities.filter((l) => l.id !== linkId)
            return { ...prev, linkedEntities: links, linkedEntityCount: links.length, workflowState: links.length > 0 ? 'linked' : 'collected' }
          })
        }}
        controlOptions={assessmentState.controls}
        canEdit={roleKnown ? canReview : null}
        canAddLink={canReview && EVIDENCE_HUB_FEATURE_GATES.untrustedExternalEvidenceLinking}
      />
    </div>
  )
}

function EvidenceEvaluations() {
  const { selectedOrg, isLoading: orgLoading, error: orgError } = useOrg()
  const { selectedSystem } = useSystemContext()
  const orgId = selectedOrg?.id
  const assignments = useFrameworkAssignments(orgId, selectedSystem.id)
  const assignmentIds = useMemo(
    () => assignments.assignments.filter((a) => a.systemId === selectedSystem.id).map((a) => a.id),
    [assignments.assignments, selectedSystem.id],
  )
  const assessmentState = useAllFrameworkAssignmentControls(orgId, assignmentIds)
  const evaluationState = useEvidenceRuns(orgId, selectedSystem.id)
  const mappingReview = useEvidenceMappingReview(orgId)
  const canReview =
    selectedOrg?.role === 'admin' || selectedOrg?.role === 'owner' || selectedOrg?.permissions?.includes('model:write') === true
  const roleKnown = !orgLoading && !orgError && Boolean(selectedOrg)
  const canViewEvaluatorCatalog = selectedOrg?.permissions?.includes('evaluation:catalog:admin') === true

  return (
    <div className="fm-page">
      <VStack gap={4}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <Heading level={1}>Evaluation runs</Heading>
          <Button label="Back to evidence" variant="secondary" href="/evidence" />
        </HStack>
        {EVALUATOR_CATALOG_UI_ENABLED && canViewEvaluatorCatalog ? (
          <EvaluatorRegistrationCatalogSection
            organizationId={selectedOrg?.id}
            authorized={canViewEvaluatorCatalog}
          />
        ) : null}
        <EvaluationRunList
          runs={evaluationState.runs}
          controls={assessmentState.controls}
          loading={evaluationState.loading || assignments.loading || assessmentState.loading}
          error={evaluationState.error || assignments.error || assessmentState.error}
          canReview={roleKnown ? canReview : null}
          onReview={mappingReview.reviewMapping}
          onRefresh={async () => {
            await Promise.all([evaluationState.refresh(), assignments.refresh(), assessmentState.refresh()])
          }}
        />
      </VStack>
    </div>
  )
}

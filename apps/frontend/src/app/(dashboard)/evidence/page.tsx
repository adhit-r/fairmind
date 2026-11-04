'use client'

import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { IconX } from '@tabler/icons-react'
import Link from 'next/link'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { BTN, BTN_P, ErrorNote, LABEL, Loading, MUTED, Pill, cap } from '@/components/packs/parts'
import { useToast } from '@/hooks/use-toast'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import { cn } from '@/lib/utils'
import { useEvidence, type Evidence } from '@/lib/api/hooks/useEvidence'
import {
  useEvidenceMappingReview,
  useEvidenceRuns,
  useAllFrameworkAssignmentControls,
  useFrameworkAssignments,
} from '@/lib/api/hooks/useGovernanceAssurance'

import { EvidenceFolderTree } from './components/EvidenceFolderTree'
import { EvidenceTagFilter } from './components/EvidenceTagFilter'
import { EvidenceUploader } from './components/EvidenceUploader'
import { EvidenceDetailDrawer } from './components/EvidenceDetailDrawer'
import { EvaluationRunList } from './components/EvaluationRunList'
import { EvaluatorRegistrationCatalogSection } from '@/components/evaluations/EvaluatorRegistrationCatalogPanel'

const EVALUATOR_CATALOG_UI_ENABLED = process.env.NEXT_PUBLIC_ASSURANCE_V2_EVALUATOR_CATALOG_UI_ENABLED === 'true'

const VIEWS = [
  ['gaps', 'Evidence gaps'],
  ['evaluations', 'Evaluations'],
  ['artifacts', 'Artifacts'],
] as const

function formatDate(ts: string) {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function getArtifactKindLabel(kind: string) {
  switch (kind) {
    case 'file': return 'File'
    case 'url': return 'External URL'
    case 'attestation': return 'Attested'
    default: return 'Narrative'
  }
}

function EvidenceRow({ evidence, onClick }: { evidence: Evidence; onClick: () => void }) {
  const tags = evidence.tags ?? []
  const date = formatDate(evidence.timestamp)
  const links = evidence.linkedEntityCount
  return (
    <button
      type="button"
      onClick={onClick}
      className="grid w-full gap-2 border-t border-[var(--fm-line)] px-5 py-3.5 text-left first:border-t-0 hover:bg-[var(--fm-bg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--fm-ink)] sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-4"
    >
      <span className="min-w-0">
        <span className="block truncate text-[13.5px] font-semibold">{evidence.title || evidence.type}</span>
        <span className={cn('mt-0.5 block truncate text-[12px]', MUTED)}>
          {evidence.type} · {getArtifactKindLabel(evidence.artifactKind)}{date && ` · ${date}`}
        </span>
        {tags.length > 0 && (
          <span className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {tags.slice(0, 3).map((tag) => <Pill key={tag}>{tag}</Pill>)}
            {tags.length > 3 && <span className={cn('text-[11.5px]', MUTED)}>+{tags.length - 3}</span>}
          </span>
        )}
      </span>
      <span className="flex flex-wrap items-center gap-2 sm:justify-end">
        {evidence.stale && <Pill tone="warn">Stale</Pill>}
        <Pill>{links > 0 ? `${links} link${links === 1 ? '' : 's'}` : 'Not linked'}</Pill>
        <span className={cn('text-[12.5px] tabular-nums', MUTED)}>{Math.round(evidence.confidence * 100)}% confidence</span>
      </span>
    </button>
  )
}

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-[rgba(21,23,26,.06)] py-1 pl-3 pr-1.5 text-[12px] font-medium">
      {label}
      <button
        type="button"
        aria-label={`Remove filter ${label}`}
        onClick={onRemove}
        className="grid h-5 w-5 place-items-center rounded-full hover:bg-[rgba(21,23,26,.1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]"
      >
        <IconX className="h-3 w-3" aria-hidden />
      </button>
    </span>
  )
}

function Notice({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <section className="fm-card grid min-h-[300px] place-items-center p-9 text-center">
      <div className="max-w-md">
        <h2 className="m-0 text-[22px] font-semibold tracking-tight">{title}</h2>
        <p className={cn('mt-3 text-[14.5px] leading-[1.55]', MUTED)}>{children}</p>
        {action && <div className="mt-6 flex justify-center">{action}</div>}
      </div>
    </section>
  )
}

export default function EvidencePage() {
  const searchParams = useSearchParams()
  const requestedView = searchParams.get('view')
  const activeView: 'gaps' | 'evaluations' | 'artifacts' = requestedView === 'evaluations' || requestedView === 'artifacts'
    ? requestedView
    : 'gaps'
  const { selectedOrg, isLoading: orgLoading, error: orgError } = useOrg()
  const { selectedSystem, loading: systemsLoading, error: systemsError, refreshSystems } = useSystemContext()
  // The context holds a placeholder system until the org registers one; never treat it as real.
  const hasSystem = selectedSystem.metadata?.source !== 'fallback' && Boolean(selectedSystem.id)
  const orgId = selectedOrg?.id
  const assignments = useFrameworkAssignments(orgId, selectedSystem.id)
  const assignmentIds = useMemo(
    () => assignments.assignments
      .filter((assignment) => assignment.systemId === selectedSystem.id)
      .map((assignment) => assignment.id),
    [assignments.assignments, selectedSystem.id],
  )
  const assessmentState = useAllFrameworkAssignmentControls(orgId, assignmentIds)
  const evaluationState = useEvidenceRuns(orgId, selectedSystem.id)
  const mappingReview = useEvidenceMappingReview(orgId)
  const canReview = selectedOrg?.role === 'admin'
    || selectedOrg?.role === 'owner'
    || selectedOrg?.permissions?.includes('model:write') === true
  // A role is only known once the organisation has loaded; until then nobody is told they lack access.
  const roleKnown = !orgLoading && !orgError && Boolean(selectedOrg)
  const readOnly = roleKnown && !canReview
  const canViewEvaluatorCatalog = selectedOrg?.permissions?.includes('evaluation:catalog:admin') === true
  const {
    data,
    summary,
    loading,
    error,
    collectEvidence,
    updateEvidence,
    addLink,
    removeLink,
    refreshEvidence,
  } = useEvidence(selectedSystem.id)
  const { toast } = useToast()

  const [activeFolder, setActiveFolder] = useState<string | null>(null)
  const [activeTags, setActiveTags] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [uploaderOpen, setUploaderOpen] = useState(false)
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    setActiveFolder(null)
    setActiveTags([])
    setSearch('')
    setSelectedEvidence(null)
    setDrawerOpen(false)
  }, [orgId, selectedSystem.id])

  const scopedSelectedEvidence = selectedEvidence?.systemId === selectedSystem.id
    ? selectedEvidence
    : null

  const filteredData = useMemo(() => {
    let result = data
    if (activeFolder !== null) {
      if (activeFolder === '__uncategorized__') {
        result = result.filter((e) => !e.folder)
      } else {
        result = result.filter((e) => e.folder === activeFolder)
      }
    }
    if (activeTags.length > 0) {
      result = result.filter((e) =>
        activeTags.every((tag) => (e.tags ?? []).includes(tag))
      )
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      result = result.filter(
        (e) =>
          (e.title || e.type).toLowerCase().includes(q) ||
          e.type.toLowerCase().includes(q) ||
          (e.tags ?? []).some((t) => t.toLowerCase().includes(q))
      )
    }
    return result
  }, [data, activeFolder, activeTags, search])

  const staleCount = useMemo(() => data.filter((e) => e.stale).length, [data])
  const linkedCount = useMemo(() => data.filter((e) => e.linkedEntityCount > 0).length, [data])
  const highConfidenceCount = useMemo(() => data.filter((e) => e.confidence >= 0.8).length, [data])
  // The hook falls back to an empty summary when the summary call fails; a real one counts the artifacts.
  const summaryAvailable = summary.totalEvidence > 0

  const handleTagToggle = (tag: string) => {
    setActiveTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    )
  }

  const openDrawer = (evidence: Evidence) => {
    setSelectedEvidence(evidence)
    setDrawerOpen(true)
  }

  const handleCollect = async (params: Parameters<typeof collectEvidence>[0]) => {
    await collectEvidence(params)
    toast({
      title: 'Evidence saved',
      description: `${params.title || params.type} added to ${selectedSystem.name}.`,
    })
  }

  // Artifact-backed views (gaps, artifacts) only show results once there is something to count.
  const artifactGate = loading ? (
    <div role="status" className={cn('fm-card p-9 text-center text-[14px]', MUTED)}>
      Loading evidence for {selectedSystem.name}
    </div>
  ) : error ? (
    <ErrorNote message={`Could not load evidence. ${error.message}`} onRetry={() => void refreshEvidence()} />
  ) : data.length === 0 ? (
    <Notice
      title="No evidence collected yet"
      action={canReview ? (
        <button type="button" className={BTN_P} onClick={() => setUploaderOpen(true)}>
          Add first evidence
        </button>
      ) : undefined}
    >
      {canReview
        ? `Upload a file, link an external artifact, write a narrative or record an attestation for ${selectedSystem.name}. Gaps and coverage appear once the first artifact is saved.`
        : readOnly
          ? `Nothing has been collected for ${selectedSystem.name}. Your role cannot add artifacts; ask a governance editor to add the first one.`
          : `Nothing has been collected for ${selectedSystem.name}. ${orgLoading ? 'Checking whether you can add artifacts.' : 'Your access to add artifacts could not be confirmed.'}`}
    </Notice>
  ) : null

  return (
    <div data-testid="evidence-evaluations-surface" className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
            <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Evidence
          </div>
          <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Evidence &amp; Evaluations</h1>
          <p className="mt-2 max-w-[640px] text-[15px] text-[var(--fm-ink2)]">
            {hasSystem
              ? `Review evaluation provenance and control mappings, close evidence gaps and manage the artifacts behind ${selectedSystem.name}.`
              : 'Review evaluation provenance and control mappings, close evidence gaps and manage the artifacts behind each AI system.'}
          </p>
        </div>

        {hasSystem && (
          <div className="flex flex-wrap items-center gap-2.5">
            <Link href="/evidence/packs" className={BTN}>Inspection packs</Link>
            {canReview ? (
              <button type="button" className={BTN_P} onClick={() => setUploaderOpen(true)}>
                Add evidence
              </button>
            ) : readOnly ? (
              <span className={cn('text-[12.5px] font-medium', MUTED)}>Read-only evidence access</span>
            ) : null}
          </div>
        )}
      </div>

      {!hasSystem ? (
        systemsLoading ? (
          <Loading label="Loading AI systems" />
        ) : systemsError ? (
          <ErrorNote message={`Could not load AI systems. ${systemsError}`} onRetry={() => void refreshSystems()} />
        ) : (
          <Notice
            title="No AI system registered yet"
            action={<Link href="/onboard" className={BTN_P}>Register a system</Link>}
          >
            Evidence is collected per AI system. Register one first, then add the artifacts and evaluation runs that back its governance record.
          </Notice>
        )
      ) : (
        <>
          <nav aria-label="Evidence views" className="flex w-max max-w-full gap-1 overflow-x-auto rounded-full bg-[#ebebe8] p-1">
            {VIEWS.map(([view, label]) => (
              <Link
                key={view}
                href={`/evidence?view=${view}`}
                aria-current={activeView === view ? 'page' : undefined}
                className={cn(
                  'flex h-[34px] items-center whitespace-nowrap rounded-full px-4 text-[13px] font-semibold text-[var(--fm-ink2)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)]',
                  activeView === view && 'bg-white text-[var(--fm-ink)] shadow-[0_1px_2px_rgba(20,20,30,.08)]',
                )}
              >
                {label}
              </Link>
            ))}
          </nav>

          {activeView === 'gaps' ? (
            artifactGate ?? (
              <section className="fm-card" aria-label="Evidence gaps">
                <div className="p-5">
                  <h2 className={cn('m-0', LABEL)}>Coverage</h2>
                  <p className="mt-2 text-[15px]">
                    <b className="font-semibold tabular-nums">{linkedCount} of {data.length}</b>{' '}
                    {data.length === 1 ? 'artifact is' : 'artifacts are'} linked to a control, policy, incident or remediation task.
                  </p>
                  <div
                    role="progressbar"
                    aria-label="Artifacts linked to an entity"
                    aria-valuemin={0}
                    aria-valuemax={data.length}
                    aria-valuenow={linkedCount}
                    className="mt-3 h-1.5 overflow-hidden rounded-full bg-[rgba(21,23,26,.08)]"
                  >
                    <div className="h-full rounded-full bg-[var(--fm-ink)]" style={{ width: `${Math.round((linkedCount / data.length) * 100)}%` }} />
                  </div>
                  <p className={cn('mt-3 text-[12.5px]', MUTED)}>
                    {summaryAvailable && summary.recommendedNextStep ? `${summary.recommendedNextStep} ` : ''}
                    This counts collected artifacts and links only. Control support still requires reviewer decisions.
                  </p>
                </div>

                {!summaryAvailable ? (
                  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--fm-line)] px-5 py-4">
                    <p className={cn('m-0 text-[13px]', MUTED)}>The gap summary could not be loaded, so gaps are not shown.</p>
                    <button type="button" className={cn(BTN, 'h-8 px-3.5 text-[12.5px]')} onClick={() => void refreshEvidence()}>
                      Try again
                    </button>
                  </div>
                ) : summary.missingSignals.length > 0 ? (
                  <>
                    <div className="flex items-center justify-between gap-3 border-t border-[var(--fm-line)] px-5 pb-1 pt-4">
                      <h2 className={cn('m-0', LABEL)}>Gaps</h2>
                      <Pill tone="you">{summary.missingSignals.length} open</Pill>
                    </div>
                    <ul className="m-0 list-none p-0">
                      {summary.missingSignals.map((signal) => (
                        <li key={signal} className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--fm-line)] px-5 py-3.5 first:border-t-0">
                          <span className="min-w-0 text-[13.5px] font-medium">{cap(signal)}</span>
                          <Link
                            href={{
                              pathname: '/remediation',
                              query: {
                                gap: signal,
                                systemId: selectedSystem.id,
                                title: `Evidence gap: ${signal}`,
                                priority: 'high',
                                source: 'evidence_gap',
                              },
                            }}
                            className={cn(BTN, 'h-8 px-3.5 text-[12.5px]')}
                          >
                            Create remediation
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <div className="flex flex-wrap items-center gap-3 border-t border-[var(--fm-line)] px-5 py-4">
                    <Pill tone="done">No gaps reported</Pill>
                    <p className={cn('m-0 min-w-0 flex-1 text-[13px]', MUTED)}>
                      Across {data.length} {data.length === 1 ? 'artifact' : 'artifacts'}. This reflects the current evidence summary, not a certification or compliance decision.
                    </p>
                  </div>
                )}
              </section>
            )
          ) : null}

          {activeView === 'evaluations' ? (
            <div className="grid gap-4">
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
            </div>
          ) : null}

          {activeView === 'artifacts' ? (
            artifactGate ?? (
              <div className="grid items-start gap-4 lg:grid-cols-[208px_minmax(0,1fr)]">
                <aside aria-label="Artifact filters" className="fm-card hidden content-start gap-5 p-4 lg:grid">
                  <EvidenceFolderTree
                    evidence={data}
                    activeFolder={activeFolder}
                    onFolderChange={setActiveFolder}
                  />
                  <EvidenceTagFilter
                    evidence={data}
                    activeTags={activeTags}
                    onTagToggle={handleTagToggle}
                    onClearTags={() => setActiveTags([])}
                  />
                </aside>

                <section className="fm-card min-w-0" aria-label="Artifacts">
                  <div className="flex items-center gap-2.5 p-4 pb-3">
                    <input
                      type="search"
                      aria-label="Search evidence by title, type or tag"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="h-9 min-w-0 flex-1 rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]"
                      placeholder="Search by title, type or tag"
                    />
                    <button type="button" className={cn(BTN, 'h-9 px-4 text-[12.5px]')} onClick={() => void refreshEvidence()} disabled={loading}>
                      Refresh
                    </button>
                  </div>

                  <p className={cn('m-0 px-4 pb-3 text-[12.5px] tabular-nums', MUTED)}>
                    {data.length} {data.length === 1 ? 'artifact' : 'artifacts'} · {linkedCount} linked · {highConfidenceCount} high confidence · {staleCount} potentially stale
                  </p>

                  {(activeTags.length > 0 || activeFolder !== null || search) && (
                    <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
                      <span className={LABEL}>Filters</span>
                      {activeFolder !== null && (
                        <Chip
                          label={`Folder: ${activeFolder === '__uncategorized__' ? 'Uncategorized' : activeFolder}`}
                          onRemove={() => setActiveFolder(null)}
                        />
                      )}
                      {activeTags.map((tag) => (
                        <Chip key={tag} label={`#${tag}`} onRemove={() => handleTagToggle(tag)} />
                      ))}
                      {search && <Chip label={`Search: ${search}`} onRemove={() => setSearch('')} />}
                    </div>
                  )}

                  {filteredData.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 border-t border-[var(--fm-line)] px-5 py-10 text-center">
                      <p className={cn('m-0 text-[13.5px]', MUTED)}>No evidence matches your filters.</p>
                      <button
                        type="button"
                        className={cn(BTN, 'h-8 px-3.5 text-[12.5px]')}
                        onClick={() => { setActiveFolder(null); setActiveTags([]); setSearch('') }}
                      >
                        Clear filters
                      </button>
                    </div>
                  ) : (
                    <div className="border-t border-[var(--fm-line)]">
                      {data.length !== filteredData.length && (
                        <p className={cn('m-0 border-b border-[var(--fm-line)] px-5 py-2 text-[12px]', MUTED)}>
                          Showing {filteredData.length} of {data.length}
                        </p>
                      )}
                      {filteredData.map((evidence) => (
                        <EvidenceRow key={evidence.id} evidence={evidence} onClick={() => openDrawer(evidence)} />
                      ))}
                    </div>
                  )}
                </section>
              </div>
            )
          ) : null}
        </>
      )}

      {/* Add evidence dialog */}
      <Dialog open={uploaderOpen} onOpenChange={setUploaderOpen}>
        <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-semibold">Add evidence</DialogTitle>
            <DialogDescription>
              Add a scoped evidence artifact for {selectedSystem.name}.
            </DialogDescription>
          </DialogHeader>
          <EvidenceUploader
            systemId={selectedSystem.id}
            onCollect={handleCollect}
            onClose={() => setUploaderOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Evidence detail drawer */}
      <EvidenceDetailDrawer
        evidence={scopedSelectedEvidence}
        open={drawerOpen && Boolean(scopedSelectedEvidence)}
        onClose={() => { setDrawerOpen(false); setSelectedEvidence(null) }}
        onUpdate={async (id, updates) => {
          const updated = await updateEvidence(id, updates)
          setSelectedEvidence(updated)
          return updated
        }}
        onAddLink={async (evidenceId, entityType, entityId) => {
          const link = await addLink(evidenceId, entityType, entityId)
          // Refresh selected evidence to show new link
          setSelectedEvidence((prev) => {
            if (!prev || prev.id !== evidenceId) return prev
            const newLinks = [...prev.linkedEntities, link]
            return { ...prev, linkedEntities: newLinks, linkedEntityCount: newLinks.length, workflowState: 'linked' }
          })
          return link
        }}
        onRemoveLink={async (evidenceId, linkId) => {
          await removeLink(evidenceId, linkId)
          setSelectedEvidence((prev) => {
            if (!prev || prev.id !== evidenceId) return prev
            const newLinks = prev.linkedEntities.filter((l) => l.id !== linkId)
            return { ...prev, linkedEntities: newLinks, linkedEntityCount: newLinks.length, workflowState: newLinks.length > 0 ? 'linked' : 'collected' }
          })
        }}
        controlOptions={assessmentState.controls}
        canEdit={roleKnown ? canReview : null}
      />
    </div>
  )
}

'use client'

import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCircleCheck,
  IconFileText,
  IconLoader2,
  IconPlus,
  IconRouteAltLeft,
  IconSearch,
  IconShieldCheck,
  IconShieldOff,
  IconX,
} from '@tabler/icons-react'
import Link from 'next/link'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
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

import { EvidenceFolderTree } from './components/EvidenceFolderTree'
import { EvidenceTagFilter } from './components/EvidenceTagFilter'
import { EvidenceUploader } from './components/EvidenceUploader'
import { EvidenceDetailDrawer } from './components/EvidenceDetailDrawer'
import { EvaluationRunList } from './components/EvaluationRunList'
import { EvaluatorRegistrationCatalogSection } from '@/components/evaluations/EvaluatorRegistrationCatalogPanel'

const EVALUATOR_CATALOG_UI_ENABLED = process.env.NEXT_PUBLIC_ASSURANCE_V2_EVALUATOR_CATALOG_UI_ENABLED === 'true'
const EVIDENCE_HUB_FEATURE_GATES = resolveEvidenceHubFeatureGates({
  untrustedExternalEvidenceLinking:
    process.env.NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED,
})

function formatDate(ts: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString()
}

function getArtifactKindLabel(kind: string) {
  switch (kind) {
    case 'file': return 'File'
    case 'url': return 'External URL'
    case 'attestation': return 'Attested'
    default: return 'Narrative'
  }
}

function EvidenceCard({
  evidence,
  onClick,
}: {
  evidence: Evidence
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full rounded-xl border-2 border-black bg-white p-4 text-left shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all hover:shadow-[5px_5px_0px_0px_rgba(0,0,0,1)] hover:-translate-x-0.5 hover:-translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge className="border-2 border-black bg-black px-2 py-0.5 text-[10px] font-black uppercase text-white">
              {evidence.type}
            </Badge>
            {evidence.stale && (
              <Badge className="border-2 border-amber-400 bg-amber-50 px-2 py-0.5 text-[10px] font-black uppercase text-amber-800">
                <IconAlertTriangle className="mr-1 h-2.5 w-2.5" />
                Stale
              </Badge>
            )}
            {evidence.linkedEntityCount > 0 && (
              <Badge className="border-2 border-emerald-500 bg-emerald-50 px-2 py-0.5 text-[10px] font-black uppercase text-emerald-800">
                <IconCircleCheck className="mr-1 h-2.5 w-2.5" />
                {evidence.linkedEntityCount} link{evidence.linkedEntityCount !== 1 ? 's' : ''}
              </Badge>
            )}
            <Badge className="border-2 border-amber-700 bg-amber-50 px-2 py-0.5 text-[10px] font-black uppercase text-amber-900">
              Trust unclassified
            </Badge>
          </div>

          <p className="truncate text-sm font-bold">
            {evidence.title || evidence.type}
          </p>

          <div className="flex flex-wrap items-center gap-1.5">
            {(evidence.tags ?? []).slice(0, 3).map((tag) => (
              <Badge
                key={tag}
                variant="outline"
                className="border border-black/30 bg-white px-1.5 py-0 text-[10px] font-bold"
              >
                {tag}
              </Badge>
            ))}
            {(evidence.tags ?? []).length > 3 && (
              <span className="text-[10px] text-muted-foreground">
                +{evidence.tags.length - 3}
              </span>
            )}
          </div>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-[10px] font-bold uppercase text-muted-foreground">
            {getArtifactKindLabel(evidence.artifactKind)}
          </p>
          <p className="mt-0.5 text-sm font-black">{Math.round(evidence.confidence * 100)}%</p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">{formatDate(evidence.timestamp)}</p>
        </div>
      </div>
    </button>
  )
}

export default function EvidencePage() {
  const searchParams = useSearchParams()
  const requestedView = searchParams.get('view')
  const activeView: 'gaps' | 'evaluations' | 'artifacts' = requestedView === 'evaluations' || requestedView === 'artifacts'
    ? requestedView
    : 'gaps'
  const { selectedOrg } = useOrg()
  const { selectedSystem } = useSystemContext()
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
  const canViewEvaluatorCatalog = selectedOrg?.permissions?.includes('evaluation:catalog:admin') === true
  const {
    data,
    summary,
    loading,
    collecting,
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

  const completeness = useMemo(() => {
    const totalRequired = summary.linkedEvidence + summary.missingSignals.length
    const linked = summary.linkedEvidence
    const gaps = summary.missingSignals.length
    const gate: 'green' | 'yellow' | 'red' = gaps === 0 ? 'green' : gaps > 2 ? 'red' : 'yellow'
    return { totalRequired, linked, gaps, gate }
  }, [summary])

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

  return (
    <div data-testid="evidence-evaluations-surface" className="flex min-h-0 flex-col gap-6">
      {/* Header */}
      <Card className="rounded-none border-4 border-[#0F1412] bg-[#FCFDF8] p-6 shadow-[8px_8px_0px_0px_#0F1412]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="rounded-none border-2 border-[#0F1412] bg-[#0B7659] px-3 py-1 font-black uppercase text-white">
                Assurance evidence
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-black uppercase">
                {selectedSystem.name}
              </Badge>
            </div>
            <h1 className="text-3xl font-black uppercase tracking-tight">
              Evidence &amp; Evaluations
            </h1>
            <p className="max-w-2xl text-sm text-muted-foreground">
              Review evaluation provenance and control mappings, resolve evidence gaps, and manage artifacts for {selectedSystem.name}.
            </p>
          </div>

          {canReview ? (
            <Button
              className="rounded-none border-2 border-black font-black uppercase shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
              onClick={() => setUploaderOpen(true)}
            >
              <IconPlus className="mr-2 h-4 w-4" />
              Add evidence
            </Button>
          ) : (
            <Badge variant="outline" className="rounded-none border-2 border-[#0F1412] bg-[#F3F5F0] px-3 py-2 font-black uppercase">
              Read-only evidence access
            </Badge>
          )}
        </div>
      </Card>

      <nav aria-label="Evidence views" className="grid border-2 border-[#0F1412] bg-[#FCFDF8] sm:grid-cols-3">
        {([
          ['gaps', 'Evidence gaps'],
          ['evaluations', 'Evaluations'],
          ['artifacts', 'Artifacts'],
        ] as const).map(([view, label]) => (
          <Link
            key={view}
            href={`/evidence?view=${view}`}
            aria-current={activeView === view ? 'page' : undefined}
            className={`min-h-12 border-b-2 border-[#0F1412] px-4 py-3 text-center text-sm font-black uppercase outline-none last:border-b-0 hover:bg-[#DDF4EA] focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-inset sm:border-b-0 sm:border-r-2 sm:last:border-r-0 ${activeView === view ? 'bg-[#0F1412] text-[#FCFDF8] hover:bg-[#0F1412]' : ''}`}
          >
            {label}
          </Link>
        ))}
      </nav>

      {/* Stats row */}
      {activeView === 'artifacts' ? (
      <div className="grid gap-4 sm:grid-cols-4">
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Total artifacts</p>
          <p className="mt-1 text-3xl font-black">{data.length}</p>
        </Card>
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Linked to entities</p>
          <p className="mt-1 text-3xl font-black text-emerald-700">{linkedCount}</p>
        </Card>
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">High confidence</p>
          <p className="mt-1 text-3xl font-black">{highConfidenceCount}</p>
        </Card>
        <Card className={`border-2 border-black p-4 shadow-brutal ${staleCount > 0 ? 'bg-amber-50' : ''}`}>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Potentially stale</p>
          <p className={`mt-1 text-3xl font-black ${staleCount > 0 ? 'text-amber-700' : ''}`}>{staleCount}</p>
        </Card>
      </div>
      ) : null}

      {/* Artifact coverage summary */}
      {activeView === 'gaps' ? (
      <Card className={`border-4 p-5 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] ${
        completeness.gate === 'green' ? 'border-emerald-600 bg-emerald-50' :
        completeness.gate === 'yellow' ? 'border-amber-500 bg-amber-50' :
        'border-red-600 bg-red-50'
      }`}>
        <div className="flex items-center gap-3">
          {completeness.gate === 'green' ? (
            <IconShieldCheck className="h-6 w-6 text-emerald-700" />
          ) : completeness.gate === 'yellow' ? (
            <IconAlertTriangle className="h-6 w-6 text-amber-700" />
          ) : (
            <IconShieldOff className="h-6 w-6 text-red-700" />
          )}
          <div className="flex-1">
            <p className="font-black uppercase">
              {completeness.gate === 'green' ? 'Artifact coverage recorded' :
               completeness.gate === 'yellow' ? 'Artifact coverage gaps identified' :
               'Multiple artifact coverage gaps identified'}
            </p>
            <p className="text-xs text-muted-foreground">
              This summary counts collected artifacts and entity links only. Control support still requires reviewer decisions.
            </p>
          </div>
          {completeness.totalRequired > 0 && (
            <div className="min-w-[120px] space-y-1">
              <div className="flex justify-between text-[10px] font-bold uppercase text-muted-foreground">
                <span>Artifact links</span>
                <span>{Math.round((completeness.linked / completeness.totalRequired) * 100)}%</span>
              </div>
              <Progress value={Math.round((completeness.linked / completeness.totalRequired) * 100)} className="h-2 border border-black" />
            </div>
          )}
        </div>
      </Card>
      ) : null}

      {/* Evidence gaps */}
      {activeView === 'gaps' && summary.missingSignals.length > 0 && (
        <Card className="border-4 border-black p-5 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
          <div className="mb-3 flex items-center gap-2">
            <IconX className="h-5 w-5 text-red-600" />
            <h2 className="font-black uppercase">Artifact coverage gaps</h2>
            <Badge className="border-2 border-red-600 bg-red-100 px-2 font-black uppercase text-red-800">
              {summary.missingSignals.length}
            </Badge>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {summary.missingSignals.map((signal) => (
              <div key={signal} className="flex flex-col gap-2 rounded-xl border-2 border-black bg-red-50 p-3 shadow-[3px_3px_0px_0px_#000]">
                <p className="text-sm font-bold uppercase">{signal}</p>
                <Button asChild size="sm" variant="default" className="mt-auto border-2 border-black font-black uppercase">
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
                  >
                    <IconRouteAltLeft className="mr-1.5 h-3.5 w-3.5" />
                    Create Remediation
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeView === 'gaps' && !loading && !error && summary.missingSignals.length === 0 ? (
        <Card className="rounded-none border-2 border-[#0F1412] bg-[#DDF4EA] p-8 text-center shadow-[5px_5px_0_0_#0F1412]">
          <IconShieldCheck className="mx-auto h-8 w-8 text-[#0B7659]" />
          <h2 className="mt-3 text-lg font-black uppercase">No evidence gaps reported</h2>
          <p className="mt-2 text-sm text-[#59615D]">This reflects the current evidence summary, not a certification or compliance decision.</p>
        </Card>
      ) : null}

      {activeView === 'evaluations' ? (
        <div className="space-y-5">
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
            canReview={canReview}
            onReview={mappingReview.reviewMapping}
            onRefresh={async () => {
              await Promise.all([evaluationState.refresh(), assignments.refresh(), assessmentState.refresh()])
            }}
          />
        </div>
      ) : null}

      {/* Main content: sidebar + list */}
      {activeView === 'artifacts' ? (
      <div className="flex min-h-0 gap-5">
        {/* Sidebar */}
        {data.length > 0 && (
          <div className="hidden w-52 shrink-0 space-y-5 lg:block">
            <EvidenceFolderTree
              evidence={data}
              activeFolder={activeFolder}
              onFolderChange={setActiveFolder}
            />
            <div className="border-t-2 border-black/10 pt-4">
              <EvidenceTagFilter
                evidence={data}
                activeTags={activeTags}
                onTagToggle={handleTagToggle}
                onClearTags={() => setActiveTags([])}
              />
            </div>
          </div>
        )}

        {/* Evidence list */}
        <div className="min-w-0 flex-1 space-y-4">
          {/* Search + filters */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="border-2 border-black pl-9 font-medium"
                placeholder="Search evidence by title, type, or tag..."
              />
            </div>
            <Button
              variant="neutral"
              className="border-2 border-black font-bold"
              onClick={() => void refreshEvidence()}
              disabled={loading}
            >
              <IconArrowRight className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>

          {/* Active filter chips */}
          {(activeTags.length > 0 || activeFolder !== null || search) && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase text-muted-foreground">Filters:</span>
              {activeFolder !== null && (
                <Badge className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                  Folder: {activeFolder === '__uncategorized__' ? 'Uncategorized' : activeFolder}
                  <button type="button" onClick={() => setActiveFolder(null)} className="ml-1.5">
                    <IconX className="h-2.5 w-2.5" />
                  </button>
                </Badge>
              )}
              {activeTags.map((tag) => (
                <Badge key={tag} className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                  #{tag}
                  <button type="button" onClick={() => handleTagToggle(tag)} className="ml-1.5">
                    <IconX className="h-2.5 w-2.5" />
                  </button>
                </Badge>
              ))}
              {search && (
                <Badge className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-bold text-white">
                  Search: {search}
                  <button type="button" onClick={() => setSearch('')} className="ml-1.5">
                    <IconX className="h-2.5 w-2.5" />
                  </button>
                </Badge>
              )}
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-16 text-center">
              <IconLoader2 className="h-8 w-8 animate-spin" />
              <p className="font-bold">Loading evidence for {selectedSystem.name}</p>
            </div>
          )}

          {!loading && error && (
            <div className="rounded-3xl border-2 border-red-600 bg-red-50 p-6">
              <div className="flex items-start gap-3">
                <IconAlertTriangle className="mt-0.5 h-5 w-5 text-red-700" />
                <div className="space-y-2">
                  <p className="font-bold text-red-800">Could not load evidence</p>
                  <p className="text-sm text-red-700">{error.message}</p>
                  <Button
                    variant="neutral"
                    className="border-2 border-red-700 font-bold text-red-700"
                    onClick={() => void refreshEvidence()}
                  >
                    Retry
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-16 text-center">
              <IconFileText className="mx-auto h-12 w-12 opacity-50" />
              <h3 className="mt-4 text-xl font-black">No evidence yet</h3>
              <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
                Start by uploading a file, recording an attestation, or writing a narrative for {selectedSystem.name}.
              </p>
              <Button
                className="mt-5 border-2 border-black font-black uppercase"
                onClick={() => setUploaderOpen(true)}
                disabled={!canReview}
              >
                <IconPlus className="mr-2 h-4 w-4" />
                Add first evidence
              </Button>
            </div>
          )}

          {!loading && !error && data.length > 0 && filteredData.length === 0 && (
            <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-10 text-center">
              <p className="font-bold text-muted-foreground">No evidence matches your filters.</p>
              <Button
                variant="neutral"
                size="sm"
                className="mt-3 border-2 border-black font-bold"
                onClick={() => { setActiveFolder(null); setActiveTags([]); setSearch('') }}
              >
                Clear filters
              </Button>
            </div>
          )}

          {!loading && !error && filteredData.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase text-muted-foreground">
                {filteredData.length} artifact{filteredData.length !== 1 ? 's' : ''}
                {data.length !== filteredData.length && ` (${data.length} total)`}
              </p>
              {filteredData.map((evidence) => (
                <EvidenceCard
                  key={evidence.id}
                  evidence={evidence}
                  onClick={() => openDrawer(evidence)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
      ) : null}

      {/* Add evidence dialog */}
      <Dialog open={uploaderOpen} onOpenChange={setUploaderOpen}>
        <DialogContent className="max-w-lg border-4 border-black">
          <DialogHeader>
            <DialogTitle className="font-black uppercase">Add evidence</DialogTitle>
            <DialogDescription>
              Add a scoped evidence artifact for {selectedSystem.name}.
            </DialogDescription>
          </DialogHeader>
          <EvidenceUploader
            systemId={selectedSystem.id}
            onCollect={handleCollect}
            onClose={() => setUploaderOpen(false)}
            externalUrlsEnabled={EVIDENCE_HUB_FEATURE_GATES.untrustedExternalEvidenceLinking}
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
        canEdit={canReview}
        canAddLink={canReview && EVIDENCE_HUB_FEATURE_GATES.untrustedExternalEvidenceLinking}
      />
    </div>
  )
}

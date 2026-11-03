'use client'

import { useEffect, useMemo, useState } from 'react'
import { IconRefresh } from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useOrg } from '@/context/OrgContext'
import {
  useFrameworkVersions,
  useGovernanceAssurance,
  type ControlAssessment,
} from '@/lib/api/hooks/useGovernanceAssurance'

import { ControlAssessmentTable } from './components/ControlAssessmentTable'
import { FrameworkCatalog } from './components/FrameworkCatalog'
import type { WorkbenchControl } from './components/ControlTracePanel'

function ReadinessStrip({
  frameworkName,
  versionLabel,
  readiness,
  loading,
}: {
  frameworkName: string
  versionLabel: string
  readiness: {
    applicable: number
    accepted: number
    readyForReview: number
    missingEvidence: number
    blockingFindings: number
  } | null
  loading: boolean
}) {
  const measures = [
    ['Applicable', readiness?.applicable],
    ['Accepted', readiness?.accepted],
    ['Ready for review', readiness?.readyForReview],
    ['Missing evidence', readiness?.missingEvidence],
    ['Rejected assessments', readiness?.blockingFindings],
  ] as const

  return (
    <section aria-labelledby="readiness-heading" className="border border-[var(--fm-line)] bg-white">
      <div className="flex flex-col gap-1 border-b border-[var(--fm-line)] bg-[oklch(0.60_0.13_163)] px-4 py-3 text-[var(--fm-ink)] sm:flex-row sm:items-center sm:justify-between">
        <h2 id="readiness-heading" className="text-base font-semibold tracking-tight">
          {frameworkName} readiness
        </h2>
        <p className="text-xs font-semibold uppercase tracking-[0.12em]">Version {versionLabel}</p>
      </div>
      <dl
        aria-label={loading ? 'Loading readiness summary' : undefined}
        className="grid grid-cols-2 divide-x-2 divide-y-2 divide-[var(--fm-line)] sm:grid-cols-5 sm:divide-y-0"
      >
        {measures.map(([label, value]) => (
          <div key={label} className="min-h-[76px] px-3 py-3 first:col-span-2 sm:first:col-span-1">
            <dt className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">{label}</dt>
            <dd className="mt-1 text-xl font-semibold text-[var(--fm-ink)]">
              {loading ? <Skeleton className="h-7 w-10" /> : value ?? 'Unknown'}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function WorkbenchLoading() {
  return (
    <div aria-label="Loading framework catalog" className="space-y-4 p-5 fm-card">
      <Skeleton className="h-5 w-48" />
      <Skeleton className="h-12 w-full" />
      <div className="grid gap-3 sm:grid-cols-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    </div>
  )
}

export default function ComplianceDashboardPage() {
  const { selectedOrg } = useOrg()
  const { selectedSystem } = useSystemContext()
  const orgId = selectedOrg?.id

  const [frameworkKey, setFrameworkKey] = useState('')
  const [selectedVersionId, setSelectedVersionId] = useState('')
  const [activeAssignment, setActiveAssignment] = useState<{ id: string; systemId: string }>()
  const [activating, setActivating] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const activeAssignmentId = activeAssignment?.systemId === selectedSystem.id
    ? activeAssignment.id
    : undefined
  const assurance = useGovernanceAssurance(orgId, selectedSystem.id, activeAssignmentId)
  const versionState = useFrameworkVersions(orgId, frameworkKey || undefined)

  useEffect(() => {
    if (!frameworkKey || !assurance.frameworks.some((item) => item.frameworkKey === frameworkKey)) {
      setFrameworkKey(assurance.frameworks[0]?.frameworkKey || '')
    }
  }, [assurance.frameworks, frameworkKey])

  useEffect(() => {
    if (versionState.versions.length === 0) {
      setSelectedVersionId('')
      return
    }
    const assignedVersion = versionState.versions.find((version) =>
      assurance.assignments.some((assignment) =>
        assignment.systemId === selectedSystem.id && assignment.frameworkVersionId === version.id,
      ),
    )
    const selectionExists = versionState.versions.some((version) => version.id === selectedVersionId)
    if (!selectionExists) {
      setSelectedVersionId(assignedVersion?.id || versionState.versions[0].id)
    }
  }, [assurance.assignments, selectedSystem.id, selectedVersionId, versionState.versions])

  useEffect(() => {
    const selectedAssignment = assurance.assignments.find(
      (assignment) =>
        assignment.systemId === selectedSystem.id
        && assignment.frameworkVersionId === selectedVersionId,
    )
    setActiveAssignment(selectedAssignment
      ? { id: selectedAssignment.id, systemId: selectedAssignment.systemId }
      : undefined)
  }, [assurance.assignments, selectedSystem.id, selectedVersionId])

  const selectedVersion = versionState.versions.find((version) => version.id === selectedVersionId)
  const selectedFramework = assurance.frameworks.find((item) => item.frameworkKey === frameworkKey)
  const assignedVersionIds = useMemo(
    () => assurance.assignments.map((assignment) => assignment.frameworkVersionId),
    [assurance.assignments],
  )
  const canEdit = selectedOrg?.role === 'admin'
    || selectedOrg?.role === 'owner'
    || selectedOrg?.permissions?.includes('model:write') === true
  const catalogLoading = assurance.loading
    && (assurance.frameworks.length === 0 || assurance.assignments.length === 0)
    && !assurance.error
  const error = actionError || assurance.error?.message || versionState.error?.message || null

  const activateFramework = async () => {
    if (!selectedVersionId) return
    if (!canEdit) {
      setActionError('Your organization role cannot activate framework versions')
      return
    }
    setActivating(true)
    setActionError(null)
    try {
      const assignment = await assurance.assign(selectedVersionId)
      setActiveAssignment({ id: assignment.id, systemId: assignment.systemId })
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : 'Framework activation failed')
    } finally {
      setActivating(false)
    }
  }

  const retry = async () => {
    setActionError(null)
    await Promise.all([assurance.refresh(), versionState.refresh()])
  }

  const updateControl = async (
    control: WorkbenchControl,
    update: Pick<ControlAssessment, 'applicability' | 'status' | 'owner'>,
  ) => {
    if (!canEdit) throw new Error('Your organization role cannot update control assessments')
    await assurance.updateAssessment(control.id, update)
  }

  return (
    <main
      data-testid="framework-controls-workbench"
      className="space-y-5 pb-10 text-[var(--fm-ink)]"
    >
      <header className="flex flex-col gap-3 border-b border-[var(--fm-line)] pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B7659]">Governance workbench</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Frameworks &amp; Controls</h1>
          <p className="mt-2 max-w-[70ch] text-sm font-medium text-[var(--fm-ink2)]">
            Activate a version for {selectedSystem.name}, assign control work, and inspect the evidence trail before review.
          </p>
        </div>
        <Button
          type="button"
          variant="neutral"
          onClick={() => void retry()}
          className="border-[var(--fm-line)] bg-white font-semibold"
        >
          <IconRefresh aria-hidden="true" />
          Refresh workbench
        </Button>
      </header>

      <div className="flex flex-wrap gap-x-6 gap-y-2 border border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3 text-sm">
        <p><span className="font-semibold">Organization:</span> {selectedOrg?.name || 'Not selected'}</p>
        <p><span className="font-semibold">AI system:</span> {selectedSystem.name}</p>
        <p><span className="font-semibold">Version:</span> {selectedVersion?.versionLabel || 'Not selected'}</p>
      </div>

      {error ? (
        <Alert role="alert" className="border-2 border-[#D83A2E] bg-[#FFF0ED] text-[var(--fm-ink)]">
          <AlertDescription className="flex flex-col gap-3 font-bold sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button
              type="button"
              variant="neutral"
              onClick={() => void retry()}
              className="border-[var(--fm-line)] bg-white"
            >
              Retry loading frameworks
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {!error && catalogLoading ? (
        <WorkbenchLoading />
      ) : !error && assurance.frameworks.length === 0 ? (
        <section className="bg-[var(--fm-bg)] p-8 text-center rounded-[14px] shadow-[var(--fm-shadow)]">
          <h2 className="text-xl font-semibold">No framework versions available</h2>
          <p className="mx-auto mt-2 max-w-[60ch] text-sm text-[var(--fm-ink2)]">
            An organization administrator must import a versioned catalog before it can be activated for this AI system.
          </p>
        </section>
      ) : !error ? (
        <FrameworkCatalog
          frameworks={assurance.frameworks}
          versions={versionState.versions}
          selectedFrameworkKey={frameworkKey}
          selectedVersionId={selectedVersionId}
          assignedVersionIds={assignedVersionIds}
          loading={versionState.loading}
          activating={activating}
          canActivate={canEdit}
          systemName={selectedSystem.name}
          onFrameworkChange={setFrameworkKey}
          onVersionChange={setSelectedVersionId}
          onActivate={() => void activateFramework()}
        />
      ) : null}

      {!error && activeAssignmentId && selectedVersion ? (
        <>
          <ReadinessStrip
            frameworkName={selectedFramework?.name || selectedVersion.name}
            versionLabel={selectedVersion.versionLabel}
            readiness={assurance.readiness}
            loading={assurance.readinessLoading}
          />
          <ControlAssessmentTable
            controls={assurance.controls}
            loading={assurance.loading}
            canEdit={canEdit}
            frameworkName={selectedFramework?.name || selectedVersion.name}
            versionLabel={selectedVersion.versionLabel}
            onUpdate={updateControl}
          />
        </>
      ) : null}
    </main>
  )
}

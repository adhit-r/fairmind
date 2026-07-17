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
}) {
  const measures = [
    ['Applicable', readiness?.applicable ?? 0],
    ['Accepted', readiness?.accepted ?? 0],
    ['Ready for review', readiness?.readyForReview ?? 0],
    ['Missing evidence', readiness?.missingEvidence ?? 0],
    ['Blocking findings', readiness?.blockingFindings ?? 0],
  ] as const

  return (
    <section aria-labelledby="readiness-heading" className="border-2 border-[#0F1412] bg-[#FCFDF8]">
      <div className="flex flex-col gap-1 border-b-2 border-[#0F1412] bg-[oklch(0.60_0.13_163)] px-4 py-3 text-[#0F1412] sm:flex-row sm:items-center sm:justify-between">
        <h2 id="readiness-heading" className="text-base font-black uppercase tracking-tight">
          {frameworkName} readiness
        </h2>
        <p className="text-xs font-black uppercase tracking-[0.12em]">Version {versionLabel}</p>
      </div>
      <dl className="grid grid-cols-2 divide-x-2 divide-y-2 divide-[#0F1412] sm:grid-cols-5 sm:divide-y-0">
        {measures.map(([label, value]) => (
          <div key={label} className="min-h-[76px] px-3 py-3 first:col-span-2 sm:first:col-span-1">
            <dt className="text-[11px] font-black uppercase tracking-[0.1em] text-[#59615D]">{label}</dt>
            <dd className="mt-1 text-xl font-black text-[#0F1412]">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function WorkbenchLoading() {
  return (
    <div aria-label="Loading framework catalog" className="space-y-4 border-4 border-[#0F1412] bg-[#FCFDF8] p-5 shadow-[8px_8px_0_0_#0F1412]">
      <Skeleton className="h-5 w-48 rounded-none" />
      <Skeleton className="h-12 w-full rounded-none" />
      <div className="grid gap-3 sm:grid-cols-3">
        <Skeleton className="h-20 rounded-none" />
        <Skeleton className="h-20 rounded-none" />
        <Skeleton className="h-20 rounded-none" />
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
      className="space-y-5 bg-[#FCFDF8] pb-10 text-[#0F1412]"
    >
      <header className="flex flex-col gap-3 border-b-4 border-[#0F1412] pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0B7659]">Governance workbench</p>
          <h1 className="mt-1 text-2xl font-black uppercase tracking-tight sm:text-3xl">Frameworks &amp; Controls</h1>
          <p className="mt-2 max-w-[70ch] text-sm font-medium text-[#59615D]">
            Activate a version for {selectedSystem.name}, assign control work, and inspect the evidence trail before review.
          </p>
        </div>
        <Button
          type="button"
          variant="neutral"
          onClick={() => void retry()}
          className="rounded-none border-[#0F1412] bg-[#FCFDF8] font-black uppercase"
        >
          <IconRefresh aria-hidden="true" />
          Refresh workbench
        </Button>
      </header>

      <div className="flex flex-wrap gap-x-6 gap-y-2 border-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-3 text-sm">
        <p><span className="font-black uppercase">Organization:</span> {selectedOrg?.name || 'Not selected'}</p>
        <p><span className="font-black uppercase">AI system:</span> {selectedSystem.name}</p>
        <p><span className="font-black uppercase">Version:</span> {selectedVersion?.versionLabel || 'Not selected'}</p>
      </div>

      {error ? (
        <Alert role="alert" className="rounded-none border-2 border-[#D83A2E] bg-[#FFF0ED] text-[#0F1412]">
          <AlertDescription className="flex flex-col gap-3 font-bold sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button
              type="button"
              variant="neutral"
              onClick={() => void retry()}
              className="rounded-none border-[#0F1412] bg-[#FCFDF8]"
            >
              Retry loading frameworks
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {!error && catalogLoading ? (
        <WorkbenchLoading />
      ) : !error && assurance.frameworks.length === 0 ? (
        <section className="border-4 border-[#0F1412] bg-[#F3F5F0] p-8 text-center shadow-[8px_8px_0_0_#0F1412]">
          <h2 className="text-xl font-black uppercase">No framework versions available</h2>
          <p className="mx-auto mt-2 max-w-[60ch] text-sm text-[#59615D]">
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

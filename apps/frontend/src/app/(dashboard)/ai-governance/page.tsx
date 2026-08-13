'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { IconAlertTriangle, IconArrowRight, IconLeaf, IconLockCheck, IconRefresh } from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useOrg } from '@/context/OrgContext'
import { useAIGovernance, useEnvironmentalImpact } from '@/lib/api/hooks/useAIGovernance'
import { useGovernanceAssurance } from '@/lib/api/hooks/useGovernanceAssurance'

function countLabel(value: number, singular: string, plural = `${singular}s`) {
  return `${value} ${value === 1 ? singular : plural}`
}

function OverviewLoading() {
  return (
    <div aria-label="Loading assurance overview" className="space-y-4">
      <Skeleton className="h-24 w-full rounded-none" />
      <Skeleton className="h-36 w-full rounded-none" />
      <Skeleton className="h-48 w-full rounded-none" />
    </div>
  )
}

export default function AIGovernancePage() {
  const { selectedOrg } = useOrg()
  const { selectedSystem } = useSystemContext()
  const orgId = selectedOrg?.id
  const assuranceBase = useGovernanceAssurance(orgId, selectedSystem.id)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState('')
  useEffect(() => {
    if (!assuranceBase.resolvedAssignments.some(({ assignment }) => assignment.id === selectedAssignmentId)) {
      setSelectedAssignmentId(assuranceBase.resolvedAssignments[0]?.assignment.id || '')
    }
  }, [assuranceBase.resolvedAssignments, selectedAssignmentId])
  const activeScope = assuranceBase.resolvedAssignments.find(
    ({ assignment }) => assignment.id === selectedAssignmentId,
  )
  const activeAssignment = activeScope?.assignment
  const assurance = useGovernanceAssurance(orgId, selectedSystem.id, activeAssignment?.id)
  const assignedVersion = activeScope?.version
  const assignedFramework = activeScope?.framework
  const frameworkName = assignedFramework?.name || assignedVersion?.name || 'Framework'
  const readiness = assurance.readiness
  const loading = assuranceBase.loading || assurance.loading || assurance.readinessLoading
  const error = assuranceBase.error || assurance.error
  const canDecide = selectedOrg?.role === 'admin'
    || selectedOrg?.role === 'owner'
    || selectedOrg?.permissions?.includes('model:write') === true
  const {
    approvalLoading,
    getSystemApproval,
    requestSystemApproval,
    decideApprovalRequest,
  } = useAIGovernance()
  const environmental = useEnvironmentalImpact(orgId, selectedSystem.id)
  type ApprovalState = Awaited<ReturnType<typeof getSystemApproval>>
  const approvalRequestIdRef = useRef(0)
  const approvalSystemIdRef = useRef(selectedSystem.id)
  approvalSystemIdRef.current = selectedSystem.id
  const [approvalSnapshot, setApprovalSnapshot] = useState<{
    systemId: string
    state: ApprovalState | null
    loading: boolean
    error: string | null
  }>({ systemId: selectedSystem.id, state: null, loading: true, error: null })
  const approvalState = approvalSnapshot.systemId === selectedSystem.id ? approvalSnapshot.state : null
  const approvalError = approvalSnapshot.systemId === selectedSystem.id ? approvalSnapshot.error : null
  const approvalScopeLoading = approvalSnapshot.systemId !== selectedSystem.id || approvalSnapshot.loading
  const environmentalRecommendation = typeof environmental.data?.recommendation === 'string'
    ? environmental.data.recommendation
    : environmental.data?.recommendation?.status
  const environmentalRecommendationLabel = environmentalRecommendation
    ? `${environmentalRecommendation[0].toUpperCase()}${environmentalRecommendation.slice(1)}`
    : 'Not recorded'

  const loadApproval = useCallback(async (systemId: string) => {
    const requestId = ++approvalRequestIdRef.current
    setApprovalSnapshot({ systemId, state: null, loading: true, error: null })
    try {
      const state = await getSystemApproval(systemId)
      if (requestId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        setApprovalSnapshot({ systemId, state, loading: false, error: null })
      }
    } catch (reason) {
      if (requestId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        setApprovalSnapshot({
          systemId,
          state: null,
          loading: false,
          error: reason instanceof Error ? reason.message : 'Approval state unavailable',
        })
      }
    }
  }, [getSystemApproval])

  useEffect(() => {
    void loadApproval(selectedSystem.id)
  }, [loadApproval, selectedSystem.id])

  const refresh = async () => {
    const systemId = selectedSystem.id
    await Promise.all([assuranceBase.refresh(), assurance.refresh()])
    if (approvalSystemIdRef.current === systemId) {
      await loadApproval(systemId)
    }
  }

  const decideApproval = async (decision: 'approved' | 'rejected') => {
    const systemId = selectedSystem.id
    const requestId = approvalState?.request?.id
    if (!requestId || approvalSnapshot.systemId !== systemId || approvalSnapshot.loading) return
    const actionId = ++approvalRequestIdRef.current
    setApprovalSnapshot((current) => ({ ...current, loading: true, error: null }))
    try {
      await decideApprovalRequest(
        requestId,
        decision,
        decision === 'approved'
          ? 'Approved after assurance review.'
          : 'Rejected pending assurance blockers.',
        selectedSystem.owner,
      )
      if (actionId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        await loadApproval(systemId)
      }
    } catch (reason) {
      if (actionId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        setApprovalSnapshot((current) => ({
          ...current,
          loading: false,
          error: reason instanceof Error ? reason.message : 'Approval decision failed',
        }))
      }
    }
  }

  const submitApproval = async () => {
    const systemId = selectedSystem.id
    if (approvalSnapshot.systemId !== systemId || approvalSnapshot.loading) return
    const actionId = ++approvalRequestIdRef.current
    setApprovalSnapshot((current) => ({ ...current, loading: true, error: null }))
    try {
      const state = await requestSystemApproval(systemId, selectedSystem.owner)
      if (actionId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        setApprovalSnapshot({ systemId, state, loading: false, error: null })
      }
    } catch (reason) {
      if (actionId === approvalRequestIdRef.current && approvalSystemIdRef.current === systemId) {
        setApprovalSnapshot((current) => ({
          ...current,
          loading: false,
          error: reason instanceof Error ? reason.message : 'Approval request failed',
        }))
      }
    }
  }

  return (
    <main
      data-testid="governance-assurance-overview"
      className="space-y-5 bg-[#FCFDF8] pb-10 text-[#0F1412]"
    >
      <header className="flex flex-col gap-3 border-b-4 border-[#0F1412] pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0B7659]">Governance overview</p>
          <h1 className="mt-1 text-2xl font-black uppercase tracking-tight sm:text-3xl">
            AI Governance Assurance
          </h1>
          <p className="mt-2 max-w-[72ch] text-sm font-medium text-[#59615D]">
            Review the selected system&apos;s framework scope, explicit blockers, and evidence-backed control state before making an assurance decision.
          </p>
        </div>
        <Button
          type="button"
          variant="neutral"
          onClick={() => void refresh()}
          className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] font-black uppercase"
        >
          <IconRefresh aria-hidden="true" />
          Refresh overview
        </Button>
      </header>

      {assuranceBase.resolvedAssignments.length > 0 ? (
        <label className="flex flex-col gap-2 border-2 border-[#0F1412] bg-[#FCFDF8] p-3 text-xs font-black uppercase tracking-[0.1em] sm:flex-row sm:items-center">
          Framework scope
          <select
            aria-label="Framework scope"
            value={selectedAssignmentId}
            onChange={(event) => setSelectedAssignmentId(event.target.value)}
            className="min-h-11 flex-1 rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 text-sm font-black normal-case"
          >
            {assuranceBase.resolvedAssignments.map(({ assignment, framework, version }) => (
              <option key={assignment.id} value={assignment.id}>{framework.name} {version.versionLabel}</option>
            ))}
          </select>
        </label>
      ) : null}

      <section
        aria-label="Assurance scope"
        className="grid border-2 border-[#0F1412] bg-[#F3F5F0] sm:grid-cols-2 xl:grid-cols-4"
      >
        {[
          ['Company', selectedOrg?.name || 'Not selected'],
          ['AI system', selectedSystem.name],
          ['Framework version', assignedVersion ? `${frameworkName} ${assignedVersion.versionLabel}` : 'Not assigned'],
          ['Review period', 'Current recorded state'],
        ].map(([label, value]) => (
          <div key={label} className="border-b-2 border-[#0F1412] px-4 py-3 last:border-b-0 sm:border-r-2 sm:[&:nth-child(2)]:border-r-0 sm:[&:nth-child(3)]:border-b-0 xl:border-b-0 xl:[&:nth-child(2)]:border-r-2 xl:[&:nth-child(3)]:border-r-2">
            <p className="text-[11px] font-black uppercase tracking-[0.12em] text-[#59615D]">{label}</p>
            <p className="mt-1 text-sm font-black">{value}</p>
          </div>
        ))}
      </section>

      {error ? (
        <Alert role="alert" className="rounded-none border-2 border-[#D83A2E] bg-[#FFF0ED] text-[#0F1412]">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription className="flex flex-col gap-3 font-bold sm:flex-row sm:items-center sm:justify-between">
            <span>{error.message}</span>
            <Button type="button" variant="neutral" onClick={() => void refresh()} className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8]">
              Retry assurance data
            </Button>
          </AlertDescription>
        </Alert>
      ) : loading ? (
        <OverviewLoading />
      ) : !activeAssignment || !assignedVersion ? (
        <section className="border-4 border-[#0F1412] bg-[#F3F5F0] p-7 shadow-[8px_8px_0_0_#0F1412]">
          <h2 className="text-xl font-black uppercase">Framework scope required</h2>
          <p className="mt-2 max-w-[65ch] text-sm text-[#59615D]">
            Activate a versioned framework for this AI system before readiness can be reviewed. No readiness counts are inferred while scope is missing.
          </p>
          <Button asChild className="mt-5 rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]">
            <Link href="/compliance-dashboard">
              Open frameworks and controls
              <IconArrowRight aria-hidden="true" />
            </Link>
          </Button>
        </section>
      ) : !readiness ? (
        <section className="border-2 border-[#0F1412] bg-[#FFF0ED] p-5">
          <h2 className="font-black uppercase">Readiness unavailable</h2>
          <p className="mt-1 text-sm text-[#59615D]">The assigned framework has no recorded readiness summary.</p>
        </section>
      ) : (
        <>
          <section aria-label="Readiness blockers" className="border-4 border-[#0F1412] bg-[#FCFDF8] shadow-[8px_8px_0_0_#0F1412]">
            <div className="border-b-4 border-[#0F1412] bg-[#0F1412] px-5 py-4 text-[#FCFDF8]">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#E97522]">Resolve before review</p>
              <h2 className="mt-1 text-xl font-black uppercase">Readiness Blockers</h2>
            </div>
            <div className="grid md:grid-cols-3">
              <div className="border-b-2 border-[#0F1412] p-5 md:border-b-0 md:border-r-2">
                <p className="text-2xl font-black text-[#D83A2E]">{readiness.blockingFindings}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.blockingFindings === 0
                    ? 'No rejected assessments reported'
                    : countLabel(readiness.blockingFindings, 'rejected assessment')}
                </p>
              </div>
              <div className="border-b-2 border-[#0F1412] p-5 md:border-b-0 md:border-r-2">
                <p className="text-2xl font-black text-[#B85A16]">{readiness.missingEvidence}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.missingEvidence === 0
                    ? 'No missing accepted evidence reported'
                    : `${countLabel(readiness.missingEvidence, 'control')} missing accepted evidence`}
                </p>
              </div>
              <div className="p-5">
                <p className="text-2xl font-black text-[#B85A16]">{readiness.staleEvidence}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.staleEvidence === 0
                    ? 'No stale evidence reported'
                    : `${countLabel(readiness.staleEvidence, 'control')} with stale evidence`}
                </p>
              </div>
            </div>
          </section>

          <section aria-label={`${frameworkName} readiness`} className="border-2 border-[#0F1412] bg-[#FCFDF8]">
            <div className="border-b-2 border-[#0F1412] bg-[oklch(0.60_0.13_163)] px-5 py-4">
              <p className="text-xs font-black uppercase tracking-[0.14em]">Version {assignedVersion.versionLabel}</p>
              <h2 className="mt-1 text-xl font-black uppercase">{frameworkName} Readiness</h2>
              <p className="mt-1 text-sm font-bold">
                {readiness.accepted} accepted of {readiness.applicable} applicable controls. Counts reflect recorded assessments and reviewed evidence mappings.
              </p>
            </div>
            <dl className="grid grid-cols-2 divide-x-2 divide-y-2 divide-[#0F1412] sm:grid-cols-4 xl:grid-cols-7 xl:divide-y-0">
              {[
                ['Applicable', readiness.applicable],
                ['Accepted', readiness.accepted],
                ['Ready for review', readiness.readyForReview],
                ['Partial', readiness.partial],
                ['Not started', readiness.notStarted],
                ['Not applicable', readiness.notApplicable],
                ['Stale evidence', readiness.staleEvidence],
              ].map(([label, value]) => (
                <div key={label} className="min-h-[84px] p-3">
                  <dt className="text-[11px] font-black uppercase tracking-[0.08em] text-[#59615D]">{label}</dt>
                  <dd className="mt-2 text-xl font-black">
                    {value}{' '}
                    <span className="text-xs font-bold text-[#59615D]">{String(label).toLowerCase()}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="grid gap-5 xl:grid-cols-2">
            <section aria-label="Approval decision" className="border-2 border-[#0F1412] bg-[#FCFDF8]">
              <div className="flex items-center gap-3 border-b-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-3">
                <IconLockCheck aria-hidden="true" />
                <div>
                  <h2 className="font-black uppercase">Approval Decision</h2>
                  <p className="mt-1 text-xs text-[#59615D]">Persisted request and reviewer decision for this AI system.</p>
                </div>
              </div>
              <div className="space-y-4 p-5">
                {approvalScopeLoading ? (
                  <div aria-label="Loading approval decision" className="space-y-2">
                    <Skeleton className="h-4 w-28 rounded-none" />
                    <Skeleton className="h-9 w-44 rounded-none" />
                  </div>
                ) : <div>
                  <p className="text-xs font-black uppercase tracking-[0.1em] text-[#59615D]">Current state</p>
                  <p className="mt-1 text-2xl font-black">
                    {approvalState?.request?.status
                      ? `${approvalState.request.status[0].toUpperCase()}${approvalState.request.status.slice(1)}`
                      : 'Not submitted'}
                  </p>
                  {approvalState?.decisions?.at(-1) ? (
                    <p className="mt-2 text-sm font-bold">Latest decision: <span className="capitalize">{approvalState.decisions.at(-1)?.decision}</span>. {approvalState.decisions.at(-1)?.notes || 'No decision rationale recorded.'}</p>
                  ) : null}
                </div>}
                {approvalError ? <p role="alert" className="border-2 border-[#D83A2E] bg-[#FFF0ED] p-3 text-sm font-bold">{approvalError}</p> : null}
                {!approvalScopeLoading && canDecide && approvalState?.request?.status === 'pending' ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Button
                      type="button"
                      disabled={approvalLoading || approvalSnapshot.loading}
                      onClick={() => void decideApproval('approved')}
                      className="rounded-none border-2 border-[#0F1412] bg-[oklch(0.60_0.13_163)] font-black uppercase text-[#0F1412]"
                    >
                      Approve request
                    </Button>
                    <Button
                      type="button"
                      variant="neutral"
                      disabled={approvalLoading || approvalSnapshot.loading}
                      onClick={() => void decideApproval('rejected')}
                      className="rounded-none border-2 border-[#0F1412] bg-[#FFF0ED] font-black uppercase"
                    >
                      Reject request
                    </Button>
                  </div>
                ) : !approvalScopeLoading && canDecide && approvalState?.request?.status !== 'pending' ? (
                  <Button
                    type="button"
                    disabled={approvalLoading || approvalSnapshot.loading}
                    onClick={() => void submitApproval()}
                    className="rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]"
                  >
                    Submit for approval
                  </Button>
                ) : !approvalScopeLoading ? (
                  <p className="text-sm font-bold text-[#59615D]">Read-only access. Approval actions require organization mutation permission.</p>
                ) : null}
              </div>
            </section>

            <section aria-label="Environmental governance" className="border-2 border-[#0F1412] bg-[#FCFDF8]">
              <div className="flex items-center gap-3 border-b-2 border-[#0F1412] bg-[#E5F4EF] px-4 py-3">
                <IconLeaf aria-hidden="true" />
                <div>
                  <h2 className="font-black uppercase">Environmental Governance</h2>
                  <p className="mt-1 text-xs text-[#59615D]">Energy, carbon, provenance, and environmental evidence for the selected system.</p>
                </div>
              </div>
              {environmental.loading ? (
                <div aria-label="Loading environmental governance" className="grid grid-cols-2 gap-3 p-5">
                  <Skeleton className="h-20 rounded-none" /><Skeleton className="h-20 rounded-none" />
                </div>
              ) : environmental.error ? (
                <p role="alert" className="m-5 border-2 border-[#D83A2E] bg-[#FFF0ED] p-3 text-sm font-bold">{environmental.error.message}</p>
              ) : !environmental.data ? (
                <p className="p-5 text-sm font-bold text-[#59615D]">{environmental.emptyReason || 'No environmental impact packet is recorded.'}</p>
              ) : (
                <div className="space-y-4 p-5">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="border-2 border-[#0F1412] p-3"><p className="text-xs font-black uppercase text-[#59615D]">Energy</p><p className="mt-1 text-xl font-black">{environmental.data.totals?.energyKwh ?? 'Unknown'}{environmental.data.totals?.energyKwh != null ? ' kWh' : ''}</p></div>
                    <div className="border-2 border-[#0F1412] p-3"><p className="text-xs font-black uppercase text-[#59615D]">Carbon</p><p className="mt-1 text-xl font-black">{environmental.data.totals?.carbonKgCo2e ?? 'Unknown'}{environmental.data.totals?.carbonKgCo2e != null ? ' kg CO2e' : ''}</p></div>
                  </div>
                  <div className="border-t-2 border-[#0F1412] pt-3">
                    <p className="text-xs font-black uppercase text-[#59615D]">Recommendation</p>
                    <p className="mt-1 font-black">{environmentalRecommendationLabel}</p>
                    {typeof environmental.data.recommendation === 'object' ? <p className="mt-1 text-sm font-bold">{environmental.data.recommendation?.summary}</p> : null}
                  </div>
                  <div className="border-t-2 border-[#0F1412] pt-3 text-sm">
                    <p><span className="font-black uppercase">Source:</span> {environmental.data.provenance?.source || 'Not recorded'}</p>
                    <p><span className="font-black uppercase">Method:</span> {environmental.data.provenance?.methodology || 'Not recorded'}</p>
                  </div>
                  {environmental.data.evidenceLinks?.length ? (
                    <ul className="border-t-2 border-[#0F1412] pt-3">
                      {environmental.data.evidenceLinks.map((item) => <li key={item.id || item.title} className="text-sm font-bold">{item.title || 'Environmental evidence'} · {item.source || 'source unknown'}</li>)}
                    </ul>
                  ) : null}
                </div>
              )}
            </section>
          </div>

          <div className="flex flex-col gap-3 border-t-2 border-[#0F1412] pt-5 sm:flex-row">
            <Button asChild className="rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]">
              <Link href="/compliance-dashboard">
                Review control assessments
                <IconArrowRight aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="neutral" className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] font-black uppercase">
              <Link href="/reports?view=builder">
                Open reports and assurance
                <IconArrowRight aria-hidden="true" />
              </Link>
            </Button>
          </div>

          <nav aria-label="Related governance workflows" className="grid border-2 border-[#0F1412] bg-[#F3F5F0] sm:grid-cols-3">
            {[
              ['/evidence?view=evaluations', 'Evidence & evaluations', 'Inspect provenance and review candidate mappings.'],
              ['/risks', 'Findings', 'Review open risks and finding context.'],
              ['/remediation', 'Remediation', 'Track corrective work and required re-tests.'],
            ].map(([href, label, description]) => (
              <Link key={href} href={href} className="border-b-2 border-[#0F1412] p-4 last:border-b-0 hover:bg-[#FCFDF8] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-[-4px] focus-visible:outline-[#0B7659] sm:border-b-0 sm:border-r-2 sm:last:border-r-0">
                <span className="font-black uppercase">{label}</span>
                <span className="mt-1 block text-sm text-[#59615D]">{description}</span>
              </Link>
            ))}
          </nav>
        </>
      )}
    </main>
  )
}

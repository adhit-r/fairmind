'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconFileCheck,
  IconHistory,
  IconLockCheck,
  IconRefresh,
} from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useOrg } from '@/context/OrgContext'
import {
  useGovernanceAssurance,
  type EvidenceMapping,
} from '@/lib/api/hooks/useGovernanceAssurance'
import { AssuranceReportStudio } from './components/AssuranceReportStudio'

function formatDate(value: string | null) {
  if (!value) return 'Not recorded'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not recorded'
  return date.toLocaleString()
}

function countLabel(value: number, singular: string, plural = `${singular}s`) {
  return `${value} ${value === 1 ? singular : plural}`
}

function latestReview(mapping: EvidenceMapping) {
  return mapping.reviewHistory[mapping.reviewHistory.length - 1]
}

export default function ReportsPage() {
  const searchParams = useSearchParams()
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
  const canEdit = selectedOrg?.role === 'admin'
    || selectedOrg?.role === 'owner'
    || selectedOrg?.permissions?.includes('model:write') === true
  const auditorMode = searchParams.get('mode') === 'auditor' || !canEdit
  const readiness = assurance.readiness
  const loading = assuranceBase.loading || assurance.loading || assurance.readinessLoading
  const error = assuranceBase.error || assurance.error

  const evidencePeriod = useMemo(() => {
    const captured = assurance.evidenceRuns
      .map((run) => run.capturedAt)
      .filter((value): value is string => Boolean(value))
      .map((value) => new Date(value))
      .filter((value) => !Number.isNaN(value.getTime()))
      .sort((left, right) => left.getTime() - right.getTime())
    if (captured.length === 0) return 'No recorded evidence period'
    const first = captured[0].toLocaleDateString()
    const last = captured[captured.length - 1].toLocaleDateString()
    return first === last ? first : `${first} to ${last}`
  }, [assurance.evidenceRuns])

  const reviewedMappings = useMemo(
    () => assurance.evidenceRuns.flatMap((run) => run.candidateMappings)
      .filter((mapping) => mapping.state === 'accepted' || mapping.state === 'rejected'),
    [assurance.evidenceRuns],
  )
  const controlById = useMemo(
    () => new Map(assurance.controls.map((control) => [control.id, control])),
    [assurance.controls],
  )
  const limitations = useMemo(
    () => [...new Set(assurance.evidenceRuns.flatMap((run) => run.limitations).filter(Boolean))],
    [assurance.evidenceRuns],
  )
  const knownControlFindingCounts = assurance.controls
    .map((control) => control.openFindings)
    .filter((value): value is number => typeof value === 'number')
  const controlFindingsIncomplete = knownControlFindingCounts.length !== assurance.controls.length
  const knownControlFindings = knownControlFindingCounts.reduce((sum, count) => sum + count, 0)

  const refresh = async () => {
    await Promise.all([assuranceBase.refresh(), assurance.refresh()])
  }

  return (
    <main data-testid="assurance-report" className="space-y-5 pb-10 text-[var(--fm-ink)]">
      <header className="fm-card p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border border-[var(--fm-line)] bg-[var(--fm-bg)] font-semibold text-[var(--fm-ink)]">
                <IconFileCheck aria-hidden="true" />
                Assurance summary
              </Badge>
              <Badge className="border border-[#E97522] bg-transparent font-semibold text-[#B85A16]">
                {auditorMode ? 'Auditor mode' : 'Builder mode'}
              </Badge>
            </div>
            <h1 className="mt-4 text-2xl font-semibold tracking-tight sm:text-3xl">Reports &amp; Assurance</h1>
            <p className="mt-2 max-w-[72ch] text-sm text-[var(--fm-ink2)]">
              A version-pinned review surface for control state, evidence provenance, reviewer decisions, unresolved findings, and known limitations.
            </p>
          </div>
          <Button
            type="button"
            variant="neutral"
            onClick={() => void refresh()}
            className="border border-[var(--fm-line)] bg-[var(--fm-bg)] font-semibold text-[var(--fm-ink)]"
          >
            <IconRefresh aria-hidden="true" />
            Refresh summary
          </Button>
        </div>
      </header>

      {auditorMode ? (
        <section className="flex items-start gap-3 border border-[var(--fm-line)] bg-[#E5F4EF] p-4" aria-label="Auditor access">
          <IconLockCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">Read-only auditor view</p>
            <p className="mt-1 text-sm text-[var(--fm-ink2)]">The same assurance route is shown without control or evidence review actions.</p>
          </div>
        </section>
      ) : null}

      {assuranceBase.resolvedAssignments.length > 0 ? (
        <label className="flex flex-col gap-2 border border-[var(--fm-line)] bg-white p-3 text-xs font-semibold uppercase tracking-[0.1em] sm:flex-row sm:items-center">
          Framework scope
          <select
            aria-label="Framework scope"
            value={selectedAssignmentId}
            onChange={(event) => setSelectedAssignmentId(event.target.value)}
            className="min-h-11 flex-1 border border-[var(--fm-line)] bg-white px-3 text-sm font-semibold normal-case"
          >
            {assuranceBase.resolvedAssignments.map(({ assignment, framework, version }) => (
              <option key={assignment.id} value={assignment.id}>{framework.name} {version.versionLabel}</option>
            ))}
          </select>
        </label>
      ) : null}

      <section aria-label="Assurance scope" className="border border-[var(--fm-line)] bg-[var(--fm-bg)]">
        <div className="border-b border-[var(--fm-line)] px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0B7659]">Pinned scope</p>
          <h2 className="mt-1 text-lg font-semibold">Assurance Scope</h2>
        </div>
        <dl className="grid sm:grid-cols-2 xl:grid-cols-5">
          {[
            ['Company', selectedOrg?.name || 'Not selected'],
            ['AI system', selectedSystem.name],
            ['Framework', assignedVersion ? `${frameworkName} ${assignedVersion.versionLabel}` : 'Not assigned'],
            ['Catalog hash', assignedVersion?.sourceHash || 'Not available'],
            ['Evidence period', evidencePeriod],
          ].map(([label, value]) => (
            <div key={label} className="border-b border-[var(--fm-line)] px-4 py-3 sm:border-r-2 xl:border-b-0 last:border-b-0 xl:last:border-r-0">
              <dt className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">{label}</dt>
              <dd className="mt-1 break-all text-sm font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      {error ? (
        <Alert role="alert" className="border-2 border-[#D83A2E] bg-[#FFF0ED] text-[var(--fm-ink)]">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription className="font-bold">{error.message}</AlertDescription>
        </Alert>
      ) : loading ? (
        <div aria-label="Loading assurance report" className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
        </div>
      ) : !activeAssignment || !assignedVersion ? (
        <section className="bg-[var(--fm-bg)] p-7 rounded-[14px] shadow-[var(--fm-shadow)]">
          <h2 className="text-xl font-semibold">No version-pinned scope</h2>
          <p className="mt-2 max-w-[66ch] text-sm text-[var(--fm-ink2)]">Activate a framework version before preparing an assurance summary. Unknown scope is not represented as zero readiness.</p>
          {!auditorMode ? (
            <Button asChild className="mt-5 border border-[var(--fm-line)] bg-[#E97522] font-semibold text-[var(--fm-ink)]">
              <Link href="/compliance-dashboard">Assign framework scope<IconArrowRight aria-hidden="true" /></Link>
            </Button>
          ) : null}
        </section>
      ) : (
        <>
          <section className="grid border border-[var(--fm-line)] bg-white lg:grid-cols-3" aria-label={`${frameworkName} readiness summary`}>
            <div className="border-b border-[var(--fm-line)] bg-[oklch(0.60_0.13_163)] p-5 lg:border-b-0 lg:border-r-2">
              <p className="text-xs font-semibold uppercase tracking-[0.14em]">Transparent readiness</p>
              <p className="mt-2 text-3xl font-semibold">{readiness ? `${readiness.accepted} / ${readiness.applicable}` : 'Unknown'}</p>
              <p className="mt-1 text-sm font-bold">Accepted controls / applicable controls</p>
            </div>
            <div className="border-b border-[var(--fm-line)] p-5 lg:border-b-0 lg:border-r-2">
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Review queue</p>
              <p className="mt-2 text-3xl font-semibold">{readiness?.readyForReview ?? 'Unknown'}</p>
              <p className="mt-1 text-sm font-bold">Ready for reviewer assessment</p>
            </div>
            <div className="p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Evidence gaps</p>
              <p className="mt-2 text-3xl font-semibold">{readiness?.missingEvidence ?? 'Unknown'}</p>
              <p className="mt-1 text-sm font-bold">Controls missing accepted evidence</p>
            </div>
          </section>

          <div className="grid gap-5 xl:grid-cols-2">
            <section aria-label="Evidence index" className="border border-[var(--fm-line)] bg-white">
              <div className="border-b border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3">
                <h2 className="font-semibold">Evidence Index</h2>
                <p className="mt-1 text-xs text-[var(--fm-ink2)]">Immutable run identity and canonical content hash.</p>
              </div>
              {assurance.evidenceRuns.length === 0 ? (
                <p className="p-5 text-sm font-bold text-[var(--fm-ink2)]">No evidence runs are recorded for this AI system.</p>
              ) : (
                <ol className="divide-y-2 divide-[var(--fm-line)]">
                  {assurance.evidenceRuns.map((run) => (
                    <li key={run.id} className="p-4">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold">{run.suiteName || run.sourceIdentifier}</p>
                          <p className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">{run.sourceIdentifier} · {run.result.replace(/_/g, ' ')}</p>
                        </div>
                        <Badge variant="outline" className="border border-[var(--fm-line)] bg-white font-semibold">{run.assuranceSource?.replace(/_/g, ' ') || 'Source unknown'}</Badge>
                      </div>
                      <dl className="mt-3 space-y-2 text-xs">
                        <div><dt className="font-semibold text-[var(--fm-ink2)]">Content hash</dt><dd className="break-all font-mono font-bold">{run.contentHash}</dd></div>
                        <div><dt className="font-semibold text-[var(--fm-ink2)]">Captured</dt><dd className="font-bold">{formatDate(run.capturedAt)}</dd></div>
                        <div><dt className="font-semibold text-[var(--fm-ink2)]">Versions</dt><dd className="font-bold">Subject {run.subjectVersion || 'not recorded'} · Suite {run.suiteVersion || 'not recorded'} · Runner {run.runnerVersion || 'not recorded'}</dd></div>
                      </dl>
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <section aria-label="Unresolved findings" className="border border-[var(--fm-line)] bg-white">
              <div className="border-b border-[var(--fm-line)] bg-[#FFF0ED] px-4 py-3">
                <h2 className="font-semibold">Unresolved Findings</h2>
                <p className="mt-1 text-xs text-[var(--fm-ink2)]">Counts are reported only when present in the framework assessment contract.</p>
              </div>
              <div className="p-5">
                <p className="text-3xl font-semibold text-[#D83A2E]">{readiness?.blockingFindings ?? 'Unknown'}</p>
                <p className="mt-1 font-semibold">{readiness ? countLabel(readiness.blockingFindings, 'rejected assessment') : 'Rejected assessment count unavailable'}</p>
                <div className="mt-5 border-t border-[var(--fm-line)] pt-4">
                  <p className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Control-linked detail</p>
                  <p className="mt-1 text-sm font-bold">
                    {controlFindingsIncomplete
                      ? `${knownControlFindings} known; at least one control does not expose a finding count.`
                      : countLabel(knownControlFindings, 'open control finding')}
                  </p>
                </div>
              </div>
            </section>

            <section aria-label="Decision register" className="border border-[var(--fm-line)] bg-white">
              <div className="border-b border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3">
                <h2 className="font-semibold">Decision Register</h2>
                <p className="mt-1 text-xs text-[var(--fm-ink2)]">Recorded mapping reviews; candidate suggestions are not decisions.</p>
              </div>
              {reviewedMappings.length === 0 ? (
                <p className="p-5 text-sm font-bold text-[var(--fm-ink2)]">No accepted or rejected mapping decisions are recorded.</p>
              ) : (
                <ol className="divide-y-2 divide-[var(--fm-line)]">
                  {reviewedMappings.map((mapping) => {
                    const review = latestReview(mapping)
                    const control = controlById.get(mapping.controlAssessmentId)
                    return (
                      <li key={mapping.id} className="p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className={`border border-[var(--fm-line)] font-semibold text-[var(--fm-ink)] ${mapping.state === 'accepted' ? 'bg-[#E5F4EF]' : 'bg-[#FFF0ED]'}`}>
                            {mapping.state === 'accepted' ? 'Accepted' : 'Rejected'}
                          </Badge>
                          <p className="font-semibold">{control ? `${control.externalId} — ${control.title}` : 'Control reference unavailable'}</p>
                        </div>
                        <p className="mt-2 text-sm font-bold">{review?.rationale || mapping.rationale || 'No rationale recorded.'}</p>
                        <p className="mt-2 text-xs text-[var(--fm-ink2)]">Reviewed by {review?.reviewedBy || 'identity unavailable'} · {formatDate(review?.reviewedAt || null)}</p>
                      </li>
                    )
                  })}
                </ol>
              )}
            </section>

            <section aria-label="Limitations" className="border border-[var(--fm-line)] bg-white">
              <div className="border-b border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3">
                <h2 className="font-semibold">Limitations</h2>
                <p className="mt-1 text-xs text-[var(--fm-ink2)]">Known evaluation and assurance-boundary limitations remain part of the report.</p>
              </div>
              <ul className="divide-y-2 divide-[var(--fm-line)]">
                {limitations.length > 0 ? limitations.map((limitation) => (
                  <li key={limitation} className="p-4 text-sm font-bold">{limitation}</li>
                )) : (
                  <li className="p-4 text-sm font-bold text-[var(--fm-ink2)]">
                    {assurance.evidenceRuns.length === 0
                      ? 'No evidence runs are in scope, so evaluation limitations are unknown.'
                      : 'No evaluation limitations were recorded in the in-scope run envelopes.'}
                  </li>
                )}
                <li className="p-4 text-sm font-bold">This summary supports readiness review. It is not an official certification or an assurance opinion.</li>
              </ul>
            </section>
          </div>

          <section aria-label="Assurance history" className="border border-[var(--fm-line)] bg-white">
            <div className="flex items-center gap-3 border-b border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3">
              <IconHistory aria-hidden="true" />
              <div>
                <h2 className="font-semibold">Assurance History</h2>
                <p className="mt-1 text-xs text-[var(--fm-ink2)]">Tenant-scoped evidence runs retained for the current report scope.</p>
              </div>
            </div>
            {assurance.evidenceRuns.length === 0 ? (
              <p className="p-5 text-sm font-bold text-[var(--fm-ink2)]">No evidence-run history is recorded.</p>
            ) : (
              <ol className="divide-y-2 divide-[var(--fm-line)]">
                {[...assurance.evidenceRuns]
                  .sort((left, right) => (right.capturedAt || '').localeCompare(left.capturedAt || ''))
                  .map((run) => (
                    <li key={run.id} className="grid gap-2 p-4 sm:grid-cols-[1fr_auto] sm:items-center">
                      <div>
                        <p className="font-semibold">{run.suiteName || run.sourceIdentifier}</p>
                        <p className="mt-1 text-xs text-[var(--fm-ink2)]">Run {run.runId} · captured {formatDate(run.capturedAt)}</p>
                      </div>
                      <p className="break-all font-mono text-xs font-bold">{run.contentHash}</p>
                    </li>
                  ))}
              </ol>
            )}
          </section>

          <AssuranceReportStudio
            system={{
              id: selectedSystem.id,
              name: selectedSystem.name,
              owner: selectedSystem.owner,
              riskTier: selectedSystem.riskTier,
              lifecycleStage: selectedSystem.stage,
              readiness: selectedSystem.readiness,
            }}
            frameworkLabel={`${frameworkName} ${assignedVersion.versionLabel}`}
            assurance={{
              frameworkLabel: `${frameworkName} ${assignedVersion.versionLabel}`,
              readiness: readiness ? {
                applicable: readiness.applicable,
                accepted: readiness.accepted,
                blockingFindings: readiness.blockingFindings,
                missingEvidence: readiness.missingEvidence,
                staleEvidence: readiness.staleEvidence,
              } : null,
              evidenceRuns: assurance.evidenceRuns.map((run) => ({
                sourceIdentifier: run.sourceIdentifier,
                suiteName: run.suiteName,
                contentHash: run.contentHash,
                result: run.result,
                capturedAt: run.capturedAt,
              })),
              controls: assurance.controls.map((control) => ({
                externalId: control.externalId,
                title: control.title,
                openFindings: control.openFindings,
              })),
              limitations,
            }}
            readOnly={auditorMode}
          />

          {!auditorMode ? (
            <nav aria-label="Assurance builder actions" className="flex flex-col gap-3 border-t border-[var(--fm-line)] pt-5 sm:flex-row">
              <Button asChild className="border border-[var(--fm-line)] bg-[#E97522] font-semibold text-[var(--fm-ink)]">
                <Link href="/compliance-dashboard">Review control assessments<IconArrowRight aria-hidden="true" /></Link>
              </Button>
              <Button asChild variant="neutral" className="border border-[var(--fm-line)] bg-white font-semibold">
                <Link href="/evidence?view=evaluations">Review evidence mappings<IconArrowRight aria-hidden="true" /></Link>
              </Button>
            </nav>
          ) : null}
        </>
      )}
    </main>
  )
}

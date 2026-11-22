'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useSearchParams } from 'next/navigation'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { BTN, BTN_P, ErrorNote, LABEL, Loading, MUTED, Pill } from '@/components/packs/parts'
import { useOrg } from '@/context/OrgContext'
import {
  useGovernanceAssurance,
  type EvidenceMapping,
} from '@/lib/api/hooks/useGovernanceAssurance'
import { AssuranceReportStudio } from './components/AssuranceReportStudio'

const field =
  'h-9 rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none focus:border-[var(--fm-ink)]'
const sub = `mt-1 text-[12.5px] ${MUTED}`
const row = 'border-t border-[var(--fm-line)] py-3'

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

function Fact({ name, value, mono }: { name: string; value: ReactNode; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className={LABEL}>{name}</dt>
      <dd className={`mt-0.5 text-[13.5px] tabular-nums ${mono ? 'break-all font-mono text-[12px]' : '[overflow-wrap:anywhere]'}`}>{value}</dd>
    </div>
  )
}

function Crumb() {
  return (
    <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
      <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Exports
    </div>
  )
}

// A value that is still loading shows a dash, and one whose load failed says so; neither is shown as a real value.
const Pending = () => (
  <>
    <span aria-hidden="true">–</span>
    <span className="sr-only">Loading</span>
  </>
)

export default function ReportsPage() {
  const searchParams = useSearchParams()
  const { selectedOrg } = useOrg()
  const { selectedSystem, loading: systemsLoading, error: systemsError, refreshSystems } = useSystemContext()
  const hasSystem = Boolean(selectedSystem.id)
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

  const runsNewestFirst = useMemo(
    () => [...assurance.evidenceRuns].sort((left, right) => (right.capturedAt || '').localeCompare(left.capturedAt || '')),
    [assurance.evidenceRuns],
  )
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

  const scoped = (value: ReactNode): ReactNode => (loading ? <Pending /> : error ? 'Unavailable' : value)

  return (
    <main data-testid="assurance-report" className="grid gap-4 pb-10 text-[var(--fm-ink)]">
      <Crumb />
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Reports &amp; Assurance</h1>
          <p className={`mt-2 max-w-[640px] text-[15px] ${MUTED}`}>
            {hasSystem
              ? `A version-pinned summary for ${selectedSystem.name}: control state, evidence, reviewer decisions, open findings and known limits. Save it as a report to export it.`
              : 'A version-pinned summary for each AI system: control state, evidence, reviewer decisions, open findings and known limits.'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <Pill>{auditorMode ? 'Auditor mode' : 'Builder mode'}</Pill>
          {hasSystem && (
            <button type="button" onClick={() => void refresh()} className={BTN}>Refresh summary</button>
          )}
        </div>
      </header>

      {auditorMode && (
        <section aria-label="Auditor access" className="fm-card px-5 py-3.5 text-[13px]">
          <span className="font-semibold">Read-only auditor view.</span>{' '}
          <span className={MUTED}>The same summary, without control or evidence review actions.</span>
        </section>
      )}

      {!hasSystem ? (
        <section aria-label="No system" className="fm-card grid content-start justify-items-start gap-3 p-6">
          {systemsLoading ? (
            <p role="status" className={`text-[13px] ${MUTED}`}>Loading your systems</p>
          ) : systemsError ? (
            <>
              <h2 className="text-[15px] font-semibold">Could not load your systems</h2>
              <p role="alert" className={`max-w-[560px] text-[13px] ${MUTED}`}>
                An assurance summary belongs to a system, so it cannot be shown until your systems load. {systemsError}
              </p>
              <button type="button" onClick={() => void refreshSystems()} className={BTN_P}>Try again</button>
            </>
          ) : (
            <>
              <h2 className="text-[15px] font-semibold">No AI system is registered yet</h2>
              <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
                An assurance summary belongs to a system, so there is nothing to report or export until one exists.
              </p>
              {!auditorMode && <Link href="/onboard" className={BTN_P}>Register a system</Link>}
            </>
          )}
        </section>
      ) : (
        <>
          <div className="fm-card p-5">
            {assuranceBase.resolvedAssignments.length > 0 && (
              <label className="mb-4 flex flex-wrap items-center gap-2.5">
                <span className={LABEL}>Framework scope</span>
                <select
                  aria-label="Framework scope"
                  value={selectedAssignmentId}
                  onChange={(event) => setSelectedAssignmentId(event.target.value)}
                  className={field}
                >
                  {assuranceBase.resolvedAssignments.map(({ assignment, framework, version }) => (
                    <option key={assignment.id} value={assignment.id}>{framework.name} {version.versionLabel}</option>
                  ))}
                </select>
              </label>
            )}
            <section aria-label="Assurance scope">
              <h2 className="text-[15px] font-semibold">Assurance scope</h2>
              <dl className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2 xl:grid-cols-5">
                <Fact name="Company" value={selectedOrg?.name || 'Not selected'} />
                <Fact name="AI system" value={selectedSystem.name} />
                <Fact name="Framework" value={scoped(assignedVersion ? `${frameworkName} ${assignedVersion.versionLabel}` : 'Not assigned')} />
                <Fact name="Catalog hash" mono value={scoped(assignedVersion?.sourceHash || 'Not available')} />
                <Fact name="Evidence period" value={scoped(evidencePeriod)} />
              </dl>
            </section>
            {!loading && !error && activeAssignment && assignedVersion && (
              <section aria-label={`${frameworkName} readiness summary`} className="mt-4 border-t border-[var(--fm-line)] pt-4">
                <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-3">
                  <div>
                    <dt className={LABEL}>Accepted controls</dt>
                    <dd className="mt-0.5 text-[22px] font-semibold tabular-nums">
                      {readiness ? `${readiness.accepted} of ${readiness.applicable}` : 'Unknown'}
                    </dd>
                  </div>
                  <div>
                    <dt className={LABEL}>Ready for review</dt>
                    <dd className="mt-0.5 flex flex-wrap items-center gap-2 text-[22px] font-semibold tabular-nums">
                      {readiness?.readyForReview ?? 'Unknown'}
                      {(readiness?.readyForReview ?? 0) > 0 && <Pill tone="you" dot>Needs a reviewer</Pill>}
                    </dd>
                  </div>
                  <div>
                    <dt className={LABEL}>Missing accepted evidence</dt>
                    <dd className="mt-0.5 text-[22px] font-semibold tabular-nums">{readiness?.missingEvidence ?? 'Unknown'}</dd>
                  </div>
                </dl>
              </section>
            )}
          </div>

          {error ? (
            <ErrorNote message={`Could not load the assurance summary. ${error.message}`} onRetry={() => void refresh()} />
          ) : loading ? (
            <Loading label="Loading assurance report" />
          ) : !activeAssignment || !assignedVersion ? (
            <section className="fm-card grid content-start justify-items-start gap-3 p-6">
              <h2 className="text-[15px] font-semibold">No version-pinned scope</h2>
              <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
                Assign a framework version to {selectedSystem.name} before preparing an assurance summary. Until then readiness is unknown, not zero.
              </p>
              {!auditorMode && <Link href="/compliance-dashboard" className={BTN_P}>Assign framework scope</Link>}
            </section>
          ) : (
            <>
              <div className="grid gap-4 xl:grid-cols-2">
                <section aria-label="Evidence index" className="fm-card p-5">
                  <h2 className="text-[15px] font-semibold">Evidence index</h2>
                  <p className={sub}>Every run in scope, newest first, with its content hash.</p>
                  {runsNewestFirst.length === 0 ? (
                    <p className={`mt-3 ${row} text-[13px] ${MUTED}`}>No evidence runs are recorded for this AI system.</p>
                  ) : (
                    <ol className="mt-3">
                      {runsNewestFirst.map((run) => (
                        <li key={run.id} className={row}>
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <p className="text-[13.5px] font-semibold">{run.suiteName || run.sourceIdentifier}</p>
                            <Pill>{run.assuranceSource?.replace(/_/g, ' ') || 'Source unknown'}</Pill>
                          </div>
                          <p className={`mt-0.5 text-[12px] ${MUTED}`}>
                            {run.sourceIdentifier} · {run.result.replace(/_/g, ' ')} · run {run.runId} · captured {formatDate(run.capturedAt)}
                          </p>
                          <p className="mt-1 break-all font-mono text-[11.5px]">{run.contentHash}</p>
                          <p className={`mt-1 text-[12px] ${MUTED}`}>
                            Subject {run.subjectVersion || 'not recorded'} · Suite {run.suiteVersion || 'not recorded'} · Runner {run.runnerVersion || 'not recorded'}
                          </p>
                        </li>
                      ))}
                    </ol>
                  )}
                </section>

                <section aria-label="Unresolved findings" className="fm-card p-5">
                  <h2 className="text-[15px] font-semibold">Unresolved findings</h2>
                  <p className={sub}>Counts appear only when the framework assessment reports them.</p>
                  <p className={`mt-3 text-[28px] font-semibold tabular-nums ${readiness && readiness.blockingFindings > 0 ? 'text-[#b42318]' : ''}`}>
                    {readiness?.blockingFindings ?? 'Unknown'}
                  </p>
                  <p className="text-[13px] font-medium">
                    {readiness ? countLabel(readiness.blockingFindings, 'rejected assessment') : 'Rejected assessment count unavailable'}
                  </p>
                  <div className={`mt-4 ${row}`}>
                    <p className={LABEL}>Control-linked detail</p>
                    <p className="mt-0.5 text-[13px]">
                      {controlFindingsIncomplete
                        ? `${knownControlFindings} known; at least one control does not report a finding count.`
                        : countLabel(knownControlFindings, 'open control finding')}
                    </p>
                  </div>
                </section>

                <section aria-label="Decision register" className="fm-card p-5">
                  <h2 className="text-[15px] font-semibold">Decision register</h2>
                  <p className={sub}>Recorded mapping reviews. Candidate suggestions are not decisions.</p>
                  {reviewedMappings.length === 0 ? (
                    <p className={`mt-3 ${row} text-[13px] ${MUTED}`}>No accepted or rejected mapping decisions are recorded.</p>
                  ) : (
                    <ol className="mt-3">
                      {reviewedMappings.map((mapping) => {
                        const review = latestReview(mapping)
                        const control = controlById.get(mapping.controlAssessmentId)
                        return (
                          <li key={mapping.id} className={row}>
                            <div className="flex flex-wrap items-center gap-2">
                              <Pill tone={mapping.state === 'accepted' ? 'done' : 'block'}>
                                {mapping.state === 'accepted' ? 'Accepted' : 'Rejected'}
                              </Pill>
                              <p className="text-[13.5px] font-semibold">{control ? `${control.externalId} ${control.title}` : 'Control reference unavailable'}</p>
                            </div>
                            <p className="mt-1.5 text-[13px]">{review?.rationale || mapping.rationale || 'No rationale recorded.'}</p>
                            <p className={`mt-1 text-[12px] ${MUTED}`}>Reviewed by {review?.reviewedBy || 'identity unavailable'} · {formatDate(review?.reviewedAt || null)}</p>
                          </li>
                        )
                      })}
                    </ol>
                  )}
                </section>

                <section aria-label="Limitations" className="fm-card p-5">
                  <h2 className="text-[15px] font-semibold">Limitations</h2>
                  <p className={sub}>Known evaluation and assurance limits stay part of the report.</p>
                  <ul className="mt-3 text-[13px]">
                    {limitations.length > 0 ? limitations.map((limitation) => (
                      <li key={limitation} className={row}>{limitation}</li>
                    )) : (
                      <li className={`${row} ${MUTED}`}>
                        {assurance.evidenceRuns.length === 0
                          ? 'No evidence runs are in scope, so evaluation limitations are unknown.'
                          : 'No evaluation limitations were recorded in the in-scope runs.'}
                      </li>
                    )}
                    <li className={`${row} ${MUTED}`}>This summary supports readiness review. It is not an official certification or an assurance opinion.</li>
                  </ul>
                </section>
              </div>

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
                readOnly={auditorMode}
              />

              {!auditorMode && (
                <nav aria-label="Assurance builder actions" className="flex flex-wrap gap-2.5">
                  <Link href="/compliance-dashboard" className={BTN_P}>Review control assessments</Link>
                  <Link href="/evidence?view=evaluations" className={BTN}>Review evidence mappings</Link>
                </nav>
              )}
            </>
          )}
        </>
      )}
    </main>
  )
}

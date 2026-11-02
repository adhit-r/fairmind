'use client'

import type {
  ControlAssessment,
  EvidenceMapping,
  EvidenceMappingReviewInput,
  EvidenceRun,
} from '@/lib/api/hooks/useGovernanceAssurance'
import { evidenceRunDisplayName } from '@/lib/api/hooks/useGovernanceAssurance'

import { EvidenceMappingReview } from './EvidenceMappingReview'

type EvaluationRunListProps = {
  runs: EvidenceRun[]
  controls: ControlAssessment[]
  loading: boolean
  error: Error | null
  canReview: boolean
  onReview: (mappingId: string, review: EvidenceMappingReviewInput) => Promise<EvidenceMapping>
  onRefresh: () => Promise<void>
}

function readable(value: string) {
  return value.replaceAll('_', ' ')
}

function formatCaptured(value: string | null) {
  if (!value) return 'Capture time unavailable'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function RunLoading() {
  return (
    <div aria-label="Loading evaluation runs" className="space-y-3">
      {[0, 1].map((item) => (
        <div key={item} className="h-48 animate-pulse border border-[var(--fm-line)] bg-[#E6EAE5]" />
      ))}
    </div>
  )
}

export function EvaluationRunList({ runs, controls, loading, error, canReview, onReview, onRefresh }: EvaluationRunListProps) {
  const controlsByAssessment = new Map(controls.map((control) => [control.id, control]))

  if (loading && runs.length === 0) return <RunLoading />

  if (error) {
    return (
      <div role="alert" className="border-4 border-[#B3261E] bg-[#FFF0ED] p-5">
        <h2 className="font-semibold">Evaluation runs could not be loaded</h2>
        <p className="mt-1 text-sm">{error.message}</p>
        <button type="button" onClick={() => void onRefresh()} className="mt-4 min-h-11 px-4 font-semibold fm-card">
          Retry
        </button>
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="border border-dashed border-[var(--fm-line)] bg-[var(--fm-bg)] p-10 text-center">
        <h2 className="text-lg font-semibold">No evaluation evidence captured</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm text-[var(--fm-ink2)]">
          Completed FairMind evaluations and company integration runs will appear here with immutable provenance.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {runs.map((run) => {
        const name = evidenceRunDisplayName(run)
        return (
          <article
            key={run.id}
            aria-label={`Evaluation run ${name}`}
            className="fm-card"
          >
            <header className="flex flex-col gap-3 border-b border-[var(--fm-line)] bg-[#DDF4EA] p-5 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#0B7659]">Completed evaluation evidence</p>
                <h2 className="mt-1 text-xl font-semibold">{name}</h2>
                <p className="mt-1 text-sm font-bold">
                  {run.sourceIdentifier} · {readable(run.sourceType)}{run.suiteVersion ? ` · suite ${run.suiteVersion}` : ''}
                </p>
              </div>
              <span className="w-fit border border-[var(--fm-line)] bg-white px-3 py-1.5 text-sm font-semibold">
                {readable(run.result)}
              </span>
            </header>

            <div className="space-y-5 p-5">
              <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="border border-[var(--fm-line)] bg-[var(--fm-bg)] p-3">
                  <dt className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">System version</dt>
                  <dd className="mt-1 text-sm font-semibold">System version {run.subjectVersion || 'not supplied'}</dd>
                </div>
                <div className="border border-[var(--fm-line)] bg-[var(--fm-bg)] p-3">
                  <dt className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Runner</dt>
                  <dd className="mt-1 text-sm font-semibold">Runner version {run.runnerVersion || 'not supplied'}</dd>
                </div>
                <div className="border border-[var(--fm-line)] bg-[var(--fm-bg)] p-3">
                  <dt className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Captured</dt>
                  <dd className="mt-1 text-sm font-semibold">Captured {formatCaptured(run.capturedAt)}</dd>
                </div>
                <div className="border border-[var(--fm-line)] bg-[var(--fm-bg)] p-3">
                  <dt className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Assurance source</dt>
                  <dd className="mt-1 text-sm font-semibold">{run.assuranceSource ? readable(run.assuranceSource) : 'Not supplied'}</dd>
                </div>
              </dl>

              <section aria-label="Evaluation limitations" className="border-l-4 border-[#E76F2E] bg-[#FFF4DE] p-4">
                <h3 className="text-xs font-semibold uppercase tracking-[0.1em]">Limitations</h3>
                {(run.limitations ?? []).length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {(run.limitations ?? []).map((limitation) => <li key={limitation}>{limitation}</li>)}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-[var(--fm-ink2)]">No limitations were supplied with this run.</p>
                )}
              </section>

              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--fm-ink2)]">Content hash</p>
                <code className="mt-1 block break-all border border-[var(--fm-line)] bg-[var(--fm-ink)] p-3 text-xs text-white">{run.contentHash}</code>
              </div>

              <section aria-label="Control mapping reviews" className="space-y-3 border-t border-[var(--fm-line)] pt-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-semibold">Control mapping reviews</h3>
                  <span className="text-sm font-bold text-[var(--fm-ink2)]">{run.candidateMappings.length} mapping{run.candidateMappings.length === 1 ? '' : 's'}</span>
                </div>
                {run.candidateMappings.length > 0 ? run.candidateMappings.map((mapping) => (
                  <EvidenceMappingReview
                    key={mapping.id}
                    mapping={mapping}
                    control={controlsByAssessment.get(mapping.controlAssessmentId)}
                    canReview={canReview}
                    onReview={onReview}
                    onRefresh={onRefresh}
                  />
                )) : (
                  <p className="border border-dashed border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 text-sm text-[var(--fm-ink2)]">
                    No control mappings were suggested for this run.
                  </p>
                )}
              </section>
            </div>
          </article>
        )
      })}
    </div>
  )
}

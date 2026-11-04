'use client'

import type {
  ControlAssessment,
  EvidenceMapping,
  EvidenceMappingReviewInput,
  EvidenceRun,
} from '@/lib/api/hooks/useGovernanceAssurance'
import { evidenceRunDisplayName } from '@/lib/api/hooks/useGovernanceAssurance'

import { BTN, LABEL, MUTED, Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

import { EvidenceMappingReview } from './EvidenceMappingReview'

type EvaluationRunListProps = {
  runs: EvidenceRun[]
  controls: ControlAssessment[]
  loading: boolean
  error: Error | null
  /** null while the role is still loading. */
  canReview: boolean | null
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
        <div key={item} className="h-48 animate-pulse rounded-[14px] bg-black/5" />
      ))}
    </div>
  )
}

export function EvaluationRunList({ runs, controls, loading, error, canReview, onReview, onRefresh }: EvaluationRunListProps) {
  const controlsByAssessment = new Map(controls.map((control) => [control.id, control]))

  if (loading && runs.length === 0) return <RunLoading />

  if (error) {
    return (
      <div role="alert" className="rounded-xl bg-[#fde8e8] p-5 text-[#b42318]">
        <h2 className="m-0 text-[15px] font-semibold">Evaluation runs could not be loaded</h2>
        <p className="mt-1 text-[13px]">{error.message}</p>
        <button type="button" onClick={() => void onRefresh()} className={cn(BTN, 'mt-4 h-9 px-4 text-[12.5px]')}>
          Retry
        </button>
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <section className="fm-card grid min-h-[240px] place-items-center p-9 text-center">
        <div className="max-w-md">
          <h2 className="m-0 text-[20px] font-semibold tracking-tight">No evaluation evidence captured</h2>
          <p className={cn('mt-3 text-[14.5px] leading-[1.55]', MUTED)}>
            Completed FairMind evaluations and company integration runs will appear here with immutable provenance.
          </p>
        </div>
      </section>
    )
  }

  return (
    <div className="grid gap-4">
      {runs.map((run) => {
        const name = evidenceRunDisplayName(run)
        return (
          <article
            key={run.id}
            aria-label={`Evaluation run ${name}`}
            className="fm-card"
          >
            <header className="flex flex-col gap-3 border-b border-[var(--fm-line)] p-5 md:flex-row md:items-start md:justify-between">
              <div>
                <p className={cn('m-0', LABEL)}>Completed evaluation evidence</p>
                <h2 className="mt-1.5 text-[18px] font-semibold tracking-tight">{name}</h2>
                <p className={cn('mt-1 text-[13px]', MUTED)}>
                  {run.sourceIdentifier} · {readable(run.sourceType)}{run.suiteVersion ? ` · suite ${run.suiteVersion}` : ''}
                </p>
              </div>
              <Pill>{readable(run.result)}</Pill>
            </header>

            <div className="grid gap-5 p-5">
              <dl className="m-0 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                  <dt className={LABEL}>System version</dt>
                  <dd className="m-0 mt-1 text-[13.5px] font-semibold">System version {run.subjectVersion || 'not supplied'}</dd>
                </div>
                <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                  <dt className={LABEL}>Runner</dt>
                  <dd className="m-0 mt-1 text-[13.5px] font-semibold">Runner version {run.runnerVersion || 'not supplied'}</dd>
                </div>
                <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                  <dt className={LABEL}>Captured</dt>
                  <dd className="m-0 mt-1 text-[13.5px] font-semibold">Captured {formatCaptured(run.capturedAt)}</dd>
                </div>
                <div className="rounded-xl bg-[var(--fm-bg)] p-3.5">
                  <dt className={LABEL}>Assurance source</dt>
                  <dd className="m-0 mt-1 text-[13.5px] font-semibold">{run.assuranceSource ? readable(run.assuranceSource) : 'Not supplied'}</dd>
                </div>
              </dl>

              <section aria-label="Evaluation limitations" className={cn((run.limitations ?? []).length > 0 && 'rounded-xl bg-[#fff4d6] p-4')}>
                <h3 className={cn('m-0', LABEL)}>Limitations</h3>
                {(run.limitations ?? []).length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-[13.5px]">
                    {(run.limitations ?? []).map((limitation) => <li key={limitation}>{limitation}</li>)}
                  </ul>
                ) : (
                  <p className={cn('mt-2 text-[13.5px]', MUTED)}>No limitations were supplied with this run.</p>
                )}
              </section>

              <div>
                <p className={cn('m-0', LABEL)}>Content hash</p>
                <code className="mt-1.5 block break-all rounded-xl bg-[var(--fm-bg)] p-3 text-[12px]">{run.contentHash}</code>
              </div>

              <section aria-label="Control mapping reviews" className="grid gap-3 border-t border-[var(--fm-line)] pt-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="m-0 text-[15px] font-semibold">Control mapping reviews</h3>
                  <span className={cn('text-[12.5px] tabular-nums', MUTED)}>{run.candidateMappings.length} mapping{run.candidateMappings.length === 1 ? '' : 's'}</span>
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
                  <p className={cn('m-0 rounded-xl border border-dashed border-[rgba(21,23,26,.16)] px-4 py-5 text-center text-[13px]', MUTED)}>
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

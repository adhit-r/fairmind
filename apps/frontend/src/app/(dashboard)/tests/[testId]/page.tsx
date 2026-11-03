'use client'

import { use, useEffect, useMemo, useState } from 'react'
import { IconArrowLeft, IconLink, IconShieldCheck } from '@tabler/icons-react'

import { FramedIcon } from '@/components/ui/FramedIcon'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import {
  StaleEvaluationResultError,
  useEvaluationRuns,
  type EvaluationLayerVerdicts,
  type EvaluationPlan,
  type EvaluationRun,
  type GovernanceVerdict,
} from '@/lib/api/hooks/useEvaluationRuns'

interface PageProps {
  params: Promise<{ testId: string }>
}
const verdictLabels: Record<GovernanceVerdict, string> = {
  approved: 'Approved',
  conditional: 'Conditional',
  review: 'Review',
  blocked: 'Blocked',
  insufficient: 'Insufficient',
}

function sentenceLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/^./, (character) => character.toUpperCase())
}

function timestampLabel(value: string | null) {
  if (!value) return 'Not recorded'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function verdictClass(verdict: GovernanceVerdict) {
  if (verdict === 'blocked') return 'border-[#D83A2E] bg-[#D83A2E] text-white'
  if (verdict === 'approved') return 'border-[#155D46] bg-[#DFF4EA] text-[#155D46]'
  if (verdict === 'conditional') return 'border-[#9A5B14] bg-[#FFF1D6] text-[#73420B]'
  if (verdict === 'review') return 'border-[var(--fm-line)] bg-[#FF6B35] text-[var(--fm-ink)]'
  return 'border-[rgba(21,23,26,.14)] bg-[var(--fm-bg)] text-[var(--fm-ink2)]'
}

function VerdictLabel({ verdict }: { verdict: GovernanceVerdict }) {
  return (
    <span className={`inline-flex min-h-8 items-center border-2 px-2.5 py-1 text-xs font-semibold uppercase ${verdictClass(verdict)}`}>
      {verdictLabels[verdict]}
    </span>
  )
}

function LayerAxis({
  label,
  verdicts,
}: {
  label: string
  verdicts: Record<string, GovernanceVerdict> | undefined
}) {
  const entries = Object.entries(verdicts ?? {})
  return (
    <section role="region" aria-label={label} className="border border-[var(--fm-line)] bg-white">
      <h2 className="border-b border-[var(--fm-line)] bg-[var(--fm-bg)] px-4 py-3 text-base font-semibold">{label}</h2>
      {entries.length === 0 ? (
        <p className="p-4 text-sm font-bold text-[var(--fm-ink2)]">Not assessed</p>
      ) : (
        <dl className="divide-y-2 divide-[var(--fm-line)]">
          {entries.map(([name, verdict]) => (
            <div key={name} className="flex min-h-14 items-center justify-between gap-3 px-4 py-2">
              <dt className="font-bold">{sentenceLabel(name)}</dt>
              <dd><VerdictLabel verdict={verdict} /></dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}

function RunScope({ run, plan }: { run: EvaluationRun; plan?: EvaluationPlan }) {
  return (
    <dl className="grid grid-cols-2 border border-[var(--fm-line)] bg-[var(--fm-bg)] text-sm lg:grid-cols-4">
      <div className="border-b border-[var(--fm-line)] p-3 lg:border-b-0 lg:border-r-2">
        <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Run ID</dt>
        <dd className="mt-1 break-all font-mono text-xs font-bold">{run.id}</dd>
      </div>
      <div className="border-b border-l border-[var(--fm-line)] p-3 lg:border-b-0 lg:border-l-0 lg:border-r-2">
        <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Plan</dt>
        <dd className="mt-1 font-bold">{plan?.name ?? run.planId}</dd>
      </div>
      <div className="border-r border-[var(--fm-line)] p-3">
        <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Target</dt>
        <dd className="mt-1 font-bold">{plan ? sentenceLabel(plan.targetKind) : 'Plan metadata unavailable'}</dd>
      </div>
      <div className="p-3">
        <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Trigger</dt>
        <dd className="mt-1 font-bold">{sentenceLabel(run.trigger)}</dd>
      </div>
    </dl>
  )
}

export default function EvaluationRunDetailPage({ params }: PageProps) {
  const { testId } = use(params)
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const { selectedSystem, loading: systemLoading } = useSystemContext()
  const realSystem = selectedSystem.metadata?.source === 'fallback' ? undefined : selectedSystem
  const evaluations = useEvaluationRuns(selectedOrg?.id, realSystem?.id)
  const scopeKey = [selectedOrg?.id ?? '', realSystem?.id ?? '', testId].join(':')
  const [runState, setRunState] = useState<{ scopeKey: string; run: EvaluationRun | null }>({
    scopeKey,
    run: null,
  })
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<Error | null>(null)

  // Mask a previous organization's/system's run synchronously on route or
  // scope changes; the fetch effect below cannot provide that guarantee.
  const run = runState.scopeKey === scopeKey ? runState.run : null

  useEffect(() => {
    let current = true
    setRunState({ scopeKey, run: null })
    setDetailError(null)
    if (!selectedOrg?.id || !realSystem?.id) return () => { current = false }

    setDetailLoading(true)
    void evaluations.getRun(testId)
      .then((result) => {
        if (current) setRunState({ scopeKey, run: result })
      })
      .catch((reason) => {
        if (!current || reason instanceof StaleEvaluationResultError) return
        setDetailError(reason instanceof Error ? reason : new Error('Unable to load evaluation run.'))
      })
      .finally(() => {
        if (current) setDetailLoading(false)
      })
    return () => { current = false }
  }, [evaluations.getRun, realSystem?.id, scopeKey, selectedOrg?.id, testId])

  const plan = useMemo(
    () => evaluations.plans.find((candidate) => candidate.id === run?.planId),
    [evaluations.plans, run?.planId],
  )
  const initialLoading = orgLoading || systemLoading || detailLoading || (!run && evaluations.loading)

  return (
    <div className="mx-auto w-full max-w-[1320px] space-y-5 text-[var(--fm-ink)]">
      <header className="border-b border-[var(--fm-line)] pb-4 pt-1">
        <FramedIcon
          href="/tests"
          icon={IconArrowLeft}
          label="Back to Evaluation Runs"
          text="Back to Evaluation Runs"
          className="mb-4 w-auto"
        />
        <div className="flex items-start gap-3">
          <span aria-hidden="true" className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center bg-[#FF6B35] rounded-[14px] shadow-[var(--fm-shadow)]">
            <IconShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <h1 className="text-3xl font-semibold tracking-[-0.02em]">Evaluation run</h1>
            <p className="mt-1 break-all font-mono text-xs font-bold text-[var(--fm-ink2)]">{testId}</p>
          </div>
        </div>
      </header>

      {!selectedOrg && !initialLoading ? (
        <section className="border border-[var(--fm-line)] bg-white p-6">
          <h2 className="text-xl font-semibold">Choose an organization</h2>
          <p className="mt-2 text-sm font-semibold text-[var(--fm-ink2)]">An organization is required before this scoped run can be retrieved.</p>
        </section>
      ) : !realSystem && !initialLoading ? (
        <section className="border border-[var(--fm-line)] bg-white p-6">
          <h2 className="text-xl font-semibold">Choose an AI system</h2>
          <p className="mt-2 text-sm font-semibold text-[var(--fm-ink2)]">A real selected system is required before this run can be retrieved.</p>
        </section>
      ) : initialLoading ? (
        <section aria-label="Loading evaluation run" className="space-y-3 border border-[var(--fm-line)] bg-white p-6">
          <div className="h-11 w-full animate-pulse bg-[var(--fm-bg)] motion-reduce:animate-none" />
          <div className="h-28 w-full animate-pulse bg-[var(--fm-bg)] motion-reduce:animate-none" />
          <div className="h-40 w-full animate-pulse bg-[var(--fm-bg)] motion-reduce:animate-none" />
        </section>
      ) : detailError || !run ? (
        <section role="alert" className="border-4 border-[#D83A2E] bg-red-50 p-6">
          <h2 className="text-xl font-semibold text-[#8F2019]">Evaluation run unavailable</h2>
          <p className="mt-2 text-sm font-semibold text-[#5B211D]">{detailError?.message ?? 'The scoped run could not be found.'}</p>
        </section>
      ) : (
        <main className="space-y-5">
          <section aria-label="Run decision state" className="border border-[var(--fm-line)] bg-white">
            <div className="grid divide-y-4 divide-[var(--fm-line)] sm:grid-cols-2 sm:divide-x-4 sm:divide-y-0">
              <div className="p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fm-ink2)]">Technical status</p>
                <p className="mt-2 inline-flex min-h-8 items-center border border-[var(--fm-line)] bg-[var(--fm-ink)] px-2.5 py-1 text-xs font-semibold uppercase text-white">
                  {sentenceLabel(run.technicalStatus)}
                </p>
                <p className="mt-2 text-sm font-semibold text-[var(--fm-ink2)]">Execution lifecycle only. This does not express governance acceptance.</p>
              </div>
              <div className="p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fm-ink2)]">Governance verdict</p>
                <div className="mt-2"><VerdictLabel verdict={run.overallVerdict} /></div>
                <p className="mt-2 text-sm font-semibold text-[var(--fm-ink2)]">Reviewer-facing judgment based only on available evidence.</p>
              </div>
            </div>
          </section>

          <RunScope run={run} plan={plan} />

          {plan && (
            <section aria-labelledby="run-plan-metadata" className="border border-[var(--fm-line)] bg-white p-4">
              <h2 id="run-plan-metadata" className="text-base font-semibold">Plan metadata</h2>
              <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Lifecycle phases</dt><dd className="mt-1 font-bold">{plan.lifecyclePhases.map(sentenceLabel).join(', ')}</dd></div>
                <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Execution depth</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.executionDepth)}</dd></div>
                <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Enforcement</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.enforcementMode)}</dd></div>
                <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Delivery</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.deliveryMode)}</dd></div>
                <div className="sm:col-span-2 lg:col-span-4"><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Versioned suites</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{plan.suiteRefs.join(', ')}</dd></div>
              </dl>
            </section>
          )}

          <div className="grid gap-5 lg:grid-cols-2">
            <LayerAxis
              label="Component layer verdicts"
              verdicts={run.layerVerdicts.components as EvaluationLayerVerdicts['components']}
            />
            <LayerAxis
              label="Risk dimension verdicts"
              verdicts={run.layerVerdicts.dimensions as EvaluationLayerVerdicts['dimensions']}
            />
          </div>

          <section aria-labelledby="passport-linkage-heading" className="border border-[var(--fm-line)] bg-white p-4">
            <div className="flex items-start gap-3">
              <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center border border-[var(--fm-line)] bg-[var(--fm-bg)]">
                <IconLink className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 id="passport-linkage-heading" className="text-lg font-semibold">Evidence Passport linkage</h2>
                {run.linkedEvidenceRunId && run.linkedPassportRevisionId ? (
                  <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Evidence run ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedEvidenceRunId}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Passport revision ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedPassportRevisionId}</dd>
                    </div>
                    <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Linked at</dt><dd className="mt-1 font-bold">{timestampLabel(run.linkedAt)}</dd></div>
                    <div><dt className="text-xs font-semibold uppercase text-[var(--fm-ink2)]">Linked by</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedBy}</dd></div>
                  </dl>
                ) : (
                  <div className="mt-3 border-2 border-[rgba(21,23,26,.14)] bg-[var(--fm-bg)] p-3">
                    <p className="font-semibold">Awaiting evidence</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--fm-ink2)]">No Evidence Passport revision is linked. FairMind does not invent artifacts or layer findings.</p>
                  </div>
                )}
              </div>
            </div>
          </section>

          {(run.failureCode || run.failureMessage) && (
            <section role="alert" className="border-4 border-[#D83A2E] bg-red-50 p-4">
              <h2 className="font-semibold text-[#8F2019]">Execution failure</h2>
              {run.failureCode && <p className="mt-1 font-mono text-xs font-bold text-[#5B211D]">{run.failureCode}</p>}
              {run.failureMessage && <p className="mt-2 text-sm font-semibold text-[#5B211D]">{run.failureMessage}</p>}
            </section>
          )}
        </main>
      )}
    </div>
  )
}

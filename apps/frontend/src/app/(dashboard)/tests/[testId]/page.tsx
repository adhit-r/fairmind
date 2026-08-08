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
  if (verdict === 'review') return 'border-[#0F1412] bg-[#FF6B35] text-[#0F1412]'
  return 'border-[#59615D] bg-[#F3F5F0] text-[#303834]'
}

function VerdictLabel({ verdict }: { verdict: GovernanceVerdict }) {
  return (
    <span className={`inline-flex min-h-8 items-center border-2 px-2.5 py-1 text-xs font-black uppercase ${verdictClass(verdict)}`}>
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
    <section role="region" aria-label={label} className="border-2 border-[#0F1412] bg-[#FCFDF8]">
      <h2 className="border-b-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-3 text-base font-black">{label}</h2>
      {entries.length === 0 ? (
        <p className="p-4 text-sm font-bold text-[#59615D]">Not assessed</p>
      ) : (
        <dl className="divide-y-2 divide-[#0F1412]">
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
    <dl className="grid grid-cols-2 border-2 border-[#0F1412] bg-[#F3F5F0] text-sm lg:grid-cols-4">
      <div className="border-b-2 border-[#0F1412] p-3 lg:border-b-0 lg:border-r-2">
        <dt className="text-xs font-black uppercase text-[#59615D]">Run ID</dt>
        <dd className="mt-1 break-all font-mono text-xs font-bold">{run.id}</dd>
      </div>
      <div className="border-b-2 border-l-2 border-[#0F1412] p-3 lg:border-b-0 lg:border-l-0 lg:border-r-2">
        <dt className="text-xs font-black uppercase text-[#59615D]">Plan</dt>
        <dd className="mt-1 font-bold">{plan?.name ?? run.planId}</dd>
      </div>
      <div className="border-r-2 border-[#0F1412] p-3">
        <dt className="text-xs font-black uppercase text-[#59615D]">Target</dt>
        <dd className="mt-1 font-bold">{plan ? sentenceLabel(plan.targetKind) : 'Plan metadata unavailable'}</dd>
      </div>
      <div className="p-3">
        <dt className="text-xs font-black uppercase text-[#59615D]">Trigger</dt>
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
  const [run, setRun] = useState<EvaluationRun | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<Error | null>(null)

  useEffect(() => {
    let current = true
    setRun(null)
    setDetailError(null)
    if (!selectedOrg?.id || !realSystem?.id) return () => { current = false }

    setDetailLoading(true)
    void evaluations.getRun(testId)
      .then((result) => {
        if (current) setRun(result)
      })
      .catch((reason) => {
        if (!current || reason instanceof StaleEvaluationResultError) return
        setDetailError(reason instanceof Error ? reason : new Error('Unable to load evaluation run.'))
      })
      .finally(() => {
        if (current) setDetailLoading(false)
      })
    return () => { current = false }
  }, [evaluations.getRun, realSystem?.id, selectedOrg?.id, testId])

  const plan = useMemo(
    () => evaluations.plans.find((candidate) => candidate.id === run?.planId),
    [evaluations.plans, run?.planId],
  )
  const initialLoading = orgLoading || systemLoading || detailLoading || (!run && evaluations.loading)

  return (
    <div className="mx-auto w-full max-w-[1320px] space-y-5 text-[#0F1412]">
      <header className="border-b-4 border-[#0F1412] pb-4 pt-1">
        <FramedIcon
          href="/tests"
          icon={IconArrowLeft}
          label="Back to Evaluation Runs"
          text="Back to Evaluation Runs"
          className="mb-4 w-auto"
        />
        <div className="flex items-start gap-3">
          <span aria-hidden="true" className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center border-2 border-[#0F1412] bg-[#FF6B35] shadow-[3px_3px_0_0_#0F1412]">
            <IconShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <h1 className="text-3xl font-black tracking-[-0.02em]">Evaluation run</h1>
            <p className="mt-1 break-all font-mono text-xs font-bold text-[#59615D]">{testId}</p>
          </div>
        </div>
      </header>

      {!selectedOrg && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an organization</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">An organization is required before this scoped run can be retrieved.</p>
        </section>
      ) : !realSystem && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an AI system</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">A real selected system is required before this run can be retrieved.</p>
        </section>
      ) : initialLoading ? (
        <section aria-label="Loading evaluation run" className="space-y-3 border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <div className="h-11 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
          <div className="h-28 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
          <div className="h-40 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
        </section>
      ) : detailError || !run ? (
        <section role="alert" className="border-4 border-[#D83A2E] bg-red-50 p-6">
          <h2 className="text-xl font-black text-[#8F2019]">Evaluation run unavailable</h2>
          <p className="mt-2 text-sm font-semibold text-[#5B211D]">{detailError?.message ?? 'The scoped run could not be found.'}</p>
        </section>
      ) : (
        <main className="space-y-5">
          <section aria-label="Run decision state" className="border-4 border-[#0F1412] bg-[#FCFDF8]">
            <div className="grid divide-y-4 divide-[#0F1412] sm:grid-cols-2 sm:divide-x-4 sm:divide-y-0">
              <div className="p-4">
                <p className="text-xs font-black uppercase tracking-wide text-[#59615D]">Technical status</p>
                <p className="mt-2 inline-flex min-h-8 items-center border-2 border-[#0F1412] bg-[#0F1412] px-2.5 py-1 text-xs font-black uppercase text-white">
                  {sentenceLabel(run.technicalStatus)}
                </p>
                <p className="mt-2 text-sm font-semibold text-[#59615D]">Execution lifecycle only. This does not express governance acceptance.</p>
              </div>
              <div className="p-4">
                <p className="text-xs font-black uppercase tracking-wide text-[#59615D]">Governance verdict</p>
                <div className="mt-2"><VerdictLabel verdict={run.overallVerdict} /></div>
                <p className="mt-2 text-sm font-semibold text-[#59615D]">Reviewer-facing judgment based only on available evidence.</p>
              </div>
            </div>
          </section>

          <RunScope run={run} plan={plan} />

          {plan && (
            <section aria-labelledby="run-plan-metadata" className="border-2 border-[#0F1412] bg-[#FCFDF8] p-4">
              <h2 id="run-plan-metadata" className="text-base font-black">Plan metadata</h2>
              <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div><dt className="text-xs font-black uppercase text-[#59615D]">Lifecycle phases</dt><dd className="mt-1 font-bold">{plan.lifecyclePhases.map(sentenceLabel).join(', ')}</dd></div>
                <div><dt className="text-xs font-black uppercase text-[#59615D]">Execution depth</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.executionDepth)}</dd></div>
                <div><dt className="text-xs font-black uppercase text-[#59615D]">Enforcement</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.enforcementMode)}</dd></div>
                <div><dt className="text-xs font-black uppercase text-[#59615D]">Delivery</dt><dd className="mt-1 font-bold">{sentenceLabel(plan.deliveryMode)}</dd></div>
                <div className="sm:col-span-2 lg:col-span-4"><dt className="text-xs font-black uppercase text-[#59615D]">Versioned suites</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{plan.suiteRefs.join(', ')}</dd></div>
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

          <section aria-labelledby="passport-linkage-heading" className="border-4 border-[#0F1412] bg-[#FCFDF8] p-4">
            <div className="flex items-start gap-3">
              <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center border-2 border-[#0F1412] bg-[#F3F5F0]">
                <IconLink className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 id="passport-linkage-heading" className="text-lg font-black">Evidence Passport linkage</h2>
                {run.linkedEvidenceRunId && run.linkedPassportRevisionId ? (
                  <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs font-black uppercase text-[#59615D]">Evidence run ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedEvidenceRunId}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-black uppercase text-[#59615D]">Passport revision ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedPassportRevisionId}</dd>
                    </div>
                    <div><dt className="text-xs font-black uppercase text-[#59615D]">Linked at</dt><dd className="mt-1 font-bold">{timestampLabel(run.linkedAt)}</dd></div>
                    <div><dt className="text-xs font-black uppercase text-[#59615D]">Linked by</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{run.linkedBy}</dd></div>
                  </dl>
                ) : (
                  <div className="mt-3 border-2 border-[#59615D] bg-[#F3F5F0] p-3">
                    <p className="font-black">Awaiting evidence</p>
                    <p className="mt-1 text-sm font-semibold text-[#59615D]">No Evidence Passport revision is linked. FairMind does not invent artifacts or layer findings.</p>
                  </div>
                )}
              </div>
            </div>
          </section>

          {(run.failureCode || run.failureMessage) && (
            <section role="alert" className="border-4 border-[#D83A2E] bg-red-50 p-4">
              <h2 className="font-black text-[#8F2019]">Execution failure</h2>
              {run.failureCode && <p className="mt-1 font-mono text-xs font-bold text-[#5B211D]">{run.failureCode}</p>}
              {run.failureMessage && <p className="mt-2 text-sm font-semibold text-[#5B211D]">{run.failureMessage}</p>}
            </section>
          )}
        </main>
      )}
    </div>
  )
}

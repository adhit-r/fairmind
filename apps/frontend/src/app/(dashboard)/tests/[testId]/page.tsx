'use client'

import Link from 'next/link'
import { use, useEffect, useMemo, useState, type ReactNode } from 'react'

import { LABEL, MUTED } from '@/components/packs/parts'
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
import {
  evaluationScopeKey,
  readEvaluationScopeState,
  type EvaluationScopeState,
} from '@/lib/evaluation-scope-state'
import { TechnicalStatusPill, VerdictPill } from '../pills'

interface PageProps {
  params: Promise<{ testId: string }>
}

type RunDetailState = {
  run: EvaluationRun | null
  loading: boolean
  error: Error | null
}

const sub = `mt-1.5 text-[12.5px] ${MUTED}`
const mono = 'break-all font-mono text-[12px]'

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

function Fact({ name, children, className }: { name: string; children: ReactNode; className?: string }) {
  return (
    <div className={`min-w-0 ${className ?? ''}`}>
      <dt className={LABEL}>{name}</dt>
      <dd className="mt-0.5 text-[13.5px]">{children}</dd>
    </div>
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
    <section role="region" aria-label={label} className="fm-card p-5">
      <h2 className="text-[15px] font-semibold">{label}</h2>
      {entries.length === 0 ? (
        <p className={`mt-3 border-t border-[var(--fm-line)] pt-3 text-[13px] ${MUTED}`}>Not assessed</p>
      ) : (
        <dl className="mt-3">
          {entries.map(([name, verdict]) => (
            <div key={name} className="flex items-center justify-between gap-3 border-t border-[var(--fm-line)] py-2.5">
              <dt className="text-[13.5px] font-medium">{sentenceLabel(name)}</dt>
              <dd><VerdictPill verdict={verdict} /></dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}

function RunScope({ run, plan }: { run: EvaluationRun; plan?: EvaluationPlan }) {
  return (
    <section aria-labelledby="run-scope-heading" className="fm-card p-5">
      <h2 id="run-scope-heading" className="text-[15px] font-semibold">Run and plan</h2>
      <dl className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
        <Fact name="Run ID"><span className={mono}>{run.id}</span></Fact>
        <Fact name="Plan">{plan?.name ?? run.planId}</Fact>
        <Fact name="Target">{plan ? sentenceLabel(plan.targetKind) : 'Plan metadata unavailable'}</Fact>
        <Fact name="Trigger">{sentenceLabel(run.trigger)}</Fact>
        {plan && (
          <>
            <Fact name="Lifecycle phases">{plan.lifecyclePhases.map(sentenceLabel).join(', ')}</Fact>
            <Fact name="Execution depth">{sentenceLabel(plan.executionDepth)}</Fact>
            <Fact name="Enforcement">{sentenceLabel(plan.enforcementMode)}</Fact>
            <Fact name="Delivery">{sentenceLabel(plan.deliveryMode)}</Fact>
            <Fact name="Versioned suites" className="sm:col-span-2 lg:col-span-4"><span className={mono}>{plan.suiteRefs.join(', ')}</span></Fact>
          </>
        )}
      </dl>
    </section>
  )
}

export default function EvaluationRunDetailPage({ params }: PageProps) {
  const { testId } = use(params)
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const { selectedSystem, loading: systemLoading } = useSystemContext()
  const realSystem = selectedSystem.metadata?.source === 'fallback' ? undefined : selectedSystem
  const evaluations = useEvaluationRuns(selectedOrg?.id, realSystem?.id)
  const scopeKey = evaluationScopeKey({
    organizationId: selectedOrg?.id,
    systemId: realSystem?.id,
    runId: testId,
  })
  const [detailState, setDetailState] = useState<EvaluationScopeState<RunDetailState>>({
    scopeKey,
    value: { run: null, loading: false, error: null },
  })

  // Mask all prior-scope detail state synchronously. Effects run after paint,
  // so clearing only inside the loader can briefly expose old data or errors.
  const {
    run,
    loading: detailLoading,
    error: detailError,
  } = readEvaluationScopeState(detailState, scopeKey, {
    run: null,
    loading: Boolean(selectedOrg?.id && realSystem?.id),
    error: null,
  })

  useEffect(() => {
    let current = true
    setDetailState({
      scopeKey,
      value: {
        run: null,
        loading: Boolean(selectedOrg?.id && realSystem?.id),
        error: null,
      },
    })
    if (!selectedOrg?.id || !realSystem?.id) return () => { current = false }

    void evaluations.getRun(testId)
      .then((result) => {
        if (current) {
          setDetailState({
            scopeKey,
            value: { run: result, loading: false, error: null },
          })
        }
      })
      .catch((reason) => {
        if (!current || reason instanceof StaleEvaluationResultError) return
        setDetailState({
          scopeKey,
          value: {
            run: null,
            loading: false,
            error: reason instanceof Error ? reason : new Error('Unable to load evaluation run.'),
          },
        })
      })
    return () => { current = false }
  }, [evaluations.getRun, realSystem?.id, scopeKey, selectedOrg?.id, testId])

  const plan = useMemo(
    () => evaluations.plans.find((candidate) => candidate.id === run?.planId),
    [evaluations.plans, run?.planId],
  )
  const initialLoading = orgLoading || systemLoading || detailLoading || (!run && evaluations.loading)
  const notice = 'fm-card grid content-start justify-items-start gap-2 p-6'

  return (
    <div className="grid gap-4 text-[var(--fm-ink)]">
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/tests" aria-label="Back to Evaluation Runs" className="hover:text-[var(--fm-ink)]">Evaluation Runs</Link> · Run
      </div>
      <header className="min-w-0">
        <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Evaluation run</h1>
        <p className={`mt-2 ${mono} ${MUTED}`}>{testId}</p>
      </header>

      {!selectedOrg && !initialLoading ? (
        <section className={notice}>
          <h2 className="text-[15px] font-semibold">Choose an organization</h2>
          <p className={`text-[13px] ${MUTED}`}>An organization is required before this scoped run can be retrieved.</p>
        </section>
      ) : !realSystem && !initialLoading ? (
        <section className={notice}>
          <h2 className="text-[15px] font-semibold">Choose an AI system</h2>
          <p className={`text-[13px] ${MUTED}`}>A real selected system is required before this run can be retrieved.</p>
        </section>
      ) : initialLoading ? (
        <section role="status" aria-label="Loading evaluation run" className="fm-card grid gap-3 p-6">
          <div className="h-9 w-full animate-pulse rounded-[10px] bg-black/5 motion-reduce:animate-none" />
          <div className="h-28 w-full animate-pulse rounded-[10px] bg-black/5 motion-reduce:animate-none" />
          <div className="h-40 w-full animate-pulse rounded-[10px] bg-black/5 motion-reduce:animate-none" />
        </section>
      ) : detailError || !run ? (
        <section role="alert" className="rounded-xl bg-[#fde8e8] px-5 py-4 text-[#b42318]">
          <h2 className="text-[15px] font-semibold">Evaluation run unavailable</h2>
          <p className="mt-1 text-[13px]">{detailError?.message ?? 'The scoped run could not be found.'}</p>
        </section>
      ) : (
        <main className="grid gap-4">
          <section aria-label="Run decision state" className="grid gap-4 sm:grid-cols-2">
            <div className="fm-card p-5">
              <p className={LABEL}>Technical status</p>
              <div className="mt-2"><TechnicalStatusPill status={run.technicalStatus} /></div>
              <p className={sub}>Execution only. This is not a governance decision.</p>
            </div>
            <div className="fm-card p-5">
              <p className={LABEL}>Governance verdict</p>
              <div className="mt-2"><VerdictPill verdict={run.overallVerdict} /></div>
              <p className={sub}>A reviewer&apos;s judgment, based only on the evidence linked to this run.</p>
            </div>
          </section>

          <RunScope run={run} plan={plan} />

          <div className="grid gap-4 lg:grid-cols-2">
            <LayerAxis
              label="Component layer verdicts"
              verdicts={run.layerVerdicts.components as EvaluationLayerVerdicts['components']}
            />
            <LayerAxis
              label="Risk dimension verdicts"
              verdicts={run.layerVerdicts.dimensions as EvaluationLayerVerdicts['dimensions']}
            />
          </div>

          <section aria-labelledby="passport-linkage-heading" className="fm-card p-5">
            <h2 id="passport-linkage-heading" className="text-[15px] font-semibold">Evidence Passport linkage</h2>
            {run.linkedEvidenceRunId && run.linkedPassportRevisionId ? (
              <dl className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2">
                <Fact name="Evidence run ID"><span className={mono}>{run.linkedEvidenceRunId}</span></Fact>
                <Fact name="Passport revision ID"><span className={mono}>{run.linkedPassportRevisionId}</span></Fact>
                <Fact name="Linked at">{timestampLabel(run.linkedAt)}</Fact>
                <Fact name="Linked by"><span className={mono}>{run.linkedBy}</span></Fact>
              </dl>
            ) : (
              <div className="mt-3 rounded-[10px] bg-[#ffeee4] px-4 py-3 text-[#a8430b]">
                <p className="text-[13.5px] font-semibold">Awaiting evidence</p>
                <p className="mt-0.5 text-[12.5px]">No Evidence Passport revision is linked yet. FairMind does not invent artifacts or layer findings.</p>
              </div>
            )}
          </section>

          {(run.failureCode || run.failureMessage) && (
            <section role="alert" className="rounded-xl bg-[#fde8e8] px-5 py-4 text-[#b42318]">
              <h2 className="text-[15px] font-semibold">Execution failure</h2>
              {run.failureCode && <p className="mt-1 font-mono text-[12px]">{run.failureCode}</p>}
              {run.failureMessage && <p className="mt-1 text-[13px]">{run.failureMessage}</p>}
            </section>
          )}
        </main>
      )}
    </div>
  )
}

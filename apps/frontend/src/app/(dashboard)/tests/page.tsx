'use client'

import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'

import { BTN, BTN_P, LABEL, MUTED, Pill } from '@/components/packs/parts'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import {
  allowedLegacyDeliveryModes,
  allowedLegacyEnforcementModes,
  legacyEvaluationFeatureGates,
} from '@/lib/assurance/legacyEvaluationFeatureGates'
import {
  EvaluationApiRequestError,
  useEvaluationRuns,
  type CreateEvaluationPlanInput,
  type DeliveryMode,
  type EnforcementMode,
  type EvaluationPlan,
  type EvaluationPreflight,
  type EvaluationRun,
  type EvaluationTargetKind,
  type ExecutionDepth,
  type LifecyclePhase,
} from '@/lib/api/hooks/useEvaluationRuns'
import { cn } from '@/lib/utils'
import { TechnicalStatusPill, VerdictPill } from './pills'

const fieldClass = 'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] text-[var(--fm-ink)] outline-none focus:border-[var(--fm-ink)] disabled:cursor-not-allowed disabled:bg-[var(--fm-bg)]'
const labelClass = 'block text-[12px] font-medium text-[var(--fm-ink2)]'
const sub = `mt-1 text-[12.5px] ${MUTED}`
const alertClass = 'rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]'
const suitePattern = /^[a-z0-9][a-z0-9._-]*\/[a-z0-9][a-z0-9._-]*@[A-Za-z0-9][A-Za-z0-9._-]*$/

const targetKindLabels: Record<EvaluationTargetKind, string> = {
  predictive_model: 'Predictive model',
  llm_application: 'LLM application',
  agent: 'Agent',
  code_generator: 'Code generator',
  image_generator: 'Image generator',
  audio_model: 'Audio model',
  video_model: 'Video model',
  multimodal_system: 'Multimodal system',
}

const lifecycleLabels: Record<LifecyclePhase, string> = {
  pre_deploy: 'Pre-deploy',
  realtime: 'Realtime',
  post_deploy: 'Post-deploy',
}

const enforcementModeLabels: Record<EnforcementMode, string> = {
  advisory: 'Advisory',
  human_approval: 'Human approval',
  automatic: 'Automatic',
}

const deliveryModeLabels: Record<DeliveryMode, string> = {
  fairmind_worker: 'FairMind worker',
  external_provider: 'External provider',
  imported_report: 'Imported report',
}

// The selects offer only the modes this deployment has switched on.
const enabledEnforcementModes = allowedLegacyEnforcementModes(legacyEvaluationFeatureGates)
const enabledDeliveryModes = allowedLegacyDeliveryModes(legacyEvaluationFeatureGates)

const PLAN_TONE = { draft: 'you', active: 'done', archived: 'plain' } as const

function sentenceLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/^./, (character) => character.toUpperCase())
}

function timestampLabel(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function preflightPresentation(plan: EvaluationPlan, preflight: EvaluationPreflight) {
  const canPrepareRun = preflight.canPrepareRun && plan.status === 'active'
  if (plan.status === 'draft') {
    return {
      canPrepareRun,
      stateLabel: 'Plan activation required',
      message: 'This plan version is still a draft and cannot prepare a run.',
      nextAction: 'Activate this plan version after review, then run preflight again.',
    }
  }
  if (plan.status === 'archived') {
    return {
      canPrepareRun,
      stateLabel: 'Plan archived',
      message: 'This plan version is archived and cannot prepare a run.',
      nextAction: 'Create a new plan version and activate it before preparing a run.',
    }
  }
  return {
    canPrepareRun,
    stateLabel: preflight.code === 'executor_unavailable' ? 'Executor unavailable' : 'Evidence link required',
    message: preflight.message,
    nextAction: preflight.nextAction,
  }
}

function ActionAlert({
  title,
  error,
  alertRef,
}: {
  title: string
  error: Error
  alertRef: React.RefObject<HTMLDivElement>
}) {
  const nextAction = error instanceof EvaluationApiRequestError ? error.nextAction : undefined
  return (
    <div
      ref={alertRef}
      role="alert"
      tabIndex={-1}
      className="rounded-xl bg-[#fde8e8] px-4 py-3 text-[13px] text-[#b42318] outline-none focus-visible:ring-2 focus-visible:ring-[#b42318]"
    >
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{error.message}</p>
      {nextAction && <p className="mt-1 font-medium">Next action: {nextAction}</p>}
    </div>
  )
}

type PlanFormProps = {
  onCreate: (input: CreateEvaluationPlanInput) => Promise<void>
  submitting: boolean
}

function EvaluationPlanForm({ onCreate, submitting }: PlanFormProps) {
  const [name, setName] = useState('')
  const [targetKind, setTargetKind] = useState<EvaluationTargetKind>('predictive_model')
  const [lifecyclePhases, setLifecyclePhases] = useState<LifecyclePhase[]>(['pre_deploy'])
  const [executionDepth, setExecutionDepth] = useState<ExecutionDepth>('hybrid')
  const [enforcementMode, setEnforcementMode] = useState<EnforcementMode>('human_approval')
  const [deliveryMode, setDeliveryMode] = useState<DeliveryMode>('external_provider')
  const [suiteRefsText, setSuiteRefsText] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)

  const togglePhase = (phase: LifecyclePhase) => {
    setLifecyclePhases((current) => current.includes(phase)
      ? current.filter((candidate) => candidate !== phase)
      : [...current, phase])
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedName = name.trim()
    const suiteRefs = [...new Set(suiteRefsText.split('\n').map((line) => line.trim()).filter(Boolean))]
    if (!trimmedName || trimmedName.length > 120) {
      setValidationError('Plan name must contain between 1 and 120 characters.')
      return
    }
    if (lifecyclePhases.length === 0) {
      setValidationError('Select at least one lifecycle phase.')
      return
    }
    if (suiteRefs.length === 0 || suiteRefs.some((suiteRef) => !suitePattern.test(suiteRef))) {
      setValidationError('Add at least one versioned suite reference in namespace/name@version format.')
      return
    }

    setValidationError(null)
    await onCreate({
      name: trimmedName,
      targetKind,
      lifecyclePhases,
      executionDepth,
      enforcementMode,
      deliveryMode,
      suiteRefs,
    })
  }

  return (
    <form aria-label="Create evaluation plan" onSubmit={handleSubmit} className="grid gap-4">
      <div>
        <label htmlFor="evaluation-plan-name" className={labelClass}>Plan name</label>
        <input
          id="evaluation-plan-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className={fieldClass}
          maxLength={120}
          disabled={submitting}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div>
          <label htmlFor="evaluation-target-kind" className={labelClass}>Target kind</label>
          <select id="evaluation-target-kind" value={targetKind} onChange={(event) => setTargetKind(event.target.value as EvaluationTargetKind)} className={fieldClass} disabled={submitting}>
            {Object.entries(targetKindLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="evaluation-depth" className={labelClass}>Execution depth</label>
          <select id="evaluation-depth" value={executionDepth} onChange={(event) => setExecutionDepth(event.target.value as ExecutionDepth)} className={fieldClass} disabled={submitting}>
            <option value="inline">Inline</option>
            <option value="deep">Deep</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>
        <div>
          <label htmlFor="evaluation-enforcement" className={labelClass}>Enforcement mode</label>
          <select id="evaluation-enforcement" value={enforcementMode} onChange={(event) => setEnforcementMode(event.target.value as EnforcementMode)} className={fieldClass} disabled={submitting}>
            {enabledEnforcementModes.map((mode) => <option key={mode} value={mode}>{enforcementModeLabels[mode]}</option>)}
          </select>
        </div>
      </div>

      <fieldset>
        <legend className={labelClass}>Lifecycle phases</legend>
        <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1">
          {(Object.entries(lifecycleLabels) as Array<[LifecyclePhase, string]>).map(([phase, label]) => (
            <label key={phase} className="flex min-h-9 cursor-pointer items-center gap-2 text-[13.5px]">
              <input
                type="checkbox"
                checked={lifecyclePhases.includes(phase)}
                onChange={() => togglePhase(phase)}
                className="h-4 w-4 accent-[var(--fm-ink)]"
                disabled={submitting}
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 lg:grid-cols-[minmax(220px,0.6fr)_minmax(320px,1.4fr)]">
        <div>
          <label htmlFor="evaluation-delivery" className={labelClass}>Delivery mode</label>
          <select id="evaluation-delivery" value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as DeliveryMode)} className={fieldClass} disabled={submitting}>
            {enabledDeliveryModes.map((mode) => <option key={mode} value={mode}>{deliveryModeLabels[mode]}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="evaluation-suite-refs" className={labelClass}>Versioned suite references</label>
          <textarea
            id="evaluation-suite-refs"
            value={suiteRefsText}
            onChange={(event) => setSuiteRefsText(event.target.value)}
            placeholder="fairmind/agent-safety@2026.07"
            rows={3}
            className={`${fieldClass} h-auto min-h-[88px] resize-y py-2 font-mono text-[12.5px]`}
            disabled={submitting}
          />
          <p className={`mt-1 text-[12px] ${MUTED}`}>One immutable namespace/name@version reference per line.</p>
        </div>
      </div>

      {validationError && <p role="alert" className={alertClass}>{validationError}</p>}

      <div>
        <button type="submit" disabled={submitting} className={BTN_P}>
          {submitting ? 'Creating plan' : 'Create evaluation plan'}
        </button>
      </div>
    </form>
  )
}

function RunsTable({ runs, plans }: { runs: EvaluationRun[]; plans: EvaluationPlan[] }) {
  const planNames = useMemo(() => new Map(plans.map((plan) => [plan.id, plan.name])), [plans])
  if (runs.length === 0) {
    return (
      <div className="mt-3 border-t border-[var(--fm-line)] pt-4">
        <h3 className="text-[13.5px] font-semibold">No evaluation runs yet</h3>
        <p className={sub}>
          Activate a plan, check preflight, then prepare a run. External and imported runs wait for evidence until an exact Passport revision is linked.
        </p>
      </div>
    )
  }

  const th = `px-2 py-2 ${LABEL}`
  return (
    <div className="mt-3 max-w-full overflow-x-auto">
      <table aria-label="Recent evaluation runs" className="w-full min-w-[840px] border-collapse text-left text-[13px]">
        <thead>
          <tr>
            <th scope="col" className={th}>Run</th>
            <th scope="col" className={th}>Plan</th>
            <th scope="col" className={th}>Technical status</th>
            <th scope="col" className={th}>Overall verdict</th>
            <th scope="col" className={th}>Trigger</th>
            <th scope="col" className={th}>Created</th>
            <th scope="col" className="px-2 py-2"><span className="sr-only">Open run</span></th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-t border-[var(--fm-line)]">
              <td className="px-2 py-3 font-mono text-[11.5px]">{run.id}</td>
              <td className="px-2 py-3 font-medium">{planNames.get(run.planId) ?? run.planId}</td>
              <td className="px-2 py-3"><TechnicalStatusPill status={run.technicalStatus} /></td>
              <td className="px-2 py-3"><VerdictPill verdict={run.overallVerdict} /></td>
              <td className="px-2 py-3">{sentenceLabel(run.trigger)}</td>
              <td className={`px-2 py-3 ${MUTED}`}>{timestampLabel(run.createdAt)}</td>
              <td className="px-2 py-3 text-right">
                <Link href={`/tests/${run.id}`} aria-label={`Open run ${run.id}`} className={cn(BTN, 'h-8 px-3.5 text-[12px]')}>
                  Open
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Fact({ name, children }: { name: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className={LABEL}>{name}</dt>
      <dd className="mt-0.5 text-[13.5px]">{children}</dd>
    </div>
  )
}

export default function EvaluationRunsPage() {
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const { selectedSystem, loading: systemLoading } = useSystemContext()
  const realSystem = selectedSystem.metadata?.source === 'fallback' ? undefined : selectedSystem
  const evaluations = useEvaluationRuns(selectedOrg?.id, realSystem?.id)
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)
  const [showCreatePlan, setShowCreatePlan] = useState(false)
  const [preflight, setPreflight] = useState<EvaluationPreflight | null>(null)
  const [preflightLoading, setPreflightLoading] = useState(false)
  const [preflightError, setPreflightError] = useState<Error | null>(null)
  const [actionError, setActionError] = useState<Error | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [actionBusy, setActionBusy] = useState(false)
  const actionAlertRef = useRef<HTMLDivElement>(null)

  const selectedPlan = evaluations.plans.find((plan) => plan.id === selectedPlanId) ?? null
  const planListUnconfirmed = evaluations.plans.length === 0 && !evaluations.plansLoaded
  const selectedPreflight = selectedPlan && preflight
    ? preflightPresentation(selectedPlan, preflight)
    : null

  useEffect(() => {
    if (evaluations.plans.length === 0) {
      setSelectedPlanId(null)
      return
    }
    if (selectedPlanId && evaluations.plans.some((plan) => plan.id === selectedPlanId)) return
    setSelectedPlanId(evaluations.plans.find((plan) => plan.status === 'active')?.id ?? evaluations.plans[0].id)
  }, [evaluations.plans, selectedPlanId])

  useEffect(() => {
    let current = true
    setPreflight(null)
    setPreflightError(null)
    if (!selectedPlan) return () => { current = false }
    setPreflightLoading(true)
    void evaluations.loadPreflight(selectedPlan.id)
      .then((result) => {
        if (current) setPreflight(result)
      })
      .catch((reason) => {
        if (current) setPreflightError(reason instanceof Error ? reason : new Error('Unable to load preflight.'))
      })
      .finally(() => {
        if (current) setPreflightLoading(false)
      })
    return () => { current = false }
  }, [evaluations.loadPreflight, selectedPlan?.id, selectedPlan?.status, selectedPlan?.updatedAt])

  const focusActionError = () => {
    window.requestAnimationFrame(() => actionAlertRef.current?.focus())
  }

  const runAction = async (action: () => Promise<void>) => {
    setActionBusy(true)
    setActionError(null)
    setActionMessage(null)
    try {
      await action()
    } catch (reason) {
      setActionError(reason instanceof Error ? reason : new Error('Evaluation action failed.'))
      focusActionError()
    } finally {
      setActionBusy(false)
    }
  }

  const createPlan = async (input: CreateEvaluationPlanInput) => runAction(async () => {
    const created = await evaluations.createPlan(input)
    setSelectedPlanId(created.id)
    setShowCreatePlan(false)
    setActionMessage('Plan created as a draft. Activate it before preparing a run.')
  })

  const activateSelectedPlan = async () => {
    if (!selectedPlan) return
    await runAction(async () => {
      await evaluations.activatePlan(selectedPlan.id)
      setActionMessage('Plan activated. Review preflight before preparing a run.')
    })
  }

  const prepareRun = async () => {
    if (!selectedPlan || !preflight?.canPrepareRun || selectedPlan.status !== 'active') return
    await runAction(async () => {
      await evaluations.createRun(selectedPlan.id)
      setActionMessage('Run prepared. Evidence is still required before governance review.')
    })
  }

  const initialLoading = (orgLoading || systemLoading) || (evaluations.loading && evaluations.plans.length === 0 && evaluations.runs.length === 0)
  const ready = Boolean(selectedOrg && realSystem) && !initialLoading

  return (
    <div data-testid="evaluation-runs-workbench" className="grid gap-4 text-[var(--fm-ink)]">
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Evaluations
      </div>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Evaluation Runs</h1>
          <p className={`mt-2 max-w-[640px] text-[15px] ${MUTED}`}>
            Plan evaluations for {realSystem ? realSystem.name : 'an AI system'}, check each plan can run, and link the evidence a run produces. A finished run is not an approval: the governance verdict is kept separate.
          </p>
        </div>
        {ready && evaluations.plansLoaded && evaluations.plans.length > 0 && (
          <button type="button" onClick={() => setShowCreatePlan((current) => !current)} className={BTN}>
            {showCreatePlan ? 'Close form' : 'New plan'}
          </button>
        )}
      </header>

      {!selectedOrg && !initialLoading ? (
        <section className="fm-card grid content-start justify-items-start gap-3 p-6">
          <h2 className="text-[15px] font-semibold">Choose an organization</h2>
          <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
            Select or create an organization before loading scoped plans, runs, or governance evidence.
          </p>
          <Link href="/org-admin" className={BTN_P}>Manage organizations</Link>
        </section>
      ) : !realSystem && !initialLoading ? (
        <section className="fm-card grid content-start justify-items-start gap-3 p-6">
          <h2 className="text-[15px] font-semibold">Choose an AI system</h2>
          <p className={`max-w-[560px] text-[13px] ${MUTED}`}>
            Select or register a real AI system before loading plans or evaluation evidence. Placeholder systems are never evaluated.
          </p>
          <Link href="/onboard" className={BTN_P}>Register an AI system</Link>
        </section>
      ) : initialLoading ? (
        <div role="status" aria-label="Loading evaluation workspace" className="fm-card grid gap-3 p-6">
          <div className="h-5 w-48 animate-pulse rounded-lg bg-black/5 motion-reduce:animate-none" />
          <div className="h-9 w-full animate-pulse rounded-[10px] bg-black/5 motion-reduce:animate-none" />
          <div className="h-28 w-full animate-pulse rounded-[10px] bg-black/5 motion-reduce:animate-none" />
        </div>
      ) : (
        <>
          {evaluations.error && (
            <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[#fde8e8] px-4 py-3 text-[13px] text-[#b42318]">
              <div className="min-w-0">
                <p className="font-semibold">Evaluation data unavailable</p>
                <p className="mt-0.5">{evaluations.error.message}</p>
              </div>
              <button type="button" onClick={() => void evaluations.refresh()} className={BTN}>
                Retry loading evaluations
              </button>
            </div>
          )}

          {actionError && <ActionAlert title="Evaluation action failed" error={actionError} alertRef={actionAlertRef} />}
          {actionMessage && (
            <p role="status" className="rounded-xl bg-[#e3f5ec] px-4 py-3 text-[13px] font-medium text-[#00704e]">
              {actionMessage}
            </p>
          )}

          <section aria-labelledby="evaluation-plan-heading" className="fm-card p-5">
            <h2 id="evaluation-plan-heading" className="text-[15px] font-semibold">Evaluation plan</h2>
            <p className={sub}>Version the target, lifecycle coverage, delivery route and suites before collecting evidence.</p>

            <div className="mt-4">
              {planListUnconfirmed ? (
                <div role="status" className="rounded-[10px] bg-[var(--fm-bg)] px-4 py-3">
                  <p className="text-[13.5px] font-semibold">Plan availability is unconfirmed</p>
                  <p className={sub}>Retry loading evaluations before creating a plan so an existing version is not duplicated.</p>
                </div>
              ) : evaluations.plans.length === 0 || showCreatePlan ? (
                <EvaluationPlanForm onCreate={createPlan} submitting={actionBusy} />
              ) : (
                <div className="grid gap-4">
                  <div className="grid gap-4 lg:grid-cols-[minmax(240px,1fr)_2fr]">
                    <div>
                      <label htmlFor="evaluation-plan-selector" className={labelClass}>Selected plan</label>
                      <select id="evaluation-plan-selector" value={selectedPlanId ?? ''} onChange={(event) => setSelectedPlanId(event.target.value)} className={fieldClass}>
                        {evaluations.plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name}</option>)}
                      </select>
                    </div>
                    {selectedPlan && (
                      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
                        <Fact name="Status">
                          <Pill tone={PLAN_TONE[selectedPlan.status] ?? 'plain'} dot={selectedPlan.status === 'draft'}>{sentenceLabel(selectedPlan.status)}</Pill>
                        </Fact>
                        <Fact name="Target">{targetKindLabels[selectedPlan.targetKind]}</Fact>
                        <Fact name="Depth">{sentenceLabel(selectedPlan.executionDepth)}</Fact>
                        <Fact name="Delivery">{sentenceLabel(selectedPlan.deliveryMode)}</Fact>
                        <div className="col-span-2 sm:col-span-4">
                          <Fact name="Suites"><span className="break-all font-mono text-[12px]">{selectedPlan.suiteRefs.join(', ')}</span></Fact>
                        </div>
                      </dl>
                    )}
                  </div>
                  {selectedPlan?.status === 'draft' && (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-[10px] bg-[#ffeee4] px-4 py-3 text-[#a8430b]">
                      <p className="text-[13px] font-medium">This version is a draft, so it cannot prepare a run. Activate it after review.</p>
                      <button type="button" onClick={() => void activateSelectedPlan()} disabled={actionBusy} className={BTN_P}>Activate plan</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          {selectedPlan && !showCreatePlan && (
            <section role="region" aria-label="Evaluation preflight" className="fm-card p-5">
              <h2 className="text-[15px] font-semibold">Preflight and run preparation</h2>
              {preflightLoading ? (
                <p role="status" aria-label="Loading evaluation preflight" className={`mt-3 text-[13px] ${MUTED}`}>Checking execution and evidence requirements</p>
              ) : preflightError ? (
                <p role="alert" className={`mt-3 ${alertClass}`}>{preflightError.message}</p>
              ) : preflight && selectedPreflight ? (
                <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
                  <div className="min-w-0 max-w-[720px]">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
                      <Pill tone={selectedPreflight.canPrepareRun ? 'done' : 'block'}>{selectedPreflight.stateLabel}</Pill>
                      <span className={`text-[12.5px] ${MUTED}`}>{selectedPreflight.canPrepareRun ? 'Run preparation: allowed' : 'Run preparation: blocked'}</span>
                      <span className={`text-[12.5px] ${MUTED}`}>FairMind execution: {preflight.fairmindExecutionAvailable ? 'available' : 'unavailable'}</span>
                    </div>
                    <p className="mt-3 text-[13.5px]">{selectedPreflight.message}</p>
                    <p className={sub}>Next action: {selectedPreflight.nextAction}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void prepareRun()}
                    disabled={actionBusy || !selectedPreflight.canPrepareRun}
                    className={BTN_P}
                  >
                    {actionBusy ? 'Preparing run' : 'Prepare evidence run'}
                  </button>
                </div>
              ) : null}
            </section>
          )}

          <section aria-labelledby="recent-runs-heading" className="fm-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 id="recent-runs-heading" className="text-[15px] font-semibold">Recent runs</h2>
                <p className={sub}>Technical status and governance verdict are judged separately.</p>
              </div>
              <button type="button" onClick={() => void evaluations.refresh()} className={BTN}>Refresh</button>
            </div>
            {/* After a failed load the list is unknown, so "No evaluation runs yet" would be a false claim. */}
            {evaluations.error && evaluations.runs.length === 0 ? (
              <p className={`mt-3 border-t border-[var(--fm-line)] pt-4 text-[13px] ${MUTED}`}>Runs could not be loaded. Retry above.</p>
            ) : (
              <RunsTable runs={evaluations.runs} plans={evaluations.plans} />
            )}
          </section>
        </>
      )}
    </div>
  )
}

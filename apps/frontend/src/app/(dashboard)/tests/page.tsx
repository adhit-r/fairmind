'use client'

import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconPlayerPlay,
  IconPlus,
  IconRefresh,
  IconShieldCheck,
} from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { FramedIcon } from '@/components/ui/FramedIcon'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
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
  type GovernanceVerdict,
  type LifecyclePhase,
  type TechnicalStatus,
} from '@/lib/api/hooks/useEvaluationRuns'

const fieldClass = 'min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 text-sm font-semibold text-[#0F1412] outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#0F1412] disabled:cursor-not-allowed disabled:bg-[#E5E9E3]'
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

const statusLabels: Record<TechnicalStatus, string> = {
  awaiting_evidence: 'Awaiting evidence',
  running: 'Running',
  succeeded: 'Succeeded',
  failed: 'Failed',
  cancelled: 'Cancelled',
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

function timestampLabel(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function technicalStatusClass(status: TechnicalStatus) {
  if (status === 'failed' || status === 'cancelled') return 'border-[#D83A2E] bg-red-50 text-[#A4231B]'
  if (status === 'running') return 'border-[#2E8266] bg-emerald-50 text-[#155D46]'
  if (status === 'succeeded') return 'border-[#0F1412] bg-[#0F1412] text-white'
  return 'border-[#59615D] bg-[#F3F5F0] text-[#303834]'
}

function verdictClass(verdict: GovernanceVerdict) {
  if (verdict === 'blocked') return 'border-[#D83A2E] bg-[#D83A2E] text-white'
  if (verdict === 'approved') return 'border-[#155D46] bg-[#DFF4EA] text-[#155D46]'
  if (verdict === 'conditional') return 'border-[#9A5B14] bg-[#FFF1D6] text-[#73420B]'
  if (verdict === 'review') return 'border-[#0F1412] bg-[#FF6B35] text-[#0F1412]'
  return 'border-[#59615D] bg-[#F3F5F0] text-[#303834]'
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

function StateLabel({ children, className }: { children: React.ReactNode; className: string }) {
  return (
    <span className={`inline-flex min-h-8 items-center border-2 px-2.5 py-1 text-xs font-black uppercase ${className}`}>
      {children}
    </span>
  )
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
      className="border-4 border-[#D83A2E] bg-red-50 p-4 outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#D83A2E]"
    >
      <div className="flex items-start gap-3">
        <IconAlertTriangle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-[#D83A2E]" />
        <div>
          <p className="font-black text-[#8F2019]">{title}</p>
          <p className="mt-1 text-sm font-semibold text-[#5B211D]">{error.message}</p>
          {nextAction && <p className="mt-2 text-sm font-bold text-[#5B211D]">Next action: {nextAction}</p>}
        </div>
      </div>
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
  const [deliveryMode, setDeliveryMode] = useState<DeliveryMode>('fairmind_worker')
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
    <form aria-label="Create evaluation plan" onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="evaluation-plan-name" className="text-xs font-black uppercase tracking-wide">Plan name</label>
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
        <div className="flex flex-col gap-1">
          <label htmlFor="evaluation-target-kind" className="text-xs font-black uppercase tracking-wide">Target kind</label>
          <select id="evaluation-target-kind" value={targetKind} onChange={(event) => setTargetKind(event.target.value as EvaluationTargetKind)} className={fieldClass} disabled={submitting}>
            {Object.entries(targetKindLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="evaluation-depth" className="text-xs font-black uppercase tracking-wide">Execution depth</label>
          <select id="evaluation-depth" value={executionDepth} onChange={(event) => setExecutionDepth(event.target.value as ExecutionDepth)} className={fieldClass} disabled={submitting}>
            <option value="inline">Inline</option>
            <option value="deep">Deep</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="evaluation-enforcement" className="text-xs font-black uppercase tracking-wide">Enforcement mode</label>
          <select id="evaluation-enforcement" value={enforcementMode} onChange={(event) => setEnforcementMode(event.target.value as EnforcementMode)} className={fieldClass} disabled={submitting}>
            <option value="advisory">Advisory</option>
            <option value="human_approval">Human approval</option>
            <option value="automatic">Automatic</option>
          </select>
        </div>
      </div>

      <fieldset className="border-2 border-[#0F1412] p-3">
        <legend className="px-1 text-xs font-black uppercase tracking-wide">Lifecycle phases</legend>
        <div className="flex flex-wrap gap-x-5 gap-y-2">
          {(Object.entries(lifecycleLabels) as Array<[LifecyclePhase, string]>).map(([phase, label]) => (
            <label key={phase} className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-bold">
              <input
                type="checkbox"
                checked={lifecyclePhases.includes(phase)}
                onChange={() => togglePhase(phase)}
                className="h-5 w-5 rounded-none border-2 border-[#0F1412] accent-[#FF6B35]"
                disabled={submitting}
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 lg:grid-cols-[minmax(220px,0.6fr)_minmax(320px,1.4fr)]">
        <div className="flex flex-col gap-1">
          <label htmlFor="evaluation-delivery" className="text-xs font-black uppercase tracking-wide">Delivery mode</label>
          <select id="evaluation-delivery" value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as DeliveryMode)} className={fieldClass} disabled={submitting}>
            <option value="fairmind_worker">FairMind worker</option>
            <option value="external_provider">External provider</option>
            <option value="imported_report">Imported report</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="evaluation-suite-refs" className="text-xs font-black uppercase tracking-wide">Versioned suite references</label>
          <textarea
            id="evaluation-suite-refs"
            value={suiteRefsText}
            onChange={(event) => setSuiteRefsText(event.target.value)}
            placeholder="fairmind/agent-safety@2026.07"
            rows={3}
            className={`${fieldClass} min-h-[88px] resize-y font-mono`}
            disabled={submitting}
          />
          <p className="text-xs font-semibold text-[#59615D]">One immutable namespace/name@version reference per line.</p>
        </div>
      </div>

      {validationError && (
        <p role="alert" className="border-2 border-[#D83A2E] bg-red-50 p-3 text-sm font-bold text-[#8F2019]">
          {validationError}
        </p>
      )}

      <Button type="submit" disabled={submitting} className="rounded-none border-[#0F1412] bg-[#FF6B35] font-black">
        <IconPlus aria-hidden="true" />
        {submitting ? 'Creating plan' : 'Create evaluation plan'}
      </Button>
    </form>
  )
}

function RunsTable({ runs, plans }: { runs: EvaluationRun[]; plans: EvaluationPlan[] }) {
  const planNames = useMemo(() => new Map(plans.map((plan) => [plan.id, plan.name])), [plans])
  if (runs.length === 0) {
    return (
      <div className="border-2 border-dashed border-[#59615D] bg-[#F3F5F0] p-6">
        <h3 className="text-base font-black">No evaluation runs yet</h3>
        <p className="mt-1 max-w-[70ch] text-sm font-semibold text-[#59615D]">
          Activate a plan, check preflight, then prepare a run. External and imported runs remain awaiting evidence until an exact Passport revision is linked.
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-full overflow-x-auto border-2 border-[#0F1412]">
      <table aria-label="Recent evaluation runs" className="w-full min-w-[840px] border-collapse text-left text-sm">
        <thead className="bg-[#0F1412] text-white">
          <tr>
            <th scope="col" className="px-3 py-3 font-black">Run</th>
            <th scope="col" className="px-3 py-3 font-black">Plan</th>
            <th scope="col" className="px-3 py-3 font-black">Technical status</th>
            <th scope="col" className="px-3 py-3 font-black">Overall verdict</th>
            <th scope="col" className="px-3 py-3 font-black">Trigger</th>
            <th scope="col" className="px-3 py-3 font-black">Created</th>
            <th scope="col" className="px-3 py-3"><span className="sr-only">Open run</span></th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-t-2 border-[#0F1412] bg-[#FCFDF8] hover:bg-[#F3F5F0]">
              <td className="px-3 py-3 font-mono text-xs font-bold">{run.id}</td>
              <td className="px-3 py-3 font-bold">{planNames.get(run.planId) ?? run.planId}</td>
              <td className="px-3 py-3"><StateLabel className={technicalStatusClass(run.technicalStatus)}>{statusLabels[run.technicalStatus]}</StateLabel></td>
              <td className="px-3 py-3"><StateLabel className={verdictClass(run.overallVerdict)}>{verdictLabels[run.overallVerdict]}</StateLabel></td>
              <td className="px-3 py-3 font-semibold">{sentenceLabel(run.trigger)}</td>
              <td className="px-3 py-3 font-semibold text-[#59615D]">{timestampLabel(run.createdAt)}</td>
              <td className="px-3 py-3 text-right">
                <Link
                  href={`/tests/${run.id}`}
                  aria-label={`Open run ${run.id}`}
                  className="inline-flex min-h-11 items-center gap-2 border-2 border-[#0F1412] bg-[#FCFDF8] px-3 font-black shadow-[3px_3px_0_0_#0F1412] outline outline-0 outline-offset-2 transition-[transform,box-shadow] duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none focus:outline-2 focus:outline-[#0F1412] motion-reduce:transition-none motion-reduce:transform-none"
                >
                  Open <IconArrowRight aria-hidden="true" className="h-4 w-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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

  return (
    <div data-testid="evaluation-runs-workbench" className="mx-auto w-full max-w-[1500px] space-y-5 text-[#0F1412]">
      <header className="border-b-4 border-[#0F1412] pb-4 pt-1">
        <div className="flex items-start gap-3">
          <span className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center border-2 border-[#0F1412] bg-[#FF6B35] shadow-[3px_3px_0_0_#0F1412]" aria-hidden="true">
            <IconShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <h1 className="text-3xl font-black tracking-[-0.02em]">Evaluation Runs</h1>
            <p className="mt-1 max-w-[72ch] text-sm font-semibold text-[#59615D]">
              Plan multi-modal evaluations, verify execution readiness, and connect exact evidence revisions without turning technical success into a governance approval.
            </p>
          </div>
        </div>
      </header>

      {!selectedOrg && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an organization</h2>
          <p className="mt-2 max-w-[70ch] text-sm font-semibold text-[#59615D]">
            Select or create an organization before loading scoped plans, runs, or governance evidence.
          </p>
          <Link href="/org-admin" className="mt-4 inline-flex min-h-11 items-center border-2 border-[#0F1412] bg-[#FF6B35] px-4 font-black shadow-[4px_4px_0_0_#0F1412] outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#0F1412]">
            Manage organizations
          </Link>
        </section>
      ) : !realSystem && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an AI system</h2>
          <p className="mt-2 max-w-[70ch] text-sm font-semibold text-[#59615D]">
            Select or register a real AI system before loading plans or evaluation evidence. Placeholder systems are never evaluated.
          </p>
          <Link href="/onboard" className="mt-4 inline-flex min-h-11 items-center border-2 border-[#0F1412] bg-[#FF6B35] px-4 font-black shadow-[4px_4px_0_0_#0F1412] outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#0F1412]">
            Register an AI system
          </Link>
        </section>
      ) : (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8]">
          {initialLoading ? (
            <div aria-label="Loading evaluation workspace" className="space-y-3 p-6">
              <div className="h-5 w-48 animate-pulse bg-[#D6DBD4] motion-reduce:animate-none" />
              <div className="h-11 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
              <div className="h-28 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
            </div>
          ) : (
            <>
              {evaluations.error && (
                <div role="alert" className="border-b-4 border-[#D83A2E] bg-red-50 p-4">
                  <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                    <div>
                      <p className="font-black text-[#8F2019]">Evaluation data unavailable</p>
                      <p className="mt-1 text-sm font-semibold text-[#5B211D]">{evaluations.error.message}</p>
                    </div>
                    <Button variant="neutral" onClick={() => void evaluations.refresh()} className="rounded-none border-[#0F1412] font-black">
                      Retry loading evaluations
                    </Button>
                  </div>
                </div>
              )}

              {actionError && <ActionAlert title="Evaluation action failed" error={actionError} alertRef={actionAlertRef} />}
              {actionMessage && (
                <p role="status" className="border-b-2 border-[#0F1412] bg-[#DFF4EA] p-3 text-sm font-bold text-[#155D46]">
                  {actionMessage}
                </p>
              )}

              <section aria-labelledby="evaluation-plan-heading" className="border-b-4 border-[#0F1412] p-4 sm:p-5">
                <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                  <div>
                    <h2 id="evaluation-plan-heading" className="text-lg font-black">Evaluation plan</h2>
                    <p className="text-sm font-semibold text-[#59615D]">Version the target, lifecycle coverage, delivery route, and suites before collecting evidence.</p>
                  </div>
                  {evaluations.plansLoaded && evaluations.plans.length > 0 && (
                    <FramedIcon
                      icon={IconPlus}
                      label={showCreatePlan ? 'Close new plan form' : 'Create another evaluation plan'}
                      text={showCreatePlan ? 'Close form' : 'New plan'}
                      onClick={() => setShowCreatePlan((current) => !current)}
                      className="sm:w-auto"
                    />
                  )}
                </div>

                {planListUnconfirmed ? (
                  <div role="status" className="border-2 border-[#0F1412] bg-[#F3F5F0] p-4">
                    <p className="font-black">Plan availability is unconfirmed</p>
                    <p className="mt-1 max-w-[70ch] text-sm font-semibold text-[#59615D]">
                      Retry loading evaluations before creating a plan so an existing version is not duplicated.
                    </p>
                  </div>
                ) : evaluations.plans.length === 0 || showCreatePlan ? (
                  <EvaluationPlanForm onCreate={createPlan} submitting={actionBusy} />
                ) : (
                  <div className="space-y-4">
                    <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_2fr]">
                      <div className="flex flex-col gap-1">
                        <label htmlFor="evaluation-plan-selector" className="text-xs font-black uppercase tracking-wide">Selected plan</label>
                        <select id="evaluation-plan-selector" value={selectedPlanId ?? ''} onChange={(event) => setSelectedPlanId(event.target.value)} className={fieldClass}>
                          {evaluations.plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name}</option>)}
                        </select>
                      </div>
                      {selectedPlan && (
                        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-2 border-[#0F1412] bg-[#F3F5F0] p-3 text-sm sm:grid-cols-4">
                          <div><dt className="text-xs font-black uppercase text-[#59615D]">Status</dt><dd className="mt-1 font-black">{sentenceLabel(selectedPlan.status)}</dd></div>
                          <div><dt className="text-xs font-black uppercase text-[#59615D]">Target</dt><dd className="mt-1 font-bold">{targetKindLabels[selectedPlan.targetKind]}</dd></div>
                          <div><dt className="text-xs font-black uppercase text-[#59615D]">Depth</dt><dd className="mt-1 font-bold">{sentenceLabel(selectedPlan.executionDepth)}</dd></div>
                          <div><dt className="text-xs font-black uppercase text-[#59615D]">Delivery</dt><dd className="mt-1 font-bold">{sentenceLabel(selectedPlan.deliveryMode)}</dd></div>
                          <div className="col-span-2 sm:col-span-4"><dt className="text-xs font-black uppercase text-[#59615D]">Suites</dt><dd className="mt-1 break-all font-mono text-xs font-bold">{selectedPlan.suiteRefs.join(', ')}</dd></div>
                        </dl>
                      )}
                    </div>
                    {selectedPlan?.status === 'draft' && (
                      <div className="flex flex-col gap-2 border-2 border-[#0F1412] bg-[#FFF1D6] p-3 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm font-bold">Draft plans cannot prepare runs. Activate this version after review.</p>
                        <Button onClick={() => void activateSelectedPlan()} disabled={actionBusy} className="rounded-none border-[#0F1412] bg-[#FF6B35] font-black">Activate plan</Button>
                      </div>
                    )}
                  </div>
                )}
              </section>

              {selectedPlan && !showCreatePlan && (
                <section role="region" aria-label="Evaluation preflight" className="border-b-4 border-[#0F1412] p-4 sm:p-5">
                  <h2 className="text-lg font-black">Preflight and run preparation</h2>
                  {preflightLoading ? (
                    <p aria-label="Loading evaluation preflight" className="mt-3 min-h-11 animate-pulse bg-[#E5E9E3] p-3 text-sm font-bold motion-reduce:animate-none">Checking execution and evidence requirements</p>
                  ) : preflightError ? (
                    <p role="alert" className="mt-3 border-2 border-[#D83A2E] bg-red-50 p-3 text-sm font-bold text-[#8F2019]">{preflightError.message}</p>
                  ) : preflight && selectedPreflight ? (
                    <div className="mt-3 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
                      <div className="border-2 border-[#0F1412] bg-[#F3F5F0] p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <StateLabel className={selectedPreflight.canPrepareRun ? 'border-[#155D46] bg-[#DFF4EA] text-[#155D46]' : 'border-[#D83A2E] bg-red-50 text-[#8F2019]'}>
                            {selectedPreflight.stateLabel}
                          </StateLabel>
                          <span className="text-xs font-black uppercase text-[#59615D]">{selectedPreflight.canPrepareRun ? 'Run preparation: allowed' : 'Run preparation: blocked'}</span>
                          <span className="text-xs font-black uppercase text-[#59615D]">FairMind execution: {preflight.fairmindExecutionAvailable ? 'available' : 'unavailable'}</span>
                        </div>
                        <p className="mt-3 text-sm font-semibold">{selectedPreflight.message}</p>
                        <p className="mt-2 text-sm font-black">Next action: {selectedPreflight.nextAction}</p>
                      </div>
                      <Button
                        onClick={() => void prepareRun()}
                        disabled={actionBusy || !selectedPreflight.canPrepareRun}
                        className="rounded-none border-[#0F1412] bg-[#FF6B35] font-black"
                      >
                        <IconPlayerPlay aria-hidden="true" />
                        {actionBusy ? 'Preparing run' : 'Prepare evidence run'}
                      </Button>
                    </div>
                  ) : null}
                </section>
              )}

              <section aria-labelledby="recent-runs-heading" className="p-4 sm:p-5">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <h2 id="recent-runs-heading" className="text-lg font-black">Recent runs</h2>
                    <p className="text-sm font-semibold text-[#59615D]">Technical execution and governance judgment stay separate.</p>
                  </div>
                  <FramedIcon icon={IconRefresh} label="Refresh evaluations" onClick={() => void evaluations.refresh()} />
                </div>
                <RunsTable runs={evaluations.runs} plans={evaluations.plans} />
              </section>
            </>
          )}
        </section>
      )}
    </div>
  )
}

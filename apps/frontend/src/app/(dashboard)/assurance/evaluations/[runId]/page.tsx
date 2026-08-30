'use client'

import { use, useEffect, useState } from 'react'
import { IconArrowLeft, IconShieldCheck } from '@tabler/icons-react'

import { EvidenceTrustPanel } from '@/components/evaluations/EvidenceTrustPanel'
import { EvaluationWorkbenchStatusNotice } from '@/components/evaluations/EvaluationWorkbenchStatusNotice'
import { FramedIcon } from '@/components/ui/FramedIcon'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import {
  StaleEvaluationWorkbenchResultError,
  useEvaluationWorkbenchV2,
  type EvaluationRunV2,
} from '@/lib/api/hooks/useEvaluationWorkbenchV2'
import {
  evaluationScopeKey,
  readEvaluationScopeState,
  writeEvaluationScopeState,
  type EvaluationScopeState,
} from '@/lib/evaluation-scope-state'

interface PageProps {
  params: Promise<{ runId: string }>
}

type RunDetailState = {
  run: EvaluationRunV2 | null
  loading: boolean
  error: Error | null
}

const ASSURANCE_V2_UI_ENABLED = process.env.NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED === 'true'
const ASSURANCE_V2_RUN_UI_ENABLED = ASSURANCE_V2_UI_ENABLED
  && process.env.NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED === 'true'

export default function AssuranceEvaluationDetailPage({ params }: PageProps) {
  const { runId } = use(params)
  const { selectedOrg, isLoading: orgLoading } = useOrg()
  const { selectedSystem, loading: systemLoading } = useSystemContext()
  const realSystem = selectedSystem.metadata?.source === 'fallback' ? undefined : selectedSystem
  const workbench = useEvaluationWorkbenchV2(
    ASSURANCE_V2_RUN_UI_ENABLED ? selectedOrg?.id : undefined,
    ASSURANCE_V2_RUN_UI_ENABLED ? realSystem?.workspaceId : undefined,
    ASSURANCE_V2_RUN_UI_ENABLED ? realSystem?.id : undefined,
  )
  const scopeKey = evaluationScopeKey({
    organizationId: selectedOrg?.id,
    workspaceId: realSystem?.workspaceId,
    systemId: realSystem?.id,
    runId,
  })
  const [detailState, setDetailState] = useState<EvaluationScopeState<RunDetailState>>({
    scopeKey,
    value: { run: null, loading: false, error: null },
  })

  const scopeCanLoad = Boolean(
    ASSURANCE_V2_RUN_UI_ENABLED
      && selectedOrg?.id
      && realSystem?.workspaceId
      && realSystem.id,
  )
  // Keep payload, loading, and failure state on the same exact scope key.
  const {
    run,
    loading: detailLoading,
    error: detailError,
  } = readEvaluationScopeState(detailState, scopeKey, {
    run: null,
    loading: scopeCanLoad,
    error: null,
  })

  useEffect(() => {
    let current = true
    setDetailState({
      scopeKey,
      value: { run: null, loading: scopeCanLoad, error: null },
    })
    if (!ASSURANCE_V2_RUN_UI_ENABLED || !selectedOrg?.id || !realSystem?.workspaceId || !realSystem.id) {
      return () => { current = false }
    }

    void workbench.getRun(runId)
      .then((result) => {
        if (current) {
          setDetailState({
            scopeKey,
            value: { run: result, loading: false, error: null },
          })
        }
      })
      .catch((reason) => {
        if (!current || reason instanceof StaleEvaluationWorkbenchResultError) return
        setDetailState({
          scopeKey,
          value: {
            run: null,
            loading: false,
            error: reason instanceof Error ? reason : new Error('Unable to load evaluation evidence.'),
          },
        })
      })

    return () => { current = false }
  }, [realSystem?.id, realSystem?.workspaceId, runId, scopeCanLoad, scopeKey, selectedOrg?.id, workbench.getRun])

  const retry = () => {
    const retryScopeKey = scopeKey
    setDetailState({
      scopeKey: retryScopeKey,
      value: { run: null, loading: true, error: null },
    })
    void workbench.getRun(runId)
      .then((result) => {
        setDetailState((current) => writeEvaluationScopeState(
          current,
          retryScopeKey,
          { run: result, loading: false, error: null },
        ))
      })
      .catch((reason) => {
        if (reason instanceof StaleEvaluationWorkbenchResultError) return
        setDetailState((current) => writeEvaluationScopeState(
          current,
          retryScopeKey,
          {
            run: null,
            loading: false,
            error: reason instanceof Error ? reason : new Error('Unable to load evaluation evidence.'),
          },
        ))
      })
  }

  const initialLoading = orgLoading || systemLoading || detailLoading || (!run && !detailError && Boolean(
    ASSURANCE_V2_RUN_UI_ENABLED && selectedOrg?.id && realSystem?.workspaceId && realSystem.id,
  ))

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
            <p className="text-xs font-black uppercase tracking-wide text-[#59615D]">Assurance preview</p>
            <h1 className="text-3xl font-black tracking-[-0.02em]">Evidence trust panel</h1>
            <p className="mt-1 break-all font-mono text-xs font-bold text-[#59615D]">{runId}</p>
          </div>
        </div>
      </header>

      <section className="border-2 border-[#0F1412] bg-[#FFF1D6] p-4 text-sm font-semibold text-[#5B492E]">
        This preview is read-only and default-off at the API. It renders only a validated, scope-matched v2 run response; unavailable or denied data is never replaced with legacy or fixture evidence.
      </section>

      {!ASSURANCE_V2_UI_ENABLED ? (
        <section className="border-4 border-[#0F1412] bg-[#F3F5F0] p-6">
          <h2 className="text-xl font-black">Assurance preview disabled</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">Set <code className="font-mono font-black">NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED=true</code> only in an allowlisted environment. The API must independently enable <code className="font-mono font-black">assurance_v2_enabled</code> before any v2 response can render.</p>
        </section>
      ) : !ASSURANCE_V2_RUN_UI_ENABLED ? (
        <section className="border-4 border-[#0F1412] bg-[#F3F5F0] p-6">
          <h2 className="text-xl font-black">Assurance run preview disabled</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">Set <code className="font-mono font-black">NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED=true</code> only when this read-only surface is approved. The API must independently enable <code className="font-mono font-black">assurance_v2_runs_enabled</code> before any run response can render.</p>
        </section>
      ) : !selectedOrg && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an organization</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">An organization is required before this scoped run can be retrieved.</p>
        </section>
      ) : !realSystem?.workspaceId && !initialLoading ? (
        <section className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <h2 className="text-xl font-black">Choose an AI system</h2>
          <p className="mt-2 text-sm font-semibold text-[#59615D]">A real selected system with a workspace binding is required before this run can be retrieved.</p>
        </section>
      ) : initialLoading ? (
        <section aria-label="Loading evaluation evidence" className="space-y-3 border-4 border-[#0F1412] bg-[#FCFDF8] p-6">
          <div className="h-11 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
          <div className="h-28 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
          <div className="h-40 w-full animate-pulse bg-[#E5E9E3] motion-reduce:animate-none" />
        </section>
      ) : detailError ? (
        <EvaluationWorkbenchStatusNotice
          error={detailError}
          onRetry={retry}
        />
      ) : run ? (
        <EvidenceTrustPanel run={run} />
      ) : (
        <section role="alert" className="border-4 border-[#D83A2E] bg-red-50 p-6">
          <h2 className="text-xl font-black text-[#8F2019]">Evaluation evidence unavailable</h2>
          <p className="mt-2 text-sm font-semibold text-[#5B211D]">The scoped v2 run did not return a response. No legacy result was substituted.</p>
        </section>
      )}
    </div>
  )
}

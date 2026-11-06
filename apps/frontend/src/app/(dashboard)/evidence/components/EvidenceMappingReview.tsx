'use client'

import { useEffect, useState } from 'react'

import { BTN, BTN_P, LABEL, MUTED, Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'
import type {
  ControlAssessment,
  EvidenceMapping,
  EvidenceMappingReviewInput,
} from '@/lib/api/hooks/useGovernanceAssurance'

type EvidenceMappingReviewProps = {
  mapping: EvidenceMapping
  control?: ControlAssessment
  /** null while the role is still loading: neither the form nor the read-only note shows. */
  canReview: boolean | null
  onReview: (mappingId: string, review: EvidenceMappingReviewInput) => Promise<EvidenceMapping>
  onRefresh: () => Promise<void>
}

function stateLabel(state: EvidenceMapping['state']) {
  return state.charAt(0).toUpperCase() + state.slice(1)
}

// A candidate mapping waits on a reviewer; only an accepted one counts as support.
const STATE_TONE = { accepted: 'done', rejected: 'block' } as const

export function EvidenceMappingReview({ mapping, control, canReview, onReview, onRefresh }: EvidenceMappingReviewProps) {
  const [current, setCurrent] = useState(mapping)
  const [rationale, setRationale] = useState(mapping.rationale || '')
  const [saving, setSaving] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setCurrent(mapping)
    setRationale(mapping.rationale || '')
    setError(null)
  }, [mapping])

  const externalId = control?.externalId || 'Unresolved control'
  const controlTitle = control?.title || `Assessment ${mapping.controlAssessmentId}`

  const review = async (state: EvidenceMappingReviewInput['state']) => {
    setSaving(true)
    setError(null)
    try {
      const updated = await onReview(mapping.id, {
        state,
        rationale: rationale.trim() || null,
        reviewVersion: current.reviewVersion,
      })
      setCurrent(updated)
      setRationale(updated.rationale || '')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Mapping review failed')
    } finally {
      setSaving(false)
    }
  }

  const refresh = async () => {
    setRefreshing(true)
    try {
      await onRefresh()
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Mapping refresh failed')
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <section
      aria-label={`Mapping review for ${externalId}`}
      className="rounded-xl border border-[var(--fm-line)] bg-white p-4"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className={cn('m-0', LABEL)}>Control mapping</p>
          <h4 className="mt-1.5 text-[14.5px] font-semibold">{externalId} — {controlTitle}</h4>
          <p className={cn('mt-1.5 text-[13px]', MUTED)}>
            {current.rationale || 'No mapping rationale was supplied.'}
          </p>
        </div>
        <span className="shrink-0">
          <Pill tone={current.state === 'accepted' || current.state === 'rejected' ? STATE_TONE[current.state] : 'you'} dot={current.state !== 'accepted' && current.state !== 'rejected'}>
            {stateLabel(current.state)}
          </Pill>
        </span>
      </div>

      {canReview ? (
        <div className="mt-4 grid gap-3 border-t border-[var(--fm-line)] pt-4">
          <label className="block text-[12px] font-medium text-[var(--fm-ink2)]" htmlFor={`mapping-rationale-${mapping.id}`}>
            Review rationale for {externalId}
          </label>
          <textarea
            id={`mapping-rationale-${mapping.id}`}
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            rows={3}
            className="w-full resize-y rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white p-3 text-[13.5px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]"
            placeholder="Record why this evidence does or does not support the control."
          />
          {error ? (
            <div role="alert" className="rounded-[10px] bg-[#fde8e8] px-3 py-2.5 text-[13px] text-[#b42318]">
              <p className="m-0">{error}. Reload the mapping before retrying if another reviewer changed it.</p>
              <button
                type="button"
                disabled={refreshing}
                onClick={() => void refresh()}
                className={cn(BTN, 'mt-3 h-8 px-3.5 text-[12.5px]')}
              >
                {refreshing ? 'Reloading mapping' : 'Reload mapping'}
              </button>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={() => void review('accepted')}
              className={cn(BTN_P, 'h-9 px-4 text-[12.5px]')}
            >
              {saving ? 'Saving review' : `Accept mapping to ${externalId}`}
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void review('rejected')}
              className={cn(BTN, 'h-9 px-4 text-[12.5px]')}
            >
              Reject mapping to {externalId}
            </button>
          </div>
        </div>
      ) : canReview === false ? (
        <p className={cn('m-0 mt-4 border-t border-[var(--fm-line)] pt-3 text-[13px]', MUTED)}>
          Read-only access. A governance editor must review this mapping.
        </p>
      ) : null}
    </section>
  )
}

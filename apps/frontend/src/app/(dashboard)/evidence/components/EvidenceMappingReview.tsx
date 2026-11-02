'use client'

import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import type {
  ControlAssessment,
  EvidenceMapping,
  EvidenceMappingReviewInput,
} from '@/lib/api/hooks/useGovernanceAssurance'

type EvidenceMappingReviewProps = {
  mapping: EvidenceMapping
  control?: ControlAssessment
  canReview: boolean
  onReview: (mappingId: string, review: EvidenceMappingReviewInput) => Promise<EvidenceMapping>
  onRefresh: () => Promise<void>
}

function stateLabel(state: EvidenceMapping['state']) {
  return state.charAt(0).toUpperCase() + state.slice(1)
}

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
      className="p-4 fm-card"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--fm-ink2)]">Control mapping</p>
          <h4 className="mt-1 text-base font-semibold">{externalId} — {controlTitle}</h4>
          <p className="mt-2 text-sm text-[#39413D]">
            {current.rationale || 'No mapping rationale was supplied.'}
          </p>
        </div>
        <span className={`w-fit border border-[var(--fm-line)] px-2 py-1 text-xs font-semibold uppercase ${
          current.state === 'accepted'
            ? 'bg-[#DDF4EA]'
            : current.state === 'rejected'
              ? 'bg-[#FFF0ED]'
              : 'bg-[#FFF4DE]'
        }`}>
          {stateLabel(current.state)}
        </span>
      </div>

      {canReview ? (
        <div className="mt-4 space-y-3 border-t border-[var(--fm-line)] pt-4">
          <label className="block text-xs font-semibold uppercase tracking-[0.08em]" htmlFor={`mapping-rationale-${mapping.id}`}>
            Review rationale for {externalId}
          </label>
          <textarea
            id={`mapping-rationale-${mapping.id}`}
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            rows={3}
            className="w-full resize-y border border-[var(--fm-line)] bg-white p-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
            placeholder="Record why this evidence does or does not support the control."
          />
          {error ? (
            <div role="alert" className="border-2 border-[#B3261E] bg-[#FFF0ED] p-3 text-sm font-bold text-[#7B1D18]">
              <p>{error}. Reload the mapping before retrying if another reviewer changed it.</p>
              <Button
                type="button"
                disabled={refreshing}
                onClick={() => void refresh()}
                variant="neutral"
                className="mt-3 font-semibold fm-card"
              >
                {refreshing ? 'Reloading mapping' : 'Reload mapping'}
              </Button>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={saving}
              onClick={() => void review('accepted')}
              className="bg-[#0B7659] font-semibold text-white hover:bg-[#095F49] rounded-[14px] shadow-[var(--fm-shadow)]"
            >
              {saving ? 'Saving review' : `Accept mapping to ${externalId}`}
            </Button>
            <Button
              type="button"
              disabled={saving}
              onClick={() => void review('rejected')}
              variant="neutral"
              className="bg-[#FFF0ED] font-semibold rounded-[14px] shadow-[var(--fm-shadow)]"
            >
              Reject mapping to {externalId}
            </Button>
          </div>
        </div>
      ) : (
        <p className="mt-4 border-t border-[var(--fm-line)] pt-3 text-sm font-bold text-[var(--fm-ink2)]">
          Read-only access. A governance editor must review this mapping.
        </p>
      )}
    </section>
  )
}

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
}

function stateLabel(state: EvidenceMapping['state']) {
  return state.charAt(0).toUpperCase() + state.slice(1)
}

export function EvidenceMappingReview({ mapping, control, canReview, onReview }: EvidenceMappingReviewProps) {
  const [current, setCurrent] = useState(mapping)
  const [rationale, setRationale] = useState(mapping.rationale || '')
  const [saving, setSaving] = useState(false)
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

  return (
    <section
      aria-label={`Mapping review for ${externalId}`}
      className="border-2 border-[#0F1412] bg-[#FCFDF8] p-4 shadow-[4px_4px_0_0_#0F1412]"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#59615D]">Control mapping</p>
          <h4 className="mt-1 text-base font-black">{externalId} — {controlTitle}</h4>
          <p className="mt-2 text-sm text-[#39413D]">
            {current.rationale || 'No mapping rationale was supplied.'}
          </p>
        </div>
        <span className={`w-fit border-2 border-[#0F1412] px-2 py-1 text-xs font-black uppercase ${
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
        <div className="mt-4 space-y-3 border-t-2 border-[#0F1412] pt-4">
          <label className="block text-xs font-black uppercase tracking-[0.08em]" htmlFor={`mapping-rationale-${mapping.id}`}>
            Review rationale for {externalId}
          </label>
          <textarea
            id={`mapping-rationale-${mapping.id}`}
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            rows={3}
            className="w-full resize-y rounded-none border-2 border-[#0F1412] bg-white p-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
            placeholder="Record why this evidence does or does not support the control."
          />
          {error ? (
            <p role="alert" className="border-2 border-[#B3261E] bg-[#FFF0ED] p-2 text-sm font-bold text-[#7B1D18]">
              {error}. Refresh the run before retrying if another reviewer changed it.
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              disabled={saving}
              onClick={() => void review('accepted')}
              className="rounded-none border-2 border-[#0F1412] bg-[#0B7659] font-black uppercase text-white shadow-[3px_3px_0_0_#0F1412] hover:bg-[#095F49]"
            >
              {saving ? 'Saving review' : `Accept mapping to ${externalId}`}
            </Button>
            <Button
              type="button"
              disabled={saving}
              onClick={() => void review('rejected')}
              variant="neutral"
              className="rounded-none border-2 border-[#0F1412] bg-[#FFF0ED] font-black uppercase shadow-[3px_3px_0_0_#0F1412]"
            >
              Reject mapping to {externalId}
            </Button>
          </div>
        </div>
      ) : (
        <p className="mt-4 border-t-2 border-[#0F1412] pt-3 text-sm font-bold text-[#59615D]">
          Read-only access. A governance editor must review this mapping.
        </p>
      )}
    </section>
  )
}

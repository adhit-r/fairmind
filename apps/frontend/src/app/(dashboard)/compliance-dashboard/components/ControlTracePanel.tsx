'use client'

import { useEffect, useState } from 'react'
import { IconCheck, IconLink } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import type { ControlAssessment } from '@/lib/api/hooks/useGovernanceAssurance'

export type WorkbenchControl = ControlAssessment

type ControlUpdate = Pick<ControlAssessment, 'applicability' | 'status' | 'owner'>

type ControlTracePanelProps = {
  control: WorkbenchControl
  canEdit: boolean
  onUpdate: (control: WorkbenchControl, update: ControlUpdate) => Promise<void>
}

function readable(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatDate(value: string | null) {
  if (!value) return 'Capture time unavailable'
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return value
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

export function ControlTracePanel({ control, canEdit, onUpdate }: ControlTracePanelProps) {
  const [owner, setOwner] = useState(control.owner || '')
  const [applicability, setApplicability] = useState(control.applicability)
  const [status, setStatus] = useState(control.status)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setOwner(control.owner || '')
    setApplicability(control.applicability)
    setStatus(control.status)
  }, [control.applicability, control.id, control.owner, control.status])

  const save = async () => {
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      await onUpdate(control, { owner: owner.trim() || null, applicability, status })
      setSaved(true)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Control update failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section
      id={`trace-${control.id}`}
      role="region"
      aria-label={`Trace for ${control.externalId}`}
      className="border-2 border-[#0F1412] bg-[#F3F5F0] p-4 sm:p-5"
    >
      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.8fr)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#0B7659]">Requirement trace</p>
          <h3 className="mt-1 text-base font-black">
            {control.parentRequirementId || 'Parent requirement'}: {control.parentRequirementTitle || control.title}
          </h3>
          <p className="mt-2 max-w-[70ch] text-sm text-[#59615D]">{control.statement}</p>

          <div className="mt-4 border-2 border-[#0F1412] bg-[#FCFDF8] p-3">
            <p className="text-xs font-black uppercase tracking-[0.1em]">Mapping rationale</p>
            <p className="mt-1 text-sm">
              {control.mappingRationale || 'No reviewed mapping rationale is available for this control yet.'}
            </p>
          </div>

          <div className="mt-4">
            <p className="text-xs font-black uppercase tracking-[0.1em]">Evidence trail</p>
            {control.evidenceTrace?.length ? (
              <ol className="mt-2 divide-y-2 divide-[#0F1412] border-2 border-[#0F1412] bg-[#FCFDF8]">
                {control.evidenceTrace.map((item) => (
                  <li key={item.id} className="grid gap-1 p-3 text-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
                    <div className="flex items-start gap-2">
                      <IconLink aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-[#0B7659]" />
                      <div>
                        <p className="font-black">{item.label}</p>
                        <p className="text-[#59615D]">{item.kind} · {formatDate(item.capturedAt)}</p>
                      </div>
                    </div>
                    <span className="w-fit border-2 border-[#0F1412] bg-[#FFF4DE] px-2 py-1 text-xs font-black uppercase">
                      {item.state}
                    </span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-2 border-2 border-[#0F1412] bg-[#FCFDF8] p-3 text-sm font-bold">
                No evidence links have been reviewed for this control.
              </p>
            )}
          </div>
        </div>

        {canEdit ? (
          <form
            className="border-2 border-[#0F1412] bg-[#FCFDF8] p-4"
            onSubmit={(event) => {
              event.preventDefault()
              void save()
            }}
          >
            <h3 className="font-black uppercase">Assessment update</h3>
            <div className="mt-4 space-y-4">
            <label className="block text-sm font-black" htmlFor={`owner-${control.id}`}>
              Control owner
              <input
                id={`owner-${control.id}`}
                value={owner}
                onChange={(event) => setOwner(event.target.value)}
                className="mt-1 min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
                placeholder="owner@company.test"
              />
            </label>

            <label className="block text-sm font-black" htmlFor={`applicability-${control.id}`}>
              Applicability
              <select
                id={`applicability-${control.id}`}
                value={applicability}
                onChange={(event) => setApplicability(event.target.value)}
                className="mt-1 min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
              >
                <option value="applicable">Applicable</option>
                <option value="not_applicable">Not applicable</option>
                <option value="pending">Pending decision</option>
              </select>
            </label>

            <label className="block text-sm font-black" htmlFor={`state-${control.id}`}>
              Assessment state
              <select
                id={`state-${control.id}`}
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="mt-1 min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] px-3 py-2 font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
              >
                <option value="not_started">Not started</option>
                <option value="partial">Partial</option>
                <option value="ready_for_review">Ready for review</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
              </select>
            </label>
            </div>

            {error ? <p role="alert" className="mt-3 text-sm font-bold text-[#B3261E]">{error}</p> : null}
            <p aria-live="polite" className="mt-3 min-h-5 text-sm font-bold text-[#0B7659]">
              {saved ? <span className="inline-flex items-center gap-1"><IconCheck aria-hidden="true" /> Changes saved</span> : null}
            </p>
            <Button
              type="submit"
              disabled={saving}
              className="mt-2 w-full rounded-none border-[#0F1412] bg-[#FF6B35] font-black uppercase text-[#0F1412]"
            >
              {saving ? 'Saving changes' : 'Save control changes'}
            </Button>
            <p className="mt-3 text-xs text-[#59615D]">
              State labels record reviewer workflow. Evidence acceptance remains a separate decision.
            </p>
          </form>
        ) : (
          <aside className="border-2 border-[#0F1412] bg-[#FCFDF8] p-4">
            <h3 className="font-black uppercase">Read-only access</h3>
            <p className="mt-2 text-sm text-[#59615D]">
              You can inspect this assessment and its evidence trace, but your organization role cannot change control state.
            </p>
          </aside>
        )}
      </div>
    </section>
  )
}

export { readable }

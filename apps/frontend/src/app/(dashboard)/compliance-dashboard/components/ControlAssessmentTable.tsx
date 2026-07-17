'use client'

import { useMemo, useState } from 'react'
import { IconChevronDown, IconChevronRight, IconSearch } from '@tabler/icons-react'

import { Skeleton } from '@/components/ui/skeleton'

import { ControlTracePanel, readable, type WorkbenchControl } from './ControlTracePanel'

type ControlAssessmentTableProps = {
  controls: WorkbenchControl[]
  loading: boolean
  frameworkName: string
  versionLabel: string
  onUpdate: (
    control: WorkbenchControl,
    update: Pick<WorkbenchControl, 'applicability' | 'status' | 'owner'>,
  ) => Promise<void>
}

const cellClass = 'flex min-h-11 items-center justify-between gap-3 border-b border-[#CCD2CE] px-3 py-2 text-sm md:table-cell md:border-b-0 md:align-middle'
const mobileLabelClass = 'text-[10px] font-black uppercase tracking-[0.1em] text-[#59615D] md:hidden'

function valueOrUnavailable(value?: string) {
  return value ? readable(value) : 'Not specified'
}

function FreshnessLabel({ control }: { control: WorkbenchControl }) {
  const value = control.freshness || (control.acceptedEvidenceCount ? 'current' : 'missing')
  const color = value === 'current'
    ? 'bg-[#DDF4EA]'
    : value === 'stale'
      ? 'bg-[#FFF4DE]'
      : 'bg-[#FFF0ED]'
  return (
    <span className={`inline-flex border-2 border-[#0F1412] px-2 py-1 text-[11px] font-black uppercase ${color}`}>
      {readable(value)}
    </span>
  )
}

function TableLoading() {
  return (
    <div aria-label="Loading control assessments" className="space-y-2 p-4">
      {Array.from({ length: 4 }, (_, index) => (
        <Skeleton key={index} className="h-14 rounded-none" />
      ))}
    </div>
  )
}

export function ControlAssessmentTable({
  controls,
  loading,
  frameworkName,
  versionLabel,
  onUpdate,
}: ControlAssessmentTableProps) {
  const [query, setQuery] = useState('')
  const [mandatoryOnly, setMandatoryOnly] = useState(false)
  const [missingEvidenceOnly, setMissingEvidenceOnly] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filtered = useMemo(() => controls.filter((control) => {
    const matchesQuery = !query.trim() || `${control.externalId} ${control.title} ${control.owner || ''}`
      .toLowerCase()
      .includes(query.trim().toLowerCase())
    const matchesMandatory = !mandatoryOnly || control.obligation === 'mandatory'
    const matchesEvidence = !missingEvidenceOnly || (control.acceptedEvidenceCount ?? 0) === 0
    return matchesQuery && matchesMandatory && matchesEvidence
  }), [controls, mandatoryOnly, missingEvidenceOnly, query])

  return (
    <section aria-labelledby="controls-heading" className="border-2 border-[#0F1412] bg-[#FCFDF8]">
      <div className="flex flex-col gap-3 border-b-2 border-[#0F1412] bg-[#F3F5F0] px-4 py-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h2 id="controls-heading" className="text-base font-black uppercase">Control assessments</h2>
          <p className="mt-1 text-sm text-[#59615D]">{frameworkName} {versionLabel} · {filtered.length} of {controls.length} controls shown</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <label className="relative block sm:min-w-[260px]" htmlFor="control-search">
            <span className="sr-only">Search controls</span>
            <IconSearch aria-hidden="true" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
            <input
              id="control-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search ID, title, or owner"
              className="min-h-11 w-full rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] py-2 pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
            />
          </label>
          <label className="flex min-h-11 cursor-pointer items-center gap-2 border-2 border-[#0F1412] bg-[#FCFDF8] px-3 text-sm font-black">
            <input
              type="checkbox"
              checked={mandatoryOnly}
              onChange={(event) => setMandatoryOnly(event.target.checked)}
              className="h-5 w-5 accent-[#0B7659]"
            />
            Mandatory controls
          </label>
          <label className="flex min-h-11 cursor-pointer items-center gap-2 border-2 border-[#0F1412] bg-[#FCFDF8] px-3 text-sm font-black">
            <input
              type="checkbox"
              checked={missingEvidenceOnly}
              onChange={(event) => setMissingEvidenceOnly(event.target.checked)}
              className="h-5 w-5 accent-[#0B7659]"
            />
            Missing accepted evidence
          </label>
        </div>
      </div>

      {loading && controls.length === 0 ? (
        <TableLoading />
      ) : filtered.length === 0 ? (
        <div className="p-8 text-center">
          <h3 className="text-lg font-black uppercase">No controls match these filters</h3>
          <p className="mt-2 text-sm text-[#59615D]">Clear a filter or search term to return to the full control set.</p>
        </div>
      ) : (
        <div className="overflow-visible md:overflow-x-auto">
          <table className="block w-full border-collapse md:table md:min-w-[980px]">
            <caption className="sr-only">System-scoped control assessments and evidence state</caption>
            <thead className="hidden border-b-2 border-[#0F1412] bg-[#0F1412] text-[#FCFDF8] md:table-header-group">
              <tr>
                {['Control', 'Requirement', 'Application', 'Owner', 'State', 'Accepted evidence', 'Latest evaluation', 'Freshness', 'Findings'].map((heading) => (
                  <th key={heading} scope="col" className="px-3 py-3 text-left text-[11px] font-black uppercase tracking-[0.08em]">{heading}</th>
                ))}
              </tr>
            </thead>
            {filtered.map((control) => {
              const expanded = expandedId === control.id
              return (
                <tbody
                  key={control.id}
                  data-testid={`control-record-${control.externalId}`}
                  className="mb-3 block border-2 border-[#0F1412] last:mb-0 md:table-row-group md:border-0 [&:not(:last-child)>tr:first-child]:md:border-b [&:not(:last-child)>tr:first-child]:md:border-[#CCD2CE]"
                >
                  <tr className="block bg-[#FCFDF8] md:table-row">
                    <td className={`${cellClass} font-black`}>
                      <span className={mobileLabelClass}>Control</span>
                      <button
                        type="button"
                        aria-expanded={expanded}
                        aria-controls={`trace-${control.id}`}
                        aria-label={`${expanded ? 'Collapse' : 'Expand'} control ${control.externalId}`}
                        onClick={() => setExpandedId(expanded ? null : control.id)}
                        className="inline-flex min-h-11 items-center gap-2 text-left font-black underline-offset-4 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[#0B7659] focus-visible:ring-offset-2"
                      >
                        {expanded ? <IconChevronDown aria-hidden="true" /> : <IconChevronRight aria-hidden="true" />}
                        <span>{control.externalId}</span>
                      </button>
                    </td>
                    <td className={`${cellClass} md:max-w-[300px]`}>
                      <span className={mobileLabelClass}>Requirement</span>
                      <span className="text-right font-bold md:text-left">{control.title}</span>
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>Application</span>
                      <span className="text-right md:text-left">
                        <span className="block font-black">{valueOrUnavailable(control.obligation)}</span>
                        <span className="block text-xs text-[#59615D]">{valueOrUnavailable(control.application)}</span>
                      </span>
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>Owner</span>
                      <span className="max-w-[180px] break-words text-right font-bold md:text-left">{control.owner || 'Unassigned'}</span>
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>State</span>
                      <span className="border-2 border-[#0F1412] bg-[#F3F5F0] px-2 py-1 text-[11px] font-black uppercase">{readable(control.status)}</span>
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>Accepted evidence</span>
                      <span className="font-black">{control.acceptedEvidenceCount ?? 0}</span>
                    </td>
                    <td className={`${cellClass} md:max-w-[200px]`}>
                      <span className={mobileLabelClass}>Latest evaluation</span>
                      <span className="text-right md:text-left">
                        <span className="block font-bold">{control.latestEvaluation || 'Not run'}</span>
                        <span className="block text-xs text-[#59615D]">
                          {control.latestEvaluationAt ? new Date(control.latestEvaluationAt).toLocaleDateString('en') : 'No capture date'}
                        </span>
                      </span>
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>Freshness</span>
                      <FreshnessLabel control={control} />
                    </td>
                    <td className={cellClass}>
                      <span className={mobileLabelClass}>Findings</span>
                      <span className={`font-black ${(control.openFindings ?? 0) > 0 ? 'text-[#B3261E]' : ''}`}>
                        {control.openFindings ?? 0} open
                      </span>
                    </td>
                  </tr>
                  {expanded ? (
                    <tr className="block border-t-2 border-[#0F1412] md:table-row">
                      <td colSpan={9} className="block p-3 md:table-cell md:p-4">
                        <ControlTracePanel control={control} onUpdate={onUpdate} />
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              )
            })}
          </table>
        </div>
      )}
    </section>
  )
}

'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { IconAlertTriangle, IconArrowRight, IconRefresh } from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useOrg } from '@/context/OrgContext'
import {
  useFrameworkVersions,
  useGovernanceAssurance,
} from '@/lib/api/hooks/useGovernanceAssurance'

function countLabel(value: number, singular: string, plural = `${singular}s`) {
  return `${value} ${value === 1 ? singular : plural}`
}

function OverviewLoading() {
  return (
    <div aria-label="Loading assurance overview" className="space-y-4">
      <Skeleton className="h-24 w-full rounded-none" />
      <Skeleton className="h-36 w-full rounded-none" />
      <Skeleton className="h-48 w-full rounded-none" />
    </div>
  )
}

export default function AIGovernancePage() {
  const { selectedOrg } = useOrg()
  const { selectedSystem } = useSystemContext()
  const orgId = selectedOrg?.id
  const assuranceBase = useGovernanceAssurance(orgId, selectedSystem.id)
  const frameworkKey = assuranceBase.frameworks[0]?.frameworkKey
  const versionState = useFrameworkVersions(orgId, frameworkKey)
  const activeAssignment = useMemo(
    () => assuranceBase.assignments.find((assignment) => assignment.systemId === selectedSystem.id),
    [assuranceBase.assignments, selectedSystem.id],
  )
  const assurance = useGovernanceAssurance(orgId, selectedSystem.id, activeAssignment?.id)
  const assignedVersion = versionState.versions.find(
    (version) => version.id === activeAssignment?.frameworkVersionId,
  )
  const assignedFramework = assurance.frameworks.find(
    (framework) => framework.frameworkKey === assignedVersion?.frameworkKey,
  )
  const frameworkName = assignedFramework?.name || assignedVersion?.name || 'Framework'
  const readiness = assurance.readiness
  const loading = assurance.loading || versionState.loading || assurance.readinessLoading
  const error = assurance.error || versionState.error

  const refresh = async () => {
    await Promise.all([assurance.refresh(), versionState.refresh()])
  }

  return (
    <main
      data-testid="governance-assurance-overview"
      className="space-y-5 bg-[#FCFDF8] pb-10 text-[#0F1412]"
    >
      <header className="flex flex-col gap-3 border-b-4 border-[#0F1412] pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0B7659]">Governance overview</p>
          <h1 className="mt-1 text-2xl font-black uppercase tracking-tight sm:text-3xl">
            AI Governance Assurance
          </h1>
          <p className="mt-2 max-w-[72ch] text-sm font-medium text-[#59615D]">
            Review the selected system&apos;s framework scope, explicit blockers, and evidence-backed control state before making an assurance decision.
          </p>
        </div>
        <Button
          type="button"
          variant="neutral"
          onClick={() => void refresh()}
          className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] font-black uppercase"
        >
          <IconRefresh aria-hidden="true" />
          Refresh overview
        </Button>
      </header>

      <section
        aria-label="Assurance scope"
        className="grid border-2 border-[#0F1412] bg-[#F3F5F0] sm:grid-cols-2 xl:grid-cols-4"
      >
        {[
          ['Company', selectedOrg?.name || 'Not selected'],
          ['AI system', selectedSystem.name],
          ['Framework version', assignedVersion ? `${frameworkName} ${assignedVersion.versionLabel}` : 'Not assigned'],
          ['Review period', 'Current recorded state'],
        ].map(([label, value]) => (
          <div key={label} className="border-b-2 border-[#0F1412] px-4 py-3 last:border-b-0 sm:border-r-2 sm:[&:nth-child(2)]:border-r-0 sm:[&:nth-child(3)]:border-b-0 xl:border-b-0 xl:[&:nth-child(2)]:border-r-2 xl:[&:nth-child(3)]:border-r-2">
            <p className="text-[11px] font-black uppercase tracking-[0.12em] text-[#59615D]">{label}</p>
            <p className="mt-1 text-sm font-black">{value}</p>
          </div>
        ))}
      </section>

      {error ? (
        <Alert role="alert" className="rounded-none border-2 border-[#D83A2E] bg-[#FFF0ED] text-[#0F1412]">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription className="flex flex-col gap-3 font-bold sm:flex-row sm:items-center sm:justify-between">
            <span>{error.message}</span>
            <Button type="button" variant="neutral" onClick={() => void refresh()} className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8]">
              Retry assurance data
            </Button>
          </AlertDescription>
        </Alert>
      ) : loading ? (
        <OverviewLoading />
      ) : !activeAssignment || !assignedVersion ? (
        <section className="border-4 border-[#0F1412] bg-[#F3F5F0] p-7 shadow-[8px_8px_0_0_#0F1412]">
          <h2 className="text-xl font-black uppercase">Framework scope required</h2>
          <p className="mt-2 max-w-[65ch] text-sm text-[#59615D]">
            Activate a versioned framework for this AI system before readiness can be reviewed. No readiness counts are inferred while scope is missing.
          </p>
          <Button asChild className="mt-5 rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]">
            <Link href="/compliance-dashboard">
              Open frameworks and controls
              <IconArrowRight aria-hidden="true" />
            </Link>
          </Button>
        </section>
      ) : !readiness ? (
        <section className="border-2 border-[#0F1412] bg-[#FFF0ED] p-5">
          <h2 className="font-black uppercase">Readiness unavailable</h2>
          <p className="mt-1 text-sm text-[#59615D]">The assigned framework has no recorded readiness summary.</p>
        </section>
      ) : (
        <>
          <section aria-label="Readiness blockers" className="border-4 border-[#0F1412] bg-[#FCFDF8] shadow-[8px_8px_0_0_#0F1412]">
            <div className="border-b-4 border-[#0F1412] bg-[#0F1412] px-5 py-4 text-[#FCFDF8]">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#E97522]">Resolve before review</p>
              <h2 className="mt-1 text-xl font-black uppercase">Readiness Blockers</h2>
            </div>
            <div className="grid md:grid-cols-3">
              <div className="border-b-2 border-[#0F1412] p-5 md:border-b-0 md:border-r-2">
                <p className="text-2xl font-black text-[#D83A2E]">{readiness.blockingFindings}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.blockingFindings === 0
                    ? 'No blocking findings reported'
                    : countLabel(readiness.blockingFindings, 'blocking finding')}
                </p>
              </div>
              <div className="border-b-2 border-[#0F1412] p-5 md:border-b-0 md:border-r-2">
                <p className="text-2xl font-black text-[#B85A16]">{readiness.missingEvidence}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.missingEvidence === 0
                    ? 'No missing accepted evidence reported'
                    : `${countLabel(readiness.missingEvidence, 'control')} missing accepted evidence`}
                </p>
              </div>
              <div className="p-5">
                <p className="text-2xl font-black text-[#B85A16]">{readiness.staleEvidence}</p>
                <p className="mt-1 text-sm font-bold">
                  {readiness.staleEvidence === 0
                    ? 'No stale evidence reported'
                    : `${countLabel(readiness.staleEvidence, 'control')} with stale evidence`}
                </p>
              </div>
            </div>
          </section>

          <section aria-label={`${frameworkName} readiness`} className="border-2 border-[#0F1412] bg-[#FCFDF8]">
            <div className="border-b-2 border-[#0F1412] bg-[oklch(0.60_0.13_163)] px-5 py-4">
              <p className="text-xs font-black uppercase tracking-[0.14em]">Version {assignedVersion.versionLabel}</p>
              <h2 className="mt-1 text-xl font-black uppercase">{frameworkName} Readiness</h2>
              <p className="mt-1 text-sm font-bold">
                {readiness.accepted} accepted of {readiness.applicable} applicable controls. Counts reflect recorded assessments and reviewed evidence mappings.
              </p>
            </div>
            <dl className="grid grid-cols-2 divide-x-2 divide-y-2 divide-[#0F1412] sm:grid-cols-4 xl:grid-cols-7 xl:divide-y-0">
              {[
                ['Applicable', readiness.applicable],
                ['Accepted', readiness.accepted],
                ['Ready for review', readiness.readyForReview],
                ['Partial', readiness.partial],
                ['Not started', readiness.notStarted],
                ['Not applicable', readiness.notApplicable],
                ['Stale evidence', readiness.staleEvidence],
              ].map(([label, value]) => (
                <div key={label} className="min-h-[84px] p-3">
                  <dt className="text-[11px] font-black uppercase tracking-[0.08em] text-[#59615D]">{label}</dt>
                  <dd className="mt-2 text-xl font-black">
                    {value}{' '}
                    <span className="text-xs font-bold text-[#59615D]">{String(label).toLowerCase()}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="flex flex-col gap-3 border-t-2 border-[#0F1412] pt-5 sm:flex-row">
            <Button asChild className="rounded-none border-2 border-[#0F1412] bg-[#E97522] font-black uppercase text-[#0F1412]">
              <Link href="/compliance-dashboard">
                Review control assessments
                <IconArrowRight aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="neutral" className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] font-black uppercase">
              <Link href="/reports?view=builder">
                Open reports and assurance
                <IconArrowRight aria-hidden="true" />
              </Link>
            </Button>
          </div>

          <nav aria-label="Related governance workflows" className="grid border-2 border-[#0F1412] bg-[#F3F5F0] sm:grid-cols-3">
            {[
              ['/evidence?view=evaluations', 'Evidence & evaluations', 'Inspect provenance and review candidate mappings.'],
              ['/risks', 'Findings', 'Review open risks and finding context.'],
              ['/remediation', 'Remediation', 'Track corrective work and required re-tests.'],
            ].map(([href, label, description]) => (
              <Link key={href} href={href} className="border-b-2 border-[#0F1412] p-4 last:border-b-0 hover:bg-[#FCFDF8] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-[-4px] focus-visible:outline-[#0B7659] sm:border-b-0 sm:border-r-2 sm:last:border-r-0">
                <span className="font-black uppercase">{label}</span>
                <span className="mt-1 block text-sm text-[#59615D]">{description}</span>
              </Link>
            ))}
          </nav>
        </>
      )}
    </main>
  )
}

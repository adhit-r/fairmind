import Link from 'next/link'
import { IconArrowRight } from '@tabler/icons-react'

import { Card } from '@/components/ui/card'
import { BTN_P, LABEL, LINE, MUTED, Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

const releaseConditions = [
  'Independent calibration against named datasets, baselines, and failure thresholds',
  'Isolated non-root execution with bounded resources and deny-default network access',
  'Versioned result contracts, signed Passport V2 evidence, and independent security review',
]

const states = [
  ['Runtime state', 'Canonical execution API unmounted; direct requests fail closed'],
  ['Metadata state', 'Assurance target-kind vocabulary remains available for versioned planning'],
  ['Governance effect', 'No output from this legacy surface can support a governance decision'],
] as const

export function UnsupportedEvaluationPackNotice({
  title,
  scope,
}: {
  title: string
  scope: string
}) {
  return (
    <section className="mx-auto max-w-3xl space-y-6 px-6 py-10" aria-labelledby="unsupported-pack-page-title">
      <header className="max-w-[70ch]">
        <h1 id="unsupported-pack-page-title" className="text-2xl font-semibold tracking-tight text-[var(--fm-ink)]">
          {title}
        </h1>
        <p className={cn('mt-2 text-sm leading-6', MUTED)}>{scope}</p>
      </header>

      <Card role="status" aria-labelledby="unsupported-pack-status-title" className="p-6 md:p-8">
        <Pill tone="warn" dot>Capability unavailable</Pill>
        <h2 id="unsupported-pack-status-title" className="mt-4 text-lg font-semibold tracking-tight text-[var(--fm-ink)]">
          Evaluation pack unavailable
        </h2>
        <p className={cn('mt-2 max-w-[70ch] text-sm leading-6', MUTED)}>
          FairMind does not execute this evaluator in the current release. The pack has not passed independent calibration, isolated-runtime, evidence-contract, and release-gate verification.
        </p>
        <p className="mt-2 max-w-[70ch] text-sm font-semibold leading-6 text-[#b42318]">
          No score, result, evidence, or compliance conclusion is generated here.
        </p>

        <dl className={cn('mt-6 border-t text-sm', LINE)}>
          {states.map(([term, detail]) => (
            <div key={term} className={cn('grid gap-1 border-b py-3 last:border-b-0 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6', LINE)}>
              <dt className="font-semibold text-[var(--fm-ink)]">{term}</dt>
              <dd className={MUTED}>{detail}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <Card aria-labelledby="unsupported-pack-release-title" className="p-6 md:p-8">
        <p className={LABEL}>Before this returns</p>
        <h2 id="unsupported-pack-release-title" className="mt-2 text-lg font-semibold tracking-tight text-[var(--fm-ink)]">
          Release conditions
        </h2>
        <p className={cn('mt-2 max-w-[70ch] text-sm', MUTED)}>
          This capability remains unavailable until every control below is implemented and verified.
        </p>
        <ul className="mt-4 space-y-2">
          {releaseConditions.map((condition) => (
            <li key={condition} className={cn('flex gap-3 border-t pt-2 text-sm text-[var(--fm-ink)] first:border-t-0 first:pt-0', LINE)}>
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--fm-ink3)]" />
              <span>{condition}</span>
            </li>
          ))}
        </ul>
        <Link href="/tests" className={cn(BTN_P, 'mt-6')}>
          Open Evaluation Runs
          <IconArrowRight aria-hidden="true" className="h-4 w-4" />
        </Link>
      </Card>
    </section>
  )
}

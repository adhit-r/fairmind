import Link from 'next/link'
import { IconArrowRight, IconLock, IconShieldCheck } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'

const releaseConditions = [
  'Independent calibration against named datasets, baselines, and failure thresholds',
  'Isolated non-root execution with bounded resources and deny-default network access',
  'Versioned result contracts, signed Passport V2 evidence, and independent security review',
]

export function UnsupportedEvaluationPackNotice({
  title,
  scope,
}: {
  title: string
  scope: string
}) {
  return (
    <section className="space-y-8" aria-labelledby="unsupported-pack-page-title">
      <header className="max-w-[70ch]">
        <h1 id="unsupported-pack-page-title" className="text-4xl font-black tracking-tight text-[#0F1412]">
          {title}
        </h1>
        <p className="mt-2 text-base font-semibold leading-7 text-[#59615D]">
          {scope}
        </p>
      </header>

      <section
        role="status"
        aria-labelledby="unsupported-pack-status-title"
        className="border-4 border-[#0F1412] bg-[#FCFDF8] p-6 shadow-[8px_8px_0_0_#0F1412] md:p-8"
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center border-2 border-[#0F1412] bg-[#FF6B35] shadow-[4px_4px_0_0_#0F1412]">
            <IconLock aria-hidden="true" className="h-6 w-6" stroke={2.4} />
          </div>
          <div className="min-w-0">
            <span className="inline-flex border-2 border-[#0F1412] bg-[#F3F5F0] px-2 py-1 text-xs font-black uppercase tracking-[0.06em]">
              Capability unavailable
            </span>
            <h2 id="unsupported-pack-status-title" className="mt-3 text-2xl font-black text-[#0F1412]">
              Evaluation pack unavailable
            </h2>
            <p className="mt-3 max-w-[70ch] text-sm font-semibold leading-6 text-[#303834]">
              FairMind does not execute this evaluator in the current release. The pack has not passed independent calibration, isolated-runtime, evidence-contract, and release-gate verification.
            </p>
            <p className="mt-3 max-w-[70ch] text-sm font-black leading-6 text-[#8F2019]">
              No score, result, evidence, or compliance conclusion is generated here.
            </p>
          </div>
        </div>

        <dl className="mt-7 border-t-2 border-[#0F1412] text-sm">
          <div className="grid gap-1 border-b-2 border-[#0F1412] py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Runtime state</dt>
            <dd className="font-semibold text-[#303834]">Canonical execution API unmounted; direct requests fail closed</dd>
          </div>
          <div className="grid gap-1 border-b-2 border-[#0F1412] py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Metadata state</dt>
            <dd className="font-semibold text-[#303834]">Assurance target-kind vocabulary remains available for versioned planning</dd>
          </div>
          <div className="grid gap-1 py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Governance effect</dt>
            <dd className="font-semibold text-[#303834]">No output from this legacy surface can support a governance decision</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="unsupported-pack-release-title" className="border-2 border-[#0F1412] bg-[#F3F5F0] p-6 md:p-8">
        <div className="flex items-start gap-3">
          <IconShieldCheck aria-hidden="true" className="mt-0.5 h-6 w-6 shrink-0 text-[#0F766E]" stroke={2.4} />
          <div className="min-w-0">
            <h2 id="unsupported-pack-release-title" className="text-xl font-black text-[#0F1412]">
              Release conditions
            </h2>
            <p className="mt-2 max-w-[70ch] text-sm font-semibold text-[#59615D]">
              This capability remains unavailable until every control below is implemented and verified.
            </p>
          </div>
        </div>

        <ul className="mt-5 space-y-3">
          {releaseConditions.map((condition) => (
            <li key={condition} className="flex gap-3 border-t-2 border-[#0F1412] pt-3 text-sm font-bold text-[#303834] first:border-t-0 first:pt-0">
              <span aria-hidden="true" className="mt-1.5 h-2.5 w-2.5 shrink-0 border-2 border-[#0F1412] bg-[#0F766E]" />
              <span>{condition}</span>
            </li>
          ))}
        </ul>

        <Button asChild variant="neutral" className="mt-7 rounded-none border-[#0F1412] font-black">
          <Link href="/tests">
            Open Assurance workbench
            <IconArrowRight aria-hidden="true" />
          </Link>
        </Button>
      </section>
    </section>
  )
}

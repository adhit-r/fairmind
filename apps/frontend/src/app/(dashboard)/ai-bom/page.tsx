import Link from 'next/link'
import { IconArrowLeft, IconLock, IconShieldCheck } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'

const releaseConditions = [
  'Authenticated organization membership and exact action permissions',
  'Server-derived organization and actor identity on every mutation',
  'Tenant-scoped persistence, audit coverage, and independent security validation',
]

export default function AIBOMPage() {
  return (
    <main className="space-y-8" aria-labelledby="ai-bom-title">
      <header className="max-w-[70ch]">
        <h1 id="ai-bom-title" className="text-4xl font-black tracking-tight text-[#0F1412]">
          AI Bill of Materials
        </h1>
        <p className="mt-2 text-base font-semibold text-[#59615D]">
          The inventory surface is retained while FairMind replaces its legacy global API with a tenant-safe assurance contract.
        </p>
      </header>

      <section
        role="status"
        aria-labelledby="ai-bom-status-title"
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
            <h2 id="ai-bom-status-title" className="mt-3 text-2xl font-black text-[#0F1412]">
              Legacy AI-BOM access is quarantined
            </h2>
            <p className="mt-3 max-w-[70ch] text-sm font-semibold leading-6 text-[#303834]">
              FairMind does not load, create, update, or delete AI-BOM records from this screen. The former API did not enforce the authenticated tenant boundary required for governance evidence, so both its HTTP routes and dashboard actions are disabled.
            </p>
          </div>
        </div>

        <dl className="mt-7 border-t-2 border-[#0F1412] text-sm">
          <div className="grid gap-1 border-b-2 border-[#0F1412] py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Runtime state</dt>
            <dd className="font-semibold text-[#303834]">HTTP surface unmounted and direct mounting fails closed</dd>
          </div>
          <div className="grid gap-1 border-b-2 border-[#0F1412] py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Data access</dt>
            <dd className="font-semibold text-[#303834]">No AI-BOM records are requested or rendered</dd>
          </div>
          <div className="grid gap-1 py-4 sm:grid-cols-[minmax(11rem,0.45fr)_1fr] sm:gap-6">
            <dt className="font-black text-[#0F1412]">Governance effect</dt>
            <dd className="font-semibold text-[#303834]">No inventory result from this legacy capability can support a decision</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="ai-bom-release-title" className="border-2 border-[#0F1412] bg-[#F3F5F0] p-6 md:p-8">
        <div className="flex items-start gap-3">
          <IconShieldCheck aria-hidden="true" className="mt-0.5 h-6 w-6 shrink-0 text-[#0F766E]" stroke={2.4} />
          <div className="min-w-0">
            <h2 id="ai-bom-release-title" className="text-xl font-black text-[#0F1412]">
              Release conditions
            </h2>
            <p className="mt-2 max-w-[70ch] text-sm font-semibold text-[#59615D]">
              The capability stays unavailable until each control below is implemented and verified.
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
          <Link href="/ai-governance">
            <IconArrowLeft aria-hidden="true" />
            Return to AI Governance
          </Link>
        </Button>
      </section>
    </main>
  )
}

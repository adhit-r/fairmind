import { IconArrowUpRight } from '@tabler/icons-react'
import Link from 'next/link'

type CapabilityState =
  | 'validated'
  | 'metadata_only'
  | 'external_provider'
  | 'unavailable'
  | 'insufficient_data'

interface EvidenceGenerator {
  name: string
  href: string
  state: CapabilityState
  output: string
  boundary: string
  action: string
}

const GENERATORS: EvidenceGenerator[] = [
  {
    name: 'Environmental evidence',
    href: '/ai-governance',
    state: 'validated',
    output: 'Energy, carbon, water, and uncertainty records',
    boundary: 'The strongest evidence-grade vertical currently in this repository.',
    action: 'Open evaluator',
  },
  {
    name: 'LLM judge',
    href: '/llm-judge',
    state: 'external_provider',
    output: 'Provider-evaluated response assessment',
    boundary: 'Results depend on a configured external model provider.',
    action: 'Configure judge',
  },
  {
    name: 'Multimodal bias',
    href: '/multimodal-bias',
    state: 'metadata_only',
    output: 'Media metadata and statistical summary',
    boundary: 'The current path does not evaluate image, audio, or video content.',
    action: 'Inspect analyzer',
  },
  {
    name: 'Tabular bias',
    href: '/bias',
    state: 'unavailable',
    output: 'No evidence artifact from this route',
    boundary: 'The interface calls an evaluator endpoint that is not present.',
    action: 'Inspect route',
  },
  {
    name: 'Modern LLM bias',
    href: '/modern-bias',
    state: 'unavailable',
    output: 'No defensible evidence artifact',
    boundary: 'The current interface produces mock results and must not be exported as evidence.',
    action: 'Inspect route',
  },
  {
    name: 'AI BOM',
    href: '/ai-bom',
    state: 'metadata_only',
    output: 'Software and model inventory profile',
    boundary: 'The current path transforms supplied metadata; it does not verify the subject.',
    action: 'Open AI BOM',
  },
]

const STATE_STYLES: Record<CapabilityState, string> = {
  validated: 'bg-[#17714F] text-[#FBF8F1]',
  metadata_only: 'bg-[#F4DDC9] text-[#6F2D0A]',
  external_provider: 'bg-[#DCEFEA] text-[#0B5E4E]',
  unavailable: 'bg-[#F7DAD6] text-[#8D1C13]',
  insufficient_data: 'bg-[#E5E8E6] text-[#39423D]',
}

export function EvidenceGeneratorWorkbench() {
  return (
    <section
      aria-labelledby="evidence-generators-heading"
      className="border-4 border-[#101614] bg-[#FBF8F1] shadow-[6px_6px_0_#101614]"
    >
      <div className="grid gap-3 border-b-2 border-[#101614] bg-[#F0EEE7] p-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.65fr)] lg:items-end">
        <div>
          <p className="font-mono text-xs font-bold uppercase tracking-[0.16em] text-[#118A72]">
            Capability register
          </p>
          <h2 id="evidence-generators-heading" className="mt-1 text-xl font-black tracking-tight text-[#101614]">
            Evidence Generator Workbench
          </h2>
          <p className="mt-2 max-w-[70ch] text-sm font-medium text-[#5B665F]">
            Launch the available tool surfaces with their current evidence boundary visible. These states describe implementation maturity, not compliance.
          </p>
        </div>
        <p className="font-mono text-xs leading-5 text-[#39423D]">
          State vocabulary: validated, metadata_only, external_provider, unavailable, insufficient_data.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[920px] border-collapse text-left">
          <caption className="sr-only">
            Current evidence generator capabilities, outputs, implementation boundaries, and routes
          </caption>
          <thead className="bg-[#101614] text-[#FBF8F1]">
            <tr className="font-mono text-[11px] uppercase tracking-[0.12em]">
              <th scope="col" className="px-4 py-3 font-bold">Generator</th>
              <th scope="col" className="px-4 py-3 font-bold">Capability state</th>
              <th scope="col" className="px-4 py-3 font-bold">Current output</th>
              <th scope="col" className="px-4 py-3 font-bold">Evidence boundary</th>
              <th scope="col" className="px-4 py-3 text-right font-bold">Route</th>
            </tr>
          </thead>
          <tbody className="divide-y-2 divide-[#101614]">
            {GENERATORS.map((generator) => (
              <tr key={generator.name} className="align-top hover:bg-[#F0EEE7]">
                <th scope="row" className="px-4 py-4 text-sm font-black text-[#101614]">
                  {generator.name}
                </th>
                <td className="px-4 py-4">
                  <span
                    className={`inline-flex border border-[#101614] px-2 py-1 font-mono text-[11px] font-bold ${STATE_STYLES[generator.state]}`}
                  >
                    {generator.state}
                  </span>
                </td>
                <td className="max-w-[240px] px-4 py-4 text-sm font-semibold text-[#101614]">
                  {generator.output}
                </td>
                <td className="max-w-[340px] px-4 py-4 text-sm font-medium leading-5 text-[#5B665F]">
                  {generator.boundary}
                </td>
                <td className="px-4 py-4 text-right">
                  <Link
                    href={generator.href}
                    className="inline-flex min-h-11 items-center gap-2 border-2 border-[#101614] bg-[#FBF8F1] px-3 py-2 text-xs font-black uppercase text-[#101614] shadow-[3px_3px_0_#101614] transition-transform duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#118A72] focus-visible:ring-offset-2"
                  >
                    {generator.action}
                    <IconArrowUpRight aria-hidden="true" className="h-4 w-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

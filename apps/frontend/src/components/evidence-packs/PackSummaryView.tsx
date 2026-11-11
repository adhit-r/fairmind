import type { PackManifest, PackSystemEntry } from '@/lib/api/hooks/useEvidencePacks'
import { Card } from '@/components/ui/card'

const VERDICT_LABEL: Record<string, string> = { go: 'Go', conditional_go: 'Conditional go', no_go: 'No go' }
const VERDICT_TONE: Record<string, string> = { go: 'text-[#1f7a4d]', conditional_go: 'text-[#a14d00]', no_go: 'text-[#b4232c]' }

export function formatDate(iso?: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function sealStatus(system: PackSystemEntry): { text: string; tone: string } {
  if (system.seals.length === 0) return { text: 'No decision sealed yet', tone: 'text-[var(--fm-ink2)]' }
  const broken = system.seals.filter((s) => s.verification.status === 'broken').length
  if (broken > 0) return { text: `${broken} of ${system.seals.length} seals broken`, tone: 'text-[#b4232c]' }
  return { text: `${system.seals.length} ${system.seals.length === 1 ? 'seal' : 'seals'} intact`, tone: 'text-[#1f7a4d]' }
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">{label}</div>
      <div className="mt-1 text-sm text-[var(--fm-ink)]">{children}</div>
    </div>
  )
}

function SystemCard({ entry }: { entry: PackSystemEntry }) {
  const seal = sealStatus(entry)
  const verdict = entry.gate.verdict
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-base font-semibold tracking-tight text-[var(--fm-ink)]">{entry.system.name}</h2>
        <span className="text-xs text-[var(--fm-ink3)]">{entry.system.riskTier} risk</span>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        <Stat label="Release gate">
          <span className={`font-semibold ${verdict ? VERDICT_TONE[verdict] : ''}`}>{verdict ? VERDICT_LABEL[verdict] : 'No verdict'}</span>
          {entry.gate.confidence != null && <span className="ml-2 text-[var(--fm-ink2)]">{entry.gate.confidence.toFixed(2)}</span>}
        </Stat>
        <Stat label="Evidence records">{entry.evidence.length}</Stat>
        <Stat label="Decision seals"><span className={seal.tone}>{seal.text}</span></Stat>
        <Stat label="Chain head"><span className="break-all font-mono text-xs">{entry.chainHead.slice(0, 16)}</span></Stat>
      </div>
      {entry.clauseMap.frameworks.length > 0 && (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">
                <th scope="col" className="pb-2 pr-4 font-semibold">Framework</th>
                <th scope="col" className="pb-2 pr-4 text-right font-semibold">Proven</th>
                <th scope="col" className="pb-2 pr-4 text-right font-semibold">Attested</th>
                <th scope="col" className="pb-2 pr-4 text-right font-semibold">Open</th>
                <th scope="col" className="pb-2 text-right font-semibold">Clauses</th>
              </tr>
            </thead>
            <tbody>
              {entry.clauseMap.frameworks.map((fw) => (
                <tr key={fw.key} className="border-t border-[var(--fm-line)]">
                  <td className="py-2 pr-4 text-[var(--fm-ink)]">{fw.name}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#1f7a4d]">{fw.counts.proven}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#a14d00]">{fw.counts.attested}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#b4232c]">{fw.counts.open}</td>
                  <td className="py-2 text-right tabular-nums text-[var(--fm-ink2)]">{fw.counts.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

/** The read-only summary shared by the signed-in pack page and the auditor page. */
export function PackSummaryView({ manifest, manifestHash }: { manifest: PackManifest; manifestHash: string }) {
  return (
    <div className="flex flex-col gap-4">
      <Card className="p-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat label="Built">{formatDate(manifest.createdAt)}</Stat>
          <Stat label="Frameworks">{manifest.frameworks.join(', ')}</Stat>
          <Stat label="Systems">{manifest.systems.length}</Stat>
        </div>
        <div className="mt-4 border-t border-[var(--fm-line)] pt-4">
          <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Manifest hash (SHA-256)</div>
          <div className="mt-1 break-all font-mono text-xs text-[var(--fm-ink)]">{manifestHash}</div>
        </div>
      </Card>
      {manifest.systems.map((entry) => (
        <SystemCard key={entry.system.id} entry={entry} />
      ))}
    </div>
  )
}

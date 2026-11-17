import type { PackEvidence, PackManifest, PackSystemEntry } from '@/lib/api/hooks/useEvidencePacks'
import { Card } from '@/components/ui/card'

const VERDICT_LABEL: Record<string, string> = { go: 'Go', conditional_go: 'Conditional go', no_go: 'No go' }
const VERDICT_TONE: Record<string, string> = { go: 'text-[#1f7a4d]', conditional_go: 'text-[#a14d00]', no_go: 'text-[#b4232c]' }
const STATE_TONE: Record<string, string> = { proven: 'text-[#1f7a4d]', attested: 'text-[#a14d00]', open: 'text-[#b4232c]' }
const LABEL = 'text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]'
const TH = 'pb-2 pr-4 font-semibold'
const TD = 'py-2 pr-4 align-top'

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

/** An evaluation run keeps its outcome (passed, failed, insufficient) in its content; other records only have a status. */
function resultOf(e: PackEvidence): string {
  try {
    const status = e.content ? JSON.parse(e.content).status : undefined
    if (typeof status === 'string') return status
  } catch {
    // content is free text for some record types
  }
  return e.status || ''
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="mt-4 border-t border-[var(--fm-line)] pt-3">
      <summary className={`cursor-pointer ${LABEL}`}>{title}</summary>
      <div className="mt-2 overflow-x-auto">{children}</div>
    </details>
  )
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
          {entry.gate.reasons?.length > 0 && (
            <ul className="mt-1 list-disc pl-4 text-xs text-[var(--fm-ink2)]">
              {entry.gate.reasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          )}
        </Stat>
        <Stat label="Evidence records">{entry.evidence.length}</Stat>
        <Stat label="Decision seals"><span className={seal.tone}>{seal.text}</span></Stat>
        <Stat label="Chain head"><span className="break-all font-mono text-xs">{entry.chainHead.slice(0, 16)}</span></Stat>
      </div>
      {entry.clauseMap.frameworks.length > 0 && (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className={LABEL}>
                <th scope="col" className={TH}>Framework</th>
                <th scope="col" className={`${TH} text-right`}>Proven</th>
                <th scope="col" className={`${TH} text-right`} title="Proven only through a weaker link than satisfies">Partial</th>
                <th scope="col" className={`${TH} text-right`}>Attested</th>
                <th scope="col" className={`${TH} text-right`}>Open</th>
                <th scope="col" className="pb-2 text-right font-semibold">Clauses</th>
              </tr>
            </thead>
            <tbody>
              {entry.clauseMap.frameworks.map((fw) => (
                <tr key={fw.key} className="border-t border-[var(--fm-line)]">
                  <td className="py-2 pr-4 text-[var(--fm-ink)]">{fw.name}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#1f7a4d]">{fw.counts.proven}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[var(--fm-ink2)]">{fw.counts.partial ?? 0}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#a14d00]">{fw.counts.attested}</td>
                  <td className="py-2 pr-4 text-right tabular-nums text-[#b4232c]">{fw.counts.open}</td>
                  <td className="py-2 text-right tabular-nums text-[var(--fm-ink2)]">{fw.counts.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {entry.clauseMap.frameworks.map((fw) => (
        <Section key={fw.key} title={`${fw.name}: ${fw.clauses.length} clauses`}>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className={LABEL}>
                <th scope="col" className={TH}>Clause</th>
                <th scope="col" className={TH}>Title</th>
                <th scope="col" className={TH}>State</th>
                <th scope="col" className="pb-2 font-semibold">Backed by</th>
              </tr>
            </thead>
            <tbody>
              {fw.clauses.map((c) => (
                <tr key={c.key} className="border-t border-[var(--fm-line)]">
                  <td className={`${TD} whitespace-nowrap font-mono text-xs text-[var(--fm-ink)]`}>{c.control}</td>
                  <td className={`${TD} text-[var(--fm-ink)]`}>{c.title}</td>
                  <td className={`${TD} ${STATE_TONE[c.state] || ''}`}>{c.state}</td>
                  <td className="py-2 align-top text-[var(--fm-ink2)]">
                    {c.checks.map((k) => (
                      <div key={k.check}>{k.label}: <span className={STATE_TONE[k.state] || ''}>{k.state}</span></div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      ))}
      {entry.evidence.length > 0 && (
        <Section title={`Evidence records: ${entry.evidence.length}`}>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className={LABEL}>
                <th scope="col" className={TH}>Type</th>
                <th scope="col" className={TH}>Title</th>
                <th scope="col" className={TH}>Result</th>
                <th scope="col" className="pb-2 font-semibold">Captured</th>
              </tr>
            </thead>
            <tbody>
              {entry.evidence.map((e) => (
                <tr key={e.id} className="border-t border-[var(--fm-line)]">
                  <td className={`${TD} whitespace-nowrap text-[var(--fm-ink2)]`}>{e.type.replace(/_/g, ' ')}</td>
                  <td className={`${TD} text-[var(--fm-ink)]`}>{e.title || <span className="font-mono text-xs text-[var(--fm-ink3)]">{e.hash.slice(0, 16)}</span>}</td>
                  <td className={`${TD} text-[var(--fm-ink2)]`}>{resultOf(e)}</td>
                  <td className="whitespace-nowrap py-2 align-top text-[var(--fm-ink2)]">{formatDate(e.createdAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}
      {entry.seals.length > 0 && (
        <Section title={`Release decisions: ${entry.seals.length}`}>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className={LABEL}>
                <th scope="col" className={TH}>Decision</th>
                <th scope="col" className={TH}>By</th>
                <th scope="col" className={TH}>Date</th>
                <th scope="col" className={TH}>Gate it saw</th>
                <th scope="col" className={TH}>Notes</th>
                <th scope="col" className="pb-2 font-semibold">Seal</th>
              </tr>
            </thead>
            <tbody>
              {entry.seals.map((s) => (
                <tr key={s.id} className="border-t border-[var(--fm-line)]">
                  <td className={`${TD} text-[var(--fm-ink)]`}>{s.decision}</td>
                  <td className={`${TD} text-[var(--fm-ink2)]`}>{s.sealedBy || ''}</td>
                  <td className={`${TD} whitespace-nowrap text-[var(--fm-ink2)]`}>{formatDate(s.createdAt)}</td>
                  <td className={`${TD} text-[var(--fm-ink2)]`}>
                    {s.gate?.verdict ? VERDICT_LABEL[s.gate.verdict] || s.gate.verdict : ''}
                    {s.gate?.effectiveTier && <div className="text-xs">{s.gate.effectiveTier} risk</div>}
                    {s.gate?.reasons?.map((r) => <div key={r} className="text-xs">{r}</div>)}
                  </td>
                  <td className={`${TD} whitespace-pre-line text-[var(--fm-ink2)]`}>{s.notes || ''}</td>
                  <td className={`py-2 align-top ${s.verification.status === 'broken' ? 'text-[#b4232c]' : 'text-[#1f7a4d]'}`}>{s.verification.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
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

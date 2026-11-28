'use client'

import './auditor-report.css'
import { useEffect, useMemo, useState } from 'react'
import type { PackManifest } from '@/lib/api/hooks/useEvidencePacks'
import { READINESS_LABEL, READINESS_OF, READINESS_ORDER, ReadinessBar, readinessCounts, type ReqState } from '@/app/(dashboard)/frameworks/parts'
import { PackSummaryView } from './PackSummaryView'
import { LedgerCard, LedgerCheckCard, useLedgerCheck } from './LedgerSection'

const WEAKEST: ReqState[] = ['fails', 'stale', 'open', 'none', 'planned', 'estimated', 'partial', 'attested', 'excluded', 'proven']
const weaker = (a: ReqState, b: ReqState) => (WEAKEST.indexOf(a) <= WEAKEST.indexOf(b) ? a : b)
const date = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

type Row = {
  key: string
  control: string
  title: string
  state: ReqState
  evidence: number
  checks: Array<{ system: string; label: string; state: string; relation: string }>
}

/** Each framework's requirements across every system in the pack: the weakest state wins, evidence is counted once. */
function statementOf(manifest: PackManifest) {
  const byFw = new Map<string, { name: string; rows: Map<string, Row> }>()
  for (const entry of manifest.systems) {
    for (const fw of entry.clauseMap?.frameworks ?? []) {
      const slot = byFw.get(fw.key) ?? { name: fw.name, rows: new Map<string, Row>() }
      byFw.set(fw.key, slot)
      for (const c of fw.clauses) {
        const row = slot.rows.get(c.key) ?? { key: c.key, control: c.control, title: c.title, state: 'proven' as ReqState, evidence: 0, checks: [] }
        row.state = weaker(row.state, (c.cell ?? 'none') as ReqState)
        row.checks.push(...c.checks.map((k) => ({ system: entry.system.name, label: k.label, state: k.fails ? 'failing' : k.stale ? 'out of date' : k.state, relation: k.relation })))
        slot.rows.set(c.key, row)
      }
    }
  }
  return [...byFw.entries()].map(([key, v]) => {
    const rows = [...v.rows.values()].map((r) => ({ ...r, evidence: new Set(r.checks.map((c) => `${c.system}|${c.label}`)).size }))
    const states: Partial<Record<ReqState, number>> = {}
    for (const r of rows) states[r.state] = (states[r.state] ?? 0) + 1
    return { key, name: v.name, rows, counts: readinessCounts(states) }
  })
}

/** The browser's own check of the manifest hash, the same canonical form the CLI uses. Packs before version 2 are left to the CLI. */
function useIntegrity(manifest: PackManifest, expected: string): 'checking' | 'match' | 'unconfirmed' {
  // a pack before version 2, or a browser without SubtleCrypto, is left to the CLI from the start
  const browserCanCheck = (manifest.version ?? 1) >= 2 && !!globalThis.crypto?.subtle
  const [state, setState] = useState<'checking' | 'match' | 'unconfirmed'>(browserCanCheck ? 'checking' : 'unconfirmed')
  useEffect(() => {
    if (!browserCanCheck) return
    let live = true
    const canonical = (v: unknown): string =>
      Array.isArray(v) ? `[${v.map(canonical).join(',')}]`
        : v && typeof v === 'object' ? `{${Object.keys(v as object).sort().map((k) => `${JSON.stringify(k)}:${canonical((v as Record<string, unknown>)[k])}`).join(',')}}`
          : JSON.stringify(v)
    void crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(manifest))).then((buf) => {
      const hex = [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
      if (live) setState(hex === expected ? 'match' : 'unconfirmed')
    })
    return () => {
      live = false
    }
  }, [manifest, expected, browserCanCheck])
  return state
}

const PILL: Record<string, string> = { met: 'ar-pill met', progress: 'ar-pill progress', attention: 'ar-pill attention', notstarted: 'ar-pill notstarted' }

export function AuditorReport({ manifest, manifestHash, expiresAt, verifyHint }: { manifest: PackManifest; manifestHash: string; expiresAt?: string | null; verifyHint?: React.ReactNode }) {
  const statement = useMemo(() => statementOf(manifest), [manifest])
  const integrity = useIntegrity(manifest, manifestHash)
  const ledger = useLedgerCheck(manifest)
  const [filter, setFilter] = useState<'all' | 'notmet'>('all')
  const org = manifest.organisation
  const excluded = manifest.systems.flatMap((s) => (s.controlApplicability ?? []).filter((c) => c.applicability === 'not_applicable').map((c) => ({ ...c, system: s.system.name })))
  const approvedPolicies = (org?.policies ?? []).filter((p) => p.approved_at)

  return (
    <div className="ar">
      <section className="ar-top">
        <div className="ar-card ar-cover" style={{ gridColumn: '1 / -1' }}>
          <span className="ar-eyebrow">{statement.map((f) => f.name).join(' · ') || manifest.frameworks.join(' · ')}</span>
          <h1>{manifest.title}</h1>
          <dl className="ar-facts">
            <div><dt>As of</dt><dd>{date(manifest.createdAt)}</dd></div>
            <div><dt>Scope</dt><dd>{manifest.systems.length} AI system{manifest.systems.length === 1 ? '' : 's'}</dd></div>
            <div><dt>Organisation records</dt><dd>{approvedPolicies.length} approved polic{approvedPolicies.length === 1 ? 'y' : 'ies'} · {org?.attestations.length ?? 0} attestations</dd></div>
          </dl>
          {expiresAt && <p className="ar-muted">This link works until {date(expiresAt)}.</p>}
        </div>
        <div className="ar-card ar-integrity">
          <div className="ar-integrity-head">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={integrity === 'match' ? '#1d6b57' : '#5a5f68'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />{integrity === 'match' && <path d="M9 12l2 2 4-4" />}</svg>
            <b>{integrity === 'match' ? 'Unchanged since it was built' : integrity === 'checking' ? 'Checking the pack' : 'Check it offline'}</b>
          </div>
          <p className="ar-muted">
            {integrity === 'match'
              ? 'Your browser recomputed the pack’s SHA-256 and it matches the hash recorded when it was built.'
              : integrity === 'checking'
                ? 'Recomputing the pack’s SHA-256 in your browser.'
                : 'Your browser could not confirm the hash. Run the offline check below before relying on this pack.'}
          </p>
          <code className="ar-hash">sha256 {manifestHash.slice(0, 12)}…{manifestHash.slice(-6)}</code>
        </div>
        <LedgerCheckCard state={ledger} />
      </section>

      {statement.map((fw) => {
        const rows = filter === 'notmet' ? fw.rows.filter((r) => READINESS_OF[r.state] !== 'met') : fw.rows
        return (
          <section key={fw.key} className="ar-card" aria-labelledby={`ar-soa-${fw.key}`}>
            <div className="ar-head">
              <h2 id={`ar-soa-${fw.key}`}>{fw.name}: where each requirement stands</h2>
              <div className="ar-filters" role="group" aria-label="Show">
                <button type="button" aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>All {fw.rows.length}</button>
                <button type="button" aria-pressed={filter === 'notmet'} onClick={() => setFilter('notmet')}>Not met {fw.rows.length - fw.counts.met}</button>
              </div>
            </div>
            <ReadinessBar counts={fw.counts} />
            <div className="ar-scroll">
              <table className="ar-table">
                <thead>
                  <tr><th scope="col">Requirement</th><th scope="col">Status</th><th scope="col">Evidence</th></tr>
                </thead>
                <tbody>
                  {rows.map((r) => {
                    const ready = READINESS_OF[r.state]
                    return (
                      <tr key={r.key}>
                        <td>
                          <details>
                            <summary><b>{r.control}</b> {r.title}</summary>
                            {r.checks.length ? (
                              <ul className="ar-checks">
                                {r.checks.map((c, i) => (
                                  <li key={i}><span>{c.label} · {c.system}</span><span className="ar-muted">{c.state} · {c.relation}</span></li>
                                ))}
                              </ul>
                            ) : (
                              <p className="ar-muted">No record reaches this requirement.</p>
                            )}
                          </details>
                        </td>
                        <td><span className={PILL[ready]}>{READINESS_LABEL[ready]}</span></td>
                        <td>{r.evidence ? `${r.evidence} record${r.evidence === 1 ? '' : 's'}` : 'None'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <p className="ar-muted">{READINESS_ORDER.map((k) => `${fw.counts[k]} ${READINESS_LABEL[k].toLowerCase()}`).join(' · ')}. Met means proven by evidence or attested by a named person.</p>
          </section>
        )
      })}

      {excluded.length > 0 && (
        <section className="ar-card" aria-labelledby="ar-excl">
          <h2 id="ar-excl">Excluded controls</h2>
          <ul className="ar-checks">
            {excluded.map((c, i) => (
              <li key={i}><span><b>{c.control}</b> {c.title} · {c.system}</span><span className="ar-muted">{c.justification || 'No reason recorded'}</span></li>
            ))}
          </ul>
        </section>
      )}

      {manifest.ledger && ledger.status !== 'none' && ledger.status !== 'empty' && <LedgerCard chain={manifest.ledger} state={ledger} />}

      <section className="ar-two">
        <div className="ar-card">
          <h2>Systems in scope {manifest.systems.length}</h2>
          <ul className="ar-checks">
            {manifest.systems.map((s) => (
              <li key={s.system.id}><span>{s.system.name}</span><span className="ar-muted">{s.system.riskTier} risk · {s.evidence.length} records{s.seals.length ? ` · ${s.seals.length} release decision${s.seals.length === 1 ? '' : 's'}` : ''}</span></li>
            ))}
          </ul>
        </div>
        <div className="ar-card">
          <h2>Check it yourself, offline</h2>
          <p className="ar-muted">You do not have to trust this page. Save the pack as pack.json, then on any machine:</p>
          <pre className="ar-pre">{`pipx install fairmind-cli\nfairmind verify pack.json`}</pre>
          <p className="ar-muted">It recomputes the manifest hash, each system’s evidence chain and, for packs that carry one, the organisation ledger, with no network, and exits 0 only when all of them match.</p>
          {verifyHint}
        </div>
      </section>

      <details className="ar-card">
        <summary><b>Full record</b> <span className="ar-muted">every evidence record, release decision, policy and attestation in the pack</span></summary>
        <div style={{ marginTop: 16 }}>
          <PackSummaryView manifest={manifest} manifestHash={manifestHash} />
        </div>
      </details>
    </div>
  )
}

import Link from 'next/link'
import { checkEvidenceIds } from '@/components/workflow/CheckEvidenceLinks'
import type { Risk } from '@/lib/api/hooks/useRisks'
import type { GateCheck, RiskStatus } from '@/lib/api/hooks/useSystemFile'
import { evaluationHref, findingHref } from '@/lib/assurance/evaluationLinks'
import { evidenceRecordHref } from '@/lib/assurance/evidenceLinks'
import './system-review-trail.css'

type TrailRisk = RiskStatus['risks'][number] & Pick<Risk, 'systemId' | 'metadata'>

function hasId(value: unknown): value is string {
  return typeof value === 'string' && value !== '' && value === value.trim()
}

function matchesFailure(risk: TrailRisk, check: GateCheck, evidenceIds: string[]) {
  const { source, metadata } = risk
  if (source === 'fairmind.watch' && check.key === 'monitoring') {
    return hasId(metadata?.latest_snapshot_id) && evidenceIds.includes(metadata.latest_snapshot_id)
  }
  if (source !== 'fairmind.eval_engines' || !metadata) return false

  // The current blocker can be a failed retest. The finding still keeps its original evidence ID.
  const earlier = Array.isArray(metadata.retestEvidenceIds) ? metadata.retestEvidenceIds : []
  return [metadata.evidenceId, metadata.retestEvidenceId, ...earlier]
    .some((id) => hasId(id) && evidenceIds.includes(id))
}

function catalogueOrigin(finding: TrailRisk) {
  const { source, metadata } = finding
  if (source !== 'fairmind.eval_engines' || !hasId(metadata?.evaluationId) || !hasId(metadata.evidenceId)) return null
  return { evaluationId: metadata.evaluationId, evidenceId: metadata.evidenceId }
}

function retestHref(systemId: string, finding: TrailRisk) {
  const origin = catalogueOrigin(finding)
  const latest = finding.metadata?.retestEvidenceId
  return origin && hasId(latest) && latest !== origin.evidenceId
    ? evaluationHref(origin.evaluationId, systemId, latest, finding.id)
    : null
}

export function SystemReviewTrail({ systemId, check, risks }: {
  systemId: string
  check?: GateCheck | null
  risks: RiskStatus | null
}) {
  if (!check) return null

  const proof = checkEvidenceIds(check, true)
  const records: TrailRisk[] | null = Array.isArray(risks?.risks) ? risks.risks : null
  const findings = records?.filter((risk) => risk?.systemId === systemId && hasId(risk.id) && matchesFailure(risk, check, proof)) ?? []
  const retests = findings.flatMap((finding) => {
    const href = retestHref(systemId, finding)
    return href ? [{ finding, href }] : []
  })

  return (
    <section className="fm-sf-review-trail" aria-labelledby="sf-review-trail">
      <h2 id="sf-review-trail">Review trail</h2>
      <ol role="list">
        <li data-state="failed">
          <h3>Failed check</h3>
          <p>{check.label}</p>
        </li>
        <li data-state={proof.length ? 'recorded' : undefined}>
          <h3>Source evidence</h3>
          <p>{proof.length ? `${proof.length} linked record${proof.length === 1 ? '' : 's'}` : 'Source record unavailable'}</p>
        </li>
        <li data-state={findings.length ? 'recorded' : undefined}>
          <h3>Finding</h3>
          {findings.length ? findings.map((finding) => (
            <Link key={finding.id} href={findingHref(systemId, finding.id)}>{finding.title || 'View linked finding'}</Link>
          )) : <p>{records ? 'No linked finding' : 'Findings unavailable'}</p>}
        </li>
        <li data-state={retests.length ? 'recorded' : undefined}>
          <h3>Retest</h3>
          {retests.length ? retests.map(({ finding, href }) => (
            <Link key={finding.id} href={href} aria-label={findings.length > 1 && finding.title ? `View recorded retest for ${finding.title}` : undefined}>
              {findings.length > 1 && finding.title ? `Retest for ${finding.title}` : 'View recorded retest'}
            </Link>
          )) : <p>{records ? 'No linked retest' : 'Retest history unavailable'}</p>}
        </li>
      </ol>
    </section>
  )
}

export function SystemReviewHistory({ systemId, risks }: { systemId: string; risks: RiskStatus | null }) {
  const records: TrailRisk[] = Array.isArray(risks?.risks) ? risks.risks : []
  const history = records.flatMap((finding) => {
    if (finding?.systemId !== systemId || !hasId(finding.id)) return []
    const origin = catalogueOrigin(finding)
    return origin ? [{ finding, origin }] : []
  })
  if (!history.length) return null

  return (
    <section className="fm-card fm-sf-review-history" aria-labelledby="sf-review-history">
      <h2 id="sf-review-history">Review history</h2>
      <ul role="list">
        {history.map(({ finding, origin }) => {
          const latest = retestHref(systemId, finding)
          return (
            <li key={finding.id}>
              <h3>{finding.title || origin.evaluationId}</h3>
              <div className="fm-sf-review-history-links">
                <Link href={evidenceRecordHref(systemId, origin.evidenceId)}>Original evidence</Link>
                <Link href={findingHref(systemId, finding.id)}>View finding</Link>
                {latest && <Link href={latest}>Latest recorded retest</Link>}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

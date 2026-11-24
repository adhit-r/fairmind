import Link from 'next/link'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { evidenceRecordHref } from '@/lib/assurance/evidenceLinks'

type Proof = Pick<GateCheck, 'evidenceId' | 'failureEvidenceIds'> & { state?: string }

/** A failing check may be held open by several records, even after a passing run. */
export function checkEvidenceIds(check: Proof, failed: boolean): string[] {
  const sources = failed ? check.failureEvidenceIds : [check.evidenceId]
  return Array.isArray(sources)
    ? [...new Set(sources.filter((id): id is string => typeof id === 'string' && Boolean(id.trim())))]
    : []
}

export function CheckEvidenceLinks({ systemId, check, failed, showRecordId = true }: {
  systemId?: string
  check: Proof
  failed: boolean
  showRecordId?: boolean
}) {
  const ids = checkEvidenceIds(check, failed)
  if (!systemId || !ids.length) {
    return <span>{!failed && check.state === 'open' ? 'None on file' : 'Source record unavailable'}</span>
  }

  return (
    <ul className="grid gap-1">
      {ids.map((id, index) => (
        <li key={id}>
          <Link className="block min-h-8 max-w-full py-1 underline" href={evidenceRecordHref(systemId, id)}>
            {ids.length === 1 ? 'Open the evidence' : `Open evidence record${showRecordId ? '' : ` ${index + 1}`}`}
            {' '}<code className={showRecordId ? 'break-all' : 'sr-only'}>{id}</code>
          </Link>
        </li>
      ))}
    </ul>
  )
}

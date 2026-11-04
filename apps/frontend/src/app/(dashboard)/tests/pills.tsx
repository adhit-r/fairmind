import { Pill } from '@/components/packs/parts'
import type { GovernanceVerdict, TechnicalStatus } from '@/lib/api/hooks/useEvaluationRuns'

type Tone = Parameters<typeof Pill>[0]['tone']

// Orange ("you") marks what waits on a person: evidence to link, a verdict to review.
const STATUS: Record<TechnicalStatus, { label: string; tone: Tone }> = {
  awaiting_evidence: { label: 'Awaiting evidence', tone: 'you' },
  running: { label: 'Running', tone: 'run' },
  succeeded: { label: 'Succeeded', tone: 'done' },
  failed: { label: 'Failed', tone: 'block' },
  cancelled: { label: 'Cancelled', tone: 'block' },
}

const VERDICT: Record<GovernanceVerdict, { label: string; tone: Tone }> = {
  approved: { label: 'Approved', tone: 'done' },
  conditional: { label: 'Conditional', tone: 'warn' },
  review: { label: 'Review', tone: 'you' },
  blocked: { label: 'Blocked', tone: 'block' },
  insufficient: { label: 'Insufficient', tone: 'plain' },
}

export function TechnicalStatusPill({ status }: { status: TechnicalStatus }) {
  const s = STATUS[status] ?? { label: status, tone: 'plain' }
  return <Pill tone={s.tone} dot={s.tone === 'you'}>{s.label}</Pill>
}

export function VerdictPill({ verdict }: { verdict: GovernanceVerdict }) {
  const v = VERDICT[verdict] ?? { label: verdict, tone: 'plain' }
  return <Pill tone={v.tone} dot={v.tone === 'you'}>{v.label}</Pill>
}

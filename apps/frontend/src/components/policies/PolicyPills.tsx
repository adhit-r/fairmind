import { Pill } from '@/components/packs/parts'
import type { PolicyStatus, RuleOutcome } from '@/lib/api/hooks/usePolicies'

const STATUS: Record<PolicyStatus, { label: string; tone: 'plain' | 'you' | 'done' | 'run' | 'block' }> = {
  draft: { label: 'Draft', tone: 'plain' },
  in_review: { label: 'In review', tone: 'you' },
  approved: { label: 'Approved', tone: 'run' },
  published: { label: 'Published', tone: 'done' },
  retired: { label: 'Retired', tone: 'plain' },
}

export function PolicyStatusPill({ status }: { status: PolicyStatus }) {
  const s = STATUS[status]
  return <Pill tone={s.tone} dot={status === 'in_review'}>{s.label}</Pill>
}

export function OutcomePill({ outcome, enforcement }: { outcome: RuleOutcome; enforcement?: 'block' | 'warn' }) {
  if (outcome === 'pass') return <Pill tone="done">Pass</Pill>
  if (outcome === 'not_applicable') return <Pill>Not applicable</Pill>
  return <Pill tone={enforcement === 'warn' ? 'you' : 'block'} dot>{enforcement === 'warn' ? 'Warning' : 'Blocking'}</Pill>
}

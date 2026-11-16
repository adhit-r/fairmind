/**
 * Status tone vocabulary shared by StatusBadge and every domain mapping.
 * Tone maps to colour AND an icon AND a text label; colour never carries meaning alone.
 * Semantics follow DESIGN.md "Evaluation State Semantics" / "Evidence Admission".
 */
export type StatusTone = 'neutral' | 'info' | 'success' | 'warning' | 'critical' | 'attention'

export interface StatusResult {
  tone: StatusTone
  label: string
}

export const NOT_ASSESSED: StatusResult = { tone: 'neutral', label: 'Not assessed' }

function normalize(value: unknown): string {
  return typeof value === 'string' ? value.trim().toLowerCase().replace(/[\s-]+/g, '_') : ''
}

function build(map: Record<string, StatusResult>) {
  return (value: unknown): StatusResult => map[normalize(value)] ?? NOT_ASSESSED
}

/** Title-case a snake_case enum for display, e.g. "passed_with_limitations" -> "Passed with limitations". */
export function humanizeEnum(value: string): string {
  const text = value.replace(/[_-]+/g, ' ').trim().toLowerCase()
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : ''
}

/** AI system risk tier (low / medium / high / critical; minimal/limited/unacceptable accepted). */
export const riskTierTone = build({
  minimal: { tone: 'success', label: 'Minimal risk' },
  low: { tone: 'success', label: 'Low risk' },
  limited: { tone: 'warning', label: 'Limited risk' },
  medium: { tone: 'warning', label: 'Medium risk' },
  high: { tone: 'critical', label: 'High risk' },
  critical: { tone: 'critical', label: 'Critical risk' },
  unacceptable: { tone: 'critical', label: 'Unacceptable risk' },
})

/** Finding / alert severity. */
export const severityTone = build({
  info: { tone: 'neutral', label: 'Info' },
  informational: { tone: 'neutral', label: 'Info' },
  low: { tone: 'info', label: 'Low' },
  medium: { tone: 'warning', label: 'Medium' },
  moderate: { tone: 'warning', label: 'Medium' },
  high: { tone: 'critical', label: 'High' },
  critical: { tone: 'critical', label: 'Critical' },
})

/** Evaluation run execution status: did the evaluator finish its work? Never implies a pass. */
export const executionStatusTone = build({
  queued: { tone: 'neutral', label: 'Queued' },
  leased: { tone: 'info', label: 'Leased' },
  running: { tone: 'info', label: 'Running' },
  awaiting_evidence: { tone: 'neutral', label: 'Awaiting evidence' },
  succeeded: { tone: 'success', label: 'Succeeded' },
  failed: { tone: 'critical', label: 'Failed' },
  timed_out: { tone: 'critical', label: 'Timed out' },
  cancelled: { tone: 'neutral', label: 'Cancelled' },
})

/** Evaluator evidence result: what the evaluator found. A failed result can come from a succeeded run. */
export const evidenceResultTone = build({
  pending: { tone: 'neutral', label: 'Pending' },
  passed: { tone: 'success', label: 'Passed' },
  passed_with_limitations: { tone: 'warning', label: 'Passed with limitations' },
  failed: { tone: 'critical', label: 'Failed' },
  informational: { tone: 'info', label: 'Informational' },
  error: { tone: 'critical', label: 'Error' },
  unavailable: { tone: 'neutral', label: 'Unavailable' },
  insufficient_data: { tone: 'neutral', label: 'Insufficient data' },
  unknown: { tone: 'neutral', label: 'Unknown' },
})

/** Governance verdict: the human-governed decision supported by admitted evidence. "review" needs attention, not a pass. */
export const verdictTone = build({
  approved: { tone: 'success', label: 'Approved' },
  conditional: { tone: 'warning', label: 'Conditional' },
  review: { tone: 'attention', label: 'Review required' },
  blocked: { tone: 'critical', label: 'Blocked' },
  insufficient: { tone: 'neutral', label: 'Insufficient evidence' },
})

/** Evidence admission state. Imported/unsigned reports stay visibly "unverified". */
export const admissionTone = build({
  pending: { tone: 'neutral', label: 'Admission pending' },
  verified: { tone: 'success', label: 'Verified' },
  unverified: { tone: 'warning', label: 'Unverified' },
  expired: { tone: 'critical', label: 'Expired' },
  superseded: { tone: 'neutral', label: 'Superseded' },
  rejected: { tone: 'critical', label: 'Rejected' },
  trust_error: { tone: 'critical', label: 'Trust error' },
})

/** Reviewer outcome on an evidence artifact (review axis only; never rewrites verdicts). */
export const reviewTone = build({
  pending: { tone: 'neutral', label: 'Review pending' },
  accepted: { tone: 'success', label: 'Accepted' },
  rejected: { tone: 'critical', label: 'Rejected' },
})

/** Evidence freshness. */
export const freshnessTone = build({
  current: { tone: 'success', label: 'Current' },
  expiring: { tone: 'warning', label: 'Expiring' },
  stale: { tone: 'critical', label: 'Stale' },
  superseded: { tone: 'neutral', label: 'Superseded' },
})

/** Capability registry state (Capability Truth Table). */
export const capabilityStateTone = build({
  planned: { tone: 'neutral', label: 'Planned' },
  experimental: { tone: 'warning', label: 'Experimental' },
  advisory: { tone: 'info', label: 'Advisory' },
  verified: { tone: 'success', label: 'Verified capability' },
  retired: { tone: 'neutral', label: 'Retired' },
})

/** Generic work status (findings, remediation tasks). */
export const workStatusTone = build({
  open: { tone: 'attention', label: 'Open' },
  new: { tone: 'attention', label: 'New' },
  todo: { tone: 'neutral', label: 'To do' },
  in_progress: { tone: 'info', label: 'In progress' },
  active: { tone: 'info', label: 'Active' },
  blocked: { tone: 'critical', label: 'Blocked' },
  retest_required: { tone: 'warning', label: 'Retest required' },
  resolved: { tone: 'success', label: 'Resolved' },
  completed: { tone: 'success', label: 'Completed' },
  closed: { tone: 'neutral', label: 'Closed' },
  accepted: { tone: 'neutral', label: 'Risk accepted' },
})

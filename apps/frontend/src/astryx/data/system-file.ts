import type { ApprovalStatus, GatePathStep, ReleaseGate, SystemRecord, Verdict } from '@/lib/api/hooks/useSystemFile'
import type { AutopilotEvent, AutopilotStep } from '@/lib/api/hooks/useAutopilot'

export type Tone = 'green' | 'red' | 'orange' | 'blue' | 'neutral'

export const VERDICT_META: Record<Verdict, { label: string; tone: Tone }> = {
  go: { label: 'Go', tone: 'green' },
  conditional_go: { label: 'Conditional go', tone: 'orange' },
  no_go: { label: 'No go', tone: 'red' },
}

export const RISK_TONE: Record<SystemRecord['riskTier'], Tone> = { low: 'neutral', medium: 'orange', high: 'red', critical: 'red' }

export const KIND_LABEL: Record<string, string> = { ml_model: 'ML model', llm_app: 'LLM app', ai_assisted_dev: 'AI-assisted development' }
export const SOURCE_LABEL: Record<string, string> = { mlflow: 'MLflow registry', github: 'GitHub', huggingface: 'Hugging Face', manual: 'Registered manually' }
export const STAGE_LABEL: Record<string, string> = { onboard: 'Onboard', assess: 'Assess', govern: 'Govern', remediate: 'Remediate', operate: 'Operate', decision: 'Decision' }

export const cap = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ') : s)

export const when = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''

/** The request status, with "not requested" when there is no request. */
export const approvalStatusOf = (gate: ReleaseGate | null, approval: ApprovalStatus | null) =>
  approval?.request?.status ?? gate?.approvalStatus ?? 'not_requested'

/** Who does a path step. The autopilot's own plan wins; otherwise measured runs can be done by the agent, statements and uploads need a person. */
export function stepWho(step: Pick<GatePathStep, 'check' | 'action' | 'evidenceClass'>, plan: AutopilotStep[] | undefined): 'agent' | 'person' {
  const planned = plan?.find((p) => p.check === step.check && p.action === step.action)
  if (planned) return planned.by
  if (step.action === 'attest' || step.action === 'evidence_upload' || step.evidenceClass === 'manual') return 'person'
  return step.action === 'environmental_assessment' ? 'person' : 'agent'
}

export interface TraceRow {
  key: string
  who: string
  body: string
  at: string
  failed?: boolean
}

/** Autopilot events plus the approval request and its decisions, newest first. */
export function buildTrace(events: AutopilotEvent[] | undefined, approval: ApprovalStatus | null): TraceRow[] {
  const rows: TraceRow[] = (events ?? []).map((e, i) => ({
    key: `ev-${i}-${e.at}`,
    who: e.actor || 'Autopilot',
    body: `${cap(e.action)} on ${e.check.replace(/_/g, ' ')}${e.detail ? `: ${e.detail}` : ''}`,
    at: e.at,
    failed: e.status === 'failed',
  }))
  const req = approval?.request
  if (req?.createdAt) rows.push({ key: `req-${req.id}`, who: req.requestedBy || 'A person', body: 'Requested the release decision', at: req.createdAt })
  for (const d of approval?.decisions ?? []) {
    if (!d.createdAt) continue
    rows.push({ key: `dec-${d.id}`, who: d.decided_by || 'A reviewer', body: `${cap(d.decision)} the release${d.notes ? `: ${d.notes}` : ''}`, at: d.createdAt })
  }
  return rows.sort((a, b) => +new Date(b.at) - +new Date(a.at))
}

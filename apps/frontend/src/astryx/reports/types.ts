/**
 * The report model from GET /api/v1/ai-governance/reports/overview (report_model_service.build_overview).
 * Sections are present only for the readers that need them; every number comes from the record.
 */

export type Role = 'executive' | 'compliance' | 'engineering' | 'auditor' | 'risk'
export const ROLES: { key: Role; label: string }[] = [
  { key: 'executive', label: 'Executive' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'engineering', label: 'Engineering' },
  { key: 'auditor', label: 'Auditor' },
  { key: 'risk', label: 'Risk' },
]

export type ReadinessKey = 'met' | 'progress' | 'attention' | 'notstarted'
export type Readiness = Record<ReadinessKey, number> & { total: number; pct: number; systems: number }

export type RoadStep = {
  systemId: string
  systemName: string
  check: string | null
  action: string | null
  evidenceClass: string | null
  closes: string[]
  gain: number
  owner: string | null
}
export type Road = { start: number; steps: RoadStep[]; forecast: number }

export type ProofCounts = { measured: number; estimated: number; attested: number; none: number }
export type Proof = ProofCounts & {
  bySystem: (ProofCounts & { systemId: string; name: string })[]
  byGroup: (ProofCounts & { group: string })[]
}

export type Governed = {
  found: number
  registered: number
  checked: number
  approved: number
  unregistered: { name: string; kind: string; source: string }[]
  unregisteredCount: number
}

export type Oversight = {
  days: { date: string; agentSteps: number; decisions: number }[]
  agentSteps: number
  decisions: number
  medianWaitHours: number | null
  approvedWithoutPerson: number
}

export type Crosswalk = {
  frameworks: { key: string; name: string; followed: boolean; coverage: number }[]
  sources: string[]
  links: number[][] // links[source][framework] = clauses covered
}

export type Tasks = {
  open: number
  overdue: number
  overdueList: { title: string; subject: string | null; owner: string; daysLate: number }[]
  byOwner: { owner: string; onTime: number; overdue: number }[]
}

export type Grid = {
  systems: { id: string; name: string }[]
  requirements: { key: string; control: string; title: string; group: string | null; cells: string[] }[]
}

export type GateSystem = {
  id: string
  name: string
  tier: string
  verdict: string | null
  approvalStatus: string | null
  confidence: number | null
  checks: { key: string; label: string | null; state: string; fails: boolean; stale: boolean }[]
}

export type Engineering = {
  toolExposure: { systemId: string; systemName: string; agent: string | null; tool: string; policy: string | null; gated: boolean; effect: string | null }[]
  fairnessDrift: { systemId: string; systemName: string; threshold: number | null; points: { at: string; value: number }[] }[]
  fixes: {
    title: string
    systemName: string
    priority: string
    status: string
    owner: string | null
    kind: 'evaluation' | 'task'
    evaluationId: string | null
    summary: string | null
  }[]
}

export type Auditor = {
  ledger: {
    chains: { kind: string; chains: number; entries: number | null; broken: number }[]
    entries: number
    intact: boolean
    recent: { at: string; kind: 'agent' | 'step' | 'decision' | 'audit' | 'seal'; hash: string }[]
  }
  sample: { seed: string; size: number; population: number; items: { id: string; title: string; type: string; provenance: string; systemName: string }[] }
  soa: null | {
    systemId: string
    systemName: string
    controls: { key: string; control: string; title: string; group: string | null; readiness: ReadinessKey; applicability: string | null; justification: string | null }[]
  }
  packs: { id: string; title: string; createdAt: string; manifestHash: string; items: number }[]
}

export type RiskModel = {
  risks: { id: string; title: string; systemName: string; severity: string; likelihood: string; impact: number; chance: number; status: string; owner: string | null }[]
  heat: { chance: number; impact: number; count: number }[]
  acceptanceWaiting: { id: string; title: string; systemName: string; owner: string | null; proposedBy: string | null; waitingDays: number | null }[]
}

export type Decision = { id: string; systemName: string; requestedBy: string | null; waitingDays: number | null }

export type BriefingPart = { text: string } | { fact: string; value: string; note: string; tone: '' | 'need' | 'bad' }
export type Briefing = { source: 'template' | 'model'; parts: BriefingPart[] }

export type ReportModel = {
  role: Role
  scope: { systemId: string | null; systemName: string | null }
  framework: { key: string | null; name: string | null }
  followed: string[]
  systemsCount: number
  outOfScope: number
  generatedAt: string
  briefing: Briefing
  readiness?: Readiness
  road?: Road
  proof?: Proof
  governed?: Governed
  oversight?: Oversight
  decisions?: Decision[]
  risk?: RiskModel
  crosswalk?: Crosswalk
  tasks?: Tasks
  grid?: Grid
  systems?: GateSystem[]
  engineering?: Engineering
  auditor?: Auditor
}

export type SealedReport = {
  id: string
  title: string
  role: Role
  systemId: string | null
  sha256: string
  approvedBy: string | null
  approvedAt: string | null
  createdAt?: string
}

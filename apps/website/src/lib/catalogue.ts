// Homepage data, read at build time from the packs catalogue the backend serves.
// One source: the run machine, the evaluation table and the pillars all read from here.
import catalogue from '../../../backend/src/api/routers/pack_catalogue_data/catalogue.json';

type Step = (typeof catalogue.workflows)[number]['steps'][number];

// Steps a person completes today; the ledger records them as manual (see the FAQ).
const manualToday = new Set(['collect', 'check', 'suggest', 'preflight', 'act', 'verify']);

const releaseGate = catalogue.workflows.find((w) => w.id === 'deployment_release_gate');
if (!releaseGate) throw new Error('deployment_release_gate missing from the catalogue');

// The main line of the workflow, in order, without the revise and escalate branches.
const lineIds = ['trigger', 'collect', 'check', 'suggest', 'preflight', 'ask', 'act', 'verify', 'file-evidence'];
const byId = new Map<string, Step>(releaseGate.steps.map((s) => [s.id, s]));

export const runWorkflow = {
  id: releaseGate.id,
  name: releaseGate.name,
  autonomy: releaseGate.autonomy,
  approver: releaseGate.approver,
  separationOfDuties: releaseGate.separationOfDuties,
  gate: releaseGate.gate,
  steps: lineIds.map((id) => {
    const s = byId.get(id) ?? releaseGate.steps.find((x) => x.kind === id.replace('-evidence', ''));
    if (!s) throw new Error(`release gate step ${id} missing`);
    return {
      id,
      kind: s.kind,
      type: s.type,
      title: s.title,
      detail: s.detail,
      permission: s.permission,
      output: s.output,
      failure: s.failure,
      auto: s.runsWithoutApproval,
      manualToday: manualToday.has(s.kind),
    };
  }),
  revise: byId.get('revise')?.failure ?? null,
  escalate: byId.get('escalate')?.failure ?? null,
};

export type EngineState = 'exists' | 'partial' | 'none';
const engineState = (e: string): EngineState => (e === 'Engine exists' ? 'exists' : e === 'Partial' ? 'partial' : 'none');

export const evaluations = catalogue.evaluations.map((e) => ({
  id: e.id,
  code: e.id.replace(/^EV-/, ''),
  name: e.name,
  measures: e.measures,
  metric: e.metric,
  threshold: e.threshold,
  thresholdSource: e.thresholdSource,
  appliesTo: e.appliesTo,
  pillar: e.pillar,
  engine: engineState(e.engine),
  tests: e.tests,
}));

export const engineCounts = evaluations.reduce(
  (acc, e) => ({ ...acc, [e.engine]: acc[e.engine] + 1 }),
  { exists: 0, partial: 0, none: 0 } as Record<EngineState, number>,
);

// Filters match on the catalogue's "applies to" text; "Any" belongs to every filter.
export const evalFilters = [
  { key: 'all', label: 'All', match: /./ },
  { key: 'agents', label: 'Agents', match: /agent/i },
  { key: 'llm', label: 'LLM apps and RAG', match: /llm|rag/i },
  { key: 'models', label: 'Models and data', match: /model|data/i },
  { key: 'decisions', label: 'Decision systems', match: /decision/i },
].map((f) => ({ key: f.key, label: f.label, count: evaluations.filter((e) => f.match.test(e.appliesTo) || /^any$/i.test(e.appliesTo)).length, match: f.match.source }));

const pillarOrder = ['GOVERN', 'EVALUATE', 'SECURE', 'COMPLY'];
export const pillars = pillarOrder.map((id) => {
  const p = catalogue.pillars.find((x) => x.id === id)!;
  return {
    id,
    name: p.name,
    description: p.description,
    workflows: catalogue.workflows.filter((w) => w.pillar === id).length,
    evaluations: catalogue.evaluations.filter((e) => e.pillar === id).length,
    packs: catalogue.packs.filter((k) => k.pillar === id).map((k) => ({ name: k.name, description: k.description })),
  };
});

// Evaluation groups for the table: security, behaviour and fairness, governance and compliance.
export const evalGroups = [
  { key: 'SECURE', label: 'Security', items: evaluations.filter((e) => e.pillar === 'SECURE') },
  { key: 'EVALUATE', label: 'Behaviour and fairness', items: evaluations.filter((e) => e.pillar === 'EVALUATE') },
  { key: 'GOVERN', label: 'Governance and compliance', items: evaluations.filter((e) => e.pillar === 'GOVERN' || e.pillar === 'COMPLY') },
];

// Short framework labels for requirement chips. Static display config; the IDs come from the catalogue.
const shortNames: Record<string, string> = {
  NISTRMF: 'NIST AI RMF', ISO42001: 'ISO/IEC 42001', UKAICOP: 'UK AI Cyber CoP', NISTADV: 'NIST AI 100-2',
  OWASPLLM: 'OWASP LLM', ATLAS: 'MITRE ATLAS', EUAIA: 'EU AI Act', AIVERIFY: 'AI Verify', NIST600: 'NIST AI 600-1',
  OWASPAG: 'OWASP Agentic', OWASPMCP: 'OWASP MCP', CSAAICM: 'CSA AICM', INDAI: 'India AI Guidelines',
  SSDF218A: 'NIST SSDF 218A', MAESTRO: 'CSA MAESTRO',
};
export const frameworkLabel = (key: string) =>
  shortNames[key] ?? catalogue.frameworks.find((f) => f.key === key)?.name.split(/[:(]/)[0].trim() ?? key;

/**
 * The roadmap page's story: eras, months and plans. Monthly commit counts come from src/lib/roadmap-activity.ts
 * (scripts/roadmap-data.mjs, from git history); the plans follow ROADMAP.md on main. Months before July 2025 have no
 * repository, so their summaries are written here by hand.
 */
import activity from './roadmap-activity';

export interface Era { key: string; name: string; color: string; from: string; to: string }
export const ERAS: Era[] = [
  { key: 'idea', name: 'Idea', color: '#9096a0', from: '2024-12', to: '2025-06' },
  { key: 'toolkit', name: 'Bias toolkit', color: '#6f7580', from: '2025-07', to: '2025-10' },
  { key: 'compliance', name: 'Compliance', color: '#2e7d8c', from: '2025-11', to: '2026-03' },
  { key: 'evidence', name: 'Evidence', color: '#1f9d7a', from: '2026-04', to: '2026-08' },
  { key: 'agentic', name: 'Agentic governance', color: '#15171a', from: '2026-09', to: '2026-12' },
  { key: 'next', name: 'Planned', color: '#9096a0', from: '2027-01', to: '2027-12' },
];

export const FIRST = '2024-12';
export const TODAY = '2026-11';
export const LAST = '2027-12';

/** Labelled points on the line. */
export const STOPS: Array<{ month: string; title: string; note: string; release?: boolean; planned?: boolean }> = [
  { month: '2024-12', title: 'The idea', note: 'Fair before it ships?' },
  { month: '2025-02', title: 'Plan and local code', note: 'On a laptop' },
  { month: '2025-07', title: 'First commit', note: 'Public on GitHub' },
  { month: '2025-11', title: 'India compliance', note: 'NITI Aayog, RBI' },
  { month: '2026-03', title: 'Audit engine, roles', note: '24 checks, 5 frameworks' },
  { month: '2026-08', title: 'Assurance rebuild', note: 'Signed evidence' },
  { month: '2026-11', title: 'v0.5.0, agents', note: 'Live runs, explained decisions', release: true },
  { month: '2027-03', title: 'Q1 2027', note: 'India checks, Evidence Passport', planned: true },
  { month: '2027-09', title: 'Later in 2027', note: 'Sandboxed workers, triggers', planned: true },
];

export interface Moment { when: string; title: string; text: string; tag?: string; local?: boolean; planned?: boolean; items?: string[] }
export interface Quarter { label: string; span: string; era: string; moments: Moment[] }

export const QUARTERS: Quarter[] = [
  { label: 'Q4 2024', span: 'December', era: 'idea', moments: [
    { when: 'Dec', title: 'The idea', text: 'How would you know an AI system is fair before it ships? The question FairMind still answers.', local: true },
  ] },
  { label: 'Q1 2025', span: 'Jan to Mar', era: 'idea', moments: [
    { when: 'Jan to Feb', title: 'Plan and first code', text: 'The plan, and the first code written locally.', local: true },
  ] },
  { label: 'Q2 2025', span: 'Apr to Jun', era: 'idea', moments: [
    { when: 'Apr to Jun', title: 'Still on a laptop', text: 'Local development until the repository went public in July.', local: true },
  ] },
  { label: 'Q3 2025', span: 'Jul to Sep', era: 'toolkit', moments: [
    { when: 'Jul', title: 'Public on GitHub', text: '23 July: the first public commit.' },
    { when: 'Aug', title: 'A bias dashboard', text: 'The dashboard, sidebar navigation and the first real data integration.' },
    { when: 'Sep', title: 'Datasets and simulation', text: 'Dataset management, an ML simulation engine and the first security and compliance work.' },
  ] },
  { label: 'Q4 2025', span: 'Oct to Dec', era: 'compliance', moments: [
    { when: 'Oct', title: 'Security first', text: 'Token handling moved to PyJWT to close critical vulnerabilities.' },
    { when: 'Nov', title: 'India compliance', text: 'NITI Aayog and RBI checks, a real-time monitor, and the FairMind brand across app and website.' },
    { when: 'Dec', title: 'Faster bias analysis', text: 'Bias detection rebuilt on DuckDB, with data distribution views.' },
  ] },
  { label: 'Q1 2026', span: 'Jan to Mar', era: 'compliance', moments: [
    { when: 'Feb', title: 'Works on phones', text: 'Mobile layouts across the app.' },
    { when: 'Mar', title: 'Compliance audit engine and roles', text: '24 checks across 5 frameworks, organisation roles and permissions, and the first public roadmap.', tag: 'v2.0.0-rbac' },
  ] },
  { label: 'Q2 2026', span: 'Apr to Jun', era: 'evidence', moments: [
    { when: 'Apr', title: 'Real statistics', text: 'Simulated results replaced with real statistical computations.' },
    { when: 'Jun', title: 'AI-BOM fairness evidence', text: 'A fairness evidence profile for AI bills of materials, and the research behind it.' },
  ] },
  { label: 'Q3 2026', span: 'Jul to Sep', era: 'evidence', moments: [
    { when: 'Aug', title: 'The assurance rebuild', text: 'PostgreSQL only, signed evidence and deterministic tests: the base the release gate stands on.' },
  ] },
  { label: 'Q4 2026', span: 'Oct to Dec, now', era: 'agentic', moments: [
    { when: 'Nov, week 1', title: 'The release gate grows up', text: 'Manual evidence capped, the shortest path to Go priced, a leased job queue, and WEAT and SEAT bias tests.', tag: 'v0.2' },
    { when: 'Nov, week 2', title: 'Discovery everywhere', text: 'AI systems found through vendor admin APIs, clouds, sign-in, gateways, logs and MCP; all 109 evaluations documented.', tag: 'v0.3' },
    { when: 'Nov, week 3', title: 'Agents in view', text: 'Shadow AI on laptops and browsers, live runs with stated reasons, consent through Olai, and the Found list.', tag: 'v0.4' },
    { when: 'Nov, week 4', title: 'Agents explained', text: 'Internal audit for ISO 42001, explained decisions, evaluation correctness, and What\'s new.', tag: 'v0.5' },
  ] },
];

export const NOW = {
  label: 'Now', span: 'Q4 2026',
  themes: [
    { title: 'Nothing broken, nothing misleading', text: 'Every page people can reach works and says only what the code does.' },
    { title: 'Trust in every result', text: 'No placeholder scores or sample results anywhere; each evaluation verdict explained.' },
    { title: 'Agents, end to end', text: 'Live runs, explained decisions and Shadow AI hardened with design partners.' },
  ],
};

export const NEXT = {
  label: 'Next', span: 'Q1 2027',
  groups: [
    { title: 'India and evidence', items: ['DPDP, NITI Aayog and RBI checks in the app, with DPDP and GDPR in the catalogue', 'Evidence Passport upload and inspection-pack export from the app, SDK and CLI', 'Organisation audit-report export'] },
    { title: 'Systems and decisions', items: ['Environmental assessment and approval on the system page', 'Edit, re-tier and archive an AI system', 'Approval workflow editor and decision history', 'The policy gate shown next to the release gate'] },
    { title: 'Evaluations', items: ['The organisation\'s own model as an LLM judge, with judge comparison', 'Engines for the catalogue evaluations still partial', 'Risk taxonomies from IBM, MIT and OECD on the risks page'] },
    { title: 'Operations', items: ['Compliance automation: schedules, Run now, violations and reports', 'API key management', 'Workflow version history', 'Accessibility audit and keyboard navigation'] },
  ],
};

export const LATER = {
  label: 'Later', span: '2027 and beyond',
  items: ['Sandboxed evaluation workers', 'Workflows that start on schedules and triggers', 'Ask about any system or finding', 'Internationalisation, starting with the navigation', 'An optional content-safety evaluator'],
};

export const RESEARCH = ['Causal DAG builder', 'Bias propagation across agent chains', 'Ingesting regulatory changes', 'Fairness and performance trade-off explorer',
  'SEBI disclosure mapping', 'FRIA and DPIA generation', 'Multi-jurisdiction what-if simulator', 'Bias lineage across model components',
  'Privacy-preserving fairness audits', 'Fairness bounds without demographics', 'Synthetic-data fairness', 'Federated fairness', 'Community red-team module'];

const ym = (m: string) => { const [y, mo] = m.split('-').map(Number); return y * 12 + mo - 1; };
const fromYm = (n: number) => `${Math.floor(n / 12)}-${String((n % 12) + 1).padStart(2, '0')}`;
export const MONTHS: string[] = Array.from({ length: ym(LAST) - ym(FIRST) + 1 }, (_, i) => fromYm(ym(FIRST) + i));

/** Commits on main that month; null before the repository existed or after today. */
export const commitsIn = (m: string): number | null =>
  m < activity.firstCommit.slice(0, 7) || m > TODAY ? null : (activity.months as Record<string, number>)[m] ?? 0;

export const eraOf = (m: string) => ERAS.find((e) => m >= e.from && m <= e.to) ?? ERAS[ERAS.length - 1];
export const ACTIVITY = activity;
export const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const monthLabel = (m: string) => `${MONTH_NAMES[Number(m.slice(5)) - 1]} ${m.slice(0, 4)}`;

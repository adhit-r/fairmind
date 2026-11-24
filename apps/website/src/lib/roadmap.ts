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
  { month: '2027-03', title: 'Q1 2027', note: 'Audit reporting, evidence intake', planned: true },
  { month: '2027-09', title: 'Later in 2027', note: 'Isolated workers, triggers', planned: true },
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
    { title: 'Release the dashboard and report updates', text: 'Verify the path from a failed check to its evidence and retest. Validate scheduled drafts, assigned review and approved export in the target workspace.' },
    { title: 'Close account and organisation gaps', text: 'Verify invitation delivery and sign-in handoffs, and consolidate team administration in Settings.' },
    { title: 'Show what the evidence supports', text: 'Distinguish unavailable, stale and failed results. Keep status and counts within the selected organisation.' },
    { title: 'Align claims with the product', text: 'Update public capability and setup guidance, then remove legacy routes whose callers have moved.' },
  ],
};

export const NEXT = {
  label: 'Next', span: 'Q1 2027',
  groups: [
    { title: 'Reporting and auditors', items: ['Organisation audit-report export', 'Auditor-pack handoff with scoped access, expiry and revocation', 'Verified delivery outcomes and persisted compliance report history'] },
    { title: 'Requirements and evidence', items: ['Trace a framework requirement to the named check and accepted evidence', 'Evidence Passport intake', 'India checks and DPDP/GDPR catalogue scope'] },
    { title: 'Systems and evaluations', items: ['Environmental review and approval', 'Workspace reuse and workflow version history', 'Reachable LLM judge comparison and evidence handoff'] },
    { title: 'Verification', items: ['Independent evaluator benchmarks', 'A private pilot for the gated Assurance V2 workbench', 'Keyboard and accessibility coverage, bundle budgets and CI workflow tests'] },
  ],
};

export const LATER = {
  label: 'Later', span: '2027 and beyond',
  items: ['Isolated evaluation workers and sandbox verification', 'Idempotent workflow starts from schedules and triggers', 'Source-linked answers about systems and findings', 'Internationalisation, starting with the navigation', 'An optional content-safety evaluator'],
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

// Homepage copy. Catalogue numbers come from lib/catalogue.ts.
import { registryTotals } from './registry';

export const autonomy = [
  { level: 'A0', name: 'Manual', detail: 'The agent does nothing unless asked for a draft.' },
  { level: 'A1', name: 'Assist', detail: 'Collects and checks. Humans write every conclusion.' },
  { level: 'A2', name: 'Propose', detail: 'Proposes; nothing is recorded until a human approves. The default.' },
  { level: 'A3', name: 'Act on internal records', detail: 'Files records inside FairMind; humans review by sampling. Never external writes.' },
];

export const registry = [
  { b: 'EU AI Act', s: '2024/1689', href: '/frameworks/eu-ai-act/' },
  { b: 'ISO/IEC 42001', s: '', href: '/frameworks/iso-42001/' },
  { b: 'NIST AI RMF', s: '', href: '/frameworks/nist-ai-rmf/' },
  { b: 'OWASP', s: 'Agentic Top 10', href: '/frameworks/' },
  { b: 'AIUC-1', s: '', href: '/frameworks/' },
  { b: 'OWASP', s: 'LLM Top 10', href: '/frameworks/' },
  { b: 'MITRE ATLAS', s: '', href: '/frameworks/' },
  { b: 'NIST AI 600-1', s: '', href: '/frameworks/nist-ai-rmf/' },
  { b: 'ISO/IEC 42005', s: '', href: '/frameworks/iso-42001/' },
  { b: 'CSA', s: 'MAESTRO', href: '/frameworks/' },
  { b: 'OWASP', s: 'MCP Top 10', href: '/frameworks/' },
];

export const faqs = [
  {
    q: 'What is agentic AI governance?',
    a: 'Agentic AI governance uses AI agents to run the repeatable parts of governing AI systems: collecting evidence, checking it against framework requirements, proposing records and fixes, and filing the trace. The decisions stay with people. In FairMind, every workflow stops at an approval gate before anything is recorded or changed.',
  },
  {
    q: 'What does a FairMind agent actually do?',
    a: 'It runs a workflow made of seven step types: collect, check, suggest, ask a person, act, verify, and file evidence. Today the trigger, escalate and file steps run themselves, the gate steps open an approval request, and a person completes the collect, check, suggest, act and verify steps, which the ledger records as manual. Agent-executed steps arrive workflow by workflow, behind the same gates, with scoped read-only credentials, rules before model judgement, and a citation for every finding.',
  },
  {
    q: 'What does FairMind evaluate?',
    a: 'The catalogue defines 109 evaluations: 53 for security, 46 for behaviour and fairness, and 10 for governance and compliance. They cover agents (tool least privilege, out-of-scope actions, MCP permissions, kill switches), LLM apps and RAG (prompt injection, jailbreaks, prompt leakage, groundedness, harmful content), models and data (accuracy, calibration, drift, membership inference, backdoors) and decision systems (selection-rate parity, error-rate parity, intersectional slices). Each one names its metric, its threshold and where that threshold comes from, and every evaluator declares whether it is validated, runs through an external provider, reads metadata only, or is not yet available.',
  },
  {
    q: 'Can the agent change things on its own?',
    a: 'Only inside FairMind, and only if you set that workflow to autonomy level A3. The default is A2: the agent proposes and a person approves. External systems are never written without an approval. If an approver is unreachable or no policy covers the action, nothing happens.',
  },
  {
    q: 'Which frameworks does FairMind cover?',
    a: `The registry holds ${registryTotals.frameworks} frameworks, including the EU AI Act, ISO/IEC 42001, NIST AI RMF and AI 600-1, the OWASP Top 10 for LLM and Agentic applications, AIUC-1, MITRE ATLAS, the OWASP MCP Top 10, CSA MAESTRO, Singapore’s Model AI Governance Framework, and national rules from India, Japan, Korea, China and US states. One workflow run counts toward every requirement it maps to.`,
  },
  {
    q: 'How is FairMind’s own agent governed?',
    a: 'Twenty runtime controls apply to it: per-step scoped identity, a deterministic tool allowlist that prompts cannot widen, collected content treated as data rather than instructions, mandatory citations, pinned model and prompt versions with golden-set evaluations, a hash-chained immutable trace, cost and rate caps, and a kill switch per run. Customers can see the agent’s metrics and incidents.',
  },
  {
    q: 'Is FairMind a certification?',
    a: 'No. FairMind produces and organises evidence and records human decisions. Certification and conformity decisions stay with your reviewers, auditors, and, where relevant, accredited bodies.',
  },
];

// llms.txt (llmstxt.org): a plain-text map of the site for AI assistants, built from the catalogue.
import type { APIRoute } from 'astro';
import { registry, registryTotals } from '../lib/registry';
import { pillars } from '../lib/catalogue';
import { frameworks } from '../lib/frameworks';

const site = 'https://fairmind.xyz';

export const GET: APIRoute = () => {
  const lines = [
    '# FairMind',
    '',
    `> FairMind is an agentic AI governance platform. Agent workflows collect evidence, check it against framework requirements, propose records and fixes, and file a hash-chained trace. Every workflow stops at a human approval gate before anything is recorded or changed. The catalogue holds ${registryTotals.workflows} workflows, ${registryTotals.evaluations} evaluations and ${registryTotals.frameworks} frameworks.`,
    '',
    'FairMind produces and organises evidence and records human decisions. It is not a certification.',
    '',
    '## Product',
    '',
    `- [Platform](${site}/features/): the system journey, packs and workflows with human gates, the ledger and the CI release gate`,
    `- [Use cases](${site}/use-cases/): how engineers, compliance leads, approvers, security teams and auditors use it`,
    `- [Walkthrough](${site}/demo/): one model from registry to release decision`,
    `- [Comparison](${site}/comparison/): where FairMind sits next to evaluation tools and GRC suites`,
    `- [Roadmap](${site}/roadmap/): shipped, next, later`,
    '',
    '## Pillars',
    '',
    ...pillars.map((p) => `- ${p.name}: ${p.description} (${p.workflows} workflows, ${p.evaluations} evaluations, ${p.packs.length} packs)`),
    '',
    '## Framework guides',
    '',
    ...frameworks.map((f) => `- [${f.shortName}](${site}/frameworks/${f.slug}/): ${f.description}`),
    `- [All ${registryTotals.frameworks} frameworks](${site}/frameworks/): ${registry.slice(0, 12).map((r) => r.name).join(', ')} and more`,
    '',
    '## Optional',
    '',
    `- [Research](${site}/research/): methods and design notes`,
    '- [Blog](https://blog.fairmind.xyz/): writing on AI assurance, standards and regulation',
    '- [Docs](https://docs.fairmind.xyz/): product documentation',
    `- [About](${site}/about/)`,
    `- [Contact](${site}/contact/)`,
    '',
  ];
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};

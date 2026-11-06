// The framework registry, read at build time from the packs catalogue the backend serves.
import catalogue from '../../../backend/src/api/routers/pack_catalogue_data/catalogue.json';

export type RegistryKind = 'law' | 'standard' | 'security' | 'guidance' | 'reference';

export const kindLabels: Record<RegistryKind, string> = {
  law: 'Binding law',
  standard: 'Standards',
  security: 'Security',
  guidance: 'Guidance',
  reference: 'Reference',
};

export interface RegistryEntry {
  key: string;
  name: string;
  jurisdiction: string;
  type: string;
  kind: RegistryKind;
  requirements: number;
  workflows: number;
  controls: number;
  evaluations: number;
  guide?: string;
}

// Catalogue keys that have a plain-English guide under /frameworks/.
const guides: Record<string, string> = {
  EUAIA: 'eu-ai-act',
  ISO42001: 'iso-42001',
  NISTRMF: 'nist-ai-rmf',
  RBIFREEAI: 'rbi-free-ai',
  OWASPLLM: 'owasp-llm-top-10',
  OWASPAG: 'owasp-agentic-top-10',
  ATLAS: 'mitre-atlas',
  AIUC1: 'aiuc-1',
  NIST600: 'nist-ai-600-1',
  ISO42005: 'iso-42005',
  OWASPMCP: 'owasp-mcp-top-10',
  MAESTRO: 'csa-maestro',
};

const requirementsByFramework = new Map<string, number>();
for (const r of catalogue.requirements) {
  if (r.active === false) continue;
  requirementsByFramework.set(r.framework, (requirementsByFramework.get(r.framework) ?? 0) + 1);
}

const controlsByFramework = new Map<string, Set<string>>();
for (const x of catalogue.crosswalk) {
  const fw = x.key.split('|')[0];
  if (!controlsByFramework.has(fw)) controlsByFramework.set(fw, new Set());
  controlsByFramework.get(fw)!.add(x.commonControl);
}

function kindOf(f: (typeof catalogue.frameworks)[number], requirements: number): RegistryKind {
  if (requirements === 0) return 'reference';
  if (f.binding.startsWith('Binding')) return 'law';
  if (/standard|certifiable/i.test(f.type)) return 'standard';
  if (f.pillar === 'SECURE') return 'security';
  return 'guidance';
}

export const registry: RegistryEntry[] = catalogue.frameworks
  .map((f) => {
    const requirements = requirementsByFramework.get(f.key) ?? 0;
    const controls = controlsByFramework.get(f.key) ?? new Set<string>();
    const workflows = catalogue.workflows.filter((w) => controls.has(w.commonControl)).length;
    return {
      key: f.key,
      name: f.name,
      jurisdiction: f.jurisdiction,
      type: f.type,
      kind: kindOf(f, requirements),
      requirements,
      workflows,
      controls: controls.size,
      evaluations: catalogue.evaluations.filter((e) => e.tests.some((t) => t.startsWith(`${f.key}|`))).length,
      guide: guides[f.key],
    };
  })
  .sort((a, b) => b.requirements - a.requirements || a.name.localeCompare(b.name));

export const registryTotals = {
  frameworks: registry.length,
  mapped: registry.filter((e) => e.requirements > 0).length,
  requirements: registry.reduce((n, e) => n + e.requirements, 0),
  workflows: catalogue.workflows.length,
  evaluations: catalogue.evaluations.length,
  commonControls: catalogue.commonControls.length,
  crosswalk: catalogue.crosswalk.length,
};

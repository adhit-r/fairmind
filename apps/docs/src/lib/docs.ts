import fs from "node:fs/promises";
import path from "node:path";

export type DocItem = {
  slug: string;
  title: string;
  file: string;
  summary: string;
};

const DOCS_ROOT = path.join(process.cwd(), "content", "docs");

export const DOC_ITEMS: DocItem[] = [
  {
    slug: "getting-started",
    title: "Getting Started",
    file: "getting-started.mdx",
    summary: "Set up FairMind and run your first governance workflow.",
  },
  {
    slug: "bias-detection",
    title: "Bias Detection",
    file: "bias-detection.mdx",
    summary: "Run fairness diagnostics and understand bias risk drivers.",
  },
  {
    slug: "simulation",
    title: "Simulation",
    file: "simulation.mdx",
    summary: "Evaluate model behavior through scenario-based simulations.",
  },
  {
    slug: "monitoring",
    title: "Monitoring",
    file: "monitoring.mdx",
    summary: "Track risk, drift, and runtime issues in production.",
  },
  {
    slug: "model-provenance",
    title: "Model Provenance",
    file: "model-provenance.mdx",
    summary: "Maintain lineage, traceability, and model evidence records.",
  },
  {
    slug: "explainability",
    title: "Explainability",
    file: "explainability.mdx",
    summary: "Generate interpretable insights and explanation artifacts.",
  },
  {
    slug: "security-compliance",
    title: "Security & Compliance",
    file: "security-compliance.mdx",
    summary: "Operationalize controls and map evidence to requirements.",
  },
];

export async function readDocBySlug(slug: string): Promise<{ doc: DocItem; content: string } | null> {
  const doc = DOC_ITEMS.find((item) => item.slug === slug);
  if (!doc) return null;

  const filePath = path.join(DOCS_ROOT, doc.file);
  try {
    const content = await fs.readFile(filePath, "utf8");
    return { doc, content };
  } catch {
    return {
      doc,
      content: `# Missing document\n\nCould not load: ${doc.file}`,
    };
  }
}

export async function searchDocs(query?: string): Promise<DocItem[]> {
  const q = (query ?? "").trim().toLowerCase();
  if (!q) return DOC_ITEMS;

  const hits: DocItem[] = [];
  for (const doc of DOC_ITEMS) {
    if (doc.title.toLowerCase().includes(q) || doc.summary.toLowerCase().includes(q)) {
      hits.push(doc);
      continue;
    }

    try {
      const content = await fs.readFile(path.join(DOCS_ROOT, doc.file), "utf8");
      if (content.toLowerCase().includes(q)) hits.push(doc);
    } catch {
      // Keep search resilient to missing content files.
    }
  }

  return hits;
}

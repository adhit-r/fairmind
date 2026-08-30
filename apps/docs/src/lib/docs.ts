import fs from "node:fs/promises";
import path from "node:path";

export type DocItem = {
  slug: string;
  title: string;
  file: string;
  summary: string;
  section: "Start here" | "Assurance foundation" | "Operate safely" | "Regulatory context";
};

const DOCS_ROOT = path.join(process.cwd(), "content", "docs");

export const DOC_ITEMS: DocItem[] = [
  {
    slug: "release-boundary",
    title: "P0 release boundary",
    file: "release-boundary.mdx",
    summary: "What v2.1.0-alpha.1 includes, excludes, and keeps default-off.",
    section: "Start here",
  },
  {
    slug: "getting-started",
    title: "Getting started",
    file: "getting-started.mdx",
    summary: "Run the verified repository locally and open the gated assurance surfaces.",
    section: "Start here",
  },
  {
    slug: "assurance-workflow",
    title: "Assurance workflow",
    file: "assurance-workflow.mdx",
    summary: "Follow target, suite, plan, run, evidence, review, and decision boundaries.",
    section: "Assurance foundation",
  },
  {
    slug: "evidence-trust-review",
    title: "Evidence trust and review",
    file: "evidence-trust-review.mdx",
    summary: "Understand Passport binding, admission, freshness, provenance, and review.",
    section: "Assurance foundation",
  },
  {
    slug: "permissions-and-separation",
    title: "Permissions and separation",
    file: "permissions-and-separation.mdx",
    summary: "Apply literal permissions, four-eyes review, and audited override controls.",
    section: "Assurance foundation",
  },
  {
    slug: "api-integration",
    title: "API integration",
    file: "api-integration.mdx",
    summary: "Use the V2 route boundary, scope headers, idempotency, and bounded errors.",
    section: "Operate safely",
  },
  {
    slug: "operator-runbook",
    title: "Operator runbook",
    file: "operator-runbook.mdx",
    summary: "Enable, validate, observe, and roll back the default-off P0 control plane.",
    section: "Operate safely",
  },
  {
    slug: "eu-ai-act-crosswalk",
    title: "EU AI Act crosswalk",
    file: "eu-ai-act-crosswalk.mdx",
    summary: "Relate P0 evidence controls to selected obligations without asserting compliance.",
    section: "Regulatory context",
  },
  {
    slug: "limitations-roadmap",
    title: "Limitations and roadmap",
    file: "limitations-roadmap.mdx",
    summary: "See unavailable execution capabilities and the gates that remain open.",
    section: "Regulatory context",
  },
];

function stripFrontmatter(source: string): string {
  if (!source.startsWith("---\n")) return source;
  const end = source.indexOf("\n---\n", 4);
  return end === -1 ? source : source.slice(end + 5).trimStart();
}

export async function readDocBySlug(slug: string): Promise<{ doc: DocItem; content: string } | null> {
  const doc = DOC_ITEMS.find((item) => item.slug === slug);
  if (!doc) return null;

  try {
    const source = await fs.readFile(path.join(DOCS_ROOT, doc.file), "utf8");
    return { doc, content: stripFrontmatter(source) };
  } catch {
    return null;
  }
}

export async function searchDocs(query?: string): Promise<DocItem[]> {
  const q = (query ?? "").trim().toLowerCase();
  if (!q) return DOC_ITEMS;

  const hits: DocItem[] = [];
  for (const doc of DOC_ITEMS) {
    if (`${doc.title} ${doc.summary} ${doc.section}`.toLowerCase().includes(q)) {
      hits.push(doc);
      continue;
    }

    try {
      const content = await fs.readFile(path.join(DOCS_ROOT, doc.file), "utf8");
      if (content.toLowerCase().includes(q)) hits.push(doc);
    } catch {
      // A missing canonical document is rejected by the validation gate.
    }
  }

  return hits;
}

export function adjacentDocs(slug: string): { previous?: DocItem; next?: DocItem } {
  const index = DOC_ITEMS.findIndex((item) => item.slug === slug);
  if (index === -1) return {};
  return {
    previous: index > 0 ? DOC_ITEMS[index - 1] : undefined,
    next: index < DOC_ITEMS.length - 1 ? DOC_ITEMS[index + 1] : undefined,
  };
}

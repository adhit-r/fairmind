import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";

const docsRoot = path.resolve("content/docs");
const repoRoot = path.resolve("../..");
const docsForgeRoot = path.join(repoRoot, ".docs-forge");
const expectedSlugs = [
  "release-boundary",
  "getting-started",
  "assurance-workflow",
  "evidence-trust-review",
  "permissions-and-separation",
  "api-integration",
  "operator-runbook",
  "eu-ai-act-crosswalk",
  "limitations-roadmap",
];

const expectedFiles = new Set(expectedSlugs.map((slug) => `${slug}.mdx`));
const files = (await readdir(docsRoot)).filter((file) => file.endsWith(".mdx"));
const errors = [];
const requiredDocsForgeFiles = [
  "scope.json",
  "state.json",
  "answers.json",
  "link-report.md",
  "completeness-report.md",
  "validation-report.md",
  "kb/00-project-overview.md",
  "kb/01-architecture.md",
  "kb/02-public-surface.md",
  "kb/03-features.md",
  "kb/04-existing-docs.md",
  "kb/05-build-and-run.md",
  "kb/06-glossary.md",
  "kb/07-source-inventory.md",
  "kb/08-page-provenance.md",
  "kb/99-open-questions.md",
];

for (const relativePath of requiredDocsForgeFiles) {
  try {
    await access(path.join(docsForgeRoot, relativePath));
  } catch {
    errors.push(`missing Docs Forge artifact: ${relativePath}`);
  }
}

const docsIndex = await readFile(path.resolve("src/lib/docs.ts"), "utf8");
let provenance = "";
try {
  provenance = await readFile(
    path.join(docsForgeRoot, "kb/08-page-provenance.md"),
    "utf8",
  );
} catch {
  // The required-artifact check above reports the missing provenance file.
}

const requiredSections = new Map([
  ["release-boundary.mdx", ["## Included in this release", "## Explicit exclusions", "## Safe claims"]],
  ["getting-started.mdx", ["## Local development", "## What is enabled by default", "## First reading path"]],
  ["operator-runbook.mdx", ["## Prerequisites", "## Procedure", "## Stop conditions", "## Evidence to retain"]],
  ["eu-ai-act-crosswalk.mdx", ["## Start with applicability", "## What P0 can support", "## Current legal guidance can change"]],
]);

for (const filename of expectedFiles) {
  if (!files.includes(filename)) errors.push(`missing canonical page: ${filename}`);
}

for (const filename of files) {
  if (!expectedFiles.has(filename)) errors.push(`uncatalogued public page: ${filename}`);

  const content = await readFile(path.join(docsRoot, filename), "utf8");
  if (!content.startsWith("---\n")) errors.push(`${filename}: missing frontmatter`);
  if (!/^title:\s*.+$/m.test(content)) errors.push(`${filename}: missing title`);
  if (!/^description:\s*.+$/m.test(content)) errors.push(`${filename}: missing description`);
  if (!/^#\s+.+$/m.test(content)) errors.push(`${filename}: missing level-one heading`);
  if (!/^## Related$/m.test(content)) errors.push(`${filename}: missing Related section`);
  if (!docsIndex.includes(`file: "${filename}"`)) {
    errors.push(`${filename}: not reachable from the canonical docs index`);
  }
  if (!provenance.includes(`\`${filename}\``)) {
    errors.push(`${filename}: missing Docs Forge page provenance`);
  }
  for (const section of requiredSections.get(filename) ?? []) {
    if (!content.includes(section)) errors.push(`${filename}: missing required section ${section}`);
  }
  if (/from\s+fairmind\s+import/i.test(content)) {
    errors.push(`${filename}: references the nonexistent public fairmind Python API`);
  }
  if (/ensure(?:s|d)?\s+(?:gdpr|eu ai act|regulatory|legal)?\s*compliance/i.test(content)) {
    errors.push(`${filename}: makes an automatic compliance claim`);
  }

  for (const match of content.matchAll(/\]\((?:\.\/|\/docs\/)([a-z0-9-]+)(?:#[^)]+)?\)/g)) {
    if (!expectedSlugs.includes(match[1])) {
      errors.push(`${filename}: broken internal docs link /docs/${match[1]}`);
    }
  }
}

if (errors.length > 0) {
  console.error(`Documentation validation failed (${errors.length}):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(
  `Documentation validation passed: ${files.length} canonical P0 pages and ${requiredDocsForgeFiles.length} Docs Forge artifacts.`,
);

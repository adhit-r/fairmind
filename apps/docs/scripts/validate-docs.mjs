import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const docsRoot = path.resolve("content/docs");
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

for (const filename of expectedFiles) {
  if (!files.includes(filename)) errors.push(`missing canonical page: ${filename}`);
}

for (const filename of files) {
  if (!expectedFiles.has(filename)) errors.push(`uncatalogued public page: ${filename}`);

  const content = await readFile(path.join(docsRoot, filename), "utf8");
  if (!content.startsWith("---\n")) errors.push(`${filename}: missing frontmatter`);
  if (!/^title:\s*.+$/m.test(content)) errors.push(`${filename}: missing title`);
  if (!/^description:\s*.+$/m.test(content)) errors.push(`${filename}: missing description`);
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

console.log(`Documentation validation passed: ${files.length} canonical P0 pages.`);

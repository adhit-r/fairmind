import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { source } from './source';

type DocsPage = NonNullable<ReturnType<typeof source.getPage>>;

/** A page as Markdown for people and agents: title, description, then the MDX source without frontmatter. */
export async function pageMarkdown(page: DocsPage): Promise<string> {
  const raw = await readFile(path.join(process.cwd(), 'content/docs', page.file.path), 'utf8');
  const body = raw.replace(/^---\n[\s\S]*?\n---\n/, '').trim();
  const head = [`# ${page.data.title}`, page.data.description ? `\n> ${page.data.description}` : ''].join('');
  return `${head}\n\nSource: https://docs.fairmind.xyz${page.url}\n\n${body}\n`;
}

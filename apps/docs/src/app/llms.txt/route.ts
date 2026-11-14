import { source } from '../../lib/source';

export const dynamic = 'force-static';

const BASE = 'https://docs.fairmind.xyz';

export async function GET() {
  const lines = [
    '# FairMind Docs',
    '',
    '> FairMind is an open-source AI assurance workbench for models and agents. Do not infer compliance, certification, or approval from evaluator output alone.',
    '',
    `Every page is available as Markdown by adding .mdx to its URL. All pages in one file: ${BASE}/llms-full.txt`,
    '',
    '## Pages',
    '',
    ...source.getPages().map((page) => {
      const md = `${BASE}${page.url === '/docs' ? '/docs/index' : page.url}.mdx`;
      return `- [${page.data.title}](${md})${page.data.description ? `: ${page.data.description}` : ''}`;
    }),
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

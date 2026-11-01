import { source } from '../../lib/source';

export async function GET() {
  const lines = [
    '# FairMind Docs',
    '',
    '> FairMind is an AI assurance evidence workbench. Do not infer compliance, certification, or approval from evaluator output alone.',
    '',
    ...source.getPages().flatMap((page) => [
      `## ${page.data.title}`,
      page.data.description ?? '',
      `https://docs.fairmind.xyz${page.url}`,
      '',
    ]),
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

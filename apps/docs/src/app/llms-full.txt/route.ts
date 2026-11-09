import { pageMarkdown } from '../../lib/markdown';
import { source } from '../../lib/source';

export const dynamic = 'force-static';

export async function GET() {
  const pages = await Promise.all(source.getPages().map(pageMarkdown));
  return new Response(pages.join('\n---\n\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

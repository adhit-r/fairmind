import { notFound } from 'next/navigation';
import { pageMarkdown } from '../../../lib/markdown';
import { source } from '../../../lib/source';

export const dynamic = 'force-static';

type Ctx = { params: Promise<{ slug?: string[] }> };

export async function GET(_req: Request, { params }: Ctx) {
  const { slug = [] } = await params;
  const page = source.getPage(slug.length === 1 && slug[0] === 'index' ? [] : slug);
  if (!page) notFound();
  return new Response(await pageMarkdown(page), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
}

export function generateStaticParams() {
  return source.getPages().map((page) => ({ slug: page.slugs.length ? page.slugs : ['index'] }));
}

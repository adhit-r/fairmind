import { dayLabel, releases } from '../../lib/releases';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** The changelog as an RSS feed: one entry per release. */
export async function GET() {
  const items = (await releases())
    .map((r) => {
      const body = [r.lead, ...r.items.map((i) => (i.name ? `${i.name}: ${i.text}` : i.text))].filter(Boolean).join('\n');
      return `<item><title>${esc(r.title.startsWith('FairMind v') ? r.title : `FairMind v${r.version}: ${r.title}`)}</title><link>https://fairmind.xyz/changelog/#${esc(r.tag)}</link>`
        + `<guid isPermaLink="false">${esc(r.tag)}</guid>${r.date ? `<pubDate>${new Date(r.date).toUTCString()}</pubDate>` : ''}`
        + `<description>${esc(body || dayLabel(r.date))}</description></item>`;
    })
    .join('');
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>FairMind changelog</title>`
    + `<link>https://fairmind.xyz/changelog/</link><description>What shipped in FairMind, release by release.</description>${items}</channel></rss>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
}

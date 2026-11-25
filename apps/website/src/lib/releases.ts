/**
 * FairMind's release notes, read from GitHub releases at build time, the same notes the app's What's new shows.
 * Convention: an optional "# Title" and lead paragraph, then "## Area" sections of "- Name: what it does (#123)".
 * Pull request numbers, app links and the Install section are developer detail and are left out here.
 */

export interface ReleaseItem { area: string; name: string; text: string }
export interface Release { tag: string; version: string; title: string; lead: string; date: string | null; url: string; items: ReleaseItem[] }

const REPO = 'adhit-r/fairmind';
const SKIP = new Set(['install', 'installation']);
const REFS = /\s*\((?:#\d+(?:,\s*)?)+\)/g;

function item(area: string, line: string): ReleaseItem {
  const body = line.replace(REFS, '').replace(/\[([^\]]+)\]\((?:https:\/\/app\.fairmind\.xyz)?\/[^)\s]*\)/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '').trim().replace(/[ .]+$/, '') + '.';
  const at = body.indexOf(': ');
  const name = at > 0 && at <= 60 ? body.slice(0, at) : '';
  const rest = name ? body.slice(at + 2) : body;
  return { area, name, text: rest.charAt(0).toUpperCase() + rest.slice(1) };
}

export function parseRelease(rel: { tag_name: string; name?: string; body?: string; published_at?: string; html_url: string }): Release {
  let title: string | null = null;
  let area: string | null = null;
  let started = false;
  const lead: string[] = [];
  const items: ReleaseItem[] = [];
  for (const raw of (rel.body ?? '').replace(/\r\n/g, '\n').split('\n')) {
    const line = raw.trim();
    if (line.startsWith('# ') && title === null && !started) title = line.slice(2).trim();
    else if (line.startsWith('## ')) {
      started = true;
      const name = line.slice(3).trim();
      area = SKIP.has(name.toLowerCase()) ? null : name;
    } else if ((line.startsWith('- ') || line.startsWith('* ')) && area) items.push(item(area, line.slice(2)));
    else if (line && !started && !line.startsWith('#') && !line.startsWith('```') && !line.startsWith('**Full changelog')) lead.push(line);
  }
  const version = rel.tag_name.replace(/^v|-alpha$|-beta$/g, '');
  return {
    tag: rel.tag_name,
    version,
    title: title ?? `FairMind v${version}`,
    lead: lead.join(' ').replace(REFS, '').trim(),
    date: rel.published_at ?? null,
    url: rel.html_url,
    items,
  };
}

let cached: Promise<Release[]> | null = null;

/** Published releases, newest first; none when GitHub cannot be reached, so the build still succeeds. */
export function releases(): Promise<Release[]> {
  cached ??= fetch(`https://api.github.com/repos/${REPO}/releases?per_page=30`, {
    headers: { Accept: 'application/vnd.github+json', ...(process.env.GITHUB_TOKEN ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } : {}) },
  })
    .then((r) => (r.ok ? r.json() : []))
    .then((list: Array<Parameters<typeof parseRelease>[0] & { draft?: boolean }>) => list.filter((r) => !r.draft).map(parseRelease))
    .catch(() => []);
  return cached;
}

export const releasesUrl = `https://github.com/${REPO}/releases`;

export const dayLabel = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '';

/** The area chips: the first word of each section heading people filter by. */
export const areaKey = (area: string) => area.split(/\s+/)[0].toLowerCase().replace(/[^a-z]/g, '');

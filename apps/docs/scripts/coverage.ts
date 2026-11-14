/**
 * Fails the build when the docs fall behind the app: every route in outline.json (`npm run outline`) must have a doc
 * page showing <PageAnatomy route="…" />, every recording a page shows must have a tour, and every tour a page.
 *
 *   npm run coverage        # runs by itself before `build`
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const DOCS = fileURLToPath(new URL('..', import.meta.url))
const OUTLINE = join(DOCS, 'outline.json')
if (!existsSync(OUTLINE)) { console.error('docs coverage: no outline.json: run npm run outline'); process.exit(1) }
const outline = JSON.parse(readFileSync(OUTLINE, 'utf8')) as { routes: Record<string, { path: string }> }

const texts: string[] = []
const walk = (dir: string): void => {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name)
    if (e.isDirectory()) walk(p)
    else if (p.endsWith('.mdx')) texts.push(readFileSync(p, 'utf8'))
  }
}
walk(join(DOCS, 'content/docs'))
const all = texts.join('\n')
const shown = new Set([...all.matchAll(/<PageAnatomy route="([^"]+)"/g)].map(m => m[1]!))

const problems: string[] = []
for (const [route, r] of Object.entries(outline.routes)) {
  if (!shown.has(route)) problems.push(`app route "${route}" (${r.path}) has no doc page: add <PageAnatomy route="${route}" />`)
}
for (const route of shown) if (!outline.routes[route]) problems.push(`<PageAnatomy route="${route}" /> names a route that is not in outline.json`)

const wanted = new Set([...all.matchAll(/<(?:Watch|TryIt) page="([^"]+)"/g)].map(m => m[1]!))
const toured = new Set(readdirSync(join(DOCS, 'tours')).filter(f => f.endsWith('.ts'))
  .map(f => /page: '([^']+)'/.exec(readFileSync(join(DOCS, 'tours', f), 'utf8'))?.[1] ?? `?${f}`))
for (const p of wanted) if (!toured.has(p)) problems.push(`a page shows the recording "${p}" but no tour has page: '${p}'`)
for (const p of toured) if (!wanted.has(p)) problems.push(`tour "${p}" is shown on no page`)

if (problems.length) {
  console.error(`docs coverage:\n- ${problems.join('\n- ')}`)
  process.exit(1)
}
console.log(`docs coverage: ${Object.keys(outline.routes).length} app routes documented, ${toured.size} tours, each on a page`)

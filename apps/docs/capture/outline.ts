/**
 * Captures outline.json: for every page in the app's menu (apps/frontend/src/astryx/nav.ts), its title, headings,
 * sections, controls, tables, empty states and the API calls it makes, read from the running demo. <PageAnatomy>
 * shows it and scripts/coverage.ts checks every route has a doc page.
 *
 *   npm run outline        # FAIRMIND_APP_URL, the live app by default
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright-core'
import { APP, CHROME, demoContext } from './run'

const DOCS = fileURLToPath(new URL('..', import.meta.url))

// Every page in the menu, read from its source as text (importing it would pull in the app's icon library).
const MENU = [...new Set([...readFileSync(join(DOCS, '../frontend/src/astryx/nav.ts'), 'utf8').matchAll(/href: '(\/[^']*)'/g)].map(m => m[1]!))]

/** The route key a doc page names in <PageAnatomy route="…" />: the path without its slash. */
export const routeKey = (path: string): string => path.replace(/^\//, '').replace(/\//g, '.') || 'home'

// Record ids in API paths: UUIDs, long hex and numbers.
const ID = /\/(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{16,}|\d+)(?=\/|$)/gi

// Runs in the page. Plain JavaScript text: a function passed from here would be rewritten by the TypeScript loader
// with helpers the page does not have.
const READ = `(() => {
  const main = document.querySelector('main') || document.body
  const name = el => (el.getAttribute('aria-label') || el.innerText || el.getAttribute('title') || '').replace(/\\s+/g, ' ').trim()
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  const uniq = xs => [...new Set(xs.filter(Boolean))]
  const headings = uniq([...main.querySelectorAll('h1, h2, h3')].filter(visible).map(h => h.tagName.toLowerCase() + ': ' + name(h)))
  const labelled = [...main.querySelectorAll('section[aria-label], [role=region][aria-label], section[aria-labelledby]')]
    .map(el => el.getAttribute('aria-label') || (document.getElementById(el.getAttribute('aria-labelledby')) || {}).innerText)
  const regions = uniq(labelled.length ? labelled : headings.filter(h => h.startsWith('h2: ')).map(h => h.slice(4)))
  const kind = el => el.getAttribute('role') || (el.tagName === 'BUTTON' ? 'button' : el.tagName === 'SELECT' ? 'combobox'
    : el.type === 'checkbox' ? 'checkbox' : el.type === 'search' ? 'searchbox' : 'textbox')
  const fieldName = el => el.getAttribute('aria-label') || (el.labels && el.labels[0] && el.labels[0].innerText) || el.placeholder || ''
  const controls = uniq([...main.querySelectorAll('button, [role=button], [role=tab], [role=switch], select, input:not([type=hidden]), textarea')]
    .filter(visible).map(el => { const n = /INPUT|SELECT|TEXTAREA/.test(el.tagName) ? fieldName(el) : name(el); return n && n.length < 60 ? kind(el) + ': ' + n.trim() : '' }))
  const tables = [...main.querySelectorAll('table, [role=table], [role=grid]')].filter(visible).map(t => ({
    name: t.getAttribute('aria-label') || (t.querySelector('caption') || {}).innerText || '',
    headers: uniq([...t.querySelectorAll('th, [role=columnheader]')].map(name)),
  }))
  const emptyStates = uniq([...main.querySelectorAll('[class*="empty" i], [data-empty]')].filter(visible)
    .map(el => (el.querySelector('h1, h2, h3, h4, strong') || el).innerText.replace(/\\s+/g, ' ').trim()).filter(t => t && t.length < 120))
  return { title: document.title.split(' · ')[0].split(' | ')[0], headings, regions, controls, tables, emptyStates }
})()`

async function main(): Promise<void> {
  if (!CHROME) throw new Error('Chrome not found: set FAIRMIND_BROWSER_EXECUTABLE')
  const browser = await chromium.launch({ executablePath: CHROME })
  const routes: Record<string, unknown> = {}
  try {
    const context = await demoContext(browser)
    const page = await context.newPage()
    let calls: string[] = []
    // The organisation's own record names (systems, policies, frameworks…) are data, not the page: collected from the
    // API's answers and removed from the outline, so it describes what any organisation sees.
    const names = new Set<string>()
    const collect = (v: unknown): void => {
      if (Array.isArray(v)) v.forEach(collect)
      else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) {
        if ((k === 'name' || k === 'title' || k === 'system_name') && typeof x === 'string' && x.length > 2) names.add(x.trim())
        else collect(x)
      }
    }
    page.on('response', async r => {
      if (r.request().resourceType() !== 'fetch' || !r.url().includes('/api/')) return
      try { collect(await r.json()) } catch { /* not JSON */ }
    })
    page.on('request', r => {
      const u = new URL(r.url())
      const path = u.pathname.replace(/^\/api\/proxy/, '')
      if (path.startsWith('/api/') && r.resourceType() === 'fetch') calls.push(`${r.method()} ${path.replace(ID, '/{id}')}`)
    })
    const visit = async (path: string) => {
      calls = []
      await page.goto(`${APP}${path}`)
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined)
      await page.waitForTimeout(800)
      const read = await page.evaluate(READ) as Record<string, any>
      const isData = (t: string): boolean => [...names].some(n => t.includes(n))
      const plain = (xs: string[]) => [...new Set(xs.filter(x => !isData(x)).map(x => x.replace(/^([a-z0-9]+: )?(.*)$/, (_m, k = '', t) => k + t.replace(/\d+/g, 'N'))))]
      routes[routeKey(path)] = {
        path, title: read.title, headings: plain(read.headings), regions: plain(read.regions), controls: plain(read.controls),
        tables: read.tables.map((t: { name: string; headers: string[] }) => ({ name: isData(t.name) ? '' : t.name, headers: plain(t.headers) })),
        emptyStates: plain(read.emptyStates), requests: [...new Set(calls)].sort(),
      }
      console.log(`  ${path}`)
    }
    for (const href of MENU) await visit(href)
    // One system's file, opened from the board on Home, stands for every /systems/{id} page.
    await page.goto(`${APP}/dashboard`)
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined)
    const href = await page.locator('main a[href^="/systems/"]').first().getAttribute('href', { timeout: 10_000 })
    if (href) { await visit(href); routes['systems.file'] = { ...(routes[routeKey(href)] as object), path: '/systems/{id}', title: 'System file' }; delete routes[routeKey(href)] }
  } finally {
    await browser.close()
  }
  writeFileSync(join(DOCS, 'outline.json'), `${JSON.stringify({ app: APP, routes }, null, 2)}\n`)
  console.log(`outline.json: ${Object.keys(routes).length} routes`)
}

await main()

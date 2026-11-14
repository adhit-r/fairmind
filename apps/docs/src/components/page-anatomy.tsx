import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { ReactNode } from 'react'

/**
 * What an app page holds, read from outline.json, which `npm run outline` captures from the running app on the demo
 * organisation, so it cannot drift from the product.
 */
interface Route { route: string; path: string; title: string; headings: string[]; regions: string[]; controls: string[]; tables: { name: string; headers: string[] }[]; emptyStates: string[]; requests: string[] }

const outline = JSON.parse(readFileSync(join(process.cwd(), 'outline.json'), 'utf8')) as { routes: Record<string, Omit<Route, 'route'>> }
const routes: Route[] = Object.entries(outline.routes).map(([route, r]) => ({ route, ...r }))

// The menu, search and sign-out appear on every page; a page's own parts are the rest.
const common = (pick: (r: Route) => string[]): Set<string> => {
  const counts = new Map<string, number>()
  for (const r of routes) for (const c of new Set(pick(r))) counts.set(c, (counts.get(c) ?? 0) + 1)
  return new Set([...counts].filter(([, n]) => n > routes.length * 0.4).map(([c]) => c))
}
const COMMON_CONTROLS = common(r => r.controls)
const COMMON_REQUESTS = common(r => r.requests)
const COMMON_REGIONS = common(r => r.regions)

export function PageAnatomy({ route }: { route: string }) {
  const r = routes.find(x => x.route === route)
  if (!r) throw new Error(`no route "${route}" in outline.json: run npm run outline`)
  const regions = r.regions.filter(x => !COMMON_REGIONS.has(x))
  const controls = r.controls.filter(c => !COMMON_CONTROLS.has(c)).slice(0, 30)
  const requests = r.requests.filter(q => !COMMON_REQUESTS.has(q))
  const heading = r.headings.find(h => h.startsWith('h1: '))?.slice(4) ?? r.title

  const row = (label: string, value: ReactNode) => (
    <tr><th scope="row">{label}</th><td>{value}</td></tr>
  )
  return (
    <table className="fm-anatomy not-prose">
      <tbody>
        {row('Address', <span className="mono">{r.path}</span>)}
        {row('Page title', heading)}
        {regions.length > 0 && row('Sections', regions.join(' · '))}
        {r.tables.map(t => row(t.name ? `Table: ${t.name}` : 'Table columns', t.headers.join(' · ')))}
        {controls.length > 0 && row('Controls', controls.map(c => c.replace(/^[a-z]+: /, '')).join(' · '))}
        {r.emptyStates.length > 0 && row('When there is nothing yet', r.emptyStates.join(' '))}
        {requests.length > 0 && row('API it calls', <span className="mono api">{requests.map(q => <span key={q}>{q}</span>)}</span>)}
      </tbody>
    </table>
  )
}

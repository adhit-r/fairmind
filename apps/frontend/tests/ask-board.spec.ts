import { expect, test, type Page, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

const provider = {
  config: { provider: 'anthropic', providerName: 'Anthropic', model: 'test-model', hasKey: true, keyHint: null, keyReadable: true, enabled: true, testedOk: true, testedAt: null, testMessage: null, updatedAt: '2026-11-26T10:00:00Z' },
}

type Pinned = { id: string; question: string; board: string; createdAt: string }

/** Answers the ask route with the given board; everything else comes from the shared grid fixtures. */
/** One system's own file: the system record and its run history, newest dates last on purpose to prove the widgets sort. */
async function withSystemFile(page: Page) {
  const path = (route: Route) => new URL(route.request().url()).pathname.replace('/api/proxy', '')
  await page.route(/\/api\/v1\/(ai-governance\/systems\/(sys-a|ghost)(\/[a-z-]+)?|packs\/systems\/sys-a\/evaluation-runs)(\?|$)/, (route) => {
    const p = path(route)
    if (p.endsWith('/ghost')) return route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Not found' }) })
    if (p.endsWith('/systems/sys-a')) return json(route, { id: 'sys-a', workspaceId: 'ws-1', name: 'Grid system A', owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: {} })
    if (p.endsWith('/fairness-runs')) {
      return json(route, [
        { evidenceId: 'f1', title: 'Fairness run, May', rows: 900, allChecksPass: true, attributes: [{ attribute: 'gender', disparateImpactRatio: 0.91, checks: { di: true }, passedOnSignificance: [] }], confidence: 0.9, createdAt: '2026-11-01T10:00:00Z' },
        { evidenceId: 'f2', title: 'Fairness run, Nov', rows: 950, allChecksPass: false, attributes: [{ attribute: 'gender', disparateImpactRatio: 0.78, checks: { di: false }, passedOnSignificance: [] }], confidence: 0.9, createdAt: '2026-11-20T10:00:00Z' },
      ])
    }
    if (p.endsWith('/evaluation-runs')) {
      return json(route, [
        { id: 'e1', evaluationId: 'EV-DAT-01', systemId: 'sys-a', systemName: 'Grid system A', status: 'passed', summary: 'Data checks passed', metrics: {}, files: {}, source: 'upload', createdAt: '2026-11-05T10:00:00Z', createdBy: null },
        { id: 'e2', evaluationId: 'EV-DAT-01', systemId: 'sys-a', systemName: 'Grid system A', status: 'failed', summary: 'Two columns drifted', metrics: {}, files: {}, source: 'upload', createdAt: '2026-11-22T10:00:00Z', createdBy: null },
      ])
    }
    if (p.endsWith('/seals')) return json(route, [{ id: 's1', requestId: 'r1', decision: 'approved', chainHead: 'h', evidenceCount: 3, gate: {}, sealedBy: 'owner-a', createdAt: '2026-11-25T10:00:00Z', verification: { status: 'intact', changed: [], missing: [], addedSince: 0 } }])
    return json(route, [])
  })
}

async function asking(page: Page, board: string, pinned: Pinned[] = [], more?: (page: Page) => Promise<void>) {
  await installGridFixtures(page)
  await more?.(page) // later routes win, so extra fixtures go after the shared ones
  // The pinned-boards route keeps its list in this array, as the server keeps it in saved_boards.
  await page.route(/\/api\/v1\/packs\/boards(\/|\?|$)/, async (route) => {
    const req = route.request()
    if (req.method() === 'POST') {
      const body = req.postDataJSON() as { question: string; board: string }
      const row = { id: `b${pinned.length + 1}`, ...body, createdAt: '2026-11-26T10:00:00Z' }
      pinned.unshift(row)
      return json(route, row)
    }
    if (req.method() === 'DELETE') {
      const id = new URL(req.url()).pathname.split('/').pop()
      pinned.splice(0, pinned.length, ...pinned.filter((b) => b.id !== id))
      return json(route, { deleted: id })
    }
    return json(route, { boards: pinned })
  })
  await page.route(/\/api\/v1\/packs\/ai-provider(\?|$)/, (route) => json(route, provider))
  await page.route(/\/api\/v1\/packs\/ask(\?|$)/, (route) =>
    json(route, { answer: 'Two systems need attention.', board, systems: [], provider: 'Anthropic', model: 'test-model', systemsRead: 2, runsRead: 0 }),
  )
  await page.goto('/ask')
  await page.getByRole('textbox').fill('Which systems fail?')
  await page.keyboard.press('Enter')
  await expect(page.getByText('Two systems need attention.')).toBeVisible({ timeout: 30_000 })
}

test.describe('Ask FairMind board', () => {
  test('draws the release matrix from the fixtures, not from the model', async ({ page }) => {
    await asking(page, 'root = Board([m])\nm = ReleaseMatrix("all")')
    const board = page.getByRole('region', { name: 'Release checks' })
    await expect(board).toBeVisible()
    await expect(board.getByRole('link', { name: 'Grid system A' })).toHaveAttribute('href', '/systems/sys-a')
    await expect(board.getByRole('link', { name: 'Grid system B' })).toBeVisible()
    await expect(board.getByRole('button')).toHaveCount(0) // links only: deciding happens on the system's own page
  })

  test('a board that does not validate draws nothing and the answer stands alone', async ({ page }) => {
    await asking(page, 'root = Board([m])\nm = Chart("revenue")')
    await expect(page.getByRole('region', { name: 'Release checks' })).toHaveCount(0)
    await expect(page.getByText('Two systems need attention.')).toBeVisible()
  })

  test('an empty board is just the answer', async ({ page }) => {
    await asking(page, '')
    await expect(page.getByRole('region', { name: 'Release checks' })).toHaveCount(0)
  })

  test('framework readiness draws a bar per followed framework from the estate', async ({ page }) => {
    await asking(page, 'root = Board([f])\nf = FrameworkReadiness("all")')
    const board = page.getByRole('region', { name: 'Framework readiness' })
    await expect(board.getByRole('link', { name: 'ISO/IEC 42001:2023' })).toHaveAttribute('href', /\/frameworks\//)
    await expect(board.getByRole('img', { name: /met, .* in progress/ })).toBeVisible()
  })

  test('a pinned board shows on Home, drawn live, and can be unpinned', async ({ page }) => {
    const board = 'root = Board([m])\nm = ReleaseMatrix("all")'
    await asking(page, board)
    await page.getByRole('button', { name: 'Pin to Home' }).click()
    await expect(page.getByRole('button', { name: 'Pinned to Home' })).toBeDisabled()

    await page.goto('/dashboard')
    const pinnedBoard = page.getByRole('region', { name: 'Pinned: Which systems fail?' })
    await expect(pinnedBoard.getByRole('link', { name: 'Grid system A' })).toBeVisible({ timeout: 30_000 })
    await pinnedBoard.getByRole('button', { name: 'Unpin' }).click()
    await expect(pinnedBoard).toHaveCount(0)
  })

  test('Pin to Home is not offered for a board that does not validate', async ({ page }) => {
    await asking(page, 'root = Board([m])\nm = Chart("revenue")')
    await expect(page.getByRole('button', { name: 'Pin to Home' })).toHaveCount(0)
  })

  test('eval comparison sets the latest run against the one before, per measure', async ({ page }) => {
    await asking(page, 'root = Board([c])\nc = EvalCompare("sys-a")', [], withSystemFile)
    const board = page.getByRole('region', { name: 'Latest run against the one before' })
    const fairness = board.getByRole('row', { name: /Fairness, gender/ })
    await expect(fairness).toContainText('0.91')
    await expect(fairness).toContainText('0.78')
    await expect(fairness).toContainText('Failed')
    const evaluation = board.getByRole('row', { name: /EV-DAT-01/ })
    await expect(evaluation).toContainText('Passed')
    await expect(evaluation).toContainText('Failed')
  })

  test('the timeline lists a system\'s history newest first', async ({ page }) => {
    await asking(page, 'root = Board([t])\nt = SystemTimeline("sys-a")', [], withSystemFile)
    const items = page.getByRole('region', { name: 'System history' }).getByRole('listitem')
    await expect(items.first()).toContainText('Release decision: approved')
    await expect(items.nth(1)).toContainText('EV-DAT-01: failed')
    await expect(items.last()).toContainText('Fairness run: passed')
  })

  test('a system id that is not found draws a plain note, not data', async ({ page }) => {
    await asking(page, 'root = Board([t])\nt = SystemTimeline("ghost")', [], withSystemFile)
    await expect(page.getByText(/That system could not be loaded/)).toBeVisible()
    await expect(page.getByRole('region', { name: 'System history' })).toHaveCount(0)
  })
})

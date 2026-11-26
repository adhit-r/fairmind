import { expect, test, type Page, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

const provider = {
  config: { provider: 'anthropic', providerName: 'Anthropic', model: 'test-model', hasKey: true, keyHint: null, keyReadable: true, enabled: true, testedOk: true, testedAt: null, testMessage: null, updatedAt: '2026-11-26T10:00:00Z' },
}

type Pinned = { id: string; question: string; board: string; createdAt: string }

/** Answers the ask route with the given board; everything else comes from the shared grid fixtures. */
async function asking(page: Page, board: string, pinned: Pinned[] = []) {
  await installGridFixtures(page)
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
})

import { expect, test } from '@playwright/test'
import { installGridFixtures, layoutFacts } from './grid-fixtures'

const cellsOf = (page: import('@playwright/test').Page) => page.locator('table button.cell')

test.describe('Home board', () => {
  test.beforeEach(async ({ page }) => installGridFixtures(page))

  test('renders one row per system with derived cell states', async ({ page }) => {
    await page.goto('/dashboard')
    const board = page.getByRole('region', { name: 'Every system against every release check' })
    await expect(board).toBeVisible({ timeout: 30_000 })
    await expect(board.getByRole('link', { name: /Grid system A/ })).toBeVisible()
    await expect(board.getByRole('link', { name: /Grid system B/ })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Fairness on Grid system A: Fails' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Monitoring on Grid system A: Out of date' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Data governance on Grid system A: Attested' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Human oversight on Grid system A: Estimated' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Environment on Grid system A: Nothing on file' })).toBeVisible()
    // Six columns (five checks and the decision) for each of the two systems.
    await expect(cellsOf(page)).toHaveCount(12)
  })

  test('a cell is focusable and Enter opens its drawer', async ({ page }) => {
    await page.goto('/dashboard')
    const cell = page.getByRole('button', { name: 'Fairness on Grid system A: Fails' })
    await expect(cell).toBeVisible({ timeout: 30_000 })
    await cell.focus()
    await page.keyboard.press('Enter')
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('link', { name: 'Open the system file' })).toHaveAttribute('href', '/systems/sys-a')
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/dashboard')
    await expect(cellsOf(page).first()).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})

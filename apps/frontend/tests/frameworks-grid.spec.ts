import { expect, test } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts, ONE_PER_TIER } from './grid-fixtures'

test.describe('Frameworks grid', () => {
  test.beforeEach(async ({ page }) => installGridFixtures(page))

  test('/frameworks lists the frameworks and links to each grid', async ({ page }) => {
    await page.goto('/frameworks')
    await expect(page).toHaveURL(/\/frameworks$/)
    const table = page.getByRole('region', { name: 'Frameworks' })
    await expect(table.getByRole('link', { name: 'ISO/IEC 42001:2023' })).toHaveAttribute('href', `/frameworks/${GRID_FW}`, { timeout: 30_000 })
  })

  test('by system renders one grid, one legend, at most three cards', async ({ page }) => {
    await page.goto(`/frameworks/${GRID_FW}`)
    const grid = page.locator('[data-mx="fwsys"]')
    await expect(grid).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('heading', { level: 1 })).toContainText('requirement')
    await expect(grid.getByRole('link', { name: 'Grid system A' })).toBeVisible()
    await expect(grid.getByText('Interested parties')).toHaveCount(0)
    await page.getByRole('button', { name: /Show all/ }).click()
    await expect(grid.getByText('Interested parties')).toBeVisible()
    const facts = await layoutFacts(page)
    expect(facts.cards).toBeLessThanOrEqual(3)
    expect(facts.legends).toBe(1)
  })

  test('a cell is focusable and Enter opens its drawer', async ({ page }) => {
    await page.goto(`/frameworks/${GRID_FW}`)
    const cell = page.locator('[data-mx="fwsys"] button.fm-cel').first()
    await expect(cell).toBeVisible({ timeout: 30_000 })
    await cell.focus()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  test('by control shows the crosswalk relation', async ({ page }) => {
    await page.goto(`/frameworks/${GRID_FW}?view=controls`)
    const grid = page.locator('[data-mx="fwctl"]')
    await expect(grid.locator('tbody .fm-cel.r3')).toHaveCount(1, { timeout: 30_000 })
    expect((await layoutFacts(page)).legends).toBe(1)
  })

  test('adjacent one-system tiers keep their group labels apart', async ({ page }) => {
    await page.unrouteAll({ behavior: 'ignoreErrors' })
    await installGridFixtures(page, ONE_PER_TIER)
    await page.goto(`/frameworks/${GRID_FW}`)
    const grid = page.locator('[data-mx="fwsys"]')
    await expect(grid.getByRole('link', { name: 'Grid system D' })).toBeVisible({ timeout: 30_000 })
    const rects = await grid.locator('.mx-gl span').evaluateAll((els) =>
      els.map((el) => {
        const r = document.createRange()
        r.selectNodeContents(el)
        const b = r.getBoundingClientRect()
        return { text: el.textContent, left: b.left, right: b.right, top: b.top, bottom: b.bottom }
      }),
    )
    expect(rects.map((r) => r.text)).toEqual(['Org', 'Critical', 'High', 'Medium'])
    for (let i = 1; i < rects.length; i++) {
      const a = rects[i - 1]
      const b = rects[i]
      expect(a.right <= b.left + 0.5 || a.bottom <= b.top + 0.5 || b.bottom <= a.top + 0.5, `${a.text} and ${b.text} overlap`).toBe(true)
    }
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(`/frameworks/${GRID_FW}`)
    await expect(page.locator('[data-mx="fwsys"]')).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})

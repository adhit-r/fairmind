import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should navigate to all main pages', async ({ page }) => {
    const pages = [
      { path: '/dashboard', name: 'Dashboard' },
      { path: '/models', name: 'Models' },
      { path: '/datasets', name: 'Datasets' },
      { path: '/bias', name: 'Bias Detection' },
      { path: '/monitoring', name: 'Monitoring' },
      { path: '/analytics', name: 'Analytics' },
      { path: '/compliance', name: 'Compliance' },
      { path: '/ai-bom', name: 'AI BOM' },
      { path: '/status', name: 'Status' },
    ]

    for (const { path, name } of pages) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      
      // Check for heading or page content
      const heading = page.getByRole('heading', { name: new RegExp(name, 'i') })
      const hasHeading = await heading.count()
      
      // Should load without errors
      expect(page.url()).toContain(path)
      
      // Should have some content
      const hasContent = await page.locator('body').textContent()
      expect(hasContent?.length || 0).toBeGreaterThan(100)
    }
  })

  test('should have sidebar navigation', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    // Check for sidebar or navigation
    const sidebar = page.locator('[data-sidebar], [class*="Sidebar"], nav, aside').first()
    const hasSidebar = await sidebar.count()
    
    // Should have navigation
    expect(hasSidebar > 0).toBeTruthy()
  })

  test('should navigate via sidebar links', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2000)
    
    // Try to find and click a navigation link
    const navLinks = page.locator('a[href*="/models"], a[href*="/bias"], button[aria-label*="models"]')
    const linkCount = await navLinks.count()
    
    if (linkCount > 0) {
      await navLinks.first().click()
      await page.waitForTimeout(1000)
      
      // URL should change
      const url = page.url()
      expect(url).not.toContain('/dashboard')
    }
  })
})


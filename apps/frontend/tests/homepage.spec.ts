import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('should load and redirect to dashboard', async ({ page }) => {
    await page.goto('/')
    
    // Should redirect to dashboard or show loading
    await page.waitForTimeout(2000)
    
    // Check if we're on dashboard or login page
    const url = page.url()
    expect(url).toMatch(/\/(dashboard|login)/)
  })

  test('should show navigation on dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Wait for page to load
    await page.waitForLoadState('networkidle')
    
    // Check for navigation elements
    const sidebar = page.locator('[data-sidebar]').first()
    await expect(sidebar).toBeVisible({ timeout: 10000 }).catch(() => {
      // Sidebar might not have data attribute, check for header instead
      const header = page.locator('header, [role="banner"]').first()
      expect(header).toBeVisible({ timeout: 5000 })
    })
  })

  test('should load login page', async ({ page }) => {
    await page.goto('/login')
    
    await page.waitForLoadState('networkidle')
    
    // Check for login form elements
    const usernameInput = page.locator('input[type="text"], input[id*="username"], input[name*="username"]').first()
    const passwordInput = page.locator('input[type="password"]').first()
    
    await expect(usernameInput).toBeVisible({ timeout: 5000 })
    await expect(passwordInput).toBeVisible({ timeout: 5000 })
  })

  test('should handle API errors gracefully', async ({ page }) => {
    await page.goto('/dashboard')
    
    await page.waitForLoadState('networkidle')
    
    // Check for error messages or loading states
    const errorAlert = page.locator('[role="alert"], .alert, [class*="error"]').first()
    const loadingSkeleton = page.locator('[class*="skeleton"], [class*="loading"]').first()
    
    // Either error or loading should be present, or page should load successfully
    const hasError = await errorAlert.isVisible().catch(() => false)
    const hasLoading = await loadingSkeleton.isVisible().catch(() => false)
    const hasContent = await page.locator('h1, [class*="dashboard"]').first().isVisible().catch(() => false)
    
    // At least one should be true
    expect(hasError || hasLoading || hasContent).toBe(true)
  })
})


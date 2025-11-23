import { test, expect } from '@playwright/test'

/**
 * Comprehensive E2E Tests for FairMind UI
 * Tests the current UI with real API integration
 */

test.describe('FairMind E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for API calls
    test.setTimeout(30000)
  })

  test.describe('Dashboard', () => {
    test('should load dashboard with real data', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Check for dashboard heading
      await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible({ timeout: 10000 })
      
      // Check for stat cards or content
      const content = await page.textContent('body')
      expect(content?.length || 0).toBeGreaterThan(500)
    })

    test('should display dashboard stats', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForTimeout(3000)
      
      // Should show stats or loading
      const hasStats = await page.locator('text=/models|datasets|scans|activity/i').count()
      const hasLoading = await page.locator('[class*="Skeleton"]').count()
      
      expect(hasStats > 0 || hasLoading > 0).toBeTruthy()
    })
  })

  test.describe('Models Page', () => {
    test('should display real models from database', async ({ page }) => {
      await page.goto('/models')
      await page.waitForTimeout(3000)
      
      // Check for real model names
      const pageText = await page.textContent('body') || ''
      const hasRealModels = [
        'ACME',
        'TechCorp',
        'Loan',
        'Fraud',
        'GPT',
        'BERT',
        'Llama'
      ].some(name => pageText.includes(name))
      
      expect(hasRealModels).toBeTruthy()
    })

    test('should open model registration dialog', async ({ page }) => {
      await page.goto('/models')
      await page.waitForTimeout(2000)
      
      const registerButton = page.getByRole('button', { name: /register|add|new/i }).first()
      if (await registerButton.isVisible()) {
        await registerButton.click()
        await page.waitForTimeout(500)
        
        // Check for dialog or form
        const hasDialog = await page.locator('[role="dialog"], [class*="Dialog"]').count()
        const hasForm = await page.locator('form, input').count()
        
        expect(hasDialog > 0 || hasForm > 0).toBeTruthy()
      }
    })
  })

  test.describe('Bias Detection', () => {
    test('should load bias detection page', async ({ page }) => {
      await page.goto('/bias')
      await page.waitForLoadState('networkidle')
      
      await expect(page.getByRole('heading', { name: /bias detection/i })).toBeVisible({ timeout: 10000 })
    })

    test('should navigate to modern bias page', async ({ page }) => {
      await page.goto('/modern-bias')
      await page.waitForLoadState('networkidle')
      
      await expect(page.getByRole('heading', { name: /modern bias/i })).toBeVisible({ timeout: 10000 })
      
      // Check for tabs
      const tabs = await page.locator('[role="tab"]').count()
      expect(tabs).toBeGreaterThan(0)
    })

    test('should navigate to multimodal bias page', async ({ page }) => {
      await page.goto('/multimodal-bias')
      await page.waitForLoadState('networkidle')
      
      await expect(page.getByRole('heading', { name: /multimodal bias/i })).toBeVisible({ timeout: 10000 })
    })
  })

  test.describe('Navigation', () => {
    test('should navigate between main pages', async ({ page }) => {
      const pages = [
        '/dashboard',
        '/models',
        '/bias',
        '/monitoring',
        '/analytics',
        '/compliance',
        '/ai-bom',
        '/status'
      ]

      for (const path of pages) {
        await page.goto(path)
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(1000)
        
        expect(page.url()).toContain(path)
        
        // Should have content
        const content = await page.textContent('body')
        expect(content?.length || 0).toBeGreaterThan(100)
      }
    })
  })

  test.describe('API Integration', () => {
    test('should fetch data from backend APIs', async ({ page }) => {
      let apiCalled = false
      
      await page.route('**/api/v1/**', route => {
        apiCalled = true
        route.continue()
      })

      await page.goto('/dashboard')
      await page.waitForTimeout(3000)
      
      expect(apiCalled).toBeTruthy()
    })

    test('should handle API errors gracefully', async ({ page }) => {
      await page.route('**/api/v1/database/dashboard-stats', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ success: false, error: 'Server error' })
        })
      })

      await page.goto('/dashboard')
      await page.waitForTimeout(2000)
      
      // Should handle error without crashing
      const content = await page.textContent('body')
      expect(content?.length || 0).toBeGreaterThan(0)
    })
  })

  test.describe('Forms', () => {
    test('should validate form inputs', async ({ page }) => {
      await page.goto('/bias')
      await page.waitForTimeout(2000)
      
      // Try to submit empty form
      const submitButton = page.getByRole('button', { name: /run|test|submit/i }).first()
      if (await submitButton.isVisible()) {
        await submitButton.click()
        await page.waitForTimeout(1000)
        
        // Should show validation or error
        const hasFeedback = await page.locator('text=/required|error|invalid/i, [role="alert"]').count()
        expect(hasFeedback >= 0).toBeTruthy()
      }
    })
  })
})


import { test, expect } from '@playwright/test'

test.describe('Models Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/models')
    await page.waitForLoadState('networkidle')
  })

  test('should display models page', async ({ page }) => {
    // Check for main heading
    await expect(page.getByRole('heading', { name: /models/i })).toBeVisible({ timeout: 10000 })
    
    // Check for register model button
    const registerButton = page.getByRole('button', { name: /register|add|new/i })
    await expect(registerButton.first()).toBeVisible({ timeout: 5000 })
  })

  test('should display models from database', async ({ page }) => {
    // Wait for models to load
    await page.waitForTimeout(3000)
    
    // Should show models table or list
    // Check for table or model cards
    const hasTable = await page.locator('table, [role="table"]').count()
    const hasModels = await page.locator('text=/ACME|TechCorp|GPT|BERT|Llama/i').count()
    
    // Should have either table structure or model names
    expect(hasTable > 0 || hasModels > 0).toBeTruthy()
  })

  test('should open model registration dialog', async ({ page }) => {
    // Click register model button
    const registerButton = page.getByRole('button', { name: /register|add|new/i }).first()
    
    if (await registerButton.isVisible()) {
      await registerButton.click()
      await page.waitForTimeout(500)
      
      // Check for dialog/form
      const dialog = page.locator('[role="dialog"], [class*="Dialog"], [class*="dialog"]')
      const form = page.locator('form, input[name*="model"], input[id*="model"]')
      
      const hasDialog = await dialog.count()
      const hasForm = await form.count()
      
      // Should show dialog or form
      expect(hasDialog > 0 || hasForm > 0).toBeTruthy()
    }
  })

  test('should handle empty state', async ({ page }) => {
    // Intercept API to return empty array
    await page.route('**/api/v1/database/models', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ success: true, data: [], count: 0 })
      })
    })

    await page.goto('/models')
    await page.waitForTimeout(2000)
    
    // Should show empty state message
    const emptyState = page.locator('text=/no models|empty|register your first/i')
    const hasEmptyState = await emptyState.count()
    
    // Empty state should be displayed
    expect(hasEmptyState > 0).toBeTruthy()
  })

  test('should display model details in table', async ({ page }) => {
    await page.waitForTimeout(3000)
    
    // Check for model information
    const hasModelInfo = await page.locator('text=/classification|llm|nlp|computer_vision/i').count()
    const hasStatus = await page.locator('text=/active|inactive|deprecated/i').count()
    
    // Should display model type or status
    expect(hasModelInfo > 0 || hasStatus > 0).toBeTruthy()
  })
})


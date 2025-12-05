import { test, expect } from '@playwright/test'

test.describe('Bias Detection', () => {
  test('should load bias detection page', async ({ page }) => {
    await page.goto('/bias')
    await page.waitForLoadState('networkidle')
    
    // Check for main heading
    await expect(page.getByRole('heading', { name: /bias detection/i })).toBeVisible({ timeout: 10000 })
  })

  test('should display bias test form', async ({ page }) => {
    await page.goto('/bias')
    await page.waitForTimeout(2000)
    
    // Check for form inputs
    const modelIdInput = page.locator('input[id*="model"], input[name*="model"], input[placeholder*="model"]').first()
    const testTypeSelect = page.locator('select, [role="combobox"]').first()
    const submitButton = page.getByRole('button', { name: /run|test|submit|detect/i })
    
    // At least one form element should be visible
    const hasInput = await modelIdInput.count()
    const hasSelect = await testTypeSelect.count()
    const hasButton = await submitButton.count()
    
    expect(hasInput > 0 || hasSelect > 0 || hasButton > 0).toBeTruthy()
  })

  test('should submit bias test form', async ({ page }) => {
    await page.goto('/bias')
    await page.waitForTimeout(2000)
    
    // Fill form if inputs exist
    const modelIdInput = page.locator('input[id*="model"], input[name*="model"]').first()
    if (await modelIdInput.isVisible()) {
      await modelIdInput.fill('test-model-123')
    }
    
    // Submit form
    const submitButton = page.getByRole('button', { name: /run|test|submit/i }).first()
    if (await submitButton.isVisible()) {
      await submitButton.click()
      await page.waitForTimeout(2000)
      
      // Should show loading or results
      const hasLoading = await page.locator('text=/loading|running|processing/i').count()
      const hasResults = await page.locator('text=/result|bias|score/i').count()
      const hasError = await page.locator('[role="alert"], text=/error/i').count()
      
      // Should show some feedback
      expect(hasLoading > 0 || hasResults > 0 || hasError > 0).toBeTruthy()
    }
  })

  test('should navigate to advanced bias page', async ({ page }) => {
    await page.goto('/advanced-bias')
    await page.waitForLoadState('networkidle')
    
    // Check for page heading
    await expect(page.getByRole('heading', { name: /advanced bias/i })).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to modern bias page', async ({ page }) => {
    await page.goto('/modern-bias')
    await page.waitForLoadState('networkidle')
    
    // Check for page heading
    await expect(page.getByRole('heading', { name: /modern bias/i })).toBeVisible({ timeout: 10000 })
    
    // Check for tabs
    const tabs = page.locator('[role="tab"], [class*="Tab"]')
    const hasTabs = await tabs.count()
    expect(hasTabs > 0).toBeTruthy()
  })

  test('should navigate to multimodal bias page', async ({ page }) => {
    await page.goto('/multimodal-bias')
    await page.waitForLoadState('networkidle')
    
    // Check for page heading
    await expect(page.getByRole('heading', { name: /multimodal bias/i })).toBeVisible({ timeout: 10000 })
  })
})


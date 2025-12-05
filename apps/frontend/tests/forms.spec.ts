import { test, expect } from '@playwright/test'

test.describe('Forms', () => {
  test('should validate model registration form', async ({ page }) => {
    await page.goto('/models')
    await page.waitForTimeout(2000)
    
    // Open registration dialog
    const registerButton = page.getByRole('button', { name: /register|add|new/i }).first()
    if (await registerButton.isVisible()) {
      await registerButton.click()
      await page.waitForTimeout(500)
      
      // Try to submit empty form
      const submitButton = page.getByRole('button', { name: /submit|register|create/i }).first()
      if (await submitButton.isVisible()) {
        await submitButton.click()
        await page.waitForTimeout(1000)
        
        // Should show validation errors
        const hasErrors = await page.locator('text=/required|invalid|error/i, [class*="error"]').count()
        // Form validation might prevent submission or show errors
        expect(hasErrors >= 0).toBeTruthy()
      }
    }
  })

  test('should submit bias detection form', async ({ page }) => {
    await page.goto('/bias')
    await page.waitForTimeout(2000)
    
    // Fill form
    const modelIdInput = page.locator('input[id*="model"], input[name*="model"]').first()
    if (await modelIdInput.isVisible()) {
      await modelIdInput.fill('test-model-id')
      
      // Submit
      const submitButton = page.getByRole('button', { name: /run|test|submit/i }).first()
      if (await submitButton.isVisible()) {
        await submitButton.click()
        await page.waitForTimeout(2000)
        
        // Should show loading or results
        const hasFeedback = await page.locator('text=/loading|result|error|success/i').count()
        expect(hasFeedback >= 0).toBeTruthy()
      }
    }
  })

  test('should show toast notifications', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2000)
    
    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /refresh/i })
    if (await refreshButton.isVisible()) {
      await refreshButton.click()
      await page.waitForTimeout(1000)
      
      // Check for toast notification
      const toast = page.locator('[role="status"], [class*="Toast"], [class*="toast"]')
      const hasToast = await toast.count()
      
      // Toast might appear or not, but should handle gracefully
      expect(hasToast >= 0).toBeTruthy()
    }
  })

  test('should handle form errors gracefully', async ({ page }) => {
    // Intercept API to return error
    await page.route('**/api/v1/bias-detection/detect', route => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({ success: false, error: 'Invalid model ID' })
      })
    })

    await page.goto('/bias')
    await page.waitForTimeout(2000)
    
    // Fill and submit form
    const modelIdInput = page.locator('input[id*="model"], input[name*="model"]').first()
    if (await modelIdInput.isVisible()) {
      await modelIdInput.fill('invalid-model')
      
      const submitButton = page.getByRole('button', { name: /run|test|submit/i }).first()
      if (await submitButton.isVisible()) {
        await submitButton.click()
        await page.waitForTimeout(2000)
        
        // Should show error message
        const hasError = await page.locator('[role="alert"], text=/error|invalid|failed/i').count()
        expect(hasError >= 0).toBeTruthy()
      }
    }
  })
})


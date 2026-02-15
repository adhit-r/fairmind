
import { test, expect } from '@playwright/test'

test.describe('User Guide Journey', () => {
    // Ensure we have a clean slate or logged in state if necessary
    // Assuming default state allows access or we can bypass login for now as per previous tests

    test('capture screenshots for user guide', async ({ page }) => {
        // Inject token before navigation
        await page.addInitScript(() => {
            localStorage.setItem('access_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiOWFiMzVhNS1hZDdiLTQ5NjMtYjAzNC02NGE0YjFhMTVjMTIiLCJyb2xlIjoiYWRtaW4iLCJlbWFpbCI6ImFkaGlAYXhvbm9tZS54eXoiLCJleHAiOjE3NjYwODA3Njl9.C6hXGPbDO2oGhPUhpLMssGRdiKYC0GvVvjlhwsniyUw')
        })

        // 0. Landing Page (Public)
        await page.goto('/')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(1000)
        await page.screenshot({ path: 'features_screenshots/0-Landing_Page.png', fullPage: true })

        // 1. Dashboard (Authenticated via Token)
        await page.goto('/dashboard')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(15000) // Increase to 15s for full chart/data load
        await page.screenshot({ path: 'features_screenshots/1-Dashboard.png', fullPage: true })

        // 2. Models Page
        await page.goto('/models')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(3000)
        await page.screenshot({ path: 'features_screenshots/2-Models_List.png', fullPage: true })

        // 3. Compliance Page
        await page.goto('/compliance')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(3000)
        await page.screenshot({ path: 'features_screenshots/3-Compliance.png', fullPage: true })

        // 4. Bias Analysis
        await page.goto('/bias')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(3000)
        await page.screenshot({ path: 'features_screenshots/4-Bias_Detection.png', fullPage: true })

        // 5. Settings / Profile
        await page.goto('/settings')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(3000)
        await page.screenshot({ path: 'features_screenshots/5-Settings.png', fullPage: true })
    })
})

import { test, expect } from '@playwright/test'

test('CORS preflight request should succeed', async ({ page }) => {
  // Navigate to the page
  await page.goto('http://localhost:1111/models')
  
  // Wait for network to settle
  await page.waitForLoadState('networkidle')
  
  // Check for CORS errors in console
  const errors: string[] = []
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text()
      if (text.includes('CORS') || text.includes('blocked')) {
        errors.push(text)
      }
    }
  })
  
  // Wait a bit for any async requests
  await page.waitForTimeout(2000)
  
  // Check if there are CORS errors
  const corsErrors = errors.filter(e => e.includes('CORS') || e.includes('blocked'))
  
  console.log('CORS Errors found:', corsErrors.length)
  if (corsErrors.length > 0) {
    console.log('Error details:', corsErrors)
  }
  
  // Test direct API call
  const response = await page.evaluate(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/database/models', {
        method: 'GET',
        headers: {
          'Origin': 'http://localhost:1111'
        }
      })
      return {
        status: res.status,
        headers: Object.fromEntries(res.headers.entries()),
        ok: res.ok
      }
    } catch (error: any) {
      return {
        error: error.message,
        status: 0
      }
    }
  })
  
  console.log('Direct API Response:', JSON.stringify(response, null, 2))
  
  // Check if response has CORS headers
  if (response.headers) {
    const hasOrigin = 'access-control-allow-origin' in response.headers
    console.log('Has Access-Control-Allow-Origin:', hasOrigin)
    console.log('CORS Headers:', Object.keys(response.headers).filter(k => k.toLowerCase().includes('access-control')))
  }
  
  // Take screenshot for debugging
  await page.screenshot({ path: 'cors-test.png', fullPage: true })
})

import { defineConfig, devices } from '@playwright/test'

const reviewedExternalLinkingEnabled =
  process.env.NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED === 'true'
const devPort = reviewedExternalLinkingEnabled ? 1112 : 1111
const baseURL = `http://localhost:${devPort}`

export default defineConfig({
  testDir: './tests',
  testMatch: /.*\.spec\.ts$/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: reviewedExternalLinkingEnabled ? 'bunx next dev -p 1112' : 'bun run dev',
    url: baseURL,
    reuseExistingServer: reviewedExternalLinkingEnabled ? false : !process.env.CI,
    timeout: 120 * 1000,
  },
})

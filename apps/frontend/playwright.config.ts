import { defineConfig, devices } from '@playwright/test'

// NEXT_PUBLIC_* flags are compiled into the client bundle, so a run with any flag on
// needs its own dev server on its own port; it must never reuse the default server.
// All dev servers share .next, so run the flagged suites one at a time.
const flag = (name: string) => process.env[name] === 'true'
const reviewedExternalLinkingEnabled = flag('NEXT_PUBLIC_ASSURANCE_UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_ENABLED')
const assuranceUiEnabled = flag('NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED')
const assuranceRunUiEnabled = flag('NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED')
const flaggedRun = reviewedExternalLinkingEnabled || assuranceUiEnabled || assuranceRunUiEnabled
const devPort = reviewedExternalLinkingEnabled ? 1112 : assuranceRunUiEnabled ? 1114 : assuranceUiEnabled ? 1113 : 1111
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
    command: flaggedRun ? `npx next dev -p ${devPort}` : 'npm run dev',
    url: baseURL,
    reuseExistingServer: flaggedRun ? false : !process.env.CI,
    timeout: 120 * 1000,
  },
})

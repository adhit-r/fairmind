import { expect, test, type BrowserContext, type Page, type Route } from '@playwright/test'

const currentUser = {
  id: 'session-user-1',
  username: 'verified-reviewer',
  email: 'verified-reviewer@acme.test',
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function installSessionShell(
  context: BrowserContext,
  { delayLogout = false }: { delayLogout?: boolean } = {},
) {
  let currentSessionRequests = 0
  let currentSessionAuthorization: string | undefined
  let logoutRequests = 0
  let releaseLogout = () => {}
  const logoutGate = new Promise<void>((resolve) => {
    releaseLogout = resolve
  })

  await context.addInitScript(() => {
    window.localStorage.setItem('access_token', 'session-access-token')
    window.localStorage.setItem('refresh_token', 'session-refresh-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.sessionStorage.setItem('oauth_state', 'oauth-state')
    window.sessionStorage.setItem('code_verifier', 'code-verifier')
  })

  await context.route('**/api/proxy/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname.replace('/api/proxy', '')

    if (path === '/api/v1/auth/me') {
      currentSessionRequests += 1
      currentSessionAuthorization = request.headers().authorization
      return fulfillJson(route, currentUser)
    }
    if (path === '/api/v1/auth/logout') {
      logoutRequests += 1
      if (delayLogout) await logoutGate
      return fulfillJson(route, { detail: 'Revocation unavailable' }, 500)
    }
    if (path === '/api/v1/organizations') {
      return fulfillJson(route, { organizations: [] })
    }
    if (path === '/api/v1/ai-governance/systems') {
      return fulfillJson(route, [])
    }
    return fulfillJson(route, [])
  })

  return {
    releaseLogout,
    getCurrentSessionRequests: () => currentSessionRequests,
    getCurrentSessionAuthorization: () => currentSessionAuthorization,
    getLogoutRequests: () => logoutRequests,
  }
}

async function expectSessionStorageCleared(page: Page) {
  await expect.poll(() => page.evaluate(() => ({
    accessToken: window.localStorage.getItem('access_token'),
    refreshToken: window.localStorage.getItem('refresh_token'),
    selectedOrgId: window.localStorage.getItem('selected_org_id'),
    oauthState: window.sessionStorage.getItem('oauth_state'),
    codeVerifier: window.sessionStorage.getItem('code_verifier'),
  }))).toEqual({
    accessToken: null,
    refreshToken: null,
    selectedOrgId: null,
    oauthState: null,
    codeVerifier: null,
  })
}

test('shares one verified session across the dashboard shell', async ({ context, page }) => {
  const session = await installSessionShell(context)

  await page.goto('/tests')

  await expect(page.getByRole('button', { name: 'verified-reviewer profile' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Open user menu for verified-reviewer' })).toBeVisible()
  await expect(page.getByText(currentUser.email, { exact: true })).toBeVisible()
  expect(session.getCurrentSessionRequests()).toBe(1)
  expect(session.getCurrentSessionAuthorization()).toBe('Bearer session-access-token')
})

test('sidebar logout clears the browser session when revocation fails', async ({ context, page }) => {
  const session = await installSessionShell(context)
  await page.goto('/tests')
  await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible()

  await page.getByRole('button', { name: 'Logout' }).click()

  await expect(page).toHaveURL(/\/login$/)
  await expectSessionStorageCleared(page)
  expect(session.getLogoutRequests()).toBe(1)
})

test('header logout clears sibling tabs before slow revocation settles', async ({ context, page }) => {
  const session = await installSessionShell(context, { delayLogout: true })
  const sibling = await context.newPage()
  await Promise.all([page.goto('/tests'), sibling.goto('/tests')])
  await expect(page.getByRole('button', { name: 'Open user menu for verified-reviewer' })).toBeVisible()
  await expect(sibling.getByRole('button', { name: 'verified-reviewer profile' })).toBeVisible()

  await page.getByRole('button', { name: 'Open user menu for verified-reviewer' }).click()
  await page.getByRole('menuitem', { name: 'LOGOUT' }).click()

  await expect(page).toHaveURL(/\/login$/)
  await expect(sibling).toHaveURL(/\/login$/)
  await expectSessionStorageCleared(page)
  expect(session.getLogoutRequests()).toBe(1)

  session.releaseLogout()
  await sibling.close()
})

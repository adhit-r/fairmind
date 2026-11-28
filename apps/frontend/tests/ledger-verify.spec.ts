import { createHash } from 'node:crypto'
import { expect, test, type Page } from '@playwright/test'

const PACK = '7c2d9a10-3b4e-4f6a-8d15-2e9b0c4a6f31'
const ORG = 'org-1'
const GENESIS = '0'.repeat(64)

/** Python's json.dumps(sort_keys=True, separators=(",", ":")), which is what the server hashed. */
const canonical = (v: unknown): string => {
  const text = Array.isArray(v)
    ? `[${v.map(canonical).join(',')}]`
    : v && typeof v === 'object'
      ? `{${Object.keys(v as object).sort().map((k) => `${JSON.stringify(k)}:${canonical((v as Record<string, unknown>)[k])}`).join(',')}}`
      : JSON.stringify(v)
  return text.replace(/[\u0080-￿]/g, (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`)
}
const sha = (text: string) => createHash('sha256').update(text).digest('hex')

type Spec = [kind: string, subjectType: string, subjectId: string, payload: Record<string, unknown>]
const SPECS: Spec[] = [
  ['board.pinned', 'saved_board', '91c0b2f4-5d1e-4a7c-8e3b-0a6d7d3e1f20', { note: 'café ✓', layoutSha256: 'ab'.repeat(32) }],
  ['board.unpinned', 'saved_board', '91c0b2f4-5d1e-4a7c-8e3b-0a6d7d3e1f20', {}],
  ['view.sealed', 'shared_view', '03d85e11-92aa-4c7f-b6f0-7a1d3e5c9b02', { seal: 'cd'.repeat(32), access: 'named', readers: 2, expiresAt: '2026-12-21T13:05:00+00:00' }],
  ['view.revoked', 'shared_view', '03d85e11-92aa-4c7f-b6f0-7a1d3e5c9b02', {}],
  ['board.pinned', 'saved_board', 'c4a2d7e0-1b53-49f8-a319-19ef6b0c2d84', { layoutSha256: 'ef'.repeat(32) }],
  ['view.sealed', 'shared_view', '5b1f5a46-7b1e-4a58-9d5e-0c6b0e3c2a11', { seal: '12'.repeat(32), access: 'link', readers: 0, expiresAt: '2026-12-28T14:02:00+00:00' }],
  ['view.revoked', 'shared_view', '5b1f5a46-7b1e-4a58-9d5e-0c6b0e3c2a11', {}],
  ['board.unpinned', 'saved_board', 'c4a2d7e0-1b53-49f8-a319-19ef6b0c2d84', {}],
]

/** An organisation's chain as the server writes it: each entry hashed over its fields and the hash before it. */
function chain() {
  const out: Array<Record<string, unknown>> = []
  let prev = GENESIS
  SPECS.forEach(([kind, subject_type, subject_id, payload], i) => {
    const fields = {
      org_id: ORG, seq: i + 1, kind, subject_type, subject_id, actor: '4f2a1c90-7b3e-4d58-9a61-2c0e5f8b3d91', payload,
      created_at: `2026-11-${String(3 + i * 3).padStart(2, '0')}T08:57:00+00:00`, prev_hash: prev,
    }
    const hash = sha(canonical(fields))
    out.push({ ...fields, hash })
    prev = hash
  })
  return out
}

async function openPack(page: Page, manifest: Record<string, unknown>) {
  await page.route(`**/api/proxy/api/v1/public/packs/${PACK}**`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: PACK, title: 'Q4 inspection pack', manifestHash: 'f'.repeat(64), manifest, expiresAt: '2026-12-28T00:00:00Z' }) }),
  )
  await page.goto(`/verify/${PACK}?t=abc`)
}

const base = { title: 'Q4 inspection pack', frameworks: [], createdAt: '2026-11-28T12:00:00Z', createdBy: 'u1', systems: [], organisation: { attestations: [], workflows: [], policies: [] } }

test.describe('Ledger on the auditor verify page', () => {
  test('the hashing here matches the server for a non-ASCII payload', () => {
    // Computed with Python json.dumps(..., sort_keys=True, separators=(",", ":")) over the first entry.
    expect(chain()[0].hash).toBe('c6638889e847f6149e83b2991d5de581afcd7f18ccefb5584f5b9541c9363331')
  })

  test('an intact ledger shows its check, the newest entries and all of them on request', async ({ page }) => {
    await openPack(page, { ...base, version: 3, ledger: chain() })
    await expect(page.getByText('Ledger chain intact')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText('Your browser rebuilt all 8 entries.')).toBeVisible()
    const ledger = page.getByRole('region', { name: 'Organisation ledger' })
    await expect(ledger.getByRole('row')).toHaveCount(7) // the header and the newest six
    await expect(ledger.getByText('Showing the newest 6 of 8.')).toBeVisible()
    await ledger.getByRole('button', { name: 'Show all 8 entries' }).click()
    await expect(ledger.getByRole('row')).toHaveCount(9)
    await expect(ledger.getByText('Board shared as a view').first()).toBeVisible()
    await expect(ledger.getByText('does not certify compliance')).toBeVisible()
  })

  test('a changed entry breaks the chain at that entry and greys the ones after it', async ({ page }) => {
    const tampered = chain()
    tampered[2] = { ...tampered[2], payload: { ...(tampered[2].payload as object), readers: 9 } }
    await openPack(page, { ...base, version: 3, ledger: tampered })
    await expect(page.getByText('Ledger chain broken at entry 3')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('alert').filter({ hasText: 'Entries 3 to 8 cannot be relied on' })).toBeVisible()
    const ledger = page.getByRole('region', { name: 'Organisation ledger' })
    await expect(ledger.getByText('Does not match its hash')).toBeVisible()
    await expect(ledger.getByText('Follows a broken link')).toHaveCount(5)
    await expect(ledger.getByText('Matches')).toHaveCount(2)
  })

  test('a pack built before ledgers says so and shows no ledger section', async ({ page }) => {
    await openPack(page, { ...base, version: 2 })
    await expect(page.getByText('No ledger in this pack')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('region', { name: 'Organisation ledger' })).toHaveCount(0)
  })
})

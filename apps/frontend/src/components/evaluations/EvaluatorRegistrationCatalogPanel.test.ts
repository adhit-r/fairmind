import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import type { EvaluatorCatalogSnapshot, EvaluatorRegistration } from '@/lib/api/hooks/useEvaluatorCatalog'

import { EvaluatorRegistrationCatalogPanel } from './EvaluatorRegistrationCatalogPanel'

function registration(overrides: Partial<EvaluatorRegistration> = {}): EvaluatorRegistration {
  return {
    id: 'registration-1',
    organizationId: 'org-1',
    evaluatorId: 'inspect-agent-safety',
    sourceType: 'external_provider',
    adapterName: 'inspect',
    adapterVersion: '0.3.0',
    resultContractVersion: '1.0.0',
    issuerId: 'issuer-a',
    signingKeyId: 'key-a',
    bindingHash: 'a'.repeat(64),
    status: 'revoked',
    submittedBy: 'user-1',
    submittedAt: '2026-08-09T00:00:00Z',
    reviewedBy: 'reviewer-1',
    reviewedAt: '2026-08-09T01:00:00Z',
    reviewRationale: 'Independent identity review recorded.',
    revokedBy: 'reviewer-2',
    revokedAt: '2026-08-09T02:00:00Z',
    revocationRationale: 'Signing key was withdrawn.',
    ...overrides,
  }
}

function snapshot(overrides: Partial<EvaluatorCatalogSnapshot> = {}): EvaluatorCatalogSnapshot {
  return {
    state: 'ready',
    organizationId: 'org-1',
    registrations: [registration()],
    page: { limit: 25, offset: 0, hasMore: true },
    error: null,
    disabledReason: null,
    canRetry: false,
    ...overrides,
  }
}

test('renders only identity-binding and lifecycle data returned by the catalog', () => {
  const markup = renderToStaticMarkup(createElement(EvaluatorRegistrationCatalogPanel, {
    catalog: snapshot(),
  }))

  assert.match(markup, /Evaluator registration catalog/)
  assert.match(markup, /Evaluator binding/)
  assert.match(markup, /Binding hash/)
  assert.match(markup, /Signer \/ source/)
  assert.match(markup, /Review \/ revocation/)
  assert.match(markup, /Registration status/)
  assert.match(markup, /inspect-agent-safety/)
  assert.match(markup, /issuer-a/)
  assert.match(markup, /key-a/)
  assert.match(markup, /Signing key was withdrawn\./)
  assert.match(markup, /More registration records are available on a later page\./)
  assert.match(markup, /Previous page/)
  assert.match(markup, /Next page/)
  assert.doesNotMatch(markup, /trusted|certified|quality|compliance|worker-ready/i)
})

test('keeps a disabled route distinct from an empty catalog and does not render records', () => {
  const markup = renderToStaticMarkup(createElement(EvaluatorRegistrationCatalogPanel, {
    catalog: snapshot({
      state: 'disabled',
      registrations: [],
      page: null,
      error: new Error('Evaluator catalog administration is not enabled.'),
      disabledReason: 'catalog_route_disabled',
    }),
  }))

  assert.match(markup, /Evaluator catalog route disabled/)
  assert.match(markup, /No registration records were displayed\./)
  assert.doesNotMatch(markup, /inspect-agent-safety/)
})

test('shows a server conflict code without offering a stale mutation retry', () => {
  const error = Object.assign(new Error('The registration changed before this request completed.'), {
    code: 'evaluator_registration_transition_conflict',
  })
  const markup = renderToStaticMarkup(createElement(EvaluatorRegistrationCatalogPanel, {
    catalog: snapshot({
      state: 'unavailable',
      registrations: [],
      error,
      canRetry: false,
    }),
  }))

  assert.match(markup, /Server code: evaluator_registration_transition_conflict/)
  assert.doesNotMatch(markup, /Retry catalog request/)
})

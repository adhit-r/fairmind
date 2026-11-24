import assert from 'node:assert/strict'
import { test } from 'node:test'
import { renderToStaticMarkup } from 'react-dom/server'
import { CheckEvidenceLinks } from './CheckEvidenceLinks'

const check = { evidenceId: 'newest-pass', state: 'proven' as const }

test('offers each distinct record supporting the failure, excluding the newest pass', () => {
  const html = renderToStaticMarkup(
    <CheckEvidenceLinks systemId="compas" check={{ ...check, failureEvidenceIds: ['one', 'two', 'one'] }} failed />
  )
  assert.equal((html.match(/<a /g) ?? []).length, 2)
  assert.match(html, /system=compas&amp;evidence=one"/)
  assert.match(html, /system=compas&amp;evidence=two"/)
  assert.doesNotMatch(html, /newest-pass/)
})

test('an unattributed failure or unknown system has no source link', () => {
  for (const evidence of [check, { ...check, failureEvidenceIds: [] }]) {
    const html = renderToStaticMarkup(<CheckEvidenceLinks systemId="compas" check={evidence} failed />)
    assert.match(html, /Source record unavailable/)
    assert.doesNotMatch(html, /href=/)
  }
  assert.doesNotMatch(renderToStaticMarkup(<CheckEvidenceLinks check={check} failed={false} />), /href=/)
})

test('an ordinary check links its own selected record', () => {
  const html = renderToStaticMarkup(<CheckEvidenceLinks systemId="compas" check={check} failed={false} />)
  assert.match(html, /system=compas&amp;evidence=newest-pass"/)
})

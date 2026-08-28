import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

test('grants the evaluator catalog render and fetch gate only to literal catalog administrators', () => {
  const pageSource = readFileSync(new URL('./page.tsx', import.meta.url), 'utf8')

  assert.doesNotMatch(pageSource, /evaluation:catalog:read/)
  assert.match(
    pageSource,
    /const canViewEvaluatorCatalog = selectedOrg\?\.permissions\?\.includes\('evaluation:catalog:admin'\) === true/,
  )
  assert.match(
    pageSource,
    /EVALUATOR_CATALOG_UI_ENABLED && canViewEvaluatorCatalog \? \(\s*<EvaluatorRegistrationCatalogSection/,
  )
  assert.match(pageSource, /authorized=\{canViewEvaluatorCatalog\}/)
})

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const pageSources = [
  ['Explainability Studio', new URL('./explainability-studio/page.tsx', import.meta.url)],
  ['LLM Judge', new URL('./llm-judge/page.tsx', import.meta.url)],
  ['LLM Testing', new URL('./llm-testing/page.tsx', import.meta.url)],
  ['Modern Bias Evaluation', new URL('./modern-bias/page.tsx', import.meta.url)],
  ['Multimodal Bias Detection', new URL('./multimodal-bias/page.tsx', import.meta.url)],
] as const

const navigationSource = readFileSync(
  new URL('../../lib/constants/navigation.ts', import.meta.url),
  'utf8',
)
const rootLayoutSource = readFileSync(new URL('../layout.tsx', import.meta.url), 'utf8')

for (const [pageName, pageUrl] of pageSources) {
  test(`${pageName} renders only the shared unsupported-pack boundary`, () => {
    const pageSource = readFileSync(pageUrl, 'utf8')

    assert.match(pageSource, /UnsupportedEvaluationPackNotice/)
    assert.doesNotMatch(pageSource, /['"]use client['"]/)
    assert.doesNotMatch(pageSource, /use(?:LLMJudge|ModernBias|MultimodalBias|Models|State|Toast)/)
    assert.doesNotMatch(pageSource, /mockResults|setTimeout|generatePDF|generateDOCX|generateBiasJSON/)
    assert.doesNotMatch(pageSource, /<form|<Button|type=['"]submit['"]/)
  })
}

test('navigation and adjacent workflows describe the pack as unavailable', () => {
  assert.match(
    navigationSource,
    /title: ['"]LLM Judge['"][\s\S]*description: ['"]Evaluation pack unavailable['"]/,
  )
  assert.match(
    navigationSource,
    /title: ['"]Explainability Studio['"][\s\S]*description: ['"]Evaluation pack unavailable['"]/,
  )
  assert.doesNotMatch(rootLayoutSource, /Detect bias in ML models, LLMs, and multimodal systems/)
  assert.doesNotMatch(rootLayoutSource, /Comprehensive bias testing for ML, LLMs, and multimodal systems/)
})

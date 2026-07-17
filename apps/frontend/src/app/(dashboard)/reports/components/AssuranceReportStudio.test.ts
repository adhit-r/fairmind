import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

import {
  buildAssurancePdfLines,
  reportMatchesAssuranceScope,
  type AssurancePdfContext,
} from './AssuranceReportStudio'
import type { SavedReport } from '../../audit-reports/components/ReportHistoryTable'

const report: SavedReport = {
  id: 'report-1',
  systemId: 'system-1',
  reportType: 'governance',
  title: 'Governance Assurance Summary',
  generatedBy: 'reviewer@acme.test',
  config: {
    frameworks: ['AIUC-1 April, 2026'],
    sections: ['risk_overview', 'remediations', 'decision_log'],
  },
  data: {
    system: { name: 'Claims Review Agent', owner: 'model-owner@acme.test' },
    risks: [{ title: 'Unbounded tool execution', severity: 'high', status: 'open' }],
    remediation: [{ title: 'Restrict production tool allowlist', status: 'in_progress', owner: 'platform@acme.test' }],
    approvals: [{ status: 'approved', requestedBy: 'governance@acme.test', decisionNotes: 'Approved for monitored deployment.' }],
  },
  createdAt: '2026-07-17T14:00:00Z',
}

const context: AssurancePdfContext = {
  frameworkLabel: 'AIUC-1 April, 2026',
  assuranceAsOf: '2026-07-17T15:00:00Z',
  readiness: {
    applicable: 4,
    accepted: 2,
    blockingFindings: 1,
    missingEvidence: 1,
    staleEvidence: 0,
  },
  evidenceRuns: [{
    sourceIdentifier: 'FairMind Bias Suite',
    suiteName: 'Bias and subgroup parity',
    contentHash: '0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55',
    result: 'passed_with_limitations',
    capturedAt: '2026-07-15T10:30:00Z',
  }],
  controls: [{ externalId: 'A006.1', title: 'Document model limitations', openFindings: 1 }],
  limitations: ['Sparse intersectional cohorts were excluded below n=30.'],
}

describe('buildAssurancePdfLines', () => {
  test('includes assurance scope, evidence, unresolved work, decisions, and claim boundaries', () => {
    const content = buildAssurancePdfLines(report, context).join('\n')

    assert.match(content, /System: Claims Review Agent/)
    assert.match(content, /Framework scope: AIUC-1 April, 2026/)
    assert.match(content, /Assurance data as of: 2026-07-17T15:00:00Z/)
    assert.match(content, /Operational source snapshot: Governance Assurance Summary generated 2026-07-17T14:00:00Z/)
    assert.match(content, /Accepted controls: 2 \/ 4/)
    assert.match(content, /Rejected assessments: 1/)
    assert.match(content, /0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55/)
    assert.match(content, /Unbounded tool execution/)
    assert.match(content, /Restrict production tool allowlist/)
    assert.match(content, /Approved for monitored deployment\./)
    assert.match(content, /Sparse intersectional cohorts were excluded below n=30\./)
    assert.match(content, /does not constitute certification or an assurance opinion/)
  })

  test('only includes reports pinned to exactly the current system and framework', () => {
    assert.equal(reportMatchesAssuranceScope(report, 'system-1', 'AIUC-1 April, 2026'), true)
    assert.equal(reportMatchesAssuranceScope({ ...report, config: { frameworks: [] } }, 'system-1', 'AIUC-1 April, 2026'), false)
    assert.equal(reportMatchesAssuranceScope({
      ...report,
      config: { frameworks: ['AIUC-1 April, 2026', 'NIST AI RMF 1.0'] },
    }, 'system-1', 'AIUC-1 April, 2026'), false)
    assert.equal(reportMatchesAssuranceScope(report, 'system-2', 'AIUC-1 April, 2026'), false)
  })
})

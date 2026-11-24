import { readFile } from 'node:fs/promises'
import { expect, test, type Page, type Route } from '@playwright/test'

const governance = '/api/v1/ai-governance'
const reports = `${governance}/reports`
const definitions = `${reports}/system-assurance/definitions`
const schedules = `${reports}/system-assurance/schedules`
const scheduledRuns = `${reports}/system-assurance/scheduled-runs`
const reviewPath = `${reports}/system-assurance`
const reportId = 'report-july-claims'
const refreshedReportId = 'report-july-claims-refreshed'
const period = { dateFrom: '2026-07-01', dateTo: '2026-07-31', timeZone: 'UTC' }
const narrative = 'The sampled claims process met the reviewed requirement.'
const source = 'July monitoring sample'
const revision = 'b'.repeat(64)
const approvedAt = '2026-08-01T14:03:00Z'
const frameworkVersion = {
  id: 'framework-version-1',
  framework_key: 'aiuc-1',
  name: 'AIUC-1',
  version_label: 'April 2026',
  source_hash: 'a'.repeat(64),
  status: 'active',
}
const systems = [
  { id: 'system-1', name: 'Claims triage', owner: 'Claims team', riskTier: 'high', lifecycleStage: 'govern', metadata: { system_version: '2.4.1' } },
  { id: 'system-2', name: 'Claims triage pilot', owner: 'Pilot team', riskTier: 'medium', lifecycleStage: 'govern', metadata: { system_version: '1.2.0' } },
]
const framework = {
  assignmentId: 'assignment-2',
  versionId: frameworkVersion.id,
  key: frameworkVersion.framework_key,
  name: frameworkVersion.name,
  versionLabel: frameworkVersion.version_label,
}
const definition = {
  id: 'setup-claims-pilot',
  title: 'Claims pilot monthly assurance',
  systemId: systems[1].id,
  assignmentId: framework.assignmentId,
  periodPreset: 'previous_complete_utc_month',
  createdBy: 'reviewer@example.test',
  createdAt: '2026-08-01T00:05:00Z',
}
const exportedPdf = '%PDF-1.7\nClaims triage pilot, July monitoring sample\n%%EOF'
const scheduledRun = {
  id: 'schedule-occurrence-july',
  definitionId: definition.id,
  systemId: definition.systemId,
  scheduledAt: '2026-08-01T14:00:00Z',
  attemptedAt: '2026-08-01T14:00:05Z',
  dateFrom: period.dateFrom,
  dateTo: period.dateTo,
  status: 'ready',
  reportId,
  error: null,
}
const failedRun = {
  ...scheduledRun,
  id: 'schedule-occurrence-june',
  scheduledAt: '2026-07-01T14:00:00Z',
  dateFrom: '2026-06-01',
  dateTo: '2026-06-30',
  status: 'failed',
  reportId: null,
  error: 'The framework assignment was unavailable.',
}
const nextScheduleRuns = [
  { scheduledAt: '2026-09-01T14:00:00Z', dateFrom: '2026-08-01', dateTo: '2026-08-31' },
  { scheduledAt: '2026-10-01T14:00:00Z', dateFrom: '2026-09-01', dateTo: '2026-09-30' },
]
const activeSchedule = {
  id: 'schedule-claims',
  definitionId: definition.id,
  systemId: definition.systemId,
  assignmentId: definition.assignmentId,
  title: definition.title,
  cadence: 'monthly',
  timeZone: 'Asia/Kolkata',
  localTime: '19:30',
  paused: false,
  next: nextScheduleRuns,
  latestRun: scheduledRun,
}
const scheduleHref = `/reports/schedules?definition=${definition.id}`
const scheduledRunHref = `/reports/system?system=${definition.systemId}&definition=${definition.id}&run=${scheduledRun.id}`
const assignedReviewer = { id: 'user-1', name: 'Jamie Patel' }
const otherReviewer = { id: 'user-2', name: 'Morgan Lee' }
const returnReason = 'Include the July cohort coverage in the evidence.'

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({ status, json: data })
}

function record(status: 'preview' | 'approved', { note = narrative, refreshed = false, reportPeriod = period, savedSetup = false } = {}) {
  const currentRevision = refreshed ? 'd'.repeat(64) : revision
  const sourceLabel = refreshed ? 'Rechecked July sample' : source
  return {
    id: refreshed ? refreshedReportId : reportId,
    systemId: systems[1].id,
    reportType: 'system-assurance',
    title: savedSetup ? definition.title : 'System Assurance Report',
    config: {
      templateVersion: 1,
      assignmentId: framework.assignmentId,
      frameworkVersionId: framework.versionId,
      frameworks: [framework.name],
      ...reportPeriod,
      ...(savedSetup ? { definitionId: definition.id } : {}),
    },
    data: {
      system: systems[1],
      framework,
      period: reportPeriod,
      controls: [{
        id: 'control-1',
        externalId: 'A006.1',
        title: 'Record monitoring coverage',
        applicability: 'applicable',
        status: 'ready_for_review',
        owner: 'Pilot team',
        justification: null,
        evidenceStatus: 'current',
        acceptedEvidenceCount: 1,
      }],
      evidence: [{
        id: 'period-evidence',
        runId: 'period-run',
        evidenceId: 'period-artifact',
        contentHash: 'c'.repeat(64),
        result: 'passed_with_limitations',
        sourceType: 'fairmind_evaluation',
        sourceIdentifier: sourceLabel,
        capturedAt: '2026-07-31T23:59:59Z',
        suiteName: sourceLabel,
        suiteVersion: '2026.07',
        subjectVersion: '1.2.0',
        runnerVersion: '1.8.0',
        assuranceSource: 'fairmind_internal',
        limitations: ['Manual checks cover one cohort.'],
        candidateMappings: [{
          id: 'mapping-1',
          evidenceId: 'period-artifact',
          controlAssessmentId: 'control-1',
          state: 'accepted',
          rationale: 'Reviewed the July sample.',
          reviewVersion: 1,
          reviewHistory: [],
        }],
      }],
      coverage: { evidenceRuns: 1, controls: 1, excludedUnmappedRuns: 1, excludedUndatedRuns: 0 },
      limitations: ['Manual checks cover one cohort.'],
      generatedAt: '2026-08-01T14:00:00Z',
    },
    generatedBy: 'author@example.test',
    createdAt: '2026-08-01T14:00:00Z',
    revision: currentRevision,
    status,
    sha256: status === 'approved' ? currentRevision : null,
    narrative: note,
    approvedBy: status === 'approved' ? 'reviewer@example.test' : null,
    approvedAt: status === 'approved' ? approvedAt : null,
  }
}

async function install(page: Page, { viewer = false, conflictOnce = false, savedSetup = false, scheduleState, assigned = false }: {
  viewer?: boolean; conflictOnce?: boolean; savedSetup?: boolean; scheduleState?: 'existing' | 'new'
  assigned?: boolean
} = {}) {
  const previewBodies: unknown[] = []
  const definitionBodies: unknown[] = []
  const approvals: Array<{ id: string; body: unknown }> = []
  const historyScopes: Array<{ systemId: string | null; reportType: string | null; definitionId?: string }> = []
  const openedVersions: string[] = []
  const downloads: string[] = []
  const schedulePreviews: unknown[] = []
  const scheduleSaves: unknown[] = []
  const schedulePauses: unknown[] = []
  const scheduleRetries: string[] = []
  const reviews: string[] = []
  const returnedReviews: unknown[] = []
  const reviewerChanges: Array<{ scope: 'schedule' | 'run'; reviewer_id: string | null }> = []
  let storedDefinition = savedSetup || scheduleState ? definition : null
  let schedule = scheduleState === 'existing' ? activeSchedule : null
  let currentRun: typeof scheduledRun & {
    reviewer?: typeof assignedReviewer | null;
    reviewState?: 'awaiting_review' | 'returned' | 'approved';
    returned?: { reason: string; by: string; at: string; revision: string };
  } = { ...scheduledRun, ...(assigned ? { reviewer: assignedReviewer, reviewState: 'awaiting_review' } : {}) }
  let defaultReviewer = assigned ? assignedReviewer : null
  let previousRun: Omit<typeof failedRun, 'error'> & { error: string | null } = { ...failedRun }
  let approved = viewer ? record('approved', { savedSetup }) : null
  let preview = scheduleState ? record('preview', { savedSetup: true, note: '' }) : record('preview')
  let conflictPending = conflictOnce

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-report-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.localStorage.setItem('fairmind:selected-ai-system', 'system-1')
  })
  await page.route('**/api/proxy/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/proxy', '')
    if (path === '/api/v1/auth/me') {
      return json(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@example.test' })
    }
    if (path === '/api/v1/organizations') {
      return json(route, { organizations: [{
        id: 'org-1',
        name: 'Claims assurance',
        slug: 'claims-assurance',
        owner_id: 'owner-1',
        created_at: '2026-01-01T00:00:00Z',
        role: viewer ? 'viewer' : 'admin',
        permissions: viewer ? ['model:read'] : ['model:read', 'model:write'],
      }] })
    }
    if (path === '/api/v1/shadow-ai') return json(route, { findings: [] })
    if (path === '/api/v1/whats-new') return json(route, { releases: [], seen: null, emails: false })
    if (path === '/api/v1/plan') return json(route, { status: 'discovery' })
    if (path === `${governance}/internal-audits/mine`) return json(route, { items: [] })
    if (path === `${governance}/systems`) return json(route, systems)
    if (path === `${reports}/overview`) {
      return json(route, {
        role: url.searchParams.get('role') || 'executive',
        scope: { systemId: null, systemName: null },
        framework: { key: framework.key, name: framework.name },
        followed: [framework.key],
        systemsCount: systems.length,
        briefing: { source: 'template', parts: [{ text: 'The Claims team captured monitoring evidence for the pilot.' }] },
        generatedAt: '2026-08-01T00:05:00Z',
      })
    }
    if (path === `${governance}/organizations/org-1/frameworks`) {
      return json(route, [{ framework_key: 'aiuc-1', name: 'AIUC-1' }])
    }
    if (path === `${governance}/organizations/org-1/frameworks/aiuc-1/versions`) {
      return json(route, [frameworkVersion])
    }
    const assignmentSystem = path.match(/\/systems\/([^/]+)\/framework-assignments$/)?.[1]
    if (assignmentSystem) {
      return json(route, [{
        id: assignmentSystem === systems[1].id ? framework.assignmentId : 'assignment-1',
        org_id: 'org-1',
        system_id: assignmentSystem,
        framework_version_id: framework.versionId,
      }])
    }
    if (path === definitions) {
      if (request.method() === 'POST') {
        definitionBodies.push(request.postDataJSON())
        if (viewer) return json(route, { detail: 'Write access required' }, 403)
        storedDefinition = definition
        return json(route, storedDefinition, 201)
      }
      return json(route, storedDefinition ? [storedDefinition] : [])
    }
    if (path === `${definitions}/${definition.id}`) {
      return storedDefinition ? json(route, storedDefinition) : json(route, { detail: 'Saved report unavailable' }, 404)
    }
    if (path === `${reviewPath}/reviewers`) return json(route, [assignedReviewer, otherReviewer])
    if (path === `${reviewPath}/review-assignments`) {
      return json(route, currentRun.reviewState === 'awaiting_review' && currentRun.reviewer?.id === assignedReviewer.id
        ? [{ run: currentRun, title: definition.title, systemName: systems[1].name }] : [])
    }
    if (scheduleState && path === schedules) {
      const latestRun = scheduleState === 'new' ? null : currentRun
      const attentionRun = scheduleState === 'new' ? null : previousRun.status === 'failed' ? previousRun
        : currentRun.status === 'ready' ? currentRun : null
      return json(route, schedule ? [{ ...schedule, latestRun, attentionRun, defaultReviewer }] : [])
    }
    if (scheduleState && path === `${schedules}/${definition.id}/reviewer`) {
      const payload = request.postDataJSON() as { reviewer_id: string | null }
      reviewerChanges.push({ scope: 'schedule', ...payload })
      defaultReviewer = [assignedReviewer, otherReviewer].find(({ id }) => id === payload.reviewer_id) ?? null
      return json(route, { ...activeSchedule, defaultReviewer })
    }
    if (scheduleState && path === `${scheduledRuns}/${scheduledRun.id}/reviewer`) {
      const payload = request.postDataJSON() as { reviewer_id: string | null }
      reviewerChanges.push({ scope: 'run', ...payload })
      currentRun = { ...currentRun, reviewer: [assignedReviewer, otherReviewer].find(({ id }) => id === payload.reviewer_id) ?? null }
      return json(route, currentRun)
    }
    if (scheduleState && path === `${schedules}/preview`) {
      schedulePreviews.push(request.postDataJSON())
      return json(route, { next: nextScheduleRuns })
    }
    if (scheduleState && path === `${schedules}/${definition.id}`) {
      if (request.method() === 'PUT') {
        scheduleSaves.push(request.postDataJSON())
        schedule = activeSchedule
      } else if (request.method() === 'PATCH') {
        const body = request.postDataJSON()
        schedulePauses.push(body)
        schedule = { ...activeSchedule, paused: body.paused, next: body.paused ? [] : nextScheduleRuns }
      }
      return json(route, schedule ? { ...schedule, latestRun: scheduleState === 'new' ? null : currentRun } : null)
    }
    if (scheduleState && path === `${schedules}/${definition.id}/runs`) {
      return json(route, scheduleState === 'existing' ? [currentRun, previousRun] : [])
    }
    if (scheduleState && path === `${scheduledRuns}/${failedRun.id}/retry`) {
      scheduleRetries.push(previousRun.id)
      previousRun = { ...previousRun, status: 'pending', error: null }
      return json(route, previousRun)
    }
    if (scheduleState && path === `${scheduledRuns}/${scheduledRun.id}/retry`) {
      scheduleRetries.push(scheduledRun.id)
      preview = { ...record('preview', { savedSetup: true, refreshed: true, note: '' }), id: reportId }
      if (assigned) currentRun = { ...currentRun, reviewState: 'awaiting_review' }
      return json(route, currentRun)
    }
    if (scheduleState && path === `${scheduledRuns}/${scheduledRun.id}/return`) {
      const payload = request.postDataJSON() as { revision: string; reason: string }
      if (currentRun.reviewer?.id !== assignedReviewer.id || currentRun.reviewState !== 'awaiting_review') {
        return json(route, { detail: 'Review is assigned to another reviewer.' }, 403)
      }
      if (payload.revision !== preview.revision) return json(route, { detail: 'The version changed.' }, 409)
      returnedReviews.push(payload)
      currentRun = { ...currentRun, reviewState: 'returned', returned: { ...payload, by: 'reviewer@example.test', at: approvedAt } }
      return json(route, currentRun)
    }
    if (scheduleState && path === `${scheduledRuns}/${scheduledRun.id}/review`) {
      reviews.push(scheduledRun.id)
      return json(route, { run: currentRun, report: approved || preview, canRefresh: !viewer,
        canReview: !viewer && currentRun.status === 'ready' && currentRun.reviewState !== 'returned'
          && (!currentRun.reviewer || currentRun.reviewer.id === assignedReviewer.id) })
    }
    if (path === `${reports}/system-assurance/preview` && request.method() === 'POST') {
      const body = request.postDataJSON()
      previewBodies.push(body)
      preview = record('preview', {
        note: body.narrative,
        refreshed: conflictOnce && previewBodies.length > 1,
        reportPeriod: { dateFrom: body.date_from, dateTo: body.date_to, timeZone: 'UTC' },
        savedSetup: body.definition_id === definition.id,
      })
      return json(route, preview, 201)
    }
    if (path === `${reports}/system-assurance/${preview.id}/approve` && request.method() === 'POST') {
      approvals.push({ id: preview.id, body: request.postDataJSON() })
      if (conflictPending) {
        conflictPending = false
        return json(route, { detail: 'Source records changed. Prepare a fresh preview before approval.' }, 409)
      }
      approved = {
        ...preview,
        status: 'approved',
        sha256: preview.revision,
        approvedBy: 'reviewer@example.test',
        approvedAt,
      }
      if (scheduleState) currentRun = { ...currentRun, status: 'approved', reviewState: 'approved' }
      return json(route, approved)
    }
    if (path === reports && request.method() === 'GET') {
      const systemId = url.searchParams.get('system_id')
      const reportType = url.searchParams.get('report_type')
      const definitionId = url.searchParams.get('definition_id')
      historyScopes.push({ systemId, reportType, ...(definitionId ? { definitionId } : {}) })
      const inScope = approved && systemId === systems[1].id && reportType === 'system-assurance'
        && (!definitionId || approved.config.definitionId === definitionId)
      return json(route, inScope ? [approved] : [])
    }
    if (approved && path === `${reports}/${approved.id}` && request.method() === 'GET') {
      openedVersions.push(approved.id)
      return json(route, approved)
    }
    if (path === `/api/v1/reports/snapshots/${reportId}/pdf` && request.method() === 'GET') {
      downloads.push(path)
      return route.fulfill({
        status: approved ? 200 : 409,
        contentType: 'application/pdf',
        headers: { 'Content-Disposition': 'attachment; filename="claims-assurance.pdf"' },
        body: exportedPdf,
      })
    }
    return json(route, [])
  })

  return { previewBodies, definitionBodies, approvals, historyScopes, openedVersions, downloads,
    schedulePreviews, scheduleSaves, schedulePauses, scheduleRetries, reviews, returnedReviews, reviewerChanges }
}

async function prepare(page: Page) {
  await page.goto('/reports/system?system=system-2')
  await expect(page.getByRole('heading', { name: 'System Assurance Report', exact: true })).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('combobox', { name: 'AI system', exact: true })).toHaveValue(systems[1].id)
  await page.getByRole('combobox', { name: 'Framework assignment', exact: true }).selectOption(framework.assignmentId)
  await page.getByLabel('Start date', { exact: true }).fill(period.dateFrom)
  await page.getByLabel('End date', { exact: true }).fill(period.dateTo)
  await page.getByLabel(/^Reviewer note/).fill(narrative)
  await page.getByRole('button', { name: 'Preview report', exact: true }).click()
  await expect(page.getByText(source, { exact: true }).first()).toBeVisible()
}

test('previews, saves and pauses a recurrence from a named report', async ({ page }) => {
  const calls = await install(page, { scheduleState: 'new' })
  await page.goto(`/reports/system?system=${definition.systemId}&definition=${definition.id}`)
  await page.getByRole('link', { name: 'Report schedule', exact: true }).click({ timeout: 30_000 })
  await expect(page).toHaveURL(new RegExp(`${scheduleHref.replace('?', '\\?')}$`), { timeout: 30_000 })
  await expect(page.getByRole('heading', { name: 'Report schedules', exact: true })).toBeVisible()
  await expect(page.getByLabel('Saved report', { exact: true })).toHaveValue(definition.id)
  await page.getByLabel('Cadence', { exact: true }).selectOption('monthly')
  await page.getByLabel('Time zone', { exact: true }).fill('Asia/Kolkata')
  await page.getByLabel('Local time', { exact: true }).fill('19:30')
  await page.getByRole('button', { name: 'Preview schedule', exact: true }).click()
  const upcoming = page.getByRole('region', { name: 'Schedule preview', exact: true })
  await expect(upcoming).toBeVisible()
  await expect(upcoming.locator('time')).toHaveCount(2)
  await expect(upcoming).toContainText('UTC')
  const input = { cadence: 'monthly', time_zone: 'Asia/Kolkata', local_time: '19:30' }
  expect(calls.schedulePreviews).toEqual([input])
  await page.getByRole('button', { name: 'Create schedule', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Pause schedule', exact: true })).toBeVisible()
  expect(calls.scheduleSaves).toEqual([input])
  await page.getByRole('button', { name: 'Pause schedule', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Resume schedule', exact: true })).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: 'Resume schedule', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Pause schedule', exact: true })).toBeVisible()
  expect(calls.schedulePauses).toEqual([{ paused: true }, { paused: false }])
})

test('on a phone reviews the exact scheduled draft, refreshes stale evidence and returns to its run', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const calls = await install(page, { scheduleState: 'existing', conflictOnce: true })
  await page.goto(scheduleHref)
  const history = page.getByRole('region', { name: 'Run history', exact: true })
  await expect(page.getByRole('region', { name: 'Needs attention', exact: true })).toContainText('Failed', { timeout: 30_000 })
  await expect(history.getByText(failedRun.error!, { exact: true })).toBeVisible({ timeout: 30_000 })
  await history.getByRole('button', { name: 'Retry preparation', exact: true }).click()
  await expect.poll(() => calls.scheduleRetries).toEqual([failedRun.id])
  await history.getByRole('link', { name: 'Review draft', exact: true }).click()
  await expect(page.getByRole('article', { name: 'Report preview', exact: true })).toContainText(source, { timeout: 30_000 })
  await expect(page.getByRole('link', { name: 'Back to schedule', exact: true })).toHaveAttribute('href', scheduleHref)
  expect(new URL(page.url()).pathname + new URL(page.url()).search).toBe(scheduledRunHref)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Scheduled preparation', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page.getByRole('main').getByRole('alert')).toContainText(/no longer current/)
  await expect(page.getByRole('button', { name: 'Approve version', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Refresh evidence', exact: true }).click()
  await page.locator('summary').filter({ hasText: 'Rechecked July sample' }).click()
  await expect(page.getByRole('link', { name: 'Open evidence', exact: true })).toHaveAttribute('href', '/evidence?system=system-2&evidence=period-artifact')
  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page.getByRole('article', { name: 'Approved report', exact: true })).toContainText('reviewer@example.test')
  expect(calls.approvals).toEqual([{ id: reportId, body: { revision } }, { id: reportId, body: { revision: 'd'.repeat(64) } }])
  expect(calls.scheduleRetries).toEqual([failedRun.id, scheduledRun.id])
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.getByRole('link', { name: 'Back to schedule', exact: true }).click()
  await expect(history.getByRole('link', { name: 'Open approved version', exact: true })).toHaveAttribute('href', scheduledRunHref)
  await history.getByRole('link', { name: 'Open approved version', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Approved report', exact: true })).toBeVisible()
  await page.goBack()
  await expect(history.getByRole('link', { name: 'Open approved version', exact: true })).toHaveAttribute('href', scheduledRunHref)
  const opened = calls.reviews.length
  await page.goto(scheduledRunHref.replace(`system=${definition.systemId}`, `system=${systems[0].id}`))
  await expect(page.getByRole('heading', { name: 'Saved report unavailable', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toHaveCount(0)
  expect(calls.reviews).toHaveLength(opened)
})

test('takes the reviewer from My work through return and approval of a fresh revision', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const calls = await install(page, { scheduleState: 'existing', assigned: true })
  await page.goto('/needs-you')
  const queue = page.getByRole('region', { name: 'Reports awaiting your review', exact: true })
  const entry = queue.getByRole('link', { name: /Review draft of Claims pilot monthly assurance/ })
  await expect(entry).toHaveAttribute('href', scheduledRunHref, { timeout: 30_000 })
  await expect(queue).toContainText(systems[1].name)
  await entry.click()
  await expect(page.getByRole('article', { name: 'Report preview', exact: true })).toContainText(assignedReviewer.name, { timeout: 30_000 })
  await page.getByRole('button', { name: 'Return for changes', exact: true }).click()
  await expect(page.getByLabel('Reason for returning', { exact: true })).toBeFocused()
  await page.getByLabel('Reason for returning', { exact: true }).fill(returnReason)
  await page.getByRole('button', { name: 'Return draft', exact: true }).click()
  const decision = page.getByRole('region', { name: 'Return decision', exact: true })
  await expect(decision).toContainText(returnReason)
  await expect(decision).toBeFocused()
  expect(calls.returnedReviews).toEqual([{ revision, reason: returnReason }])
  await expect(page.getByRole('button', { name: 'Approve version', exact: true })).toHaveCount(0)
  await page.reload()
  await expect(decision).toContainText(returnReason)
  await page.getByRole('link', { name: 'Back to schedule', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Run history', exact: true })).toContainText(returnReason)
  await page.getByRole('link', { name: 'Open returned draft', exact: true }).first().click()
  await page.getByRole('button', { name: 'Prepare new revision', exact: true }).click()
  await expect(page.locator('summary').filter({ hasText: 'Rechecked July sample' })).toBeVisible()
  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Approved report', exact: true })).toBeVisible()
  expect(calls.approvals).toEqual([{ id: reportId, body: { revision: 'd'.repeat(64) } }])
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.goto('/needs-you')
  await expect(page.getByRole('heading', { name: 'Needs you', exact: true })).toBeVisible()
  await expect(entry).toHaveCount(0)
})

test('changes the default reviewer separately from the reviewer of an outstanding run', async ({ page }) => {
  const calls = await install(page, { scheduleState: 'existing', assigned: true })
  await page.goto(scheduleHref)
  const future = page.getByRole('region', { name: 'Default reviewer', exact: true })
  await future.getByLabel('Reviewer for future runs', { exact: true }).selectOption(otherReviewer.id, { timeout: 30_000 })
  await future.getByRole('button', { name: 'Save reviewer', exact: true }).click()
  await expect(future).toContainText(`${otherReviewer.name} is assigned to future runs.`)
  const history = page.getByRole('region', { name: 'Run history', exact: true })
  await expect(history).toContainText(assignedReviewer.name)
  await history.locator('summary').filter({ hasText: 'Reassign reviewer' }).click()
  await history.getByLabel('Run reviewer', { exact: true }).selectOption(otherReviewer.id)
  await history.getByRole('button', { name: 'Save reviewer', exact: true }).click()
  await expect(history).toContainText(otherReviewer.name)
  expect(calls.reviewerChanges).toEqual([
    { scope: 'schedule', reviewer_id: otherReviewer.id }, { scope: 'run', reviewer_id: otherReviewer.id },
  ])
  await page.goto(scheduledRunHref)
  await expect(page.getByRole('article', { name: 'Report preview', exact: true })).toContainText(otherReviewer.name)
  await expect(page.getByRole('button', { name: 'Approve version', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Return for changes', exact: true })).toHaveCount(0)
})

test('previews and approves one scoped period, then reopens and exports the stored version', async ({ page }) => {
  const calls = await install(page)
  await prepare(page)
  expect(calls.previewBodies).toEqual([{
    system_id: systems[1].id,
    assignment_id: framework.assignmentId,
    date_from: period.dateFrom,
    date_to: period.dateTo,
    narrative,
  }])
  await expect(page.getByText('Manual checks cover one cohort.', { exact: true }).first()).toBeVisible()
  await page.locator('summary').filter({ hasText: source }).click()
  await expect(page.getByRole('link', { name: 'Open evidence' })).toHaveAttribute('href', '/evidence?system=system-2&evidence=period-artifact')
  await expect(page.getByText('c'.repeat(64), { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page.getByRole('article', { name: 'Approved report' })).toContainText('reviewer@example.test')
  expect(calls.approvals).toEqual([{ id: reportId, body: { revision } }])
  await expect.poll(() => calls.historyScopes).toContainEqual({ systemId: systems[1].id, reportType: 'system-assurance' })

  await page.getByRole('link', { name: 'Open approved version', exact: true }).click()
  await expect(page).toHaveURL(new RegExp(reportId))
  const previousOpens = calls.openedVersions.length
  await page.reload()
  await expect(page.getByText(source, { exact: true }).first()).toBeVisible()
  await expect(page.getByText(narrative, { exact: true })).toBeVisible()
  expect(calls.openedVersions.length).toBeGreaterThan(previousOpens)
  const downloading = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download PDF', exact: true }).click()
  const download = await downloading
  expect(download.suggestedFilename()).toMatch(/\.pdf$/)
  expect(await readFile(await download.path(), 'utf8')).toBe(exportedPdf)
  expect(calls.downloads).toEqual([`/api/v1/reports/snapshots/${reportId}/pdf`])
})

test('requires a new preview when source records change before approval', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const calls = await install(page, { conflictOnce: true })
  await prepare(page)
  for (const dateLabel of ['Start date', 'End date']) {
    const bounds = await page.getByLabel(dateLabel, { exact: true }).boundingBox()
    expect(bounds).not.toBeNull()
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(390)
  }

  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page.getByRole('main').getByRole('alert')).toContainText(/source records changed/i)
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toHaveCount(0)
  expect(calls.approvals).toEqual([{ id: reportId, body: { revision } }])

  await page.getByRole('button', { name: 'Preview report', exact: true }).click()
  await expect(page.getByText('Rechecked July sample', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Approve version', exact: true }).click()
  await expect(page).toHaveURL(new RegExp(refreshedReportId), { timeout: 30_000 })
  await expect(page.getByRole('article', { name: 'Approved report' })).toContainText('reviewer@example.test')
  expect(calls.approvals).toEqual([
    { id: reportId, body: { revision } },
    { id: refreshedReportId, body: { revision: 'd'.repeat(64) } },
  ])
})

test('shows approved versions to mobile readers without write actions', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const calls = await install(page, { viewer: true })
  await page.goto('/reports/system?system=system-2')
  await expect(page.getByRole('heading', { name: 'System Assurance Report', exact: true })).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('button', { name: 'Preview report', exact: true })).toHaveCount(0)
  await page.getByRole('link', { name: 'Open approved version', exact: true }).click()
  await expect(page.getByText(source, { exact: true }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: 'Approve version', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Back to version history', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toBeVisible()
  expect(calls.previewBodies).toHaveLength(0)
  expect(calls.approvals).toHaveLength(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)

  await page.goto(`/reports/system?system=system-1&report=${reportId}`)
  await expect(page.getByRole('heading', { name: 'Approved version unavailable' })).toBeVisible()
  await expect(page.getByText(source, { exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Download PDF', exact: true })).toHaveCount(0)
})

test.describe('Saved assurance reports', () => {
  test.use({ timezoneId: 'America/Los_Angeles' })

  test('saves a named setup, retains it for approval, and starts another period independently', async ({ page }) => {
    await page.clock.setFixedTime(new Date('2026-08-01T00:05:00Z'))
    const calls = await install(page)
    await page.goto('/reports/system?system=system-2')
    await page.getByText('Save report setup', { exact: true }).click()
    await page.getByLabel('Report name', { exact: true }).fill(definition.title)
    await page.getByRole('button', { name: 'Save setup', exact: true }).click()
    await expect(page.getByRole('heading', { name: definition.title, exact: true })).toBeVisible()
    expect(calls.definitionBodies).toEqual([{ title: definition.title, system_id: definition.systemId, assignment_id: definition.assignmentId }])
    await expect(page.getByText('Saved report', { exact: true })).toBeVisible()
    await expect(page.getByRole('combobox', { name: 'AI system', exact: true })).toHaveCount(0)
    await expect(page.getByRole('combobox', { name: 'Framework assignment', exact: true })).toHaveCount(0)

    const startDate = page.getByLabel('Start date', { exact: true })
    const endDate = page.getByLabel('End date', { exact: true })
    const note = page.getByLabel(/^Reviewer note/)
    await expect(startDate).toHaveValue('2026-07-01')
    await expect(endDate).toHaveValue('2026-07-31')
    await startDate.fill('2026-07-12')
    await note.fill(narrative)
    await page.getByRole('button', { name: 'Preview report', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Report preview', exact: true })).toBeVisible()
    expect(calls.previewBodies).toEqual([{
      system_id: definition.systemId,
      assignment_id: definition.assignmentId,
      definition_id: definition.id,
      date_from: '2026-07-12',
      date_to: '2026-07-31',
      narrative,
    }])
    await page.getByRole('button', { name: 'Approve version', exact: true }).click()
    await expect(page.getByRole('article', { name: 'Approved report' })).toBeVisible()
    const approvedURL = new URL(page.url())
    expect(approvedURL.searchParams.get('definition')).toBe(definition.id)
    expect(approvedURL.searchParams.get('report')).toBe(reportId)
    expect(calls.historyScopes).toContainEqual({ systemId: definition.systemId, reportType: 'system-assurance', definitionId: definition.id })

    await page.clock.setFixedTime(new Date('2026-09-01T00:05:00Z'))
    await page.goto('/reports')
    const savedReports = page.getByRole('region', { name: 'Saved reports' })
    const saved = savedReports.getByRole('link', { name: definition.title, exact: true })
    await expect(saved).toHaveAttribute('href', `/reports/system?system=${definition.systemId}&definition=${definition.id}`)
    await saved.click()
    await expect(page.getByRole('heading', { name: definition.title, exact: true })).toBeVisible()
    await expect(startDate).toHaveValue('2026-08-01')
    await expect(endDate).toHaveValue('2026-08-31')
    await expect(note).toHaveValue('')
    await expect(page.getByRole('link', { name: 'Open approved version', exact: true })).toBeVisible()
  })

  test('opens saved scopes as a mobile reader and rejects a conflicting system link', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const calls = await install(page, { viewer: true, savedSetup: true })
    await page.goto('/reports')
    const savedReports = page.getByRole('region', { name: 'Saved reports' })
    await savedReports.getByRole('searchbox', { name: 'Search saved reports' }).fill(systems[1].name)
    await savedReports.getByRole('link', { name: definition.title, exact: true }).click()
    await expect(page.getByRole('heading', { name: definition.title, exact: true })).toBeVisible()
    await expect(page.getByText('Open an approved version and inspect its evidence.', { exact: true })).toBeVisible()
    await expect(page.getByText('Save report setup', { exact: true })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Preview report', exact: true })).toHaveCount(0)
    await expect(page.getByRole('link', { name: 'Open approved version', exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)

    await page.goto(`/reports/system?system=${systems[0].id}&definition=${definition.id}`)
    await expect(page.getByText('Saved report unavailable', { exact: true })).toBeVisible()
    await expect(page.getByText(definition.title, { exact: true })).toHaveCount(0)
    await expect(page.getByRole('link', { name: 'Open approved version', exact: true })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Preview report', exact: true })).toHaveCount(0)
    expect(calls.definitionBodies).toHaveLength(0)
    expect(calls.previewBodies).toHaveLength(0)
  })
})

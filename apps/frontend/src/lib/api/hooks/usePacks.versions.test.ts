import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

import { API_ENDPOINTS } from '../endpoints'
import type { ApiResponse } from '../api-client'
import { loadResource, viewResource, type ResourceState } from './usePacks'
import type { WorkflowVersion } from './usePacks'

const VERSIONS_URL = '/api/v1/packs/workflows/wf-1/versions?org_id=org-1'

const VERSION_A: WorkflowVersion = {
  version: 2,
  label: 'org-2',
  status: 'published',
  basedOn: 'org-1',
  createdBy: 'ada@example.test',
  publishedBy: 'ada@example.test',
  createdAt: '2026-11-01T10:00:00Z',
  publishedAt: '2026-11-02T10:00:00Z',
}

describe('workflow versions', () => {
  test('the versions endpoint names the workflow versions route', () => {
    assert.equal(API_ENDPOINTS.packs.workflowVersions('wf-1'), '/api/v1/packs/workflows/wf-1/versions')
  })

  test('loads the version list for the workflow', async () => {
    let state: ResourceState<WorkflowVersion[]> = { scopeKey: VERSIONS_URL, value: { data: null, loading: true, error: null } }
    const get = async (): Promise<ApiResponse<WorkflowVersion[]>> => ({ success: true, data: [VERSION_A] })
    const update = (next: (s: ResourceState<WorkflowVersion[]>) => ResourceState<WorkflowVersion[]>) => {
      state = next(state)
    }
    await loadResource<WorkflowVersion[]>(get, VERSIONS_URL, update)
    const view = viewResource(state, VERSIONS_URL)
    assert.equal(view.loading, false)
    assert.equal(view.data?.length, 1)
    assert.equal(view.data?.[0].label, 'org-2')
    assert.equal(view.data?.[0].publishedBy, 'ada@example.test')
  })
})

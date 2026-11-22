import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { RunWay } from '@/lib/api/hooks/usePacks'
import { bucketOf, defaultWay, groupRows, keptAs, presetFor, proves } from './evaluations'

const w = (way: RunWay, ready = true) => ({ way, ready })

test('the run page opens on calling the system when ready, then live runs, then files', () => {
  assert.equal(defaultWay([w('files'), w('calls_system')]), 'calls_system')
  assert.equal(defaultWay([w('files'), w('calls_system', false), w('live_runs')]), 'live_runs')
  assert.equal(defaultWay([w('calls_system', false), w('live_runs', false), w('files')]), 'files')
  assert.equal(defaultWay([w('calls_system', false)]), 'calls_system') // shows its setup
  assert.equal(defaultWay([w('platform'), w('files')]), 'platform')
  assert.equal(defaultWay([w('fairmind_data'), w('files')]), 'fairmind_data') // records FairMind holds beat an upload
  assert.equal(defaultWay([w('fairmind_data', false), w('files')]), 'files')
  assert.equal(defaultWay([w('files'), w('live_runs')], 'live_runs'), 'live_runs') // asked by a link
  assert.equal(defaultWay([w('files'), w('live_runs', false)], 'live_runs'), 'files') // asked, but no live runs yet
  assert.equal(defaultWay([w('files')], 'live_runs'), 'files')
  assert.equal(defaultWay([]), null)
})

test('the probe count defaults to the smallest preset that proves the limit, else the largest', () => {
  const bounds = [{ count: 50, bound: 5.82 }, { count: 10, bound: 25.89 }, { count: 20, bound: 13.91 }]
  assert.equal(presetFor(bounds, 15), 20)
  assert.equal(presetFor(bounds, 30), 10)
  assert.equal(presetFor(bounds, 2), 50) // none can: a pass at 2% needs an uploaded set
  assert.equal(presetFor(bounds, 0), 10) // zero tolerance needs no bound
  assert.equal(presetFor(bounds, null), null)
  assert.equal(presetFor([], 5), null)
  assert.ok(proves(13.91, 13.91) && !proves(13.92, 13.91))
})

test('evaluations group into ready now, need a file, need setup and does not apply', () => {
  assert.equal(bucketOf({ fit: 'applies', ways: [w('calls_system'), w('files')] }), 'ready')
  assert.equal(bucketOf({ fit: 'unknown', ways: [w('calls_system', false), w('files')] }), 'file')
  assert.equal(bucketOf({ fit: 'applies', ways: [w('calls_system', false)] }), 'setup')
  assert.equal(bucketOf({ fit: 'other', ways: [w('calls_system')] }), 'other')
  assert.equal(bucketOf({ fit: 'applies', ways: [] }), null) // FairMind cannot run it
  const g = groupRows([{ id: 'a', ways: [w('files')] }, { id: 'b', fit: 'other' as const, ways: [w('files')] }, { id: 'c' }])
  assert.deepEqual([g.ready.length, g.file.map((r) => r.id), g.setup.length, g.other.map((r) => r.id)], [0, ['a'], 0, ['b']])
})

test('a run is kept as measured live only when FairMind called the system or read the platform', () => {
  assert.equal(keptAs('calls_system'), 'Measured live')
  assert.equal(keptAs('platform'), 'Measured live')
  assert.equal(keptAs('live_runs'), 'Computed from upload')
  assert.equal(keptAs('files'), 'Computed from upload')
  assert.equal(keptAs('fairmind_data'), 'Computed from FairMind records') // nothing is uploaded
  assert.equal(keptAs('files', true), 'Measured live') // FairMind's own agent answers live
  assert.equal(keptAs('live_runs', true), 'Computed from upload')
  assert.equal(keptAs('live_runs', false, true), 'Measured live') // Explanation quality replays live runs on the connection
})

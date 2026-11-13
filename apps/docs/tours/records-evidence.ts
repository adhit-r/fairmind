import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/records/evidence',
  title: 'Find and inspect the evidence behind a release decision',
  steps: [
    { goto: '/evidence', say: 'Evidence is collected per AI system. Pick the system here.' },
    { click: role('combobox', 'AI system'), say: 'Choose a system to see what backs its release decision.' },
    { click: role('option', /sst-2/), say: 'Here, the sentiment classifier, which has a fairness test, its model card and an accuracy run on file.' },
    { point: role('region', 'Evidence chain'), say: 'The summary shows how many items exist, whether the chain is sealed, and how many are stale.' },
    { click: css('main table tbody tr button', 0), say: 'Select an item to open it: what it is, where it came from, and how much it counts.' },
  ],
})

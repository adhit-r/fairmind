import { css, role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/records/evidence',
  title: 'Find and inspect the evidence behind a release decision',
  steps: [
    { goto: '/evidence', say: 'Evidence is collected per AI system. Pick the system here.' },
    { point: role('region', 'Evidence chain'), say: 'This summary shows how many items exist, whether the chain is intact and how many are stale.' },
    { point: role('textbox', 'Search evidence'), say: 'Search by title, type, folder or tag.' },
    { click: css('main table tbody tr button', 0), say: 'Select an item to open its detail drawer.' },
  ],
})

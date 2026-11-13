import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/release/decisions',
  title: 'Read a release decision and its sealed record',
  steps: [
    { goto: '/decisions', say: 'Decisions lists every release approval request for your systems.' },
    { point: role('radio', /^Pending/), say: 'The filter switches between pending, approved and rejected. Each shows its count.' },
    { click: css('button.fm-dec-row', 0), say: 'Click a request to open it.' },
    { point: role('link', 'Review and decide'), say: 'A pending request is decided on the system file, beside the release gate, by someone other than the person who asked.' },
  ],
})

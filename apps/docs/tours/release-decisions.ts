import { css, role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/release/decisions',
  title: 'Read a release decision and its sealed record',
  steps: [
    { goto: '/decisions', say: 'Decisions lists every release approval request for your systems.' },
    { click: text('Approved'), say: 'Switch the filter between pending, approved and rejected. Each shows its count.' },
    { click: css('.fm-dec-row:not(.fm-dec-head)', 0), say: 'Click a row to open the request.' },
    { point: text('Sealed records for this system'), say: 'Each seal shows the gate verdict at the time, the evidence count, and whether the chain is intact.' },
    { point: role('link', 'Open the system file'), say: 'Pending requests are decided on the system file, beside the release gate.' },
  ],
})

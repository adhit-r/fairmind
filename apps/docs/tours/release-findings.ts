import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/release/findings',
  title: 'See where findings collect',
  steps: [
    { goto: '/findings', say: 'Findings lists everything raised against your systems, most serious first.' },
    { point: text('No findings'), say: 'The demo has none yet: its one fairness test passed. A failed check, a policy alert or a monitoring watch raises a finding here.' },
    { point: role('link', 'Release'), say: 'Each finding opens with what was found, the suggested fix and its remediation tasks. It closes when the next check passes.' },
  ],
})

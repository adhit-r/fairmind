import { css, text, tour } from '../capture/tour'

export default tour({
  page: 'app/release/findings',
  title: 'Open a finding and read its fix and tasks',
  steps: [
    { goto: '/findings', say: 'Findings lists everything raised against your systems, most serious first.' },
    { point: css('.fm-fnd-counts'), say: 'The counts show all findings, how many are open, and the split by severity.' },
    { click: css('.fm-fnd button.title', 0), say: 'Click a finding to open it.' },
    { point: text('Suggested fix'), say: 'The drawer says what was found and what fix was suggested, when the source recorded one.' },
    { point: text('Remediation tasks'), say: 'Remediation tasks track the work. A finding closes when the next check result passes.' },
  ],
})

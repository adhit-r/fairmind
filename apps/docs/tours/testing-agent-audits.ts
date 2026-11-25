import { css, role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/testing/agent-audits',
  title: 'See the connection and the audit checks',
  steps: [
    { goto: '/agent-audits', say: 'Agent audits reads your agent platform with a read-only key. Claude Managed Agents is the only platform today.' },
    { point: role('button', 'Save key'), say: 'This is where you would save the key. It is encrypted and never shown again.' },
    { point: text('Audit checks'), say: 'Below the connection are the checks. Each one says whether it reads the platform or an uploaded file.' },
    { click: css('.fm-au-twisty', 0), say: 'Open a check to see the latest result for each system.' },
    { point: css('.fm-au-check td:last-child a, .fm-au-check td:last-child button', 0), say: 'Run leads to the evaluation page, where the check is started on a registered system.' },
  ],
})

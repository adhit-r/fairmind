import { css, text, tour } from '../capture/tour'

export default tour({
  page: 'app/testing/runs',
  title: 'Open a run and read its steps and ledger',
  steps: [
    { goto: '/runs', say: 'Every started workflow is a run. The line under the title says how many are waiting on a person.' },
    { point: css('.fm-rn-list'), say: 'Filter by status. Only statuses that exist in your runs are offered.' },
    { click: css('.fm-rn-item', 0), say: 'Click a run to open its detail beside the list.' },
    { point: text('Steps'), say: 'Steps shows which are done, which is current, and where a person decides.' },
    { scroll: 600, say: 'Further down, the ledger lists each event with its hash, and says whether the chain is intact.' },
  ],
})

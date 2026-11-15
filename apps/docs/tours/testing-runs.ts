import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/testing/runs',
  title: 'See where workflow runs appear',
  steps: [
    { goto: '/runs', say: 'Every started workflow is a run. The line under the title says how many are waiting on a person.' },
    { point: text('No runs yet'), say: 'The demo has none yet. A run starts when a workflow is started from a framework or a system.' },
    { point: role('link', 'Frameworks'), say: 'Open a run to see its steps, where a person decides, and a ledger whose chain of hashes shows nothing was changed.' },
  ],
})
